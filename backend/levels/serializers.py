from rest_framework import serializers

from .models import UserLevel, UserWeeklyChallenge, WeeklyChallenge, XPTransaction


class XPTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = XPTransaction
        fields = [
            "id", "amount", "base_amount", "multiplier",
            "reason", "source_type", "source_id", "created_at",
        ]


class UserLevelSerializer(serializers.ModelSerializer):
    xp_in_current_level  = serializers.IntegerField(read_only=True)
    xp_for_next_level    = serializers.IntegerField(read_only=True)
    xp_progress_pct      = serializers.FloatField(read_only=True)
    athlete_class_display = serializers.CharField(
        source="get_athlete_class_display", read_only=True
    )
    tier_display          = serializers.CharField(source="get_tier_display", read_only=True)
    recent_transactions   = serializers.SerializerMethodField()

    class Meta:
        model  = UserLevel
        fields = [
            "level", "tier", "tier_display",
            "athlete_class", "athlete_class_display",
            "total_xp", "xp_in_current_level", "xp_for_next_level", "xp_progress_pct",
            "prestige_count", "updated_at",
            "recent_transactions",
        ]

    def get_recent_transactions(self, obj):
        qs = obj.user.xp_transactions.all()[:5]
        return XPTransactionSerializer(qs, many=True).data


class WeeklyChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WeeklyChallenge
        fields = ["id", "challenge_type", "description", "target_value", "xp_reward", "week_start"]


class UserWeeklyChallengeSerializer(serializers.ModelSerializer):
    challenge    = WeeklyChallengeSerializer(read_only=True)
    progress_pct = serializers.SerializerMethodField()

    class Meta:
        model  = UserWeeklyChallenge
        fields = [
            "id", "challenge", "current_value",
            "completed", "completed_at", "progress_pct",
        ]

    def get_progress_pct(self, obj) -> float:
        target = obj.challenge.target_value
        if not target:
            return 100.0
        return round(min(obj.current_value / target * 100, 100), 1)


class LeaderboardEntrySerializer(serializers.Serializer):
    rank              = serializers.IntegerField()
    user_id           = serializers.IntegerField()
    username          = serializers.CharField()
    display_name      = serializers.CharField()
    avatar            = serializers.URLField(allow_null=True)
    level             = serializers.IntegerField()
    tier              = serializers.CharField()
    athlete_class     = serializers.CharField()
    athlete_class_display = serializers.CharField()
    total_xp          = serializers.IntegerField()
    is_self           = serializers.BooleanField()
