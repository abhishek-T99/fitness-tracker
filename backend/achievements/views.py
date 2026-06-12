from django.core.cache import cache
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


class AchievementCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    """Static catalog — cached for 24h, invalidated on Achievement save."""

    serializer_class = AchievementSerializer
    queryset = Achievement.objects.all()

    def list(self, request, *args, **kwargs):
        cached = cache.get(cache_keys.ACHIEVEMENT_CATALOG)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_keys.ACHIEVEMENT_CATALOG, response.data, cache_keys.ACHIEVEMENT_CATALOG_TTL)
        return response


class UserAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserAchievementSerializer

    def get_queryset(self):
        return UserAchievement.objects.filter(user=self.request.user).select_related("achievement")


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
