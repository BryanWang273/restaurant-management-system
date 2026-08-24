from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order import OrderCreate, OrderRead
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db)):
    return order_service.list_orders(db)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderRead, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    try:
        return order_service.place_order(db, data)
    except order_service.MenuItemNotFound as e:
        raise HTTPException(status_code=404, detail=f"Menu item {e.menu_item_id} not found")
    except order_service.MenuItemInactive as e:
        raise HTTPException(
            status_code=400, detail=f"Menu item {e.menu_item_id} is not currently available"
        )
    except order_service.InsufficientStock as e:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Insufficient stock for this order",
                "shortfalls": [
                    {
                        "inventory_item_id": s["inventory_item_id"],
                        "name": s["name"],
                        "required": float(s["required"]),
                        "available": float(s["available"]),
                    }
                    for s in e.shortfalls
                ],
            },
        )
