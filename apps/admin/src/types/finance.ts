export type ManualClientPaymentPayload = {
  requirement_id: number;
  amount: number;
  payment_model: string;
  payment_mode: string;
  payment_status: string;
  reference_note?: string | null;
};

export type ManualClientPaymentResponse = {
  success: boolean;
  message: string;
  data: {
    payment_id: number;
    status: string;
  };
};

/** Richer record returned by GET /admin/finance/client-payments */
export type AdminClientPaymentRecord = {
  id: number;
  client_id: number;
  client_name: string;
  requirement_id: number;
  requirement_category: string | null;
  requirement_city: string | null;
  requirement_state: string | null;
  amount: number;
  payment_model: string;
  payment_mode: string;
  payment_status: "pending" | "paid" | "failed" | "refunded";
  is_advance: boolean;
  gateway_order_id: string | null;
  gateway_payment_id: string | null;
  reference_note: string | null;
  paid_at: string | null;
  created_at: string | null;
};

export type AdminClientPaymentsListResponse = {
  success: boolean;
  message: string;
  data: AdminClientPaymentRecord[];
};

export type UpdateClientPaymentStatusPayload = {
  payment_status: string;
};

export type UpdateClientPaymentStatusResponse = {
  success: boolean;
  message: string;
  data: {
    payment_id: number;
    status: string;
    requirement_auto_transitioned: boolean;
    new_requirement_status: string | null;
  };
};

export type ClientPaymentItem = {
  id: number;
  amount: number;
  payment_model: string;
  payment_mode: string;
  payment_status: string;
  gateway_order_id: string | null;
  gateway_payment_id: string | null;
  reference_note: string | null;
  paid_at: string | null;
};

export type ClientPaymentsListResponse = {
  success: boolean;
  message: string;
  data: ClientPaymentItem[];
};

export type WorkerPayoutCreatePayload = {
  payroll_item_id: number;
  amount: number;
  payout_mode: string;
  transaction_reference?: string | null;
  notes?: string | null;
};

export type WorkerPayoutCreateResponse = {
  success: boolean;
  message: string;
  data: {
    payout_id: number;
    status: string;
  };
};

export type WorkerPayoutItem = {
  id: number;
  payroll_item_id: number;
  worker_profile_id: number;
  amount: number;
  payout_mode: string;
  payout_status: string;
  transaction_reference: string | null;
  notes: string | null;
  paid_at: string | null;
};

export type WorkerPayoutListResponse = {
  success: boolean;
  message: string;
  data: WorkerPayoutItem[];
};

export type WorkerPayoutStatusUpdatePayload = {
  payout_status: string;
};

export type WorkerPayoutStatusUpdateResponse = {
  success: boolean;
  message: string;
  data: {
    payout_id: number;
    status: string;
  };
};

// ─── Payroll Queue ─────────────────────────────────────────────────────────────

export type PayrollQueueDeduction = {
  deduction_type: string;
  amount: number;
  reason: string | null;
};

export type PayrollQueueItem = {
  payroll_item_id: number;
  assignment_id: number;
  worker_profile_id: number;
  worker_name: string;
  gross_amount: number;
  total_deduction_amount: number;
  net_amount: number;
  attendance_days: number;
  half_days: number;
  payment_status: string;
  deductions: PayrollQueueDeduction[];
};

export type PayrollQueueRun = {
  payroll_run_id: number;
  period_start: string;
  period_end: string;
  status: string;
  notes: string | null;
  items: PayrollQueueItem[];
};

export type PayrollQueueResponse = {
  success: boolean;
  message: string;
  data: PayrollQueueRun[];
};

export type MarkRunPaidPayload = {
  payout_mode: string;
};

export type MarkRunPaidResponse = {
  success: boolean;
  message: string;
  data: {
    payroll_run_id: number;
    status: string;
    payouts_created: number;
  };
};
