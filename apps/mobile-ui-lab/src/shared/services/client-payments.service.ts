import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type ClientPaymentRecord = {
  id: number;
  amount: number;
  payment_model: string;
  payment_mode: string;
  payment_status: 'pending' | 'pending_verification' | 'paid' | 'failed' | 'refunded';
  gateway_order_id: string | null;
  gateway_payment_id: string | null;
  reference_note: string | null;
  paid_at: string | null;
  created_at: string;
};

export type ClientPaymentSummary = ClientPaymentRecord & {
  requirement_id: number;
  job_name: string | null;
  location: string | null;
  duration_days: number | null;
};

export type SubmitReferencePayload = {
  requirement_id: number;
  amount: number;
  payment_mode: 'upi' | 'neft';
  reference_note: string;
};

export type CreateOrderPayload = {
  requirement_id: number;
  amount: number;
  payment_model: string;
  reference_note?: string;
};

export type CreateOrderResponse = {
  payment_id: number;
  gateway_order_id: string;
  amount: number;
  amount_paise: number;
  currency: string;
  razorpay_key_id: string;
  status: string;
};

export type VerifyPaymentPayload = {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
};

export const clientPaymentsService = {
  /** List all payments for the current client. GET /client/payments */
  async listAll(): Promise<ClientPaymentSummary[]> {
    const res = await http.get<Envelope<ClientPaymentSummary[]>>('/client/payments');
    return res.data.data;
  },

  /** List all payment records for a requirement. GET /client/payments/requirement/{id} */
  async listForRequirement(requirementId: number): Promise<ClientPaymentRecord[]> {
    const res = await http.get<Envelope<ClientPaymentRecord[]>>(
      `/client/payments/requirement/${requirementId}`,
    );
    return res.data.data;
  },

  /** Submit a UTR/UPI ref after an out-of-app transfer. POST /client/payments/submit-reference */
  async submitReference(payload: SubmitReferencePayload): Promise<{ payment_id: number }> {
    const res = await http.post<Envelope<{ payment_id: number }>>(
      '/client/payments/submit-reference',
      payload,
    );
    return res.data.data;
  },

  /** Create a Razorpay order. POST /client/payments/create-order */
  async createOrder(payload: CreateOrderPayload): Promise<CreateOrderResponse> {
    const res = await http.post<Envelope<CreateOrderResponse>>(
      '/client/payments/create-order',
      payload,
    );
    return res.data.data;
  },

  /** Verify a completed Razorpay checkout. POST /client/payments/verify */
  async verifyPayment(payload: VerifyPaymentPayload): Promise<{ payment_id: number }> {
    const res = await http.post<Envelope<{ payment_id: number }>>(
      '/client/payments/verify',
      payload,
    );
    return res.data.data;
  },
};
