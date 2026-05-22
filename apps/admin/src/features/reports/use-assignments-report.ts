"use client";

import { useQuery } from "@tanstack/react-query";
import { reportsService } from "@/services/reports.service";
import type { ReportFilters } from "@/types/report";

export function useAssignmentsReport(filters: ReportFilters = {}) {
  return useQuery({
    queryKey: ["assignments-report", filters],
    queryFn: () => reportsService.getAssignmentsReport(filters),
  });
}
