from datetime import timedelta

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BodyMeasurement
from .serializers import BodyMeasurementSerializer


class BodyMeasurementViewSet(viewsets.ModelViewSet):
    serializer_class = BodyMeasurementSerializer
    ordering_fields = ["recorded_at"]
    ordering = ["-recorded_at"]

    def get_queryset(self):
        return BodyMeasurement.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def weight_history(self, request):
        days = int(request.query_params.get("days", 90))
        since = timezone.localdate() - timedelta(days=days)
        rows = (
            self.get_queryset()
            .filter(recorded_at__gte=since, weight_kg__isnull=False)
            .order_by("recorded_at")
            .values("recorded_at", "weight_kg")
        )
        return Response(list(rows))

    @action(detail=False, methods=["get"])
    def latest(self, request):
        latest = self.get_queryset().first()
        if not latest:
            return Response({})
        return Response(self.get_serializer(latest).data)
