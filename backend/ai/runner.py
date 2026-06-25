"""Generic tool-use loop.

Owns the conversation with Claude: builds the request, calls the API,
dispatches tool_use blocks to registered handlers, feeds tool_results back,
and persists every step to AgentSession / AgentStep for audit.

The loop is intentionally feature-agnostic. Each feature view picks the
system prompt and tool whitelist, then calls ``run_agent``.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from django.utils import timezone

from .budgets import BudgetExceeded, check as budget_check, record as budget_record
from .client import AIUnavailable, get_client, get_model
from .context import build as build_context_pack, render_system_block
from .models import AgentSession, AgentStep
from .registry import REGISTRY

logger = logging.getLogger(__name__)


# Per-feature defaults; features can override.
DEFAULT_MAX_TOKENS = 4096
DEFAULT_MAX_STEPS = 10


@dataclass
class AgentResult:
    session_id: int
    status: str
    summary: str
    structured: Dict[str, Any] = field(default_factory=dict)
    tokens_in: int = 0
    tokens_out: int = 0


def _serialise_block(block: Any) -> Dict[str, Any]:
    """Best-effort dict view of an Anthropic SDK content block for the audit log."""
    if isinstance(block, dict):
        return block
    payload = {"type": getattr(block, "type", "unknown")}
    for attr in ("text", "name", "id", "input"):
        if hasattr(block, attr):
            payload[attr] = getattr(block, attr)
    return payload


def _assistant_content_for_history(content_blocks: List[Any]) -> List[Dict[str, Any]]:
    """Convert the SDK's response content into the dict shape needed to echo it back."""
    out: List[Dict[str, Any]] = []
    for block in content_blocks:
        btype = getattr(block, "type", None) if not isinstance(block, dict) else block.get("type")
        if btype == "text":
            text = block.text if not isinstance(block, dict) else block["text"]
            out.append({"type": "text", "text": text})
        elif btype == "tool_use":
            if isinstance(block, dict):
                out.append({
                    "type": "tool_use",
                    "id": block["id"],
                    "name": block["name"],
                    "input": block["input"],
                })
            else:
                out.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        # thinking and other block types are ignored for follow-up history
    return out


