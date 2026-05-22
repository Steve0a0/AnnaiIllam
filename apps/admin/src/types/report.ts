export type ReportFilters = {
  from_date?: string;
  to_date?: string;
  status?: string;
};

export type RequirementReportItem = {
  id: number;
  client_id: number;
  category: string;
  city: string;
  number_of_workers: number;
  status: string;
  start_date: string;
};

export type RequirementReportResponse = {
  success: boolean;
  message: string;
  data: RequirementReportItem[];
};

export type AssignmentReportItem = {
  id: number;
  requirement_id: number;
  worker_profile_id: number;
  status: string;
  assigned_role: string | null;
  assigned_shift: string | null;
  salary_amount: number | null;
};

export type AssignmentReportResponse = {
  success: boolean;
  message: string;
  data: AssignmentReportItem[];
};

export type ComplaintReportItem = {
  id: number;
  requirement_id: number;
  assignment_id: number | null;
  complaint_type: string;
  severity: string;
  status: string;
  created_at: string;
};

export type ComplaintReportResponse = {
  success: boolean;
  message: string;
  data: ComplaintReportItem[];
};
