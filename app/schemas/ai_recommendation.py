from typing import Literal

from pydantic import BaseModel


class InventoryRecommendation(BaseModel):
    inventory_item_id: int
    name: str
    recommended_reorder_qty: float
    urgency: Literal["low", "medium", "high"]
    reasoning: str


class InventoryRecommendationResponse(BaseModel):
    recommendations: list[InventoryRecommendation]
