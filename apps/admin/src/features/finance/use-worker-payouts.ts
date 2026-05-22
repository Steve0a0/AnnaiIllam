"use client";

import { useQuery } from "@tanstack/react-query";
import { financeService } from "@/services/finance.service";

export function useWorkerPayouts(payrollItemId: number) {
  return useQuery({
    queryKey: ["worker-payouts", payrollItemId],
    queryFn: () => financeService.getWorkerPayoutsByPayrollItem(payrollItemId),
    enabled: !!payrollItemId,
  });
}
