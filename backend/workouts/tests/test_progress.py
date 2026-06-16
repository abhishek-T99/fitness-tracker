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
