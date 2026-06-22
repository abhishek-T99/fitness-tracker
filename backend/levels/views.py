import datetime as dt
from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .models import UserLevel, UserWeeklyChallenge, WeeklyChallenge, XPTransaction
from .serializers import (
    LeaderboardEntrySerializer,
    UserLevelSerializer,
    UserWeeklyChallengeSerializer,
    XPTransactionSerializer,
)
from .services import award_xp, detect_athlete_class, xp_for_level


class LevelProfileView(APIView):
    """GET /api/v1/levels/profile/ — full level profile for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Current user's level, XP, tier, class, and recent transactions",
        responses={200: UserLevelSerializer},
    )
    def get(self, request):
        user_level, _ = UserLevel.objects.get_or_create(user=request.user)
        return Response(UserLevelSerializer(user_level).data)


class XPTransactionListView(APIView):
    """GET /api/v1/levels/transactions/?limit=20&offset=0"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Paginated XP transaction history",
        parameters=[
            OpenApiParameter("limit",  int, description="Page size (default 20, max 100)"),
            OpenApiParameter("offset", int, description="Offset (default 0)"),
        ],
        responses={200: XPTransactionSerializer(many=True)},
    )
    def get(self, request):
        try:
            limit  = min(int(request.query_params.get("limit", 20)), 100)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except (TypeError, ValueError):
            limit, offset = 20, 0

        qs    = XPTransaction.objects.filter(user=request.user)
        total = qs.count()
        page  = qs[offset : offset + limit]

        return Response({
            "count":   total,
            "results": XPTransactionSerializer(page, many=True).data,
        })


class ChallengesView(APIView):
    """GET /api/v1/levels/challenges/ — this week's challenges + user progress."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Weekly challenges and the authenticated user's progress",
        responses={200: UserWeeklyChallengeSerializer(many=True)},
    )
    def get(self, request):
        today      = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())

        challenges = WeeklyChallenge.objects.filter(week_start=week_start)

        # Ensure UserWeeklyChallenge rows exist for all this week's challenges
        for ch in challenges:
            UserWeeklyChallenge.objects.get_or_create(user=request.user, challenge=ch)

        user_challenges = UserWeeklyChallenge.objects.filter(
            user=request.user, challenge__week_start=week_start
        ).select_related("challenge")

        reset_date     = week_start + timedelta(days=7)
        reset_dt       = timezone.make_aware(dt.datetime.combine(reset_date, dt.time.min))
        resets_in_secs = max(int((reset_dt - timezone.now()).total_seconds()), 0)

        return Response({
            "week_start":     week_start.isoformat(),
            "resets_in_secs": resets_in_secs,
            "challenges":     UserWeeklyChallengeSerializer(user_challenges, many=True).data,
        })


class LeaderboardView(APIView):
    """GET /api/v1/levels/leaderboard/ — friends ranked by total XP."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Friends leaderboard ranked by total XP",
        responses={200: LeaderboardEntrySerializer(many=True)},
    )
    def get(self, request):
        from django.contrib.auth import get_user_model
        from social.models import Friendship

        User = get_user_model()

        # Collect friend user ids (accepted friendships)
        friend_ids = set()
        for f in Friendship.objects.filter(
            requester=request.user, status="accepted"
        ).values_list("addressee_id", flat=True):
            friend_ids.add(f)
        for f in Friendship.objects.filter(
            addressee=request.user, status="accepted"
        ).values_list("requester_id", flat=True):
            friend_ids.add(f)

        # Include self
        all_ids = friend_ids | {request.user.id}

        level_profiles = (
            UserLevel.objects.filter(user_id__in=all_ids)
            .select_related("user")
            .order_by("-total_xp")
        )

        # Users without a profile yet get a synthetic empty entry
        profiled_ids  = {lp.user_id for lp in level_profiles}
        missing_users = User.objects.filter(id__in=all_ids - profiled_ids)

        entries = []
        rank    = 1
        for lp in level_profiles:
            u = lp.user
            entries.append({
                "rank":                   rank,
                "user_id":                u.id,
                "username":               u.username,
                "display_name":           u.get_full_name() or u.username,
                "avatar":                 u.avatar.url if getattr(u, "avatar", None) and u.avatar else None,
                "level":                  lp.level,
                "tier":                   lp.tier,
                "athlete_class":          lp.athlete_class,
                "athlete_class_display":  lp.get_athlete_class_display(),
                "total_xp":               lp.total_xp,
                "is_self":                u.id == request.user.id,
            })
            rank += 1

        for u in missing_users:
            entries.append({
                "rank":                   rank,
                "user_id":                u.id,
                "username":               u.username,
                "display_name":           u.get_full_name() or u.username,
                "avatar":                 None,
                "level":                  1,
                "tier":                   "rookie",
                "athlete_class":          "rookie",
                "athlete_class_display":  "Rookie",
                "total_xp":               0,
                "is_self":                u.id == request.user.id,
            })
            rank += 1

        return Response(LeaderboardEntrySerializer(entries, many=True).data)


class PrestigeView(APIView):
    """POST /api/v1/levels/prestige/ — prestige at level 100."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Prestige: reset to level 1 in exchange for a permanent XP multiplier bonus",
        responses={
            200: UserLevelSerializer,
            400: {"description": "Not at level 100 yet or max prestiges reached"},
        },
    )
    def post(self, request):
        MAX_PRESTIGES = 5
        try:
            user_level = UserLevel.objects.get(user=request.user)
        except UserLevel.DoesNotExist:
            return Response({"detail": "No level profile found."}, status=status.HTTP_400_BAD_REQUEST)

        if user_level.level < 100:
            return Response(
                {"detail": f"Prestige requires level 100. You are level {user_level.level}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user_level.prestige_count >= MAX_PRESTIGES:
            return Response(
                {"detail": "Maximum prestige level already reached."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_prestige = user_level.prestige_count + 1
        user_level.total_xp       = 0
        user_level.level          = 1
        user_level.tier           = UserLevel.Tier.ROOKIE
        user_level.prestige_count = new_prestige
        user_level.save()

        XPTransaction.objects.create(
            user        = request.user,
            amount      = 0,
            base_amount = 0,
            multiplier  = 1,
            reason      = f"Prestige {new_prestige} — reset to Level 1",
            source_type = "challenge",
        )

        return Response(UserLevelSerializer(user_level).data)
