from django.conf import settings
from django.db import models
from django.utils import timezone


class Provider(models.TextChoices):
    STRAVA = "strava", "Strava"
    INTERVALS = "intervals", "Intervals.icu"


class Integration(models.Model):
    """One row per user × provider pair."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="integrations",
    )
    provider = models.CharField(max_length=32, choices=Provider.choices)
    is_active = models.BooleanField(default=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "provider")]
        ordering = ["provider"]

    def __str__(self):
        return f"{self.user.username} / {self.provider}"


class OAuthToken(models.Model):
    """
    Stores the OAuth2 access + refresh tokens for an integration.

    NOTE: tokens are stored as plaintext here. In a production deployment,
    encrypt them at rest (e.g. django-cryptography, AWS Secrets Manager).
    """

    integration = models.OneToOneField(
        Integration, on_delete=models.CASCADE, related_name="token"
    )
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()
    scope = models.CharField(max_length=255, blank=True)
    # Provider-specific athlete/user ID for deduplication and webhook routing
    athlete_id = models.CharField(max_length=64, blank=True)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"Token({self.integration})"


class SyncLog(models.Model):
    """Audit trail for every sync attempt."""

    class Status(models.TextChoices):
        SUCCESS = "success"
        FAILED = "failed"
        SKIPPED = "skipped"

    integration = models.ForeignKey(
        Integration, on_delete=models.CASCADE, related_name="sync_logs"
    )
    synced_at = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=64)  # e.g. "activity.create"
    external_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices)
    detail = models.TextField(blank=True)
    # The workout created/updated as a result of this sync (nullable)
    workout = models.ForeignKey(
        "workouts.Workout",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sync_logs",
    )

    class Meta:
        ordering = ["-synced_at"]

    def __str__(self):
        return f"{self.integration} / {self.event_type} / {self.status}"
