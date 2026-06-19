"""Tests for the reports REST API views."""
from datetime import date
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from reports.models import FitnessReport


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username="api_user", password="pw", email="api@test.com", is_active=True
    )


@pytest.fixture
def auth_client(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def report(user):
    return FitnessReport.objects.create(
        user=user,
        period_type=FitnessReport.PeriodType.WEEKLY,
        period_start=date(2025, 1, 1),
        period_end=date(2025, 1, 7),
    )


@pytest.mark.django_db
class TestReportListView:
    url = "/api/v1/reports/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == 401

    def test_returns_user_reports(self, auth_client, report):
        resp = auth_client.get(self.url)
        assert resp.status_code == 200
        results = resp.data.get("results", resp.data)
        assert len(results) == 1
        assert results[0]["period_type"] == "weekly"

    def test_does_not_return_other_users_reports(self, auth_client, db):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other = User.objects.create_user(
            username="other", password="pw", email="other@test.com", is_active=True
        )
        FitnessReport.objects.create(
            user=other, period_type="weekly",
            period_start=date(2025, 1, 1), period_end=date(2025, 1, 7),
        )
        resp = auth_client.get(self.url)
        assert resp.status_code == 200
        results = resp.data.get("results", resp.data)
        assert len(results) == 0

    def test_serializer_fields(self, auth_client, report):
        resp = auth_client.get(self.url)
        results = resp.data.get("results", resp.data)
        keys = set(results[0].keys())
        assert {"id", "period_type", "period_start", "period_end", "generated_at", "emailed_at", "pdf_url"} <= keys


@pytest.mark.django_db
class TestTriggerReportView:
    url = "/api/v1/reports/trigger/"

    def test_requires_auth(self, api_client):
        resp = api_client.post(self.url, {"period_type": "weekly"})
        assert resp.status_code == 401

    def test_accepts_valid_period_types(self, auth_client):
        with patch("reports.views.generate_and_email_report") as mock_task:
            mock_task.delay = lambda *a: None
            for pt in ("weekly", "monthly", "yearly"):
                resp = auth_client.post(self.url, {"period_type": pt})
                assert resp.status_code == 202, f"Expected 202 for {pt}, got {resp.status_code}"

    def test_rejects_invalid_period_type(self, auth_client):
        resp = auth_client.post(self.url, {"period_type": "daily"})
        assert resp.status_code == 400

    def test_queues_celery_task(self, auth_client, user):
        with patch("reports.views.generate_and_email_report") as mock_task:
            mock_task.delay = lambda uid, pt: None
            resp = auth_client.post(self.url, {"period_type": "weekly"})
        assert resp.status_code == 202
        assert "weekly" in resp.data["detail"].lower()

    def test_response_contains_detail(self, auth_client):
        with patch("reports.views.generate_and_email_report") as mock_task:
            mock_task.delay = lambda *a: None
            resp = auth_client.post(self.url, {"period_type": "monthly"})
        assert "detail" in resp.data


@pytest.mark.django_db
class TestProfileReportFields:
    """Verify report prefs are exposed/settable via /api/v1/auth/me/."""

    url = "/api/v1/auth/me/"

    def test_me_includes_report_fields(self, auth_client):
        resp = auth_client.get(self.url)
        assert resp.status_code == 200
        profile = resp.data["profile"]
        assert "reports_enabled" in profile
        assert "report_frequency" in profile
        assert "last_report_sent_at" in profile

    def test_can_enable_reports_via_patch(self, auth_client, user):
        resp = auth_client.patch(
            self.url,
            {"profile": {"reports_enabled": True, "report_frequency": "monthly"}},
            format="json",
        )
        assert resp.status_code == 200
        user.profile.refresh_from_db()
        assert user.profile.reports_enabled is True
        assert user.profile.report_frequency == "monthly"

    def test_last_report_sent_at_is_read_only(self, auth_client, user):
        resp = auth_client.patch(
            self.url,
            {"profile": {"last_report_sent_at": "2025-01-01T00:00:00Z"}},
            format="json",
        )
        assert resp.status_code == 200
        user.profile.refresh_from_db()
        assert user.profile.last_report_sent_at is None
