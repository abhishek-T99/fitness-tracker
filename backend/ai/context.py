"""Per-user context pack.

A small JSON-serialisable snapshot of who the user is, what they've eaten
today, what their goals look like, etc. Every feature shares this so the
agent has a stable picture without each feature re-gathering it.

The pack is rendered into the system prompt as a single block and marked
cacheable so repeated calls within the prompt-cache TTL stay cheap.
"""
from __future__ import annotations

import json
from datetime import datetime, time
from typing import Any, Dict

from django.utils import timezone


def _safe(value: Any, default: Any = None) -> Any:
    return default if value is None else value


def build(user) -> Dict[str, Any]:
    """Return a small JSON-safe summary the model can reason over."""
    today = timezone.localdate()
    profile = getattr(user, "profile", None)

    pack: Dict[str, Any] = {
        "user": {
            "id": user.id,
            "username": user.username,
            "timezone": str(timezone.get_current_timezone()),
            "today": today.isoformat(),
            "current_local_time": timezone.localtime().isoformat(timespec="minutes"),
        },
        "profile": {},
        "today_nutrition": {},
    }

    if profile is not None:
        pack["profile"] = {
            "daily_calorie_goal": _safe(getattr(profile, "daily_calorie_goal", None)),
            "weekly_workout_goal": _safe(getattr(profile, "weekly_workout_goal", None)),
            "activity_level": _safe(getattr(profile, "activity_level", None)),
            "units": _safe(getattr(profile, "units", "metric")),
        }

    # Today's nutrition is cheap to compute and the most useful state for the
    # nutrition-parse feature. Other features can extend this lazily.
    try:
        from django.db.models import Sum
        from nutrition.models import WaterLog

        start = timezone.make_aware(datetime.combine(today, time.min))
        end = timezone.make_aware(datetime.combine(today, time.max))
        water_total = (
            WaterLog.objects.filter(user=user, logged_at__range=(start, end))
            .aggregate(total=Sum("amount_ml"))["total"]
            or 0
        )
        pack["today_nutrition"]["water_ml"] = water_total
    except Exception:
        # Stay defensive — context pack should never break a request.
        pass

    return pack


def render_system_block(pack: Dict[str, Any]) -> Dict[str, Any]:
    """Format the context pack as a cacheable system text block."""
    body = json.dumps(pack, sort_keys=True, default=str)
    return {
        "type": "text",
        "text": f"<user_context>\n{body}\n</user_context>",
    }
