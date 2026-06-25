"""Unit tests for the nutrition tool handlers — exercised directly without
the agent runner so we can assert on DB state and serializer validation.
"""
from __future__ import annotations

import pytest
from django.utils import timezone

from ai.tools import nutrition as nutrition_tools
from nutrition.models import Food, Meal, WaterLog
from tests.factories import FoodFactory


@pytest.mark.django_db
class TestSearchFoods:
    def test_returns_public_foods_matching_query(self, user):
        FoodFactory(name="Banana", is_public=True)
        FoodFactory(name="Apple", is_public=True)
        FoodFactory(name="Boiled Egg", is_public=True)

        result = nutrition_tools.search_foods(user=user, query="egg")
        assert result["query"] == "egg"
        names = [r["name"] for r in result["results"]]
        assert "Boiled Egg" in names
        assert "Banana" not in names

    def test_excludes_other_users_private_foods(self, user, other_user):
        FoodFactory(name="Secret Snack", is_public=False, created_by=other_user)
        result = nutrition_tools.search_foods(user=user, query="Secret")
        assert result["results"] == []

    def test_respects_limit(self, user):
        for i in range(15):
            FoodFactory(name=f"Apple {i}", is_public=True)
        result = nutrition_tools.search_foods(user=user, query="Apple", limit=5)
        assert len(result["results"]) == 5


@pytest.mark.django_db
class TestCreateFood:
    def test_creates_private_food_owned_by_user(self, user):
        result = nutrition_tools.create_food(
            user=user,
            name="Roti",
            serving_size=40,
            serving_unit="piece",
            calories=120,
            protein_g=4,
            carbs_g=22,
            fat_g=2,
        )
        assert "id" in result
        food = Food.objects.get(pk=result["id"])
        assert food.created_by_id == user.id
        assert food.is_public is False

    def test_validation_error_returned_as_dict(self, user):
        result = nutrition_tools.create_food(
            user=user, name="", calories=100, protein_g=1, carbs_g=1, fat_g=1
        )
        assert result["error"] == "validation_failed"


@pytest.mark.django_db
class TestCreateMeal:
    def test_creates_meal_with_items(self, user, food):
        result = nutrition_tools.create_meal(
            user=user,
            meal_type="breakfast",
            consumed_at=timezone.now().isoformat(),
            items=[{"food_id": food.id, "servings": 2}],
        )
        assert "id" in result
        meal = Meal.objects.get(pk=result["id"])
        assert meal.user_id == user.id
        assert meal.meal_type == "breakfast"
        assert meal.items.count() == 1
        assert meal.items.first().food_id == food.id

    def test_invalid_meal_type_returns_error(self, user, food):
        result = nutrition_tools.create_meal(
            user=user,
            meal_type="brunch",
            consumed_at=timezone.now().isoformat(),
            items=[{"food_id": food.id, "servings": 1}],
        )
        assert result["error"] == "validation_failed"


@pytest.mark.django_db
class TestCreateWaterLog:
    def test_creates_water_log_owned_by_user(self, user):
        result = nutrition_tools.create_water_log(
            user=user, amount_ml=500, logged_at=timezone.now().isoformat()
        )
        assert "id" in result
        log = WaterLog.objects.get(pk=result["id"])
        assert log.user_id == user.id
        assert log.amount_ml == 500

    def test_negative_amount_rejected(self, user):
        result = nutrition_tools.create_water_log(
            user=user, amount_ml=-100, logged_at=timezone.now().isoformat()
        )
        assert result["error"] == "validation_failed"
