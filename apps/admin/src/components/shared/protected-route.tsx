"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuthStore } from "@/store/auth-store";
import FullPageLoader from "@/components/shared/full-page-loader";
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
    return <FullPageLoader />;
  }

  if (!accessToken || !user || user.role !== "admin") {
    return <FullPageLoader />;
  }

  return <>{children}</>;
}
