"""FitnessReport model tests."""
from datetime import date

import pytest
from django.contrib.auth import get_user_model

from reports.models import FitnessReport

User = get_user_model()


@pytest.mark.django_db
class TestFitnessReportModel:
    def test_str(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="rptuser", password="pw", email="rpt@test.com"
        )
        report = FitnessReport.objects.create(
            user=user,
            period_type=FitnessReport.PeriodType.WEEKLY,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 7),
        )
        assert "rptuser" in str(report)
        assert "weekly" in str(report)

    def test_default_ordering_is_newest_first(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="rptuser2", password="pw", email="rpt2@test.com"
        )
        r1 = FitnessReport.objects.create(
            user=user, period_type="weekly",
            period_start=date(2025, 1, 1), period_end=date(2025, 1, 7),
        )
        r2 = FitnessReport.objects.create(
            user=user, period_type="weekly",
            period_start=date(2025, 1, 8), period_end=date(2025, 1, 14),
        )
        reports = list(FitnessReport.objects.filter(user=user))
        assert reports[0].pk == r2.pk  # newest first

    def test_period_type_choices(self):
        choices = {c[0] for c in FitnessReport.PeriodType.choices}
        assert choices == {"weekly", "monthly", "yearly"}
