export default function ReportsLoading() {
  return (
    <div className="divide-y divide-border">
      {Array.from({ length: 7 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3.5">
          <div
            className="h-4 w-8 shrink-0 animate-pulse rounded"
            style={{ background: "var(--color-brand-50)" }}
          />
          <div
            className="h-4 w-24 animate-pulse rounded"
            style={{ background: "var(--color-brand-50)" }}
          />
          <div
            className="h-4 w-32 animate-pulse rounded"
            style={{ background: "var(--color-brand-50)" }}
          />
          <div
            className="h-4 w-20 animate-pulse rounded"
            style={{ background: "var(--color-brand-50)" }}
          />
          <div className="ml-auto">
            <div
              className="h-5 w-16 animate-pulse rounded-full"
              style={{ background: "var(--color-brand-50)" }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
