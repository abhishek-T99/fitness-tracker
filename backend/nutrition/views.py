from datetime import datetime, time

from django.core.cache import cache
from django.db.models import Q, Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiParameter
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from fitness_tracker import cache_keys

from .models import Food, Meal, WaterLog
from .serializers import FoodSerializer, MealSerializer, WaterLogSerializer


@extend_schema(tags=["Nutrition"])
class FoodViewSet(viewsets.ModelViewSet):
    serializer_class = FoodSerializer
    filterset_fields = ["is_public"]
    search_fields = ["name", "brand"]
    ordering_fields = ["name", "calories"]

    def get_queryset(self):
        return Food.objects.filter(Q(is_public=True) | Q(created_by=self.request.user))

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, is_public=False)


@extend_schema(tags=["Nutrition"])
@extend_schema_view(
    daily_summary=extend_schema(
        summary="Daily macro and water totals",
        parameters=[
            OpenApiParameter(
                name="date",
                type=str,
                description="ISO 8601 date (YYYY-MM-DD). Defaults to today in the user's timezone.",
            ),
        ],
        responses=inline_serializer(
            name="DailySummary",
            fields={
                "date": serializers.DateField(),
                "totals": inline_serializer(
                    name="MacroTotals",
                    fields={
                        "calories": serializers.FloatField(),
                        "protein_g": serializers.FloatField(),
                        "carbs_g": serializers.FloatField(),
                        "fat_g": serializers.FloatField(),
                    },
                ),
                "by_meal": serializers.DictField(
                    child=serializers.DictField(child=serializers.FloatField()),
                    help_text="Macro breakdown keyed by meal_type.",
                ),
                "water_ml": serializers.IntegerField(),
                "calorie_goal": serializers.IntegerField(allow_null=True),
            },
        ),
    ),
)
class MealViewSet(viewsets.ModelViewSet):
    serializer_class = MealSerializer
    filterset_fields = ["meal_type"]
    ordering_fields = ["consumed_at"]

    def get_queryset(self):
        qs = Meal.objects.filter(user=self.request.user).prefetch_related("items__food")
        date = self.request.query_params.get("date")
        if date:
            qs = qs.filter(consumed_at__date=date)
        return qs

    @action(detail=False, methods=["get"])
    def daily_summary(self, request):
        """Per-user daily macro totals.

        Cached for a short TTL and invalidated on Meal / WaterLog write
        signals so the dashboard reflects edits immediately while still
        absorbing repeated reads across browser tabs.
        """
        date_str = request.query_params.get("date")
        if date_str:
            day = datetime.fromisoformat(date_str).date()
        else:
            day = timezone.localdate()

        key = cache_keys.nutrition_summary(request.user.id, day.isoformat())
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        start = timezone.make_aware(datetime.combine(day, time.min))
        end = timezone.make_aware(datetime.combine(day, time.max))

        meals = self.get_queryset().filter(consumed_at__range=(start, end))
        totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
        breakdown = {}
        for meal in meals:
            t = meal.totals
            for k in totals:
                totals[k] += t[k]
            running = breakdown.setdefault(meal.meal_type, {k: 0 for k in totals})
            for k in totals:
                running[k] += t[k]

        water_total = (
            WaterLog.objects.filter(user=request.user, logged_at__range=(start, end))
            .aggregate(total=Sum("amount_ml"))["total"]
            or 0
        )

        payload = {
            "date": day.isoformat(),
            "totals": {k: round(v, 1) for k, v in totals.items()},
            "by_meal": breakdown,
            "water_ml": water_total,
            "calorie_goal": getattr(request.user.profile, "daily_calorie_goal", None),
        }
        cache.set(key, payload, cache_keys.NUTRITION_SUMMARY_TTL)
        return Response(payload)


@extend_schema(tags=["Nutrition"])
class WaterLogViewSet(viewsets.ModelViewSet):
    serializer_class = WaterLogSerializer

    def get_queryset(self):
        qs = WaterLog.objects.filter(user=self.request.user)
        date = self.request.query_params.get("date")
        if date:
            qs = qs.filter(logged_at__date=date)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
