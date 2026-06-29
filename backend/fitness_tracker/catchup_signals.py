"""Stamp the cache with last_run_at for catch-up-tracked tasks on success.

Runs in the worker process via Celery's ``task_postrun`` signal so beat-driven
fires and boot-time catch-up runs share one source of truth. Failed tasks do
not update the stamp — they will be retried on the next boot.
"""
from __future__ import annotations

from datetime import datetime, timezone

from celery.signals import task_postrun
from django.core.cache import cache

from fitness_tracker.catchup import CATCHUP_TASK_NAMES, state_key


@task_postrun.connect
def _record_catchup_run(sender=None, task=None, state=None, **kwargs) -> None:
    if state != "SUCCESS":
        return
    name = getattr(task, "name", None)
    if name not in CATCHUP_TASK_NAMES:
        return
    cache.set(
        state_key(name),
        datetime.now(timezone.utc).isoformat(),
        timeout=None,  # persist across reboots; only overwritten on the next run
    )
