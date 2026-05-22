import axios from 'axios';
import { authStorage } from './auth-storage';
import { useAuthStore } from '../store/auth.store';

export const http = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

let refreshPromise: Promise<string | null> | null = null;

http.interceptors.request.use(async (config) => {
  const token = await authStorage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status !== 401 || originalRequest?._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
    }

    const token = await refreshPromise;
    if (!token) {
      await authStorage.clear();
      useAuthStore.getState().clearAuth();
      return Promise.reject(error);
    }

    originalRequest.headers = originalRequest.headers ?? {};
    originalRequest.headers.Authorization = `Bearer ${token}`;
    return http(originalRequest);
  },
);

async function refreshAccessToken() {
  const refreshToken = await authStorage.getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const res = await axios.post(
      `${process.env.EXPO_PUBLIC_API_BASE_URL}/auth/refresh`,
      { refresh_token: refreshToken },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      },
    );
    const { access_token, refresh_token } = res.data;
    await authStorage.setTokens(access_token, refresh_token);
    return access_token;
  } catch {
    return null;
  }
}
