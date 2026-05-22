import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type WorkerProfilePatch = {
  is_available?: boolean;
  available_days?: string | null;
  available_shifts?: string | null;
};

export type WorkerProfileSummary = {
  id: number;
  is_available: boolean;
  available_days: string | null;
  available_shifts: string | null;
};

export const workerProfileService = {
  getProfile: async (): Promise<WorkerProfileSummary> => {
    const res = await http.get<Envelope<WorkerProfileSummary>>('/worker/profile');
    return res.data.data;
  },

  patch: async (data: WorkerProfilePatch): Promise<WorkerProfileSummary> => {
    const res = await http.patch<Envelope<WorkerProfileSummary>>('/worker/profile', data);
    return res.data.data;
  },
};
