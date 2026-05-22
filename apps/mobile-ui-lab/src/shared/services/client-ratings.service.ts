import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type ClientRatingPayload = {
  requirement_id: number;
  rating: number; // 1-5
  comments?: string;
};

export type ClientRatingResult = {
  id: number;
  requirement_id: number;
  rating: number;
  comments: string | null;
};

export const clientRatingsService = {
  async submitRating(payload: ClientRatingPayload): Promise<ClientRatingResult> {
    const res = await http.post<Envelope<ClientRatingResult>>('/client/ratings', payload);
    return res.data.data;
  },
};
