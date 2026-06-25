"""Anthropic client wrapper.

Centralises model selection, API key handling, and the "no key configured"
degradation path so the runner stays unaware of either. A test fake can be
injected via ``set_client_factory`` — see ``tests/test_ai_runner.py``.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Optional

from django.conf import settings


class AIUnavailable(Exception):
    """Raised when the Anthropic API key is not configured."""


# Sensible defaults — see CLAUDE.md / plan: Sonnet 4.6 for tool-loop features.
DEFAULT_MODEL = "claude-sonnet-4-6"


_factory: Optional[Callable[[], Any]] = None


def set_client_factory(factory: Optional[Callable[[], Any]]) -> None:
    """Inject a custom client factory (used by tests with a fake client)."""
    global _factory
    _factory = factory


def get_client() -> Any:
    """Return an Anthropic SDK client.

    Raises :class:`AIUnavailable` when no key is configured — feature views
    translate this into a 503 with a clear message rather than 500-ing.
    """
    if _factory is not None:
        return _factory()

    api_key = getattr(settings, "ANTHROPIC_API_KEY", "") or os.getenv(
        "ANTHROPIC_API_KEY", ""
    )
    if not api_key:
        raise AIUnavailable(
            "ANTHROPIC_API_KEY is not configured. Set it in the backend .env "
            "to enable AI-assisted features."
        )

    # Imported lazily so the rest of the stack works even if `anthropic` isn't
    # installed in the runtime image (the tests use a fake client).
    import anthropic  # type: ignore

    return anthropic.Anthropic(api_key=api_key)


def get_model() -> str:
    return getattr(settings, "AI_MODEL", DEFAULT_MODEL)
