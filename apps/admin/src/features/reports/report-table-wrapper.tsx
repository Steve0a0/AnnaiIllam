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
  /** Toolbar area: export buttons, filters, search, date range, etc. */
  actions?: React.ReactNode;
  filters?: React.ReactNode;
  rowCount?: number;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
          {subtitle ? (
            <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
          ) : null}
        </div>

        {actions ? (
          <div className="flex shrink-0 items-center gap-2">{actions}</div>
        ) : null}
      </div>

      {filters ? <div>{filters}</div> : null}

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {children}
      </div>

      {typeof rowCount === "number" ? (
        <p className="text-sm text-muted-foreground">
          Showing {rowCount} {rowCount === 1 ? "record" : "records"}.
        </p>
      ) : null}
    </div>
  );
}
