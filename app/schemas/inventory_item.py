from pydantic import BaseModel, ConfigDict


class InventoryItemBase(BaseModel):
    name: str
    unit: str
    quantity_on_hand: float = 0
    reorder_point: float = 0


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    quantity_on_hand: float | None = None
    reorder_point: float | None = None


class InventoryItemRead(InventoryItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
