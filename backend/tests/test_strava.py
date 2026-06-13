"""
Tests for Strava integration.

Strategy
--------
We never call Strava in tests. Two mock boundaries:

1. Strava client unit tests — mock `requests.post` / `requests.get` and assert
   our normalization + error-raising logic in strava.py.
2. View + task tests — mock `integrations.strava.*` functions and assert our
   side: Integration/OAuthToken creation, Workout creation, dedup logic,
   webhook challenge, and error paths.
"""
from datetime import datetime, timezone as dt_timezone
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from integrations.models import Integration, OAuthToken, Provider, SyncLog
from integrations.strava import StravaError
from workouts.models import Workout
from tests.factories import UserFactory, WorkoutFactory

User = get_user_model()

LIST_URL = "/api/v1/integrations/"
CONNECT_URL = "/api/v1/integrations/strava/connect/"
CALLBACK_URL = "/api/v1/integrations/strava/callback/"
DISCONNECT_URL = "/api/v1/integrations/strava/disconnect/"
WEBHOOK_URL = "/api/v1/integrations/strava/webhook/"

# Minimal Strava token response
FAKE_TOKEN = {
    "access_token": "access-abc",
    "refresh_token": "refresh-xyz",
    "expires_at": 9999999999,
    "expires_in": 21600,
    "scope": "read,activity:read_all",
    "athlete": {"id": 42, "firstname": "Jane", "lastname": "Doe"},
}

