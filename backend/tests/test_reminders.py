"""Tests for the reminders app: CRUD and ownership isolation."""
import pytest

from tests.factories import ReminderFactory

REMINDER_URL = "/api/v1/reminders/"


def reminder_url(pk):
    return f"/api/v1/reminders/{pk}/"


@pytest.mark.django_db
class TestReminderList:
    def test_returns_only_own_reminders(self, auth_client, user, other_user):
        ReminderFactory(user=user)
        ReminderFactory(user=other_user)
        res = auth_client.get(REMINDER_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(REMINDER_URL)
        assert res.status_code == 401


@pytest.mark.django_db
class TestReminderCreate:
    def test_creates_reminder_with_required_fields(self, auth_client, user):
        payload = {
            "title": "Morning Workout",
            "reminder_type": "workout",
            "time_of_day": "07:00:00",
            "days_of_week": ["mon", "wed", "fri"],
        }
        res = auth_client.post(REMINDER_URL, payload, format="json")
        assert res.status_code == 201
        assert res.data["title"] == "Morning Workout"
        assert res.data["is_active"] is True

    def test_missing_required_fields_returns_400(self, auth_client):
        res = auth_client.post(REMINDER_URL, {"title": "No time"})
        assert res.status_code == 400

    def test_invalid_reminder_type_returns_400(self, auth_client):
        payload = {
            "title": "Bad type",
            "reminder_type": "telekinesis",
            "time_of_day": "08:00:00",
        }
        res = auth_client.post(REMINDER_URL, payload, format="json")
        assert res.status_code == 400


@pytest.mark.django_db
class TestReminderDetail:
    def test_owner_can_retrieve_reminder(self, auth_client, user):
        reminder = ReminderFactory(user=user)
        res = auth_client.get(reminder_url(reminder.pk))
        assert res.status_code == 200
        assert res.data["id"] == reminder.pk

    def test_other_users_reminder_returns_404(self, auth_client, other_user):
        reminder = ReminderFactory(user=other_user)
        res = auth_client.get(reminder_url(reminder.pk))
        assert res.status_code == 404

    def test_owner_can_toggle_active_state(self, auth_client, user):
        reminder = ReminderFactory(user=user, is_active=True)
        res = auth_client.patch(reminder_url(reminder.pk), {"is_active": False})
        assert res.status_code == 200
        assert res.data["is_active"] is False

    def test_owner_can_delete_reminder(self, auth_client, user):
        reminder = ReminderFactory(user=user)
        res = auth_client.delete(reminder_url(reminder.pk))
        assert res.status_code == 204
        res = auth_client.get(reminder_url(reminder.pk))
        assert res.status_code == 404