def run_agent(
    *,
    user,
    feature: str,
    system_prompt: str,
    user_message: str,
    tool_names: List[str],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> AgentResult:
    """Run a tool-using agent turn end-to-end.

    Raises :class:`AIUnavailable` if the API key isn't configured and
    :class:`BudgetExceeded` if the user is over their daily token cap. All
    other failures are recorded on the AgentSession and returned via the
    ``status`` field instead of raising.
    """
    budget_check(user.id)
    client = get_client()  # may raise AIUnavailable

    session = AgentSession.objects.create(
        user=user,
        feature=feature,
        input_text=user_message,
        model=get_model(),
        status=AgentSession.Status.PENDING,
    )
    ordinal = 0

    # ── Build the static parts of the request ────────────────────────────────
    context_pack = build_context_pack(user)
    system_blocks = [
        # Frozen instruction block — stable across requests for the same feature.
        {"type": "text", "text": system_prompt},
        # User context — refreshed per request but identical bytes during a
        # 5-minute window for the same user (modulo today's nutrition deltas).
        render_system_block(context_pack),
    ]
    # Mark the last system block cacheable so tools + system + user context
    # all get cached together. See shared/prompt-caching.md.
    system_blocks[-1]["cache_control"] = {"type": "ephemeral"}

    tools = REGISTRY.schemas(tool_names)
    messages: List[Dict[str, Any]] = [{"role": "user", "content": user_message}]

    final_text = ""
    structured: Dict[str, Any] = {
        "created_meal_ids": [],
        "created_water_log_ids": [],
        "created_food_ids": [],
    }
    total_in = 0
    total_out = 0
    cache_read = 0
    cache_write = 0

    try:
        for step in range(max_steps):
            ordinal += 1
            t0 = time.monotonic()
            response = client.messages.create(
                model=get_model(),
                max_tokens=max_tokens,
                system=system_blocks,
                tools=tools,
                messages=messages,
            )
            elapsed = time.monotonic() - t0

            usage = getattr(response, "usage", None)
            if usage is not None:
                total_in += getattr(usage, "input_tokens", 0) or 0
                total_out += getattr(usage, "output_tokens", 0) or 0
                cache_read += getattr(usage, "cache_read_input_tokens", 0) or 0
                cache_write += getattr(usage, "cache_creation_input_tokens", 0) or 0

            AgentStep.objects.create(
                session=session,
                ordinal=ordinal,
                kind=AgentStep.Kind.MODEL_CALL,
                name=get_model(),
                payload={
                    "stop_reason": getattr(response, "stop_reason", None),
                    "elapsed_seconds": round(elapsed, 3),
                    "content": [_serialise_block(b) for b in response.content],
                },
            )

            # Capture any text the model emitted this turn — we'll use the
            # final iteration's text as the user-visible summary.
            for block in response.content:
                btype = getattr(block, "type", None)
                if btype == "text":
                    final_text = block.text

            if getattr(response, "stop_reason", None) == "end_turn":
                break

            tool_use_blocks = [
                b for b in response.content if getattr(b, "type", None) == "tool_use"
            ]
            if not tool_use_blocks:
                # Defensive: stop_reason wasn't end_turn but no tools were
                # requested either. Bail rather than spin.
                break

            messages.append(
                {"role": "assistant", "content": _assistant_content_for_history(response.content)}
            )

            tool_results: List[Dict[str, Any]] = []
            for block in tool_use_blocks:
                ordinal += 1
                tool_name = block.name
                tool_input = block.input or {}
                try:
                    tool = REGISTRY.get(tool_name)
                    raw_result = tool.handler(user=user, **tool_input)
                    is_error = False
                except Exception as exc:  # noqa: BLE001 — feed error to the model
                    raw_result = {"error": str(exc), "type": type(exc).__name__}
                    is_error = True
                    logger.warning("Tool %s failed: %s", tool_name, exc)

                _record_created_ids(tool_name, raw_result, structured)

                AgentStep.objects.create(
                    session=session,
                    ordinal=ordinal,
                    kind=AgentStep.Kind.TOOL_CALL,
                    name=tool_name,
                    is_error=is_error,
                    payload={"input": tool_input, "output": raw_result},
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(raw_result, default=str),
                    "is_error": is_error,
                })

            messages.append({"role": "user", "content": tool_results})

        session.status = AgentSession.Status.COMPLETED
    except BudgetExceeded:
        session.status = AgentSession.Status.BUDGET_EXCEEDED
        session.error = "Daily token budget exceeded"
        raise
    except Exception as exc:  # noqa: BLE001
        session.status = AgentSession.Status.FAILED
        session.error = f"{type(exc).__name__}: {exc}"
        logger.exception("Agent run failed for feature=%s user=%s", feature, user.id)
    finally:
        session.final_output = final_text
        session.tokens_in = total_in
        session.tokens_out = total_out
        session.cache_read_tokens = cache_read
        session.cache_write_tokens = cache_write
        session.completed_at = timezone.now()
        session.save()
        budget_record(user.id, total_in + total_out)

    return AgentResult(
        session_id=session.pk,
        status=session.status,
        summary=final_text,
        structured=structured,
        tokens_in=total_in,
        tokens_out=total_out,
    )


def _record_created_ids(tool_name: str, result: Any, structured: Dict[str, Any]) -> None:
    """Track IDs of records the agent created so the frontend can offer Undo."""
    if not isinstance(result, dict):
        return
    if tool_name == "create_meal" and "id" in result:
        structured["created_meal_ids"].append(result["id"])
    elif tool_name == "create_water_log" and "id" in result:
        structured["created_water_log_ids"].append(result["id"])
    elif tool_name == "create_food" and "id" in result:
        structured["created_food_ids"].append(result["id"])