FAKE_ACTIVITY = {
    "id": 111,
    "name": "Morning Run",
    "type": "Run",
    "start_date": "2024-03-15T07:00:00Z",
    "start_date_local": "2024-03-15T07:00:00Z",
    "elapsed_time": 3600,
    "distance": 10000.0,
    "average_heartrate": 145.0,
    "calories": 600,
    "athlete": {"id": 42},
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_integration(user):
    integration = Integration.objects.create(user=user, provider=Provider.STRAVA)
    OAuthToken.objects.create(
        integration=integration,
        access_token="access-abc",
        refresh_token="refresh-xyz",
        expires_at=datetime(2099, 1, 1, tzinfo=dt_timezone.utc),
        athlete_id="42",
    )
    return integration


# ── Strava client unit tests ───────────────────────────────────────────────────

class TestStravaClient:
    @patch("integrations.strava.requests.post")
    def test_exchange_code_success(self, mock_post):
        from integrations.strava import exchange_code
        mock_post.return_value = MagicMock(status_code=200, json=lambda: FAKE_TOKEN)
        result = exchange_code("valid-code")
        assert result["access_token"] == "access-abc"
        assert result["athlete"]["id"] == 42

    @patch("integrations.strava.requests.post")
    def test_exchange_code_failure_raises(self, mock_post):
        from integrations.strava import StravaError, exchange_code
        mock_post.return_value = MagicMock(
            status_code=401,
            json=lambda: {"message": "Bad verification code"},
        )
        with pytest.raises(StravaError):
            exchange_code("bad-code")

    @patch("integrations.strava.requests.get")
    def test_get_activity_success(self, mock_get):
        from integrations.strava import get_activity
        mock_get.return_value = MagicMock(status_code=200, json=lambda: FAKE_ACTIVITY)
        result = get_activity("token", 111)
        assert result["id"] == 111

    @patch("integrations.strava.requests.get")
    def test_get_activity_failure_raises(self, mock_get):
        from integrations.strava import StravaError, get_activity
        mock_get.return_value = MagicMock(status_code=404, json=lambda: {})
        with pytest.raises(StravaError):
            get_activity("token", 999)

    def test_map_activity_to_workout(self):
        from integrations.strava import map_activity_to_workout
        result = map_activity_to_workout(FAKE_ACTIVITY)
        assert result["name"] == "Morning Run"
        assert result["duration_min"] == 60
        assert result["calories_burned"] == 600
        assert result["status"] == "completed"
        assert result["source"] == "strava"
        assert float(result["distance_km"]) == pytest.approx(10.0, rel=0.01)

    def test_map_activity_unnamed_uses_type_label(self):
        from integrations.strava import map_activity_to_workout
        activity = {**FAKE_ACTIVITY, "name": "", "type": "Ride"}
        result = map_activity_to_workout(activity)
        assert "Ride" in result["name"]

    @patch("integrations.strava.requests.post")
    def test_refresh_access_token_success(self, mock_post):
        from integrations.strava import refresh_access_token
        mock_post.return_value = MagicMock(status_code=200, json=lambda: FAKE_TOKEN)
        result = refresh_access_token("refresh-xyz")
        assert result["access_token"] == "access-abc"

    @patch("integrations.strava.requests.post")
    def test_refresh_access_token_failure_raises(self, mock_post):
        from integrations.strava import StravaError, refresh_access_token
        mock_post.return_value = MagicMock(status_code=401, json=lambda: {"message": "Bad token"})
        with pytest.raises(StravaError):
            refresh_access_token("bad-refresh")


# ── Connect view ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStravaConnect:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(CONNECT_URL)
        assert res.status_code == 401

    def test_authenticated_redirects_to_strava(self, api_client):
        from rest_framework_simplejwt.tokens import AccessToken
        user = UserFactory()
        token = str(AccessToken.for_user(user))
        res = api_client.get(CONNECT_URL, {"jwt": token})
        assert res.status_code == 302
        assert "strava.com/oauth/authorize" in res["Location"]
        assert "activity:read_all" in res["Location"]

    def test_redirect_contains_client_id(self, api_client):
        from rest_framework_simplejwt.tokens import AccessToken
        user = UserFactory()
        token = str(AccessToken.for_user(user))
        res = api_client.get(CONNECT_URL, {"jwt": token})
        assert "test-strava-client-id" in res["Location"]


# ── Callback view ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStravaCallback:
    @patch("integrations.views.exchange_code", return_value=FAKE_TOKEN)
    def test_valid_code_creates_integration(self, _, api_client):
        user = UserFactory()
        # Get a valid signed state
        from integrations.views import _sign_state
        state = _sign_state(user.pk)
        res = api_client.get(CALLBACK_URL, {"code": "valid", "state": state})
        assert res.status_code == 302
        assert Integration.objects.filter(user=user, provider=Provider.STRAVA).exists()

    @patch("integrations.views.exchange_code", return_value=FAKE_TOKEN)
    def test_valid_code_creates_oauth_token(self, _, api_client):
        user = UserFactory()
        from integrations.views import _sign_state
        state = _sign_state(user.pk)
        api_client.get(CALLBACK_URL, {"code": "valid", "state": state})
        integration = Integration.objects.get(user=user)
        assert OAuthToken.objects.filter(integration=integration).exists()
        assert OAuthToken.objects.get(integration=integration).athlete_id == "42"

    @patch("integrations.views.exchange_code", return_value=FAKE_TOKEN)
    def test_reconnect_does_not_duplicate_integration(self, _, api_client):
        user = UserFactory()
        _make_integration(user)
        from integrations.views import _sign_state
        state = _sign_state(user.pk)
        api_client.get(CALLBACK_URL, {"code": "valid", "state": state})
        assert Integration.objects.filter(user=user).count() == 1

    def test_invalid_state_returns_400(self, api_client):
        res = api_client.get(CALLBACK_URL, {"code": "x", "state": "tampered"})
        assert res.status_code == 400

    def test_user_denied_redirects_with_error(self, api_client):
        res = api_client.get(CALLBACK_URL, {"error": "access_denied"})
        assert res.status_code == 302
        assert "strava_error" in res["Location"]

    @patch("integrations.views.exchange_code", side_effect=StravaError("Strava down"))
    def test_token_exchange_failure_redirects_with_error(self, _, api_client):
        user = UserFactory()
        from integrations.views import _sign_state
        state = _sign_state(user.pk)
        res = api_client.get(CALLBACK_URL, {"code": "x", "state": state})
        assert res.status_code == 302
        assert "strava_error" in res["Location"]


# ── Disconnect view ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStravaDisconnect:
    def test_disconnect_deactivates_integration(self, api_client):
        user = UserFactory()
        integration = _make_integration(user)
        api_client.force_authenticate(user)
        res = api_client.delete(DISCONNECT_URL)
        assert res.status_code == 204
        integration.refresh_from_db()
        assert not integration.is_active

    def test_disconnect_removes_token(self, api_client):
        user = UserFactory()
        _make_integration(user)
        api_client.force_authenticate(user)
        api_client.delete(DISCONNECT_URL)
        assert not OAuthToken.objects.filter(integration__user=user).exists()

    def test_disconnect_not_connected_returns_404(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        res = api_client.delete(DISCONNECT_URL)
        assert res.status_code == 404

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.delete(DISCONNECT_URL)
        assert res.status_code == 401


# ── Webhook view ───────────────────────────────────────────────────────────────

class TestStravaWebhook:
    def test_hub_challenge_verification(self, api_client):
        res = api_client.get(WEBHOOK_URL, {
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token",
            "hub.challenge": "abc123",
        })
        assert res.status_code == 200
        assert res.data["hub.challenge"] == "abc123"

    def test_hub_challenge_wrong_token_returns_403(self, api_client):
        res = api_client.get(WEBHOOK_URL, {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "abc123",
        })
        assert res.status_code == 403

    @pytest.mark.django_db
    @patch("integrations.views.process_strava_activity.delay")
    def test_activity_create_queues_task(self, mock_delay, api_client):
        user = UserFactory()
        integration = _make_integration(user)
        res = api_client.post(WEBHOOK_URL, {
            "object_type": "activity",
            "aspect_type": "create",
            "object_id": 111,
            "owner_id": 42,
        }, format="json")
        assert res.status_code == 200
        mock_delay.assert_called_once_with(integration.pk, 111, "activity.create")

    @pytest.mark.django_db
    @patch("integrations.views.process_strava_activity.delay")
    def test_unknown_athlete_returns_200_no_task(self, mock_delay, api_client):
        # Strava requires a 200 even when we don't know the athlete
        res = api_client.post(WEBHOOK_URL, {
            "object_type": "activity",
            "aspect_type": "create",
            "object_id": 999,
            "owner_id": 9999,  # not in our DB
        }, format="json")
        assert res.status_code == 200
        mock_delay.assert_not_called()

    @pytest.mark.django_db
    @patch("integrations.views.process_strava_activity.delay")
    def test_non_activity_event_ignored(self, mock_delay, api_client):
        res = api_client.post(WEBHOOK_URL, {
            "object_type": "athlete",
            "aspect_type": "update",
            "object_id": 42,
            "owner_id": 42,
        }, format="json")
        assert res.status_code == 200
        mock_delay.assert_not_called()


# ── Task: process_strava_activity ──────────────────────────────────────────────

@pytest.mark.django_db
class TestProcessStravaActivity:
    @patch("integrations.strava.get_activity", return_value=FAKE_ACTIVITY)
    @patch("integrations.strava.ensure_fresh_token", return_value="access-abc")
    def test_create_event_creates_workout(self, _, __):
        from integrations.tasks import process_strava_activity
        user = UserFactory()
        integration = _make_integration(user)
        process_strava_activity(integration.pk, 111, "activity.create")
        assert Workout.objects.filter(user=user, name="Morning Run").exists()

    @patch("integrations.strava.get_activity", return_value=FAKE_ACTIVITY)
    @patch("integrations.strava.ensure_fresh_token", return_value="access-abc")
    def test_create_event_logs_success(self, _, __):
        from integrations.tasks import process_strava_activity
        user = UserFactory()
        integration = _make_integration(user)
        process_strava_activity(integration.pk, 111, "activity.create")
        log = SyncLog.objects.get(integration=integration, external_id="111")
        assert log.status == SyncLog.Status.SUCCESS
        assert log.workout is not None

    @patch("integrations.strava.get_activity", return_value=FAKE_ACTIVITY)
    @patch("integrations.strava.ensure_fresh_token", return_value="access-abc")
    def test_duplicate_create_is_skipped(self, _, __):
        from integrations.tasks import process_strava_activity
        user = UserFactory()
        integration = _make_integration(user)
        process_strava_activity(integration.pk, 111, "activity.create")
        process_strava_activity(integration.pk, 111, "activity.create")
        assert Workout.objects.filter(user=user).count() == 1
        skipped = SyncLog.objects.filter(integration=integration, status=SyncLog.Status.SKIPPED)
        assert skipped.exists()

    @patch("integrations.strava.get_activity", return_value=FAKE_ACTIVITY)
    @patch("integrations.strava.ensure_fresh_token", return_value="access-abc")
    def test_update_event_updates_existing_workout(self, _, __):
        from integrations.tasks import process_strava_activity
        user = UserFactory()
        integration = _make_integration(user)
        workout = WorkoutFactory(user=user, name="Old Name")
        SyncLog.objects.create(
            integration=integration,
            event_type="activity.create",
            external_id="111",
            status=SyncLog.Status.SUCCESS,
            workout=workout,
        )
        updated_activity = {**FAKE_ACTIVITY, "name": "Updated Run"}
        with patch("integrations.strava.get_activity", return_value=updated_activity), \
             patch("integrations.strava.ensure_fresh_token", return_value="access-abc"):
            process_strava_activity(integration.pk, 111, "activity.update")
        workout.refresh_from_db()
        assert workout.name == "Updated Run"

    def test_delete_event_removes_workout(self):
        from integrations.tasks import process_strava_activity
        user = UserFactory()
        integration = _make_integration(user)
        workout = WorkoutFactory(user=user)
        SyncLog.objects.create(
            integration=integration,
            event_type="activity.create",
            external_id="111",
            status=SyncLog.Status.SUCCESS,
            workout=workout,
        )
        workout_pk = workout.pk
        process_strava_activity(integration.pk, 111, "activity.delete")
        assert not Workout.objects.filter(pk=workout_pk).exists()

    def test_strava_api_failure_logs_failed(self):
        from integrations.strava import StravaError
        from integrations.tasks import process_strava_activity
        user = UserFactory()
        integration = _make_integration(user)
        with patch("integrations.strava.get_activity", side_effect=StravaError("down")), \
             patch("integrations.strava.ensure_fresh_token", return_value="access-abc"), \
             pytest.raises(Exception):
            process_strava_activity(integration.pk, 111, "activity.create")
        log = SyncLog.objects.get(integration=integration)
        assert log.status == SyncLog.Status.FAILED


# ── Integration list view ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIntegrationListView:
    def test_lists_active_integrations(self, api_client):
        user = UserFactory()
        _make_integration(user)
        api_client.force_authenticate(user)
        res = api_client.get(LIST_URL)
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["provider"] == "strava"

    def test_does_not_list_other_users_integrations(self, api_client):
        other = UserFactory()
        _make_integration(other)
        user = UserFactory()
        api_client.force_authenticate(user)
        res = api_client.get(LIST_URL)
        assert res.data == []

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(LIST_URL)
        assert res.status_code == 401
