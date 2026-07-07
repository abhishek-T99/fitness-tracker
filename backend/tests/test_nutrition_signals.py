"""
Tests for nutrition/signals.py — verifies that the weekly challenges
"log_water" and "log_meals" count distinct days, not total log entries.

Regression: previously every WaterLog/Meal creation incremented the
challenge counter, so logging water 7× on one day completed a
"log water for 5 days" challenge immediately.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from levels.models import UserWeeklyChallenge, WeeklyChallenge
from tests.factories import MealFactory, UserFactory, WaterLogFactory


def _make_challenge(challenge_type: str, target: int, week_start):
    return WeeklyChallenge.objects.create(
        week_start=week_start,
        challenge_type=challenge_type,
        target_value=target,
        xp_reward=100,
        description=f"Test {challenge_type}",
    )


def _current_value(user, challenge) -> int:
    uc = UserWeeklyChallenge.objects.filter(user=user, challenge=challenge).first()
    return uc.current_value if uc else 0


def _week_start():
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


# ---------------------------------------------------------------------------
# WaterLog challenge — log_water
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWaterLogChallenge:
    def setup_method(self):
        self.user = UserFactory()
        self.challenge = _make_challenge("log_water", 5, _week_start())

    def test_first_log_of_day_increments_challenge(self):
        WaterLogFactory(user=self.user, logged_at=timezone.now())
        assert _current_value(self.user, self.challenge) == 1

    def test_multiple_logs_same_day_count_as_one(self):
        now = timezone.now()
        WaterLogFactory(user=self.user, logged_at=now)
        WaterLogFactory(user=self.user, logged_at=now + timedelta(hours=1))
        WaterLogFactory(user=self.user, logged_at=now + timedelta(hours=3))
        assert _current_value(self.user, self.challenge) == 1

    def test_seven_logs_same_day_does_not_complete_five_day_challenge(self):
        now = timezone.now()
        for i in range(7):
            WaterLogFactory(user=self.user, logged_at=now + timedelta(hours=i))
        uc = UserWeeklyChallenge.objects.get(user=self.user, challenge=self.challenge)
        assert uc.current_value == 1
        assert not uc.completed

    def test_logs_on_distinct_days_each_increment_challenge(self):
        base = timezone.now()
        for day_offset in range(5):
            WaterLogFactory(user=self.user, logged_at=base + timedelta(days=day_offset))
        uc = UserWeeklyChallenge.objects.get(user=self.user, challenge=self.challenge)
        assert uc.current_value == 5
        assert uc.completed

    def test_challenge_completes_only_after_required_distinct_days(self):
        base = timezone.now()
        for day_offset in range(4):
            WaterLogFactory(user=self.user, logged_at=base + timedelta(days=day_offset))
        uc = UserWeeklyChallenge.objects.get(user=self.user, challenge=self.challenge)
        assert not uc.completed

        WaterLogFactory(user=self.user, logged_at=base + timedelta(days=4))
        uc.refresh_from_db()
        assert uc.completed


# ---------------------------------------------------------------------------
# Meal challenge — log_meals
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMealLogChallenge:
    def setup_method(self):
        self.user = UserFactory()
        self.challenge = _make_challenge("log_meals", 5, _week_start())

    def test_first_meal_of_day_increments_challenge(self):
        MealFactory(user=self.user, consumed_at=timezone.now())
        assert _current_value(self.user, self.challenge) == 1

    def test_multiple_meals_same_day_count_as_one(self):
        now = timezone.now()
        MealFactory(user=self.user, consumed_at=now)
        MealFactory(user=self.user, consumed_at=now + timedelta(hours=2))
        MealFactory(user=self.user, consumed_at=now + timedelta(hours=5))
        assert _current_value(self.user, self.challenge) == 1

    def test_meals_on_distinct_days_each_increment_challenge(self):
        base = timezone.now()
        for day_offset in range(5):
            MealFactory(user=self.user, consumed_at=base + timedelta(days=day_offset))
        uc = UserWeeklyChallenge.objects.get(user=self.user, challenge=self.challenge)
        assert uc.current_value == 5
        assert uc.completed
