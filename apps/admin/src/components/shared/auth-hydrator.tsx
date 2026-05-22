"use client";

import { useEffect } from "react";
import { authStorage } from "@/lib/auth-storage";
import { useAuthStore } from "@/store/auth-store";
import type { AuthUser } from "@/types/auth";

export default function AuthHydrator() {
  const hydrateAuth = useAuthStore((state) => state.hydrateAuth);

  useEffect(() => {
    const accessToken = authStorage.getAccessToken();
    const refreshToken = authStorage.getRefreshToken();
    const user = authStorage.getUser() as AuthUser | null;

    hydrateAuth({ accessToken, refreshToken, user });
  }, [hydrateAuth]);

  return null;
}
