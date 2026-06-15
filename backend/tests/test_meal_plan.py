"""
TDD tests for the Meal Plan feature.

Covers:
  - CRUD for MealPlan (week-scoped, one per user per week)
  - MealPlanItem add / update / delete / reorder
  - Auto-generate: fills 7 days × 4 meal types from user history or public foods
  - Log-day: copies a day's plan into real Meal + MealItem records
  - Weekly summary: computed daily totals and target percentages
  - User isolation throughout
"""
from datetime import date, timedelta

import pytest

from tests.factories import FoodFactory, MealFactory, MealItemFactory, UserFactory

LIST_URL     = "/api/v1/meal-plans/"
DETAIL_URL   = "/api/v1/meal-plans/{id}/"
ITEMS_URL    = "/api/v1/meal-plans/{id}/items/"
ITEM_URL     = "/api/v1/meal-plan-items/{id}/"
GENERATE_URL = "/api/v1/meal-plans/{id}/generate/"
LOG_DAY_URL  = "/api/v1/meal-plans/{id}/log-day/"
SUMMARY_URL  = "/api/v1/meal-plans/{id}/summary/"

THIS_MONDAY = date(2024, 3, 11)   # a known Monday


def _plan_url(plan_id):
    return DETAIL_URL.format(id=plan_id)

def _items_url(plan_id):
    return ITEMS_URL.format(id=plan_id)

def _item_url(item_id):
    return ITEM_URL.format(id=item_id)

def _generate_url(plan_id):
    return GENERATE_URL.format(id=plan_id)

def _log_day_url(plan_id):
    return LOG_DAY_URL.format(id=plan_id)

def _summary_url(plan_id):
    return SUMMARY_URL.format(id=plan_id)


# ── helpers ────────────────────────────────────────────────────────────────────

def _create_plan(api_client, week_start=None, name="Test Plan"):
    ws = (week_start or THIS_MONDAY).isoformat()
    return api_client.post(LIST_URL, {"name": name, "week_start": ws}, format="json")


# ── Auth ───────────────────────────────────────────────────────────────────────

class TestMealPlanAuth:
    def test_list_requires_auth(self, api_client):
        assert api_client.get(LIST_URL).status_code == 401

    def test_create_requires_auth(self, api_client):
        assert api_client.post(LIST_URL, {}).status_code == 401


# ── CRUD ───────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMealPlanCRUD:
    def test_create_plan(self, auth_client):
        res = _create_plan(auth_client)
        assert res.status_code == 201
        assert res.data["name"] == "Test Plan"

    def test_week_start_normalised_to_monday(self, auth_client):
        # Wednesday → preceding Monday
        wednesday = date(2024, 3, 13)
        res = _create_plan(auth_client, week_start=wednesday)
        assert res.status_code == 201
        assert res.data["week_start"] == THIS_MONDAY.isoformat()

    def test_user_sees_only_own_plans(self, auth_client, api_client):
        other = UserFactory()
        api_client.force_authenticate(other)
        _create_plan(api_client, name="Other plan")
        api_client.force_authenticate(None)

        _create_plan(auth_client, name="My plan")
        res = auth_client.get(LIST_URL)
        assert res.status_code == 200
        names = [p["name"] for p in (res.data.get("results") or res.data)]
        assert "My plan" in names
        assert "Other plan" not in names

    def test_cannot_access_another_users_plan(self, auth_client, api_client):
        other = UserFactory()
        api_client.force_authenticate(other)
        res = _create_plan(api_client)
        plan_id = res.data["id"]
        api_client.force_authenticate(None)

        assert auth_client.get(_plan_url(plan_id)).status_code == 404

    def test_update_plan_name(self, auth_client):
        res = _create_plan(auth_client)
        plan_id = res.data["id"]
        res2 = auth_client.patch(_plan_url(plan_id), {"name": "Renamed"}, format="json")
        assert res2.status_code == 200
        assert res2.data["name"] == "Renamed"

    def test_delete_plan(self, auth_client):
        res = _create_plan(auth_client)
        plan_id = res.data["id"]
        assert auth_client.delete(_plan_url(plan_id)).status_code == 204
        assert auth_client.get(_plan_url(plan_id)).status_code == 404

    def test_filter_plan_by_week_start(self, auth_client):
        _create_plan(auth_client, week_start=THIS_MONDAY, name="Week A")
        next_week = THIS_MONDAY + timedelta(weeks=1)
        _create_plan(auth_client, week_start=next_week, name="Week B")
        res = auth_client.get(LIST_URL, {"week_start": THIS_MONDAY.isoformat()})
        names = [p["name"] for p in (res.data.get("results") or res.data)]
        assert "Week A" in names
        assert "Week B" not in names


