"""Celery tasks for the achievements app."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Streak

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def evaluate_workout_achievements(workout_id: int):
    """Re-evaluate achievements + streak for a workout's owner.

    Heavy because it aggregates total volume across every completed workout;
    running it inline blocked the API response on workout save.
    """
    from workouts.models import Workout

    from . import services

    try:
        workout = Workout.objects.select_related("user").get(pk=workout_id)
    except Workout.DoesNotExist:
        logger.warning("evaluate_workout_achievements: workout %s missing", workout_id)
        return
    services.evaluate_after_workout(workout)


@shared_task(ignore_result=True)
def decay_inactive_streaks():
    """Reset streaks for users who didn't train yesterday OR today.

    Runs once per day. A streak is "current" only if the user trained either
    yesterday or today; otherwise it drops to zero (longest is preserved).
    """
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    stale = Streak.objects.exclude(last_workout_date__in=[today, yesterday]).filter(
        current_days__gt=0
    )
    count = stale.update(current_days=0)
    if count:
        logger.info("decay_inactive_streaks: reset %d streaks", count)
    return count
