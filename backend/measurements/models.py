import math

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
    neck_cm = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        help_text="Neck circumference in cm — used for the U.S. Navy body-fat formula.",
    )
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

    @property
    def estimated_body_fat(self):
        """
        Estimate body fat % using the best available formula.

        Priority:
          1. U.S. Navy formula — waist + neck (+ hips for women), height.
             Error ≈ ±1–3 %.  Requires neck_cm.
          2. Deurenberg BMI formula — BMI + age + sex.
             Error ≈ ±3–5 %.  Fallback when neck_cm is absent.

        Returns None if insufficient data is available.
        Returns a dict:
            { "value": float, "formula": "navy" | "deurenberg" }
        """
        profile = getattr(self.user, "profile", None)
        if not profile:
            return None

        height_cm = float(profile.height_cm) if profile.height_cm else None
        gender = getattr(profile, "gender", None)

        # ── U.S. Navy formula ─────────────────────────────────────────────
        if height_cm and self.waist_cm and self.neck_cm:
            waist  = float(self.waist_cm)
            neck   = float(self.neck_cm)
            height = height_cm

            if gender == "male":
                diff = waist - neck
                if diff <= 0:
                    pass
                else:
                    bf = 86.010 * math.log10(diff) - 70.041 * math.log10(height) + 36.76
                    return {"value": round(max(1.0, bf), 1), "formula": "navy"}

            elif gender == "female" and self.hips_cm:
                hips = float(self.hips_cm)
                diff = waist + hips - neck
                if diff <= 0:
                    pass
                else:
                    bf = 163.205 * math.log10(diff) - 97.684 * math.log10(height) - 78.387
                    return {"value": round(max(1.0, bf), 1), "formula": "navy"}

        # ── Deurenberg BMI fallback ───────────────────────────────────────
        bmi = self.bmi
        if bmi is None:
            return None

        dob = getattr(profile, "date_of_birth", None)
        if not dob:
            return None
        from datetime import date
        age = (date.today() - dob).days / 365.25

        sex = 1 if gender == "male" else 0  # 1=male, 0=female/other
        bf = (1.2 * bmi) + (0.23 * age) - (10.8 * sex) - 5.4
        return {"value": round(max(1.0, bf), 1), "formula": "deurenberg"}
