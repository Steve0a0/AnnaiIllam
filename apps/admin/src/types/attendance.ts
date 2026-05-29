export type AttendanceItem = {
  id: number;
  assignment_id: number;
  requirement_id: number | null;
  worker_profile_id: number;
  worker_name: string;
  attendance_date: string;
  status: string;
  check_in_time: string | null;
  check_out_time: string | null;
  notes: string | null;
  approval_status: string | null;
  approval_notes: string | null;
};

/** @deprecated requirement_id is now in AttendanceItem directly */
export type EnrichedAttendanceItem = AttendanceItem;

export type AttendanceListResponse = {
  success: boolean;
  message: string;
  data: AttendanceItem[];
};

export type AttendanceCorrectionPayload = {
  status: string;
  notes?: string | null;
};

export type AttendanceCorrectionResponse = {
  success: boolean;
  message: string;
  data: {
    attendance_id: number;
    status: string;
  };
};

export type AttendanceApprovalResponse = {
  success: boolean;
  message: string;
  data: {
    attendance_id: number;
    approval_status: string;
    approval_notes?: string | null;
    approved_by_user_id?: number | null;
    approved_at?: string | null;
  };
};

export type CloseShiftResponse = {
  success: boolean;
  message: string;
  data: {
    attendance_id: number;
    check_out_time: string;
  };
};
