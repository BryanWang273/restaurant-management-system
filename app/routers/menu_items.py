from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.menu_item import MenuItemCreate, MenuItemRead, MenuItemUpdate
from app.schemas.recipe_item import RecipeItemCreate, RecipeItemRead
from app.services import menu_service, recipe_service

router = APIRouter(prefix="/menu-items", tags=["menu"])


@router.get("/", response_model=list[MenuItemRead])
def list_menu_items(db: Session = Depends(get_db)):
    return menu_service.list_items(db)


@router.get("/{menu_item_id}", response_model=MenuItemRead)
def get_menu_item(menu_item_id: int, db: Session = Depends(get_db)):
    item = menu_service.get_item(db, menu_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item


@router.post("/", response_model=MenuItemRead, status_code=201)
def create_menu_item(data: MenuItemCreate, db: Session = Depends(get_db)):
    return menu_service.create_item(db, data)


@router.patch("/{menu_item_id}", response_model=MenuItemRead)
def update_menu_item(menu_item_id: int, data: MenuItemUpdate, db: Session = Depends(get_db)):
    item = menu_service.get_item(db, menu_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return menu_service.update_item(db, item, data)


@router.delete("/{menu_item_id}", status_code=204)
def delete_menu_item(menu_item_id: int, db: Session = Depends(get_db)):
    item = menu_service.get_item(db, menu_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    menu_service.delete_item(db, item)


@router.post("/{menu_item_id}/recipe-items", response_model=RecipeItemRead, status_code=201)
def add_recipe_item(menu_item_id: int, data: RecipeItemCreate, db: Session = Depends(get_db)):
    menu_item = menu_service.get_item(db, menu_item_id)
    if menu_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    try:
        return recipe_service.add_recipe_item(db, menu_item_id, data)
    except recipe_service.InventoryItemNotFound:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    except recipe_service.DuplicateRecipeItem:
        raise HTTPException(
            status_code=409,
            detail="This menu item already has a recipe line for that inventory item",
        )


@router.delete("/{menu_item_id}/recipe-items/{recipe_item_id}", status_code=204)
def delete_recipe_item(menu_item_id: int, recipe_item_id: int, db: Session = Depends(get_db)):
    recipe_item = recipe_service.get_recipe_item(db, menu_item_id, recipe_item_id)
    if recipe_item is None:
        raise HTTPException(status_code=404, detail="Recipe item not found")
    recipe_service.delete_recipe_item(db, recipe_item)
