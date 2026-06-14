from rest_framework import serializers

from .models import BodyMeasurement


class BodyMeasurementSerializer(serializers.ModelSerializer):
    bmi = serializers.FloatField(read_only=True)
    estimated_body_fat = serializers.SerializerMethodField()

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
            "neck_cm",
            "arm_cm",
            "thigh_cm",
            "resting_hr_bpm",
            "steps",
            "hrv_rmssd",
            "sleep_score",
            "notes",
            "bmi",
            "estimated_body_fat",
            "created_at",
        ]
        read_only_fields = ["created_at", "bmi", "estimated_body_fat"]

    def get_estimated_body_fat(self, obj):
        return obj.estimated_body_fat

    def validate(self, attrs):
        request = self.context.get("request")
        if request and "recorded_at" in attrs:
            qs = BodyMeasurement.objects.filter(
                user=request.user, recorded_at=attrs["recorded_at"]
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"recorded_at": "A measurement for this date already exists."}
                )
        return attrs
