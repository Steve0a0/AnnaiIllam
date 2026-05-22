import { http } from "@/lib/http";
import type {
  ComplaintListResponse,
  ComplaintDetailResponse,
  ComplaintStatusUpdatePayload,
  ComplaintStatusUpdateResponse,
  ReplacementCreatePayload,
  ReplacementCreateResponse,
  ReplacementListResponse,
  ReplacementStatusUpdatePayload,
  ReplacementStatusUpdateResponse,
} from "@/types/complaint";

export const complaintsService = {
  getAllComplaints: async (): Promise<ComplaintListResponse> => {
    const res = await http.get("/admin/complaints");
    return res.data;
  },

  getComplaintById: async (
    complaintId: number,
  ): Promise<ComplaintDetailResponse> => {
    const res = await http.get(`/admin/complaints/${complaintId}`);
    return res.data;
  },

  updateComplaintStatus: async (
    complaintId: number,
    payload: ComplaintStatusUpdatePayload,
  ): Promise<ComplaintStatusUpdateResponse> => {
    const res = await http.patch(
      `/admin/complaints/${complaintId}/status`,
      payload,
    );
    return res.data;
  },

  getAllReplacements: async (status?: string): Promise<ReplacementListResponse> => {
    const res = await http.get("/admin/replacements", {
      params: status ? { status } : {},
    });
    return res.data;
  },

  createReplacement: async (
    payload: ReplacementCreatePayload,
  ): Promise<ReplacementCreateResponse> => {
    const res = await http.post("/admin/replacements", payload);
    return res.data;
  },

  updateReplacementStatus: async (
    replacementId: number,
    payload: ReplacementStatusUpdatePayload,
  ): Promise<ReplacementStatusUpdateResponse> => {
    const res = await http.patch(
      `/admin/replacements/${replacementId}/status`,
      payload,
    );
    return res.data;
  },
};
