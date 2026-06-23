from django.db import transaction
from rest_framework import serializers

from .models import Food, Meal, MealItem, WaterLog


class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = [
            "id",
            "name",
            "brand",
            "serving_size",
            "serving_unit",
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
            "fiber_g",
            "sugar_g",
            "is_public",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class MealItemSerializer(serializers.ModelSerializer):
    food_detail = FoodSerializer(source="food", read_only=True)
    calories = serializers.FloatField(read_only=True)
    protein_g = serializers.FloatField(read_only=True)
    carbs_g = serializers.FloatField(read_only=True)
    fat_g = serializers.FloatField(read_only=True)

    class Meta:
        model = MealItem
        fields = [
            "id",
            "food",
            "food_detail",
            "servings",
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
        ]


class MealSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True)
    totals = serializers.DictField(read_only=True)

    class Meta:
        model = Meal
        fields = [
            "id",
            "meal_type",
            "consumed_at",
            "notes",
            "items",
            "totals",
            "created_at",
        ]
        read_only_fields = ["created_at", "totals"]

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        meal = Meal.objects.create(user=self.context["request"].user, **validated_data)
        if items:
            MealItem.objects.bulk_create([MealItem(meal=meal, **item) for item in items])
        return meal

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            if items:
                MealItem.objects.bulk_create([MealItem(meal=instance, **item) for item in items])
        return instance


class WaterLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterLog
        fields = ["id", "amount_ml", "logged_at"]
