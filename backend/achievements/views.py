from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from fitness_tracker import cache_keys

from .models import Achievement, Streak, UserAchievement
from .serializers import (
    AchievementSerializer,
    StreakSerializer,
    UserAchievementSerializer,
)


@extend_schema(tags=["Achievements"])
class AchievementCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    """Static catalog — cached for 24h, invalidated on Achievement save."""

    serializer_class = AchievementSerializer
    queryset = Achievement.objects.all()
    # The catalog is a small, static dataset (< 50 rows) that the frontend
    # must receive in full to render the badge grid correctly.  Pagination
    # would cause the frontend to only see page 1, hiding earned badges that
    # happen to fall on later pages.
    pagination_class = None

    def list(self, request, *args, **kwargs):
        cached = cache.get(cache_keys.ACHIEVEMENT_CATALOG)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_keys.ACHIEVEMENT_CATALOG, response.data, cache_keys.ACHIEVEMENT_CATALOG_TTL)
        return response


@extend_schema(tags=["Achievements"])
class UserAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserAchievementSerializer
    # Return all unlocked badges in one response so the frontend ID lookup
    # works regardless of how many badges a user has earned.
    pagination_class = None

    def get_queryset(self):
        return UserAchievement.objects.filter(user=self.request.user).select_related("achievement")


@extend_schema(tags=["Achievements"], responses=StreakSerializer)
class StreakView(APIView):
    def get(self, request):
        key = cache_keys.streak(request.user.id)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        streak, _ = Streak.objects.get_or_create(user=request.user)
        data = StreakSerializer(streak).data
        cache.set(key, data, cache_keys.STREAK_TTL)
        return Response(data)
