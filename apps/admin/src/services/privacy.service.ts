import { http } from "@/lib/http";
import type {
  PrivacyRequestListResponse,
  PrivacyRequestResponse,
  PrivacyRequestStatus,
  PrivacyRequestType,
} from "@/types/privacy";

export const privacyService = {
  list: async (filters?: {
    status?: PrivacyRequestStatus;
    requestType?: PrivacyRequestType;
  }): Promise<PrivacyRequestListResponse> => {
    const response = await http.get("/admin/privacy-requests", {
      params: {
        status: filters?.status,
        request_type: filters?.requestType,
        page_size: 200,
      },
    });
    return response.data;
  },

  resolve: async (
    requestId: number,
    payload: { status: "in_review" | "completed" | "rejected"; resolution_notes?: string },
  ): Promise<PrivacyRequestResponse> => {
    const response = await http.patch(`/admin/privacy-requests/${requestId}`, payload);
    return response.data;
  },
};
