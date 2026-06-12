from rest_framework import serializers

from .models import Achievement, Streak, UserAchievement


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ["id", "code", "name", "description", "icon", "kind", "threshold"]


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement_detail = AchievementSerializer(source="achievement", read_only=True)

    class Meta:
        model = UserAchievement
        fields = ["id", "achievement", "achievement_detail", "unlocked_at"]


class StreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Streak
        fields = ["current_days", "longest_days", "last_workout_date", "updated_at"]
