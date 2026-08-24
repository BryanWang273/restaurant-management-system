from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.recipe_item import RecipeItem
from app.schemas.recipe_item import RecipeItemCreate


class InventoryItemNotFound(Exception):
    pass


class DuplicateRecipeItem(Exception):
    pass


def add_recipe_item(db: Session, menu_item_id: int, data: RecipeItemCreate) -> RecipeItem:
    inventory_item = db.get(InventoryItem, data.inventory_item_id)
    if inventory_item is None:
        raise InventoryItemNotFound()

    existing = db.scalar(
        select(RecipeItem).where(
            RecipeItem.menu_item_id == menu_item_id,
            RecipeItem.inventory_item_id == data.inventory_item_id,
        )
    )
    if existing is not None:
        raise DuplicateRecipeItem()

    recipe_item = RecipeItem(menu_item_id=menu_item_id, **data.model_dump())
    db.add(recipe_item)
    db.commit()
    db.refresh(recipe_item)
    return recipe_item


def get_recipe_item(db: Session, menu_item_id: int, recipe_item_id: int) -> RecipeItem | None:
    item = db.get(RecipeItem, recipe_item_id)
    if item is None or item.menu_item_id != menu_item_id:
        return None
    return item


def delete_recipe_item(db: Session, recipe_item: RecipeItem) -> None:
    db.delete(recipe_item)
    db.commit()
