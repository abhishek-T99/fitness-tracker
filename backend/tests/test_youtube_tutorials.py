"""
TDD tests for GET /api/v1/exercises/youtube-tutorials/?exercise_slug=bench-press

The endpoint:
  1. Looks up the exercise by slug
  2. Checks Redis cache (key based on the exercise's youtube_search_query)
  3. On miss: calls YouTube Data API (search + statistics) and caches the result
  4. Returns a list of video dicts: video_id, title, channel, thumbnail, view_count, duration_label

Mock boundaries
───────────────
  - exercises.youtube.requests.get  — the HTTP client used by our YouTube module
  - django.core.cache               — already patched to in-memory in test_settings

All YouTube network calls are mocked so these tests never hit the real API.
"""
from unittest.mock import MagicMock, call, patch

import pytest

from tests.factories import ExerciseFactory, UserFactory

URL = "/api/v1/exercises/youtube-tutorials/"


# ── Fake YouTube API responses ─────────────────────────────────────────────

def _search_response(video_ids):
    """Fake YouTube search.list response."""
    return MagicMock(
        status_code=200,
        json=lambda: {
            "items": [
                {
                    "id": {"kind": "youtube#video", "videoId": vid},
                    "snippet": {
                        "title": f"Tutorial for {vid}",
                        "channelTitle": f"Channel {vid}",
                        "thumbnails": {
                            "medium": {"url": f"https://img.youtube.com/vi/{vid}/mqdefault.jpg"}
                        },
                    },
                }
                for vid in video_ids
            ]
        },
    )


def _stats_response(video_data):
    """Fake YouTube videos.list response.  video_data = [(id, views, duration)]"""
    return MagicMock(
        status_code=200,
        json=lambda: {
            "items": [
                {
                    "id": vid,
                    "snippet": {
                        "title": f"Tutorial {vid}",
                        "channelTitle": f"Channel {vid}",
                        "thumbnails": {
                            "medium": {"url": f"https://img.youtube.com/vi/{vid}/mqdefault.jpg"}
                        },
                    },
                    "statistics": {"viewCount": str(views)},
                    "contentDetails": {"duration": duration},
                }
                for vid, views, duration in video_data
            ]
        },
    )


def _error_response(status_code=403):
    return MagicMock(status_code=status_code, json=lambda: {"error": {"message": "quota exceeded"}})


# ── Auth & input validation ────────────────────────────────────────────────

class TestAuthAndValidation:
    def test_requires_authentication(self, api_client):
        res = api_client.get(URL)
        assert res.status_code == 401

    @pytest.mark.django_db
    def test_missing_slug_returns_400(self, auth_client):
        res = auth_client.get(URL)
        assert res.status_code == 400

    @pytest.mark.django_db
    def test_nonexistent_slug_returns_404(self, auth_client):
        res = auth_client.get(URL, {"exercise_slug": "does-not-exist"})
        assert res.status_code == 404

    @pytest.mark.django_db
    def test_missing_api_key_returns_503(self, auth_client, settings):
        settings.YOUTUBE_API_KEY = ""
        ex = ExerciseFactory()
        res = auth_client.get(URL, {"exercise_slug": ex.slug})
        assert res.status_code == 503


# ── Successful response shape ──────────────────────────────────────────────

