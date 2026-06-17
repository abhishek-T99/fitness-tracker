"""Unit tests for levels.services — XP math, award_xp, challenges, athlete class."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from fitness_tracker import cache_keys
from levels.models import UserLevel, UserWeeklyChallenge, WeeklyChallenge, XPTransaction
from levels.services import (
    award_xp,
    calculate_level,
    detect_athlete_class,
    generate_weekly_challenges,
    get_streak_multiplier,
    get_tier,
    increment_challenge,
    xp_for_level,
)

User = get_user_model()


def make_user(username="tester", **kw):
    kw.setdefault("email", f"{username}@test.com")
    return User.objects.create_user(username=username, password="pw", **kw)


# ── xp_for_level ─────────────────────────────────────────────────────────────

class XpForLevelTests(TestCase):
    def test_level_1_is_zero(self):
        self.assertEqual(xp_for_level(1), 0)

    def test_level_0_and_negative_also_zero(self):
        self.assertEqual(xp_for_level(0), 0)
        self.assertEqual(xp_for_level(-5), 0)

    def test_level_2(self):
        # int(100 * (2-1)^1.6) = int(100 * 1) = 100
        self.assertEqual(xp_for_level(2), 100)

    def test_level_10(self):
        # int(100 * 9^1.6) ≈ int(100 * 36.058) = 3605
        expected = int(100 * (10 - 1) ** 1.6)
        self.assertEqual(xp_for_level(10), expected)

    def test_monotonically_increasing(self):
        for n in range(1, 50):
            self.assertLess(xp_for_level(n), xp_for_level(n + 1))

    def test_level_100_no_crash(self):
        result = xp_for_level(100)
        self.assertGreater(result, 0)


# ── calculate_level ───────────────────────────────────────────────────────────

class CalculateLevelTests(TestCase):
    def test_zero_xp_is_level_1(self):
        self.assertEqual(calculate_level(0), 1)

    def test_just_below_level_2_threshold(self):
        self.assertEqual(calculate_level(xp_for_level(2) - 1), 1)

    def test_exact_level_2_threshold(self):
        self.assertEqual(calculate_level(xp_for_level(2)), 2)

    def test_just_below_level_10_threshold(self):
        self.assertEqual(calculate_level(xp_for_level(10) - 1), 9)

    def test_exact_level_10_threshold(self):
        self.assertEqual(calculate_level(xp_for_level(10)), 10)

    def test_large_xp_no_crash(self):
        result = calculate_level(10_000_000)
        self.assertGreater(result, 100)

    def test_round_trip_consistency(self):
        for level in [1, 5, 10, 20, 35, 50, 75, 100]:
            self.assertEqual(calculate_level(xp_for_level(level)), level)


# ── get_tier ─────────────────────────────────────────────────────────────────

class GetTierTests(TestCase):
    def test_rookie_bounds(self):
        self.assertEqual(get_tier(1), "rookie")
        self.assertEqual(get_tier(9), "rookie")

    def test_amateur(self):
        self.assertEqual(get_tier(10), "amateur")
        self.assertEqual(get_tier(19), "amateur")

    def test_athlete(self):
        self.assertEqual(get_tier(20), "athlete")
        self.assertEqual(get_tier(34), "athlete")

    def test_warrior(self):
        self.assertEqual(get_tier(35), "warrior")
        self.assertEqual(get_tier(49), "warrior")

    def test_legend(self):
        self.assertEqual(get_tier(50), "legend")
        self.assertEqual(get_tier(74), "legend")

    def test_elite(self):
        self.assertEqual(get_tier(75), "elite")
        self.assertEqual(get_tier(99), "elite")

    def test_immortal(self):
        self.assertEqual(get_tier(100), "immortal")
        self.assertEqual(get_tier(200), "immortal")


# ── get_streak_multiplier ─────────────────────────────────────────────────────

class GetStreakMultiplierTests(TestCase):
    def setUp(self):
        self.user = make_user("streak_user")
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _set_streak(self, current):
        cache.set(cache_keys.streak(self.user.id), {"current": current, "longest": current})

    def test_no_cache_returns_1(self):
        self.assertEqual(get_streak_multiplier(self.user), 1.0)

    def test_streak_0(self):
        self._set_streak(0)
        self.assertEqual(get_streak_multiplier(self.user), 1.0)

    def test_streak_2_no_bonus(self):
        self._set_streak(2)
        self.assertEqual(get_streak_multiplier(self.user), 1.0)

    def test_streak_3_gives_1_1(self):
        self._set_streak(3)
        self.assertAlmostEqual(get_streak_multiplier(self.user), 1.1)

    def test_streak_7_gives_1_25(self):
        self._set_streak(7)
        self.assertAlmostEqual(get_streak_multiplier(self.user), 1.25)

    def test_streak_14_gives_1_5(self):
        self._set_streak(14)
        self.assertAlmostEqual(get_streak_multiplier(self.user), 1.5)

    def test_streak_30_gives_2(self):
        self._set_streak(30)
        self.assertAlmostEqual(get_streak_multiplier(self.user), 2.0)

    def test_streak_100_still_2(self):
        self._set_streak(100)
        self.assertAlmostEqual(get_streak_multiplier(self.user), 2.0)


# ── award_xp ─────────────────────────────────────────────────────────────────

class AwardXpTests(TestCase):
    def setUp(self):
        self.user = make_user("xp_user")
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_creates_userlevel_if_absent(self):
        self.assertFalse(UserLevel.objects.filter(user=self.user).exists())
        award_xp(self.user, 50, "test", "workout")
        self.assertTrue(UserLevel.objects.filter(user=self.user).exists())

    def test_creates_xptransaction(self):
        award_xp(self.user, 50, "reason", "nutrition", source_id=7)
        tx = XPTransaction.objects.get(user=self.user)
        self.assertEqual(tx.base_amount, 50)
        self.assertEqual(tx.amount, 50)
        self.assertEqual(tx.multiplier, Decimal("1.0"))
        self.assertEqual(tx.reason, "reason")
        self.assertEqual(tx.source_type, "nutrition")
        self.assertEqual(tx.source_id, 7)

    def test_total_xp_accumulates(self):
        award_xp(self.user, 100, "a", "workout")
        award_xp(self.user, 50, "b", "nutrition")
        ul = UserLevel.objects.get(user=self.user)
        self.assertEqual(ul.total_xp, 150)

    def test_returns_xp_awarded_and_leveled_up(self):
        xp_awarded, leveled_up = award_xp(self.user, 50, "test", "workout")
        self.assertEqual(xp_awarded, 50)
        self.assertFalse(leveled_up)

    def test_leveled_up_true_on_threshold_crossing(self):
        # Get to just below level 2 threshold
        threshold = xp_for_level(2)  # 100 XP
        award_xp(self.user, threshold - 1, "setup", "workout")
        ul = UserLevel.objects.get(user=self.user)
        self.assertEqual(ul.level, 1)

        _, leveled_up = award_xp(self.user, 1, "push", "workout")
        ul.refresh_from_db()
        self.assertTrue(leveled_up)
        self.assertEqual(ul.level, 2)
        self.assertEqual(ul.tier, "rookie")

    def test_multiplier_applied_from_streak_cache(self):
        cache.set(
            cache_keys.streak(self.user.id),
            {"current": 7, "longest": 7},
        )
        xp_awarded, _ = award_xp(self.user, 100, "with mult", "workout")
        # 7-day streak → 1.25× → int(100 * 1.25) = 125
        self.assertEqual(xp_awarded, 125)
        tx = XPTransaction.objects.get(user=self.user)
        self.assertEqual(tx.multiplier, Decimal("1.25"))
        self.assertEqual(tx.base_amount, 100)
        self.assertEqual(tx.amount, 125)

    def test_minimum_1_xp_awarded(self):
        xp_awarded, _ = award_xp(self.user, 0, "zero", "workout")
        self.assertEqual(xp_awarded, 1)

    def test_tier_updates_on_level_up(self):
        # Award enough XP to reach level 10 (amateur tier)
        target_xp = xp_for_level(10)
        award_xp(self.user, target_xp, "big award", "workout")
        ul = UserLevel.objects.get(user=self.user)
        self.assertEqual(ul.level, 10)
        self.assertEqual(ul.tier, "amateur")

    def test_concurrent_isolation(self):
        # Two calls should not create duplicate profiles
        award_xp(self.user, 10, "a", "workout")
        award_xp(self.user, 10, "b", "workout")
        self.assertEqual(UserLevel.objects.filter(user=self.user).count(), 1)
        ul = UserLevel.objects.get(user=self.user)
        self.assertEqual(ul.total_xp, 20)


# ── increment_challenge ───────────────────────────────────────────────────────

class IncrementChallengeTests(TestCase):
    def setUp(self):
        self.user = make_user("challenge_user")
        today = timezone.localdate()
        self.week_start = today - timedelta(days=today.weekday())

    def test_no_challenge_no_error(self):
        # Should silently no-op if there's no matching challenge this week
        increment_challenge(self.user, "complete_workouts")
        self.assertEqual(XPTransaction.objects.filter(user=self.user).count(), 0)

    def test_increments_progress(self):
        ch = WeeklyChallenge.objects.create(
            week_start=self.week_start,
            challenge_type="complete_workouts",
            target_value=5,
            xp_reward=300,
            description="Complete 5 workouts",
        )
        increment_challenge(self.user, "complete_workouts")
        uc = UserWeeklyChallenge.objects.get(user=self.user, challenge=ch)
        self.assertEqual(uc.current_value, 1)
        self.assertFalse(uc.completed)

    def test_marks_complete_and_awards_xp_at_target(self):
        ch = WeeklyChallenge.objects.create(
            week_start=self.week_start,
            challenge_type="log_meals",
            target_value=3,
            xp_reward=200,
            description="Log meals 3 days",
        )
        for _ in range(3):
            increment_challenge(self.user, "log_meals")

        uc = UserWeeklyChallenge.objects.get(user=self.user, challenge=ch)
        self.assertTrue(uc.completed)
        self.assertIsNotNone(uc.completed_at)
        self.assertTrue(
            XPTransaction.objects.filter(user=self.user, source_type="challenge").exists()
        )

    def test_no_double_award_after_completed(self):
        ch = WeeklyChallenge.objects.create(
            week_start=self.week_start,
            challenge_type="record_pr",
            target_value=1,
            xp_reward=200,
            description="Set 1 PR",
        )
        increment_challenge(self.user, "record_pr")
        increment_challenge(self.user, "record_pr")  # should be a no-op
        self.assertEqual(
            XPTransaction.objects.filter(user=self.user, source_type="challenge").count(), 1
        )

    def test_custom_increment(self):
        ch = WeeklyChallenge.objects.create(
            week_start=self.week_start,
            challenge_type="log_water",
            target_value=7,
            xp_reward=150,
            description="Log water 7 days",
        )
        increment_challenge(self.user, "log_water", increment=3)
        uc = UserWeeklyChallenge.objects.get(user=self.user, challenge=ch)
        self.assertEqual(uc.current_value, 3)

    def test_only_current_week_challenges_matched(self):
        last_week = self.week_start - timedelta(days=7)
        WeeklyChallenge.objects.create(
            week_start=last_week,
            challenge_type="complete_workouts",
            target_value=3,
            xp_reward=200,
            description="Old challenge",
        )
        increment_challenge(self.user, "complete_workouts")
        self.assertEqual(UserWeeklyChallenge.objects.filter(user=self.user).count(), 0)


# ── generate_weekly_challenges ────────────────────────────────────────────────

class GenerateWeeklyChallengesTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        self.week_start = today - timedelta(days=today.weekday())

    def test_creates_up_to_3_challenges(self):
        result = generate_weekly_challenges(self.week_start)
        self.assertLessEqual(len(result), 3)
        self.assertGreater(len(result), 0)

    def test_idempotent_no_duplicate_types(self):
        # Call twice; the second call fills remaining template slots but
        # must never create two challenges of the same type for the same week.
        generate_weekly_challenges(self.week_start)
        generate_weekly_challenges(self.week_start)
        types = list(
            WeeklyChallenge.objects
            .filter(week_start=self.week_start)
            .values_list("challenge_type", flat=True)
        )
        self.assertEqual(len(types), len(set(types)), "Duplicate challenge types created")

    def test_no_new_challenges_when_all_types_exist(self):
        # Manually create all 5 types first
        from levels.services import CHALLENGE_TEMPLATES
        for tmpl in CHALLENGE_TEMPLATES:
            WeeklyChallenge.objects.create(
                week_start=self.week_start,
                challenge_type=tmpl["type"],
                target_value=1,
                xp_reward=100,
                description="pre-existing",
            )
        result = generate_weekly_challenges(self.week_start)
        self.assertEqual(len(result), 0)

    def test_all_challenges_have_description_and_reward(self):
        challenges = generate_weekly_challenges(self.week_start)
        for ch in challenges:
            self.assertGreater(len(ch.description), 0)
            self.assertGreater(ch.xp_reward, 0)
            self.assertGreater(ch.target_value, 0)

    def test_challenge_types_are_distinct(self):
        challenges = generate_weekly_challenges(self.week_start)
        types = [ch.challenge_type for ch in challenges]
        self.assertEqual(len(types), len(set(types)))


# ── detect_athlete_class ──────────────────────────────────────────────────────

class DetectAthleteClassTests(TestCase):
    def test_few_workouts_returns_rookie(self):
        user = make_user("athlete_rookie")
        result = detect_athlete_class(user)
        self.assertEqual(result, "rookie")

    def test_requires_at_least_3_workouts(self):
        from workouts.models import Workout

        user = make_user("athlete_lt3")
        Workout.objects.create(
            user=user, name="W1",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=1),
        )
        Workout.objects.create(
            user=user, name="W2",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=2),
        )
        result = detect_athlete_class(user)
        self.assertEqual(result, "rookie")
