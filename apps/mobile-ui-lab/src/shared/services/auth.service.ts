import { http } from '../lib/http';
import type { AuthTokens, MeResponse, SocialAuthTokens } from '../types/auth';

type Envelope<T> = { success: boolean; message: string; data: T };

export const authService = {
  requestOtp: async (payload: { phone: string; role: 'client' | 'worker' }) => {
    const res = await http.post<Envelope<{ phone: string; role: string; otp?: string }>>(
      `/auth/${payload.role}/request-otp`,
      { phone: payload.phone },
    );
    return res.data.data;
  },

  verifyOtp: async (payload: { phone: string; code: string; role: 'client' | 'worker' }) => {
    const res = await http.post<Envelope<AuthTokens>>(
      `/auth/${payload.role}/verify-otp`,
      { phone: payload.phone, code: payload.code },
    );
    return res.data.data;
  },

  socialAuth: async (payload: {
    provider: 'google' | 'apple';
    id_token: string;
    name?: string | null;
  }): Promise<SocialAuthTokens> => {
    const res = await http.post<Envelope<SocialAuthTokens>>('/auth/client/social', payload);
    return res.data.data;
  },

  getMe: async (): Promise<MeResponse> => {
    const res = await http.get<Envelope<MeResponse>>('/me');
    return res.data.data;
  },

  logout: async (refreshToken: string) => {
    const res = await http.post('/auth/logout', { refresh_token: refreshToken });
    return res.data;
  },

  refresh: async (refreshToken: string) => {
    const res = await http.post<Envelope<AuthTokens>>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return res.data.data;
  },
};
