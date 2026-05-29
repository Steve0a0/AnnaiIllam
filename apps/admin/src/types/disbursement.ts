export type DisbursementItem = {
  id: number;
  assignment_id: number;
  worker_profile_id: number;
  amount: number; // paise
  disbursement_status: 'pending' | 'paid' | 'failed';
  scheduled_date: string;
  paid_at: string | null;
  payment_reference: string | null;
  notes: string | null;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
};

export type DisbursementListResponse = {
  success: boolean;
  message: string;
  data: DisbursementItem[];
};

export type DisbursementResponse = {
  success: boolean;
  message: string;
  data: DisbursementItem;
};

export type DisbursementCreatePayload = {
  assignment_id: number;
  amount: number; // paise
  scheduled_date: string;
};
