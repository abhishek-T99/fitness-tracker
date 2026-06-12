from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer, NotificationUpdateSerializer


@extend_schema(tags=["Notifications"])
@extend_schema_view(
    list=extend_schema(summary="List notifications (unread first)"),
    partial_update=extend_schema(summary="Mark a notification as read"),
    unread_count=extend_schema(
        summary="Count of unread notifications",
        responses=inline_serializer(
            name="UnreadCountResponse",
            fields={"count": serializers.IntegerField()},
        ),
    ),
    mark_all_read=extend_schema(summary="Mark all notifications as read"),
)
class NotificationViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return NotificationUpdateSerializer
        return NotificationSerializer

    # Disable create / destroy — notifications are system-generated only.
    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(read=False).count()
        return Response({"count": count})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().filter(read=False).update(read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
