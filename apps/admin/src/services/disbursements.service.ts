import { http } from "@/lib/http";

export type DisbursementItem = {
  id: number;
  assignment_id: number;
  worker_profile_id: number;
  amount: number; // paise
  disbursement_status: "pending" | "processing" | "paid" | "failed";
  scheduled_date: string;
  paid_at: string | null;
  payment_reference: string | null;
  notes: string | null;
  created_by_user_id: number;
  created_at: string;
  updated_at: string;
};

type Envelope<T> = { success: boolean; message: string; data: T };

export const disbursementsService = {
  getByRequirement: async (requirementId: number): Promise<DisbursementItem[]> => {
    const res = await http.get<Envelope<DisbursementItem[]>>(
      `/admin/disbursements/requirement/${requirementId}`
    );
    return res.data.data ?? [];
  },

  create: async (payload: {
    assignment_id: number;
    amount: number;
    scheduled_date: string;
  }): Promise<DisbursementItem> => {
    const res = await http.post<Envelope<DisbursementItem>>("/admin/disbursements", payload);
    return res.data.data;
  },

  markPaid: async (
    disbursementId: number,
    paymentReference: string
  ): Promise<DisbursementItem> => {
    const res = await http.patch<Envelope<DisbursementItem>>(
      `/admin/disbursements/${disbursementId}/paid`,
      { payment_reference: paymentReference }
    );
    return res.data.data;
  },

  markFailed: async (
    disbursementId: number,
    notes: string
  ): Promise<DisbursementItem> => {
    const res = await http.patch<Envelope<DisbursementItem>>(
      `/admin/disbursements/${disbursementId}/failed`,
      { notes }
    );
    return res.data.data;
  },
};
