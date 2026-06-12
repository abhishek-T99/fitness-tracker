"""Weekly per-user progress summary — runs Mondays via Beat.

The output is cached so the Dashboard / Profile can surface it cheaply
without recomputing aggregates on every request.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

WEEKLY_SUMMARY_CACHE_TTL = 60 * 60 * 24 * 8  # one week + slack


def weekly_summary_cache_key(user_id: int) -> str:
    return f"weekly_summary:{user_id}"


@shared_task(ignore_result=True)
def build_weekly_summaries():
    """Build last-week stats for every active user and cache them."""
    from workouts.models import Workout

    User = get_user_model()
    now = timezone.now()
    week_start = now - timedelta(days=7)
    built = 0
    for user_id in User.objects.filter(is_active=True).values_list("id", flat=True):
        agg = Workout.objects.filter(
            user_id=user_id,
            status=Workout.Status.COMPLETED,
            started_at__gte=week_start,
        ).aggregate(
            workouts=Sum("duration_min"),
            minutes=Sum("duration_min"),
            calories=Sum("calories_burned"),
        )
        payload = {
            "generated_at": now.isoformat(),
            "workouts": agg["workouts"] or 0,
            "minutes": agg["minutes"] or 0,
            "calories": agg["calories"] or 0,
        }
        cache.set(weekly_summary_cache_key(user_id), payload, WEEKLY_SUMMARY_CACHE_TTL)
        built += 1
    logger.info("build_weekly_summaries: cached %d user summaries", built)
    return built
