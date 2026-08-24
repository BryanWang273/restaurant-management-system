import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatQuantity } from "@/lib/format";
import type { InventoryRecommendation, RecommendationUrgency } from "@/lib/types";

const URGENCY_BADGE_STYLES: Record<RecommendationUrgency, string> = {
  high: "border-destructive/40 text-destructive",
  medium: "border-primary/50 text-primary",
  low: "border-border text-muted-foreground",
};

export function RecommendationTicket({
  recommendation,
  unit,
}: {
  recommendation: InventoryRecommendation;
  unit?: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-md border border-border bg-card pt-3 shadow-sm">
      {/* Perforated tear line along the top edge, punched out in the page background color. */}
      <div
        aria-hidden
        className="absolute inset-x-0 top-0 h-2.5 bg-repeat-x [background-image:radial-gradient(circle,var(--background)_3px,transparent_3.25px)] [background-size:14px_10px] [background-position:0_-5px]"
      />

      <div className="border-b border-dashed border-border px-4 pb-3">
        <div className="flex items-center justify-between gap-2">
          <span className="font-mono text-[0.65rem] font-medium tracking-[0.2em] text-muted-foreground uppercase">
            Reorder Ticket
          </span>
          <Badge
            variant="outline"
            className={cn(
              "font-mono uppercase",
              URGENCY_BADGE_STYLES[recommendation.urgency]
            )}
          >
            {recommendation.urgency}
          </Badge>
        </div>
        <h3 className="mt-2 font-heading text-lg font-semibold text-card-foreground">
          {recommendation.name}
        </h3>
        <p className="font-mono text-2xl font-medium tabular-nums text-card-foreground">
          {formatQuantity(recommendation.recommended_reorder_qty)}
          {unit ? <span className="ml-1 text-base text-muted-foreground">{unit}</span> : null}
        </p>
      </div>

      <p className="whitespace-pre-wrap px-4 py-3 font-mono text-xs leading-relaxed text-muted-foreground">
        {recommendation.reasoning}
      </p>
    </div>
  );
}
