import { PageHeader } from "@/components/page-header";
import { OrderBuilder } from "@/components/order-builder";
import { OrderHistoryTable } from "@/components/order-history-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { MenuItem, Order } from "@/lib/types";

// A plain `async function` Server Component: this runs on the Next.js
// server at request time, fetches straight from FastAPI, and streams
// rendered HTML to the browser. No client-side loading spinner, no
// useEffect — the data is already there when the page arrives.
export default async function OrdersPage() {
  const [menuItems, orders] = await Promise.all([
    api.get<MenuItem[]>("/menu-items/", { cache: "no-store" }),
    api.get<Order[]>("/orders/", { cache: "no-store" }),
  ]);

  const sortedOrders = [...orders].sort((a, b) => b.id - a.id);

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader
        title="Orders"
        description="Build a new order from the menu, or review order history."
      />
      <div className="flex flex-1 flex-col gap-8 p-6">
        <OrderBuilder menuItems={menuItems} />

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Order History</CardTitle>
          </CardHeader>
          <CardContent>
            <OrderHistoryTable orders={sortedOrders} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
