"use client";

import { useMemo, useState, useTransition } from "react";
import { Minus, Plus, ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { formatPrice } from "@/lib/format";
import type { MenuItem, StockShortfall } from "@/lib/types";
import { placeOrder } from "@/app/orders/actions";
import { toast } from "sonner";

type CartLine = { menuItem: MenuItem; quantity: number };

export function OrderBuilder({ menuItems }: { menuItems: MenuItem[] }) {
  const [cart, setCart] = useState<Map<number, CartLine>>(new Map());
  const [shortfalls, setShortfalls] = useState<StockShortfall[] | null>(null);
  const [isPending, startTransition] = useTransition();

  const lines = useMemo(() => Array.from(cart.values()), [cart]);
  const total = useMemo(
    () => lines.reduce((sum, l) => sum + l.menuItem.price * l.quantity, 0),
    [lines]
  );

  function addItem(menuItem: MenuItem) {
    setCart((prev) => {
      const next = new Map(prev);
      const existing = next.get(menuItem.id);
      next.set(menuItem.id, {
        menuItem,
        quantity: (existing?.quantity ?? 0) + 1,
      });
      return next;
    });
  }

  function changeQuantity(menuItemId: number, delta: number) {
    setCart((prev) => {
      const next = new Map(prev);
      const existing = next.get(menuItemId);
      if (!existing) return prev;
      const quantity = existing.quantity + delta;
      if (quantity <= 0) {
        next.delete(menuItemId);
      } else {
        next.set(menuItemId, { ...existing, quantity });
      }
      return next;
    });
  }

  function submitOrder() {
    setShortfalls(null);
    const payload = {
      items: lines.map((l) => ({
        menu_item_id: l.menuItem.id,
        quantity: l.quantity,
      })),
    };

    startTransition(async () => {
      const result = await placeOrder(payload);
      if (result.ok) {
        toast.success(`Order #${result.order.id} placed`, {
          description: `Total ${formatPrice(result.order.total_amount)}`,
        });
        setCart(new Map());
      } else {
        toast.error(result.error);
        setShortfalls(result.shortfalls ?? null);
      }
    });
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
      <div className="flex flex-col gap-3">
        {menuItems.map((item) => (
          <Card key={item.id} className={!item.is_active ? "opacity-50" : ""}>
            <CardContent className="flex items-center justify-between gap-4 py-4">
              <div className="min-w-0">
                <p className="truncate font-medium">{item.name}</p>
                {item.description ? (
                  <p className="truncate text-sm text-muted-foreground">
                    {item.description}
                  </p>
                ) : null}
              </div>
              <div className="flex shrink-0 items-center gap-4">
                <span className="font-mono text-sm tabular-nums">
                  {formatPrice(item.price)}
                </span>
                <Button
                  size="sm"
                  disabled={!item.is_active}
                  onClick={() => addItem(item)}
                >
                  {item.is_active ? "Add" : "Unavailable"}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {menuItems.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No menu items to order yet.
          </p>
        ) : null}
      </div>

      <Card className="h-fit lg:sticky lg:top-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShoppingCart className="size-4" />
            Current Order
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {lines.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No items yet — add something from the menu.
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              {lines.map(({ menuItem, quantity }) => (
                <div
                  key={menuItem.id}
                  className="flex items-center justify-between gap-2 text-sm"
                >
                  <span className="min-w-0 truncate">{menuItem.name}</span>
                  <div className="flex shrink-0 items-center gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      className="size-6"
                      onClick={() => changeQuantity(menuItem.id, -1)}
                    >
                      <Minus className="size-3" />
                    </Button>
                    <span className="w-4 text-center font-mono tabular-nums">
                      {quantity}
                    </span>
                    <Button
                      variant="outline"
                      size="icon"
                      className="size-6"
                      onClick={() => changeQuantity(menuItem.id, 1)}
                    >
                      <Plus className="size-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <Separator />

          <div className="flex items-center justify-between font-medium">
            <span>Total</span>
            <span className="font-mono tabular-nums">
              {formatPrice(total)}
            </span>
          </div>

          <Button
            className="w-full"
            disabled={lines.length === 0 || isPending}
            onClick={submitOrder}
          >
            {isPending ? "Placing order…" : "Place Order"}
          </Button>

          {shortfalls && shortfalls.length > 0 ? (
            <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              <p className="font-medium">Not enough stock:</p>
              <ul className="mt-1 list-disc pl-4">
                {shortfalls.map((s) => (
                  <li key={s.inventory_item_id}>
                    {s.name} — need {s.required}, have {s.available}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
