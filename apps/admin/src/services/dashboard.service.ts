import { http } from "@/lib/http";
import type { DashboardAlertsResponse, DashboardSummaryResponse } from "@/types/dashboard";

export const dashboardService = {
  getSummary: async (): Promise<DashboardSummaryResponse> => {
    const res = await http.get("/admin/dashboard/summary");
    return res.data;
  },

  getAlerts: async (): Promise<DashboardAlertsResponse> => {
    const res = await http.get("/admin/dashboard/alerts");
    return res.data;
  },
};
