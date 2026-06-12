"""
Tests for the nutrition app: food visibility rules, meal CRUD with nested
items, daily macro summary, and water logging.
"""
import pytest
from django.utils import timezone

from tests.factories import FoodFactory, MealFactory, MealItemFactory, WaterLogFactory

FOOD_URL = "/api/v1/nutrition/foods/"
MEAL_URL = "/api/v1/nutrition/meals/"
WATER_URL = "/api/v1/nutrition/water/"
DAILY_SUMMARY_URL = "/api/v1/nutrition/meals/daily_summary/"


def food_url(pk):
    return f"/api/v1/nutrition/foods/{pk}/"


def meal_url(pk):
    return f"/api/v1/nutrition/meals/{pk}/"


def water_url(pk):
    return f"/api/v1/nutrition/water/{pk}/"


# ---------------------------------------------------------------------------
# Foods
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFoodList:
    def test_public_foods_are_visible_to_all_authenticated_users(self, auth_client, other_user):
        FoodFactory(is_public=True, created_by=other_user)
        res = auth_client.get(FOOD_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_private_food_only_visible_to_its_creator(self, auth_client, user, other_user):
        FoodFactory(is_public=False, created_by=other_user)  # not visible
        FoodFactory(is_public=False, created_by=user)        # visible
        res = auth_client.get(FOOD_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(FOOD_URL)
        assert res.status_code == 401


@pytest.mark.django_db
class TestFoodCreate:
    def test_user_can_create_food(self, auth_client, user):
        payload = {
            "name": "Chicken Breast",
            "calories": "165.00",
            "protein_g": "31.00",
            "carbs_g": "0.00",
            "fat_g": "3.60",
        }
        res = auth_client.post(FOOD_URL, payload)
        assert res.status_code == 201
        assert res.data["name"] == "Chicken Breast"

    def test_missing_required_calories_returns_400(self, auth_client):
        res = auth_client.post(FOOD_URL, {"name": "Mystery Food"})
        assert res.status_code == 400


@pytest.mark.django_db
class TestFoodDetail:
    def test_owner_can_update_own_food(self, auth_client, user):
        food = FoodFactory(created_by=user, is_public=False)
        res = auth_client.patch(food_url(food.pk), {"name": "Updated Name"})
        assert res.status_code == 200
        assert res.data["name"] == "Updated Name"

    def test_user_cannot_update_another_users_private_food(self, auth_client, other_user):
        food = FoodFactory(created_by=other_user, is_public=False)
        res = auth_client.patch(food_url(food.pk), {"name": "Hijacked"})
        assert res.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Meals
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMealList:
    def test_returns_only_own_meals(self, auth_client, user, other_user):
        MealFactory(user=user)
        MealFactory(user=other_user)
        res = auth_client.get(MEAL_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1


@pytest.mark.django_db
class TestMealCreate:
    def test_creates_meal_without_items(self, auth_client, user):
        payload = {
            "meal_type": "lunch",
            "consumed_at": timezone.now().isoformat(),
            "items": [],
        }
        res = auth_client.post(MEAL_URL, payload, format="json")
        assert res.status_code == 201
        assert res.data["meal_type"] == "lunch"

    def test_creates_meal_with_nested_items(self, auth_client, user, food):
        payload = {
            "meal_type": "dinner",
            "consumed_at": timezone.now().isoformat(),
            "items": [{"food": food.pk, "servings": "2.00"}],
        }
        res = auth_client.post(MEAL_URL, payload, format="json")
        assert res.status_code == 201
        assert len(res.data["items"]) == 1

    def test_invalid_meal_type_returns_400(self, auth_client):
        payload = {
            "meal_type": "brunch",       # not a valid choice
            "consumed_at": timezone.now().isoformat(),
            "items": [],
        }
        res = auth_client.post(MEAL_URL, payload, format="json")
        assert res.status_code == 400


@pytest.mark.django_db
class TestMealDetail:
    def test_owner_can_delete_meal(self, auth_client, user):
        meal = MealFactory(user=user)
        res = auth_client.delete(meal_url(meal.pk))
        assert res.status_code == 204

    def test_other_users_meal_returns_404(self, auth_client, other_user):
        meal = MealFactory(user=other_user)
        res = auth_client.get(meal_url(meal.pk))
        assert res.status_code == 404


@pytest.mark.django_db
class TestDailySummary:
    def test_returns_macro_totals_for_date(self, auth_client, user, food):
        today = timezone.localdate().isoformat()
        meal = MealFactory(user=user, consumed_at=timezone.now())
        MealItemFactory(meal=meal, food=food, servings="1.00")
        res = auth_client.get(DAILY_SUMMARY_URL, {"date": today})
        assert res.status_code == 200
        # Response shape: {"totals": {"calories": ..., "protein_g": ...}, ...}
        assert "totals" in res.data
        assert "calories" in res.data["totals"]
        assert "protein_g" in res.data["totals"]

    def test_empty_day_returns_zero_totals(self, auth_client):
        res = auth_client.get(DAILY_SUMMARY_URL, {"date": "2000-01-01"})
        assert res.status_code == 200
        assert float(res.data["totals"]["calories"]) == 0.0


# ---------------------------------------------------------------------------
# Water logs
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWaterLog:
    def test_user_can_log_water(self, auth_client, user):
        payload = {"amount_ml": 750, "logged_at": timezone.now().isoformat()}
        res = auth_client.post(WATER_URL, payload)
        assert res.status_code == 201
        assert res.data["amount_ml"] == 750

    def test_returns_only_own_logs(self, auth_client, user, other_user):
        WaterLogFactory(user=user)
        WaterLogFactory(user=other_user)
        res = auth_client.get(WATER_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_owner_can_delete_log(self, auth_client, user):
        log = WaterLogFactory(user=user)
        res = auth_client.delete(water_url(log.pk))
        assert res.status_code == 204
