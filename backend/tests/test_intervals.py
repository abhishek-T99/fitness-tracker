"""
Tests for Intervals.icu integration.

Strategy
--------
1. Client unit tests  — mock requests.get and verify our normalization,
   error-raising, and activity-mapping logic.
2. View tests         — mock the intervals client functions and assert
   credential storage, dedup, error paths, and the sync trigger.
3. Task tests         — mock the client and assert workout creation / update /
   dedup logic inside sync_intervals_activities.
"""
from datetime import datetime, timezone as dt_timezone
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from integrations.models import Integration, OAuthToken, Provider, SyncLog
from integrations.intervals import IntervalsError
from workouts.models import Workout
from tests.factories import UserFactory, WorkoutFactory

CONNECT_URL = "/api/v1/integrations/intervals/connect/"
DISCONNECT_URL = "/api/v1/integrations/intervals/disconnect/"
SYNC_URL = "/api/v1/integrations/intervals/sync/"
WEBHOOK_URL = "/api/v1/integrations/intervals/webhook/"

FAKE_ATHLETE = {
    "id": "i12345",
    "name": "Jane Doe",
    "email": "jane@example.com",
}

FAKE_ACTIVITY = {
    "id": 9001,
    "name": "Morning Run",
    "type": "Run",
    "start_date_local": "2024-03-15T07:00:00",
    "moving_time": 3600,
    "elapsed_time": 3700,
    "distance": 10000.0,
    "average_heartrate": 145.0,
    "calories": 600,
    "icu_training_load": 55,
}

FAKE_ACTIVITIES = [FAKE_ACTIVITY]


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_integration(user):
    integration = Integration.objects.create(
        user=user, provider=Provider.INTERVALS, is_active=True
    )
    OAuthToken.objects.create(
        integration=integration,
        access_token="test-api-key",
        refresh_token="",
        expires_at=datetime(2099, 1, 1, tzinfo=dt_timezone.utc),
        athlete_id="i12345",
    )
    return integration


# ── Client unit tests ──────────────────────────────────────────────────────────

class TestIntervalsClient:
    @patch("integrations.intervals.requests.get")
    def test_verify_credentials_success(self, mock_get):
        from integrations.intervals import verify_credentials
        mock_get.return_value = MagicMock(ok=True, status_code=200, json=lambda: FAKE_ATHLETE)
        result = verify_credentials("i12345", "good-key")
        assert result["id"] == "i12345"

    @patch("integrations.intervals.requests.get")
    def test_verify_credentials_bad_key_raises(self, mock_get):
        from integrations.intervals import verify_credentials
        mock_get.return_value = MagicMock(ok=False, status_code=401, json=lambda: {})
        with pytest.raises(IntervalsError):
            verify_credentials("i12345", "bad-key")

    @patch("integrations.intervals.requests.get")
    def test_get_activities_returns_list(self, mock_get):
        from integrations.intervals import get_activities
        mock_get.return_value = MagicMock(ok=True, status_code=200, json=lambda: FAKE_ACTIVITIES)
        result = get_activities("i12345", "key")
        assert len(result) == 1
        assert result[0]["id"] == 9001

    @patch("integrations.intervals.requests.get")
    def test_get_activities_api_error_raises(self, mock_get):
        from integrations.intervals import get_activities
        mock_get.return_value = MagicMock(ok=False, status_code=500, text="Internal Server Error")
        with pytest.raises(IntervalsError):
            get_activities("i12345", "key")

    def test_map_activity_to_workout_fields(self):
        from integrations.intervals import map_activity_to_workout
        result = map_activity_to_workout(FAKE_ACTIVITY)
        assert result["name"] == "Morning Run"
        assert result["duration_min"] == 60
        assert result["calories_burned"] == 600
        assert result["status"] == "completed"
        assert result["source"] == "intervals"
        assert float(result["distance_km"]) == pytest.approx(10.0, rel=0.01)
        assert result["avg_hr_bpm"] == 145
        assert "Training load: 55" in result["notes"]

    def test_map_unnamed_activity_uses_type_label(self):
        from integrations.intervals import map_activity_to_workout
        activity = {**FAKE_ACTIVITY, "name": "", "type": "Ride"}
        result = map_activity_to_workout(activity)
        assert "Ride" in result["name"]

    def test_map_activity_no_distance(self):
        from integrations.intervals import map_activity_to_workout
        activity = {**FAKE_ACTIVITY, "distance": None}
        result = map_activity_to_workout(activity)
        assert "km" not in result["notes"]

    def test_map_activity_uses_elapsed_time_fallback(self):
        from integrations.intervals import map_activity_to_workout
        activity = {**FAKE_ACTIVITY, "moving_time": None, "elapsed_time": 1800}
        result = map_activity_to_workout(activity)
        assert result["duration_min"] == 30


