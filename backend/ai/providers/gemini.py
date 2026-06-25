"""Gemini Flash provider — exposes an Anthropic-shaped Messages API.

The runner is written against Anthropic's ``client.messages.create(...)``
shape (content blocks of type ``text`` / ``tool_use``, a ``stop_reason``
field, a ``usage`` object with input/output token counts). This adapter
translates the google-genai SDK into that shape so the runner stays
provider-agnostic.

Why translate here instead of teaching the runner two dialects?
The translation is mechanical and small (tools, messages, response).
Putting it behind an adapter keeps the runner — the most subtle bit of
the AI scaffold — single-target. Adding a third provider later means a
new file under ``ai/providers/``, not surgery in ``runner.py``.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# ── Anthropic-shaped response objects the runner consumes ───────────────────


@dataclass
class _TextBlock:
    text: str
    type: str = "text"


@dataclass
class _ToolUseBlock:
    id: str
    name: str
    input: Dict[str, Any]
    type: str = "tool_use"


@dataclass
class _Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


@dataclass
class _Response:
    content: List[Any]
    stop_reason: str
    usage: _Usage = field(default_factory=_Usage)


# ── Adapter ─────────────────────────────────────────────────────────────────


class _MessagesShim:
    """Mimics the SDK's ``client.messages`` namespace."""

    def __init__(self, parent: "GeminiAdapter"):
        self._parent = parent

    def create(self, *, model, max_tokens, system, tools, messages, **_kwargs):
        return self._parent._create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=messages,
        )


class GeminiAdapter:
    """Anthropic-shaped wrapper over the google-genai SDK.

    Tool calls coming back from Gemini are ``function_call`` parts with no
    ID — we mint a synthetic ``toolu_<uuid>`` so the runner's audit log and
    tool-result echo path work unchanged. The name→id map is kept on the
    adapter instance so the follow-up ``tool_result`` can re-attach the
    function name when echoed back as a ``function_response``.
    """

    def __init__(self, api_key: str):
        # Imported lazily so the rest of the stack works even if the package
        # isn't installed (tests inject a fake client via set_client_factory).
        from google import genai  # type: ignore

        self._genai = genai
        self._client = genai.Client(api_key=api_key)
        self.messages = _MessagesShim(self)
        # tool_use_id → function_name, populated as Gemini emits function calls
        # and consumed when we translate tool_result blocks back to the API.
        self._call_name_by_id: Dict[str, str] = {}

    # ── public surface ─────────────────────────────────────────────────────

    def _create(self, *, model, max_tokens, system, tools, messages):
        from google.genai import types  # type: ignore

        system_text = "\n\n".join(
            b["text"] for b in (system or []) if isinstance(b, dict) and b.get("type") == "text"
        )
        gemini_tools = self._translate_tools(tools)
        contents = self._translate_messages(messages)

        config_kwargs: Dict[str, Any] = {"max_output_tokens": max_tokens}
        if system_text:
            config_kwargs["system_instruction"] = system_text
        if gemini_tools:
            config_kwargs["tools"] = gemini_tools

        config = types.GenerateContentConfig(**config_kwargs)
        response = self._client.models.generate_content(
            model=model, contents=contents, config=config
        )
        return self._translate_response(response)

    # ── translation helpers ────────────────────────────────────────────────

    def _translate_tools(self, anthropic_tools):
        if not anthropic_tools:
            return None
        from google.genai import types  # type: ignore

        decls = []
        for t in anthropic_tools:
            decls.append(
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=_jsonschema_to_gemini(t["input_schema"]),
                )
            )
        return [types.Tool(function_declarations=decls)]

    def _translate_messages(self, anthropic_messages):
        from google.genai import types  # type: ignore

        out = []
        for msg in anthropic_messages:
            role = msg["role"]
            gemini_role = "model" if role == "assistant" else "user"
            content = msg["content"]

            if isinstance(content, str):
                out.append(
                    types.Content(
                        role=gemini_role, parts=[types.Part.from_text(text=content)]
                    )
                )
                continue

            parts = []
            for block in content:
                btype = block.get("type") if isinstance(block, dict) else None
                if btype == "text":
                    parts.append(types.Part.from_text(text=block["text"]))
                elif btype == "tool_use":
                    parts.append(
                        types.Part(
                            function_call=types.FunctionCall(
                                name=block["name"], args=block.get("input") or {}
                            )
                        )
                    )
                elif btype == "tool_result":
                    tool_use_id = block.get("tool_use_id", "")
                    name = self._call_name_by_id.get(tool_use_id) or "unknown"
                    raw = block.get("content", "")
                    response_obj: Any
                    if isinstance(raw, str):
                        try:
                            response_obj = json.loads(raw)
                        except (TypeError, ValueError):
                            response_obj = {"result": raw}
                    else:
                        response_obj = raw
                    if not isinstance(response_obj, dict):
                        response_obj = {"result": response_obj}
                    parts.append(
                        types.Part.from_function_response(
                            name=name, response=response_obj
                        )
                    )
            if parts:
                out.append(types.Content(role=gemini_role, parts=parts))
        return out

    def _translate_response(self, gemini_response) -> _Response:
        candidates = getattr(gemini_response, "candidates", None) or []
        if not candidates:
            return _Response(content=[], stop_reason="end_turn", usage=_extract_usage(gemini_response))

        candidate = candidates[0]
        gcontent = getattr(candidate, "content", None)
        parts = getattr(gcontent, "parts", None) or []

        blocks: List[Any] = []
        has_function_call = False
        for part in parts:
            fc = getattr(part, "function_call", None)
            if fc and getattr(fc, "name", None):
                tool_id = f"toolu_{uuid.uuid4().hex[:16]}"
                self._call_name_by_id[tool_id] = fc.name
                args = _proto_to_dict(getattr(fc, "args", None))
                blocks.append(_ToolUseBlock(id=tool_id, name=fc.name, input=args))
                has_function_call = True
                continue
            text = getattr(part, "text", None)
            if text:
                blocks.append(_TextBlock(text=text))

        # Gemini reports finish_reason=STOP even when emitting a function call,
        # so we infer stop_reason from the content shape instead.
        stop_reason = "tool_use" if has_function_call else "end_turn"

        return _Response(
            content=blocks,
            stop_reason=stop_reason,
            usage=_extract_usage(gemini_response),
        )


