"""Queue any beat-scheduled task whose last successful run is overdue.

Wired into ``entrypoint.sh`` for the ``web`` role so an intermittent server
self-heals on boot: tasks missed while the server was off are re-enqueued
once each, and beat takes over for subsequent fires.

State lives in the Django cache (Redis) under ``catchup:last_run:<task>`` and
is written by a ``task_postrun`` signal — so a healthy always-on deployment
never re-fires anything here.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery import current_app
from django.core.cache import cache
from django.core.management.base import BaseCommand

from fitness_tracker.catchup import CATCHUP_TASKS, state_key

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Queue any beat-scheduled task whose last run is older than its period."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would run without enqueuing anything.",
        )

    def handle(self, *args, **options) -> None:
        dry_run: bool = options["dry_run"]
        now = datetime.now(timezone.utc)
        triggered: list[str] = []
        skipped: list[str] = []
        failed: list[str] = []

        for entry in CATCHUP_TASKS:
            last_iso = cache.get(state_key(entry.task))
            last_run = datetime.fromisoformat(last_iso) if last_iso else None
            overdue = last_run is None or (now - last_run) >= entry.overdue_after

            if not overdue:
                skipped.append(entry.task)
                continue

            if dry_run:
                triggered.append(entry.task)
                continue

            try:
                current_app.send_task(entry.task)
            except Exception as exc:
                # Broker down, name typo, etc. — log and continue; we don't
                # want one bad entry to block the rest of boot.
                logger.warning("catchup: failed to enqueue %s: %s", entry.task, exc)
                failed.append(entry.task)
                continue

            triggered.append(entry.task)

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            f"{prefix}catchup: triggered={len(triggered)} "
            f"skipped={len(skipped)} failed={len(failed)}"
        )
        for name in triggered:
            self.stdout.write(f"  triggered: {name}")
        for name in skipped:
            self.stdout.write(f"  up-to-date: {name}")
        for name in failed:
            self.stdout.write(f"  failed:    {name}")
