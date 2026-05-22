export type AssignmentItem = {
  id: number;
  worker_profile_id: number;
  worker_name: string;
  worker_city: string | null;
  worker_category: string | null;
  status: string;
  assigned_role: string | null;
  assigned_shift: string | null;
  salary_amount: number | null;
  notes: string | null;
};

export type GlobalAssignmentItem = {
  id: number;
  requirement_id: number;
  requirement_category: string | null;
  requirement_city: string | null;
  requirement_status: string | null;
  worker_profile_id: number;
  worker_name: string;
  worker_city: string | null;
  status: string;
  assigned_role: string | null;
  assigned_shift: string | null;
  salary_amount: number | null;
  assigned_at: string | null;
};

export type GlobalAssignmentListData = {
  items: GlobalAssignmentItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type GlobalAssignmentListResponse = {
  success: boolean;
  message: string;
  data: GlobalAssignmentListData;
};

export type AssignmentListResponse = {
  success: boolean;
  message: string;
  data: AssignmentItem[];
};

export type CreateAssignmentPayload = {
  requirement_id: number;
  worker_profile_id: number;
  assigned_role?: string | null;
  assigned_shift?: string | null;
  salary_amount?: number | null;
  notes?: string | null;
};

export type CreateAssignmentResponse = {
  success: boolean;
  message: string;
  data: {
    assignment_id: number;
    status: string;
  };
};

export type UpdateAssignmentStatusPayload = {
  status: string;
};

export type UpdateAssignmentStatusResponse = {
  success: boolean;
  message: string;
  data: {
    assignment_id: number;
    status: string;
  };
};

export type WorkerMatch = {
  worker_profile_id: number;
  full_name: string;
  category: string;
  city: string;
  state: string;
  is_available: boolean;
  verification_status: string;
  available_days: string | null;
  available_shifts: string | null;
  score: number;
  reasons: string[];
  has_interest: boolean;
  conflict: null | {
    assignment_id: number;
    requirement_id: number;
    start_date: string;
    duration_days: number;
    status: string;
  };
};

export type WorkerMatchesResponse = {
  success: boolean;
  message: string;
  data: WorkerMatch[];
};
