import { AlertTriangle } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { formatQuantity } from "@/lib/format";
import { api } from "@/lib/api";
import type { InventoryItem } from "@/lib/types";

export default async function InventoryPage() {
  const items = await api.get<InventoryItem[]>("/inventory-items/", {
    cache: "no-store",
  });

  const sorted = [...items].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader
        title="Inventory"
        description="Stock on hand across every ingredient. Rows in red are at or below their reorder point."
      />
      <div className="flex flex-1 flex-col p-6">
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ingredient</TableHead>
                  <TableHead>Unit</TableHead>
                  <TableHead className="text-right">On Hand</TableHead>
                  <TableHead className="text-right">Reorder Point</TableHead>
                  <TableHead className="text-right">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sorted.map((item) => {
                  const isLow = item.quantity_on_hand <= item.reorder_point;
                  return (
                    <TableRow
                      key={item.id}
                      className={cn(
                        isLow &&
                          "bg-destructive/10 hover:bg-destructive/15"
                      )}
                    >
                      <TableCell
                        className={cn(
                          "font-medium",
                          isLow && "text-destructive"
                        )}
                      >
                        {item.name}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {item.unit}
                      </TableCell>
                      <TableCell
                        className={cn(
                          "text-right font-mono tabular-nums",
                          isLow && "font-medium text-destructive"
                        )}
                      >
                        {formatQuantity(item.quantity_on_hand)}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums text-muted-foreground">
                        {formatQuantity(item.reorder_point)}
                      </TableCell>
                      <TableCell className="text-right">
                        {isLow ? (
                          <Badge
                            variant="destructive"
                            className="gap-1"
                          >
                            <AlertTriangle className="size-3" />
                            Low stock
                          </Badge>
                        ) : (
                          <Badge
                            variant="secondary"
                            className="gap-1 bg-success/15 text-success"
                          >
                            Healthy
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
                {sorted.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={5}
                      className="text-center text-muted-foreground"
                    >
                      No inventory items yet.
                    </TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
