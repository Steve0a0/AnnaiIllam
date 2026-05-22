"use client";

import { useQuery } from "@tanstack/react-query";
import { dashboardService } from "@/services/dashboard.service";

export function useDashboardAlerts() {
  return useQuery({
    queryKey: ["dashboard-alerts"],
    queryFn: dashboardService.getAlerts,
    refetchInterval: 30000,
  });
}
