export type PayrollRunListItem = {
  id: number;
  period_start: string;
  period_end: string;
  status: string;
  notes: string | null;
  require_verified_attendance: boolean;
  created_at: string;
};

export type PayrollRunCreatePayload = {
  period_start: string;
  period_end: string;
  notes?: string | null;
  require_verified_attendance?: boolean;
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

export type PayrollWarning = {
  code: string;
  message: string;
};

export type PayrollDeductionCreateResponse = {
  success: boolean;
  message: string;
  data: {
    deduction_id: number;
    payroll_item_id: number;
    total_deduction_amount: number;
    net_amount: number;
    warning: PayrollWarning | null;
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
  platform_margin: number | null;
  is_stale: boolean;
  deductions: PayrollDeductionItem[];
};

export type RecalculatePayrollItemResponse = {
  success: boolean;
  message: string;
  data: PayrollItem;
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
      require_verified_attendance: boolean;
    };
    items: PayrollItem[];
  };
};
