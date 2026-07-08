"""
Tests for the three progress-analytics endpoints:
  GET /api/v1/workouts/strength-history/
  GET /api/v1/workouts/volume-by-muscle/
  GET /api/v1/workouts/activity-heatmap/
And for the measurements body-composition endpoint:
  GET /api/v1/measurements/body-composition/
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from exercises.models import Exercise
from measurements.models import BodyMeasurement
from workouts.models import ExerciseSet, Routine, Workout, WorkoutExercise

User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(username="testuser"):
    return User.objects.create_user(username=username, password="pw", email=f"{username}@example.com")


def _make_exercise(name="Bench Press", primary_muscle="chest"):
    return Exercise.objects.get_or_create(
        name=name,
        defaults={
            "slug": name.lower().replace(" ", "-"),
            "primary_muscle": primary_muscle,
            "category": "strength",
            "equipment": "barbell",
        },
    )[0]


def _make_workout(user, started_at=None, status=Workout.Status.COMPLETED, duration_min=60):
    if started_at is None:
        started_at = timezone.now()
    return Workout.objects.create(
        user=user,
        name="Test",
        status=status,
        started_at=started_at,
        duration_min=duration_min,
    )


def _add_sets(workout, exercise, sets_data, warmup_index=None):
    """sets_data: list of (reps, weight)."""
    we = WorkoutExercise.objects.create(workout=workout, exercise=exercise, order=0)
    objs = []
    for i, (reps, weight) in enumerate(sets_data, start=1):
        objs.append(ExerciseSet(
            workout_exercise=we,
            set_number=i,
            reps=reps,
            weight=Decimal(str(weight)) if weight else None,
            is_warmup=(i - 1 == warmup_index),
            completed=True,
        ))
    ExerciseSet.objects.bulk_create(objs)
    return we


# ---------------------------------------------------------------------------
# Strength history
# ---------------------------------------------------------------------------

class StrengthHistoryTests(TestCase):
    URL = "/api/v1/workouts/strength-history/"

    def setUp(self):
        self.user = _make_user()
        self.other = _make_user("other")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = _make_exercise("Bench Press", "chest")

    def test_requires_exercise_id(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 400)

    def test_empty_when_no_workouts(self):
        resp = self.client.get(self.URL, {"exercise_id": self.exercise.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_single_session_epley_formula(self):
        w = _make_workout(self.user)
        _add_sets(w, self.exercise, [(5, 100)])  # 1RM = 100 * (1 + 5/30) ≈ 116.7

        resp = self.client.get(self.URL, {"exercise_id": self.exercise.id})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertAlmostEqual(data[0]["estimated_1rm"], 116.7, places=0)
        self.assertEqual(data[0]["max_weight"], 100.0)
        self.assertEqual(data[0]["max_reps"], 5)
        self.assertEqual(data[0]["total_volume"], 500.0)

    def test_picks_best_set_per_day(self):
        """Two sets on the same day — should return max 1RM, not duplicate entries."""
        w = _make_workout(self.user)
        _add_sets(w, self.exercise, [(5, 100), (3, 110)])  # 110*(1+3/30) ≈ 121

        resp = self.client.get(self.URL, {"exercise_id": self.exercise.id})
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertGreater(data[0]["estimated_1rm"], 116.7)

    def test_multiple_dates_ordered(self):
        now = timezone.now()
        w1 = _make_workout(self.user, started_at=now - timedelta(days=10))
        w2 = _make_workout(self.user, started_at=now - timedelta(days=5))
        _add_sets(w1, self.exercise, [(5, 80)])
        _add_sets(w2, self.exercise, [(5, 90)])

        resp = self.client.get(self.URL, {"exercise_id": self.exercise.id})
        data = resp.json()
        self.assertEqual(len(data), 2)
        self.assertLess(data[0]["date"], data[1]["date"])
        self.assertLess(data[0]["estimated_1rm"], data[1]["estimated_1rm"])

    def test_warmup_sets_excluded(self):
        w = _make_workout(self.user)
        we = WorkoutExercise.objects.create(workout=w, exercise=self.exercise, order=0)
        ExerciseSet.objects.create(workout_exercise=we, set_number=1, reps=10, weight=60,
                                   is_warmup=True, completed=True)
        ExerciseSet.objects.create(workout_exercise=we, set_number=2, reps=5, weight=100,
                                   is_warmup=False, completed=True)

        resp = self.client.get(self.URL, {"exercise_id": self.exercise.id})
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["max_weight"], 100.0)

    def test_excludes_other_users_data(self):
        w = _make_workout(self.other)
        _add_sets(w, self.exercise, [(5, 200)])

        resp = self.client.get(self.URL, {"exercise_id": self.exercise.id})
        self.assertEqual(resp.json(), [])

    def test_respects_days_window(self):
        now = timezone.now()
        w_old = _make_workout(self.user, started_at=now - timedelta(days=100))
        w_recent = _make_workout(self.user, started_at=now - timedelta(days=5))
        _add_sets(w_old, self.exercise, [(5, 100)])
        _add_sets(w_recent, self.exercise, [(5, 110)])

        resp = self.client.get(self.URL, {"exercise_id": self.exercise.id, "days": 30})
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["max_weight"], 110.0)

    def test_draft_workouts_excluded(self):
        w = _make_workout(self.user, status=Workout.Status.DRAFT)
        _add_sets(w, self.exercise, [(5, 100)])
        resp = self.client.get(self.URL, {"exercise_id": self.exercise.id})
        self.assertEqual(resp.json(), [])

    def test_unauthenticated_rejected(self):
        anon = APIClient()
        resp = anon.get(self.URL, {"exercise_id": self.exercise.id})
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Volume by muscle
# ---------------------------------------------------------------------------

class VolumeByMuscleTests(TestCase):
    URL = "/api/v1/workouts/volume-by-muscle/"

    def setUp(self):
        self.user = _make_user("vol_user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.chest = _make_exercise("Bench Press", "chest")
        self.back  = _make_exercise("Bent-Over Row", "back")

    def test_empty_response_no_workouts(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_volume_calculation(self):
        """3 sets × (5 reps × 100 kg) = 1500 kg volume for chest."""
        w = _make_workout(self.user)
        _add_sets(w, self.chest, [(5, 100), (5, 100), (5, 100)])

        resp = self.client.get(self.URL)
        data = resp.json()
        chest_entry = next(d for d in data if d["muscle_group"] == "chest")
        self.assertAlmostEqual(chest_entry["volume_kg"], 1500.0, places=1)

    def test_multiple_muscle_groups(self):
        w = _make_workout(self.user)
        _add_sets(w, self.chest, [(5, 100)])
        _add_sets(w, self.back,  [(8, 80)])

        resp = self.client.get(self.URL)
        data = resp.json()
        muscles = {d["muscle_group"] for d in data}
        self.assertIn("chest", muscles)
        self.assertIn("back", muscles)

    def test_warmup_and_zero_weight_excluded(self):
        w = _make_workout(self.user)
        we = WorkoutExercise.objects.create(workout=w, exercise=self.chest, order=0)
        # warmup
        ExerciseSet.objects.create(workout_exercise=we, set_number=1, reps=10, weight=40,
                                   is_warmup=True, completed=True)
        # bodyweight (no weight)
        ExerciseSet.objects.create(workout_exercise=we, set_number=2, reps=10, weight=None,
                                   is_warmup=False, completed=True)
        # working set
        ExerciseSet.objects.create(workout_exercise=we, set_number=3, reps=5, weight=100,
                                   is_warmup=False, completed=True)

        resp = self.client.get(self.URL)
        data = resp.json()
        chest_entry = next((d for d in data if d["muscle_group"] == "chest"), None)
        self.assertIsNotNone(chest_entry)
        self.assertAlmostEqual(chest_entry["volume_kg"], 500.0, places=1)

    def test_weeks_param_limits_window(self):
        now = timezone.now()
        w_old = _make_workout(self.user, started_at=now - timedelta(weeks=15))
        w_recent = _make_workout(self.user, started_at=now - timedelta(weeks=2))
        _add_sets(w_old, self.chest, [(5, 100)])
        _add_sets(w_recent, self.chest, [(5, 80)])

        resp = self.client.get(self.URL, {"weeks": 4})
        data = resp.json()
        # Only the recent workout should appear
        self.assertEqual(len(data), 1)
        chest_entry = data[0]
        self.assertAlmostEqual(chest_entry["volume_kg"], 400.0, places=1)

    def test_excludes_other_users(self):
        other = _make_user("other_vol")
        w = _make_workout(other)
        _add_sets(w, self.chest, [(5, 200)])
        resp = self.client.get(self.URL)
        self.assertEqual(resp.json(), [])


# ---------------------------------------------------------------------------
# Activity heatmap
# ---------------------------------------------------------------------------

class ActivityHeatmapTests(TestCase):
    URL = "/api/v1/workouts/activity-heatmap/"

    def setUp(self):
        self.user = _make_user("heat_user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = _make_exercise("Squat", "quads")

    def test_empty_no_workouts(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_single_workout_entry(self):
        now = timezone.now()
        w = _make_workout(self.user, started_at=now, duration_min=45)
        _add_sets(w, self.exercise, [(5, 100)])

        resp = self.client.get(self.URL)
        data = resp.json()
        self.assertEqual(len(data), 1)
        entry = data[0]
        self.assertEqual(entry["workout_count"], 1)
        self.assertEqual(entry["total_duration_min"], 45)
        self.assertAlmostEqual(entry["total_volume_kg"], 500.0, places=1)

    def test_multiple_workouts_same_day_aggregated(self):
        # Zero out sub-hour parts so the UTC times map to the same calendar
        # date in any UTC+ timezone (Nepal is UTC+5:45; 16:00 UTC = 21:45 NST,
        # still the same day).
        today = timezone.now().replace(hour=7, minute=0, second=0, microsecond=0)
        _make_workout(self.user, started_at=today, duration_min=30)
        _make_workout(self.user, started_at=today.replace(hour=16), duration_min=45)

        resp = self.client.get(self.URL)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["workout_count"], 2)
        self.assertEqual(data[0]["total_duration_min"], 75)

    def test_days_param_filters_old_workouts(self):
        now = timezone.now()
        _make_workout(self.user, started_at=now - timedelta(days=400))
        _make_workout(self.user, started_at=now - timedelta(days=10))

        resp = self.client.get(self.URL, {"days": 30})
        data = resp.json()
        self.assertEqual(len(data), 1)

    def test_draft_workouts_excluded(self):
        _make_workout(self.user, status=Workout.Status.DRAFT)
        resp = self.client.get(self.URL)
        self.assertEqual(resp.json(), [])

    def test_excludes_other_users(self):
        other = _make_user("other_heat")
        _make_workout(other)
        resp = self.client.get(self.URL)
        self.assertEqual(resp.json(), [])

    def test_no_volume_workout_has_zero_volume(self):
        """Cardio workouts with no weighted sets still appear with volume=0."""
        _make_workout(self.user, duration_min=60)
        resp = self.client.get(self.URL)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["total_volume_kg"], 0.0)


# ---------------------------------------------------------------------------
# Body composition
# ---------------------------------------------------------------------------

class BodyCompositionTests(TestCase):
    URL = "/api/v1/measurements/body-composition/"

    def setUp(self):
        self.user = _make_user("body_user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _make_measurement(self, days_ago, weight_kg=None, body_fat_percent=None):
        return BodyMeasurement.objects.create(
            user=self.user,
            recorded_at=date.today() - timedelta(days=days_ago),
            weight_kg=weight_kg,
            body_fat_percent=body_fat_percent,
        )

    def test_empty_no_measurements(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_returns_weight_and_body_fat(self):
        self._make_measurement(5, weight_kg=75.0, body_fat_percent=18.0)
        resp = self.client.get(self.URL)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertAlmostEqual(data[0]["weight_kg"], 75.0)
        self.assertAlmostEqual(data[0]["body_fat_percent"], 18.0)

    def test_entry_with_only_weight_included(self):
        self._make_measurement(3, weight_kg=74.0)
        resp = self.client.get(self.URL)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertIsNone(data[0]["body_fat_percent"])

    def test_entry_with_only_body_fat_included(self):
        self._make_measurement(3, body_fat_percent=20.0)
        resp = self.client.get(self.URL)
        self.assertEqual(len(resp.json()), 1)

    def test_entry_with_neither_excluded(self):
        """Measurement with no weight or body_fat should not appear."""
        BodyMeasurement.objects.create(
            user=self.user,
            recorded_at=date.today() - timedelta(days=1),
        )
        resp = self.client.get(self.URL)
        self.assertEqual(resp.json(), [])

    def test_ordered_chronologically(self):
        self._make_measurement(10, weight_kg=80.0)
        self._make_measurement(3, weight_kg=78.0)
        self._make_measurement(1, weight_kg=77.0)
        data = self.client.get(self.URL).json()
        dates = [d["recorded_at"] for d in data]
        self.assertEqual(dates, sorted(dates))

    def test_days_param_limits_window(self):
        self._make_measurement(100, weight_kg=82.0)
        self._make_measurement(5, weight_kg=78.0)
        resp = self.client.get(self.URL, {"days": 30})
        self.assertEqual(len(resp.json()), 1)

    def test_excludes_other_users(self):
        other = _make_user("other_body")
        BodyMeasurement.objects.create(
            user=other,
            recorded_at=date.today(),
            weight_kg=90.0,
        )
        resp = self.client.get(self.URL)
        self.assertEqual(resp.json(), [])

    def test_unauthenticated_rejected(self):
        anon = APIClient()
        self.assertEqual(anon.get(self.URL).status_code, 401)


# ---------------------------------------------------------------------------
# Personal records
# ---------------------------------------------------------------------------

class PersonalRecordsTests(TestCase):
    URL = "/api/v1/workouts/personal-records/"

    def setUp(self):
        self.user = _make_user("pr_user")
        self.other = _make_user("pr_other")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = _make_exercise("Bench Press", "chest")
        self.squat = _make_exercise("Squat", "quads")

    def test_empty_no_workouts(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)

    def test_single_set_pr_values(self):
        w = _make_workout(self.user)
        _add_sets(w, self.exercise, [(5, 100)])  # 1RM = 100*(1+5/30) ≈ 116.7

        data = self.client.get(self.URL).json()
        self.assertEqual(len(data), 1)
        entry = data[0]
        self.assertEqual(entry["exercise_id"], self.exercise.id)
        self.assertEqual(entry["exercise_name"], "Bench Press")
        self.assertEqual(entry["primary_muscle"], "chest")
        self.assertAlmostEqual(entry["pr_1rm"], 116.7, places=0)
        self.assertEqual(entry["pr_weight"], 100.0)
        self.assertEqual(entry["pr_reps"], 5)

    def test_multiple_sets_picks_best_per_metric(self):
        w = _make_workout(self.user)
        # Set 1: heavy weight, low reps → high 1RM
        # Set 2: lighter weight, high reps → high rep PR
        _add_sets(w, self.exercise, [(3, 120), (12, 80)])

        data = self.client.get(self.URL).json()
        entry = data[0]
        # 1RM: 120*(1+3/30)=132.0 vs 80*(1+12/30)=112.0 → 132.0 wins
        self.assertAlmostEqual(entry["pr_1rm"], 132.0, places=0)
        self.assertEqual(entry["pr_weight"], 120.0)
        self.assertEqual(entry["pr_reps"], 12)

    def test_pr_improves_over_sessions(self):
        now = timezone.now()
        w1 = _make_workout(self.user, started_at=now - timedelta(days=10))
        w2 = _make_workout(self.user, started_at=now - timedelta(days=2))
        _add_sets(w1, self.exercise, [(5, 100)])  # 1RM ≈ 116.7
        _add_sets(w2, self.exercise, [(5, 110)])  # 1RM ≈ 128.3 — breaks PR

        data = self.client.get(self.URL).json()
        entry = data[0]
        self.assertAlmostEqual(entry["pr_1rm"], 128.3, places=0)
        self.assertEqual(entry["pr_weight"], 110.0)

    def test_has_recent_pr_true_within_30_days(self):
        w = _make_workout(self.user, started_at=timezone.now() - timedelta(days=5))
        _add_sets(w, self.exercise, [(5, 100)])
        data = self.client.get(self.URL).json()
        self.assertTrue(data[0]["has_recent_pr"])

    def test_has_recent_pr_false_older_than_30_days(self):
        w = _make_workout(self.user, started_at=timezone.now() - timedelta(days=45))
        _add_sets(w, self.exercise, [(5, 100)])
        data = self.client.get(self.URL).json()
        self.assertFalse(data[0]["has_recent_pr"])

    def test_warmup_sets_excluded(self):
        w = _make_workout(self.user)
        we = WorkoutExercise.objects.create(workout=w, exercise=self.exercise, order=0)
        ExerciseSet.objects.create(workout_exercise=we, set_number=1, reps=15, weight=200,
                                   is_warmup=True, completed=True)
        ExerciseSet.objects.create(workout_exercise=we, set_number=2, reps=5, weight=100,
                                   is_warmup=False, completed=True)
        data = self.client.get(self.URL).json()
        self.assertEqual(data[0]["pr_weight"], 100.0)

    def test_draft_workouts_excluded(self):
        w = _make_workout(self.user, status=Workout.Status.DRAFT)
        _add_sets(w, self.exercise, [(5, 100)])
        self.assertEqual(self.client.get(self.URL).json(), [])

    def test_excludes_other_users_data(self):
        w = _make_workout(self.other)
        _add_sets(w, self.exercise, [(5, 200)])
        self.assertEqual(self.client.get(self.URL).json(), [])

    def test_sorted_by_1rm_descending(self):
        w = _make_workout(self.user)
        _add_sets(w, self.exercise, [(5, 50)])   # 1RM ≈ 58.3 (bench)
        _add_sets(w, self.squat, [(5, 150)])    # 1RM ≈ 175.0 (squat)

        data = self.client.get(self.URL).json()
        self.assertEqual(len(data), 2)
        self.assertGreater(data[0]["pr_1rm"], data[1]["pr_1rm"])
        self.assertEqual(data[0]["exercise_name"], "Squat")

    def test_multiple_exercises_returned(self):
        w = _make_workout(self.user)
        _add_sets(w, self.exercise, [(5, 100)])
        _add_sets(w, self.squat, [(5, 120)])
        data = self.client.get(self.URL).json()
        self.assertEqual(len(data), 2)


# ---------------------------------------------------------------------------
# Overload streaks
# ---------------------------------------------------------------------------

class OverloadStreaksTests(TestCase):
    URL = "/api/v1/workouts/overload-streaks/"

    def setUp(self):
        self.user = _make_user("streak_user")
        self.other = _make_user("streak_other")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = _make_exercise("Deadlift", "back")

    def test_empty_no_workouts(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)

    def test_single_session_no_streak(self):
        w = _make_workout(self.user)
        _add_sets(w, self.exercise, [(5, 100)])
        data = self.client.get(self.URL).json()
        # Need ≥2 sessions to form a streak
        self.assertEqual(data, [])

    def test_two_sessions_improving_streak_of_1(self):
        now = timezone.now()
        w1 = _make_workout(self.user, started_at=now - timedelta(days=7))
        w2 = _make_workout(self.user, started_at=now - timedelta(days=1))
        _add_sets(w1, self.exercise, [(5, 100)])
        _add_sets(w2, self.exercise, [(5, 110)])  # improved

        data = self.client.get(self.URL).json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["current_streak"], 1)
        self.assertEqual(data[0]["exercise_name"], "Deadlift")

    def test_three_consecutive_improving_sessions(self):
        now = timezone.now()
        for i, weight in enumerate([100, 105, 110], start=1):
            w = _make_workout(self.user, started_at=now - timedelta(days=10 - i * 3))
            _add_sets(w, self.exercise, [(5, weight)])

        data = self.client.get(self.URL).json()
        self.assertEqual(data[0]["current_streak"], 2)

    def test_regression_breaks_streak(self):
        now = timezone.now()
        # Sessions: 100 → 110 → 105 (regression) → 115
        for days_ago, weight in [(12, 100), (8, 110), (4, 105), (1, 115)]:
            w = _make_workout(self.user, started_at=now - timedelta(days=days_ago))
            _add_sets(w, self.exercise, [(5, weight)])

        data = self.client.get(self.URL).json()
        # Most recent pair: 115 > 105 → streak=1; pair before: 105 < 110 → break
        self.assertEqual(data[0]["current_streak"], 1)

    def test_no_streak_when_regressed_last_session(self):
        now = timezone.now()
        w1 = _make_workout(self.user, started_at=now - timedelta(days=7))
        w2 = _make_workout(self.user, started_at=now - timedelta(days=1))
        _add_sets(w1, self.exercise, [(5, 110)])
        _add_sets(w2, self.exercise, [(5, 100)])  # regressed

        data = self.client.get(self.URL).json()
        self.assertEqual(data, [])

    def test_sorted_by_streak_length_descending(self):
        squat = _make_exercise("Squat", "quads")
        now = timezone.now()
        # Bench: 3-session streak (2 improvements)
        for days_ago, weight in [(9, 100), (6, 105), (3, 110)]:
            w = _make_workout(self.user, started_at=now - timedelta(days=days_ago))
            _add_sets(w, self.exercise, [(5, weight)])
        # Squat: 2-session streak (1 improvement)
        w1 = _make_workout(self.user, started_at=now - timedelta(days=8))
        w2 = _make_workout(self.user, started_at=now - timedelta(days=2))
        _add_sets(w1, squat, [(5, 120)])
        _add_sets(w2, squat, [(5, 130)])

        data = self.client.get(self.URL).json()
        self.assertGreaterEqual(data[0]["current_streak"], data[1]["current_streak"])

    def test_draft_workouts_excluded(self):
        w = _make_workout(self.user, status=Workout.Status.DRAFT)
        _add_sets(w, self.exercise, [(5, 100)])
        self.assertEqual(self.client.get(self.URL).json(), [])

    def test_excludes_other_users_data(self):
        now = timezone.now()
        for days_ago, weight in [(7, 100), (1, 110)]:
            w = _make_workout(self.other, started_at=now - timedelta(days=days_ago))
            _add_sets(w, self.exercise, [(5, weight)])
        self.assertEqual(self.client.get(self.URL).json(), [])


# ---------------------------------------------------------------------------
# RPE trend
# ---------------------------------------------------------------------------

class RpeTrendTests(TestCase):
    URL = "/api/v1/workouts/rpe-trend/"

    def setUp(self):
        self.user = _make_user("rpe_user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _make_rpe_workout(self, days_ago, rpe):
        return Workout.objects.create(
            user=self.user,
            name="RPE workout",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=days_ago),
            duration_min=60,
            perceived_exertion=rpe,
        )

    def test_empty_no_workouts(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)

    def test_invalid_days_param(self):
        resp = self.client.get(self.URL, {"days": "abc"})
        self.assertEqual(resp.status_code, 400)

    def test_single_week_avg_rpe(self):
        self._make_rpe_workout(3, 7)
        self._make_rpe_workout(5, 9)

        data = self.client.get(self.URL).json()
        self.assertEqual(len(data), 1)
        self.assertAlmostEqual(data[0]["avg_rpe"], 8.0, places=1)
        self.assertEqual(data[0]["workout_count"], 2)
        self.assertIn("week_start", data[0])

    def test_workouts_without_rpe_excluded(self):
        # Workout without RPE
        Workout.objects.create(
            user=self.user, name="no rpe",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=3),
            duration_min=60,
        )
        self._make_rpe_workout(2, 8)

        data = self.client.get(self.URL).json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["workout_count"], 1)

    def test_days_param_limits_window(self):
        self._make_rpe_workout(100, 8)
        self._make_rpe_workout(5, 7)
        data = self.client.get(self.URL, {"days": 30}).json()
        self.assertEqual(len(data), 1)
        self.assertAlmostEqual(data[0]["avg_rpe"], 7.0, places=1)

    def test_excludes_other_users(self):
        other = _make_user("rpe_other")
        Workout.objects.create(
            user=other, name="other",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=3),
            duration_min=60, perceived_exertion=9,
        )
        self.assertEqual(self.client.get(self.URL).json(), [])

    def test_draft_workouts_excluded(self):
        Workout.objects.create(
            user=self.user, name="draft",
            status=Workout.Status.DRAFT,
            started_at=timezone.now() - timedelta(days=3),
            duration_min=60, perceived_exertion=8,
        )
        self.assertEqual(self.client.get(self.URL).json(), [])


# ---------------------------------------------------------------------------
# Duration trend
# ---------------------------------------------------------------------------

class DurationTrendTests(TestCase):
    URL = "/api/v1/workouts/duration-trend/"

    def setUp(self):
        self.user = _make_user("dur_user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_empty_no_workouts(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)

    def test_invalid_weeks_param(self):
        resp = self.client.get(self.URL, {"weeks": "bad"})
        self.assertEqual(resp.status_code, 400)

    def test_single_week_avg_duration(self):
        for dur in [60, 90]:
            Workout.objects.create(
                user=self.user, name="dur",
                status=Workout.Status.COMPLETED,
                started_at=timezone.now() - timedelta(days=3),
                duration_min=dur,
            )
        data = self.client.get(self.URL).json()
        self.assertEqual(len(data), 1)
        self.assertAlmostEqual(data[0]["avg_duration_min"], 75.0, places=1)
        self.assertEqual(data[0]["total_duration_min"], 150)
        self.assertEqual(data[0]["workout_count"], 2)

    def test_workouts_without_duration_excluded(self):
        Workout.objects.create(
            user=self.user, name="no dur",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=3),
        )
        Workout.objects.create(
            user=self.user, name="with dur",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=3),
            duration_min=60,
        )
        data = self.client.get(self.URL).json()
        self.assertEqual(data[0]["workout_count"], 1)

    def test_weeks_param_limits_window(self):
        Workout.objects.create(
            user=self.user, name="old",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(weeks=20),
            duration_min=90,
        )
        Workout.objects.create(
            user=self.user, name="recent",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(weeks=2),
            duration_min=60,
        )
        data = self.client.get(self.URL, {"weeks": 4}).json()
        self.assertEqual(len(data), 1)
        self.assertAlmostEqual(data[0]["avg_duration_min"], 60.0, places=1)

    def test_excludes_other_users(self):
        other = _make_user("dur_other")
        Workout.objects.create(
            user=other, name="x",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=3),
            duration_min=60,
        )
        self.assertEqual(self.client.get(self.URL).json(), [])


# ---------------------------------------------------------------------------
# Session density
# ---------------------------------------------------------------------------

class SessionDensityTests(TestCase):
    URL = "/api/v1/workouts/session-density/"

    def setUp(self):
        self.user = _make_user("density_user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = _make_exercise("Press", "chest")

    def test_empty_no_workouts(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)

    def test_invalid_weeks_param(self):
        resp = self.client.get(self.URL, {"weeks": "x"})
        self.assertEqual(resp.status_code, 400)

    def test_density_calculation(self):
        # volume = 5 * 100 = 500 kg, duration = 50 min → density = 10.0 kg/min
        w = _make_workout(self.user, duration_min=50)
        _add_sets(w, self.exercise, [(5, 100)])

        data = self.client.get(self.URL).json()
        self.assertEqual(len(data), 1)
        self.assertAlmostEqual(data[0]["density_kg_per_min"], 10.0, places=1)
        self.assertEqual(data[0]["total_volume_kg"], 500.0)
        self.assertEqual(data[0]["total_duration_min"], 50)

    def test_cardio_only_workout_zero_density(self):
        # Workout with duration but no weighted sets → density = 0
        Workout.objects.create(
            user=self.user, name="cardio",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=3),
            duration_min=45,
        )
        data = self.client.get(self.URL).json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["density_kg_per_min"], 0.0)

    def test_workout_without_duration_excluded(self):
        w = _make_workout(self.user, duration_min=None)
        _add_sets(w, self.exercise, [(5, 100)])
        self.assertEqual(self.client.get(self.URL).json(), [])

    def test_excludes_other_users(self):
        other = _make_user("density_other")
        w = _make_workout(other, duration_min=60)
        _add_sets(w, self.exercise, [(5, 100)])
        self.assertEqual(self.client.get(self.URL).json(), [])


# ---------------------------------------------------------------------------
# Cardio summary
# ---------------------------------------------------------------------------

class CardioSummaryTests(TestCase):
    URL = "/api/v1/workouts/cardio-summary/"

    def setUp(self):
        self.user = _make_user("cardio_user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _make_cardio(self, days_ago, distance_km=None, avg_hr=None):
        from decimal import Decimal
        return Workout.objects.create(
            user=self.user,
            name="run",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=days_ago),
            duration_min=45,
            distance_km=Decimal(str(distance_km)) if distance_km else None,
            avg_hr_bpm=avg_hr,
        )

    def test_empty_no_cardio_workouts(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_distance_km"], 0.0)
        self.assertEqual(data["total_sessions"], 0)
        self.assertIsNone(data["avg_hr_bpm"])
        self.assertEqual(data["weekly_distance"], [])
        self.assertEqual(data["hr_trend"], [])

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)

    def test_invalid_days_param(self):
        self.assertEqual(self.client.get(self.URL, {"days": "bad"}).status_code, 400)

    def test_total_distance_aggregation(self):
        self._make_cardio(3, distance_km=5.0)
        self._make_cardio(6, distance_km=8.5)

        data = self.client.get(self.URL).json()
        self.assertAlmostEqual(data["total_distance_km"], 13.5, places=1)
        self.assertEqual(data["total_sessions"], 2)

    def test_avg_hr_computed(self):
        self._make_cardio(3, avg_hr=140)
        self._make_cardio(6, avg_hr=160)

        data = self.client.get(self.URL).json()
        self.assertAlmostEqual(data["avg_hr_bpm"], 150.0, places=0)

    def test_pure_strength_workout_excluded(self):
        # Workout with neither distance nor HR — should not appear
        Workout.objects.create(
            user=self.user, name="strength",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=3),
            duration_min=60,
        )
        data = self.client.get(self.URL).json()
        self.assertEqual(data["total_sessions"], 0)

    def test_weekly_distance_breakdown(self):
        self._make_cardio(3, distance_km=5.0)
        data = self.client.get(self.URL).json()
        self.assertEqual(len(data["weekly_distance"]), 1)
        self.assertAlmostEqual(data["weekly_distance"][0]["distance_km"], 5.0, places=1)

    def test_days_param_limits_window(self):
        self._make_cardio(100, distance_km=10.0)
        self._make_cardio(3, distance_km=5.0)
        data = self.client.get(self.URL, {"days": 30}).json()
        self.assertAlmostEqual(data["total_distance_km"], 5.0, places=1)

    def test_excludes_other_users(self):
        other = _make_user("cardio_other")
        Workout.objects.create(
            user=other, name="run",
            status=Workout.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=3),
            duration_min=45, avg_hr_bpm=145,
        )
        data = self.client.get(self.URL).json()
        self.assertEqual(data["total_sessions"], 0)


# ---------------------------------------------------------------------------
# Day-of-week heatmap
# ---------------------------------------------------------------------------

class DowHeatmapTests(TestCase):
    URL = "/api/v1/workouts/dow-heatmap/"

    def setUp(self):
        self.user = _make_user("dow_user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = _make_exercise("Row", "back")

    def test_always_returns_7_days(self):
        # Even with no workouts, all 7 days are returned with zeros
        data = self.client.get(self.URL).json()
        self.assertEqual(len(data), 7)
        self.assertEqual([d["day_of_week"] for d in data], list(range(1, 8)))

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)

    def test_invalid_weeks_param(self):
        self.assertEqual(self.client.get(self.URL, {"weeks": "z"}).status_code, 400)

    def test_workout_count_per_day(self):
        # Create a workout on a known day of week
        # Use a recent Monday (ISO weekday 1)
        from datetime import date as date_cls
        today = timezone.now().date()
        days_since_monday = today.weekday()  # 0=Mon
        last_monday = today - timedelta(days=days_since_monday)
        monday_dt = timezone.make_aware(
            timezone.datetime(last_monday.year, last_monday.month, last_monday.day, 10, 0)
        )

        _make_workout(self.user, started_at=monday_dt)

        data = self.client.get(self.URL).json()
        monday_entry = next(d for d in data if d["day_of_week"] == 1)
        self.assertEqual(monday_entry["workout_count"], 1)
        self.assertEqual(monday_entry["day_name"], "Monday")

    def test_zero_entries_for_unworked_days(self):
        data = self.client.get(self.URL).json()
        for entry in data:
            self.assertEqual(entry["workout_count"], 0)
            self.assertEqual(entry["total_volume_kg"], 0.0)
            self.assertEqual(entry["avg_volume_kg"], 0.0)

    def test_volume_aggregated_per_day(self):
        from datetime import date as date_cls
        today = timezone.now().date()
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday)
        monday_dt = timezone.make_aware(
            timezone.datetime(last_monday.year, last_monday.month, last_monday.day, 10, 0)
        )
        w = _make_workout(self.user, started_at=monday_dt)
        _add_sets(w, self.exercise, [(5, 100)])  # 500 kg

        data = self.client.get(self.URL).json()
        monday_entry = next(d for d in data if d["day_of_week"] == 1)
        self.assertAlmostEqual(monday_entry["total_volume_kg"], 500.0, places=1)
        self.assertAlmostEqual(monday_entry["avg_volume_kg"], 500.0, places=1)

    def test_excludes_other_users(self):
        other = _make_user("dow_other")
        _make_workout(other)
        data = self.client.get(self.URL).json()
        self.assertTrue(all(d["workout_count"] == 0 for d in data))

    def test_draft_workouts_excluded(self):
        _make_workout(self.user, status=Workout.Status.DRAFT)
        data = self.client.get(self.URL).json()
        self.assertTrue(all(d["workout_count"] == 0 for d in data))


# ---------------------------------------------------------------------------
# Muscle balance
# ---------------------------------------------------------------------------

class MuscleBalanceTests(TestCase):
    URL = "/api/v1/workouts/muscle-balance/"

    def setUp(self):
        self.user = _make_user("balance_user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.chest = _make_exercise("Bench", "chest")
        self.back = _make_exercise("Pull-Up", "back")
        self.quads = _make_exercise("Leg Press", "quads")

    def test_empty_no_workouts(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_volume_kg"], 0.0)
        self.assertIsNone(data["push_pull_ratio"])
        self.assertIsNone(data["upper_lower_ratio"])
        self.assertEqual(data["muscle_shares"], [])

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)

    def test_invalid_weeks_param(self):
        self.assertEqual(self.client.get(self.URL, {"weeks": "bad"}).status_code, 400)

    def test_push_pull_ratio(self):
        w = _make_workout(self.user)
        _add_sets(w, self.chest, [(5, 100)])  # push: 500 kg
        _add_sets(w, self.back,  [(5, 100)])  # pull: 500 kg

        data = self.client.get(self.URL).json()
        self.assertAlmostEqual(data["push_pull_ratio"], 1.0, places=2)

    def test_push_pull_ratio_none_when_no_pull(self):
        w = _make_workout(self.user)
        _add_sets(w, self.chest, [(5, 100)])

        data = self.client.get(self.URL).json()
        # No pull volume → ratio is None
        self.assertIsNone(data["push_pull_ratio"])

    def test_upper_lower_ratio(self):
        w = _make_workout(self.user)
        _add_sets(w, self.chest, [(5, 100)])  # upper: 500
        _add_sets(w, self.quads, [(5, 100)])  # lower: 500

        data = self.client.get(self.URL).json()
        self.assertAlmostEqual(data["upper_lower_ratio"], 1.0, places=2)

    def test_muscle_shares_sum_to_100(self):
        w = _make_workout(self.user)
        _add_sets(w, self.chest, [(5, 100)])
        _add_sets(w, self.back,  [(5, 80)])

        data = self.client.get(self.URL).json()
        total_pct = sum(s["share_pct"] for s in data["muscle_shares"])
        self.assertAlmostEqual(total_pct, 100.0, places=0)

    def test_muscle_shares_sorted_by_volume_descending(self):
        w = _make_workout(self.user)
        _add_sets(w, self.chest, [(5, 80)])   # 400 kg
        _add_sets(w, self.back,  [(5, 100)])  # 500 kg — should rank first

        data = self.client.get(self.URL).json()
        shares = data["muscle_shares"]
        self.assertEqual(shares[0]["muscle"], "back")

    def test_warmup_sets_excluded(self):
        w = _make_workout(self.user)
        we = WorkoutExercise.objects.create(workout=w, exercise=self.chest, order=0)
        ExerciseSet.objects.create(workout_exercise=we, set_number=1, reps=10, weight=40,
                                   is_warmup=True, completed=True)
        ExerciseSet.objects.create(workout_exercise=we, set_number=2, reps=5, weight=100,
                                   is_warmup=False, completed=True)
        data = self.client.get(self.URL).json()
        self.assertAlmostEqual(data["total_volume_kg"], 500.0, places=1)

    def test_weeks_param_limits_window(self):
        old = _make_workout(self.user, started_at=timezone.now() - timedelta(weeks=20))
        recent = _make_workout(self.user, started_at=timezone.now() - timedelta(weeks=2))
        _add_sets(old, self.chest, [(5, 100)])
        _add_sets(recent, self.back, [(5, 100)])

        data = self.client.get(self.URL, {"weeks": 4}).json()
        muscles = {s["muscle"] for s in data["muscle_shares"]}
        self.assertIn("back", muscles)
        self.assertNotIn("chest", muscles)

    def test_excludes_other_users(self):
        other = _make_user("balance_other")
        w = _make_workout(other)
        _add_sets(w, self.chest, [(5, 100)])
        data = self.client.get(self.URL).json()
        self.assertEqual(data["total_volume_kg"], 0.0)
