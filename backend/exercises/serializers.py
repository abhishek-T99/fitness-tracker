from rest_framework import serializers

from .models import Exercise


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "primary_muscle",
            "secondary_muscles",
            "equipment",
            "instructions",
            "is_compound",
            "met_value",
        ]
