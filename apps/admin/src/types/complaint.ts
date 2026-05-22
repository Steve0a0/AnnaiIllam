export type ComplaintListItem = {
  id: number;
  requirement_id: number;
  assignment_id: number | null;
  complaint_type: string;
  severity: string;
  status: string;
  created_at: string;
};

export type ComplaintListResponse = {
  success: boolean;
  message: string;
  data: { items: ComplaintListItem[]; page: number; page_size: number; total: number; total_pages: number; };
};

export type ReplacementItem = {
  id: number;
  old_assignment_id: number;
  new_assignment_id: number | null;
  old_worker_profile_id: number;
  new_worker_profile_id: number | null;
  status: string;
  reason: string | null;
};

export type ComplaintDetailResponse = {
  success: boolean;
  message: string;
  data: {
    id: number;
    requirement_id: number;
    assignment_id: number | null;
    raised_by_user_id: number;
    complaint_type: string;
    severity: string;
    description: string;
    status: string;
    resolution_notes: string | null;
    resolved_by_user_id: number | null;
    created_at: string;
    updated_at: string;
    replacements: ReplacementItem[];
  };
};

export type ComplaintStatusUpdatePayload = {
  status: string;
  resolution_notes?: string | null;
};

export type ComplaintStatusUpdateResponse = {
  success: boolean;
  message: string;
  data: {
    complaint_id: number;
    status: string;
  };
};

export type ReplacementListItem = {
  id: number;
  complaint_id: number;
  old_assignment_id: number;
  new_assignment_id: number | null;
  old_worker_profile_id: number;
  new_worker_profile_id: number | null;
  reason: string | null;
  status: string;
  created_by_user_id: number;
  created_at: string;
};

export type ReplacementListResponse = {
  success: boolean;
  message: string;
  data: {
    items: ReplacementListItem[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};

export type ReplacementCreatePayload = {
  complaint_id: number;
  old_assignment_id: number;
  new_worker_profile_id: number;
  reason?: string | null;
};

export type ReplacementCreateResponse = {
  success: boolean;
  message: string;
  data: {
    replacement_id: number;
    old_assignment_id: number;
    new_assignment_id: number;
    status: string;
  };
};

export type ReplacementStatusUpdatePayload = {
  status: string;
};

export type ReplacementStatusUpdateResponse = {
  success: boolean;
  message: string;
  data: {
    replacement_id: number;
    status: string;
  };
};
