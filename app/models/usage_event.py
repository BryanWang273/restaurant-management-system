from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.inventory_item import InventoryItem
    from app.models.order import Order


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    quantity_used: Mapped[float] = mapped_column(Numeric(10, 2))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    inventory_item: Mapped["InventoryItem"] = relationship()
    order: Mapped["Order"] = relationship()
