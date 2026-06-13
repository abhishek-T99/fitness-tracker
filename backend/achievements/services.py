"""Achievement + streak evaluation triggered after a workout is completed."""
from datetime import timedelta

from django.db.models import Sum

from .models import Achievement, Streak, UserAchievement


def _update_streak(user, workout_date) -> Streak:
    streak, _ = Streak.objects.get_or_create(user=user)
    if streak.last_workout_date == workout_date:
        return streak
    if streak.last_workout_date and streak.last_workout_date == workout_date - timedelta(days=1):
        streak.current_days += 1
    else:
        streak.current_days = 1
    streak.longest_days = max(streak.longest_days, streak.current_days)
    streak.last_workout_date = workout_date
    streak.save()
    return streak


def _unlock(user, achievement: Achievement):
    UserAchievement.objects.get_or_create(user=user, achievement=achievement)


def evaluate_after_workout(workout):
    """Re-evaluate all achievement criteria for the workout's user."""
    # Local imports to avoid circular module load at startup.
    from workouts.models import Workout
    from goals.models import Goal

    user = workout.user
    streak = _update_streak(user, workout.started_at.date())

    completed_qs = Workout.objects.filter(user=user, status=Workout.Status.COMPLETED)

    agg = completed_qs.aggregate(
        total_minutes=Sum("duration_min"),
        total_calories=Sum("calories_burned"),
        total_distance=Sum("distance_km"),
    )

    total_workouts = completed_qs.count()
    total_minutes  = agg["total_minutes"]  or 0
    total_calories = agg["total_calories"] or 0
    total_distance = int(agg["total_distance"] or 0)

    # Time-of-day counts (based on UTC hour of started_at)
    early_bird_count = completed_qs.filter(started_at__hour__lt=7).count()
    night_owl_count  = completed_qs.filter(started_at__hour__gte=21).count()

    # Total lifted volume — must iterate because total_volume is a @property
    total_volume = sum(
        w.total_volume
        for w in completed_qs.prefetch_related("exercises__sets")
    )

    # Goals achieved — evaluated opportunistically on every workout save
    goals_completed = Goal.objects.filter(user=user, status="achieved").count()

    metrics = {
        Achievement.Kind.WORKOUT_COUNT:   total_workouts,
        Achievement.Kind.STREAK_DAYS:     streak.current_days,
        Achievement.Kind.VOLUME_TOTAL:    int(total_volume),
        Achievement.Kind.WORKOUT_MINUTES: total_minutes,
        Achievement.Kind.CALORIE_BURN:    total_calories,
        Achievement.Kind.DISTANCE_KM:     total_distance,
        Achievement.Kind.EARLY_BIRD:      early_bird_count,
        Achievement.Kind.NIGHT_OWL:       night_owl_count,
        Achievement.Kind.GOALS_COMPLETED: goals_completed,
    }

    for kind, value in metrics.items():
        for ach in Achievement.objects.filter(kind=kind, threshold__lte=value):
            _unlock(user, ach)
