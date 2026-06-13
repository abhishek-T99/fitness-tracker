from django.conf import settings
from django.db import models


class Reminder(models.Model):
    class Type(models.TextChoices):
        WORKOUT     = "workout",     "Workout"
        WATER       = "water",       "Water / Hydration"
        MEAL        = "meal",        "Meal / Nutrition"
        MEASUREMENT = "measurement", "Measurement"
        MOVEMENT    = "movement",    "Movement / Stretch"
        CUSTOM      = "custom",      "Custom"

    class Recurrence(models.TextChoices):
        ONCE     = "once",     "Once per day"
        INTERVAL = "interval", "Repeat throughout the day"

    DAYS_OF_WEEK = [
        ("mon", "Mon"), ("tue", "Tue"), ("wed", "Wed"),
        ("thu", "Thu"), ("fri", "Fri"), ("sat", "Sat"), ("sun", "Sun"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders"
    )
    title = models.CharField(max_length=120)
    reminder_type = models.CharField(max_length=20, choices=Type.choices, default=Type.WORKOUT)

    # ── Schedule ─────────────────────────────────────────────────────────────
    recurrence_type = models.CharField(
        max_length=20, choices=Recurrence.choices, default=Recurrence.ONCE
    )

    # Used when recurrence_type == "once"
    time_of_day = models.TimeField(
        null=True, blank=True,
        help_text="Trigger time for once-per-day reminders.",
    )

    # Used when recurrence_type == "interval"
    start_time = models.TimeField(
        null=True, blank=True,
        help_text="First trigger of the day for interval reminders.",
    )
    end_time = models.TimeField(
        null=True, blank=True,
        help_text="Last allowed trigger time for interval reminders.",
    )
    interval_minutes = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Minutes between triggers (e.g. 60 = every hour).",
    )

    days_of_week = models.JSONField(
        default=list,
        help_text="3-letter weekday codes. Empty list = every day.",
    )
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "time_of_day", "start_time"]

    def __str__(self):
        if self.recurrence_type == self.Recurrence.INTERVAL:
            return f"{self.title} every {self.interval_minutes}m ({self.start_time}–{self.end_time})"
        return f"{self.title} @ {self.time_of_day}"
