"use client";

import { useQuery } from "@tanstack/react-query";
import { reportsService } from "@/services/reports.service";
import type { ReportFilters } from "@/types/report";

export function useComplaintsReport(filters: ReportFilters = {}) {
  return useQuery({
    queryKey: ["complaints-report", filters],
    queryFn: () => reportsService.getComplaintsReport(filters),
  });
}
