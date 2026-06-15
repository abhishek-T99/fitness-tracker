from datetime import date, timedelta

from rest_framework import serializers

from nutrition.serializers import FoodSerializer
from .models import MealPlan, MealPlanItem


def _normalise_to_monday(d: date) -> date:
    """Return the Monday of the week containing *d*."""
    return d - timedelta(days=d.weekday())


class MealPlanItemSerializer(serializers.ModelSerializer):
    food_detail = FoodSerializer(source="food", read_only=True)
    calories    = serializers.FloatField(read_only=True)
    protein_g   = serializers.FloatField(read_only=True)
    carbs_g     = serializers.FloatField(read_only=True)
    fat_g       = serializers.FloatField(read_only=True)

    class Meta:
        model  = MealPlanItem
        fields = [
            "id", "day", "meal_type", "food", "food_detail",
            "servings", "order", "calories", "protein_g", "carbs_g", "fat_g",
        ]


class MealPlanSerializer(serializers.ModelSerializer):
    items = MealPlanItemSerializer(many=True, read_only=True)

    class Meta:
        model  = MealPlan
        fields = ["id", "name", "week_start", "items", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate_week_start(self, value):
        return _normalise_to_monday(value)

    def validate(self, attrs):
        request = self.context.get("request")
        if request and "week_start" in attrs:
            week_start = _normalise_to_monday(attrs["week_start"])
            qs = MealPlan.objects.filter(user=request.user, week_start=week_start)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"week_start": "You already have a plan for this week."}
                )
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
