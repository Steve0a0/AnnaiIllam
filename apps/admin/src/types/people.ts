export type AdminClient = {
  id: number;
  user_id: number;
  phone: string | null;
  client_type: 'individual' | 'company';
  company_name: string | null;
  contact_name: string;
  city: string;
  state: string;
  gst_number: string | null;
  is_active: boolean;
};

export type AdminClientCreatePayload = {
  phone: string;
  client_type: 'individual' | 'company';
  company_name: string | null;
  contact_name: string;
  city: string;
  state: string;
  gst_number: string | null;
};

export type AdminClientUpdatePayload = {
  client_type?: 'individual' | 'company';
  company_name: string | null;
  contact_name: string;
  city: string;
  state: string;
  gst_number: string | null;
};

export type AdminClientMutationResponse = {
  success: boolean;
  message: string;
  data: AdminClient;
};

export type AdminClientRequirement = {
  id: number;
  category: string;
  subcategory: string | null;
  number_of_workers: number;
  city: string;
  state: string;
  start_date: string;
  duration_days: number;
  status: string;
  created_at: string;
};

export type AdminClientDetail = AdminClient & {
  requirements: AdminClientRequirement[];
};

export type AdminClientDetailResponse = {
  success: boolean;
  message: string;
  data: AdminClientDetail;
};

export type AdminWorker = {
  id: number;
  user_id: number;
  phone: string | null;
  email: string | null;
  onboarding_step: string | null;
  full_name: string;
  category: string;
  subcategory: string | null;
  city: string;
  state: string;
  address: string | null;
  date_of_birth: string | null;
  skills: string | null;
  experience_years: string | null;
  experience_notes: string | null;
  available_days: string | null;
  available_shifts: string | null;
  is_available: boolean;
  verification_status: string;
  submitted_at: string | null;
  photo_url: string | null;
  documents: WorkerReviewDocument[];
};

export type WorkerReviewDocument = {
  id: number;
  document_type: string;
  file_url: string;
  verification_status: string;
  remarks: string | null;
  uploaded_at: string | null;
};

export type WorkerImportItem = {
  phone: string;
  email?: string;
  full_name: string;
  category: string;
  subcategory?: string;
  city: string;
  state: string;
  address?: string;
  date_of_birth?: string;
  skills?: string;
  experience_notes?: string;
};

export type WorkerImportResponse = {
  success: boolean;
  message: string;
  data: {
    created_count: number;
    skipped_count: number;
    created: Array<{ phone: string; user_id: number; worker_profile_id: number }>;
    skipped: Array<{ phone: string; reason: string }>;
  };
};

export type AdminWorkerAssignment = {
  id: number;
  requirement_id: number;
  assigned_role: string | null;
  assigned_shift: string | null;
  salary_amount: number | null;
  status: string;
  assigned_at: string | null;
};

export type AdminWorkerPayrollItem = {
  id: number;
  payroll_run_id: number;
  assignment_id: number;
  gross_amount: number;
  total_deduction_amount: number;
  net_amount: number;
  attendance_days: number;
  payment_status: string;
};

export type AdminWorkerDetail = AdminWorker & {
  assignments: AdminWorkerAssignment[];
  payroll_items: AdminWorkerPayrollItem[];
};

export type AdminWorkerDetailResponse = {
  success: boolean;
  message: string;
  data: AdminWorkerDetail;
};

export type AdminWorkerUpdatePayload = {
  city?: string | null;
  state?: string | null;
  skills?: string | null;
  available_days?: string | null;
  available_shifts?: string | null;
  is_available?: boolean | null;
  phone?: string | null;
  email?: string | null;
};

export type AdminWorkerUpdateResponse = {
  success: boolean;
  message: string;
  data: { worker_profile_id: number };
};

type PaginatedData<T> = { items: T[]; page: number; page_size: number; total: number; total_pages: number; };
export type AdminClientsResponse = { success: boolean; message: string; data: PaginatedData<AdminClient> };
export type AdminWorkersResponse = { success: boolean; message: string; data: PaginatedData<AdminWorker> };
export type WorkerReviewActionResponse = {
  success: boolean;
  message: string;
  data: { user_id: number; onboarding_step: string };
};
export type WorkerDocumentViewUrlResponse = {
  success: boolean;
  message: string;
  data: { mode: "s3" | "local"; url: string | null };
};

export type WorkerAvailabilityToggleResponse = {
  success: boolean;
  message: string;
  data: { user_id: number; is_available: boolean };
};
