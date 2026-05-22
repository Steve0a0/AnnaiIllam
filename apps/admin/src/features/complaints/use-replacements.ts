"use client";

import { useQuery } from "@tanstack/react-query";
import { complaintsService } from "@/services/complaints.service";

export function useReplacements(status?: string) {
  return useQuery({
    queryKey: ["replacements", status],
    queryFn: () => complaintsService.getAllReplacements(status),
  });
}
