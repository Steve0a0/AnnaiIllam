"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth-store";
import { getErrorMessage } from "@/lib/get-error-message";

export default function VerifyOtpForm({
  phone,
  devOtp,
  onBack,
}: {
  phone: string;
  devOtp?: string;
  onBack: () => void;
}) {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) {
      setError("Please enter the OTP.");
      return;
    }
    setLoading(true);
    setError("");

    try {
      const response = await authService.verifyOtp({ phone, code: code.trim() });
      const authData = response.data;

      setAuth({
        accessToken: authData.access_token,
        csrfToken: authData.csrf_token,
        user: authData.user,
      });

      router.replace("/dashboard");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleVerify} className="space-y-5">
      <div className="rounded-lg border border-border bg-secondary px-4 py-3 text-sm text-muted-foreground">
        OTP sent to <span className="font-semibold">{phone}</span>
      </div>

      {devOtp ? (
        <div className="rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Dev OTP: <span className="font-semibold tracking-widest">{devOtp}</span>
        </div>
      ) : null}

      <Input
        label="Enter OTP"
        type="text"
        placeholder="000000"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        autoComplete="one-time-code"
        inputMode="numeric"
        maxLength={6}
        required
      />

      {error ? (
        <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      <div className="flex gap-3">
        <Button type="button" variant="secondary" className="w-full" onClick={onBack} disabled={loading}>
          Back
        </Button>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Verifying…" : "Verify OTP"}
        </Button>
      </div>
    </form>
  );
}