@pytest.mark.django_db
class TestSuccessfulResponse:
    @patch("exercises.youtube.requests.get")
    def test_returns_200_with_videos_list(self, mock_get, auth_client, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        ex = ExerciseFactory(name="Bench Press")
        ids = ["vid1", "vid2"]
        mock_get.side_effect = [
            _search_response(ids),
            _stats_response([("vid1", 2_000_000, "PT5M30S"), ("vid2", 900_000, "PT8M")]),
        ]
        res = auth_client.get(URL, {"exercise_slug": ex.slug})
        assert res.status_code == 200
        assert "videos" in res.data

    @patch("exercises.youtube.requests.get")
    def test_each_video_has_required_fields(self, mock_get, auth_client, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        ex = ExerciseFactory()
        ids = ["aaa"]
        mock_get.side_effect = [
            _search_response(ids),
            _stats_response([("aaa", 1_000_000, "PT4M")]),
        ]
        res = auth_client.get(URL, {"exercise_slug": ex.slug})
        video = res.data["videos"][0]
        for field in ("video_id", "title", "channel", "thumbnail", "view_count", "duration_label"):
            assert field in video, f"Missing field: {field}"

    @patch("exercises.youtube.requests.get")
    def test_videos_sorted_by_view_count_descending(self, mock_get, auth_client, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        ex = ExerciseFactory()
        ids = ["low", "high", "mid"]
        mock_get.side_effect = [
            _search_response(ids),
            _stats_response([
                ("low",  100_000, "PT3M"),
                ("high", 5_000_000, "PT6M"),
                ("mid",  800_000, "PT4M"),
            ]),
        ]
        res = auth_client.get(URL, {"exercise_slug": ex.slug})
        counts = [v["view_count"] for v in res.data["videos"]]
        assert counts == sorted(counts, reverse=True)

    @patch("exercises.youtube.requests.get")
    def test_returns_at_most_four_videos(self, mock_get, auth_client, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        ex = ExerciseFactory()
        ids = [f"v{i}" for i in range(8)]
        mock_get.side_effect = [
            _search_response(ids),
            _stats_response([(vid, i * 100_000, "PT5M") for i, vid in enumerate(ids)]),
        ]
        res = auth_client.get(URL, {"exercise_slug": ex.slug})
        assert len(res.data["videos"]) <= 4

    @patch("exercises.youtube.requests.get")
    def test_duration_label_formatted_correctly(self, mock_get, auth_client, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        ex = ExerciseFactory()
        mock_get.side_effect = [
            _search_response(["x1"]),
            _stats_response([("x1", 1_000_000, "PT4M30S")]),
        ]
        res = auth_client.get(URL, {"exercise_slug": ex.slug})
        assert res.data["videos"][0]["duration_label"] == "4:30"

    @patch("exercises.youtube.requests.get")
    def test_view_count_in_response_is_integer(self, mock_get, auth_client, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        ex = ExerciseFactory()
        mock_get.side_effect = [
            _search_response(["z1"]),
            _stats_response([("z1", 2_500_000, "PT7M")]),
        ]
        res = auth_client.get(URL, {"exercise_slug": ex.slug})
        assert isinstance(res.data["videos"][0]["view_count"], int)


# ── Caching ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCaching:
    @patch("exercises.youtube.requests.get")
    def test_second_request_uses_cache_not_api(self, mock_get, auth_client, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        ex = ExerciseFactory()
        mock_get.side_effect = [
            _search_response(["c1"]),
            _stats_response([("c1", 1_000_000, "PT3M")]),
        ]
        # First request — hits API
        auth_client.get(URL, {"exercise_slug": ex.slug})
        # Second request — should use cache, not call the API again
        auth_client.get(URL, {"exercise_slug": ex.slug})
        assert mock_get.call_count == 2  # search + stats, NOT 4


# ── Error handling ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestErrorHandling:
    @patch("exercises.youtube.requests.get")
    def test_youtube_search_api_error_returns_502(self, mock_get, auth_client, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        ex = ExerciseFactory()
        mock_get.return_value = _error_response(403)
        res = auth_client.get(URL, {"exercise_slug": ex.slug})
        assert res.status_code == 502

    @patch("exercises.youtube.requests.get")
    def test_empty_search_results_returns_empty_list(self, mock_get, auth_client, settings):
        settings.YOUTUBE_API_KEY = "fake-key"
        ex = ExerciseFactory()
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: {"items": []}),
        ]
        res = auth_client.get(URL, {"exercise_slug": ex.slug})
        assert res.status_code == 200
        assert res.data["videos"] == []

    @patch("exercises.youtube.requests.get")
    def test_network_timeout_returns_502(self, mock_get, auth_client, settings):
        import requests as req_lib
        settings.YOUTUBE_API_KEY = "fake-key"
        ex = ExerciseFactory()
        mock_get.side_effect = req_lib.Timeout()
        res = auth_client.get(URL, {"exercise_slug": ex.slug})
        assert res.status_code == 502
