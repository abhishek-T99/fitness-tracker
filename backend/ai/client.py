"""LLM client factory with multi-provider support.

Two providers are supported out of the box:

* ``gemini`` — Google's Gemini Flash via the ``google-genai`` SDK
  (generous free tier). This is the default.
* ``anthropic`` — Claude via the ``anthropic`` SDK (paid).

The runner only ever sees an Anthropic-shaped ``client.messages.create(...)``
surface. The Gemini adapter (``ai/providers/gemini.py``) translates Google's
SDK into that shape so we don't need a provider-agnostic interface in the
runner itself.

A test fake can be injected via :func:`set_client_factory`.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Optional

from django.conf import settings


class AIUnavailable(Exception):
    """Raised when no provider can be used (missing key, unknown provider)."""


DEFAULT_PROVIDER = "gemini"
DEFAULT_MODELS = {
    "gemini": "gemini-2.0-flash",
    "anthropic": "claude-sonnet-4-6",
}


_factory: Optional[Callable[[], Any]] = None


def set_client_factory(factory: Optional[Callable[[], Any]]) -> None:
    """Inject a custom client factory (used by tests with a fake client)."""
    global _factory
    _factory = factory


def get_provider() -> str:
    return (
        getattr(settings, "AI_PROVIDER", "")
        or os.getenv("AI_PROVIDER", "")
        or DEFAULT_PROVIDER
    ).lower()


def get_model() -> str:
    explicit = getattr(settings, "AI_MODEL", "") or os.getenv("AI_MODEL", "")
    if explicit:
        return explicit
    return DEFAULT_MODELS.get(get_provider(), DEFAULT_MODELS[DEFAULT_PROVIDER])


def get_client() -> Any:
    """Return a Messages-shaped client for the configured provider.

    Raises :class:`AIUnavailable` when the provider's key is missing — the
    feature views translate this into a 503 with a clear message rather
    than 500-ing.
    """
    if _factory is not None:
        return _factory()

    provider = get_provider()

    if provider == "gemini":
        api_key = getattr(settings, "GEMINI_API_KEY", "") or os.getenv(
            "GEMINI_API_KEY", ""
        )
        if not api_key:
            raise AIUnavailable(
                "GEMINI_API_KEY is not configured. Set it in the backend .env. "
                "Get a free key at https://aistudio.google.com/app/apikey."
            )
        from .providers.gemini import GeminiAdapter

        return GeminiAdapter(api_key=api_key)

    if provider == "anthropic":
        api_key = getattr(settings, "ANTHROPIC_API_KEY", "") or os.getenv(
            "ANTHROPIC_API_KEY", ""
        )
        if not api_key:
            raise AIUnavailable(
                "ANTHROPIC_API_KEY is not configured. Set it in the backend .env "
                "or switch to a free provider with AI_PROVIDER=gemini."
            )
        import anthropic  # type: ignore

        return anthropic.Anthropic(api_key=api_key)

    raise AIUnavailable(
        f"Unknown AI provider: {provider!r}. Set AI_PROVIDER to 'gemini' or 'anthropic'."
    )
