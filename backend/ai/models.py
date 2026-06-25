from django.conf import settings
from django.db import models


class AgentSession(models.Model):
    """One agent invocation per row.

    Captures the full audit trail of an AI-assisted action: what the user
    asked, what the model decided, which tools ran, and what was created.
    Every feature endpoint creates exactly one of these.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        BUDGET_EXCEEDED = "budget_exceeded", "Budget exceeded"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent_sessions",
    )
    feature = models.CharField(max_length=64, db_index=True)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.PENDING
    )
    input_text = models.TextField(blank=True)
    final_output = models.TextField(blank=True)
    model = models.CharField(max_length=64, blank=True)
    tokens_in = models.PositiveIntegerField(default=0)
    tokens_out = models.PositiveIntegerField(default=0)
    cache_read_tokens = models.PositiveIntegerField(default=0)
    cache_write_tokens = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user", "-started_at"]),
            models.Index(fields=["feature", "-started_at"]),
        ]

    def __str__(self):
        return f"{self.feature} #{self.pk} ({self.status})"


class AgentStep(models.Model):
    """One step within an AgentSession — either a model call or a tool call."""

    class Kind(models.TextChoices):
        MODEL_CALL = "model_call", "Model call"
        TOOL_CALL = "tool_call", "Tool call"

    session = models.ForeignKey(
        AgentSession, on_delete=models.CASCADE, related_name="steps"
    )
    ordinal = models.PositiveIntegerField()
    kind = models.CharField(max_length=16, choices=Kind.choices)
    name = models.CharField(max_length=128, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    is_error = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["session_id", "ordinal"]
        unique_together = [("session", "ordinal")]

    def __str__(self):
        return f"{self.session_id}:{self.ordinal} {self.kind}"
