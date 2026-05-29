import { http } from "@/lib/http";
import type {
  AttendanceListResponse,
  AttendanceCorrectionPayload,
  AttendanceCorrectionResponse,
  AttendanceApprovalResponse,
  CloseShiftResponse,
} from "@/types/attendance";

export const attendanceService = {
  listAll: async (params?: {
    date?: string;
    requirement_id?: number;
    status?: string;
  }): Promise<AttendanceListResponse> => {
    const res = await http.get("/admin/attendance", { params });
    return res.data;
  },

  getAttendanceByAssignment: async (
    assignmentId: number
  ): Promise<AttendanceListResponse> => {
    const res = await http.get(
      `/admin/attendance/assignment/${assignmentId}`
    );
    return res.data;
  },

  getPendingAttendance: async (
    requirementId: number
  ): Promise<AttendanceListResponse> => {
    const res = await http.get(
      `/admin/attendance/requirement/${requirementId}/pending`
    );
    return res.data;
  },

  approveAttendance: async (
    attendanceId: number
  ): Promise<AttendanceApprovalResponse> => {
    const res = await http.post(`/admin/attendance/${attendanceId}/approve`);
    return res.data;
  },

  rejectAttendance: async (
    attendanceId: number,
    notes: string
  ): Promise<AttendanceApprovalResponse> => {
    const res = await http.post(`/admin/attendance/${attendanceId}/reject`, {
      notes,
    });
    return res.data;
  },

  correctAttendance: async (
    attendanceId: number,
    payload: AttendanceCorrectionPayload
  ): Promise<AttendanceCorrectionResponse> => {
    const res = await http.patch(
      `/admin/attendance/${attendanceId}`,
      payload
    );
    return res.data;
  },

  closeShift: async (
    attendanceId: number,
    notes?: string
  ): Promise<CloseShiftResponse> => {
    const res = await http.post(`/admin/attendance/${attendanceId}/close-shift`, {
      notes: notes ?? null,
    });
    return res.data;
  },
};
