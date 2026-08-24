import Link from "next/link";
import { ClipboardList, DollarSign, TriangleAlert, UtensilsCrossed } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { OrderHistoryTable } from "@/components/order-history-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatPrice, isSameDay } from "@/lib/format";
import { api } from "@/lib/api";
import type { InventoryItem, MenuItem, Order } from "@/lib/types";

export default async function DashboardPage() {
  const [orders, menuItems, lowStockItems] = await Promise.all([
    api.get<Order[]>("/orders/", { cache: "no-store" }),
    api.get<MenuItem[]>("/menu-items/", { cache: "no-store" }),
    api.get<InventoryItem[]>("/inventory-items/low-stock", {
      cache: "no-store",
    }),
  ]);

  // There's no dashboard/stats endpoint on the backend, and orders/menu
  // items have no server-side date filtering — so "today" is derived here
  // from the full order list, not a query FastAPI ran for us.
  const today = new Date();
  const ordersToday = orders.filter((o) => isSameDay(o.created_at, today));
  const revenueToday = ordersToday.reduce((sum, o) => sum + o.total_amount, 0);
  const activeMenuItems = menuItems.filter((m) => m.is_active).length;

  const recentOrders = [...orders].sort((a, b) => b.id - a.id).slice(0, 5);

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader
        title="Dashboard"
        description="Today at a glance."
        action={
          <Button asChild>
            <Link href="/orders">New Order</Link>
          </Button>
        }
      />
      <div className="flex flex-1 flex-col gap-6 p-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Orders Today"
            value={String(ordersToday.length)}
            icon={ClipboardList}
          />
          <StatCard
            label="Revenue Today"
            value={formatPrice(revenueToday)}
            icon={DollarSign}
            tone="success"
          />
          <StatCard
            label="Active Menu Items"
            value={String(activeMenuItems)}
            icon={UtensilsCrossed}
          />
          <StatCard
            label="Low Stock Items"
            value={String(lowStockItems.length)}
            icon={TriangleAlert}
            tone={lowStockItems.length > 0 ? "destructive" : "default"}
          />
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Recent Orders</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/orders">View all</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <OrderHistoryTable orders={recentOrders} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