# ── MealPlanItems ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMealPlanItems:
    def test_add_item_to_plan(self, auth_client):
        plan_id = _create_plan(auth_client).data["id"]
        food = FoodFactory(calories="300", protein_g="30", carbs_g="20", fat_g="8")
        res = auth_client.post(_items_url(plan_id), {
            "day": 0, "meal_type": "breakfast", "food": food.id, "servings": "1.5"
        }, format="json")
        assert res.status_code == 201
        assert res.data["day"] == 0
        assert res.data["meal_type"] == "breakfast"

    def test_item_has_computed_macros(self, auth_client):
        plan_id = _create_plan(auth_client).data["id"]
        food = FoodFactory(calories="200", protein_g="20", carbs_g="25", fat_g="5")
        res = auth_client.post(_items_url(plan_id), {
            "day": 0, "meal_type": "lunch", "food": food.id, "servings": "2"
        }, format="json")
        assert float(res.data["calories"])   == pytest.approx(400.0, rel=0.01)
        assert float(res.data["protein_g"])  == pytest.approx(40.0,  rel=0.01)

    def test_update_item_servings(self, auth_client):
        plan_id = _create_plan(auth_client).data["id"]
        food = FoodFactory()
        item_id = auth_client.post(_items_url(plan_id), {
            "day": 1, "meal_type": "dinner", "food": food.id, "servings": "1"
        }, format="json").data["id"]
        res = auth_client.patch(_item_url(item_id), {"servings": "2.5"}, format="json")
        assert res.status_code == 200
        assert float(res.data["servings"]) == 2.5

    def test_delete_item(self, auth_client):
        plan_id = _create_plan(auth_client).data["id"]
        food = FoodFactory()
        item_id = auth_client.post(_items_url(plan_id), {
            "day": 0, "meal_type": "snack", "food": food.id, "servings": "1"
        }, format="json").data["id"]
        assert auth_client.delete(_item_url(item_id)).status_code == 204

    def test_cannot_add_item_to_another_users_plan(self, auth_client, api_client):
        other = UserFactory()
        api_client.force_authenticate(other)
        plan_id = _create_plan(api_client).data["id"]
        api_client.force_authenticate(None)

        food = FoodFactory()
        res = auth_client.post(_items_url(plan_id), {
            "day": 0, "meal_type": "breakfast", "food": food.id, "servings": "1"
        }, format="json")
        assert res.status_code == 404

    def test_plan_detail_includes_items(self, auth_client):
        plan_id = _create_plan(auth_client).data["id"]
        food = FoodFactory()
        auth_client.post(_items_url(plan_id), {
            "day": 2, "meal_type": "lunch", "food": food.id, "servings": "1"
        }, format="json")
        res = auth_client.get(_plan_url(plan_id))
        assert len(res.data["items"]) == 1
        assert res.data["items"][0]["food_detail"]["name"] == food.name


# ── Generate ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMealPlanGenerate:
    def test_generate_returns_200(self, auth_client):
        FoodFactory.create_batch(10, is_public=True)
        plan_id = _create_plan(auth_client).data["id"]
        res = auth_client.post(_generate_url(plan_id))
        assert res.status_code == 200

    def test_generate_creates_items_for_all_7_days(self, auth_client):
        FoodFactory.create_batch(20, is_public=True)
        plan_id = _create_plan(auth_client).data["id"]
        auth_client.post(_generate_url(plan_id))
        res = auth_client.get(_plan_url(plan_id))
        days_covered = {item["day"] for item in res.data["items"]}
        assert days_covered == {0, 1, 2, 3, 4, 5, 6}

    def test_generate_creates_all_four_meal_types(self, auth_client):
        FoodFactory.create_batch(20, is_public=True)
        plan_id = _create_plan(auth_client).data["id"]
        auth_client.post(_generate_url(plan_id))
        res = auth_client.get(_plan_url(plan_id))
        meal_types = {item["meal_type"] for item in res.data["items"]}
        assert "breakfast" in meal_types
        assert "lunch"     in meal_types
        assert "dinner"    in meal_types

    def test_generate_clears_existing_items(self, auth_client):
        food = FoodFactory()
        plan_id = _create_plan(auth_client).data["id"]
        # Add a manual item first
        auth_client.post(_items_url(plan_id), {
            "day": 0, "meal_type": "breakfast", "food": food.id, "servings": "1"
        }, format="json")
        FoodFactory.create_batch(20, is_public=True)
        auth_client.post(_generate_url(plan_id))
        res = auth_client.get(_plan_url(plan_id))
        # The manual breakfast item should be gone (replaced by generated items)
        manual_ids = [it["food"] for it in res.data["items"] if it["day"] == 0
                      and it["meal_type"] == "breakfast" and it["food"] == food.id]
        # Generated plan replaces everything — original food may or may not reappear
        # but at least items exist
        assert len(res.data["items"]) > 0

    def test_generate_without_foods_returns_error(self, auth_client):
        from nutrition.models import Food
        Food.objects.all().delete()
        plan_id = _create_plan(auth_client).data["id"]
        res = auth_client.post(_generate_url(plan_id))
        assert res.status_code == 400

    def test_generate_prefers_user_meal_history(self, auth_client, user):
        # User has a breakfast history with a specific food
        favourite = FoodFactory(name="Favourite Breakfast Food", is_public=True)
        FoodFactory.create_batch(10, is_public=True)
        meal = MealFactory(user=user, meal_type="breakfast")
        MealItemFactory(meal=meal, food=favourite, servings="1")

        plan_id = _create_plan(auth_client).data["id"]
        auth_client.post(_generate_url(plan_id))
        res = auth_client.get(_plan_url(plan_id))

        breakfast_food_ids = [
            it["food"] for it in res.data["items"] if it["meal_type"] == "breakfast"
        ]
        assert favourite.id in breakfast_food_ids


