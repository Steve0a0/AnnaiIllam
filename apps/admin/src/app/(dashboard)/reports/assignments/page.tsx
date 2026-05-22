"use client";

import { useState } from "react";
import { FileDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import ReportTableWrapper from "@/features/reports/report-table-wrapper";
import ReportFilters from "@/features/reports/report-filters";
import ReportsLoading from "@/features/reports/reports-loading";
import ReportsError from "@/features/reports/reports-error";
import ReportsEmpty from "@/features/reports/reports-empty";
import StatusBadge from "@/components/shared/status-badge";
import { useAssignmentsReport } from "@/features/reports/use-assignments-report";
import { reportsService } from "@/services/reports.service";
import { formatCurrency } from "@/lib/format-currency";
import type { ReportFilters as ReportFiltersState } from "@/types/report";

const assignmentStatusOptions = [
  "assigned",
  "accepted",
  "declined",
  "replaced",
  "completed",
].map((status) => ({ label: status.replaceAll("_", " "), value: status }));

export default function AssignmentsReportPage() {
  const [filters, setFilters] = useState<ReportFiltersState>({});
  const [exporting, setExporting] = useState(false);
  const { data, isLoading, isError, error } = useAssignmentsReport(filters);
  const items = data?.data ?? [];

  async function handleExport() {
    setExporting(true);
    try {
      await reportsService.downloadAssignmentsCsv(filters);
    } finally {
      setExporting(false);
    }
  }

  return (
    <ReportTableWrapper
      title="Assignments Report"
      subtitle="View all active assignment records."
      filters={
        <ReportFilters
          filters={filters}
          statusOptions={assignmentStatusOptions}
          onChange={setFilters}
        />
      }
      rowCount={items.length}
      actions={
        <Button
          type="button"
          variant="secondary"
          onClick={handleExport}
          disabled={exporting}
        >
          <FileDown />
          {exporting ? "Exporting…" : "Export CSV"}
        </Button>
      }
    >
      {isLoading ? <ReportsLoading /> : null}
      {isError ? <ReportsError message={error?.message} /> : null}
      {!isLoading && !isError && !items.length ? (
        <ReportsEmpty label="assignments report records" />
      ) : null}
      {!isLoading && !isError && items.length ? (
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              ID
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Requirement
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Worker
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Role
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Shift
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Salary
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Status
            </th>
          </tr>
        </thead>

        <tbody className="divide-y divide-slate-100">
          {items.map((item) => (
            <tr key={item.id}>
              <td className="px-4 py-3 text-sm text-slate-700">{item.id}</td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.requirement_id}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.worker_profile_id}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.assigned_role ?? "-"}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.assigned_shift ?? "-"}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.salary_amount != null
                  ? formatCurrency(item.salary_amount)
                  : "-"}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                <StatusBadge value={item.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      ) : null}
    </ReportTableWrapper>
  );
}
