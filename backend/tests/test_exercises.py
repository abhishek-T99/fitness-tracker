"""Tests for the exercise catalog (read-only, cached)."""
import pytest

from tests.factories import ExerciseFactory

LIST_URL = "/api/v1/exercises/"


def detail_url(slug):
    return f"/api/v1/exercises/{slug}/"


@pytest.mark.django_db
class TestExerciseList:
    def test_authenticated_user_can_list_exercises(self, auth_client):
        ExerciseFactory.create_batch(3)
        res = auth_client.get(LIST_URL)
        assert res.status_code == 200
        assert res.data["count"] == 3

    def test_unauthenticated_user_can_list_exercises(self, api_client):
        """Exercises use IsAuthenticatedOrReadOnly — public read access."""
        ExerciseFactory()
        res = api_client.get(LIST_URL)
        assert res.status_code == 200

    def test_filter_by_category(self, auth_client):
        ExerciseFactory(category="strength")
        ExerciseFactory(category="cardio")
        res = auth_client.get(LIST_URL, {"category": "strength"})
        assert res.status_code == 200
        assert res.data["count"] == 1
        assert res.data["results"][0]["category"] == "strength"

    def test_filter_by_primary_muscle(self, auth_client):
        ExerciseFactory(primary_muscle="chest")
        ExerciseFactory(primary_muscle="back")
        res = auth_client.get(LIST_URL, {"primary_muscle": "chest"})
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_filter_by_equipment(self, auth_client):
        ExerciseFactory(equipment="barbell")
        ExerciseFactory(equipment="dumbbell")
        res = auth_client.get(LIST_URL, {"equipment": "dumbbell"})
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_search_by_name(self, auth_client):
        ExerciseFactory(name="Bench Press")
        ExerciseFactory(name="Squat")
        res = auth_client.get(LIST_URL, {"search": "bench"})
        assert res.status_code == 200
        assert res.data["count"] == 1
        assert "Bench" in res.data["results"][0]["name"]

    def test_empty_catalog_returns_empty_results(self, auth_client):
        res = auth_client.get(LIST_URL)
        assert res.status_code == 200
        assert res.data["count"] == 0


@pytest.mark.django_db
class TestExerciseDetail:
    def test_returns_exercise_by_slug(self, auth_client, exercise):
        res = auth_client.get(detail_url(exercise.slug))
        assert res.status_code == 200
        assert res.data["slug"] == exercise.slug
        assert res.data["name"] == exercise.name

    def test_nonexistent_slug_returns_404(self, auth_client):
        res = auth_client.get(detail_url("does-not-exist"))
        assert res.status_code == 404
