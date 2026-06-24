"""Celery tasks for the achievements app."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Streak

logger = logging.getLogger(__name__)


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
