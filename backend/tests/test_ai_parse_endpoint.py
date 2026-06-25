"""End-to-end integration tests for /api/v1/ai/nutrition/parse/ using a
scripted fake Claude client. Verifies the HTTP contract, authentication,
and that the agent's tool calls actually create DB records.
"""
from __future__ import annotations

import pytest

from ai import client as ai_client
from nutrition.models import Meal, WaterLog
from tests.factories import FoodFactory


PARSE_URL = "/api/v1/ai/nutrition/parse/"


class _Block:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class _Usage:
    def __init__(self, **kw):
        self.input_tokens = kw.get("input_tokens", 0)
        self.output_tokens = kw.get("output_tokens", 0)
        self.cache_read_input_tokens = 0
        self.cache_creation_input_tokens = 0


class _Response:
    def __init__(self, content, stop_reason="end_turn", usage=None):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = usage or _Usage()


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)

        class _M:
            def __init__(self, parent):
                self.parent = parent

            def create(self, **kwargs):
                if not self.parent._responses:
                    raise AssertionError("FakeClient out of scripted responses")
                return self.parent._responses.pop(0)

        self.messages = _M(self)


@pytest.fixture
def scripted_client():
    """Install a scripted fake client and tear it down."""

    def _install(responses):
        ai_client.set_client_factory(lambda: FakeClient(responses))

    yield _install
    ai_client.set_client_factory(None)


@pytest.mark.django_db
class TestNutritionParseEndpoint:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.post(PARSE_URL, {"text": "two eggs"})
        assert res.status_code == 401

    def test_empty_text_returns_400(self, auth_client, scripted_client):
        # No client setup needed — the view rejects empty input before calling the runner.
        ai_client.set_client_factory(lambda: FakeClient([]))
        res = auth_client.post(PARSE_URL, {"text": "   "})
        assert res.status_code == 400

    def test_503_when_api_key_missing(self, auth_client, settings, monkeypatch):
        ai_client.set_client_factory(None)
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        res = auth_client.post(PARSE_URL, {"text": "two eggs"})
        assert res.status_code == 503

    def test_full_loop_creates_meal_and_water(self, auth_client, user, scripted_client):
        # Seed a food the agent can find.
        egg = FoodFactory(name="Boiled Egg", is_public=True)

        # Script: search_foods → create_meal → create_water_log → end_turn
        scripted_client([
            _Response(
                content=[
                    _Block(
                        type="tool_use",
                        id="t1",
                        name="search_foods",
                        input={"query": "egg"},
                    )
                ],
                stop_reason="tool_use",
            ),
            _Response(
                content=[
                    _Block(
                        type="tool_use",
                        id="t2",
                        name="create_meal",
                        input={
                            "meal_type": "breakfast",
                            "consumed_at": "2026-06-25T08:30:00+05:45",
                            "items": [{"food_id": egg.id, "servings": 2}],
                        },
                    )
                ],
                stop_reason="tool_use",
            ),
            _Response(
                content=[
                    _Block(
                        type="tool_use",
                        id="t3",
                        name="create_water_log",
                        input={
                            "amount_ml": 500,
                            "logged_at": "2026-06-25T08:31:00+05:45",
                        },
                    )
                ],
                stop_reason="tool_use",
            ),
            _Response(
                content=[
                    _Block(
                        type="text",
                        text="Logged a breakfast with 2 eggs and 500 ml of water.",
                    )
                ],
                stop_reason="end_turn",
            ),
        ])

        res = auth_client.post(
            PARSE_URL, {"text": "two boiled eggs and 500 ml of water"}, format="json"
        )
        assert res.status_code == 200, res.data
        body = res.data
        assert body["status"] == "completed"
        assert "breakfast" in body["summary"].lower()
        assert len(body["created"]["meal_ids"]) == 1
        assert len(body["created"]["water_log_ids"]) == 1

        # DB side-effects landed
        assert Meal.objects.filter(user=user).count() == 1
        assert WaterLog.objects.filter(user=user).count() == 1
        meal = Meal.objects.get(user=user)
        assert meal.items.first().food_id == egg.id

    def test_agent_failure_surfaces_as_502_with_friendly_detail(
        self, auth_client, scripted_client
    ):
        # Fake client that raises an Anthropic-style error mid-loop.
        class BoomClient:
            class _M:
                def create(self, **_):
                    raise RuntimeError(
                        "BadRequestError: Your credit balance is too low"
                    )

            messages = _M()

        ai_client.set_client_factory(lambda: BoomClient())
        res = auth_client.post(PARSE_URL, {"text": "two eggs"}, format="json")
        assert res.status_code == 502, res.data
        assert "credit" in res.data["detail"].lower()
        assert "session_id" in res.data

    def test_only_water_no_meal(self, auth_client, user, scripted_client):
        scripted_client([
            _Response(
                content=[
                    _Block(
                        type="tool_use",
                        id="t1",
                        name="create_water_log",
                        input={
                            "amount_ml": 250,
                            "logged_at": "2026-06-25T15:00:00+05:45",
                        },
                    )
                ],
                stop_reason="tool_use",
            ),
            _Response(
                content=[_Block(type="text", text="Logged 250 ml of water.")],
                stop_reason="end_turn",
            ),
        ])

        res = auth_client.post(PARSE_URL, {"text": "a glass of water"}, format="json")
        assert res.status_code == 200
        assert res.data["created"]["meal_ids"] == []
        assert len(res.data["created"]["water_log_ids"]) == 1
        assert WaterLog.objects.filter(user=user, amount_ml=250).exists()
