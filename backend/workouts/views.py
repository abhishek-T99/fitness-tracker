from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from fitness_tracker import cache_keys

from .models import Routine, Workout
from .serializers import RoutineSerializer, WorkoutSerializer


class WorkoutViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutSerializer
    filterset_fields = ["status", "routine"]
    ordering_fields = ["started_at", "duration_min", "calories_burned"]
    ordering = ["-started_at"]

    def get_queryset(self):
        return (
            Workout.objects.filter(user=self.request.user)
            .prefetch_related("exercises__sets", "exercises__exercise")
            .select_related("routine")
        )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Aggregated workout stats — heavy enough to cache per-user.

        Invalidated automatically on Workout / WorkoutExercise / ExerciseSet
        save & delete via workouts.signals.
        """
        key = cache_keys.workout_stats(request.user.id)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        now = timezone.now()
        since = now - timedelta(days=30)
        qs = self.get_queryset().filter(started_at__gte=since)

        weekly = (
            self.get_queryset()
            .filter(started_at__gte=now - timedelta(days=7))
            .aggregate(
                count=Count("id"),
                total_minutes=Sum("duration_min"),
                total_calories=Sum("calories_burned"),
            )
        )

        by_day = {}
        recent = self.get_queryset().filter(started_at__gte=now - timedelta(days=14))
        for w in recent:
            day_key = w.started_at.date().isoformat()
            by_day[day_key] = by_day.get(day_key, 0) + 1

        payload = {
            "this_week": {
                "workouts": weekly["count"] or 0,
                "minutes": weekly["total_minutes"] or 0,
                "calories": weekly["total_calories"] or 0,
            },
            "last_30_days": qs.count(),
            "daily_counts": by_day,
        }
        cache.set(key, payload, cache_keys.WORKOUT_STATS_TTL)
        return Response(payload)


class RoutineViewSet(viewsets.ModelViewSet):
    serializer_class = RoutineSerializer
    filterset_fields = ["is_public"]
    ordering_fields = ["name", "updated_at"]

    def get_queryset(self):
        return (
            Routine.objects.filter(user=self.request.user)
            .prefetch_related("items__exercise")
        )
