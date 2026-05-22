"use client";

import StatusBadge from "@/components/shared/status-badge";
import type { ReplacementItem } from "@/types/complaint";

export default function ReplacementsList({
  replacements,
}: {
  replacements: ReplacementItem[];
}) {
  if (!replacements.length) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">
        No replacements created for this complaint yet.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Replacement ID
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Old Assignment
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              New Assignment
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Old Worker
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              New Worker
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Status
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Reason
            </th>
          </tr>
        </thead>

        <tbody className="divide-y divide-slate-100">
          {replacements.map((item) => (
            <tr key={item.id}>
              <td className="px-4 py-3 text-sm text-slate-700">{item.id}</td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.old_assignment_id}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.new_assignment_id ?? "-"}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.old_worker_profile_id}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.new_worker_profile_id ?? "-"}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                <StatusBadge value={item.status} />
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.reason ?? "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
