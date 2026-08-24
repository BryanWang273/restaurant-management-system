from fastapi import FastAPI
from app.routers import ai, inventory, menu_items, orders

app = FastAPI(title="Restaurant Management System")

app.include_router(inventory.router)
app.include_router(menu_items.router)
app.include_router(orders.router)
app.include_router(ai.router)


@app.get("/health")
def health():
    return {"status": "ok"} 
