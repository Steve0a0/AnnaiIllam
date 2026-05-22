export default function PayrollLoading() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, index) => (
        <div
          key={index}
          className="h-16 animate-pulse rounded-xl bg-slate-200"
        />
      ))}
    </div>
  );
}
