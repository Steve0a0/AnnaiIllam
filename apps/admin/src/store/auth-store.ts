"use client";

import { create } from "zustand";
import type { AuthUser } from "@/types/auth";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  /** true once AuthHydrator has run and restored (or confirmed absent) tokens */
  isHydrated: boolean;
  /** Alias kept for any existing code using hasHydrated */
  hasHydrated: boolean;
  setAuth: (payload: {
    accessToken: string;
    refreshToken: string;
    user: AuthUser;
  }) => void;
  setUser: (user: AuthUser | null) => void;
  hydrateAuth: (data: {
    accessToken: string | null;
    refreshToken: string | null;
    user: AuthUser | null;
  }) => void;
  clearAuth: () => void;
  /** @deprecated use isHydrated */
  setHasHydrated: (value: boolean) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  isHydrated: false,
  hasHydrated: false,

  setAuth: ({ accessToken, refreshToken, user }) =>
    set({ accessToken, refreshToken, user, isHydrated: true, hasHydrated: true }),

  setUser: (user) => set({ user }),

  hydrateAuth: ({ accessToken, refreshToken, user }) =>
    set({ accessToken, refreshToken, user, isHydrated: true, hasHydrated: true }),

  clearAuth: () =>
    set({
      accessToken: null,
      refreshToken: null,
      user: null,
      isHydrated: true,
      hasHydrated: true,
    }),

  setHasHydrated: (value) => set({ hasHydrated: value, isHydrated: value }),
}));
