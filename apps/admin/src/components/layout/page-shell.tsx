import { cn } from "@/lib/cn";
import { Separator } from "@/components/ui/separator";

export default function PageShell({
  title,
  description,
  children,
  actions,
  eyebrow,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  eyebrow?: string;
}) {
  return (
    <section className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      {/* Page header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          {eyebrow ? (
            <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.28em] text-accent">
              {eyebrow}
            </p>
          ) : null}
          <h1 className="font-display text-2xl font-semibold tracking-tight text-foreground md:text-3xl">
            {title}
          </h1>
          {description ? (
            <p className="mt-1.5 max-w-2xl text-sm leading-6 text-muted-foreground">
              {description}
            </p>
          ) : null}
        </div>
        <div className={cn("flex shrink-0 items-center gap-2", !actions && "hidden")}>
          {actions}
        </div>
      </div>

      <Separator />

      {children}
    </section>
  );
}

