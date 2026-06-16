from datetime import timedelta

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from fitness_tracker import cache_keys

from .models import BodyMeasurement
from .serializers import BodyMeasurementSerializer


@extend_schema(tags=["Measurements"])
@extend_schema_view(
    weight_history=extend_schema(
        summary="Weight readings over time",
        parameters=[
            OpenApiParameter(
                name="days",
                type=int,
                description="Look-back window in days (default: 90).",
            ),
        ],
        responses=inline_serializer(
            name="WeightHistoryEntry",
            fields={
                "recorded_at": serializers.DateField(),
                "weight_kg": serializers.FloatField(),
            },
            many=True,
        ),
    ),
    latest=extend_schema(
        summary="Most recent measurement snapshot",
        responses={200: BodyMeasurementSerializer},
    ),
)
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

    @extend_schema(
        summary="Weight and body-fat percentage history for progress charts",
        parameters=[
            OpenApiParameter("days", int, description="Look-back window in days (default 90, max 365)"),
        ],
        responses=inline_serializer(
            name="BodyCompositionEntry",
            fields={
                "recorded_at":      serializers.DateField(),
                "weight_kg":        serializers.FloatField(allow_null=True),
                "body_fat_percent": serializers.FloatField(allow_null=True),
            },
            many=True,
        ),
    )
    @action(detail=False, methods=["get"], url_path="body-composition")
    def body_composition(self, request):
        """
        Returns measurements that have at least weight or body-fat recorded,
        ordered chronologically.  Used by the Progress page charts.
        """
        try:
            days = min(int(request.query_params.get("days", 90)), 365)
        except (TypeError, ValueError):
            days = 90

        key = cache_keys.body_composition(request.user.id, days)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        since = timezone.localdate() - timedelta(days=days)
        rows = (
            self.get_queryset()
            .filter(
                recorded_at__gte=since,
            )
            .filter(Q(weight_kg__isnull=False) | Q(body_fat_percent__isnull=False))
            .order_by("recorded_at")
            .values("recorded_at", "weight_kg", "body_fat_percent")
        )

        payload = [
            {
                "recorded_at":      r["recorded_at"].isoformat(),
                "weight_kg":        float(r["weight_kg"]) if r["weight_kg"] is not None else None,
                "body_fat_percent": float(r["body_fat_percent"]) if r["body_fat_percent"] is not None else None,
            }
            for r in rows
        ]
        cache.set(key, payload, cache_keys.BODY_COMP_TTL)
        return Response(payload)

    @action(detail=False, methods=["get"])
    def today_wellness(self, request):
        """Return today's wellness snapshot (steps, resting HR, HRV, sleep score)."""
        today = timezone.localdate()
        entry = self.get_queryset().filter(recorded_at=today).first()
        if not entry:
            return Response({
                "recorded_at": str(today),
                "steps": None,
                "resting_hr_bpm": None,
                "hrv_rmssd": None,
                "sleep_score": None,
            })
        return Response({
            "recorded_at": str(entry.recorded_at),
            "steps": entry.steps,
            "resting_hr_bpm": entry.resting_hr_bpm,
            "hrv_rmssd": float(entry.hrv_rmssd) if entry.hrv_rmssd else None,
            "sleep_score": entry.sleep_score,
        })
