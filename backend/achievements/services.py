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
    """Re-evaluate achievement criteria for the workout's user."""
    user = workout.user
    streak = _update_streak(user, workout.started_at.date())

    from workouts.models import Workout  # local import to avoid circular load

    total_workouts = Workout.objects.filter(
        user=user, status=Workout.Status.COMPLETED
    ).count()

    total_minutes = (
        Workout.objects.filter(user=user, status=Workout.Status.COMPLETED).aggregate(
            total=Sum("duration_min")
        )["total"]
        or 0
    )

    # Total volume across all workouts.
    total_volume = 0.0
    for w in Workout.objects.filter(user=user, status=Workout.Status.COMPLETED):
        total_volume += w.total_volume

    metrics = {
        Achievement.Kind.WORKOUT_COUNT: total_workouts,
        Achievement.Kind.STREAK_DAYS: streak.current_days,
        Achievement.Kind.VOLUME_TOTAL: int(total_volume),
        Achievement.Kind.WORKOUT_MINUTES: total_minutes,
    }

    for kind, value in metrics.items():
        eligible = Achievement.objects.filter(kind=kind, threshold__lte=value)
        for ach in eligible:
            _unlock(user, ach)
