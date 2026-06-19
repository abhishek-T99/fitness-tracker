"""Tests for report generation and dispatch Celery tasks."""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        username="task_user", password="pw", email="task@test.com", is_active=True
    )
    return u


@pytest.fixture
def opted_in_user(db):
    u = User.objects.create_user(
        username="opted_in", password="pw", email="opted@test.com", is_active=True
    )
    from accounts.models import Profile
    Profile.objects.filter(user=u).update(
        reports_enabled=True,
        report_frequency="weekly",
    )
    u.refresh_from_db()
    return u


@pytest.mark.django_db
class TestPeriodBounds:
    def test_weekly_bounds(self):
        from reports.tasks import _period_bounds

        ref = date(2025, 6, 16)   # Monday
        start, end = _period_bounds("weekly", ref)
        assert end.weekday() == 6   # Sunday
        assert (end - start).days == 6

    def test_monthly_bounds(self):
        from reports.tasks import _period_bounds

        ref = date(2025, 3, 1)   # March 1 → February report
        start, end = _period_bounds("monthly", ref)
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)

    def test_yearly_bounds(self):
        from reports.tasks import _period_bounds

        ref = date(2025, 1, 1)   # New Year → previous year
        start, end = _period_bounds("yearly", ref)
        assert start == date(2024, 1, 1)
        assert end == date(2024, 12, 31)

    def test_invalid_period_type_raises(self):
        from reports.tasks import _period_bounds

        with pytest.raises(ValueError):
            _period_bounds("daily")


@pytest.mark.django_db
class TestGenerateAndEmailReport:
    def test_creates_fitness_report_record(self, user):
        from reports.models import FitnessReport
        from reports.tasks import generate_and_email_report

        _fake_data = {
            "user": user,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 1, 7),
            "workout": {"count": 3, "total_minutes": 150, "total_calories": 600,
                        "total_volume_kg": 1000, "longest_workout_min": 60,
                        "avg_duration_min": 50, "avg_rpe": None, "total_distance_km": 0,
                        "top_muscles": [], "weekly_goal": 3, "goal_for_period": 3, "goal_met": True},
            "streak": {"current": 5, "longest": 10},
            "nutrition": {"logged_days": 7, "period_days": 7, "avg_calories": 2000,
                          "avg_protein_g": 120, "avg_carbs_g": 200, "avg_fat_g": 70,
                          "calorie_goal": 2200, "days_on_target": 5, "avg_water_ml": 2000, "avg_water_l": 2.0},
            "body": {"units": "metric", "weight_unit": "kg", "weight_start": 80,
                     "weight_end": 79, "weight_change": -1.0, "bmi_start": 26.1, "bmi_end": 25.8},
            "goals": {"active_count": 1, "active_goals": [], "avg_progress_percent": 50, "achieved_in_period": 0, "achieved_titles": []},
            "achievements": {"new_count": 0, "new_badges": [], "total_count": 3},
        }
        with (
            patch("reports.report_service.collect_report_data", return_value=_fake_data),
            patch("reports.pdf_generator.generate_pdf", return_value=b"%PDF-fake"),
            patch("reports.tasks._send_report_email"),
        ):
            report_id = generate_and_email_report(user.pk, "weekly", "2025-01-08")

        assert report_id is not None
        assert FitnessReport.objects.filter(pk=report_id).exists()
        rpt = FitnessReport.objects.get(pk=report_id)
        assert rpt.period_type == "weekly"
        assert rpt.emailed_at is not None

    def test_skips_nonexistent_user(self):
        from reports.tasks import generate_and_email_report

        result = generate_and_email_report(99999, "weekly")
        assert result is None

    def test_updates_last_report_sent_at(self, user):
        from reports.tasks import generate_and_email_report

        _empty = {
            "user": user,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 1, 7),
            "workout": {"count": 0, "total_minutes": 0, "total_calories": 0,
                        "total_volume_kg": 0, "longest_workout_min": 0,
                        "avg_duration_min": 0, "avg_rpe": None, "total_distance_km": 0,
                        "top_muscles": [], "weekly_goal": 3, "goal_for_period": 3, "goal_met": False},
            "streak": {"current": 0, "longest": 0},
            "nutrition": {"logged_days": 0, "period_days": 7, "avg_calories": 0,
                          "avg_protein_g": 0, "avg_carbs_g": 0, "avg_fat_g": 0,
                          "calorie_goal": None, "days_on_target": 0, "avg_water_ml": 0, "avg_water_l": 0},
            "body": {"units": "metric", "weight_unit": "kg", "weight_start": None,
                     "weight_end": None, "weight_change": None, "bmi_start": None, "bmi_end": None},
            "goals": {"active_count": 0, "active_goals": [], "avg_progress_percent": 0, "achieved_in_period": 0, "achieved_titles": []},
            "achievements": {"new_count": 0, "new_badges": [], "total_count": 0},
        }
        with (
            patch("reports.report_service.collect_report_data", return_value=_empty),
            patch("reports.pdf_generator.generate_pdf", return_value=b"%PDF-fake"),
            patch("reports.tasks._send_report_email"),
        ):
            generate_and_email_report(user.pk, "weekly")

        user.profile.refresh_from_db()
        assert user.profile.last_report_sent_at is not None


@pytest.mark.django_db
class TestDispatchReports:
    def test_dispatch_weekly_queues_opted_in_users(self, opted_in_user):
        from reports.tasks import dispatch_weekly_reports

        with patch("reports.tasks.generate_and_email_report") as mock_task:
            mock_task.delay = MagicMock()
            dispatch_weekly_reports()
            mock_task.delay.assert_called_once_with(opted_in_user.pk, "weekly")

    def test_dispatch_skips_users_with_different_frequency(self, opted_in_user):
        from accounts.models import Profile
        from reports.tasks import dispatch_weekly_reports

        Profile.objects.filter(user=opted_in_user).update(report_frequency="monthly")

        with patch("reports.tasks.generate_and_email_report") as mock_task:
            mock_task.delay = MagicMock()
            dispatch_weekly_reports()
            mock_task.delay.assert_not_called()

    def test_dispatch_skips_disabled_users(self, opted_in_user):
        from accounts.models import Profile
        from reports.tasks import dispatch_weekly_reports

        Profile.objects.filter(user=opted_in_user).update(reports_enabled=False)

        with patch("reports.tasks.generate_and_email_report") as mock_task:
            mock_task.delay = MagicMock()
            dispatch_weekly_reports()
            mock_task.delay.assert_not_called()
