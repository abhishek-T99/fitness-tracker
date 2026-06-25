"""Per-user daily token budgets.

A coarse guardrail so a runaway agent loop or an attacker who steals a
session token can't burn the project's Anthropic credit. Tracked in Redis
because django-redis is already configured project-wide; the in-memory
test cache implements ``incr`` too so this works under pytest.
"""
from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


DEFAULT_DAILY_TOKEN_CAP = 250_000  # input + output combined; tune in settings


class BudgetExceeded(Exception):
    """Raised when a user has consumed their daily token allowance."""


def _key(user_id: int) -> str:
    today = timezone.localdate().isoformat()
    return f"ai:budget:{user_id}:{today}"


def get_cap() -> int:
    return int(getattr(settings, "AI_DAILY_TOKEN_CAP", DEFAULT_DAILY_TOKEN_CAP))


def check(user_id: int) -> None:
    """Raise BudgetExceeded if the user is already over budget for today."""
    cap = get_cap()
    if cap <= 0:
        return  # disabled
    used = cache.get(_key(user_id), 0) or 0
    if used >= cap:
        raise BudgetExceeded(
            f"AI daily token budget of {cap} exceeded. Try again tomorrow."
        )


def record(user_id: int, tokens: int) -> None:
    """Add ``tokens`` to the user's running daily total. Best-effort."""
    if tokens <= 0:
        return
    key = _key(user_id)
    try:
        # 26h TTL so the key survives until shortly after the next localdate
        # roll-over, then drops without manual cleanup.
        if cache.get(key) is None:
            cache.set(key, tokens, timeout=60 * 60 * 26)
        else:
            cache.incr(key, tokens)
    except Exception:
        # Budget tracking is advisory — never let it block a real request.
        pass
