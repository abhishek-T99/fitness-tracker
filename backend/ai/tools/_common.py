"""Tools every feature can use."""
from __future__ import annotations

from django.utils import timezone

from ..registry import tool


@tool(
    name="get_current_datetime",
    description=(
        "Get the current date and time in the user's timezone. Use this when you need "
        "to anchor an event to 'now' (e.g. 'I just drank a glass of water' → logged_at = "
        "the value returned here). Returns ISO 8601 strings."
    ),
    schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
    kind="read",
)
def get_current_datetime(*, user, **_) -> dict:
    now = timezone.localtime()
    return {
        "iso": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        "time": now.time().isoformat(timespec="minutes"),
        "timezone": str(timezone.get_current_timezone()),
    }
