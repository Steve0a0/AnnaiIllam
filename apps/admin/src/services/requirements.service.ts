import { http } from "@/lib/http";
import type {
  AdminRequirementListResponse,
  AdminRequirementDetailResponse,
  CancelRequirementResponse,
  CreateQuotePayload,
  CreateQuoteResponse,
  MarkCompleteResponse,
  MarkReviewResponse,
  RejectRequirementResponse,
  RequirementInterestsResponse,
  WorkerPaymentsResponse,
  WorkerPaymentRecordPayload,
} from "@/types/requirement";

export const requirementsService = {
  getAllRequirements: async (page = 1, pageSize = 200): Promise<AdminRequirementListResponse> => {
    const res = await http.get("/admin/requirements", { params: { page, page_size: pageSize } });
    return res.data;
  },

  getRequirementById: async (
    requirementId: number
  ): Promise<AdminRequirementDetailResponse> => {
    const res = await http.get(`/admin/requirements/${requirementId}`);
    return res.data;
  },

  markRequirementUnderReview: async (
    requirementId: number
  ): Promise<MarkReviewResponse> => {
    const res = await http.post(
      `/admin/requirements/${requirementId}/mark-review`
    );
    return res.data;
  },

  markRequirementComplete: async (
    requirementId: number
  ): Promise<MarkCompleteResponse> => {
    const res = await http.post(
      `/admin/requirements/${requirementId}/complete`
    );
    return res.data;
  },

  createQuote: async (
    requirementId: number,
    payload: CreateQuotePayload
  ): Promise<CreateQuoteResponse> => {
    const res = await http.post(
      `/admin/requirements/${requirementId}/quote`,
      payload
    );
    return res.data;
  },

  getRequirementInterests: async (
    requirementId: number
  ): Promise<RequirementInterestsResponse> => {
    const res = await http.get(`/admin/requirements/${requirementId}/interests`);
    return res.data;
  },

  getWorkerPayments: async (
    requirementId: number
  ): Promise<WorkerPaymentsResponse> => {
    const res = await http.get(
      `/admin/requirements/${requirementId}/worker-payments`
    );
    return res.data;
  },

  recordWorkerPayment: async (
    requirementId: number,
    payload: WorkerPaymentRecordPayload
  ) => {
    const res = await http.post(
      `/admin/requirements/${requirementId}/worker-payments`,
      payload
    );
    return res.data;
  },

  rejectRequirement: async (
    requirementId: number,
    reason: string
  ): Promise<RejectRequirementResponse> => {
    const res = await http.post(
      `/admin/requirements/${requirementId}/reject`,
      { reason }
    );
    return res.data;
  },

  cancelRequirement: async (
    requirementId: number,
    reason: string
  ): Promise<CancelRequirementResponse> => {
    const res = await http.post(
      `/admin/requirements/${requirementId}/cancel`,
      { reason }
    );
    return res.data;
  },

  requestExtension: async (
    requirementId: number,
    additionalDays: number,
    newRatePerWorker: number
  ) => {
    const res = await http.post(
      `/admin/requirements/${requirementId}/request-extension`,
      { additional_days: additionalDays, new_rate_per_worker: newRatePerWorker }
    );
    return res.data;
  },
};
