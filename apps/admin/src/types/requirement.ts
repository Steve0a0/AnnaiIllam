export type AdminRequirementListItem = {
  id: number;
  category: string;
  number_of_workers: number;
  city: string;
  status: string;
  start_date: string;
};

export type AdminRequirementListData = {
  items: AdminRequirementListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type AdminRequirementListResponse = {
  success: boolean;
  message: string;
  data: AdminRequirementListData;
};

export type AdminRequirementDetail = {
  id: number;
  client_id: number;
  category: string;
  subcategory: string | null;
  number_of_workers: number;
  work_location: string;
  city: string;
  state: string;
  start_date: string;
  duration_days: number;
  shift_details: string | null;
  food_required: boolean;
  accommodation_required: boolean;
  budget_amount: number | null;
  notes: string | null;
  status: string;
  quote: null | {
    id: number;
    quoted_amount: number;
    rate_per_worker: number | null;
    total_worker_days: number | null;
    advance_amount: number | null;
    payment_model: string;
    valid_until: string | null;
    terms_notes: string | null;
    internal_notes: string | null;
    status: string;
  };
};

export type AdminRequirementDetailResponse = {
  success: boolean;
  message: string;
  data: AdminRequirementDetail;
};

export type CreateQuotePayload = {
  requirement_id: number;
  quoted_amount: number;
  rate_per_worker?: number | null;
  total_worker_days?: number | null;
  advance_amount?: number | null;
  payment_model: string;
  valid_until?: string | null;
  terms_notes?: string | null;
  internal_notes?: string | null;
};

export type MarkReviewResponse = {
  success: boolean;
  message: string;
  data: {
    id: number;
    status: string;
  };
};

export type CreateQuoteResponse = {
  success: boolean;
  message: string;
  data: {
    quote_id: number;
    requirement_id: number;
    quote_status: string;
    requirement_status: string;
  };
};

export type RequirementInterestItem = {
  interest_id: number;
  status: string;
  expressed_at: string;
  worker_profile_id: number;
  worker_user_id: number;
  full_name: string;
  city: string;
  category: string;
  subcategory: string | null;
  verification_status: string;
  is_available: boolean;
};

export type RequirementInterestsResponse = {
  success: boolean;
  message: string;
  data: RequirementInterestItem[];
};
