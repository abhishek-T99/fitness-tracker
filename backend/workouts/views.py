from collections import defaultdict
from datetime import date, timedelta

from django.core.cache import cache
from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, Q, Sum
from django.db.models.functions import ExtractIsoWeekDay, TruncDate, TruncWeek
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
            Workout.objects.for_user(self.request.user)
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
        # Lightweight base queryset — aggregation never needs exercises/sets prefetched.
        base_qs = Workout.objects.filter(user=request.user)

        weekly = base_qs.filter(started_at__gte=now - timedelta(days=7)).aggregate(
            count=Count("id"),
            total_minutes=Sum("duration_min"),
            total_calories=Sum("calories_burned"),
        )
        last_30 = base_qs.filter(started_at__gte=now - timedelta(days=30)).count()
        # Single grouped query instead of a Python loop over individual rows.
        by_day_rows = (
            base_qs.filter(started_at__gte=now - timedelta(days=14))
            .annotate(day=TruncDate("started_at"))
            .values("day")
            .annotate(cnt=Count("id"))
            .order_by()
        )
        by_day = {r["day"].isoformat(): r["cnt"] for r in by_day_rows}

        payload = {
            "this_week": {
                "workouts": weekly["count"] or 0,
                "minutes": weekly["total_minutes"] or 0,
                "calories": weekly["total_calories"] or 0,
            },
            "last_30_days": last_30,
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

    # ── New insight endpoints ──────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="personal-records")
    def personal_records(self, request):
        """
        All-time PRs (estimated 1RM, max weight, max reps) per exercise the user
        has trained in the last 730 days, sorted by estimated 1RM descending.
        Includes a flag when any PR was set within the last 30 days.
        """
        key = cache_keys.personal_records(request.user.id)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = timezone.now() - timedelta(days=730)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)

        sets = (
            ExerciseSet.objects
            .filter(
                workout_exercise__workout__user=request.user,
                workout_exercise__workout__status=Workout.Status.COMPLETED,
                workout_exercise__workout__started_at__gte=since,
                is_warmup=False,
                completed=True,
                reps__gt=0,
                weight__isnull=False,
            )
            .annotate(
                session_date=TruncDate("workout_exercise__workout__started_at"),
                ex_id=F("workout_exercise__exercise_id"),
                ex_name=F("workout_exercise__exercise__name"),
                ex_muscle=F("workout_exercise__exercise__primary_muscle"),
            )
            .values("session_date", "ex_id", "ex_name", "ex_muscle", "reps", "weight")
            .order_by("session_date")
        )

        by_exercise = {}
        for s in sets:
            w = float(s["weight"])
            r = int(s["reps"])
            d_iso = s["session_date"].isoformat()
            ex_id = s["ex_id"]
            one_rm = round(w * (1 + r / 30), 1)

            if ex_id not in by_exercise:
                by_exercise[ex_id] = {
                    "exercise_id": ex_id,
                    "exercise_name": s["ex_name"],
                    "primary_muscle": s["ex_muscle"],
                    "pr_1rm": 0.0, "pr_1rm_date": None,
                    "pr_weight": 0.0, "pr_weight_date": None,
                    "pr_reps": 0, "pr_reps_date": None,
                }

            entry = by_exercise[ex_id]
            if one_rm > entry["pr_1rm"]:
                entry["pr_1rm"] = one_rm
                entry["pr_1rm_date"] = d_iso
            if w > entry["pr_weight"]:
                entry["pr_weight"] = w
                entry["pr_weight_date"] = d_iso
            if r > entry["pr_reps"]:
                entry["pr_reps"] = r
                entry["pr_reps_date"] = d_iso

        for entry in by_exercise.values():
            entry["has_recent_pr"] = any(
                entry[field] and date.fromisoformat(entry[field]) >= thirty_days_ago
                for field in ("pr_1rm_date", "pr_weight_date", "pr_reps_date")
            )

        payload = sorted(by_exercise.values(), key=lambda x: x["pr_1rm"], reverse=True)
        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="overload-streaks")
    def overload_streaks(self, request):
        """
        For each exercise trained in the last 365 days, counts how many consecutive
        sessions (from most recent backwards) showed a higher estimated 1RM than the
        previous session.  Only exercises with an active streak (≥1 improvement) are
        returned, sorted by streak length descending.
        """
        key = cache_keys.overload_streaks(request.user.id)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = timezone.now() - timedelta(days=365)

        sets = (
            ExerciseSet.objects
            .filter(
                workout_exercise__workout__user=request.user,
                workout_exercise__workout__status=Workout.Status.COMPLETED,
                workout_exercise__workout__started_at__gte=since,
                is_warmup=False,
                completed=True,
                reps__gt=0,
                weight__isnull=False,
            )
            .annotate(
                session_date=TruncDate("workout_exercise__workout__started_at"),
                ex_id=F("workout_exercise__exercise_id"),
                ex_name=F("workout_exercise__exercise__name"),
            )
            .values("session_date", "ex_id", "ex_name", "reps", "weight")
            .order_by("session_date")
        )

        # Best 1RM per exercise per session date
        by_exercise = {}
        for s in sets:
            ex_id = s["ex_id"]
            d_iso = s["session_date"].isoformat()
            orm = round(float(s["weight"]) * (1 + int(s["reps"]) / 30), 1)

            if ex_id not in by_exercise:
                by_exercise[ex_id] = {"name": s["ex_name"], "sessions": {}}

            existing = by_exercise[ex_id]["sessions"].get(d_iso, 0.0)
            by_exercise[ex_id]["sessions"][d_iso] = max(existing, orm)

        result = []
        for ex_id, data in by_exercise.items():
            sessions = sorted(data["sessions"].items(), reverse=True)  # most recent first
            if len(sessions) < 2:
                continue

            streak = 0
            streak_since = None
            for i in range(len(sessions) - 1):
                curr_orm = sessions[i][1]
                prev_orm = sessions[i + 1][1]
                if curr_orm > prev_orm:
                    streak += 1
                    streak_since = sessions[i + 1][0]
                else:
                    break

            if streak > 0:
                result.append({
                    "exercise_id": ex_id,
                    "exercise_name": data["name"],
                    "current_streak": streak,
                    "streak_since": streak_since,
                    "last_session_date": sessions[0][0],
                    "last_1rm": sessions[0][1],
                })

        payload = sorted(result, key=lambda x: x["current_streak"], reverse=True)
        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="rpe-trend")
    def rpe_trend(self, request):
        """Weekly average RPE (perceived exertion) trend from workout-level RPE ratings."""
        try:
            days = min(int(request.query_params.get("days", 90)), 365)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid days parameter."}, status=status.HTTP_400_BAD_REQUEST)

        key = cache_keys.rpe_trend(request.user.id, days)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = timezone.now() - timedelta(days=days)
        rows = (
            Workout.objects
            .filter(
                user=request.user,
                status=Workout.Status.COMPLETED,
                started_at__gte=since,
                perceived_exertion__isnull=False,
            )
            .annotate(week=TruncWeek("started_at"))
            .values("week")
            .annotate(avg_rpe=Avg("perceived_exertion"), workout_count=Count("id"))
            .order_by("week")
        )

        payload = [
            {
                "week_start": r["week"].date().isoformat(),
                "avg_rpe": round(float(r["avg_rpe"]), 1),
                "workout_count": r["workout_count"],
            }
            for r in rows
        ]
        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="duration-trend")
    def duration_trend(self, request):
        """Weekly average and total session duration trend."""
        try:
            weeks = min(int(request.query_params.get("weeks", 12)), 52)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid weeks parameter."}, status=status.HTTP_400_BAD_REQUEST)

        key = cache_keys.duration_trend(request.user.id, weeks)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = timezone.now() - timedelta(weeks=weeks)
        rows = (
            Workout.objects
            .filter(
                user=request.user,
                status=Workout.Status.COMPLETED,
                started_at__gte=since,
                duration_min__isnull=False,
            )
            .annotate(week=TruncWeek("started_at"))
            .values("week")
            .annotate(
                avg_duration_min=Avg("duration_min"),
                total_duration_min=Sum("duration_min"),
                workout_count=Count("id"),
            )
            .order_by("week")
        )

        payload = [
            {
                "week_start": r["week"].date().isoformat(),
                "avg_duration_min": round(float(r["avg_duration_min"]), 1),
                "total_duration_min": r["total_duration_min"] or 0,
                "workout_count": r["workout_count"],
            }
            for r in rows
        ]
        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="session-density")
    def session_density(self, request):
        """
        Weekly workout density: total volume (kg) divided by total duration (min).
        Weeks where no workout has a duration_min value are excluded.
        """
        try:
            weeks = min(int(request.query_params.get("weeks", 12)), 52)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid weeks parameter."}, status=status.HTTP_400_BAD_REQUEST)

        key = cache_keys.session_density(request.user.id, weeks)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = timezone.now() - timedelta(weeks=weeks)

        volume_rows = (
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
            .annotate(week=TruncWeek("workout_exercise__workout__started_at"))
            .values("week")
            .annotate(
                total_volume=Sum(ExpressionWrapper(F("weight") * F("reps"), output_field=FloatField()))
            )
        )
        volume_map = {r["week"]: float(r["total_volume"]) for r in volume_rows}

        duration_rows = (
            Workout.objects
            .filter(
                user=request.user,
                status=Workout.Status.COMPLETED,
                started_at__gte=since,
                duration_min__isnull=False,
            )
            .annotate(week=TruncWeek("started_at"))
            .values("week")
            .annotate(total_duration=Sum("duration_min"))
            .order_by("week")
        )

        payload = []
        for r in duration_rows:
            week = r["week"]
            total_vol = volume_map.get(week, 0.0)
            total_dur = r["total_duration"] or 0
            density = round(total_vol / total_dur, 1) if total_dur > 0 else 0.0
            payload.append({
                "week_start": week.date().isoformat(),
                "density_kg_per_min": density,
                "total_volume_kg": round(total_vol, 1),
                "total_duration_min": total_dur,
            })

        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="cardio-summary")
    def cardio_summary(self, request):
        """
        Cardio-specific summary: total distance, session count, avg heart rate,
        plus weekly distance and HR trend.  Includes workouts where distance_km > 0
        or avg_hr_bpm is recorded.
        """
        try:
            days = min(int(request.query_params.get("days", 90)), 365)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid days parameter."}, status=status.HTTP_400_BAD_REQUEST)

        key = cache_keys.cardio_summary(request.user.id, days)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = timezone.now() - timedelta(days=days)
        cardio_qs = Workout.objects.filter(
            user=request.user,
            status=Workout.Status.COMPLETED,
            started_at__gte=since,
        ).filter(Q(distance_km__gt=0) | Q(avg_hr_bpm__isnull=False))

        agg = cardio_qs.aggregate(
            total_distance=Sum("distance_km"),
            total_sessions=Count("id"),
            avg_hr=Avg("avg_hr_bpm"),
        )

        weekly_distance = list(
            cardio_qs
            .filter(distance_km__gt=0)
            .annotate(week=TruncWeek("started_at"))
            .values("week")
            .annotate(distance_km=Sum("distance_km"), session_count=Count("id"))
            .order_by("week")
            .values_list("week", "distance_km", "session_count")
        )

        hr_trend = list(
            cardio_qs
            .filter(avg_hr_bpm__isnull=False)
            .annotate(week=TruncWeek("started_at"))
            .values("week")
            .annotate(avg_hr_bpm=Avg("avg_hr_bpm"))
            .order_by("week")
            .values_list("week", "avg_hr_bpm")
        )

        avg_hr = agg["avg_hr"]
        payload = {
            "total_distance_km": round(float(agg["total_distance"] or 0), 1),
            "total_sessions": agg["total_sessions"],
            "avg_hr_bpm": round(float(avg_hr), 0) if avg_hr is not None else None,
            "weekly_distance": [
                {
                    "week_start": week.date().isoformat(),
                    "distance_km": round(float(dist), 1),
                    "session_count": cnt,
                }
                for week, dist, cnt in weekly_distance
            ],
            "hr_trend": [
                {
                    "week_start": week.date().isoformat(),
                    "avg_hr_bpm": round(float(hr), 0),
                }
                for week, hr in hr_trend
            ],
        }
        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="dow-heatmap")
    def dow_heatmap(self, request):
        """
        Workout count and average volume per ISO day of week (1=Mon … 7=Sun).
        Always returns all 7 days so the frontend can render a complete grid.
        """
        try:
            weeks = min(int(request.query_params.get("weeks", 12)), 52)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid weeks parameter."}, status=status.HTTP_400_BAD_REQUEST)

        key = cache_keys.dow_heatmap(request.user.id, weeks)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = timezone.now() - timedelta(weeks=weeks)

        workout_rows = (
            Workout.objects
            .filter(user=request.user, status=Workout.Status.COMPLETED, started_at__gte=since)
            .annotate(dow=ExtractIsoWeekDay("started_at"))
            .values("dow")
            .annotate(workout_count=Count("id"))
        )
        count_map = {r["dow"]: r["workout_count"] for r in workout_rows}

        volume_rows = (
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
            .annotate(dow=ExtractIsoWeekDay("workout_exercise__workout__started_at"))
            .values("dow")
            .annotate(
                total_volume=Sum(ExpressionWrapper(F("weight") * F("reps"), output_field=FloatField()))
            )
        )
        volume_map = {r["dow"]: float(r["total_volume"]) for r in volume_rows}

        DAY_NAMES = {
            1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
            5: "Friday", 6: "Saturday", 7: "Sunday",
        }

        payload = []
        for dow in range(1, 8):
            wc = count_map.get(dow, 0)
            vol = volume_map.get(dow, 0.0)
            payload.append({
                "day_of_week": dow,
                "day_name": DAY_NAMES[dow],
                "workout_count": wc,
                "total_volume_kg": round(vol, 1),
                "avg_volume_kg": round(vol / wc, 1) if wc > 0 else 0.0,
            })

        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="muscle-balance")
    def muscle_balance(self, request):
        """
        Push/pull and upper/lower volume ratios plus per-muscle volume share,
        computed from weighted working sets in the last N weeks.
        """
        try:
            weeks = min(int(request.query_params.get("weeks", 8)), 52)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid weeks parameter."}, status=status.HTTP_400_BAD_REQUEST)

        key = cache_keys.muscle_balance(request.user.id, weeks)
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
            .annotate(muscle=F("workout_exercise__exercise__primary_muscle"))
            .values("muscle")
            .annotate(
                volume_kg=Sum(ExpressionWrapper(F("weight") * F("reps"), output_field=FloatField()))
            )
        )

        PUSH_MUSCLES = {"chest", "shoulders", "triceps"}
        PULL_MUSCLES = {"back", "biceps", "forearms"}
        UPPER_MUSCLES = {"chest", "back", "shoulders", "biceps", "triceps", "forearms"}
        LOWER_MUSCLES = {"quads", "hamstrings", "glutes", "calves"}

        muscle_volumes = {r["muscle"]: round(float(r["volume_kg"]), 1) for r in rows}
        total_volume = sum(muscle_volumes.values())

        push_vol = sum(muscle_volumes.get(m, 0.0) for m in PUSH_MUSCLES)
        pull_vol = sum(muscle_volumes.get(m, 0.0) for m in PULL_MUSCLES)
        upper_vol = sum(muscle_volumes.get(m, 0.0) for m in UPPER_MUSCLES)
        lower_vol = sum(muscle_volumes.get(m, 0.0) for m in LOWER_MUSCLES)

        payload = {
            "push_pull_ratio": round(push_vol / pull_vol, 2) if pull_vol > 0 else None,
            "upper_lower_ratio": round(upper_vol / lower_vol, 2) if lower_vol > 0 else None,
            "push_volume_kg": round(push_vol, 1),
            "pull_volume_kg": round(pull_vol, 1),
            "upper_volume_kg": round(upper_vol, 1),
            "lower_volume_kg": round(lower_vol, 1),
            "total_volume_kg": round(total_volume, 1),
            "muscle_shares": [
                {
                    "muscle": muscle,
                    "volume_kg": vol,
                    "share_pct": round(vol / total_volume * 100, 1) if total_volume > 0 else 0.0,
                }
                for muscle, vol in sorted(muscle_volumes.items(), key=lambda x: x[1], reverse=True)
            ],
        }
        cache.set(key, payload, cache_keys.PROGRESS_TTL)
        return Response(payload)


@extend_schema(tags=["Workouts"])
class RoutineViewSet(viewsets.ModelViewSet):
    serializer_class = RoutineSerializer
    filterset_fields = ["is_public"]
    ordering_fields = ["name", "updated_at", "order"]

    def get_queryset(self):
        return (
            Routine.objects.for_user(self.request.user)
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
