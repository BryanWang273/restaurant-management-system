from pydantic import BaseModel, ConfigDict

from app.schemas.recipe_item import RecipeItemRead


class MenuItemBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    is_active: bool = True


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    is_active: bool | None = None


class MenuItemRead(MenuItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_items: list[RecipeItemRead] = []
