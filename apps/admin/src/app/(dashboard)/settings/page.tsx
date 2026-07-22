"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import { LogOut, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { apiClient } from "@/services/api-client";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth-store";
import { getErrorMessage } from "@/lib/get-error-message";

interface ChangePasswordForm {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

function getInitials(name?: string | null) {
  if (!name) return "A";
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function SettingsPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const csrfToken = useAuthStore((state) => state.csrfToken);

  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSigningOut, setIsSigningOut] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordForm>();

  const newPassword = watch("new_password");

  const onSubmit = async (data: ChangePasswordForm) => {
    setError(null);
    setSuccess(false);
    try {
      await apiClient.patch("/me/password", {
        current_password: data.current_password,
        new_password: data.new_password,
      });
      setSuccess(true);
      reset();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  async function handleSignOut() {
    setIsSigningOut(true);
    try {
      if (csrfToken) await authService.logout(csrfToken);
    } catch {
      // ignore — clear locally regardless
    } finally {
      clearAuth();
      router.replace("/login");
    }
  }

  return (
    <div className="space-y-8">
      {/* Page header */}
      <section className="border-b border-border pb-6">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
          Management
        </p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-[-0.02em] text-foreground">
          Settings
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Manage your account and workspace preferences.
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1fr_400px] lg:items-start">
        {/* Left column */}
        <div className="space-y-6">

          {/* Profile card */}
          <Card className="border-border bg-card shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Account</CardTitle>
              <CardDescription>Your identity on this workspace.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <Avatar
                  className="h-14 w-14 shrink-0 border-2"
                  style={{ borderColor: "var(--color-brand-100)" }}
                >
                  <AvatarFallback
                    className="text-base font-semibold text-primary-foreground"
                    style={{ background: "var(--color-brand-600)" }}
                  >
                    {getInitials(user?.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold text-foreground">
                    {user?.name ?? "—"}
                  </p>
                  <p className="truncate text-sm text-muted-foreground">{user?.email}</p>
                </div>
                {/* Role badge */}
                <span
                  className="shrink-0 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
                  style={{
                    background: "var(--color-brand-50)",
                    color: "var(--color-brand-700)",
                  }}
                >
                  <ShieldCheck className="h-3.5 w-3.5" />
                  {user?.role ?? "admin"}
                </span>
              </div>

              <p className="mt-4 text-xs text-muted-foreground">
                To update your name or email, ask a Super Admin to edit your account.
              </p>
            </CardContent>
          </Card>

          {/* Change password */}
          <Card className="border-border bg-card shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Change Password</CardTitle>
              <CardDescription>
                Use a strong password of at least 8 characters.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="current_password">Current Password</Label>
                  <Input
                    id="current_password"
                    type="password"
                    autoComplete="current-password"
                    {...register("current_password", { required: "Current password is required" })}
                  />
                  {errors.current_password && (
                    <p className="text-xs text-destructive">{errors.current_password.message}</p>
                  )}
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="new_password">New Password</Label>
                  <Input
                    id="new_password"
                    type="password"
                    autoComplete="new-password"
                    {...register("new_password", {
                      required: "New password is required",
                      minLength: { value: 8, message: "Must be at least 8 characters" },
                    })}
                  />
                  {errors.new_password && (
                    <p className="text-xs text-destructive">{errors.new_password.message}</p>
                  )}
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="confirm_password">Confirm New Password</Label>
                  <Input
                    id="confirm_password"
                    type="password"
                    autoComplete="new-password"
                    {...register("confirm_password", {
                      required: "Please confirm your new password",
                      validate: (val) => val === newPassword || "Passwords do not match",
                    })}
                  />
                  {errors.confirm_password && (
                    <p className="text-xs text-destructive">{errors.confirm_password.message}</p>
                  )}
                </div>

                {error && <p className="text-sm text-destructive">{error}</p>}
                {success && (
                  <p className="text-sm font-medium" style={{ color: "var(--color-brand-600)" }}>
                    Password changed successfully.
                  </p>
                )}

                <Button type="submit" disabled={isSubmitting} className="w-full">
                  {isSubmitting ? "Saving…" : "Update Password"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Session */}
          <Card className="border-border bg-card shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Session</CardTitle>
              <CardDescription>You are currently signed in as an admin.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg border border-border bg-muted/40 px-4 py-3 text-sm">
                <p className="font-medium text-foreground">{user?.name ?? user?.email}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{user?.email}</p>
              </div>
              <Button
                variant="outline"
                className="mt-4 w-full border-destructive/40 text-destructive hover:bg-destructive/5 hover:border-destructive"
                onClick={handleSignOut}
                disabled={isSigningOut}
              >
                <LogOut className="mr-2 h-4 w-4" />
                {isSigningOut ? "Signing out…" : "Sign out"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
