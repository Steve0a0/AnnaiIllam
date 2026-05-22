"use client";

import { useQuery } from "@tanstack/react-query";
import { payrollService } from "@/services/payroll.service";

export function usePayrollRunDetail(payrollRunId: number) {
  return useQuery({
    queryKey: ["payroll-run-detail", payrollRunId],
    queryFn: () => payrollService.getPayrollRunDetail(payrollRunId),
    enabled: !!payrollRunId,
  });
}
