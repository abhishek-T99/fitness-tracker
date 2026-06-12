"""
Tests for Celery tasks.

CELERY_TASK_ALWAYS_EAGER=True (set in test_settings.py) means tasks run
synchronously in the same process, making side effects directly assertable.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from django.core import mail
from django.utils import timezone

from accounts.tokens import make_email_verify_token, make_password_reset_token
from tests.factories import (
    GoalFactory,
    ReminderFactory,
    UserFactory,
    WorkoutFactory,
)


@pytest.mark.django_db
class TestSendVerificationEmail:
    def test_sends_email_to_user(self):
        user = UserFactory(is_active=False)
        token = make_email_verify_token(user.pk)

        from accounts.tasks import send_verification_email
        send_verification_email(user.pk, token)

        assert len(mail.outbox) == 1
        assert user.email in mail.outbox[0].to

    def test_email_contains_verify_link(self):
        user = UserFactory(is_active=False)
        token = make_email_verify_token(user.pk)

        from accounts.tasks import send_verification_email
        send_verification_email(user.pk, token)

        body = mail.outbox[0].body or mail.outbox[0].alternatives[0][0]
        assert token in body

    def test_nonexistent_user_does_not_raise(self):
        from accounts.tasks import send_verification_email
        # Should exit silently, not crash the worker.
        send_verification_email(99999, "some-token")
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestSendPasswordResetEmail:
    def test_sends_reset_email_to_user(self):
        user = UserFactory()
        token = make_password_reset_token(user.pk)

        from accounts.tasks import send_password_reset_email
        send_password_reset_email(user.pk, token)

        assert len(mail.outbox) == 1
        assert user.email in mail.outbox[0].to

    def test_email_contains_reset_token(self):
        user = UserFactory()
        token = make_password_reset_token(user.pk)

        from accounts.tasks import send_password_reset_email
        send_password_reset_email(user.pk, token)

        body = mail.outbox[0].body or mail.outbox[0].alternatives[0][0]
        assert token in body


@pytest.mark.django_db
class TestMarkExpiredGoals:
    def test_overdue_goal_with_target_met_is_marked_achieved(self):
        yesterday = date.today() - timedelta(days=1)
        goal = GoalFactory(
            deadline=yesterday,
            status="active",
            target_value="70.00",
            current_value="70.00",  # target met
        )

        from goals.tasks import mark_expired_goals
        mark_expired_goals()

        goal.refresh_from_db()
        assert goal.status == "achieved"

    def test_active_goal_within_deadline_is_not_touched(self):
        tomorrow = date.today() + timedelta(days=1)
        goal = GoalFactory(deadline=tomorrow, status="active")

        from goals.tasks import mark_expired_goals
        mark_expired_goals()

        goal.refresh_from_db()
        assert goal.status == "active"

    def test_goal_without_deadline_is_not_touched(self):
        goal = GoalFactory(deadline=None, status="active")

        from goals.tasks import mark_expired_goals
        mark_expired_goals()

        goal.refresh_from_db()
        assert goal.status == "active"


@pytest.mark.django_db
class TestDecayInactiveStreaks:
    def test_streak_with_stale_last_workout_date_is_reset(self):
        from achievements.models import Streak
        user = UserFactory()
        streak = Streak.objects.create(
            user=user,
            current_days=5,
            longest_days=5,
            last_workout_date=date.today() - timedelta(days=2),
        )

        from achievements.tasks import decay_inactive_streaks
        decay_inactive_streaks()

        streak.refresh_from_db()
        assert streak.current_days == 0

    def test_streak_active_today_is_not_reset(self):
        from achievements.models import Streak
        user = UserFactory()
        streak = Streak.objects.create(
            user=user,
            current_days=3,
            longest_days=3,
            last_workout_date=date.today(),
        )

        from achievements.tasks import decay_inactive_streaks
        decay_inactive_streaks()

        streak.refresh_from_db()
        assert streak.current_days == 3


@pytest.mark.django_db
class TestDispatchDueReminders:
    def test_active_reminder_matching_current_time_is_dispatched(self):
        """
        We patch the 'now' used inside dispatch_due_reminders so we can
        control which reminders qualify without relying on real wall time.
        """
        from django.utils import timezone as tz
        now = tz.now()
        day_abbrev = now.strftime("%a").lower()  # e.g. "mon"
        current_time = now.time().replace(second=0, microsecond=0)

        reminder = ReminderFactory(
            time_of_day=current_time,
            days_of_week=[day_abbrev],
            is_active=True,
        )

        from reminders.tasks import dispatch_due_reminders, deliver_reminder
        with patch.object(deliver_reminder, "delay") as mock_deliver:
            dispatch_due_reminders()
            mock_deliver.assert_called_once_with(reminder.pk)

    def test_inactive_reminder_is_not_dispatched(self):
        from django.utils import timezone as tz
        now = tz.now()
        day_abbrev = now.strftime("%a").lower()
        current_time = now.time().replace(second=0, microsecond=0)

        ReminderFactory(
            time_of_day=current_time,
            days_of_week=[day_abbrev],
            is_active=False,
        )

        from reminders.tasks import dispatch_due_reminders, deliver_reminder
        with patch.object(deliver_reminder, "delay") as mock_deliver:
            dispatch_due_reminders()
            mock_deliver.assert_not_called()
