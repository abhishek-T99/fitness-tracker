from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


class Profile(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        UNSPECIFIED = "unspecified", "Prefer not to say"

    class ActivityLevel(models.TextChoices):
        SEDENTARY = "sedentary", "Sedentary"
        LIGHT = "light", "Lightly active"
        MODERATE = "moderate", "Moderately active"
        ACTIVE = "active", "Very active"
        ATHLETE = "athlete", "Athlete"

    class Units(models.TextChoices):
        METRIC = "metric", "Metric (kg / cm)"
        IMPERIAL = "imperial", "Imperial (lb / in)"

    class ReportFrequency(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=20, choices=Gender.choices, default=Gender.UNSPECIFIED
    )
    height_cm = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    activity_level = models.CharField(
        max_length=20, choices=ActivityLevel.choices, default=ActivityLevel.MODERATE
    )
    units = models.CharField(max_length=10, choices=Units.choices, default=Units.METRIC)
    daily_calorie_goal = models.PositiveIntegerField(blank=True, null=True)
    weekly_workout_goal = models.PositiveIntegerField(default=3)
    timezone = models.CharField(max_length=64, default="UTC")
    # Updated by ActivityTrackingMiddleware on every authenticated request.
    # Used to enforce the 5-day inactivity auto-logout policy.
    last_activity = models.DateTimeField(blank=True, null=True)
    # Fitness report preferences
    reports_enabled = models.BooleanField(default=False)
    report_frequency = models.CharField(
        max_length=10,
        choices=ReportFrequency.choices,
        default=ReportFrequency.WEEKLY,
    )
    last_report_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile<{self.user.username}>"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        from datetime import date

        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )
