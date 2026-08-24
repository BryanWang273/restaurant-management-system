"use server";

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import type { Order, OrderCreate, StockShortfall } from "@/lib/types";

// A discriminated union instead of throwing: Server Actions can throw, but
// then the client only gets a generic "something went wrong" message unless
// you wire up an error boundary. Returning a typed result lets the form show
// exactly which ingredients are short, which is the whole point of surfacing
// this error at all.
export type PlaceOrderResult =
  | { ok: true; order: Order }
  | { ok: false; error: string; shortfalls?: StockShortfall[] };

export async function placeOrder(
  payload: OrderCreate
): Promise<PlaceOrderResult> {
  try {
    const order = await api.post<Order>("/orders/", payload);

    // Revalidate every route whose data this order just changed: the order
    // history table, the inventory levels it deducted from, and the
    // dashboard stats that summarize both.
    revalidatePath("/orders");
    revalidatePath("/inventory");
    revalidatePath("/");

    return { ok: true, order };
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      const body = err.body as { shortfalls?: StockShortfall[] } | null;
      return {
        ok: false,
        error: "Insufficient stock for this order.",
        shortfalls: body?.shortfalls,
      };
    }
    if (err instanceof ApiError) {
      return { ok: false, error: err.message };
    }
    return { ok: false, error: "Could not reach the server." };
  }
}
