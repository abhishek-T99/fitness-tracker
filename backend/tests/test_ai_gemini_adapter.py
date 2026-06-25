"""Unit tests for the Gemini → Anthropic translation in the adapter.

These tests stub the underlying google-genai client to keep them
offline and deterministic, then exercise:

* tools  → FunctionDeclaration
* messages → Content/Part (incl. tool_use + tool_result round-trip)
* response → Anthropic-shaped content blocks + stop_reason

This is the layer the runner depends on. The runner has its own tests
against an Anthropic-shaped fake client; this file covers the seam
between the two.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ai.providers import gemini as gemini_mod


# ── Fixture: an adapter whose underlying SDK is a MagicMock ─────────────────


@pytest.fixture
def adapter():
    """Build an adapter without touching the real google-genai client."""
    a = gemini_mod.GeminiAdapter.__new__(gemini_mod.GeminiAdapter)
    a._client = MagicMock()
    a._client.models = MagicMock()
    a._call_name_by_id = {}
    a.messages = gemini_mod._MessagesShim(a)
    return a


# ── Schema cleaning ─────────────────────────────────────────────────────────


class TestJsonSchemaToGemini:
    def test_strips_empty_required(self):
        cleaned = gemini_mod._jsonschema_to_gemini(
            {"type": "object", "properties": {}, "required": []}
        )
        assert "required" not in cleaned

    def test_strips_additional_properties(self):
        cleaned = gemini_mod._jsonschema_to_gemini(
            {"type": "object", "additionalProperties": False, "properties": {}}
        )
        assert "additionalProperties" not in cleaned

    def test_recurses_into_properties_and_items(self):
        cleaned = gemini_mod._jsonschema_to_gemini(
            {
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "object", "additionalProperties": False},
                    }
                },
                "required": ["tags"],
            }
        )
        assert "additionalProperties" not in cleaned["properties"]["tags"]["items"]
        assert cleaned["required"] == ["tags"]


# ── Response translation ────────────────────────────────────────────────────


class TestTranslateResponse:
    def _resp(self, parts, finish_reason="STOP", usage=(10, 5, 0)):
        candidate = SimpleNamespace(
            content=SimpleNamespace(parts=parts), finish_reason=finish_reason
        )
        meta = SimpleNamespace(
            prompt_token_count=usage[0],
            candidates_token_count=usage[1],
            cached_content_token_count=usage[2],
        )
        return SimpleNamespace(candidates=[candidate], usage_metadata=meta)

    def test_text_only_response_maps_to_end_turn(self, adapter):
        result = adapter._translate_response(
            self._resp([SimpleNamespace(text="hello there", function_call=None)])
        )
        assert result.stop_reason == "end_turn"
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert result.content[0].text == "hello there"
        assert result.usage.input_tokens == 10
        assert result.usage.output_tokens == 5

    def test_function_call_maps_to_tool_use_with_synthesized_id(self, adapter):
        fc = SimpleNamespace(name="search_foods", args={"query": "egg"})
        result = adapter._translate_response(
            self._resp([SimpleNamespace(text=None, function_call=fc)])
        )
        assert result.stop_reason == "tool_use"
        block = result.content[0]
        assert block.type == "tool_use"
        assert block.name == "search_foods"
        assert block.input == {"query": "egg"}
        # Synthetic ID is recorded so a follow-up tool_result can resolve the name
        assert block.id in adapter._call_name_by_id
        assert adapter._call_name_by_id[block.id] == "search_foods"

    def test_empty_candidates_returns_empty_end_turn(self, adapter):
        empty = SimpleNamespace(candidates=[], usage_metadata=None)
        result = adapter._translate_response(empty)
        assert result.content == []
        assert result.stop_reason == "end_turn"
        assert result.usage.input_tokens == 0


# ── Message translation (tool_use / tool_result round-trip) ─────────────────


class TestTranslateMessages:
    def test_user_text_message(self, adapter):
        out = adapter._translate_messages([{"role": "user", "content": "hi"}])
        assert len(out) == 1
        assert out[0].role == "user"
        assert len(out[0].parts) == 1

    def test_assistant_tool_use_then_user_tool_result_round_trip(self, adapter):
        # Pretend the adapter just emitted a tool_use with id toolu_abc.
        adapter._call_name_by_id["toolu_abc"] = "search_foods"

        msgs = [
            {"role": "user", "content": "find eggs"},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_abc",
                        "name": "search_foods",
                        "input": {"query": "egg"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_abc",
                        "content": '{"results": [{"id": 1, "name": "Boiled Egg"}]}',
                    }
                ],
            },
        ]
        out = adapter._translate_messages(msgs)
        assert [c.role for c in out] == ["user", "model", "user"]

        # The tool_result was parsed back into a dict for from_function_response.
        # We can't easily inspect the proto Part fields, but we can confirm one
        # was emitted in the third Content.
        assert len(out[2].parts) == 1

    def test_unknown_tool_result_id_falls_back_to_unknown_name(self, adapter):
        # No prior tool_use registered.
        out = adapter._translate_messages(
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_missing",
                            "content": '{"x": 1}',
                        }
                    ],
                }
            ]
        )
        # Just check it doesn't raise — adapter inserts a Part with name="unknown".
        assert len(out) == 1


# ── End-to-end: adapter.messages.create wiring ──────────────────────────────


class TestAdapterCreate:
    def test_create_calls_underlying_client_and_translates(self, adapter):
        fake_response = SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[SimpleNamespace(text="done", function_call=None)]
                    ),
                    finish_reason="STOP",
                )
            ],
            usage_metadata=SimpleNamespace(
                prompt_token_count=7,
                candidates_token_count=2,
                cached_content_token_count=0,
            ),
        )
        adapter._client.models.generate_content.return_value = fake_response

        result = adapter.messages.create(
            model="gemini-2.0-flash",
            max_tokens=1024,
            system=[{"type": "text", "text": "you are helpful"}],
            tools=[],
            messages=[{"role": "user", "content": "hello"}],
        )

        assert result.stop_reason == "end_turn"
        assert result.content[0].text == "done"
        assert result.usage.input_tokens == 7

        # Verify we called the SDK with the right model name.
        call_kwargs = adapter._client.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == "gemini-2.0-flash"
