import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type WorkerIssueStatus = 'open' | 'in_review' | 'resolved' | 'closed';

export type WorkerIssue = {
  id: number;
  assignment_id: number | null;
  issue_type: string;
  description: string;
  status: WorkerIssueStatus;
  resolution_notes: string | null;
  created_at: string;
};

export type WorkerIssueCreatePayload = {
  assignment_id?: number | null;
  issue_type: string;
  description: string;
};

export const workerIssuesService = {
  list: async (): Promise<WorkerIssue[]> => {
    const res = await http.get<Envelope<WorkerIssue[]>>('/worker/issues');
    return res.data.data;
  },

  create: async (payload: WorkerIssueCreatePayload): Promise<{ id: number; status: string }> => {
    const res = await http.post<Envelope<{ id: number; status: string }>>(
      '/worker/issues',
      payload,
    );
    return res.data.data;
  },
};
