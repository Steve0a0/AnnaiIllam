import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type WorkerAssignmentStatus =
  | 'assigned'
  | 'accepted'
  | 'declined'
  | 'active'
  | 'completed'
  | 'cancelled'
  | 'replaced';

export type WorkerAssignment = {
  assignment_id: number;
  status: WorkerAssignmentStatus;
  assigned_role: string | null;
  assigned_shift: string | null;
  salary_amount: number | null;
  notes: string | null;
  start_date: string | null;
  end_date: string | null;
  requirement: null | {
    id: number;
    category: string;
    subcategory: string | null;
    work_location: string;
    city: string;
    state: string;
    start_date: string;
    duration_days: number;
    food_required: boolean;
    accommodation_required: boolean;
  };
};

export const workerAssignmentsService = {
  list: async () => {
    const res = await http.get<Envelope<WorkerAssignment[]>>('/worker/assignments');
    return res.data.data;
  },

  accept: async (assignmentId: number) => {
    const res = await http.post<Envelope<{ assignment_id: number; status: WorkerAssignmentStatus }>>(
      `/worker/assignments/${assignmentId}/acknowledge`,
    );
    return res.data.data;
  },

  decline: async (assignmentId: number) => {
    const res = await http.post<Envelope<{ assignment_id: number; status: WorkerAssignmentStatus }>>(
      `/worker/assignments/${assignmentId}/decline`,
    );
    return res.data.data;
  },
};
