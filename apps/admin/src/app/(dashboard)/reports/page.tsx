import Link from "next/link";

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Reports</h1>
        <p className="mt-1 text-sm text-slate-600">
          Review requirement, assignment, and complaint reports.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Link
          href="/reports/requirements"
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
        >
          <h2 className="text-lg font-semibold text-slate-900">
            Requirements Report
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            View all requirements and statuses.
          </p>
        </Link>

        <Link
          href="/reports/assignments"
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
        >
          <h2 className="text-lg font-semibold text-slate-900">
            Assignments Report
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            View all assignment records.
          </p>
        </Link>

        <Link
          href="/reports/complaints"
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
        >
          <h2 className="text-lg font-semibold text-slate-900">
            Complaints Report
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            View all complaints and issue records.
          </p>
        </Link>
      </div>
    </div>
  );
}