# ── Connect view ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIntervalsConnect:
    @patch("integrations.intervals.verify_credentials", return_value=FAKE_ATHLETE)
    @patch("integrations.tasks.sync_intervals_wellness.delay")
    @patch("integrations.tasks.sync_intervals_activities.delay")
    def test_valid_credentials_create_integration(self, _act, _well, _verify, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        res = api_client.post(CONNECT_URL, {"athlete_id": "i12345", "api_key": "good-key"})
        assert res.status_code == 201
        assert Integration.objects.filter(user=user, provider=Provider.INTERVALS).exists()

    @patch("integrations.intervals.verify_credentials", return_value=FAKE_ATHLETE)
    @patch("integrations.tasks.sync_intervals_wellness.delay")
    @patch("integrations.tasks.sync_intervals_activities.delay")
    def test_valid_credentials_store_api_key(self, _act, _well, _verify, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        api_client.post(CONNECT_URL, {"athlete_id": "i12345", "api_key": "good-key"})
        token = OAuthToken.objects.get(integration__user=user)
        assert token.access_token == "good-key"
        assert token.athlete_id == "i12345"

    @patch("integrations.intervals.verify_credentials", return_value=FAKE_ATHLETE)
    @patch("integrations.tasks.sync_intervals_wellness.delay")
    @patch("integrations.tasks.sync_intervals_activities.delay")
    def test_reconnect_does_not_duplicate(self, _act, _well, _verify, api_client):
        user = UserFactory()
        _make_integration(user)
        api_client.force_authenticate(user)
        api_client.post(CONNECT_URL, {"athlete_id": "i12345", "api_key": "good-key"})
        assert Integration.objects.filter(user=user, provider=Provider.INTERVALS).count() == 1

    @patch("integrations.intervals.verify_credentials", return_value=FAKE_ATHLETE)
    @patch("integrations.tasks.sync_intervals_wellness.delay")
    @patch("integrations.tasks.sync_intervals_activities.delay")
    def test_connect_triggers_backfill(self, mock_act, _well, _verify, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        api_client.post(CONNECT_URL, {"athlete_id": "i12345", "api_key": "good-key"})
        integration = Integration.objects.get(user=user)
        mock_act.assert_called_once_with(integration.pk, days_back=30)

    @patch("integrations.intervals.verify_credentials", side_effect=IntervalsError("Invalid API key."))
    def test_bad_credentials_return_401(self, _, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        res = api_client.post(CONNECT_URL, {"athlete_id": "i12345", "api_key": "bad-key"})
        assert res.status_code == 401
        assert not Integration.objects.filter(user=user).exists()

    def test_missing_fields_return_400(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        res = api_client.post(CONNECT_URL, {"athlete_id": "i12345"})
        assert res.status_code == 400

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.post(CONNECT_URL, {"athlete_id": "x", "api_key": "y"})
        assert res.status_code == 401


# ── Disconnect view ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIntervalsDisconnect:
    def test_disconnect_deactivates_integration(self, api_client):
        user = UserFactory()
        integration = _make_integration(user)
        api_client.force_authenticate(user)
        res = api_client.delete(DISCONNECT_URL)
        assert res.status_code == 204
        integration.refresh_from_db()
        assert not integration.is_active

    def test_disconnect_removes_api_key(self, api_client):
        user = UserFactory()
        _make_integration(user)
        api_client.force_authenticate(user)
        api_client.delete(DISCONNECT_URL)
        assert not OAuthToken.objects.filter(integration__user=user).exists()

    def test_not_connected_returns_404(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        res = api_client.delete(DISCONNECT_URL)
        assert res.status_code == 404

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.delete(DISCONNECT_URL)
        assert res.status_code == 401


# ── Manual sync view ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIntervalsSyncView:
    @patch("integrations.tasks.sync_intervals_activities.delay")
    def test_triggers_sync_task(self, mock_delay, api_client):
        user = UserFactory()
        integration = _make_integration(user)
        api_client.force_authenticate(user)
        res = api_client.post(SYNC_URL, {"days_back": 14})
        assert res.status_code == 200
        mock_delay.assert_called_once_with(integration.pk, days_back=14)

    @patch("integrations.tasks.sync_intervals_activities.delay")
    def test_default_days_back_is_7(self, mock_delay, api_client):
        user = UserFactory()
        integration = _make_integration(user)
        api_client.force_authenticate(user)
        api_client.post(SYNC_URL, {})
        mock_delay.assert_called_once_with(integration.pk, days_back=7)

    def test_not_connected_returns_404(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        res = api_client.post(SYNC_URL, {})
        assert res.status_code == 404


# ── Webhook view ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIntervalsWebhook:
    @patch("integrations.tasks.sync_intervals_activities.delay")
    def test_known_athlete_triggers_sync(self, mock_delay, api_client):
        user = UserFactory()
        integration = _make_integration(user)
        res = api_client.post(WEBHOOK_URL, {
            "athlete_id": "i12345",
            "activity_id": 9001,
            "type": "activity",
        }, format="json")
        assert res.status_code == 200
        mock_delay.assert_called_once_with(integration.pk, days_back=2)

    @patch("integrations.tasks.sync_intervals_activities.delay")
    def test_unknown_athlete_returns_200_no_sync(self, mock_delay, api_client):
        res = api_client.post(WEBHOOK_URL, {
            "athlete_id": "i99999",
            "activity_id": 9001,
        }, format="json")
        assert res.status_code == 200
        mock_delay.assert_not_called()

    @patch("integrations.tasks.sync_intervals_activities.delay")
    def test_missing_payload_returns_200(self, mock_delay, api_client):
        res = api_client.post(WEBHOOK_URL, {}, format="json")
        assert res.status_code == 200
        mock_delay.assert_not_called()


# ── Task: sync_intervals_activities ───────────────────────────────────────────

@pytest.mark.django_db
class TestSyncIntervalsActivities:
    @patch("integrations.intervals.get_activities", return_value=FAKE_ACTIVITIES)
    def test_creates_workout_from_activity(self, _):
        from integrations.tasks import sync_intervals_activities
        user = UserFactory()
        integration = _make_integration(user)
        sync_intervals_activities(integration.pk, days_back=7)
        assert Workout.objects.filter(user=user, name="Morning Run").exists()

    @patch("integrations.intervals.get_activities", return_value=FAKE_ACTIVITIES)
    def test_logs_success_with_workout_link(self, _):
        from integrations.tasks import sync_intervals_activities
        user = UserFactory()
        integration = _make_integration(user)
        sync_intervals_activities(integration.pk, days_back=7)
        log = SyncLog.objects.get(integration=integration, external_id="9001")
        assert log.status == SyncLog.Status.SUCCESS
        assert log.workout is not None

    @patch("integrations.intervals.get_activities", return_value=FAKE_ACTIVITIES)
    def test_duplicate_activity_is_not_recreated(self, _):
        from integrations.tasks import sync_intervals_activities
        user = UserFactory()
        integration = _make_integration(user)
        sync_intervals_activities(integration.pk, days_back=7)
        sync_intervals_activities(integration.pk, days_back=7)
        assert Workout.objects.filter(user=user).count() == 1

    @patch("integrations.intervals.get_activities", return_value=[{**FAKE_ACTIVITY, "name": "Updated Run"}])
    def test_changed_activity_updates_existing_workout(self, _):
        from integrations.tasks import sync_intervals_activities
        user = UserFactory()
        integration = _make_integration(user)
        workout = WorkoutFactory(user=user, name="Morning Run")
        SyncLog.objects.create(
            integration=integration,
            event_type="activity.create",
            external_id="9001",
            status=SyncLog.Status.SUCCESS,
            workout=workout,
        )
        sync_intervals_activities(integration.pk, days_back=7)
        workout.refresh_from_db()
        assert workout.name == "Updated Run"

    @patch("integrations.intervals.get_activities", return_value=FAKE_ACTIVITIES)
    def test_updates_last_synced_at(self, _):
        from integrations.tasks import sync_intervals_activities
        user = UserFactory()
        integration = _make_integration(user)
        assert integration.last_synced_at is None
        sync_intervals_activities(integration.pk, days_back=7)
        integration.refresh_from_db()
        assert integration.last_synced_at is not None

    @patch("integrations.intervals.get_activities", side_effect=IntervalsError("Rate limited"))
    def test_api_failure_logs_and_retries(self, _):
        from integrations.tasks import sync_intervals_activities
        user = UserFactory()
        integration = _make_integration(user)
        with pytest.raises(Exception):
            sync_intervals_activities(integration.pk, days_back=7)
        log = SyncLog.objects.get(integration=integration)
        assert log.status == SyncLog.Status.FAILED
        assert "Rate limited" in log.detail
