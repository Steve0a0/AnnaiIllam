import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type ComplaintStatus = 'open' | 'under_review' | 'resolved' | 'closed';
export type ComplaintSeverity = 'low' | 'medium' | 'high' | 'urgent';
export type ComplaintType =
  | 'absent'
  | 'behavior'
  | 'performance'
  | 'payment'
  | 'replacement_request'
  | 'other';

export type ClientComplaint = {
  id: number;
  requirement_id: number;
  requirement_category: string;
  assignment_id: number | null;
  complaint_type: ComplaintType;
  severity: ComplaintSeverity;
  description: string;
  status: ComplaintStatus;
  resolution_notes: string | null;
  created_at: string;
};

export type ClientComplaintCreatePayload = {
  requirement_id: number;
  assignment_id?: number | null;
  complaint_type: ComplaintType;
  severity: ComplaintSeverity;
  description: string;
};

export const clientComplaintsService = {
  listAll: async (): Promise<ClientComplaint[]> => {
    const res = await http.get<Envelope<ClientComplaint[]>>('/client/complaints');
    return res.data.data;
  },

  create: async (payload: ClientComplaintCreatePayload): Promise<{ complaint_id: number; status: string }> => {
    const res = await http.post<Envelope<{ complaint_id: number; status: string }>>(
      '/client/complaints',
      payload,
    );
    return res.data.data;
  },
};
