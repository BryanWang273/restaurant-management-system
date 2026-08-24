import json
from datetime import datetime, timedelta, timezone

import openai
from openai import OpenAI, OpenAIError
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.recipe_item import RecipeItem
from app.models.usage_event import UsageEvent
from app.schemas.ai_recommendation import InventoryRecommendationResponse
from app.services import inventory_service

LOOKBACK_DAYS = 30
MAX_TOOL_ITERATIONS = 6

SYSTEM_PROMPT = (
    "You are an inventory planning assistant for a restaurant. Use the "
    "available tools to inspect currently low-stock ingredients and how "
    "they're used on the menu, then recommend a reorder quantity and "
    "urgency (low, medium, or high) for each low-stock item. Ground every "
    "number and claim in the data returned by the tools — never invent "
    "consumption figures. Call list_low_stock_items first, then look up "
    "menu context for items whose reasoning would benefit from it before "
    "finalizing your recommendations."
)


class AIRecommendationError(Exception):
    pass


class AIRecommendationConfigError(AIRecommendationError):
    pass


class AIRecommendationUpstreamError(AIRecommendationError):
    pass


# ---------------------------------------------------------------------------
# Pure math — kept free of the DB session so it's trivially unit-testable.
# ---------------------------------------------------------------------------


def compute_daily_rate(total_used: float, lookback_days: int) -> float:
    if lookback_days <= 0:
        return 0.0
    return total_used / lookback_days


def compute_days_until_stockout(quantity_on_hand: float, daily_rate: float) -> float | None:
    if daily_rate <= 0:
        return None
    return round(quantity_on_hand / daily_rate, 1)


# ---------------------------------------------------------------------------
# DB-backed tool implementations. Each returns plain JSON-able data — the
# model only ever sees pre-aggregated numbers, never raw usage_events rows,
# so it can't get the arithmetic wrong.
# ---------------------------------------------------------------------------


def _usage_totals(db: Session, inventory_item_ids: list[int], lookback_days: int) -> dict[int, float]:
    if not inventory_item_ids:
        return {}
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    rows = db.execute(
        select(UsageEvent.inventory_item_id, func.sum(UsageEvent.quantity_used))
        .where(
            UsageEvent.inventory_item_id.in_(inventory_item_ids),
            UsageEvent.occurred_at >= cutoff,
        )
        .group_by(UsageEvent.inventory_item_id)
    ).all()
    return {item_id: float(total) for item_id, total in rows}


def _low_stock_snapshot(db: Session) -> list[dict]:
    items = inventory_service.list_low_stock(db)
    totals = _usage_totals(db, [item.id for item in items], LOOKBACK_DAYS)

    snapshot = []
    for item in items:
        daily_rate = compute_daily_rate(totals.get(item.id, 0.0), LOOKBACK_DAYS)
        snapshot.append(
            {
                "inventory_item_id": item.id,
                "name": item.name,
                "unit": item.unit,
                "quantity_on_hand": float(item.quantity_on_hand),
                "reorder_point": float(item.reorder_point),
                "daily_consumption_rate": round(daily_rate, 3),
                "days_until_stockout": compute_days_until_stockout(float(item.quantity_on_hand), daily_rate),
                "lookback_days": LOOKBACK_DAYS,
            }
        )
    return snapshot


def _menu_items_for_ingredient(db: Session, inventory_item_id: int) -> list[dict]:
    recipe_rows = list(
        db.scalars(
            select(RecipeItem)
            .options(selectinload(RecipeItem.menu_item), selectinload(RecipeItem.inventory_item))
            .where(RecipeItem.inventory_item_id == inventory_item_id)
        )
    )
    if not recipe_rows:
        return []

    menu_item_ids = [row.menu_item_id for row in recipe_rows]
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    order_totals = dict(
        db.execute(
            select(OrderItem.menu_item_id, func.sum(OrderItem.quantity))
            .join(Order, Order.id == OrderItem.order_id)
            .where(OrderItem.menu_item_id.in_(menu_item_ids), Order.created_at >= cutoff)
            .group_by(OrderItem.menu_item_id)
        ).all()
    )

    return [
        {
            "menu_item_id": row.menu_item_id,
            "menu_item_name": row.menu_item.name,
            "is_active": row.menu_item.is_active,
            "quantity_used_per_serving": float(row.quantity_used),
            "unit": row.inventory_item.unit,
            "servings_ordered_recently": int(order_totals.get(row.menu_item_id, 0)),
            "lookback_days": LOOKBACK_DAYS,
        }
        for row in recipe_rows
    ]


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------


