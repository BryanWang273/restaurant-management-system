import json

import pytest

from app.models.inventory_item import InventoryItem
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.recipe_item import RecipeItem
from app.models.usage_event import UsageEvent
from app.schemas.ai_recommendation import InventoryRecommendation, InventoryRecommendationResponse
from app.services import ai_recommendation_service as svc


# ---------------------------------------------------------------------------
# Pure math
# ---------------------------------------------------------------------------


def test_compute_daily_rate_divides_total_by_lookback_window():
    assert svc.compute_daily_rate(30.0, 30) == 1.0
    assert svc.compute_daily_rate(0.0, 30) == 0.0


def test_compute_daily_rate_guards_against_zero_lookback():
    assert svc.compute_daily_rate(10.0, 0) == 0.0


def test_compute_days_until_stockout_with_positive_rate():
    assert svc.compute_days_until_stockout(10.0, 2.0) == 5.0


def test_compute_days_until_stockout_returns_none_with_no_usage():
    assert svc.compute_days_until_stockout(10.0, 0.0) is None


# ---------------------------------------------------------------------------
# DB-backed tool functions
# ---------------------------------------------------------------------------


def test_low_stock_snapshot_includes_consumption_rate(db_session):
    item = InventoryItem(name="Test Flour", unit="kg", quantity_on_hand=5, reorder_point=10)
    db_session.add(item)
    db_session.flush()

    order = Order(total_amount=0)
    db_session.add(order)
    db_session.flush()

    db_session.add(
        UsageEvent(inventory_item_id=item.id, order_id=order.id, quantity_used=15)
    )
    db_session.flush()

    snapshot = svc._low_stock_snapshot(db_session)
    by_name = {row["name"]: row for row in snapshot}

    assert "Test Flour" in by_name
    row = by_name["Test Flour"]
    assert row["inventory_item_id"] == item.id
    assert row["daily_consumption_rate"] == pytest.approx(15 / svc.LOOKBACK_DAYS)
    assert row["days_until_stockout"] == pytest.approx(
        5 / (15 / svc.LOOKBACK_DAYS), rel=1e-3
    )


def test_low_stock_snapshot_omits_healthy_items(db_session):
    item = InventoryItem(name="Test Sugar", unit="kg", quantity_on_hand=100, reorder_point=10)
    db_session.add(item)
    db_session.flush()

    snapshot = svc._low_stock_snapshot(db_session)
    assert "Test Sugar" not in {row["name"] for row in snapshot}


def test_menu_items_for_ingredient_returns_recent_order_volume(db_session):
    ingredient = InventoryItem(name="Test Cheese", unit="kg", quantity_on_hand=5, reorder_point=10)
    db_session.add(ingredient)
    db_session.flush()

    menu_item = MenuItem(name="Test Pizza", price=12.0, is_active=True)
    db_session.add(menu_item)
    db_session.flush()

    db_session.add(
        RecipeItem(menu_item_id=menu_item.id, inventory_item_id=ingredient.id, quantity_used=0.2)
    )
    order = Order(total_amount=12.0)
    db_session.add(order)
    db_session.flush()
    db_session.add(
        OrderItem(order_id=order.id, menu_item_id=menu_item.id, quantity=3, unit_price=12.0)
    )
    db_session.flush()

    results = svc._menu_items_for_ingredient(db_session, ingredient.id)

    assert len(results) == 1
    assert results[0]["menu_item_name"] == "Test Pizza"
    assert results[0]["unit"] == "kg"
    assert results[0]["quantity_used_per_serving"] == 0.2
    assert results[0]["servings_ordered_recently"] == 3


def test_menu_items_for_ingredient_returns_empty_for_unused_ingredient(db_session):
    ingredient = InventoryItem(name="Test Saffron", unit="g", quantity_on_hand=5, reorder_point=1)
    db_session.add(ingredient)
    db_session.flush()

    assert svc._menu_items_for_ingredient(db_session, ingredient.id) == []


# ---------------------------------------------------------------------------
# Agent loop, with a fake OpenAI client
# ---------------------------------------------------------------------------


