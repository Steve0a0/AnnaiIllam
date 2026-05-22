"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/services/api-client";
import { getErrorMessage } from "@/lib/get-error-message";

interface ChangePasswordForm {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export default function SettingsPage() {
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="space-y-6">
      <section className="border-b border-border pb-6">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
          Management
        </p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-[-0.02em] text-foreground">
          Settings
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Admin profile and workspace settings.
        </p>
      </section>

      <Card className="max-w-md border-border bg-white shadow-sm">
        <CardHeader>
          <CardTitle className="font-display text-xl font-semibold">Change Password</CardTitle>
          <CardDescription>Update your admin account password.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1">
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

            <div className="space-y-1">
              <Label htmlFor="new_password">New Password</Label>
              <Input
                id="new_password"
                type="password"
                autoComplete="new-password"
                {...register("new_password", {
                  required: "New password is required",
                  minLength: { value: 8, message: "Password must be at least 8 characters" },
                })}
              />
              {errors.new_password && (
                <p className="text-xs text-destructive">{errors.new_password.message}</p>
              )}
            </div>

            <div className="space-y-1">
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
              <p className="text-sm text-green-600">Password changed successfully.</p>
            )}

            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? "Saving…" : "Change Password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

