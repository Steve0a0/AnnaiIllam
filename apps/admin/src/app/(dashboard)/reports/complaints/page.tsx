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
import { useComplaintsReport } from "@/features/reports/use-complaints-report";
import { reportsService } from "@/services/reports.service";
import type { ReportFilters as ReportFiltersState } from "@/types/report";

const complaintStatusOptions = ["open", "under_review", "resolved", "closed"].map(
  (status) => ({ label: status.replaceAll("_", " "), value: status }),
);

export default function ComplaintsReportPage() {
  const [filters, setFilters] = useState<ReportFiltersState>({});
  const [exporting, setExporting] = useState(false);
  const { data, isLoading, isError, error } = useComplaintsReport(filters);
  const items = data?.data ?? [];

  async function handleExport() {
    setExporting(true);
    try {
      await reportsService.downloadComplaintsCsv(filters);
    } finally {
      setExporting(false);
    }
  }

  return (
    <ReportTableWrapper
      title="Complaints Report"
      subtitle="View complaint records with severity and status."
      filters={
        <ReportFilters
          filters={filters}
          statusOptions={complaintStatusOptions}
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
        <ReportsEmpty label="complaints report records" />
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
              Assignment
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Type
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Severity
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Status
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Created At
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
                {item.assignment_id ?? "-"}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.complaint_type.replaceAll("_", " ")}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                <StatusBadge value={item.severity} />
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                <StatusBadge value={item.status} />
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.created_at}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      ) : null}
    </ReportTableWrapper>
  );
}
