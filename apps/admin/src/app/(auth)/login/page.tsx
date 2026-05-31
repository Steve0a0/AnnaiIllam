"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import LoadingState from "@/components/shared/loading-state";
import { LoginForm } from "@/features/auth";
import { useAuthStore } from "@/store/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  useEffect(() => {
    if (!isHydrated) return;
    if (accessToken && user?.role === "admin") {
      router.replace("/dashboard");
    }
  }, [accessToken, user, isHydrated, router]);

  if (!isHydrated) {
    return <LoadingState title="Loading" description="Preparing the admin workspace." />;
  }

  if (accessToken && user?.role === "admin") {
    return null;
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-background px-8 py-16">
      <div className="w-full max-w-[380px]">
        {/* Wordmark */}
        <p className="mb-8 text-[20px] font-extrabold tracking-[-0.02em] text-brand-900">
          Annai Illam
        </p>

        {/* Form header */}
        <p className="mb-2.5 text-[11px] font-semibold uppercase tracking-[0.1em] text-accent">
          Admin Portal
        </p>
        <h1 className="mb-1.5 text-[28px] font-extrabold leading-[1.15] tracking-[-0.02em] text-foreground">
          Welcome back
        </h1>
        <p className="mb-8 text-sm text-muted-foreground">
          Sign in to manage your workforce
        </p>

        <LoginForm />
      </div>

      <span className="absolute bottom-5 right-6 select-none font-mono text-[11px] text-muted-foreground">
        v2.1.0
      </span>
    </main>
  );
}
