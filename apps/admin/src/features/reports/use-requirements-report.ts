"use client";

import { useQuery } from "@tanstack/react-query";
import { reportsService } from "@/services/reports.service";
import type { ReportFilters } from "@/types/report";

export function useRequirementsReport(filters: ReportFilters = {}) {
  return useQuery({
    queryKey: ["requirements-report", filters],
    queryFn: () => reportsService.getRequirementsReport(filters),
  });
}
