from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.schemas.inventory_item import InventoryItemCreate, InventoryItemUpdate


def list_items(db: Session) -> list[InventoryItem]:
    return list(db.scalars(select(InventoryItem).order_by(InventoryItem.name)))


def get_item(db: Session, item_id: int) -> InventoryItem | None:
    return db.get(InventoryItem, item_id)


def create_item(db: Session, data: InventoryItemCreate) -> InventoryItem:
    item = InventoryItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item: InventoryItem, data: InventoryItemUpdate) -> InventoryItem:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: InventoryItem) -> None:
    db.delete(item)
    db.commit()


def list_low_stock(db: Session) -> list[InventoryItem]:
    return list(
        db.scalars(
            select(InventoryItem)
            .where(InventoryItem.quantity_on_hand <= InventoryItem.reorder_point)
            .order_by(InventoryItem.name)
        )
    )
