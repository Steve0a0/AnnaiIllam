"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
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
    <main className="grid min-h-screen place-items-center bg-background px-4 py-10">
      <Card className="w-full max-w-md p-8">
        <div className="mb-8">
          <p className="text-[10px] font-bold uppercase tracking-[0.28em] text-accent">Admin access</p>
          <h1 className="mt-3 font-display text-3xl font-semibold tracking-tight text-foreground">Sign in</h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Login with your email address and password.
          </p>
        </div>

        <LoginForm />
      </Card>
    </main>
  );
}
