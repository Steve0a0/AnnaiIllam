import { useQuery } from "@tanstack/react-query";
import { financeService } from "@/services/finance.service";

export function usePayrollItemPayouts(payrollItemId: number) {
  return useQuery({
    queryKey: ["payroll-item-payouts", payrollItemId],
    queryFn: () =>
      financeService.getWorkerPayoutsByPayrollItem(payrollItemId).then((r) => r.data),
    enabled: !!payrollItemId,
  });
}
