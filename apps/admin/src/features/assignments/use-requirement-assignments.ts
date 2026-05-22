"use client";

import { useQuery } from "@tanstack/react-query";
import { assignmentsService } from "@/services/assignments.service";

export function useRequirementAssignments(requirementId: number) {
  return useQuery({
    queryKey: ["requirement-assignments", requirementId],
    queryFn: () =>
      assignmentsService.getAssignmentsByRequirement(requirementId),
    enabled: !!requirementId,
  });
}
