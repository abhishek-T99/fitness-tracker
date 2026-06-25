"""Nutrition tools — search the food catalogue and write meal/water logs.

Write tools route through the existing DRF serializers so signals
(XP, cache invalidation, challenges) keep firing exactly as they would
for a normal API call.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from django.db.models import Q
from rest_framework.exceptions import ValidationError as DRFValidationError

from nutrition.models import Food
from nutrition.serializers import FoodSerializer, MealSerializer, WaterLogSerializer

from ..registry import tool


# ── search_foods ────────────────────────────────────────────────────────────

@tool(
    name="search_foods",
    description=(
        "Search the food catalogue by name or brand. Always call this BEFORE "
        "create_food — only create a new food entry when no reasonable match exists. "
        "Returns up to `limit` matches with id, name, brand, serving size, and macros "
        "per serving. Public foods are visible to everyone; private foods only to their "
        "creator (the current user)."
    ),
    schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search string — matched against name and brand (case-insensitive).",
            },
            "limit": {
                "type": "integer",
                "description": "Max results to return (1-20).",
                "minimum": 1,
                "maximum": 20,
            },
        },
        "required": ["query"],
    },
    kind="read",
)
def search_foods(*, user, query: str, limit: int = 10, **_) -> Dict[str, Any]:
    limit = max(1, min(20, int(limit)))
    qs = (
        Food.objects.filter(Q(is_public=True) | Q(created_by=user))
        .filter(Q(name__icontains=query) | Q(brand__icontains=query))
        .order_by("name")[:limit]
    )
    return {
        "query": query,
        "results": [
            {
                "id": f.id,
                "name": f.name,
                "brand": f.brand or "",
                "serving_size": float(f.serving_size) if f.serving_size is not None else None,
                "serving_unit": f.serving_unit,
                "calories": float(f.calories),
                "protein_g": float(f.protein_g),
                "carbs_g": float(f.carbs_g),
                "fat_g": float(f.fat_g),
            }
            for f in qs
        ],
    }


# ── create_food ─────────────────────────────────────────────────────────────

@tool(
    name="create_food",
    description=(
        "Create a private food entry for this user when no acceptable match exists in "
        "the catalogue. Use realistic per-serving macros; if you're unsure, ask the user "
        "rather than guessing. The food is created as private (is_public=false) and "
        "owned by the current user."
    ),
    schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Food name (e.g. 'Boiled Egg')."},
            "brand": {"type": "string", "description": "Optional brand."},
            "serving_size": {
                "type": "number",
                "description": "Amount per serving (e.g. 50 for one 50g egg).",
            },
            "serving_unit": {
                "type": "string",
                "description": "Unit for serving_size: 'g', 'ml', 'piece', 'cup', etc.",
            },
            "calories": {"type": "number", "description": "kcal per serving."},
            "protein_g": {"type": "number", "description": "Protein grams per serving."},
            "carbs_g": {"type": "number", "description": "Carbs grams per serving."},
            "fat_g": {"type": "number", "description": "Fat grams per serving."},
            "fiber_g": {"type": "number", "description": "Optional fibre grams per serving."},
            "sugar_g": {"type": "number", "description": "Optional sugar grams per serving."},
        },
        "required": ["name", "calories", "protein_g", "carbs_g", "fat_g"],
    },
    kind="write",
)
def create_food(*, user, **payload) -> Dict[str, Any]:
    serializer = FoodSerializer(data=payload)
    try:
        serializer.is_valid(raise_exception=True)
    except DRFValidationError as exc:
        return {"error": "validation_failed", "details": exc.detail}
    food = serializer.save(created_by=user, is_public=False)
    return {
        "id": food.id,
        "name": food.name,
        "calories": float(food.calories),
        "protein_g": float(food.protein_g),
    }


# ── create_meal ─────────────────────────────────────────────────────────────

@tool(
    name="create_meal",
    description=(
        "Log a meal with one or more food items. Each item references a food by ID "
        "(use search_foods first to find it) and a servings count. consumed_at must be "
        "an ISO 8601 datetime; if the user said 'I just had ...', call "
        "get_current_datetime first. meal_type is one of: breakfast, lunch, dinner, snack."
    ),
    schema={
        "type": "object",
        "properties": {
            "meal_type": {
                "type": "string",
                "enum": ["breakfast", "lunch", "dinner", "snack"],
            },
            "consumed_at": {
                "type": "string",
                "description": "ISO 8601 datetime (with timezone or interpreted as user-local).",
            },
            "items": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "food_id": {"type": "integer", "description": "ID from search_foods."},
                        "servings": {
                            "type": "number",
                            "description": "Number of servings (e.g. 2 for two eggs).",
                            "minimum": 0.01,
                        },
                    },
                    "required": ["food_id", "servings"],
                },
            },
            "notes": {"type": "string", "description": "Optional free-form notes."},
        },
        "required": ["meal_type", "consumed_at", "items"],
    },
    kind="write",
)
def create_meal(
    *,
    user,
    meal_type: str,
    consumed_at: str,
    items: List[Dict[str, Any]],
    notes: str = "",
    **_,
) -> Dict[str, Any]:
    # The MealSerializer expects items with a "food" key (FK), not "food_id".
    normalised_items = []
    for it in items:
        normalised_items.append({"food": it["food_id"], "servings": it["servings"]})

    payload = {
        "meal_type": meal_type,
        "consumed_at": consumed_at,
        "items": normalised_items,
    }
    if notes:
        payload["notes"] = notes

    # MealSerializer.create reads self.context["request"].user — provide a
    # minimal shim so we don't need a real Request object.
    serializer = MealSerializer(data=payload, context={"request": _RequestShim(user)})
    try:
        serializer.is_valid(raise_exception=True)
    except DRFValidationError as exc:
        return {"error": "validation_failed", "details": exc.detail}
    meal = serializer.save()
    return {
        "id": meal.id,
        "meal_type": meal.meal_type,
        "consumed_at": meal.consumed_at.isoformat() if meal.consumed_at else None,
        "item_count": meal.items.count(),
    }


# ── create_water_log ────────────────────────────────────────────────────────

@tool(
    name="create_water_log",
    description=(
        "Log a water intake entry. amount_ml is the volume drunk in millilitres. "
        "logged_at must be an ISO 8601 datetime; call get_current_datetime if the user "
        "said 'just now' or 'I just drank'. Common conversions: 1 cup ≈ 240 ml, "
        "1 small bottle ≈ 330-500 ml, 1 large bottle ≈ 750-1000 ml."
    ),
    schema={
        "type": "object",
        "properties": {
            "amount_ml": {
                "type": "integer",
                "description": "Water volume in millilitres.",
                "minimum": 1,
            },
            "logged_at": {
                "type": "string",
                "description": "ISO 8601 datetime.",
            },
        },
        "required": ["amount_ml", "logged_at"],
    },
    kind="write",
)
def create_water_log(*, user, amount_ml: int, logged_at: str, **_) -> Dict[str, Any]:
    serializer = WaterLogSerializer(data={"amount_ml": amount_ml, "logged_at": logged_at})
    try:
        serializer.is_valid(raise_exception=True)
    except DRFValidationError as exc:
        return {"error": "validation_failed", "details": exc.detail}
    log = serializer.save(user=user)
    return {
        "id": log.id,
        "amount_ml": log.amount_ml,
        "logged_at": log.logged_at.isoformat() if log.logged_at else None,
    }


class _RequestShim:
    """Just enough of an HttpRequest to satisfy serializers that need `.user`."""

    def __init__(self, user):
        self.user = user
