import { http } from '../lib/http';

type Envelope<T> = { success: boolean; message: string; data: T };

export type ClientProfile = {
  id: number;
  client_type: 'individual' | 'company';
  company_name: string | null;
  contact_name: string;
  phone: string | null;
  city: string;
  state: string;
  address: string | null;
  gst_number: string | null;
  industry: string | null;
  email: string | null;
  default_job_category: string | null;
  food_preference: boolean;
  accommodation_preference: boolean;
  standing_notes: string | null;
};

export type ClientProfilePatch = {
  client_type?: 'individual' | 'company';
  company_name?: string | null;
  contact_name?: string;
  city?: string;
  state?: string;
  address?: string | null;
  industry?: string | null;
  email?: string | null;
  default_job_category?: string | null;
  food_preference?: boolean;
  accommodation_preference?: boolean;
  standing_notes?: string | null;
};

export type ClientProfileCreate = {
  client_type: 'individual' | 'company';
  company_name?: string | null;
  contact_name: string;
  city: string;
  state: string;
  address?: string | null;
  gst_number?: string | null;
};

export const clientPhoneService = {
  requestOtp: async (phone: string): Promise<{ phone: string; otp?: string }> => {
    const res = await http.post<Envelope<{ phone: string; otp?: string }>>('/client/phone/request-otp', { phone });
    return res.data.data;
  },
  verify: async (phone: string, code: string): Promise<{ phone: string }> => {
    const res = await http.post<Envelope<{ phone: string }>>('/client/phone/verify', { phone, code });
    return res.data.data;
  },
};

export const clientProfileService = {
  createProfile: async (data: ClientProfileCreate): Promise<{ id: number }> => {
    const res = await http.post<Envelope<{ id: number }>>('/client/profile', data);
    return res.data.data;
  },

  getProfile: async (): Promise<ClientProfile> => {
    const res = await http.get<Envelope<ClientProfile>>('/client/profile');
    return res.data.data;
  },

  patchProfile: async (data: ClientProfilePatch): Promise<{ id: number }> => {
    const res = await http.patch<Envelope<{ id: number }>>('/client/profile', data);
    return res.data.data;
  },
};
