"use client";

import { useState, useTransition } from "react";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { RecommendationTicket } from "@/components/recommendation-ticket";
import { generateRecommendations } from "@/app/recommendations/actions";
import type { InventoryItem, InventoryRecommendation } from "@/lib/types";

export function RecommendationsPanel({
  inventoryItems,
}: {
  inventoryItems: InventoryItem[];
}) {
  const [recommendations, setRecommendations] = useState<
    InventoryRecommendation[] | null
  >(null);
  const [isPending, startTransition] = useTransition();

  const inventoryById = new Map(inventoryItems.map((item) => [item.id, item]));

  function handleGenerate() {
    startTransition(async () => {
      const result = await generateRecommendations();
      if (result.ok) {
        setRecommendations(result.data.recommendations);
        if (result.data.recommendations.length === 0) {
          toast.success("Nothing needs reordering right now.");
        }
      } else {
        toast.error(result.error);
      }
    });
  }

  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <Button onClick={handleGenerate} disabled={isPending}>
          <Sparkles />
          {isPending ? "Firing the line…" : "Generate Recommendations"}
        </Button>
      </div>

      {recommendations === null && !isPending ? (
        <p className="text-sm text-muted-foreground">
          Generate recommendations to see reorder suggestions for low-stock
          ingredients, grounded in actual consumption data.
        </p>
      ) : null}

      {isPending ? (
        <p className="font-mono text-sm text-muted-foreground">
          Checking the pass…
        </p>
      ) : null}

      {recommendations !== null && recommendations.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Nothing needs reordering right now — every ingredient is above its
          reorder point.
        </p>
      ) : null}

      {recommendations && recommendations.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {recommendations.map((recommendation) => (
            <RecommendationTicket
              key={recommendation.inventory_item_id}
              recommendation={recommendation}
              unit={inventoryById.get(recommendation.inventory_item_id)?.unit}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}
