import { http } from "@/lib/http";
import type {
  AdminLoginPayload,
  AuthSuccessResponse,
  MeResponse,
} from "@/types/auth";

export const authService = {
  requestOtp: async (_payload: { phone: string }): Promise<{ data?: { otp?: string } }> => {
    throw new Error("OTP login is not enabled for the admin web app. Use password login.");
  },

  verifyOtp: async (_payload: { phone: string; code: string }): Promise<AuthSuccessResponse> => {
    throw new Error("OTP login is not enabled for the admin web app. Use password login.");
  },

  login: async (payload: AdminLoginPayload): Promise<AuthSuccessResponse> => {
    const res = await http.post("/auth/admin/login", payload);
    return res.data;
  },

  getMe: async (): Promise<MeResponse> => {
    const res = await http.get("/me");
    return res.data;
  },

  refreshToken: async (refreshToken: string) => {
    const res = await http.post("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return res.data;
  },

  logout: async (refreshToken: string) => {
    const res = await http.post("/auth/logout", {
      refresh_token: refreshToken,
    });
    return res.data;
  },
};
