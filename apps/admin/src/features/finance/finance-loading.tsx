export default function FinanceLoading() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="h-16 animate-pulse rounded-xl bg-slate-100"
        />
      ))}
    </div>
  );
}
