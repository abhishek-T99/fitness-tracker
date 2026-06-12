from django.conf import settings
from django.db import models


class Reminder(models.Model):
    class Type(models.TextChoices):
        WORKOUT = "workout", "Workout"
        WATER = "water", "Water"
        MEAL = "meal", "Meal"
        MEASUREMENT = "measurement", "Measurement"
        CUSTOM = "custom", "Custom"

    DAYS_OF_WEEK = [
        ("mon", "Mon"),
        ("tue", "Tue"),
        ("wed", "Wed"),
        ("thu", "Thu"),
        ("fri", "Fri"),
        ("sat", "Sat"),
        ("sun", "Sun"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders"
    )
    title = models.CharField(max_length=120)
    reminder_type = models.CharField(max_length=20, choices=Type.choices, default=Type.WORKOUT)
    time_of_day = models.TimeField()
    days_of_week = models.JSONField(
        default=list,
        help_text="List of 3-letter weekday codes: mon, tue, wed, thu, fri, sat, sun.",
    )
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["time_of_day"]

    def __str__(self):
        return f"{self.title} @ {self.time_of_day}"
