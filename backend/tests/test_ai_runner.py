"""Runner tests using a scripted fake Claude client — no network calls.

The fake client is driven by a list of pre-canned ``Message`` responses.
Each test scripts the exact sequence of tool_use → end_turn the runner
should walk through, then asserts on the audit log it built.
"""
from __future__ import annotations

import pytest

from ai import client as ai_client
from ai.models import AgentSession, AgentStep
from ai.registry import REGISTRY, Tool
from ai.runner import run_agent


# ── Fake Claude SDK shims ───────────────────────────────────────────────────


class _Block:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class _Usage:
    def __init__(self, **kw):
        self.input_tokens = kw.get("input_tokens", 0)
        self.output_tokens = kw.get("output_tokens", 0)
        self.cache_read_input_tokens = kw.get("cache_read_input_tokens", 0)
        self.cache_creation_input_tokens = kw.get("cache_creation_input_tokens", 0)


class _Response:
    def __init__(self, content, stop_reason="end_turn", usage=None):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = usage or _Usage()


class FakeClient:
    """Replays a scripted sequence of model responses."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

        class _Messages:
            def __init__(self, parent):
                self._parent = parent

            def create(self, **kwargs):
                self._parent.calls.append(kwargs)
                if not self._parent._responses:
                    raise AssertionError("FakeClient ran out of scripted responses")
                return self._parent._responses.pop(0)

        self.messages = _Messages(self)


@pytest.fixture
def fake_client_factory():
    """Inject a FakeClient script and tear it down after the test."""

    def _factory(responses):
        client = FakeClient(responses)
        ai_client.set_client_factory(lambda: client)
        return client

    yield _factory
    ai_client.set_client_factory(None)


@pytest.fixture
def echo_tool():
    """Register a one-off tool that records calls into a shared list."""
    calls: list = []

    def handler(*, user, **kw):
        calls.append({"user_id": user.id, **kw})
        return {"echoed": kw}

    REGISTRY.register(
        Tool(
            name="_echo_test",
            description="Echo input for runner tests.",
            input_schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
            handler=handler,
            kind="read",
        )
    )
    yield calls
    REGISTRY.tools.pop("_echo_test", None)


# ── Tests ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRunnerHappyPath:
    def test_end_turn_no_tools_records_session(self, user, fake_client_factory):
        fake_client_factory([
            _Response(
                content=[_Block(type="text", text="All done.")],
                stop_reason="end_turn",
                usage=_Usage(input_tokens=10, output_tokens=5),
            )
        ])

        result = run_agent(
            user=user,
            feature="test_feature",
            system_prompt="You are a test.",
            user_message="hi",
            tool_names=[],
        )

        assert result.status == AgentSession.Status.COMPLETED
        assert result.summary == "All done."
        session = AgentSession.objects.get(pk=result.session_id)
        assert session.tokens_in == 10
        assert session.tokens_out == 5
        # One model_call step recorded
        assert session.steps.count() == 1
        assert session.steps.first().kind == AgentStep.Kind.MODEL_CALL

    def test_tool_use_then_end_turn(self, user, fake_client_factory, echo_tool):
        fake_client_factory([
            # Turn 1: model asks to call the tool
            _Response(
                content=[
                    _Block(
                        type="tool_use",
                        id="toolu_1",
                        name="_echo_test",
                        input={"message": "hello"},
                    )
                ],
                stop_reason="tool_use",
                usage=_Usage(input_tokens=20, output_tokens=10),
            ),
            # Turn 2: model wraps up after seeing the result
            _Response(
                content=[_Block(type="text", text="Echoed.")],
                stop_reason="end_turn",
                usage=_Usage(input_tokens=15, output_tokens=3),
            ),
        ])

        result = run_agent(
            user=user,
            feature="test_feature",
            system_prompt="Use the echo tool.",
            user_message="say hello",
            tool_names=["_echo_test"],
        )

        assert result.status == AgentSession.Status.COMPLETED
        assert result.summary == "Echoed."
        # Tool was actually called with the right input and user
        assert echo_tool == [{"user_id": user.id, "message": "hello"}]
        # Audit log has model_call, tool_call, model_call
        kinds = list(
            AgentStep.objects.filter(session_id=result.session_id)
            .order_by("ordinal")
            .values_list("kind", flat=True)
        )
        assert kinds == [
            AgentStep.Kind.MODEL_CALL,
            AgentStep.Kind.TOOL_CALL,
            AgentStep.Kind.MODEL_CALL,
        ]


@pytest.mark.django_db
class TestRunnerErrorPaths:
    def test_tool_handler_exception_is_fed_back_to_model(
        self, user, fake_client_factory
    ):
        def broken_handler(*, user, **kw):
            raise RuntimeError("kaboom")

        REGISTRY.register(
            Tool(
                name="_broken",
                description="Always raises.",
                input_schema={"type": "object", "properties": {}, "required": []},
                handler=broken_handler,
            )
        )
        try:
            fake_client_factory([
                _Response(
                    content=[_Block(type="tool_use", id="toolu_x", name="_broken", input={})],
                    stop_reason="tool_use",
                ),
                _Response(
                    content=[_Block(type="text", text="Recovered.")],
                    stop_reason="end_turn",
                ),
            ])

            result = run_agent(
                user=user,
                feature="test_feature",
                system_prompt="x",
                user_message="x",
                tool_names=["_broken"],
            )

            assert result.status == AgentSession.Status.COMPLETED
            tool_step = AgentStep.objects.get(
                session_id=result.session_id, kind=AgentStep.Kind.TOOL_CALL
            )
            assert tool_step.is_error is True
            assert "kaboom" in tool_step.payload["output"]["error"]
        finally:
            REGISTRY.tools.pop("_broken", None)

    def test_unavailable_when_no_api_key(self, user, settings, monkeypatch):
        # Ensure no factory is set and no key is configured for either provider
        ai_client.set_client_factory(None)
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from ai.client import AIUnavailable

        with pytest.raises(AIUnavailable):
            run_agent(
                user=user,
                feature="test_feature",
                system_prompt="x",
                user_message="x",
                tool_names=[],
            )
