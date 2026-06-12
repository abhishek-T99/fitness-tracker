"""Tests for the measurements app: CRUD, uniqueness, weight history, latest."""
import pytest
from datetime import date, timedelta

from tests.factories import BodyMeasurementFactory

MEASUREMENT_URL = "/api/v1/measurements/"
WEIGHT_HISTORY_URL = "/api/v1/measurements/weight_history/"
LATEST_URL = "/api/v1/measurements/latest/"


def measurement_url(pk):
    return f"/api/v1/measurements/{pk}/"


@pytest.mark.django_db
class TestBodyMeasurementList:
    def test_returns_only_own_measurements(self, auth_client, user, other_user):
        BodyMeasurementFactory(user=user)
        BodyMeasurementFactory(user=other_user)
        res = auth_client.get(MEASUREMENT_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(MEASUREMENT_URL)
        assert res.status_code == 401


@pytest.mark.django_db
class TestBodyMeasurementCreate:
    def test_creates_measurement_with_required_fields(self, auth_client, user):
        payload = {"recorded_at": "2024-06-01", "weight_kg": "74.5"}
        res = auth_client.post(MEASUREMENT_URL, payload)
        assert res.status_code == 201
        assert res.data["weight_kg"] == "74.50"

    def test_duplicate_date_for_same_user_returns_400(self, auth_client, user):
        BodyMeasurementFactory(user=user, recorded_at=date(2024, 6, 1))
        payload = {"recorded_at": "2024-06-01", "weight_kg": "75.0"}
        res = auth_client.post(MEASUREMENT_URL, payload)
        assert res.status_code == 400

    def test_same_date_for_different_users_is_allowed(self, auth_client, other_user):
        BodyMeasurementFactory(user=other_user, recorded_at=date(2024, 6, 1))
        payload = {"recorded_at": "2024-06-01", "weight_kg": "75.0"}
        res = auth_client.post(MEASUREMENT_URL, payload)
        assert res.status_code == 201


@pytest.mark.django_db
class TestBodyMeasurementDetail:
    def test_owner_can_retrieve_measurement(self, auth_client, user):
        m = BodyMeasurementFactory(user=user)
        res = auth_client.get(measurement_url(m.pk))
        assert res.status_code == 200

    def test_owner_can_update_measurement(self, auth_client, user):
        m = BodyMeasurementFactory(user=user)
        res = auth_client.patch(measurement_url(m.pk), {"weight_kg": "73.00"})
        assert res.status_code == 200
        assert res.data["weight_kg"] == "73.00"

    def test_owner_can_delete_measurement(self, auth_client, user):
        m = BodyMeasurementFactory(user=user)
        res = auth_client.delete(measurement_url(m.pk))
        assert res.status_code == 204

    def test_other_users_measurement_returns_404(self, auth_client, other_user):
        m = BodyMeasurementFactory(user=other_user)
        res = auth_client.get(measurement_url(m.pk))
        assert res.status_code == 404


@pytest.mark.django_db
class TestWeightHistory:
    def test_returns_chronological_weight_entries(self, auth_client, user):
        from django.utils import timezone
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        BodyMeasurementFactory(user=user, recorded_at=yesterday, weight_kg="80.0")
        BodyMeasurementFactory(user=user, recorded_at=today, weight_kg="78.0")
        res = auth_client.get(WEIGHT_HISTORY_URL)
        assert res.status_code == 200
        assert len(res.data) == 2
        assert "recorded_at" in res.data[0]
        assert "weight_kg" in res.data[0]

    def test_excludes_measurements_without_weight(self, auth_client, user):
        BodyMeasurementFactory(user=user, recorded_at=date(2024, 1, 1), weight_kg=None)
        res = auth_client.get(WEIGHT_HISTORY_URL)
        assert res.status_code == 200
        assert len(res.data) == 0


@pytest.mark.django_db
class TestLatestMeasurement:
    def test_returns_most_recent_measurement(self, auth_client, user):
        BodyMeasurementFactory(user=user, recorded_at=date(2024, 1, 1))
        BodyMeasurementFactory(user=user, recorded_at=date(2024, 3, 1))
        res = auth_client.get(LATEST_URL)
        assert res.status_code == 200
        assert res.data["recorded_at"] == "2024-03-01"

    def test_returns_empty_when_no_measurements(self, auth_client):
        res = auth_client.get(LATEST_URL)
        assert res.status_code == 200
        assert res.data == {}
