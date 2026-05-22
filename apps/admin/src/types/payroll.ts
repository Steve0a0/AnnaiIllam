export type PayrollRunCreatePayload = {
  period_start: string;
  period_end: string;
  notes?: string | null;
};

export type PayrollRunCreateResponse = {
  success: boolean;
  message: string;
  data: {
    payroll_run_id: number;
    status: string;
  };
};

export type PayrollRunStatusUpdatePayload = {
  status: string;
};

export type PayrollRunStatusUpdateResponse = {
  success: boolean;
  message: string;
  data: {
    payroll_run_id: number;
    status: string;
  };
};

export type PayrollDeductionCreatePayload = {
  payroll_item_id: number;
  deduction_type: string;
  amount: number;
  reason?: string | null;
};

export type PayrollDeductionCreateResponse = {
  success: boolean;
  message: string;
  data: {
    payroll_item_id: number;
    total_deduction_amount: number;
    net_amount: number;
  };
};

export type PayrollDeductionItem = {
  id: number;
  deduction_type: string;
  amount: number;
  reason: string | null;
};

export type PayrollItem = {
  id: number;
  assignment_id: number;
  worker_profile_id: number;
  gross_amount: number;
  total_deduction_amount: number;
  net_amount: number;
  attendance_days: number;
  half_days: number;
  absent_days: number;
  payment_status: string;
  deductions: PayrollDeductionItem[];
};

export type PayrollRunDetailResponse = {
  success: boolean;
  message: string;
  data: {
    payroll_run: {
      id: number;
      period_start: string;
      period_end: string;
      status: string;
      notes: string | null;
    };
    items: PayrollItem[];
  };
};
