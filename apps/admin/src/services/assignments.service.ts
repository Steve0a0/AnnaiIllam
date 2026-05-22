import { http } from "@/lib/http";
import type {
  AssignmentListResponse,
  CreateAssignmentPayload,
  CreateAssignmentResponse,
  GlobalAssignmentListResponse,
  UpdateAssignmentStatusPayload,
  UpdateAssignmentStatusResponse,
  WorkerMatchesResponse,
} from "@/types/assignment";

export const assignmentsService = {
  listAll: async (): Promise<GlobalAssignmentListResponse> => {
    const res = await http.get("/admin/assignments");
    return res.data;
  },

  getAssignmentsByRequirement: async (
    requirementId: number
  ): Promise<AssignmentListResponse> => {
    const res = await http.get(
      `/admin/assignments/requirement/${requirementId}`
    );
    return res.data;
  },

  createAssignment: async (
    payload: CreateAssignmentPayload,
    skipPaymentCheck = false
  ): Promise<CreateAssignmentResponse> => {
    const res = await http.post("/admin/assignments", payload, {
      params: skipPaymentCheck ? { skip_payment_check: true } : undefined,
    });
    return res.data;
  },

  updateAssignmentStatus: async (
    assignmentId: number,
    payload: UpdateAssignmentStatusPayload
  ): Promise<UpdateAssignmentStatusResponse> => {
    const res = await http.patch(
      `/admin/assignments/${assignmentId}/status`,
      payload
    );
    return res.data;
  },

  getWorkerMatches: async (requirementId: number): Promise<WorkerMatchesResponse> => {
    const res = await http.get(`/admin/assignments/requirement/${requirementId}/matches`);
    return res.data;
  },
};
