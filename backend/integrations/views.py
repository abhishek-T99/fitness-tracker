"""
Integration views: Strava (OAuth2) and Intervals.icu (API key).

Strava flow
-----------
GET  /integrations/strava/connect/    → redirect to Strava consent (JWT in ?state=)
GET  /integrations/strava/callback/   → exchange code, store tokens, redirect to /settings
DELETE /integrations/strava/disconnect/ → deactivate, remove tokens
GET/POST /integrations/strava/webhook/ → hub challenge + activity event routing

Intervals.icu flow
------------------
POST /integrations/intervals/connect/    → verify API key, store, kick off 30-day backfill
DELETE /integrations/intervals/disconnect/ → deactivate, remove key
POST /integrations/intervals/sync/       → manual pull for last N days
POST /integrations/intervals/webhook/    → activity push → sync_intervals_activities.delay
"""
import logging
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.core import signing
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Integration, OAuthToken, Provider, SyncLog
from .serializers import IntegrationSerializer
from .strava import StravaError, get_auth_url, exchange_code
from .tasks import process_strava_activity, sync_intervals_activities, sync_intervals_wellness

logger = logging.getLogger(__name__)

FRONTEND_SETTINGS_URL = "/settings"


def _sign_state(user_id: int) -> str:
    return signing.dumps(user_id, salt="strava-oauth")


def _unsign_state(state: str) -> int:
    return signing.loads(state, salt="strava-oauth", max_age=600)


