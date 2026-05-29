import { http } from "@/lib/http";

export type DisputeItem = {
  id: number;
  requirement_id: number;
  raised_by_user_id: number;
  dispute_type: string;
  description: string;
  status: 'open' | 'under_review' | 'resolved' | 'closed';
  resolution_notes: string | null;
  resolved_by_user_id: number | null;
  resolved_at: string | null;
  credit_amount: number | null;
  created_at: string;
  updated_at: string;
};

type Envelope<T> = { success: boolean; message: string; data: T };
type Page<T> = { items: T[]; total: number; page: number; limit: number; pages: number };

export const disputesService = {
  list: async (status?: string): Promise<{ items: DisputeItem[]; total: number }> => {
    const params = status ? `?status=${status}` : '';
    const res = await http.get<Envelope<Page<DisputeItem>>>(`/admin/disputes${params}`);
    return { items: res.data.data.items, total: res.data.data.total };
  },

  getById: async (id: number): Promise<DisputeItem> => {
    const res = await http.get<Envelope<DisputeItem>>(`/admin/disputes/${id}`);
    return res.data.data;
  },

  review: async (id: number): Promise<DisputeItem> => {
    const res = await http.patch<Envelope<DisputeItem>>(`/admin/disputes/${id}/review`);
    return res.data.data;
  },

  resolve: async (id: number, resolutionNotes: string, creditAmount?: number): Promise<DisputeItem> => {
    const res = await http.patch<Envelope<DisputeItem>>(`/admin/disputes/${id}/resolve`, {
      resolution_notes: resolutionNotes,
      ...(creditAmount != null && creditAmount > 0 ? { credit_amount: creditAmount } : {}),
    });
    return res.data.data;
  },

  close: async (id: number): Promise<DisputeItem> => {
    const res = await http.patch<Envelope<DisputeItem>>(`/admin/disputes/${id}/close`);
    return res.data.data;
  },
};
