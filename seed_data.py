"""Reset the demo data to a realistic Wagamama-inspired menu.

Wipes every menu item, inventory item, order, and recipe link, then
reinserts a fixed set of menu items with their ingredient recipes and
matching inventory. A couple of ingredients are seeded already at or just
under their reorder point, so the inventory page's low-stock highlighting
and the AI recommendation agent both have something real to react to
right after a fresh run.

Safe to re-run: it always clears prior data first rather than appending,
so running it again resets the demo back to this same known state
(useful after a demo session has placed orders and drained stock).

Run from the repo root:

    venv/Scripts/python.exe seed_data.py
"""

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.inventory_item import InventoryItem
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.recipe_item import RecipeItem
from app.models.usage_event import UsageEvent

# (name, unit, quantity_on_hand, reorder_point)
INVENTORY_ITEMS = [
    ("Breaded Chicken Breast", "g", 6000, 1500),
    ("Breaded Mixed Vegetables", "g", 4000, 1000),
    ("Curry Sauce", "ml", 850, 1000),  # low stock — used by 2 dishes
    ("Jasmine Rice", "g", 8000, 2000),
    ("Chicken Thigh", "g", 5000, 1200),
    ("Teriyaki Sauce", "ml", 1600, 400),
    ("Mixed Vegetables", "g", 6000, 1500),
    ("Beef", "g", 5000, 1200),
    ("Bulgogi Sauce", "ml", 1600, 400),
    ("Udon Noodles", "g", 5000, 1000),
    ("Curry Broth Base", "ml", 6000, 1600),
    ("Tofu", "g", 3000, 800),
    ("Mushrooms", "g", 2400, 640),
    ("Soba Noodles", "g", 4000, 1000),
    ("Yaki Soba Sauce", "ml", 1200, 300),
    ("Gyoza Dumplings", "count", 54, 60),  # low stock — popular starter
    ("Dipping Sauce", "ml", 900, 240),
    ("Squid", "g", 900, 1000),  # low stock — limited supply item
    ("Chilli Sauce", "ml", 1000, 250),
    ("Spring Onion", "g", 500, 150),
    ("Soybeans", "g", 4500, 1000),
    ("Salt", "g", 1000, 200),
    ("Chilli", "g", 400, 100),
]

# (name, description, price, is_active, [(ingredient, quantity_used)])
MENU_ITEMS = [
    (
        "Chicken Katsu Curry",
        "Breaded chicken breast, katsu curry sauce, jasmine rice",
        13.95,
        True,
        [
            ("Breaded Chicken Breast", 200),
            ("Curry Sauce", 150),
            ("Jasmine Rice", 200),
        ],
    ),
    (
        "Yasai Katsu Curry",
        "Breaded mixed vegetables, katsu curry sauce, jasmine rice (vegetarian)",
        12.50,
        True,
        [
            ("Breaded Mixed Vegetables", 200),
            ("Curry Sauce", 150),
            ("Jasmine Rice", 200),
        ],
    ),
    (
        "Chicken Teriyaki Donburi",
        "Grilled chicken thigh, teriyaki sauce, jasmine rice, mixed vegetables",
        13.50,
        True,
        [
            ("Chicken Thigh", 200),
            ("Teriyaki Sauce", 80),
            ("Jasmine Rice", 200),
            ("Mixed Vegetables", 100),
        ],
    ),
    (
        "Beef Bulgogi Donburi",
        "Beef bulgogi, jasmine rice, mixed vegetables",
        14.50,
        True,
        [
            ("Beef", 200),
            ("Bulgogi Sauce", 80),
            ("Jasmine Rice", 200),
            ("Mixed Vegetables", 100),
        ],
    ),
    (
        "Kare Burosu Ramen",
        "Udon noodles in a vegan curry broth with tofu, mushrooms, and mixed vegetables",
        13.95,
        True,
        [
            ("Udon Noodles", 250),
            ("Curry Broth Base", 400),
            ("Tofu", 100),
            ("Mushrooms", 80),
            ("Mixed Vegetables", 100),
        ],
    ),
    (
        "Yasai Yaki Soba",
        "Stir-fried soba noodles with mixed vegetables and yaki soba sauce",
        11.95,
        True,
        [
            ("Soba Noodles", 200),
            ("Mixed Vegetables", 150),
            ("Yaki Soba Sauce", 60),
        ],
    ),
    (
        "Chicken Gyoza",
        "Pan-fried chicken dumplings with dipping sauce",
        6.50,
        True,
        [
            ("Gyoza Dumplings", 6),
            ("Dipping Sauce", 30),
        ],
    ),
    (
        "Chilli Squid",
        "Crispy squid with chilli sauce and spring onion",
        7.95,
        True,
        [
            ("Squid", 180),
            ("Chilli Sauce", 50),
            ("Spring Onion", 10),
        ],
    ),
    (
        "Edamame",
        "Steamed soybeans with salt",
        4.50,
        True,
        [
            ("Soybeans", 150),
            ("Salt", 2),
        ],
    ),
    (
        "Spicy Edamame",
        "Steamed soybeans with chilli and salt",
        4.95,
        True,
        [
            ("Soybeans", 150),
            ("Chilli", 5),
            ("Salt", 2),
        ],
    ),
]


def main() -> None:
    db = SessionLocal()
    try:
        # Clear in FK-safe order (children before parents) so this is
        # always safe to re-run.
        db.execute(delete(UsageEvent))
        db.execute(delete(OrderItem))
        db.execute(delete(Order))
        db.execute(delete(RecipeItem))
        db.execute(delete(MenuItem))
        db.execute(delete(InventoryItem))
        db.flush()

        inventory_by_name = {}
        for name, unit, quantity_on_hand, reorder_point in INVENTORY_ITEMS:
            item = InventoryItem(
                name=name,
                unit=unit,
                quantity_on_hand=quantity_on_hand,
                reorder_point=reorder_point,
            )
            db.add(item)
            inventory_by_name[name] = item
        db.flush()  # assigns ids without ending the transaction

        for name, description, price, is_active, recipe in MENU_ITEMS:
            menu_item = MenuItem(
                name=name,
                description=description,
                price=price,
                is_active=is_active,
            )
            db.add(menu_item)
            db.flush()

            for ingredient_name, quantity_used in recipe:
                db.add(
                    RecipeItem(
                        menu_item_id=menu_item.id,
                        inventory_item_id=inventory_by_name[ingredient_name].id,
                        quantity_used=quantity_used,
                    )
                )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    low_stock = [
        name
        for name, _, quantity_on_hand, reorder_point in INVENTORY_ITEMS
        if quantity_on_hand <= reorder_point
    ]
    print(f"Seeded {len(INVENTORY_ITEMS)} inventory items and {len(MENU_ITEMS)} menu items.")
    print(f"Low-stock on seed: {', '.join(low_stock)}")


if __name__ == "__main__":
    main()
