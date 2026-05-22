import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type JobMatchTier = 'best' | 'nearby' | 'other';

export type OpenJob = {
  requirement_id: number;
  category: string;
  subcategory: string | null;
  work_location: string;
  city: string;
  state: string;
  start_date: string;
  duration_days: number;
  number_of_workers: number;
  shift_details: string | null;
  food_required: boolean;
  accommodation_required: boolean;
  score: number;
  match_reasons: string[];
  match_tier: JobMatchTier;
  my_interest: 'interested' | 'withdrawn' | null;
};

export const workerJobsService = {
  getOpenJobs: async (): Promise<OpenJob[]> => {
    const res = await http.get<Envelope<OpenJob[]>>('/worker/jobs/open');
    return res.data.data;
  },

  expressInterest: async (requirementId: number): Promise<void> => {
    await http.post(`/worker/jobs/${requirementId}/interest`);
  },

  withdrawInterest: async (requirementId: number): Promise<void> => {
    await http.post(`/worker/jobs/${requirementId}/withdraw`);
  },
};
