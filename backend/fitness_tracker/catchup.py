"""Registry of beat-scheduled tasks to re-attempt on web boot when overdue.

This project is deployed on an intermittent server (single-user), so Celery
beat doesn't run 24/7 and scheduled fires get missed. On each web boot we
queue any task whose last successful run is older than its natural schedule
period; beat takes over from there.

The "last run" timestamp is stamped by a task_postrun signal (see
``catchup_signals``) regardless of whether the run was triggered by beat or
by the boot-time catch-up command — so a healthy always-on deployment never
triggers catch-up unnecessarily.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class CatchupTask:
    task: str
    overdue_after: timedelta


# Order matches CELERY_BEAT_SCHEDULE in settings for readability.
# Yearly reports are intentionally excluded — catching up a missed yearly
# report on an arbitrary boot day produces confusing artifacts.
CATCHUP_TASKS: tuple[CatchupTask, ...] = (
    CatchupTask("reminders.tasks.dispatch_due_reminders", timedelta(minutes=1)),
    CatchupTask("achievements.tasks.decay_inactive_streaks", timedelta(days=1)),
    CatchupTask("goals.tasks.mark_expired_goals", timedelta(days=1)),
    CatchupTask("accounts.tasks.build_weekly_summaries", timedelta(days=7)),
    CatchupTask("notifications.tasks.notify_streak_at_risk", timedelta(days=1)),
    CatchupTask("notifications.tasks.notify_goal_deadlines", timedelta(days=1)),
    CatchupTask("integrations.tasks.sync_all_intervals_integrations", timedelta(hours=6)),
    CatchupTask("levels.tasks.generate_weekly_challenges", timedelta(days=7)),
    CatchupTask("levels.tasks.update_athlete_classes", timedelta(days=7)),
    CatchupTask("reports.tasks.dispatch_weekly_reports", timedelta(days=7)),
    CatchupTask("reports.tasks.dispatch_monthly_reports", timedelta(days=30)),
)

CATCHUP_TASK_NAMES: frozenset[str] = frozenset(t.task for t in CATCHUP_TASKS)

_STATE_KEY_PREFIX = "catchup:last_run:"


def state_key(task_name: str) -> str:
    return f"{_STATE_KEY_PREFIX}{task_name}"
