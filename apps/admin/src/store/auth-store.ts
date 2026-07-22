"use client";

import { create } from "zustand";
import type { AuthUser } from "@/types/auth";

type AuthState = {
  accessToken: string | null;
  csrfToken: string | null;
  user: AuthUser | null;
  /** true once AuthHydrator has run and restored (or confirmed absent) tokens */
  isHydrated: boolean;
  /** Alias kept for any existing code using hasHydrated */
  hasHydrated: boolean;
  setAuth: (payload: {
    accessToken: string;
    csrfToken: string;
    user: AuthUser;
  }) => void;
  setUser: (user: AuthUser | null) => void;
  hydrateAuth: (data: {
    accessToken: string | null;
    csrfToken: string | null;
    user: AuthUser | null;
  }) => void;
  clearAuth: () => void;
  /** @deprecated use isHydrated */
  setHasHydrated: (value: boolean) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  csrfToken: null,
  user: null,
  isHydrated: false,
  hasHydrated: false,

  setAuth: ({ accessToken, csrfToken, user }) =>
    set({ accessToken, csrfToken, user, isHydrated: true, hasHydrated: true }),

  setUser: (user) => set({ user }),

  hydrateAuth: ({ accessToken, csrfToken, user }) =>
    set({ accessToken, csrfToken, user, isHydrated: true, hasHydrated: true }),

  clearAuth: () =>
    set({
      accessToken: null,
      csrfToken: null,
      user: null,
      isHydrated: true,
      hasHydrated: true,
    }),

  setHasHydrated: (value) => set({ hasHydrated: value, isHydrated: value }),
}));
