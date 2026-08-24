from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    unit: Mapped[str] = mapped_column(String(50))
    quantity_on_hand: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    reorder_point: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
