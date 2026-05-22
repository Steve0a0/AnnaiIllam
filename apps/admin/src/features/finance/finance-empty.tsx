export default function FinanceEmpty({ label }: { label: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">
      No {label} found.
    </div>
  );
}
