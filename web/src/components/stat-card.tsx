import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = "default",
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  tone?: "default" | "success" | "destructive";
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-3 py-5">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p
            className={cn(
              "mt-1 font-mono text-3xl font-medium tabular-nums",
              tone === "success" && "text-success",
              tone === "destructive" && "text-destructive"
            )}
          >
            {value}
          </p>
        </div>
        <div
          className={cn(
            "flex size-9 shrink-0 items-center justify-center rounded-md",
            tone === "default" && "bg-accent text-accent-foreground",
            tone === "success" && "bg-success/15 text-success",
            tone === "destructive" && "bg-destructive/15 text-destructive"
          )}
        >
          <Icon className="size-4" />
        </div>
      </CardContent>
    </Card>
  );
}
