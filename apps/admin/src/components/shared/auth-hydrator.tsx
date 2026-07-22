"use client";

import { useEffect } from "react";
import { refreshAdminSession } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";

export default function AuthHydrator() {
  const clearAuth = useAuthStore((state) => state.clearAuth);

  useEffect(() => {
    void refreshAdminSession().catch(() => clearAuth());
  }, [clearAuth]);

  return null;
}
