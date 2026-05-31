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
      title="Requirements"
      subtitle="All requirements with key business fields."
      filters={
        <ReportFilters
          filters={filters}
          statusOptions={requirementStatusOptions}
          onChange={setFilters}
        />
      }
      rowCount={items.length}
      actions={
        <Button type="button" variant="secondary" onClick={handleExport} disabled={exporting}>
          <FileDown />
          {exporting ? "Exporting…" : "Export CSV"}
        </Button>
      }
    >
      {isLoading ? <ReportsLoading /> : null}
      {isError ? <ReportsError message={error?.message} /> : null}
      {!isLoading && !isError && !items.length ? (
        <ReportsEmpty label="requirements" />
      ) : null}
      {!isLoading && !isError && items.length ? (
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              {["ID", "Client", "Category", "City", "Workers", "Start Date", "Status"].map((h) => (
                <th
                  key={h}
                  className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.map((item) => (
              <tr key={item.id} className="transition-colors hover:bg-muted/20">
                <td className="px-4 py-3 text-sm tabular-nums text-muted-foreground">{item.id}</td>
                <td className="px-4 py-3 text-sm text-foreground">{item.client_id}</td>
                <td className="px-4 py-3 text-sm text-foreground">{item.category}</td>
                <td className="px-4 py-3 text-sm text-foreground">{item.city}</td>
                <td className="px-4 py-3 text-sm tabular-nums text-foreground">{item.number_of_workers}</td>
                <td className="px-4 py-3 text-sm tabular-nums text-foreground">{item.start_date}</td>
                <td className="px-4 py-3">
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
