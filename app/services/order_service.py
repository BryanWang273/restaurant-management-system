from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.inventory_item import InventoryItem
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.usage_event import UsageEvent
from app.schemas.order import OrderCreate


class MenuItemNotFound(Exception):
    def __init__(self, menu_item_id: int):
        self.menu_item_id = menu_item_id


class MenuItemInactive(Exception):
    def __init__(self, menu_item_id: int):
        self.menu_item_id = menu_item_id


class InsufficientStock(Exception):
    def __init__(self, shortfalls: list[dict]):
        self.shortfalls = shortfalls


def place_order(db: Session, data: OrderCreate) -> Order:
    try:
        order = _place_order(db, data)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_order(db, order.id)


def _place_order(db: Session, data: OrderCreate) -> Order:
    menu_item_ids = {line.menu_item_id for line in data.items}
    menu_items = {
        m.id: m
        for m in db.scalars(
            select(MenuItem)
            .options(selectinload(MenuItem.recipe_items))
            .where(MenuItem.id.in_(menu_item_ids))
        )
    }

    for line in data.items:
        menu_item = menu_items.get(line.menu_item_id)
        if menu_item is None:
            raise MenuItemNotFound(line.menu_item_id)
        if not menu_item.is_active:
            raise MenuItemInactive(line.menu_item_id)

    # Aggregate inventory required across every line, in case two different
    # menu items in the same order both consume the same inventory item.
    required: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    for line in data.items:
        menu_item = menu_items[line.menu_item_id]
        for recipe_item in menu_item.recipe_items:
            required[recipe_item.inventory_item_id] += recipe_item.quantity_used * line.quantity

    inventory_items: dict[int, InventoryItem] = {}
    if required:
        # Lock the rows we're about to deduct from, in a fixed (id) order,
        # so two concurrent orders can't both read stale stock and both
        # succeed, and so concurrent transactions can't deadlock against
        # each other by locking the same rows in different orders.
        inventory_items = {
            i.id: i
            for i in db.scalars(
                select(InventoryItem)
                .where(InventoryItem.id.in_(required.keys()))
                .order_by(InventoryItem.id)
                .with_for_update()
            )
        }

        shortfalls = [
            {
                "inventory_item_id": inventory_item_id,
                "name": inventory_items[inventory_item_id].name,
                "required": needed_qty,
                "available": inventory_items[inventory_item_id].quantity_on_hand,
            }
            for inventory_item_id, needed_qty in required.items()
            if inventory_items[inventory_item_id].quantity_on_hand < needed_qty
        ]
        if shortfalls:
            raise InsufficientStock(shortfalls)

    order = Order(
        total_amount=sum(menu_items[line.menu_item_id].price * line.quantity for line in data.items)
    )
    db.add(order)
    db.flush()  # assigns order.id without ending the transaction

    for line in data.items:
        menu_item = menu_items[line.menu_item_id]
        db.add(
            OrderItem(
                order_id=order.id,
                menu_item_id=menu_item.id,
                quantity=line.quantity,
                unit_price=menu_item.price,
            )
        )

    for inventory_item_id, needed_qty in required.items():
        inventory_item = inventory_items[inventory_item_id]
        inventory_item.quantity_on_hand -= needed_qty
        db.add(
            UsageEvent(
                inventory_item_id=inventory_item_id,
                order_id=order.id,
                quantity_used=needed_qty,
            )
        )

    return order


def get_order(db: Session, order_id: int) -> Order | None:
    return db.scalars(
        select(Order).options(selectinload(Order.order_items)).where(Order.id == order_id)
    ).first()


def list_orders(db: Session) -> list[Order]:
    return list(
        db.scalars(
            select(Order).options(selectinload(Order.order_items)).order_by(Order.created_at.desc())
        )
    )
