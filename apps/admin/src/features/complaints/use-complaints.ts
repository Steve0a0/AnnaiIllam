"use client";

import { useQuery } from "@tanstack/react-query";
import { complaintsService } from "@/services/complaints.service";

export function useComplaints() {
  return useQuery({
    queryKey: ["admin-complaints"],
    queryFn: complaintsService.getAllComplaints,
  });
}
