import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";
import { env } from "@/lib/env";
import { useAuthStore } from "@/store/auth-store";
import type { AuthSuccessResponse, CsrfResponse } from "@/types/auth";

type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

const sessionClient = axios.create({
  baseURL: env.apiBaseUrl,
  headers: { "Content-Type": "application/json" },
  timeout: 20_000,
  withCredentials: true,
});

let refreshPromise: Promise<string> | null = null;

export async function refreshAdminSession(): Promise<string> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const csrfResponse = await sessionClient.get<CsrfResponse>("/auth/admin/csrf");
    const csrfToken = csrfResponse.data.data.csrf_token;
    const refreshResponse = await sessionClient.post<AuthSuccessResponse>(
      "/auth/admin/refresh",
      undefined,
      { headers: { "X-CSRF-Token": csrfToken } },
    );
    const authData = refreshResponse.data.data;
    useAuthStore.getState().setAuth({
      accessToken: authData.access_token,
      csrfToken: authData.csrf_token,
      user: authData.user,
    });
    return authData.access_token;
  })();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

export const apiClient = axios.create({
  baseURL: env.apiBaseUrl,
  headers: { "Content-Type": "application/json" },
  timeout: 20_000,
  withCredentials: true,
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetriableRequestConfig | undefined;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      originalRequest.url?.includes("/auth/admin/")
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    try {
      const accessToken = await refreshAdminSession();
      originalRequest.headers.Authorization = `Bearer ${accessToken}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      useAuthStore.getState().clearAuth();
      return Promise.reject(refreshError);
    }
  },
);
