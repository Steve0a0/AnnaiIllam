import { http } from "@/lib/http";
import type {
  AssignmentListResponse,
  CreateAssignmentPayload,
  CreateAssignmentResponse,
  GlobalAssignmentListResponse,
  ReplaceWorkerResponse,
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
    payload: CreateAssignmentPayload
  ): Promise<CreateAssignmentResponse> => {
    const res = await http.post("/admin/assignments", payload);
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

  replaceWorker: async (
    assignmentId: number,
    newWorkerProfileId: number,
    reason: string,
  ): Promise<ReplaceWorkerResponse> => {
    const res = await http.post(`/admin/assignments/${assignmentId}/replace`, {
      new_worker_profile_id: newWorkerProfileId,
      reason,
    });
    return res.data;
  },

  getCoverageCalendar: async (requirementId: number): Promise<CoverageCalendarResponse> => {
    const res = await http.get(`/admin/assignments/requirement/${requirementId}/coverage`);
    return res.data;
  },
};

export type CoverageDay = {
  date: string;
  covering_count: number;
  confirmed_count: number;
  checked_in_count: number;
  required: number;
  coverage_status: "full" | "partial" | "uncovered";
  workers: { assignment_id: number; worker_profile_id: number; worker_name: string; status: string }[];
};

export type CoverageCalendarResponse = {
  success: boolean;
  message: string;
  data: {
    requirement_id: number;
    start_date: string;
    end_date: string;
    duration_days: number;
    required_per_day: number;
    days: CoverageDay[];
  };
};
