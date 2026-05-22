export default function RequirementsEmpty() {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
      <h3 className="text-lg font-semibold text-slate-900">
        No requirements found
      </h3>
      <p className="mt-2 text-sm text-slate-600">
        Requirement requests will appear here once clients create them.
      </p>
    </div>
  );
}
