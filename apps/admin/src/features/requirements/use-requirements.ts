"use client";

import { useQuery } from "@tanstack/react-query";
import { requirementsService } from "@/services/requirements.service";

export function useRequirements() {
  return useQuery({
    queryKey: ["admin-requirements"],
    queryFn: requirementsService.getAllRequirements,
  });
}
