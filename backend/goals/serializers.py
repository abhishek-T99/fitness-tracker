from rest_framework import serializers

from .models import Goal


class GoalSerializer(serializers.ModelSerializer):
    progress_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = Goal
        fields = [
            "id",
            "title",
            "goal_type",
            "target_value",
            "current_value",
            "starting_value",
            "unit",
            "deadline",
            "status",
            "notes",
            "order",
            "progress_percent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "progress_percent"]
