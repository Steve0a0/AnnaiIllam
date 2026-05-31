/** Skeleton block tinted with brand-50 so it reads as on-brand, not plain gray */
function Bone({ className }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-xl ${className ?? ""}`}
      style={{ background: "var(--color-brand-50)" }}
    />
  );
}

export default function DashboardLoading() {
  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <Bone className="h-4 w-24 rounded" />
        <Bone className="h-8 w-72 rounded-lg" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Bone key={i} className="h-40" />
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <Bone className="h-96" />
        <Bone className="h-96" />
      </div>
    </div>
  );
}
