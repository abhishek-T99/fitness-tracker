from rest_framework import serializers

from .models import Exercise


class ExerciseSerializer(serializers.ModelSerializer):
    # Computed field — always present so the frontend never has to build URLs
    youtube_search_query = serializers.CharField(read_only=True)

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
            "tutorial_url",
            "youtube_search_query",
            "is_compound",
            "met_value",
        ]
