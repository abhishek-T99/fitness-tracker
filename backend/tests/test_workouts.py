"""
Tests for the workouts app: workout CRUD, nested exercise/set writes,
ownership isolation, routine CRUD, and the stats endpoint.
"""
import pytest
from django.utils import timezone

from tests.factories import (
    ExerciseFactory,
    ExerciseSetFactory,
    RoutineFactory,
    WorkoutExerciseFactory,
    WorkoutFactory,
)

WORKOUT_LIST_URL = "/api/v1/workouts/"
ROUTINE_LIST_URL = "/api/v1/workouts/routines/"
STATS_URL = "/api/v1/workouts/stats/"


def workout_url(pk):
    return f"/api/v1/workouts/{pk}/"


def routine_url(pk):
    return f"/api/v1/workouts/routines/{pk}/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def workout_payload(exercise_id=None):
    payload = {
        "name": "Test Workout",
        "started_at": timezone.now().isoformat(),
        "status": "completed",
        "exercises": [],
    }
    if exercise_id:
        payload["exercises"] = [{
            "exercise": exercise_id,
            "order": 1,
            "notes": "",
            "sets": [
                {"set_number": 1, "reps": 10, "weight": "60.00"},
                {"set_number": 2, "reps": 8, "weight": "65.00"},
            ],
        }]
    return payload


# ---------------------------------------------------------------------------
# Workout CRUD
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWorkoutList:
    def test_returns_only_own_workouts(self, auth_client, user, other_user):
        WorkoutFactory(user=user)
        WorkoutFactory(user=user)
        WorkoutFactory(user=other_user)  # should not appear
        res = auth_client.get(WORKOUT_LIST_URL)
        assert res.status_code == 200
        assert res.data["count"] == 2

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(WORKOUT_LIST_URL)
        assert res.status_code == 401

    def test_empty_list_when_no_workouts(self, auth_client):
        res = auth_client.get(WORKOUT_LIST_URL)
        assert res.status_code == 200
        assert res.data["count"] == 0


@pytest.mark.django_db
class TestWorkoutCreate:
    def test_minimal_payload_creates_workout(self, auth_client, user):
        payload = {"started_at": timezone.now().isoformat(), "exercises": []}
        res = auth_client.post(WORKOUT_LIST_URL, payload, format="json")
        assert res.status_code == 201
        assert res.data["id"] is not None

    def test_nested_exercises_and_sets_are_created(self, auth_client, exercise):
        payload = workout_payload(exercise.pk)
        res = auth_client.post(WORKOUT_LIST_URL, payload, format="json")
        assert res.status_code == 201
        assert len(res.data["exercises"]) == 1
        assert len(res.data["exercises"][0]["sets"]) == 2

    def test_workout_belongs_to_requesting_user(self, auth_client, user, exercise):
        payload = workout_payload(exercise.pk)
        res = auth_client.post(WORKOUT_LIST_URL, payload, format="json")
        assert res.status_code == 201
        from workouts.models import Workout
        assert Workout.objects.get(pk=res.data["id"]).user == user


@pytest.mark.django_db
class TestWorkoutDetail:
    def test_owner_can_retrieve_workout(self, auth_client, user):
        workout = WorkoutFactory(user=user)
        res = auth_client.get(workout_url(workout.pk))
        assert res.status_code == 200
        assert res.data["id"] == workout.pk

    def test_other_users_workout_returns_404(self, auth_client, other_user):
        workout = WorkoutFactory(user=other_user)
        res = auth_client.get(workout_url(workout.pk))
        assert res.status_code == 404

    def test_nonexistent_workout_returns_404(self, auth_client):
        res = auth_client.get(workout_url(99999))
        assert res.status_code == 404


@pytest.mark.django_db
class TestWorkoutUpdate:
    def test_patch_updates_name(self, auth_client, user):
        workout = WorkoutFactory(user=user)
        res = auth_client.patch(workout_url(workout.pk), {"name": "Renamed"}, format="json")
        assert res.status_code == 200
        assert res.data["name"] == "Renamed"

    def test_patch_replaces_nested_exercises(self, auth_client, user):
        exercise = ExerciseFactory()
        workout = WorkoutFactory(user=user)
        # Add one exercise via PATCH
        payload = {
            "exercises": [{"exercise": exercise.pk, "order": 1, "sets": []}]
        }
        res = auth_client.patch(workout_url(workout.pk), payload, format="json")
        assert res.status_code == 200
        assert len(res.data["exercises"]) == 1

    def test_other_users_workout_cannot_be_updated(self, auth_client, other_user):
        workout = WorkoutFactory(user=other_user)
        res = auth_client.patch(workout_url(workout.pk), {"name": "Hijacked"}, format="json")
        assert res.status_code == 404


@pytest.mark.django_db
class TestWorkoutDelete:
    def test_owner_can_delete_workout(self, auth_client, user):
        workout = WorkoutFactory(user=user)
        res = auth_client.delete(workout_url(workout.pk))
        assert res.status_code == 204

    def test_other_users_workout_cannot_be_deleted(self, auth_client, other_user):
        workout = WorkoutFactory(user=other_user)
        res = auth_client.delete(workout_url(workout.pk))
        assert res.status_code == 404


@pytest.mark.django_db
class TestWorkoutStats:
    def test_stats_returns_expected_structure(self, auth_client, user):
        WorkoutFactory(user=user)
        res = auth_client.get(STATS_URL)
        assert res.status_code == 200
        assert "this_week" in res.data

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(STATS_URL)
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# Routines
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRoutineList:
    def test_returns_only_own_routines(self, auth_client, user, other_user):
        RoutineFactory(user=user)
        RoutineFactory(user=other_user)
        res = auth_client.get(ROUTINE_LIST_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1


@pytest.mark.django_db
class TestRoutineCreate:
    def test_creates_routine_with_items(self, auth_client, user):
        exercise = ExerciseFactory()
        payload = {
            "name": "Push Day",
            "items": [{"exercise": exercise.pk, "order": 1, "target_sets": 4, "target_reps": 10}],
        }
        res = auth_client.post(ROUTINE_LIST_URL, payload, format="json")
        assert res.status_code == 201
        assert res.data["name"] == "Push Day"
        assert len(res.data["items"]) == 1

    def test_duplicate_name_per_user_returns_400(self, auth_client, user):
        RoutineFactory(user=user, name="My Routine")
        payload = {"name": "My Routine", "items": []}
        res = auth_client.post(ROUTINE_LIST_URL, payload, format="json")
        assert res.status_code == 400


@pytest.mark.django_db
class TestRoutineDetail:
    def test_owner_can_retrieve_routine(self, auth_client, user):
        routine = RoutineFactory(user=user)
        res = auth_client.get(routine_url(routine.pk))
        assert res.status_code == 200

    def test_other_users_routine_returns_404(self, auth_client, other_user):
        routine = RoutineFactory(user=other_user)
        res = auth_client.get(routine_url(routine.pk))
        assert res.status_code == 404

    def test_owner_can_delete_routine(self, auth_client, user):
        routine = RoutineFactory(user=user)
        res = auth_client.delete(routine_url(routine.pk))
        assert res.status_code == 204
