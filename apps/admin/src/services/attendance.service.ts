import { http } from "@/lib/http";
import type {
  AttendanceListResponse,
  AttendanceCorrectionPayload,
  AttendanceCorrectionResponse,
} from "@/types/attendance";

export const attendanceService = {
  getAttendanceByAssignment: async (
    assignmentId: number
  ): Promise<AttendanceListResponse> => {
    const res = await http.get(
      `/admin/attendance/assignment/${assignmentId}`
    );
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
};
