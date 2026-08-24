from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.inventory_item import InventoryItemCreate, InventoryItemRead, InventoryItemUpdate
from app.services import inventory_service

router = APIRouter(prefix="/inventory-items", tags=["inventory"])


@router.get("/", response_model=list[InventoryItemRead])
def list_inventory_items(db: Session = Depends(get_db)):
    return inventory_service.list_items(db)


@router.get("/low-stock", response_model=list[InventoryItemRead])
def get_low_stock_items(db: Session = Depends(get_db)):
    return inventory_service.list_low_stock(db)


@router.get("/{item_id}", response_model=InventoryItemRead)
def get_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = inventory_service.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.post("/", response_model=InventoryItemRead, status_code=201)
def create_inventory_item(data: InventoryItemCreate, db: Session = Depends(get_db)):
    return inventory_service.create_item(db, data)


@router.patch("/{item_id}", response_model=InventoryItemRead)
def update_inventory_item(item_id: int, data: InventoryItemUpdate, db: Session = Depends(get_db)):
    item = inventory_service.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return inventory_service.update_item(db, item, data)


@router.delete("/{item_id}", status_code=204)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = inventory_service.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    inventory_service.delete_item(db, item)
