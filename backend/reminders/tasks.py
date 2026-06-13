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


def _is_due_once(reminder: Reminder, local_now: datetime) -> bool:
    """True if this once-per-day reminder fires at the current minute."""
    if not reminder.time_of_day:
        return False
    return (
        local_now.hour   == reminder.time_of_day.hour
        and local_now.minute == reminder.time_of_day.minute
    )


def _is_due_interval(reminder: Reminder, local_now: datetime) -> bool:
    """
    True if the current minute falls on an interval tick.

    Logic:
      - Current time must be within [start_time, end_time].
      - Minutes elapsed since start_time must be an exact multiple of interval_minutes.
    """
    if not all([reminder.start_time, reminder.end_time, reminder.interval_minutes]):
        return False

    # Strip seconds/microseconds for clean minute-level comparison
    current = local_now.time().replace(second=0, microsecond=0)

    if not (reminder.start_time <= current <= reminder.end_time):
        return False

    start_mins   = reminder.start_time.hour   * 60 + reminder.start_time.minute
    current_mins = current.hour * 60 + current.minute
    elapsed      = current_mins - start_mins

    return elapsed >= 0 and elapsed % reminder.interval_minutes == 0


@shared_task(ignore_result=True)
def dispatch_due_reminders():
    """
    Scan all active reminders and fire those whose trigger matches the current minute.

    Runs every minute via Celery Beat. Handles both once-per-day and
    interval (recurring) reminders, respecting each user's timezone.
    """
    active = Reminder.objects.select_related("user__profile").filter(is_active=True)
    fired = 0

    for reminder in active:
        local_now   = _user_now(reminder)
        today_code  = WEEKDAY_CODES[local_now.weekday()]

        # Day-of-week gate (empty list = every day)
        if reminder.days_of_week and today_code not in reminder.days_of_week:
            continue

        due = False
        if reminder.recurrence_type == Reminder.Recurrence.ONCE:
            due = _is_due_once(reminder, local_now)
        elif reminder.recurrence_type == Reminder.Recurrence.INTERVAL:
            due = _is_due_interval(reminder, local_now)

        if due:
            deliver_reminder.delay(reminder.id)
            fired += 1

    if fired:
        logger.info("dispatch_due_reminders: queued %d notifications", fired)
    return fired


@shared_task(ignore_result=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def deliver_reminder(reminder_id: int):
    """
    Deliver a single reminder as an in-app notification.

    Swap the notification body here for push, email, or websocket delivery.
    """
    try:
        reminder = Reminder.objects.select_related("user").get(pk=reminder_id, is_active=True)
    except Reminder.DoesNotExist:
        return

    # Build a contextual message based on reminder type
    messages = {
        "water":       "Time to hydrate — have a glass of water.",
        "workout":     "Time to train. Your workout is waiting.",
        "meal":        "Meal time. Don't forget to log what you eat.",
        "measurement": "Measurement check-in. Log your weight or body stats.",
        "movement":    "Time to move. A quick stretch or walk goes a long way.",
    }
    message = messages.get(reminder.reminder_type, reminder.title)

    logger.info(
        "REMINDER → user=%s type=%s recurrence=%s title=%r",
        reminder.user.username,
        reminder.reminder_type,
        reminder.recurrence_type,
        reminder.title,
    )

    from notifications.models import Notification
    Notification.objects.create(
        recipient=reminder.user,
        notif_type=Notification.Type.REMINDER,
        message=message,
        target_url="/reminders",
    )
