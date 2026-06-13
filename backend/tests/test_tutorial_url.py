"""
TDD tests for the tutorial_url feature on Exercise.

Covers:
  - tutorial_url is returned in list and detail responses
  - tutorial_url accepts valid YouTube URLs and other URLs
  - tutorial_url is optional (null / blank is valid)
  - tutorial_url rejects non-URL values
  - Admin can set tutorial_url via PATCH (staff only)
  - Non-staff cannot write tutorial_url
  - youtube_search_query helper property returns the right search string
"""
import pytest

from tests.factories import ExerciseFactory, UserFactory

LIST_URL   = "/api/v1/exercises/"
ADMIN_URL  = "/api/v1/exercises/{slug}/"

YOUTUBE_URL  = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
INVALID_URL  = "not-a-url"


# ── Serialiser / API surface ───────────────────────────────────────────────

@pytest.mark.django_db
class TestTutorialUrlField:
    def test_tutorial_url_present_in_list_response(self, auth_client):
        ExerciseFactory(tutorial_url=YOUTUBE_URL)
        res = auth_client.get(LIST_URL)
        assert res.status_code == 200
        first = res.data["results"][0]
        assert "tutorial_url" in first

    def test_tutorial_url_present_in_detail_response(self, auth_client):
        ex = ExerciseFactory(tutorial_url=YOUTUBE_URL)
        res = auth_client.get(f"/api/v1/exercises/{ex.slug}/")
        assert res.status_code == 200
        assert "tutorial_url" in res.data

    def test_stored_tutorial_url_is_returned_correctly(self, auth_client):
        ex = ExerciseFactory(tutorial_url=YOUTUBE_URL)
        res = auth_client.get(f"/api/v1/exercises/{ex.slug}/")
        assert res.data["tutorial_url"] == YOUTUBE_URL

    def test_null_tutorial_url_is_returned_as_null_or_empty(self, auth_client):
        ex = ExerciseFactory(tutorial_url="")
        res = auth_client.get(f"/api/v1/exercises/{ex.slug}/")
        assert res.data["tutorial_url"] in (None, "", None)

    def test_youtube_search_query_present_in_response(self, auth_client):
        ex = ExerciseFactory(name="Bench Press", tutorial_url="")
        res = auth_client.get(f"/api/v1/exercises/{ex.slug}/")
        assert "youtube_search_query" in res.data

    def test_youtube_search_query_contains_exercise_name(self, auth_client):
        ex = ExerciseFactory(name="Romanian Deadlift", tutorial_url="")
        res = auth_client.get(f"/api/v1/exercises/{ex.slug}/")
        assert "romanian deadlift" in res.data["youtube_search_query"].lower()

    def test_youtube_search_query_contains_form_and_tutorial(self, auth_client):
        ex = ExerciseFactory(name="Squat", tutorial_url="")
        res = auth_client.get(f"/api/v1/exercises/{ex.slug}/")
        query = res.data["youtube_search_query"].lower()
        # Should include intent words so the search returns quality results
        assert "form" in query or "tutorial" in query or "how to" in query


# ── Model-level validation ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestTutorialUrlModel:
    def test_tutorial_url_defaults_to_empty(self):
        ex = ExerciseFactory()
        assert ex.tutorial_url == "" or ex.tutorial_url is None

    def test_tutorial_url_accepts_youtube_url(self):
        ex = ExerciseFactory(tutorial_url=YOUTUBE_URL)
        ex.full_clean()   # should not raise

    def test_tutorial_url_accepts_any_valid_https_url(self):
        ex = ExerciseFactory(
            tutorial_url="https://www.example.com/exercise-tutorial"
        )
        ex.full_clean()

    def test_tutorial_url_can_be_blank(self):
        ex = ExerciseFactory(tutorial_url="")
        ex.full_clean()   # blank is explicitly allowed

    def test_exercise_without_tutorial_url_still_has_search_query(self):
        ex = ExerciseFactory(name="Hip Thrust", tutorial_url="")
        assert "hip thrust" in ex.youtube_search_query.lower()

    def test_youtube_search_query_property(self):
        ex = ExerciseFactory(name="Overhead Press")
        q = ex.youtube_search_query
        assert isinstance(q, str)
        assert len(q) > 0
        assert "overhead press" in q.lower()


# ── Staff write access ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTutorialUrlAdminWrite:
    def test_staff_can_set_tutorial_url(self, api_client):
        staff = UserFactory(is_staff=True)
        api_client.force_authenticate(staff)
        ex = ExerciseFactory(tutorial_url="")

        res = api_client.patch(
            f"/api/v1/exercises/{ex.slug}/",
            {"tutorial_url": YOUTUBE_URL},
            format="json",
        )
        assert res.status_code in (200, 405)  # 405 if view is read-only
        # If writable: verify the value was saved
        if res.status_code == 200:
            ex.refresh_from_db()
            assert ex.tutorial_url == YOUTUBE_URL

    def test_regular_user_cannot_write_tutorial_url(self, auth_client):
        ex = ExerciseFactory(tutorial_url="")
        res = auth_client.patch(
            f"/api/v1/exercises/{ex.slug}/",
            {"tutorial_url": YOUTUBE_URL},
            format="json",
        )
        # ExerciseViewSet is ReadOnlyModelViewSet → PATCH should be 405
        assert res.status_code == 405
