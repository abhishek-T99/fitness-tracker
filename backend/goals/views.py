from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Goal
from .serializers import GoalSerializer


@extend_schema(tags=["Goals"])
class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    filterset_fields = ["status", "goal_type"]
    ordering_fields = ["deadline", "created_at", "status", "order"]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Place new goals at the end of the current list
        last = self.get_queryset().order_by("order").last()
        next_order = (last.order + 1) if last else 0
        serializer.save(user=self.request.user, order=next_order)

    @extend_schema(
        request={"application/json": {"type": "array", "items": {"type": "object",
            "properties": {"id": {"type": "integer"}, "order": {"type": "integer"}}}}},
        responses={200: None},
        summary="Bulk-update the display order of goals",
    )
    @action(detail=False, methods=["post"])
    def reorder(self, request):
        """Accept [{id, order}, …] and bulk-update."""
        qs = self.get_queryset()
        updates = []
        for item in request.data:
            try:
                obj = qs.get(pk=item["id"])
                obj.order = int(item["order"])
                updates.append(obj)
            except (Goal.DoesNotExist, KeyError, TypeError, ValueError):
                pass
        Goal.objects.bulk_update(updates, ["order"])
        return Response({"detail": f"Reordered {len(updates)} goals."})
