from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.inventory_item import InventoryItem
    from app.models.menu_item import MenuItem


class RecipeItem(Base):
    __tablename__ = "recipe_items"
    __table_args__ = (UniqueConstraint("menu_item_id", "inventory_item_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    quantity_used: Mapped[float] = mapped_column(Numeric(10, 2))

    menu_item: Mapped["MenuItem"] = relationship(back_populates="recipe_items")
    inventory_item: Mapped["InventoryItem"] = relationship()
