"""Celery tasks for reminders — dispatched by Beat every minute."""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from celery import shared_task
from django.utils import timezone

from .models import Reminder

logger = logging.getLogger(__name__)

WEEKDAY_CODES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _user_now(reminder: Reminder) -> datetime:
    tz_name = getattr(reminder.user, "profile", None)
    tz_name = getattr(tz_name, "timezone", None) or "UTC"
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    return timezone.now().astimezone(tz)


@shared_task(name="reminders.dispatch_due_reminders", ignore_result=True)
def dispatch_due_reminders():
    """Find reminders whose local trigger time matches now (per user TZ) and fire them.

    Hook this into a real delivery channel (push, email, websocket fan-out, etc.).
    For now we log each fired reminder so the wiring is observable end-to-end.
    """
    active = Reminder.objects.select_related("user__profile").filter(is_active=True)
    fired = 0
    for reminder in active:
        local_now = _user_now(reminder)
        today_code = WEEKDAY_CODES[local_now.weekday()]
        if reminder.days_of_week and today_code not in reminder.days_of_week:
            continue
        if (
            local_now.hour == reminder.time_of_day.hour
            and local_now.minute == reminder.time_of_day.minute
        ):
            deliver_reminder.delay(reminder.id)
            fired += 1
    if fired:
        logger.info("dispatch_due_reminders: queued %d notifications", fired)
    return fired


@shared_task(name="reminders.deliver_reminder", ignore_result=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def deliver_reminder(reminder_id: int):
    """Single-reminder delivery. Swap in push/email/webhook here."""
    try:
        reminder = Reminder.objects.select_related("user").get(pk=reminder_id, is_active=True)
    except Reminder.DoesNotExist:
        return
    logger.info(
        "REMINDER → user=%s type=%s title=%r",
        reminder.user.username,
        reminder.reminder_type,
        reminder.title,
    )
