from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Reminder
from .serializers import ReminderSerializer


@extend_schema(tags=["Reminders"])
class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    filterset_fields = ["reminder_type", "is_active"]

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        last = self.get_queryset().order_by("order").last()
        next_order = (last.order + 1) if last else 0
        serializer.save(user=self.request.user, order=next_order)

    @extend_schema(
        request={"application/json": {"type": "array", "items": {"type": "object",
            "properties": {"id": {"type": "integer"}, "order": {"type": "integer"}}}}},
        responses={200: None},
        summary="Bulk-update the display order of reminders",
    )
    @action(detail=False, methods=["post"])
    def reorder(self, request):
        qs = self.get_queryset()
        updates = []
        for item in request.data:
            try:
                obj = qs.get(pk=item["id"])
                obj.order = int(item["order"])
                updates.append(obj)
            except (Reminder.DoesNotExist, KeyError, TypeError, ValueError):
                pass
        Reminder.objects.bulk_update(updates, ["order"])
        return Response({"detail": f"Reordered {len(updates)} reminders."})
