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
import { useRequirementsReport } from "@/features/reports/use-requirements-report";
import { reportsService } from "@/services/reports.service";
import type { ReportFilters as ReportFiltersState } from "@/types/report";

const requirementStatusOptions = [
  "draft",
  "submitted",
  "under_review",
  "approved",
  "rejected",
  "workers_assigned",
  "in_progress",
  "completed",
  "cancelled",
].map((status) => ({ label: status.replaceAll("_", " "), value: status }));

export default function RequirementsReportPage() {
  const [filters, setFilters] = useState<ReportFiltersState>({});
  const [exporting, setExporting] = useState(false);
  const { data, isLoading, isError, error } = useRequirementsReport(filters);
  const items = data?.data ?? [];

  async function handleExport() {
    setExporting(true);
    try {
      await reportsService.downloadRequirementsCsv(filters);
    } finally {
      setExporting(false);
    }
  }

  return (
    <ReportTableWrapper
      title="Requirements Report"
      subtitle="View all requirements with key business fields."
      filters={
        <ReportFilters
          filters={filters}
          statusOptions={requirementStatusOptions}
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
        <ReportsEmpty label="requirements report records" />
      ) : null}
      {!isLoading && !isError && items.length ? (
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              ID
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Client
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Category
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              City
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Workers
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
              Start Date
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
                {item.client_id}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.category}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">{item.city}</td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.number_of_workers}
              </td>
              <td className="px-4 py-3 text-sm text-slate-700">
                {item.start_date}
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
