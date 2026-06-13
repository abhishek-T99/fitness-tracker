from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Max, Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from fitness_tracker import cache_keys

from .models import ExerciseSet, Routine, Workout, WorkoutExercise
from .serializers import RoutineSerializer, WorkoutSerializer


@extend_schema(tags=["Workouts"])
@extend_schema_view(
    stats=extend_schema(
        summary="Aggregated workout statistics",
        responses=inline_serializer(
            name="WorkoutStats",
            fields={
                "this_week": inline_serializer(
                    name="WorkoutWeeklyStats",
                    fields={
                        "workouts": serializers.IntegerField(),
                        "minutes": serializers.IntegerField(),
                        "calories": serializers.IntegerField(),
                    },
                ),
                "last_30_days": serializers.IntegerField(),
                "daily_counts": serializers.DictField(child=serializers.IntegerField()),
            },
        ),
    ),
)
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


@extend_schema(tags=["Workouts"])
class RoutineViewSet(viewsets.ModelViewSet):
    serializer_class = RoutineSerializer
    filterset_fields = ["is_public"]
    ordering_fields = ["name", "updated_at", "order"]

    def get_queryset(self):
        return (
            Routine.objects.filter(user=self.request.user)
            .prefetch_related("items__exercise")
        )

    def perform_create(self, serializer):
        last = self.get_queryset().order_by("order").last()
        next_order = (last.order + 1) if last else 0
        # RoutineSerializer.create() already sets user from context; pass order only.
        serializer.save(order=next_order)

    @extend_schema(
        request={"application/json": {"type": "array", "items": {"type": "object",
            "properties": {"id": {"type": "integer"}, "order": {"type": "integer"}}}}},
        responses={200: None},
        summary="Bulk-update the display order of routines",
    )
    @action(detail=False, methods=["post"])
    def reorder(self, request):
        from .models import Routine as _Routine
        qs = self.get_queryset()
        updates = []
        for item in request.data:
            try:
                obj = qs.get(pk=item["id"])
                obj.order = int(item["order"])
                updates.append(obj)
            except (_Routine.DoesNotExist, KeyError, TypeError, ValueError):
                pass
        _Routine.objects.bulk_update(updates, ["order"])
        return Response({"detail": f"Reordered {len(updates)} routines."})


@extend_schema(tags=["Workouts"])
class ExerciseHistoryView(APIView):
    """
    GET /api/v1/workouts/exercise-history/?exercise_ids=1,2,3

    Returns, for each exercise ID, the user's most recent completed sets
    and their personal best (heaviest completed set).

    Used by the Active Workout Session to display previous performance and
    drive progressive-overload suggestions on the client.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        raw = request.query_params.get("exercise_ids", "").strip()
        if not raw:
            return Response(
                {"detail": "exercise_ids query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            exercise_ids = [int(x) for x in raw.split(",") if x.strip()]
        except ValueError:
            return Response(
                {"detail": "exercise_ids must be comma-separated integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not exercise_ids:
            return Response(
                {"detail": "exercise_ids must contain at least one ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = {}
        for ex_id in exercise_ids:
            result[str(ex_id)] = self._history_for_exercise(request.user, ex_id)

        return Response(result)

    def _history_for_exercise(self, user, exercise_id):
        # Find the most recent workout for this user that contains this exercise
        latest_we = (
            WorkoutExercise.objects
            .filter(
                workout__user=user,
                workout__status=Workout.Status.COMPLETED,
                exercise_id=exercise_id,
            )
            .select_related("workout")
            .order_by("-workout__started_at")
            .first()
        )

        if not latest_we:
            return None

        # Completed sets from that workout for this exercise
        completed_sets = (
            ExerciseSet.objects
            .filter(workout_exercise=latest_we, completed=True)
            .order_by("set_number")
            .values("set_number", "reps", "weight", "rpe", "duration_sec", "distance_m")
        )

        # Personal best: heaviest single completed set with reps > 0
        pb = (
            ExerciseSet.objects
            .filter(
                workout_exercise__workout__user=user,
                workout_exercise__workout__status=Workout.Status.COMPLETED,
                workout_exercise__exercise_id=exercise_id,
                completed=True,
                reps__gt=0,
                weight__isnull=False,
            )
            .order_by("-weight", "-reps")
            .values("reps", "weight")
            .first()
        )

        return {
            "exercise_id": exercise_id,
            "last_session": {
                "workout_started_at": latest_we.workout.started_at,
                "sets": list(completed_sets),
            },
            "personal_best": pb,
        }
