import type { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";

type DashboardStatCardProps = {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  tone?: "brand" | "warning" | "danger" | "info" | "teal";
  trend?: string;
};

const toneStyles = {
  brand: "bg-(--color-brand-50) text-(--color-brand-600)",
  warning: "bg-amber-50 text-amber-700",
  danger: "bg-red-50 text-red-700",
  info: "bg-blue-50 text-blue-700",
  teal: "bg-cyan-50 text-cyan-700",
};

export default function DashboardStatCard({
  title,
  value,
  subtitle,
  icon,
  tone = "brand",
  trend,
}: DashboardStatCardProps) {
  return (
    <Card className="border-border bg-white shadow-sm">
      <CardContent className="p-4 md:p-5">
        <div className="flex items-center justify-between gap-3">
          <div className={cn("flex h-9 w-9 items-center justify-center rounded-md", toneStyles[tone])}>
            {icon}
          </div>
          {trend ? (
            <Badge className="rounded-full border-transparent bg-muted text-xs font-medium text-muted-foreground">
              {trend}
            </Badge>
          ) : null}
        </div>
        <p className="mt-3 font-display text-3xl font-semibold leading-none tracking-tight text-foreground">
          {value}
        </p>
        <div className="mt-2 flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <p className="text-xs font-medium text-foreground">{title}</p>
          {subtitle ? <p className="text-xs text-muted-foreground">{subtitle}</p> : null}
        </div>
      </CardContent>
    </Card>
  );
}
