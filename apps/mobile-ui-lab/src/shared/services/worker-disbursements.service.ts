import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type WorkerDisbursement = {
  id: number;
  assignment_id: number;
  worker_profile_id: number;
  amount: number; // paise
  disbursement_status: 'pending' | 'processing' | 'paid' | 'failed';
  scheduled_date: string;
  paid_at: string | null;
  payment_reference: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

type DisbursementsPage = {
  items: WorkerDisbursement[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export const workerDisbursementsService = {
  list: async (page = 1, pageSize = 20): Promise<DisbursementsPage> => {
    const res = await http.get<Envelope<DisbursementsPage>>(
      `/worker/disbursements?page=${page}&page_size=${pageSize}`
    );
    return res.data.data;
  },
};
