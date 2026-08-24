import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatPrice, formatQuantity } from "@/lib/format";
import { api } from "@/lib/api";
import type { InventoryItem, MenuItem } from "@/lib/types";

export default async function MenuPage() {
  const [menuItems, inventoryItems] = await Promise.all([
    api.get<MenuItem[]>("/menu-items/", { cache: "no-store" }),
    api.get<InventoryItem[]>("/inventory-items/", { cache: "no-store" }),
  ]);

  const inventoryById = new Map(inventoryItems.map((i) => [i.id, i]));

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader
        title="Menu"
        description="Everything on the menu, with the ingredients each dish draws from."
      />
      <div className="flex flex-1 flex-col gap-3 p-6">
        {menuItems.map((item) => (
          <Card key={item.id}>
            <CardContent className="flex flex-col gap-3 py-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-heading text-lg font-medium">
                    {item.name}
                  </h3>
                  <Badge variant={item.is_active ? "secondary" : "outline"}>
                    {item.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
                {item.description ? (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {item.description}
                  </p>
                ) : null}

                {item.recipe_items.length > 0 ? (
                  <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-muted-foreground">
                    {item.recipe_items.map((recipe) => {
                      const ingredient = inventoryById.get(
                        recipe.inventory_item_id
                      );
                      return (
                        <li key={recipe.id}>
                          {formatQuantity(recipe.quantity_used)}
                          {ingredient?.unit ?? ""} {ingredient?.name ?? "unknown ingredient"}
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </div>

              <span className="shrink-0 font-mono text-lg tabular-nums">
                {formatPrice(item.price)}
              </span>
            </CardContent>
          </Card>
        ))}

        {menuItems.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No menu items yet.
          </p>
        ) : null}
      </div>
    </div>
  );
}
