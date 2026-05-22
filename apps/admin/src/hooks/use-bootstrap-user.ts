"use client";

import { useEffect } from "react";
import { authService } from "@/services/auth.service";
import { authStorage } from "@/lib/auth-storage";
import { useAuthStore } from "@/store/auth-store";

export function useBootstrapUser() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  useEffect(() => {
    if (!accessToken || user) return;

    const run = async () => {
      try {
        const response = await authService.getMe();
        setUser(response.data);
        authStorage.setUser(response.data);
      } catch {
        authStorage.clear();
        clearAuth();
      }
    };

    run();
  }, [accessToken, user, setUser, clearAuth]);
}
