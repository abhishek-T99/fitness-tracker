from django.conf import settings
from django.db import models


class Goal(models.Model):
    class Type(models.TextChoices):
        WEIGHT_LOSS = "weight_loss", "Weight loss"
        WEIGHT_GAIN = "weight_gain", "Weight gain"
        STRENGTH = "strength", "Strength PR"
        ENDURANCE = "endurance", "Endurance"
        WORKOUTS_PER_WEEK = "workouts_per_week", "Workouts per week"
        CALORIES = "calories", "Daily calorie target"
        CUSTOM = "custom", "Custom"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ACHIEVED = "achieved", "Achieved"
        ABANDONED = "abandoned", "Abandoned"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=120)
    goal_type = models.CharField(max_length=30, choices=Type.choices)
    target_value = models.DecimalField(max_digits=8, decimal_places=2)
    current_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    starting_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, blank=True, help_text="kg, lb, reps, min, etc.")
    deadline = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def progress_percent(self):
        try:
            target = float(self.target_value)
            start = float(self.starting_value)
            current = float(self.current_value)
        except (TypeError, ValueError):
            return 0
        denom = target - start
        if denom == 0:
            return 100 if current == target else 0
        pct = ((current - start) / denom) * 100
        return max(0, min(100, round(pct, 1)))

    def __str__(self):
        return f"{self.title} ({self.user.username})"
