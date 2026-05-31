import Link from "next/link";
import { ChevronLeft } from "lucide-react";

export default function ReportTableWrapper({
  title,
  subtitle,
  actions,
  filters,
  rowCount,
  children,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  filters?: React.ReactNode;
  rowCount?: number;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <section className="border-b border-border pb-6">
        <Link
          href="/reports"
          className="mb-3 inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          All reports
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
              Reports
            </p>
            <h1 className="mt-2 font-display text-3xl font-semibold tracking-[-0.02em] text-foreground">
              {title}
            </h1>
            {subtitle && (
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{subtitle}</p>
            )}
          </div>
          {actions && (
            <div className="flex shrink-0 items-center gap-2 pt-7">{actions}</div>
          )}
        </div>
      </section>

      {/* Filters */}
      {filters && <div>{filters}</div>}

      {/* Table card */}
      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        {children}
      </div>

      {/* Row count */}
      {typeof rowCount === "number" && (
        <p className="text-sm text-muted-foreground">
          {rowCount} {rowCount === 1 ? "record" : "records"}
          {rowCount === 0 ? "" : " shown"}.
        </p>
      )}
    </div>
  );
}
