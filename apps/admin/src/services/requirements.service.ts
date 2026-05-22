import { http } from "@/lib/http";
import type {
  AdminRequirementListResponse,
  AdminRequirementDetailResponse,
  CreateQuotePayload,
  CreateQuoteResponse,
  MarkReviewResponse,
  RequirementInterestsResponse,
} from "@/types/requirement";

export const requirementsService = {
  getAllRequirements: async (): Promise<AdminRequirementListResponse> => {
    const res = await http.get("/admin/requirements");
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
};
