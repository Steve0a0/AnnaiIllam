import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";
import { env } from "@/lib/env";
import { authStorage } from "@/lib/auth-storage";
import { useAuthStore } from "@/store/auth-store";
import type { AuthUser } from "@/types/auth";

type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

type RefreshResponse = {
  success: boolean;
  data: {
    access_token: string;
    refresh_token: string;
    token_type: string;
  };
};

function isAuthUser(value: unknown): value is AuthUser {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    "phone" in value &&
    "role" in value
  );
}

export const apiClient = axios.create({
  baseURL: env.apiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 20_000,
});

apiClient.interceptors.request.use((config) => {
  const storeToken = useAuthStore.getState().accessToken;
  const token =
    storeToken ||
    (typeof window !== "undefined" ? authStorage.getAccessToken() : null);

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
      originalRequest.url?.includes("/auth/")
    ) {
      return Promise.reject(error);
    }

    const refreshToken =
      useAuthStore.getState().refreshToken ||
      (typeof window !== "undefined" ? authStorage.getRefreshToken() : null);

    if (!refreshToken) {
      authStorage.clear();
      useAuthStore.getState().clearAuth();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const refreshResponse = await axios.post<RefreshResponse>(
        `${env.apiBaseUrl}/auth/refresh`,
        { refresh_token: refreshToken },
        { headers: { "Content-Type": "application/json" } }
      );

      const { access_token, refresh_token } = refreshResponse.data.data;
      const storedUser = authStorage.getUser();
      const user =
        useAuthStore.getState().user ||
        (isAuthUser(storedUser) ? storedUser : null);

      authStorage.setTokens(access_token, refresh_token);
      if (user) {
        authStorage.setUser(user);
        useAuthStore.getState().setAuth({
          accessToken: access_token,
          refreshToken: refresh_token,
          user,
        });
      } else {
        useAuthStore.getState().hydrateAuth({
          accessToken: access_token,
          refreshToken: refresh_token,
          user: null,
        });
      }

      originalRequest.headers.Authorization = `Bearer ${access_token}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      authStorage.clear();
      useAuthStore.getState().clearAuth();
      return Promise.reject(refreshError);
    }
  }
);
