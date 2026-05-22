export default function RequirementsLoading() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="h-16 animate-pulse rounded-xl bg-slate-200"
        />
      ))}
    </div>
  );
}
