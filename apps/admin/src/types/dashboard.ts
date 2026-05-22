export type DashboardSummaryData = {
  requirements: { total: number; open: number };
  assignments: { total: number; active: number };
  workers: { total: number; available: number };
  complaints: { total: number; open: number };
  attendance: { total_records: number; present: number; absent: number };
  payroll: { runs: number; items: number };
  finance: {
    client_payments_count: number;
    worker_payouts_count: number;
    client_paid_total: number;
    worker_paid_total: number;
  };
};

export type DashboardSummaryResponse = {
  success: boolean;
  message: string;
  data: DashboardSummaryData;
};

export type DashboardAlertsData = {
  overdue_complaints: Array<{
    id: number;
    requirement_id: number;
    severity: string;
    status: string;
    created_at: string;
    age_hours: number;
  }>;
  missing_attendance: Array<{
    assignment_id: number;
    worker_profile_id: number;
    requirement_id: number;
    status: string;
  }>;
  unpaid_invoices: Array<{
    requirement_id: number;
    client_id: number;
    pending_amount: number;
    status: string;
  }>;
};

export type DashboardAlertsResponse = {
  success: boolean;
  message: string;
  data: DashboardAlertsData;
};

/** Legacy — kept for compatibility */
export type DashboardMetric = { label: string; value: number | string };
export type DashboardStats = {
  open_requirements: number;
  active_assignments: number;
  open_complaints: number;
  payroll_runs: number;
};
