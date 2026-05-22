import { type ReactNode } from "react";
import { cn } from "@/lib/cn";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export default function SectionCard({
  title,
  description,
  action,
  children,
  className,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const hasHeader = title || description || action;

  return (
    <Card className={cn("overflow-hidden", className)}>
      {hasHeader ? (
        <>
          <CardHeader className="flex-row items-start justify-between gap-4 py-4">
            <div className="space-y-0.5">
              {title ? <CardTitle>{title}</CardTitle> : null}
              {description ? <CardDescription>{description}</CardDescription> : null}
            </div>
            {action ? <div className="shrink-0">{action}</div> : null}
          </CardHeader>
          <Separator />
        </>
      ) : null}
      <CardContent className={cn("p-6", !hasHeader && "pt-6")}>{children}</CardContent>
    </Card>
  );
}

