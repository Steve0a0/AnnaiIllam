import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type DisputeType = 'attendance' | 'quality' | 'billing' | 'other';
export type DisputeStatus = 'open' | 'under_review' | 'resolved' | 'closed';

export type ClientDispute = {
  id: number;
  requirement_id: number;
  dispute_type: DisputeType;
  description: string;
  status: DisputeStatus;
  resolution_notes: string | null;
  credit_amount: number | null;
  created_at: string;
  updated_at: string;
};

export const clientDisputesService = {
  raise: async (payload: {
    requirement_id: number;
    dispute_type: DisputeType;
    description: string;
  }): Promise<ClientDispute> => {
    const res = await http.post<Envelope<ClientDispute>>('/client/disputes', payload);
    return res.data.data;
  },

};
