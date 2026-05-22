"use client";

import { useQuery } from "@tanstack/react-query";
import { assignmentsService } from "@/services/assignments.service";

export function useAllAssignments() {
  return useQuery({
    queryKey: ["all-assignments"],
    queryFn: () => assignmentsService.listAll(),
    staleTime: 30_000,
  });
}
