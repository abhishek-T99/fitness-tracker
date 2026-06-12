from rest_framework import viewsets

from .models import Goal
from .serializers import GoalSerializer


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    filterset_fields = ["status", "goal_type"]
    ordering_fields = ["deadline", "created_at", "status"]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
