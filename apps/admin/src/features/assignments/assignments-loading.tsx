export default function AssignmentsLoading() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, index) => (
        <div
          key={index}
          className="h-14 animate-pulse rounded-xl bg-slate-200"
        />
      ))}
    </div>
  );
}
