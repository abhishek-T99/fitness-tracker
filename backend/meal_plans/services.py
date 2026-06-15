"""
Meal plan generation service.

Algorithm (no ML — pure data-driven):
  1. For each meal type, pull the user's most-logged foods (last 90 days).
  2. Rotate them across the 7 days so no meal repeats two days in a row.
  3. Adjust servings so each day approximately hits the calorie target.
  4. Fall back to the most-popular public foods when history is thin.

Calorie split across meal types:
  Breakfast 25 % · Lunch 35 % · Dinner 30 % · Snack 10 %
"""
import math
import random
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from .models import MealPlanItem, MEAL_TYPES


MEAL_CALORIE_SPLIT = {
    "breakfast": 0.25,
    "lunch":     0.35,
    "dinner":    0.30,
    "snack":     0.10,
}

# How many different food options to rotate per meal type per week
OPTIONS_PER_SLOT = 3


def _daily_calorie_target(user) -> float:
    profile = getattr(user, "profile", None)
    return float(getattr(profile, "daily_calorie_goal", None) or 2000)


def _daily_protein_target(user) -> float:
    """0.8 g per kg bodyweight, or 30 % of calories / 4."""
    from measurements.models import BodyMeasurement
    latest = BodyMeasurement.objects.filter(user=user).order_by("-recorded_at").first()
    if latest and latest.weight_kg:
        return float(latest.weight_kg) * 1.8
    return _daily_calorie_target(user) * 0.30 / 4


def _user_food_history(user, meal_type: str, limit: int = 10):
    """Return the most-frequently logged foods for a given meal type."""
    from nutrition.models import MealItem
    since = timezone.now() - timedelta(days=90)
    qs = (
        MealItem.objects
        .filter(meal__user=user, meal__meal_type=meal_type, meal__consumed_at__gte=since)
        .values("food")
        .annotate(freq=Count("id"))
        .order_by("-freq")[:limit]
    )
    food_ids = [r["food"] for r in qs]
    from nutrition.models import Food
    foods = {f.id: f for f in Food.objects.filter(id__in=food_ids)}
    return [foods[fid] for fid in food_ids if fid in foods]


def _fallback_foods(meal_type: str, limit: int = 10):
    """Public foods sorted by protein (best nutritional bang for the buck)."""
    from nutrition.models import Food
    return list(
        Food.objects.filter(is_public=True)
        .order_by("-protein_g")[:limit]
    )


def _servings_to_hit_target(food, target_calories: float) -> float:
    """Calculate servings that get close to the calorie target."""
    if not food.calories or float(food.calories) == 0:
        return 1.0
    raw = target_calories / float(food.calories)
    # Round to nearest 0.25 serving, clamp between 0.5 and 4
    rounded = round(raw * 4) / 4
    return max(0.5, min(4.0, rounded))


def generate_plan(plan) -> int:
    """
    Fill *plan* with generated MealPlanItems.
    Returns the total number of items created.
    Raises ValueError if no foods are available.
    """
    from nutrition.models import Food
    if not Food.objects.filter(is_public=True).exists():
        raise ValueError("No public foods available to generate a plan.")

    user          = plan.user
    daily_cal     = _daily_calorie_target(user)

    # Wipe any existing items
    plan.items.all().delete()

    created = 0
    for meal_type, split in MEAL_CALORIE_SPLIT.items():
        target_cal = daily_cal * split

        # Gather food options: prefer history, top-up with fallback
        history  = _user_food_history(user, meal_type, limit=10)
        fallback = _fallback_foods(meal_type, limit=15)
        # Merge: history first, then fallback (de-duplicated)
        seen_ids = {f.id for f in history}
        combined = history + [f for f in fallback if f.id not in seen_ids]
        options  = combined[:OPTIONS_PER_SLOT * 3] or fallback

        if not options:
            continue

        # Rotate options across 7 days to avoid repetition
        for day in range(7):
            food = options[day % len(options)]
            servings = _servings_to_hit_target(food, target_cal)
            MealPlanItem.objects.create(
                plan=plan, day=day, meal_type=meal_type,
                food=food, servings=servings, order=0,
            )
            created += 1

    return created
