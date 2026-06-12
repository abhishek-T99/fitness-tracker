"""Tests for the goals app: CRUD, status filtering, and progress computation."""
import pytest

from tests.factories import GoalFactory

GOAL_URL = "/api/v1/goals/"


def goal_url(pk):
    return f"/api/v1/goals/{pk}/"


@pytest.mark.django_db
class TestGoalList:
    def test_returns_only_own_goals(self, auth_client, user, other_user):
        GoalFactory(user=user)
        GoalFactory(user=other_user)
        res = auth_client.get(GOAL_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_filter_by_status(self, auth_client, user):
        GoalFactory(user=user, status="active")
        GoalFactory(user=user, status="achieved")
        res = auth_client.get(GOAL_URL, {"status": "active"})
        assert res.status_code == 200
        assert res.data["count"] == 1
        assert res.data["results"][0]["status"] == "active"

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(GOAL_URL)
        assert res.status_code == 401


@pytest.mark.django_db
class TestGoalCreate:
    def test_creates_goal_with_required_fields(self, auth_client, user):
        payload = {
            "title": "Lose 5 kg",
            "goal_type": "weight_loss",
            "target_value": "75.00",
            "starting_value": "80.00",
        }
        res = auth_client.post(GOAL_URL, payload)
        assert res.status_code == 201
        assert res.data["title"] == "Lose 5 kg"
        assert res.data["status"] == "active"

    def test_missing_required_fields_returns_400(self, auth_client):
        res = auth_client.post(GOAL_URL, {"title": "No type"})
        assert res.status_code == 400


@pytest.mark.django_db
class TestGoalDetail:
    def test_owner_can_retrieve_goal(self, auth_client, user):
        goal = GoalFactory(user=user)
        res = auth_client.get(goal_url(goal.pk))
        assert res.status_code == 200
        assert res.data["id"] == goal.pk

    def test_other_users_goal_returns_404(self, auth_client, other_user):
        goal = GoalFactory(user=other_user)
        res = auth_client.get(goal_url(goal.pk))
        assert res.status_code == 404

    def test_owner_can_update_current_value(self, auth_client, user):
        goal = GoalFactory(user=user, target_value="75.00", starting_value="85.00", current_value="85.00")
        res = auth_client.patch(goal_url(goal.pk), {"current_value": "80.00"})
        assert res.status_code == 200
        assert float(res.data["current_value"]) == 80.0

    def test_owner_can_delete_goal(self, auth_client, user):
        goal = GoalFactory(user=user)
        res = auth_client.delete(goal_url(goal.pk))
        assert res.status_code == 204


@pytest.mark.django_db
class TestGoalProgressPercent:
    def test_progress_percent_is_correct(self, auth_client, user):
        # starting=80, target=70, current=75 → 50 % progress
        goal = GoalFactory(
            user=user,
            starting_value="80.00",
            target_value="70.00",
            current_value="75.00",
        )
        res = auth_client.get(goal_url(goal.pk))
        assert res.status_code == 200
        assert float(res.data["progress_percent"]) == pytest.approx(50.0, abs=1)

    def test_progress_clamped_at_100(self, auth_client, user):
        # current already past target
        goal = GoalFactory(
            user=user,
            starting_value="80.00",
            target_value="70.00",
            current_value="65.00",
        )
        res = auth_client.get(goal_url(goal.pk))
        assert float(res.data["progress_percent"]) == 100.0

    def test_zero_progress_when_not_started(self, auth_client, user):
        goal = GoalFactory(
            user=user,
            starting_value="80.00",
            target_value="70.00",
            current_value="80.00",
        )
        res = auth_client.get(goal_url(goal.pk))
        assert float(res.data["progress_percent"]) == 0.0
