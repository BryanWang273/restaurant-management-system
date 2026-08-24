from pydantic import BaseModel, ConfigDict


class RecipeItemBase(BaseModel):
    inventory_item_id: int
    quantity_used: float


class RecipeItemCreate(RecipeItemBase):
    pass


class RecipeItemRead(RecipeItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
