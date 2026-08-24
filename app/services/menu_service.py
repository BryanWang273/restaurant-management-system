from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.menu_item import MenuItem
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate


def list_items(db: Session) -> list[MenuItem]:
    return list(
        db.scalars(
            select(MenuItem).options(selectinload(MenuItem.recipe_items)).order_by(MenuItem.name)
        )
    )


def get_item(db: Session, item_id: int) -> MenuItem | None:
    return db.scalars(
        select(MenuItem)
        .options(selectinload(MenuItem.recipe_items))
        .where(MenuItem.id == item_id)
    ).first()


def create_item(db: Session, data: MenuItemCreate) -> MenuItem:
    item = MenuItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item: MenuItem, data: MenuItemUpdate) -> MenuItem:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: MenuItem) -> None:
    db.delete(item)
    db.commit()
