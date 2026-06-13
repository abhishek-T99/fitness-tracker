from rest_framework import serializers

from .models import Integration, SyncLog


class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = ["id", "synced_at", "event_type", "external_id", "status", "detail"]


class IntegrationSerializer(serializers.ModelSerializer):
    last_sync = SyncLogSerializer(source="sync_logs.first", read_only=True)
    token_athlete_id = serializers.SerializerMethodField()

    class Meta:
        model = Integration
        fields = [
            "id",
            "provider",
            "is_active",
            "connected_at",
            "last_synced_at",
            "last_sync",
            "token_athlete_id",
        ]
        read_only_fields = fields

    def get_token_athlete_id(self, obj):
        try:
            return obj.token.athlete_id
        except Exception:
            return None
