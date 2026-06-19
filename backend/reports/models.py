from django.conf import settings
from django.db import models


def _report_upload_path(instance, filename):
    return f"reports/{instance.user_id}/{filename}"


class FitnessReport(models.Model):
    class PeriodType(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fitness_reports",
    )
    period_type = models.CharField(max_length=10, choices=PeriodType.choices)
    period_start = models.DateField()
    period_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    emailed_at = models.DateTimeField(blank=True, null=True)
    pdf = models.FileField(upload_to=_report_upload_path, blank=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.user.username} | {self.period_type} | {self.period_start}"
