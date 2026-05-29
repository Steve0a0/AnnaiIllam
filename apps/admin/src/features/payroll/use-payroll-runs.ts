"use client";

import { useQuery } from "@tanstack/react-query";
import { payrollService } from "@/services/payroll.service";

export function usePayrollRuns() {
  return useQuery({
    queryKey: ["payroll-runs"],
    queryFn: () => payrollService.listPayrollRuns(),
    staleTime: 30_000,
  });
}