class _FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, call_id, name, arguments):
        self.id = call_id
        self.function = _FakeFunction(name, arguments)


class _FakeMessage:
    def __init__(self, tool_calls=None, parsed=None, content=None):
        self.tool_calls = tool_calls
        self.parsed = parsed
        self.content = content


class _FakeResponse:
    def __init__(self, message):
        self.choices = [type("Choice", (), {"message": message})()]


class _FakeClient:
    """Mimics the two-phase call pattern the service now uses: `create()`
    during tool-gathering, `parse()` for the final structured response."""

    def __init__(self, create_responses, parse_response=None):
        self._create_responses = iter(create_responses)
        self._parse_response = parse_response
        self.calls = []

        class _Completions:
            def create(inner_self, **kwargs):
                self.calls.append(("create", kwargs))
                return next(self._create_responses)

            def parse(inner_self, **kwargs):
                self.calls.append(("parse", kwargs))
                if self._parse_response is None:
                    raise AssertionError("parse() called but no parse_response configured")
                return self._parse_response

        self.chat = type("Chat", (), {"completions": _Completions()})()


def test_generate_recommendations_executes_tool_call_then_returns_parsed(db_session):
    item = InventoryItem(name="Test Yeast", unit="kg", quantity_on_hand=1, reorder_point=5)
    db_session.add(item)
    db_session.flush()

    final = InventoryRecommendationResponse(
        recommendations=[
            InventoryRecommendation(
                inventory_item_id=item.id,
                name="Test Yeast",
                recommended_reorder_qty=10.0,
                urgency="high",
                reasoning="Below reorder point with active consumption.",
            )
        ]
    )

    create_responses = [
        _FakeResponse(
            _FakeMessage(
                tool_calls=[_FakeToolCall("call_1", "list_low_stock_items", "{}")]
            )
        ),
        _FakeResponse(_FakeMessage(content="Done gathering.")),
    ]
    parse_response = _FakeResponse(_FakeMessage(parsed=final))
    client = _FakeClient(create_responses, parse_response=parse_response)

    result = svc.generate_recommendations(db_session, client=client)

    assert result is final
    assert [kind for kind, _ in client.calls] == ["create", "create", "parse"]
    # the finalize call must carry the tool's result forward as a "tool" message
    finalize_messages = client.calls[-1][1]["messages"]
    tool_messages = [m for m in finalize_messages if m.get("role") == "tool"]
    assert len(tool_messages) == 1
    payload = json.loads(tool_messages[0]["content"])
    assert any(row["name"] == "Test Yeast" for row in payload)


def test_generate_recommendations_raises_without_api_key(db_session, monkeypatch):
    monkeypatch.setattr(svc.settings, "openai_api_key", None)

    with pytest.raises(svc.AIRecommendationConfigError):
        svc.generate_recommendations(db_session)


def test_generate_recommendations_raises_after_max_iterations(db_session):
    create_responses = [
        _FakeResponse(
            _FakeMessage(tool_calls=[_FakeToolCall(f"call_{i}", "list_low_stock_items", "{}")])
        )
        for i in range(svc.MAX_TOOL_ITERATIONS)
    ]
    client = _FakeClient(create_responses)

    with pytest.raises(svc.AIRecommendationError):
        svc.generate_recommendations(db_session, client=client)


def test_generate_recommendations_rejects_unknown_tool(db_session):
    final = InventoryRecommendationResponse(recommendations=[])
    create_responses = [
        _FakeResponse(
            _FakeMessage(tool_calls=[_FakeToolCall("call_1", "not_a_real_tool", "{}")])
        ),
        _FakeResponse(_FakeMessage(content="Done gathering.")),
    ]
    parse_response = _FakeResponse(_FakeMessage(parsed=final))
    client = _FakeClient(create_responses, parse_response=parse_response)

    result = svc.generate_recommendations(db_session, client=client)

    assert result is final
    finalize_messages = client.calls[-1][1]["messages"]
    tool_messages = [m for m in finalize_messages if m.get("role") == "tool"]
    assert "error" in json.loads(tool_messages[0]["content"])
