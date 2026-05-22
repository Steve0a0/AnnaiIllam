export type AttendanceItem = {
  id: number;
  worker_profile_id: number;
  attendance_date: string;
  status: string;
  check_in_time: string | null;
  check_out_time: string | null;
  notes: string | null;
};

export type EnrichedAttendanceItem = AttendanceItem & {
  worker_name: string;
  assignment_id: number;
  requirement_id: number | null;
};

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
