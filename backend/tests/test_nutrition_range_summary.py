"""Tests for the /nutrition/meals/range_summary/ endpoint and its
supporting service functions.

Covers:
- Empty range (no crashes, zero aggregate)
- Single-day parity with the existing daily_summary contract
- Weekly bucketing across an ISO week boundary
- Adherence math + streak tracking against calorie_goal
- Versioned cache: hit on repeat, miss after a Meal write
- Cross-user isolation and unauthenticated access
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone

from fitness_tracker import cache_keys
from nutrition.services import (
    MAX_RANGE_DAYS,
    RangeRequest,
    _bucket_key,
    compute_range_summary,
    parse_range,
)
from tests.factories import (
    FoodFactory,
    MealFactory,
    MealItemFactory,
    WaterLogFactory,
)

RANGE_URL = "/api/v1/nutrition/meals/range_summary/"


def _at(local_date: date, hour: int = 12) -> datetime:
    """Build a timezone-aware datetime for a local calendar date."""
    return timezone.make_aware(datetime.combine(local_date, time(hour, 0)))


# ---------------------------------------------------------------------------
# parse_range — pure input validation, no DB
# ---------------------------------------------------------------------------

class TestParseRange:
    def test_defaults_to_last_30_days_ending_today(self):
        today = date(2026, 6, 15)
        req = parse_range(None, None, None, today=today)
        assert req.end == today
        assert req.start == today - timedelta(days=29)
        assert req.granularity == "day"
        assert req.days == 30

    def test_accepts_explicit_range_and_granularity(self):
        req = parse_range("2026-01-01", "2026-01-31", "week")
        assert req.start == date(2026, 1, 1)
        assert req.end == date(2026, 1, 31)
        assert req.granularity == "week"

    def test_rejects_start_after_end(self):
        with pytest.raises(ValueError, match="start must be on or before end"):
            parse_range("2026-02-01", "2026-01-01", "day")

    def test_rejects_unknown_granularity(self):
        with pytest.raises(ValueError, match="granularity"):
            parse_range("2026-01-01", "2026-01-02", "quarterly")

    def test_rejects_range_over_the_cap(self):
        # 400 days exceeds MAX_RANGE_DAYS.
        with pytest.raises(ValueError, match="range cannot exceed"):
            parse_range("2024-01-01", "2025-02-04", "day")

    def test_accepts_range_exactly_at_cap(self):
        # boundary: an exact MAX_RANGE_DAYS window is fine
        end = date(2026, 12, 31)
        start = end - timedelta(days=MAX_RANGE_DAYS - 1)
        assert parse_range(start.isoformat(), end.isoformat(), "day").days == MAX_RANGE_DAYS


# ---------------------------------------------------------------------------
# _bucket_key — deterministic mapping used by both aggregate and streak logic
# ---------------------------------------------------------------------------

class TestBucketKey:
    def test_day_bucket_is_the_day(self):
        d = date(2026, 6, 15)
        assert _bucket_key(d, "day") == d

    def test_week_bucket_is_iso_monday(self):
        # 2026-06-17 is a Wednesday → Monday of that week is 2026-06-15.
        assert _bucket_key(date(2026, 6, 17), "week") == date(2026, 6, 15)
        # Monday itself is its own bucket.
        assert _bucket_key(date(2026, 6, 15), "week") == date(2026, 6, 15)
        # Sunday belongs to the week that started on the previous Monday.
        assert _bucket_key(date(2026, 6, 21), "week") == date(2026, 6, 15)

    def test_month_bucket_is_first_of_month(self):
        assert _bucket_key(date(2026, 6, 30), "month") == date(2026, 6, 1)


# ---------------------------------------------------------------------------
# Service-level aggregation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestComputeRangeSummary:
    def test_empty_range_returns_zero_aggregate_and_full_bucket_list(self, user):
        req = parse_range("2026-06-01", "2026-06-07", "day")
        out = compute_range_summary(user, req)
        assert out["range"]["days"] == 7
        assert len(out["buckets"]) == 7  # one zero-bucket per day, so charts have a baseline
        assert all(b["calories"] == 0.0 for b in out["buckets"])
        assert out["aggregate"]["days_logged"] == 0
        assert out["aggregate"]["avg_calories"] == 0.0
        assert out["aggregate"]["min_calories_day"] is None
        assert out["adherence"]["days_on_target"] == 0

    def test_single_day_matches_daily_summary_totals(self, auth_client, user, food):
        """A range of one day must agree with the existing daily_summary endpoint.

        Prevents drift between the two aggregation paths — the whole point of
        range_summary is that a 1-day range is just a day. If these disagree
        the frontend can't trust either.
        """
        today = timezone.localdate()
        meal = MealFactory(user=user, consumed_at=_at(today))
        MealItemFactory(meal=meal, food=food, servings="2.00")

        daily = auth_client.get(
            "/api/v1/nutrition/meals/daily_summary/", {"date": today.isoformat()}
        ).data
        req = parse_range(today.isoformat(), today.isoformat(), "day")
        ranged = compute_range_summary(user, req)

        assert ranged["buckets"][0]["calories"] == daily["totals"]["calories"]
        assert ranged["buckets"][0]["protein_g"] == daily["totals"]["protein_g"]
        assert ranged["aggregate"]["days_logged"] == 1

    def test_weekly_bucketing_sums_across_iso_week(self, user, food):
        """Meals logged on different weekdays should collapse into one weekly bucket."""
        # 2026-06-15 is a Monday; 2026-06-17 is a Wednesday of the same ISO week.
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(date(2026, 6, 15))), food=food)
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(date(2026, 6, 17))), food=food)

        req = parse_range("2026-06-15", "2026-06-21", "week")
        out = compute_range_summary(user, req)
        assert len(out["buckets"]) == 1  # both meals fall in the same weekly bucket
        assert out["buckets"][0]["date"] == "2026-06-15"
        # Food default (see factories.py) is 200 kcal/serving → 2 servings = 400 kcal.
        assert out["buckets"][0]["calories"] == pytest.approx(400.0)
        assert out["aggregate"]["days_logged"] == 2  # two distinct local days

    def test_min_max_ignores_empty_buckets(self, user, food):
        """Zero-calorie buckets exist for the chart baseline but must not
        pollute min_calories_day (otherwise every user with a rest day has
        a "0 kcal" minimum, which is meaningless)."""
        d1, d2 = date(2026, 6, 15), date(2026, 6, 17)
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(d1)), food=food, servings="1.00")
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(d2)), food=food, servings="3.00")

        req = parse_range("2026-06-15", "2026-06-21", "day")
        out = compute_range_summary(user, req)
        agg = out["aggregate"]
        # Empty buckets exist in `buckets` but are excluded from min/max.
        assert agg["min_calories_day"]["value"] == pytest.approx(200.0)
        assert agg["max_calories_day"]["value"] == pytest.approx(600.0)
        assert agg["min_calories_day"]["date"] != agg["max_calories_day"]["date"]


# ---------------------------------------------------------------------------
# Adherence + streak logic
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdherence:
    def test_no_calorie_goal_returns_neutral_shape(self, user, food):
        # profile.daily_calorie_goal is None by default.
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(timezone.localdate())), food=food)
        req = parse_range(None, None, "day")
        out = compute_range_summary(user, req)
        assert out["adherence"]["calorie_goal"] is None
        assert out["adherence"]["days_on_target"] == 0
        assert out["adherence"]["current_streak_days"] == 0

    def test_days_within_tolerance_count_as_on_target(self, user):
        user.profile.daily_calorie_goal = 2000
        user.profile.save(update_fields=["daily_calorie_goal"])

        # Custom food so we can hit the tolerance band exactly.
        food_target = FoodFactory(calories="2000.00", protein_g="0", carbs_g="0", fat_g="0")
        food_low = FoodFactory(calories="1500.00", protein_g="0", carbs_g="0", fat_g="0")  # off-target

        base = date(2026, 6, 15)
        # d0 on-target, d1 off, d2 on, d3 on → longest streak 2 ending at d3
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(base + timedelta(days=0))), food=food_target)
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(base + timedelta(days=1))), food=food_low)
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(base + timedelta(days=2))), food=food_target)
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(base + timedelta(days=3))), food=food_target)

        req = parse_range(base.isoformat(), (base + timedelta(days=3)).isoformat(), "day")
        adherence = compute_range_summary(user, req)["adherence"]
        assert adherence["days_on_target"] == 3
        assert adherence["longest_streak_days"] == 2
        assert adherence["current_streak_days"] == 2  # streak ending at req.end
        assert adherence["on_target_pct"] == 75.0

    def test_untracked_day_breaks_streak(self, user):
        user.profile.daily_calorie_goal = 2000
        user.profile.save(update_fields=["daily_calorie_goal"])
        food_target = FoodFactory(calories="2000.00", protein_g="0", carbs_g="0", fat_g="0")

        base = date(2026, 6, 15)
        # Two on-target days, then a gap, then one more on-target day.
        for offset in (0, 1, 3):
            MealItemFactory(
                meal=MealFactory(user=user, consumed_at=_at(base + timedelta(days=offset))),
                food=food_target,
            )
        req = parse_range(base.isoformat(), (base + timedelta(days=3)).isoformat(), "day")
        adherence = compute_range_summary(user, req)["adherence"]
        assert adherence["days_on_target"] == 3
        assert adherence["longest_streak_days"] == 2  # broken by the gap
        assert adherence["current_streak_days"] == 1


# ---------------------------------------------------------------------------
# Endpoint — HTTP-level contract, permissions, caching behaviour
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRangeSummaryEndpoint:
    def test_defaults_to_last_30_days(self, auth_client):
        res = auth_client.get(RANGE_URL)
        assert res.status_code == 200
        assert res.data["range"]["granularity"] == "day"
        assert res.data["range"]["days"] == 30

    def test_returns_400_on_bad_granularity(self, auth_client):
        res = auth_client.get(RANGE_URL, {"granularity": "century"})
        assert res.status_code == 400
        assert "granularity" in res.data["detail"]

    def test_returns_400_when_start_after_end(self, auth_client):
        res = auth_client.get(RANGE_URL, {"start": "2026-02-01", "end": "2026-01-01"})
        assert res.status_code == 400

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(RANGE_URL)
        assert res.status_code == 401

    def test_excludes_other_users_meals(self, auth_client, user, other_user, food):
        MealItemFactory(
            meal=MealFactory(user=other_user, consumed_at=_at(timezone.localdate())),
            food=food,
        )
        res = auth_client.get(RANGE_URL)
        assert res.status_code == 200
        assert res.data["aggregate"]["days_logged"] == 0

    def test_response_shape_includes_top_foods(self, auth_client, user, food):
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(timezone.localdate())), food=food)
        res = auth_client.get(RANGE_URL)
        assert res.status_code == 200
        assert res.data["top_foods"][0]["name"] == food.name
        assert res.data["top_foods"][0]["times_logged"] == 1

    def test_cache_is_invalidated_when_a_meal_is_added(self, auth_client, user, food):
        cache.clear()

        first = auth_client.get(RANGE_URL).data
        assert first["aggregate"]["days_logged"] == 0

        # Signal on Meal save must bump the user's nutrition_version so the
        # previous cached payload is orphaned — the second read must reflect
        # the new meal even though the URL is byte-for-byte identical.
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(timezone.localdate())), food=food)

        second = auth_client.get(RANGE_URL).data
        assert second["aggregate"]["days_logged"] == 1
        assert second["aggregate"]["avg_calories"] > 0


@pytest.mark.django_db
class TestNutritionVersionSignal:
    """The version counter is the linchpin of range-cache invalidation, so
    unit-test its behaviour independently of the endpoint."""

    def test_meal_write_bumps_version(self, user, food):
        cache.clear()
        # Force the counter to exist so incr succeeds on the first bump.
        cache.set(cache_keys.nutrition_version(user.id), 1, None)
        MealItemFactory(meal=MealFactory(user=user, consumed_at=_at(timezone.localdate())), food=food)
        assert cache.get(cache_keys.nutrition_version(user.id)) > 1

    def test_water_write_bumps_version(self, user):
        cache.clear()
        cache.set(cache_keys.nutrition_version(user.id), 5, None)
        WaterLogFactory(user=user, logged_at=timezone.now())
        assert cache.get(cache_keys.nutrition_version(user.id)) > 5

    def test_other_users_write_does_not_bump_this_users_version(self, user, other_user, food):
        cache.clear()
        cache.set(cache_keys.nutrition_version(user.id), 7, None)
        MealItemFactory(
            meal=MealFactory(user=other_user, consumed_at=_at(timezone.localdate())),
            food=food,
        )
        assert cache.get(cache_keys.nutrition_version(user.id)) == 7
