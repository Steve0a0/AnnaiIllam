import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };
type PaginatedEnvelope<T> = Envelope<{ items: T[]; total: number; page: number; limit: number; pages: number }>;

export type WorkerAttendanceStatus =
  | 'present'
  | 'absent'
  | 'half_day'
  | 'late'
  | 'approved'
  | 'corrected';

export type WorkerAttendanceRecord = {
  id: number;
  assignment_id: number;
  attendance_date: string;
  status: WorkerAttendanceStatus;
  check_in_time: string | null;
  check_out_time: string | null;
  check_in_latitude: number | null;
  check_in_longitude: number | null;
  check_out_latitude: number | null;
  check_out_longitude: number | null;
  check_in_selfie_url: string | null;
  check_out_selfie_url: string | null;
  qr_code: string | null;
  notes: string | null;
};

export type AttendanceActionPayload = {
  assignment_id: number;
  latitude?: number | null;
  longitude?: number | null;
  notes?: string | null;
  selfie_url?: string | null;
  selfie_token?: string | null;
  qr_code?: string | null;
};

export const workerAttendanceService = {
  list: async () => {
    const res = await http.get<PaginatedEnvelope<WorkerAttendanceRecord>>('/worker/attendance');
    return res.data.data.items;
  },

  getSelfieToken: async (): Promise<string> => {
    const res = await http.post<Envelope<{ selfie_token: string; expires_in_seconds: number }>>(
      '/worker/attendance/selfie-token',
    );
    return res.data.data.selfie_token;
  },

  checkIn: async (payload: AttendanceActionPayload) => {
    const res = await http.post<Envelope<WorkerAttendanceRecord>>(
      '/worker/attendance/check-in',
      payload,
    );
    return res.data.data;
  },

  checkOut: async (payload: AttendanceActionPayload) => {
    const res = await http.post<Envelope<WorkerAttendanceRecord>>(
      '/worker/attendance/check-out',
      payload,
    );
    return res.data.data;
  },
};
