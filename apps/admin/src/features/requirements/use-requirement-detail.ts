"use client";

import { useQuery } from "@tanstack/react-query";
import { requirementsService } from "@/services/requirements.service";

export function useRequirementDetail(requirementId: number) {
  return useQuery({
    queryKey: ["admin-requirement-detail", requirementId],
    queryFn: () => requirementsService.getRequirementById(requirementId),
    enabled: !!requirementId,
  });
}
