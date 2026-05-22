import { http } from "@/lib/http";
import type {
  ComplaintSlaPoliciesResponse,
  ComplaintSlaPolicyUpdate,
} from "@/types/sla";

export const slaService = {
  getComplaintPolicies: async (): Promise<ComplaintSlaPoliciesResponse> => {
    const res = await http.get("/admin/sla/complaints");
    return res.data;
  },

  updateComplaintPolicy: async (payload: ComplaintSlaPolicyUpdate) => {
    const res = await http.put("/admin/sla/complaints", payload);
    return res.data;
  },
};
