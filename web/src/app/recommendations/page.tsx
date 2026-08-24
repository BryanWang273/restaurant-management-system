import { PageHeader } from "@/components/page-header";
import { RecommendationsPanel } from "@/components/recommendations-panel";
import { api } from "@/lib/api";
import type { InventoryItem } from "@/lib/types";

export default async function RecommendationsPage() {
  const inventoryItems = await api.get<InventoryItem[]>("/inventory-items/", {
    cache: "no-store",
  });

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader
        title="Recommendations"
        description="AI-generated reorder suggestions for low-stock ingredients."
      />
      <div className="flex flex-1 flex-col p-6">
        <RecommendationsPanel inventoryItems={inventoryItems} />
      </div>
    </div>
  );
}