class _GetMenuItemsForIngredientArgs(BaseModel):
    inventory_item_id: int


# Hand-written rather than generated via pydantic_function_tool: the SDK's
# strict-mode schema for a zero-argument tool includes `"required": []`,
# which — combined with empty `properties` — Groq's validator rejects as
# "'required' present but 'properties' is missing" (valid JSON Schema, but a
# bug in Groq's validator). `strict: true` is still required client-side by
# `.parse()`, and Groq separately requires `additionalProperties: false` on
# every object under strict mode — so the one combination that satisfies the
# SDK, OpenAI, and Groq is: strict, additionalProperties, no `required` key.
_LIST_LOW_STOCK_ITEMS_TOOL = {
    "type": "function",
    "function": {
        "name": "list_low_stock_items",
        "description": (
            "List every inventory item currently at or below its reorder "
            "point, including its current daily consumption rate and "
            "estimated days until stockout."
        ),
        "strict": True,
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}

TOOLS = [
    _LIST_LOW_STOCK_ITEMS_TOOL,
    openai.pydantic_function_tool(
        _GetMenuItemsForIngredientArgs,
        name="get_menu_items_for_ingredient",
        description=(
            "List the menu items that use a given inventory item as an "
            "ingredient, including how much is used per serving and how "
            "many servings were ordered recently."
        ),
    ),
]


def _execute_tool(db: Session, name: str, arguments: dict) -> object:
    if name == "list_low_stock_items":
        return _low_stock_snapshot(db)
    if name == "get_menu_items_for_ingredient":
        args = _GetMenuItemsForIngredientArgs.model_validate(arguments)
        return _menu_items_for_ingredient(db, args.inventory_item_id)
    raise AIRecommendationError(f"Model requested an unknown tool: {name}")


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------


def generate_recommendations(
    db: Session, client: OpenAI | None = None
) -> InventoryRecommendationResponse:
    if client is None:
        if not settings.openai_api_key:
            raise AIRecommendationConfigError(
                "OPENAI_API_KEY is not configured; AI inventory recommendations are unavailable."
            )
        client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Generate reorder recommendations for all currently low-stock inventory items.",
        },
    ]

    # Phase 1: data gathering. `tools` and `response_format` are requested
    # together on some providers (OpenAI), but Groq rejects that combination
    # outright ("json mode cannot be combined with tool/function calling"),
    # so gathering and finalizing have to be separate calls regardless.
    done_gathering = False
    for _ in range(MAX_TOOL_ITERATIONS):
        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=TOOLS,
            )
        except OpenAIError as exc:
            raise AIRecommendationUpstreamError(f"OpenAI request failed: {exc}") from exc

        message = response.choices[0].message

        if not message.tool_calls:
            done_gathering = True
            break

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ],
            }
        )
        for tool_call in message.tool_calls:
            arguments = json.loads(tool_call.function.arguments or "{}")
            try:
                result = _execute_tool(db, tool_call.function.name, arguments)
            except AIRecommendationError as exc:
                result = {"error": str(exc)}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

    if not done_gathering:
        raise AIRecommendationError(
            f"Exceeded {MAX_TOOL_ITERATIONS} tool-calling iterations without finishing data gathering."
        )

    # Phase 2: finalize. A separate, tools-free call so the structured
    # `response_format` request is never mixed with `tools` in the same call.
    messages.append(
        {
            "role": "user",
            "content": "Based on everything gathered above, output the final structured recommendations now.",
        }
    )
    try:
        final_response = client.chat.completions.parse(
            model=settings.openai_model,
            messages=messages,
            response_format=InventoryRecommendationResponse,
        )
    except OpenAIError as exc:
        raise AIRecommendationUpstreamError(f"OpenAI request failed: {exc}") from exc

    final_message = final_response.choices[0].message
    if final_message.parsed is None:
        raise AIRecommendationUpstreamError(
            "Model did not return structured recommendations on finalization."
        )
    return final_message.parsed
