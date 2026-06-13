from django.conf import settings
from django.db import models


class Achievement(models.Model):
    class Kind(models.TextChoices):
        WORKOUT_COUNT   = "workout_count",   "Total workouts"
        STREAK_DAYS     = "streak_days",     "Consecutive day streak"
        VOLUME_TOTAL    = "volume_total",    "Total lifting volume (kg)"
        WORKOUT_MINUTES = "workout_minutes", "Total workout minutes"
        CALORIE_BURN    = "calorie_burn",    "Total calories burned"
        DISTANCE_KM     = "distance_km",     "Total distance covered (km)"
        EARLY_BIRD      = "early_bird",      "Workouts started before 7 am"
        NIGHT_OWL       = "night_owl",       "Workouts started at 9 pm or later"
        GOALS_COMPLETED = "goals_completed", "Goals marked achieved"

    code = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField()
    icon = models.CharField(max_length=40, default="trophy", help_text="lucide icon name")
    kind = models.CharField(max_length=30, choices=Kind.choices)
    threshold = models.PositiveIntegerField()

    class Meta:
        ordering = ["kind", "threshold"]

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievements"
    )
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "achievement"], name="unique_user_achievement"
            ),
        ]
        ordering = ["-unlocked_at"]


class Streak(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="streak"
    )
    current_days = models.PositiveIntegerField(default=0)
    longest_days = models.PositiveIntegerField(default=0)
    last_workout_date = models.DateField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
