"""Business logic for the nutrition app.

Views should stay thin — parse input, delegate here, wrap the result. Keeping
the aggregations pure functions also makes them trivial to unit-test without
building an APIClient.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable

from django.db.models import Count, Sum
from django.utils import timezone

from .models import Meal, MealItem, WaterLog

# Adherence tolerance — a day counts as "on target" if daily calories land within
# ±10% of the profile's daily_calorie_goal. Tight enough to reward discipline,
# loose enough that a single 200-kcal treat doesn't break the streak.
_ADHERENCE_TOLERANCE = 0.10

_MACRO_KEYS = ("calories", "protein_g", "carbs_g", "fat_g")

# Fitness-app scale: guard against range explosion (e.g. accidental start=1970),
# not against malicious payloads. 366 covers "last year" which is the widest
# useful window we expose on the frontend.
MAX_RANGE_DAYS = 366

VALID_GRANULARITIES = ("day", "week", "month")


@dataclass(frozen=True)
class RangeRequest:
    start: date
    end: date  # inclusive
    granularity: str  # one of VALID_GRANULARITIES

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def parse_range(
    start_str: str | None,
    end_str: str | None,
    granularity: str | None,
    *,
    today: date | None = None,
) -> RangeRequest:
    """Normalise query params. Defaults: last 30 days, day granularity.

    Raises ValueError with a user-safe message on bad input — the view maps
    that to a 400.
    """
    today = today or timezone.localdate()
    gran = (granularity or "day").lower()
    if gran not in VALID_GRANULARITIES:
        raise ValueError(f"granularity must be one of {VALID_GRANULARITIES}")

    end = date.fromisoformat(end_str) if end_str else today
    start = date.fromisoformat(start_str) if start_str else end - timedelta(days=29)

    if start > end:
        raise ValueError("start must be on or before end")
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise ValueError(f"range cannot exceed {MAX_RANGE_DAYS} days")

    return RangeRequest(start=start, end=end, granularity=gran)


def _bucket_key(day: date, granularity: str) -> date:
    """Return the canonical bucket-start date for a given day.

    - day     → the day itself
    - week    → Monday of that week (ISO)
    - month   → first of that month
    """
    if granularity == "day":
        return day
    if granularity == "week":
        return day - timedelta(days=day.weekday())
    if granularity == "month":
        return day.replace(day=1)
    raise ValueError(granularity)  # pragma: no cover — parse_range gates this


def _zero_macros() -> dict[str, float]:
    return {k: 0.0 for k in _MACRO_KEYS}


def _empty_bucket(bucket_date: date) -> dict:
    return {"date": bucket_date.isoformat(), **_zero_macros(), "water_ml": 0}


def _iter_bucket_dates(req: RangeRequest) -> Iterable[date]:
    """Yield every bucket-start between req.start and req.end, inclusive."""
    seen: set[date] = set()
    cursor = req.start
    while cursor <= req.end:
        key = _bucket_key(cursor, req.granularity)
        if key not in seen:
            seen.add(key)
            yield key
        cursor += timedelta(days=1)


def compute_range_summary(user, req: RangeRequest) -> dict:
    """Aggregate macros, water, adherence, and top foods over a date range.

    Bucketing happens in Python against the server-local date (matching
    daily_summary), so DST/timezone behaviour stays consistent with the rest
    of the read path.
    """
    start_dt = timezone.make_aware(datetime.combine(req.start, time.min))
    end_dt = timezone.make_aware(datetime.combine(req.end, time.max))

    meals = (
        Meal.objects.for_user(user)
        .filter(consumed_at__range=(start_dt, end_dt))
        .prefetch_related("items__food")
    )

    buckets: dict[date, dict] = {b: _empty_bucket(b) for b in _iter_bucket_dates(req)}
    days_with_meals: set[date] = set()

    for meal in meals:
        local_day = timezone.localtime(meal.consumed_at).date()
        bucket_date = _bucket_key(local_day, req.granularity)
        bucket = buckets.setdefault(bucket_date, _empty_bucket(bucket_date))
        totals = meal.totals
        for k in _MACRO_KEYS:
            bucket[k] += totals[k]
        days_with_meals.add(local_day)

    water_qs = (
        WaterLog.objects.for_user(user)
        .filter(logged_at__range=(start_dt, end_dt))
    )
    for log in water_qs:
        local_day = timezone.localtime(log.logged_at).date()
        bucket_date = _bucket_key(local_day, req.granularity)
        bucket = buckets.setdefault(bucket_date, _empty_bucket(bucket_date))
        bucket["water_ml"] += log.amount_ml

    ordered_buckets = [
        {**b, **{k: round(b[k], 1) for k in _MACRO_KEYS}}
        for b in sorted(buckets.values(), key=lambda x: x["date"])
    ]

    calorie_goal = getattr(getattr(user, "profile", None), "daily_calorie_goal", None)
    aggregate = _aggregate(ordered_buckets, days_with_meals, req.days)
    adherence = _adherence(user, req, calorie_goal)
    top_foods = _top_foods(user, start_dt, end_dt)

    return {
        "range": {
            "start": req.start.isoformat(),
            "end": req.end.isoformat(),
            "granularity": req.granularity,
            "days": req.days,
        },
        "buckets": ordered_buckets,
        "aggregate": aggregate,
        "adherence": adherence,
        "top_foods": top_foods,
    }


def _aggregate(buckets: list[dict], days_with_meals: set[date], total_days: int) -> dict:
    """Roll bucket-level numbers up to headline stats for the summary cards."""
    days_logged = len(days_with_meals)
    totals = _zero_macros()
    total_water = 0
    min_day: dict | None = None
    max_day: dict | None = None

    for b in buckets:
        for k in _MACRO_KEYS:
            totals[k] += b[k]
        total_water += b["water_ml"]
        cal = b["calories"]
        # Skip empty buckets when computing min/max so a zero day doesn't
        # masquerade as the user's best/worst.
        if cal > 0:
            if min_day is None or cal < min_day["value"]:
                min_day = {"date": b["date"], "value": round(cal, 1)}
            if max_day is None or cal > max_day["value"]:
                max_day = {"date": b["date"], "value": round(cal, 1)}

    def avg(x: float) -> float:
        return round(x / days_logged, 1) if days_logged else 0.0

    protein_kcal = totals["protein_g"] * 4
    carbs_kcal = totals["carbs_g"] * 4
    fat_kcal = totals["fat_g"] * 9
    macro_kcal_total = protein_kcal + carbs_kcal + fat_kcal
    if macro_kcal_total > 0:
        macro_split = {
            "protein": round(protein_kcal / macro_kcal_total * 100, 1),
            "carbs": round(carbs_kcal / macro_kcal_total * 100, 1),
            "fat": round(fat_kcal / macro_kcal_total * 100, 1),
        }
    else:
        macro_split = {"protein": 0.0, "carbs": 0.0, "fat": 0.0}

    return {
        "days_in_range": total_days,
        "days_logged": days_logged,
        "avg_calories": avg(totals["calories"]),
        "avg_protein_g": avg(totals["protein_g"]),
        "avg_carbs_g": avg(totals["carbs_g"]),
        "avg_fat_g": avg(totals["fat_g"]),
        "avg_water_ml": round(total_water / days_logged) if days_logged else 0,
        "total_calories": round(totals["calories"], 1),
        "min_calories_day": min_day,
        "max_calories_day": max_day,
        "macro_split_pct": macro_split,
    }


def _adherence(user, req: RangeRequest, calorie_goal: int | None) -> dict:
    """Daily adherence against the user's calorie goal.

    Always uses per-day granularity — computing "on-target days" against a
    weekly bucket would double-count off days.
    """
    if not calorie_goal:
        return {
            "calorie_goal": None,
            "days_on_target": 0,
            "on_target_pct": 0.0,
            "current_streak_days": 0,
            "longest_streak_days": 0,
        }

    day_totals = _per_day_calories(user, req.start, req.end)

    lower = calorie_goal * (1 - _ADHERENCE_TOLERANCE)
    upper = calorie_goal * (1 + _ADHERENCE_TOLERANCE)

    days_on_target = 0
    longest = current = 0
    running = 0
    # Walk in date order so streak accounting is trivial. Days with no meals
    # logged don't count as on-target — you can't hit a goal you didn't track.
    cursor = req.start
    while cursor <= req.end:
        cal = day_totals.get(cursor, 0.0)
        on_target = cal > 0 and lower <= cal <= upper
        if on_target:
            days_on_target += 1
            running += 1
            longest = max(longest, running)
        else:
            running = 0
        # `current_streak_days` is the streak ending on req.end (or today if
        # end is in the future) — the user's live streak, not the max.
        if cursor == req.end:
            current = running
        cursor += timedelta(days=1)

    return {
        "calorie_goal": calorie_goal,
        "tolerance_pct": round(_ADHERENCE_TOLERANCE * 100),
        "days_on_target": days_on_target,
        "on_target_pct": round(days_on_target / req.days * 100, 1) if req.days else 0.0,
        "current_streak_days": current,
        "longest_streak_days": longest,
    }


def _per_day_calories(user, start: date, end: date) -> dict[date, float]:
    """Total calories per local date across the range."""
    start_dt = timezone.make_aware(datetime.combine(start, time.min))
    end_dt = timezone.make_aware(datetime.combine(end, time.max))
    out: dict[date, float] = {}
    for meal in (
        Meal.objects.for_user(user)
        .filter(consumed_at__range=(start_dt, end_dt))
        .prefetch_related("items__food")
    ):
        day = timezone.localtime(meal.consumed_at).date()
        out[day] = out.get(day, 0.0) + meal.totals["calories"]
    return out


def _top_foods(user, start_dt: datetime, end_dt: datetime, limit: int = 5) -> list[dict]:
    """Foods logged most often in the range, with total kcal contributed."""
    rows = (
        MealItem.objects.filter(
            meal__user=user, meal__consumed_at__range=(start_dt, end_dt)
        )
        .values("food_id", "food__name")
        .annotate(times_logged=Count("id"), total_servings=Sum("servings"))
        .order_by("-times_logged", "food__name")[:limit]
    )
    out: list[dict] = []
    for row in rows:
        # calories aren't a stored column on MealItem (it's a property), so we
        # can't Sum them in SQL. Fall back to two lookups; top-N is small.
        from .models import Food

        food = Food.objects.filter(pk=row["food_id"]).only("calories").first()
        total_cal = (
            round(float(food.calories) * float(row["total_servings"] or 0), 1)
            if food
            else 0.0
        )
        out.append(
            {
                "food_id": row["food_id"],
                "name": row["food__name"],
                "times_logged": row["times_logged"],
                "total_calories": total_cal,
            }
        )
    return out