# ── helpers ─────────────────────────────────────────────────────────────────


def _extract_usage(gemini_response) -> _Usage:
    meta = getattr(gemini_response, "usage_metadata", None)
    if meta is None:
        return _Usage()
    return _Usage(
        input_tokens=int(getattr(meta, "prompt_token_count", 0) or 0),
        output_tokens=int(getattr(meta, "candidates_token_count", 0) or 0),
        cache_read_input_tokens=int(getattr(meta, "cached_content_token_count", 0) or 0),
    )


def _proto_to_dict(value) -> Dict[str, Any]:
    """Best-effort: turn google-genai's MapComposite / Struct into a plain dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {k: _maybe_unwrap(v) for k, v in value.items()}
    try:
        return {k: _maybe_unwrap(v) for k, v in dict(value).items()}
    except Exception:
        return {}


def _maybe_unwrap(v):
    # Nested proto Map / RepeatedComposite need the same treatment.
    if isinstance(v, dict):
        return {k: _maybe_unwrap(vv) for k, vv in v.items()}
    if isinstance(v, (list, tuple)):
        return [_maybe_unwrap(x) for x in v]
    try:
        # protobuf Struct / MapComposite are dict-like — duck-type via items()
        return {k: _maybe_unwrap(vv) for k, vv in v.items()}
    except Exception:
        pass
    try:
        # Repeated proto fields are list-like via iter()
        if not isinstance(v, (str, bytes)) and hasattr(v, "__iter__"):
            return [_maybe_unwrap(x) for x in v]
    except Exception:
        pass
    return v


def _jsonschema_to_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Strip JSON Schema fields Gemini's parameter schema rejects.

    Gemini accepts an OpenAPI-3 subset. Most of our schemas are simple
    (type/properties/required/description/enum/items), but the no-arg
    ``get_current_datetime`` tool has ``"required": []`` which Gemini's
    validator dislikes on a parameterless schema. Strip a few known
    irritants here without trying to be exhaustive.
    """
    if not isinstance(schema, dict):
        return schema
    cleaned: Dict[str, Any] = {}
    for k, v in schema.items():
        if k == "additionalProperties":
            continue  # not supported
        if k == "required" and not v:
            continue  # empty required list trips the validator
        if k == "properties" and isinstance(v, dict):
            cleaned[k] = {pk: _jsonschema_to_gemini(pv) for pk, pv in v.items()}
        elif k == "items" and isinstance(v, dict):
            cleaned[k] = _jsonschema_to_gemini(v)
        else:
            cleaned[k] = v
    # Gemini requires a `type` at every schema node — default to object when missing.
    if "type" not in cleaned and "properties" in cleaned:
        cleaned["type"] = "object"
    return cleaned
