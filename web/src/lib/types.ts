// Mirrors app/schemas/*.py on the FastAPI side. Kept hand-written and in
// sync manually since the backend has no OpenAPI-to-TS generation step yet.

export interface RecipeItem {
  id: number;
  inventory_item_id: number;
  quantity_used: number;
}

export interface MenuItem {
  id: number;
  name: string;
  description: string | null;
  price: number;
  is_active: boolean;
  recipe_items: RecipeItem[];
}

export interface InventoryItem {
  id: number;
  name: string;
  unit: string;
  quantity_on_hand: number;
  reorder_point: number;
}

export interface OrderItem {
  id: number;
  menu_item_id: number;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: number;
  created_at: string;
  total_amount: number;
  order_items: OrderItem[];
}

export interface OrderItemCreate {
  menu_item_id: number;
  quantity: number;
}

export interface OrderCreate {
  items: OrderItemCreate[];
}

export interface StockShortfall {
  inventory_item_id: number;
  name: string;
  required: number;
  available: number;
}

export type RecommendationUrgency = "low" | "medium" | "high";

export interface InventoryRecommendation {
  inventory_item_id: number;
  name: string;
  recommended_reorder_qty: number;
  urgency: RecommendationUrgency;
  reasoning: string;
}

export interface InventoryRecommendationResponse {
  recommendations: InventoryRecommendation[];
}
