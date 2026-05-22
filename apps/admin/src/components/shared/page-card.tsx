import { type ReactNode } from "react";
import { cn } from "@/lib/cn";
import { Card } from "@/components/ui/card";

export default function PageCard({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("p-6", className)}>
      {children}
    </Card>
  );
}

