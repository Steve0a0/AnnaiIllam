"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuthStore } from "@/store/auth-store";
import LoadingState from "@/components/shared/loading-state";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  useEffect(() => {
    if (!isHydrated) return;

    if (!accessToken || !user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }

    if (user.role !== "admin") {
      router.replace("/login");
    }
  }, [accessToken, user, isHydrated, pathname, router]);

  if (!isHydrated) {
    return <LoadingState title="Checking access" description="Preparing the admin workspace." />;
  }

  if (!accessToken || !user || user.role !== "admin") {
    return <LoadingState title="Redirecting" description="Please wait…" />;
  }

  return <>{children}</>;
}
