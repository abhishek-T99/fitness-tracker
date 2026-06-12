from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(
        source="actor.username", read_only=True, default=None
    )

    class Meta:
        model  = Notification
        fields = [
            "id",
            "notif_type",
            "message",
            "target_url",
            "read",
            "actor_username",
            "created_at",
        ]
        read_only_fields = [
            "id", "notif_type", "message", "target_url", "actor_username", "created_at"
        ]


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Only the `read` field may be changed via PATCH."""

    class Meta:
        model  = Notification
        fields = ["read"]
