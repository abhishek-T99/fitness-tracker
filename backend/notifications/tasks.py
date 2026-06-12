"""Celery tasks for time-based notifications (streak at risk, goal deadlines)."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def notify_streak_at_risk():
    """
    Notify users whose active streak will be broken if they don't
    log a workout today. Runs once daily (configured in CELERY_BEAT_SCHEDULE).
    One notification per user per day — skips if already sent today.
    """
    from achievements.models import Streak
    from .models import Notification

    today = timezone.localdate()
    at_risk = (
        Streak.objects
        .filter(current_days__gt=0)
        .exclude(last_workout_date=today)
        .select_related("user")
    )
    fired = 0
    for streak in at_risk:
        already_sent = Notification.objects.filter(
            recipient=streak.user,
            notif_type=Notification.Type.STREAK_AT_RISK,
            created_at__date=today,
        ).exists()
        if already_sent:
            continue
        Notification.objects.create(
            recipient=streak.user,
            notif_type=Notification.Type.STREAK_AT_RISK,
            message=(
                f"Your {streak.current_days}-day streak is at risk! "
                "Log a workout today to keep it alive. 🔥"
            ),
            target_url="/workouts",
        )
        fired += 1
    if fired:
        logger.info("notify_streak_at_risk: created %d notifications", fired)
    return fired


@shared_task(ignore_result=True)
def notify_goal_deadlines():
    """
    Notify users about active goals whose deadline is exactly 3 days away.
    One notification per goal per day.
    """
    from goals.models import Goal
    from .models import Notification

    three_days_out = timezone.localdate() + timedelta(days=3)
    today = timezone.localdate()
    upcoming = (
        Goal.objects
        .filter(status="active", deadline=three_days_out)
        .select_related("user")
    )
    fired = 0
    for goal in upcoming:
        already_sent = Notification.objects.filter(
            recipient=goal.user,
            notif_type=Notification.Type.GOAL_DEADLINE,
            created_at__date=today,
        ).exists()
        if already_sent:
            continue
        Notification.objects.create(
            recipient=goal.user,
            notif_type=Notification.Type.GOAL_DEADLINE,
            message=(
                f"'{goal.title}' deadline is in 3 days. "
                f"You're at {goal.progress_percent:.0f}% — keep pushing! 🎯"
            ),
            target_url="/goals",
        )
        fired += 1
    if fired:
        logger.info("notify_goal_deadlines: created %d notifications", fired)
    return fired
