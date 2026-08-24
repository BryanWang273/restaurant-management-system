import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDateTime, formatPrice } from "@/lib/format";
import type { Order } from "@/lib/types";

export function OrderHistoryTable({ orders }: { orders: Order[] }) {
  if (orders.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No orders placed yet.</p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Order</TableHead>
          <TableHead>Placed</TableHead>
          <TableHead>Items</TableHead>
          <TableHead className="text-right">Total</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {orders.map((order) => (
          <TableRow key={order.id}>
            <TableCell className="font-mono">#{order.id}</TableCell>
            <TableCell className="text-muted-foreground">
              {formatDateTime(order.created_at)}
            </TableCell>
            <TableCell className="text-muted-foreground">
              {order.order_items.reduce((n, i) => n + i.quantity, 0)} items
            </TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatPrice(order.total_amount)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
