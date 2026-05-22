import { http } from "@/lib/http";
import type { AuditLogResponse } from "@/types/audit";

export const auditService = {
  getAuditLogs: async (limit = 100): Promise<AuditLogResponse> => {
    const res = await http.get(`/admin/audit?limit=${limit}`);
    return res.data;
  },
};