class IntegrationListView(APIView):
    """List all integrations for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Integrations"], responses={200: IntegrationSerializer(many=True)})
    def get(self, request):
        integrations = Integration.objects.filter(user=request.user, is_active=True)
        return Response(IntegrationSerializer(integrations, many=True).data)


class StravaConnectView(APIView):
    """
    Redirect the authenticated user to Strava's OAuth consent screen.

    Accepts authentication via the standard Authorization header OR via a
    `jwt` query parameter (needed for browser redirect flows where JavaScript
    cannot set headers).
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=["Integrations"])
    def get(self, request):
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

        # Try header first, then fall back to ?jwt= query param
        user = None
        jwt_param = request.query_params.get("jwt")
        if jwt_param:
            try:
                auth = JWTAuthentication()
                from rest_framework_simplejwt.tokens import AccessToken
                validated = AccessToken(jwt_param)
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(pk=validated["user_id"])
            except Exception:
                return Response({"detail": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            # Standard JWT auth via header
            try:
                auth = JWTAuthentication()
                result = auth.authenticate(request)
                if result is None:
                    return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
                user, _ = result
            except Exception:
                return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        state = _sign_state(user.pk)
        callback = request.build_absolute_uri("/api/v1/integrations/strava/callback/")
        url = get_auth_url(redirect_uri=callback, state=state)
        return redirect(url)


class StravaCallbackView(APIView):
    """
    Handle Strava's OAuth callback.

    Strava redirects here after the user grants (or denies) access.
    The view is technically unauthenticated (Strava calls it), but the user
    identity is carried in the signed `state` parameter.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=["Integrations"])
    def get(self, request):
        error = request.query_params.get("error")
        if error:
            return redirect(f"{FRONTEND_SETTINGS_URL}?strava_error={error}")

        code = request.query_params.get("code")
        state = request.query_params.get("state", "")

        try:
            user_id = _unsign_state(state)
        except signing.BadSignature:
            return Response({"detail": "Invalid state parameter."}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_data = exchange_code(code)
        except StravaError as exc:
            logger.error("Strava code exchange failed for user %s: %s", user_id, exc)
            return redirect(f"{FRONTEND_SETTINGS_URL}?strava_error=token_exchange_failed")

        athlete = token_data.get("athlete", {})
        athlete_id = str(athlete.get("id", ""))

        integration, _ = Integration.objects.get_or_create(
            user=user, provider=Provider.STRAVA,
            defaults={"is_active": True},
        )
        integration.is_active = True
        integration.save(update_fields=["is_active"])

        expires_at = datetime.fromtimestamp(token_data["expires_at"], tz=dt_timezone.utc)
        OAuthToken.objects.update_or_create(
            integration=integration,
            defaults={
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "expires_at": expires_at,
                "scope": token_data.get("scope", ""),
                "athlete_id": athlete_id,
            },
        )

        return redirect(f"{FRONTEND_SETTINGS_URL}?strava_connected=true")


class StravaDisconnectView(APIView):
    """Disconnect the Strava integration (keeps existing workouts)."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Integrations"])
    def delete(self, request):
        try:
            integration = Integration.objects.get(user=request.user, provider=Provider.STRAVA)
        except Integration.DoesNotExist:
            return Response({"detail": "Not connected."}, status=status.HTTP_404_NOT_FOUND)

        # Remove tokens so we can't use them again
        OAuthToken.objects.filter(integration=integration).delete()
        integration.is_active = False
        integration.save(update_fields=["is_active"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class StravaWebhookView(APIView):
    """
    Strava webhook endpoint.

    GET  → hub.challenge validation (called once when you register the webhook)
    POST → incoming event (activity create / update / delete)
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=["Integrations"])
    def get(self, request):
        """Respond to Strava's subscription validation challenge."""
        hub_mode = request.query_params.get("hub.mode")
        hub_verify_token = request.query_params.get("hub.verify_token")
        hub_challenge = request.query_params.get("hub.challenge")

        if hub_mode != "subscribe" or hub_verify_token != settings.STRAVA_WEBHOOK_VERIFY_TOKEN:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        return Response({"hub.challenge": hub_challenge})

    @extend_schema(tags=["Integrations"])
    def post(self, request):
        """Process an incoming Strava event."""
        payload = request.data

        object_type = payload.get("object_type")   # "activity" or "athlete"
        aspect_type = payload.get("aspect_type")    # "create" / "update" / "delete"
        object_id = payload.get("object_id")        # activity ID
        owner_id = payload.get("owner_id")          # Strava athlete ID

        if object_type != "activity":
            return Response(status=status.HTTP_200_OK)

        event_type = f"activity.{aspect_type}"

        try:
            oauth = OAuthToken.objects.select_related("integration__user").get(
                athlete_id=str(owner_id)
            )
        except OAuthToken.DoesNotExist:
            # Athlete not in our system — ignore silently (Strava requires 200)
            return Response(status=status.HTTP_200_OK)

        if not oauth.integration.is_active:
            return Response(status=status.HTTP_200_OK)

        process_strava_activity.delay(
            oauth.integration.pk,
            object_id,
            event_type,
        )

        return Response(status=status.HTTP_200_OK)


# ── Intervals.icu ──────────────────────────────────────────────────────────────

class IntervalsConnectView(APIView):
    """
    Connect an Intervals.icu account using API key credentials.

    POST { athlete_id, api_key }
    → Verifies credentials against intervals.icu, stores them, kicks off a
      30-day backfill sync, returns the integration record.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Integrations"])
    def post(self, request):
        from .intervals import IntervalsError, verify_credentials

        athlete_id = (request.data.get("athlete_id") or "").strip()
        api_key = (request.data.get("api_key") or "").strip()

        if not athlete_id or not api_key:
            return Response(
                {"detail": "Both athlete_id and api_key are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the credentials actually work before storing anything
        try:
            athlete = verify_credentials(athlete_id, api_key)
        except IntervalsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        integration, _ = Integration.objects.get_or_create(
            user=request.user,
            provider=Provider.INTERVALS,
            defaults={"is_active": True},
        )
        integration.is_active = True
        integration.save(update_fields=["is_active"])

        # Store API key in access_token; Intervals keys never expire
        from django.utils import timezone as dj_timezone
        from datetime import datetime, timezone as dt_timezone

        OAuthToken.objects.update_or_create(
            integration=integration,
            defaults={
                "access_token": api_key,
                "refresh_token": "",
                "expires_at": datetime(2099, 1, 1, tzinfo=dt_timezone.utc),
                "scope": "read",
                "athlete_id": athlete_id,
            },
        )

        # Backfill last 30 days in the background
        sync_intervals_activities.delay(integration.pk, days_back=30)
        sync_intervals_wellness.delay(integration.pk, days_back=30)

        return Response(IntegrationSerializer(integration).data, status=status.HTTP_201_CREATED)


class IntervalsDisconnectView(APIView):
    """Disconnect the Intervals.icu integration (keeps existing workouts)."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Integrations"])
    def delete(self, request):
        try:
            integration = Integration.objects.get(
                user=request.user, provider=Provider.INTERVALS
            )
        except Integration.DoesNotExist:
            return Response({"detail": "Not connected."}, status=status.HTTP_404_NOT_FOUND)

        OAuthToken.objects.filter(integration=integration).delete()
        integration.is_active = False
        integration.save(update_fields=["is_active"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class IntervalsSyncView(APIView):
    """Manually trigger a sync for the last N days (default 7)."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Integrations"])
    def post(self, request):
        try:
            integration = Integration.objects.get(
                user=request.user, provider=Provider.INTERVALS, is_active=True
            )
        except Integration.DoesNotExist:
            return Response({"detail": "Not connected."}, status=status.HTTP_404_NOT_FOUND)

        days_back = int(request.data.get("days_back", 7))
        days_back = max(1, min(days_back, 365))

        sync_intervals_activities.delay(integration.pk, days_back=days_back)
        return Response({"detail": f"Sync started for the last {days_back} days."})


class IntervalsWebhookView(APIView):
    """
    Receive push events from Intervals.icu.

    Intervals.icu sends a POST to this URL whenever an activity is
    created or updated for a connected athlete. The payload contains the
    athlete ID, allowing us to identify the user.

    Configure this URL in Intervals.icu:
      Settings → API → Webhook URL → https://your-domain/api/v1/integrations/intervals/webhook/
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=["Integrations"])
    def post(self, request):
        payload = request.data
        # Intervals sends { athlete_id: "i12345", activity_id: 123, type: "activity" }
        athlete_id = str(payload.get("athlete_id", ""))
        activity_id = payload.get("activity_id") or payload.get("id")
        event_type = payload.get("type", "activity")

        if not athlete_id or not activity_id:
            return Response(status=status.HTTP_200_OK)

        try:
            token = OAuthToken.objects.select_related("integration__user").get(
                athlete_id=athlete_id,
                integration__provider=Provider.INTERVALS,
                integration__is_active=True,
            )
        except OAuthToken.DoesNotExist:
            return Response(status=status.HTTP_200_OK)

        # Trigger a short sync (today + yesterday) to pick up the new activity
        sync_intervals_activities.delay(token.integration.pk, days_back=2)
        return Response(status=status.HTTP_200_OK)
