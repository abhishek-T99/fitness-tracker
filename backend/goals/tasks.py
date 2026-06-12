"""Daily goal-deadline check."""
import logging

from celery import shared_task
from django.utils import timezone

from .models import Goal

logger = logging.getLogger(__name__)


@shared_task(name="goals.mark_expired_goals", ignore_result=True)
def mark_expired_goals():
    """Auto-mark active goals whose deadline has passed.

    If the user already reached the target we mark it `achieved`; otherwise
    we leave it `active` but bump `notes` so the UI can surface it. We
    intentionally do not delete or abandon — that's the user's call.
    """
    today = timezone.localdate()
    overdue = Goal.objects.filter(status=Goal.Status.ACTIVE, deadline__lt=today)
    achieved = 0
    for goal in overdue:
        if goal.target_value and goal.current_value >= goal.target_value:
            goal.status = Goal.Status.ACHIEVED
            goal.save(update_fields=["status", "updated_at"])
            achieved += 1
    if achieved:
        logger.info("mark_expired_goals: %d goals auto-marked achieved", achieved)
    return achieved
