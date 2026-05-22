"use client";

import { useQuery } from "@tanstack/react-query";
import { financeService } from "@/services/finance.service";

export function useClientPayments(requirementId: number) {
  return useQuery({
    queryKey: ["client-payments", requirementId],
    queryFn: () => financeService.getClientPaymentsByRequirement(requirementId),
    enabled: !!requirementId,
  });
}
