import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type PrivacyRequestType = 'deletion' | 'export';
export type PrivacyRequestStatus = 'pending' | 'in_review' | 'completed' | 'rejected';

export type PrivacyRequest = {
  id: number;
  request_type: PrivacyRequestType;
  status: PrivacyRequestStatus;
  reason: string | null;
  resolution_notes: string | null;
  requested_at: string;
  resolved_at: string | null;
};

export const privacyService = {
  list: async (): Promise<PrivacyRequest[]> => {
    const response = await http.get<Envelope<PrivacyRequest[]>>('/me/privacy-requests');
    return response.data.data;
  },

  create: async (requestType: PrivacyRequestType): Promise<PrivacyRequest> => {
    const response = await http.post<Envelope<PrivacyRequest>>('/me/privacy-requests', {
      request_type: requestType,
    });
    return response.data.data;
  },

  exportData: async (requestId: number): Promise<Record<string, unknown>> => {
    const response = await http.get<Envelope<Record<string, unknown>>>(
      `/me/privacy-requests/${requestId}/export`,
    );
    return response.data.data;
  },
};
