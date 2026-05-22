"use client";

import { useQuery } from "@tanstack/react-query";
import { complaintsService } from "@/services/complaints.service";

export function useComplaintDetail(complaintId: number) {
  return useQuery({
    queryKey: ["admin-complaint-detail", complaintId],
    queryFn: () => complaintsService.getComplaintById(complaintId),
    enabled: Number.isFinite(complaintId) && complaintId > 0,
  });
}
