"""Celery application factory for fitness_tracker.

The worker entrypoint runs:  celery -A fitness_tracker worker -l info
The beat entrypoint runs:    celery -A fitness_tracker beat -l info
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fitness_tracker.settings")

app = Celery("fitness_tracker")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Register the task_postrun listener that stamps last_run_at for the
# boot-time catch-up runner. Import for side effects only.
from fitness_tracker import catchup_signals  # noqa: E402, F401


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
