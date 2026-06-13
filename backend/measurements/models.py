from django.conf import settings
from django.db import models


class BodyMeasurement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="measurements"
    )
    recorded_at = models.DateField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    body_fat_percent = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    chest_cm = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    waist_cm = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    hips_cm = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    arm_cm = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    thigh_cm = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    resting_hr_bpm = models.PositiveIntegerField(blank=True, null=True)
    steps = models.PositiveIntegerField(blank=True, null=True)
    hrv_rmssd = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    sleep_score = models.PositiveSmallIntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recorded_at"],
                name="one_measurement_per_day",
            )
        ]

    @property
    def bmi(self):
        height_cm = getattr(self.user.profile, "height_cm", None)
        if not self.weight_kg or not height_cm:
            return None
        h_m = float(height_cm) / 100
        return round(float(self.weight_kg) / (h_m * h_m), 1) if h_m > 0 else None
