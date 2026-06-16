from collections import defaultdict
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, ExpressionWrapper, F, FloatField, Sum
from django.db.models.functions import TruncDate, TruncWeek
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
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

    @extend_schema(
        summary="Estimated 1RM progression for a single exercise over time",
        parameters=[
            OpenApiParameter("exercise_id", int, required=True,
                             description="Exercise primary key"),
            OpenApiParameter("days", int, description="Look-back window (default 90, max 365)"),
        ],
        responses=inline_serializer(
            name="StrengthHistoryEntry",
            fields={
                "date":           serializers.DateField(),
                "estimated_1rm":  serializers.FloatField(),
                "max_weight":     serializers.FloatField(),
                "max_reps":       serializers.IntegerField(),
                "total_volume":   serializers.FloatField(),
            },
            many=True,
        ),
    )
    @action(detail=False, methods=["get"], url_path="strength-history")
    def strength_history(self, request):
        """
        Returns a time-series of estimated 1-rep-max (Epley formula) per date
        for the requested exercise.  Only completed, non-warmup sets with both
        weight and reps are included.
        """
        exercise_id = request.query_params.get("exercise_id")
        if not exercise_id:
            return Response(
                {"detail": "exercise_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            exercise_id = int(exercise_id)
            days = min(int(request.query_params.get("days", 90)), 365)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid parameters."}, status=status.HTTP_400_BAD_REQUEST)

        key = cache_keys.strength_history(request.user.id, exercise_id, days)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = (timezone.now() - timedelta(days=days)).date()
        sets = (
            ExerciseSet.objects
            .filter(
                workout_exercise__exercise_id=exercise_id,
                workout_exercise__workout__user=request.user,
                workout_exercise__workout__status=Workout.Status.COMPLETED,
                workout_exercise__workout__started_at__date__gte=since,
                is_warmup=False,
                completed=True,
                reps__gt=0,
                weight__isnull=False,
            )
            .annotate(date=TruncDate("workout_exercise__workout__started_at"))
            .values("date", "reps", "weight")
            .order_by("date")
        )

        # Epley 1RM: weight × (1 + reps / 30)
        by_date = defaultdict(lambda: {"estimated_1rm": 0.0, "max_weight": 0.0,
                                       "max_reps": 0, "total_volume": 0.0})
        for s in sets:
            w = float(s["weight"])
            r = int(s["reps"])
            d = s["date"].isoformat()
            orm = round(w * (1 + r / 30), 1)
            entry = by_date[d]
            entry["estimated_1rm"] = max(entry["estimated_1rm"], orm)
            entry["max_weight"]    = max(entry["max_weight"], w)
            entry["max_reps"]      = max(entry["max_reps"], r)
            entry["total_volume"]  += round(w * r, 1)

        payload = [{"date": d, **v} for d, v in sorted(by_date.items())]
        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)

    @extend_schema(
        summary="Weekly training volume broken down by primary muscle group",
        parameters=[
            OpenApiParameter("weeks", int, description="Number of weeks to look back (default 12, max 52)"),
        ],
        responses=inline_serializer(
            name="VolumeByMuscleEntry",
            fields={
                "week_start":   serializers.DateField(),
                "muscle_group": serializers.CharField(),
                "volume_kg":    serializers.FloatField(),
            },
            many=True,
        ),
    )
    @action(detail=False, methods=["get"], url_path="volume-by-muscle")
    def volume_by_muscle(self, request):
        """
        Returns weekly volume (kg × reps) per primary muscle group for the last
        N weeks.  Warmup sets are excluded.  Cardio/bodyweight exercises with no
        weight are excluded (zero-weight sets carry no load volume).
        """
        try:
            weeks = min(int(request.query_params.get("weeks", 12)), 52)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid weeks parameter."}, status=status.HTTP_400_BAD_REQUEST)

        key = cache_keys.volume_by_muscle(request.user.id, weeks)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = timezone.now() - timedelta(weeks=weeks)
        rows = (
            ExerciseSet.objects
            .filter(
                workout_exercise__workout__user=request.user,
                workout_exercise__workout__status=Workout.Status.COMPLETED,
                workout_exercise__workout__started_at__gte=since,
                is_warmup=False,
                completed=True,
                weight__gt=0,
                reps__gt=0,
            )
            .annotate(
                week=TruncWeek("workout_exercise__workout__started_at"),
                muscle=F("workout_exercise__exercise__primary_muscle"),
                vol=ExpressionWrapper(F("weight") * F("reps"), output_field=FloatField()),
            )
            .values("week", "muscle")
            .annotate(volume_kg=Sum("vol"))
            .order_by("week", "muscle")
        )

        payload = [
            {
                "week_start":   r["week"].date().isoformat(),
                "muscle_group": r["muscle"],
                "volume_kg":    round(float(r["volume_kg"]), 1),
            }
            for r in rows
        ]
        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)

    @extend_schema(
        summary="Daily workout activity for the calendar heatmap",
        parameters=[
            OpenApiParameter("days", int, description="Look-back window in days (default 365, max 730)"),
        ],
        responses=inline_serializer(
            name="ActivityHeatmapEntry",
            fields={
                "date":               serializers.DateField(),
                "workout_count":      serializers.IntegerField(),
                "total_volume_kg":    serializers.FloatField(),
                "total_duration_min": serializers.IntegerField(),
            },
            many=True,
        ),
    )
    @action(detail=False, methods=["get"], url_path="activity-heatmap")
    def activity_heatmap(self, request):
        """
        Returns one entry per day the user had at least one completed workout.
        Used to render a GitHub-style contribution grid in the frontend.
        """
        try:
            days = min(int(request.query_params.get("days", 365)), 730)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid days parameter."}, status=status.HTTP_400_BAD_REQUEST)

        key = cache_keys.activity_heatmap(request.user.id, days)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = (timezone.now() - timedelta(days=days)).date()

        # Per-day workout counts + duration
        workout_rows = (
            Workout.objects
            .filter(
                user=request.user,
                status=Workout.Status.COMPLETED,
                started_at__date__gte=since,
            )
            .annotate(date=TruncDate("started_at"))
            .values("date")
            .annotate(
                workout_count=Count("id"),
                total_duration_min=Sum("duration_min"),
            )
            .order_by("date")
        )

        # Per-day volume from sets (separate query — sets live on a child table)
        volume_rows = (
            ExerciseSet.objects
            .filter(
                workout_exercise__workout__user=request.user,
                workout_exercise__workout__status=Workout.Status.COMPLETED,
                workout_exercise__workout__started_at__date__gte=since,
                completed=True,
                weight__gt=0,
                reps__gt=0,
            )
            .annotate(date=TruncDate("workout_exercise__workout__started_at"))
            .values("date")
            .annotate(
                total_volume_kg=Sum(
                    ExpressionWrapper(F("weight") * F("reps"), output_field=FloatField())
                )
            )
        )

        volume_map = {r["date"]: round(float(r["total_volume_kg"]), 1) for r in volume_rows}

        payload = [
            {
                "date":               r["date"].isoformat(),
                "workout_count":      r["workout_count"],
                "total_volume_kg":    volume_map.get(r["date"], 0.0),
                "total_duration_min": r["total_duration_min"] or 0,
            }
            for r in workout_rows
        ]
        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)

    @extend_schema(
        request=None, responses={200: WorkoutSerializer},
        summary="Reset calories_burned to None and re-estimate from set data",
    )
    @action(detail=True, methods=["post"], url_path="recalculate-calories")
    def recalculate_calories(self, request, pk=None):
        """
        Clears the current calories_burned and re-runs the MET-based
        estimation from the workout's exercise sets. Call this after
        editing sets, or when the user wants to discard a manual entry.
        """
        from .services import estimate_calories
        workout = self.get_object()
        Workout.objects.filter(pk=workout.pk).update(calories_burned=None)
        workout.calories_burned = None
        estimate = estimate_calories(workout)
        if estimate is not None:
            Workout.objects.filter(pk=workout.pk).update(calories_burned=estimate)
            workout.calories_burned = estimate
        return Response(self.get_serializer(workout).data)


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
