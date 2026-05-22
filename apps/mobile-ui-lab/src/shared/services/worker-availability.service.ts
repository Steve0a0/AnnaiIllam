import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type WorkerAvailabilityStatus = 'available' | 'unavailable' | 'leave';

export type WorkerAvailabilityRecord = {
  id: number;
  availability_date: string;
  status: WorkerAvailabilityStatus;
  notes: string | null;
};

export const workerAvailabilityService = {
  list: async (startDate: string, endDate: string) => {
    const res = await http.get<Envelope<WorkerAvailabilityRecord[]>>('/worker/availability', {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    });
    return res.data.data;
  },

  setDay: async (availabilityDate: string, status: WorkerAvailabilityStatus, notes?: string | null) => {
    const res = await http.put<Envelope<WorkerAvailabilityRecord>>('/worker/availability', {
      availability_date: availabilityDate,
      status,
      notes: notes ?? null,
    });
    return res.data.data;
  },
};