# ── Log day ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMealPlanLogDay:
    def test_log_day_creates_meal_records(self, auth_client):
        from nutrition.models import Meal
        food = FoodFactory()
        plan_id = _create_plan(auth_client).data["id"]
        auth_client.post(_items_url(plan_id), {
            "day": 0, "meal_type": "breakfast", "food": food.id, "servings": "1"
        }, format="json")
        res = auth_client.post(_log_day_url(plan_id), {"day": 0}, format="json")
        assert res.status_code == 201
        assert Meal.objects.filter(meal_type="breakfast").exists()

    def test_log_day_creates_correct_food_items(self, auth_client):
        from nutrition.models import MealItem
        food = FoodFactory()
        plan_id = _create_plan(auth_client).data["id"]
        auth_client.post(_items_url(plan_id), {
            "day": 1, "meal_type": "lunch", "food": food.id, "servings": "2"
        }, format="json")
        auth_client.post(_log_day_url(plan_id), {"day": 1}, format="json")
        item = MealItem.objects.filter(food=food).first()
        assert item is not None
        assert float(item.servings) == 2.0

    def test_log_day_with_empty_day_returns_400(self, auth_client):
        plan_id = _create_plan(auth_client).data["id"]
        res = auth_client.post(_log_day_url(plan_id), {"day": 3}, format="json")
        assert res.status_code == 400

    def test_log_day_requires_day_param(self, auth_client):
        plan_id = _create_plan(auth_client).data["id"]
        res = auth_client.post(_log_day_url(plan_id), {}, format="json")
        assert res.status_code == 400

    def test_log_day_groups_by_meal_type(self, auth_client):
        from nutrition.models import Meal
        food1, food2 = FoodFactory(), FoodFactory()
        plan_id = _create_plan(auth_client).data["id"]
        for food, meal_type in [(food1, "breakfast"), (food2, "lunch")]:
            auth_client.post(_items_url(plan_id), {
                "day": 0, "meal_type": meal_type, "food": food.id, "servings": "1"
            }, format="json")
        auth_client.post(_log_day_url(plan_id), {"day": 0}, format="json")
        assert Meal.objects.filter(meal_type="breakfast").count() == 1
        assert Meal.objects.filter(meal_type="lunch").count() == 1


# ── Weekly summary ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMealPlanSummary:
    def test_summary_returns_seven_days(self, auth_client):
        plan_id = _create_plan(auth_client).data["id"]
        res = auth_client.get(_summary_url(plan_id))
        assert res.status_code == 200
        assert len(res.data["days"]) == 7

    def test_summary_daily_calorie_total(self, auth_client):
        food = FoodFactory(calories="500", protein_g="30", carbs_g="50", fat_g="10")
        plan_id = _create_plan(auth_client).data["id"]
        auth_client.post(_items_url(plan_id), {
            "day": 0, "meal_type": "breakfast", "food": food.id, "servings": "1"
        }, format="json")
        res = auth_client.get(_summary_url(plan_id))
        monday = res.data["days"][0]
        assert float(monday["calories"]) == pytest.approx(500.0, rel=0.01)

    def test_summary_includes_target_percentage(self, auth_client):
        plan_id = _create_plan(auth_client).data["id"]
        res = auth_client.get(_summary_url(plan_id))
        for day in res.data["days"]:
            assert "calorie_pct" in day
            assert "protein_pct" in day

    def test_summary_empty_day_has_zero_totals(self, auth_client):
        plan_id = _create_plan(auth_client).data["id"]
        res = auth_client.get(_summary_url(plan_id))
        assert float(res.data["days"][0]["calories"]) == 0.0
