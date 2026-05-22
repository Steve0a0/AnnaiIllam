export default function DashboardLoading() {
  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        <div className="h-8 w-72 animate-pulse rounded-lg bg-muted" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-40 animate-pulse rounded-xl bg-muted" />
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <div className="h-96 animate-pulse rounded-xl bg-muted" />
        <div className="h-96 animate-pulse rounded-xl bg-muted" />
      </div>
    </div>
  );
}
