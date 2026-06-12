from rest_framework import serializers

from .models import BodyMeasurement


class BodyMeasurementSerializer(serializers.ModelSerializer):
    bmi = serializers.FloatField(read_only=True)

    class Meta:
        model = BodyMeasurement
        fields = [
            "id",
            "recorded_at",
            "weight_kg",
            "body_fat_percent",
            "chest_cm",
            "waist_cm",
            "hips_cm",
            "arm_cm",
            "thigh_cm",
            "resting_hr_bpm",
            "notes",
            "bmi",
            "created_at",
        ]
        read_only_fields = ["created_at", "bmi"]
