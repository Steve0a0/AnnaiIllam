import { useQuery } from "@tanstack/react-query";
import { financeService } from "@/services/finance.service";

export function useRequirementPayments(requirementId: number) {
  return useQuery({
    queryKey: ["requirement-payments", requirementId],
    queryFn: () =>
      financeService.getClientPaymentsByRequirement(requirementId).then((r) => r.data),
    enabled: !!requirementId,
  });
}
