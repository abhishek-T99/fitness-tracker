"""
TDD tests for GET /api/v1/workouts/exercise-history/

The endpoint returns, for each requested exercise ID:
  - The most recent ExerciseSet data (from the user's latest workout that
    included that exercise)
  - A personal best (heaviest completed set, reps > 0)

Used by the Active Workout Session to show previous performance and
drive the progressive-overload suggestion on the client side.
"""
import pytest
from django.utils import timezone

from tests.factories import (
    ExerciseFactory,
    ExerciseSetFactory,
    UserFactory,
    WorkoutExerciseFactory,
    WorkoutFactory,
)

URL = "/api/v1/workouts/exercise-history/"


# ── helpers ───────────────────────────────────────────────────────────────────

def _workout_with_exercise(user, exercise, sets_data, days_ago=0):
    """Create a completed workout for *user* containing *exercise* with sets."""
    started = timezone.now() - timezone.timedelta(days=days_ago)
    workout = WorkoutFactory(user=user, started_at=started, status="completed")
    we = WorkoutExerciseFactory(workout=workout, exercise=exercise)
    for i, (reps, weight, rpe) in enumerate(sets_data, start=1):
        ExerciseSetFactory(
            workout_exercise=we,
            set_number=i,
            reps=reps,
            weight=str(weight),
            rpe=rpe,
            completed=True,
        )
    return workout


# ── Auth ──────────────────────────────────────────────────────────────────────

class TestAuth:
    def test_requires_authentication(self, api_client):
        res = api_client.get(URL, {"exercise_ids": "1"})
        assert res.status_code == 401

    @pytest.mark.django_db
    def test_missing_exercise_ids_param_returns_400(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        res = api_client.get(URL)
        assert res.status_code == 400

    @pytest.mark.django_db
    def test_empty_exercise_ids_returns_400(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        res = api_client.get(URL, {"exercise_ids": ""})
        assert res.status_code == 400


# ── History retrieval ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHistory:
    def test_returns_last_session_sets(self, api_client):
        user = UserFactory()
        ex = ExerciseFactory()
        _workout_with_exercise(user, ex, [(8, 80.0, 8), (8, 80.0, 8), (7, 80.0, 9)])
        api_client.force_authenticate(user)

        res = api_client.get(URL, {"exercise_ids": str(ex.id)})
        assert res.status_code == 200
        data = res.data[str(ex.id)]
        assert data is not None
        assert len(data["last_session"]["sets"]) == 3
        assert data["last_session"]["sets"][0]["reps"] == 8
        assert float(data["last_session"]["sets"][0]["weight"]) == 80.0

    def test_returns_null_for_exercise_with_no_history(self, api_client):
        user = UserFactory()
        ex = ExerciseFactory()
        api_client.force_authenticate(user)

        res = api_client.get(URL, {"exercise_ids": str(ex.id)})
        assert res.status_code == 200
        assert res.data[str(ex.id)] is None

    def test_most_recent_workout_is_returned(self, api_client):
        user = UserFactory()
        ex = ExerciseFactory()
        _workout_with_exercise(user, ex, [(6, 70.0, 8)], days_ago=7)   # older
        _workout_with_exercise(user, ex, [(8, 80.0, 8)], days_ago=1)   # newer
        api_client.force_authenticate(user)

        res = api_client.get(URL, {"exercise_ids": str(ex.id)})
        sets = res.data[str(ex.id)]["last_session"]["sets"]
        assert float(sets[0]["weight"]) == 80.0  # most recent workout

    def test_multiple_exercises_in_one_request(self, api_client):
        user = UserFactory()
        ex1 = ExerciseFactory()
        ex2 = ExerciseFactory()
        ex3 = ExerciseFactory()
        _workout_with_exercise(user, ex1, [(8, 80.0, 7)])
        _workout_with_exercise(user, ex2, [(10, 40.0, 6)])
        # ex3 has no history
        api_client.force_authenticate(user)

        ids = f"{ex1.id},{ex2.id},{ex3.id}"
        res = api_client.get(URL, {"exercise_ids": ids})
        assert res.status_code == 200
        assert res.data[str(ex1.id)] is not None
        assert res.data[str(ex2.id)] is not None
        assert res.data[str(ex3.id)] is None

    def test_only_returns_own_data(self, api_client):
        user_a = UserFactory()
        user_b = UserFactory()
        ex = ExerciseFactory()
        _workout_with_exercise(user_b, ex, [(8, 100.0, 9)])  # belongs to user_b
        api_client.force_authenticate(user_a)

        res = api_client.get(URL, {"exercise_ids": str(ex.id)})
        assert res.data[str(ex.id)] is None  # user_a sees no data

    def test_skips_uncompleted_sets(self, api_client):
        user = UserFactory()
        ex = ExerciseFactory()
        workout = WorkoutFactory(user=user, status="completed")
        we = WorkoutExerciseFactory(workout=workout, exercise=ex)
        ExerciseSetFactory(workout_exercise=we, set_number=1, reps=8, weight="80.00", completed=True)
        ExerciseSetFactory(workout_exercise=we, set_number=2, reps=0, weight="80.00", completed=False)
        api_client.force_authenticate(user)

        res = api_client.get(URL, {"exercise_ids": str(ex.id)})
        sets = res.data[str(ex.id)]["last_session"]["sets"]
        assert len(sets) == 1  # only the completed set

    def test_last_session_includes_workout_date(self, api_client):
        user = UserFactory()
        ex = ExerciseFactory()
        _workout_with_exercise(user, ex, [(8, 80.0, 8)])
        api_client.force_authenticate(user)

        res = api_client.get(URL, {"exercise_ids": str(ex.id)})
        assert "workout_started_at" in res.data[str(ex.id)]["last_session"]


# ── Personal best ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPersonalBest:
    def test_personal_best_is_heaviest_weight(self, api_client):
        user = UserFactory()
        ex = ExerciseFactory()
        _workout_with_exercise(user, ex, [(5, 100.0, 9)], days_ago=14)
        _workout_with_exercise(user, ex, [(8, 80.0,  8)], days_ago=1)
        api_client.force_authenticate(user)

        res = api_client.get(URL, {"exercise_ids": str(ex.id)})
        pb = res.data[str(ex.id)]["personal_best"]
        assert float(pb["weight"]) == 100.0  # heaviest, not most recent
        assert pb["reps"] == 5

    def test_personal_best_is_null_when_no_history(self, api_client):
        user = UserFactory()
        ex = ExerciseFactory()
        api_client.force_authenticate(user)

        res = api_client.get(URL, {"exercise_ids": str(ex.id)})
        assert res.data[str(ex.id)] is None
