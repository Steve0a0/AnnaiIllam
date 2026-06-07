import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type RequirementStatus =
  | 'submitted'
  | 'under_review'
  | 'quoted'
  | 'approved'
  | 'rejected'
  | 'assigned'
  | 'in_progress'
  | 'completed'
  | 'cancelled';

export type ClientRequirementListItem = {
  id: number;
  category: string;
  number_of_workers: number;
  city: string;
  start_date: string;
  status: RequirementStatus;
  pending_balance_amount: number | null;
  has_rated: boolean;
};

export type ClientRequirementDetail = {
  id: number;
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
  status: RequirementStatus;
  rejection_reason: string | null;
  cancellation_reason: string | null;
  assignments: Array<{
    id: number;
    worker_profile_id: number;
    worker_name: string;
    worker_city: string | null;
    worker_category: string | null;
    status: string;
    assigned_role: string | null;
    assigned_shift: string | null;
    assigned_at: string;
    attendance: Array<{
      id: number;
      attendance_date: string;
      status: string;
      check_in_time: string | null;
      check_out_time: string | null;
      notes: string | null;
    }>;
  }>;
  quote: null | {
    id: number;
    quoted_amount: number;
    rate_per_worker: number | null;
    total_worker_days: number | null;
    advance_amount: number | null;
    payment_model: string;
    valid_until: string | null;
    terms_notes: string | null;
    status: string;
  };
};

export type ClientDashboardSummary = {
  total_requirements: number;
  open_jobs: number;
  pending_quotes: number;
  completed_jobs: number;
};

export type CreateRequirementPayload = {
  category: string;
  subcategory?: string | null;
  number_of_workers: number;
  work_location: string;
  city: string;
  state: string;
  site_latitude?: number | null;
  site_longitude?: number | null;
  geofence_radius_meters?: number | null;
  start_date: string;
  duration_days: number;
  shift_details?: string | null;
  food_required: boolean;
  accommodation_required: boolean;
  budget_amount?: number | null;
  notes?: string | null;
};

export const clientRequirementsService = {
  getSummary: async () => {
    const res = await http.get<Envelope<ClientDashboardSummary>>('/client/requirements/summary');
    return res.data.data;
  },

  list: async () => {
    const res = await http.get<Envelope<{ items: ClientRequirementListItem[] }>>('/client/requirements');
    return res.data.data.items;
  },

  getDetail: async (requirementId: number) => {
    const res = await http.get<Envelope<ClientRequirementDetail>>(`/client/requirements/${requirementId}`);
    return res.data.data;
  },

  create: async (payload: CreateRequirementPayload) => {
    const res = await http.post<Envelope<{ id: number; status: RequirementStatus }>>('/client/requirements', payload);
    return res.data.data;
  },

  decideQuote: async (requirementId: number, action: 'approve' | 'reject') => {
    const res = await http.post<Envelope<{
      requirement_id: number;
      requirement_status: RequirementStatus;
      quote_status: string;
    }>>(`/client/requirements/${requirementId}/quote-decision`, { action });
    return res.data.data;
  },

  cancel: async (requirementId: number, reason: string) => {
    const res = await http.post<Envelope<{
      id: number;
      status: RequirementStatus;
      cancellation_reason: string;
    }>>(`/client/requirements/${requirementId}/cancel`, { reason });
    return res.data.data;
  },
};
