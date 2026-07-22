import type { ApiResponse } from "@/types/api";

export type PrivacyRequestType = "deletion" | "export";
export type PrivacyRequestStatus = "pending" | "in_review" | "completed" | "rejected";

export type PrivacyRequest = {
  id: number;
  user_id: number;
  user_role: "client" | "worker";
  user_name: string | null;
  user_contact: string | null;
  request_type: PrivacyRequestType;
  status: PrivacyRequestStatus;
  reason: string | null;
  resolution_notes: string | null;
  requested_at: string;
  resolved_at: string | null;
  resolved_by_user_id: number | null;
};

export type PrivacyRequestList = {
  items: PrivacyRequest[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type PrivacyRequestListResponse = ApiResponse<PrivacyRequestList>;
export type PrivacyRequestResponse = ApiResponse<PrivacyRequest>;
