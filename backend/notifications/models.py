from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        LIKE             = "like",            "Like"
        COMMENT          = "comment",         "Comment"
        FRIEND_REQUEST   = "friend_request",  "Friend Request"
        FRIEND_ACCEPTED  = "friend_accepted", "Friend Accepted"
        ACHIEVEMENT      = "achievement",     "Achievement Unlocked"
        STREAK_AT_RISK   = "streak_at_risk",  "Streak at Risk"
        GOAL_MILESTONE   = "goal_milestone",  "Goal Milestone"
        GOAL_DEADLINE    = "goal_deadline",   "Goal Deadline"
        REMINDER         = "reminder",        "Reminder"
        WEEKLY_SUMMARY   = "weekly_summary",  "Weekly Summary"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    notif_type = models.CharField(max_length=30, choices=Type.choices)
    message    = models.CharField(max_length=255)
    target_url = models.CharField(max_length=255, blank=True)
    read       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Unread first, then newest — consistent ordering for the API and tests.
        ordering = ["read", "-created_at"]
        indexes  = [
            models.Index(fields=["recipient", "read"]),
        ]

    def __str__(self):
        return f"[{self.notif_type}] → {self.recipient.username}"
