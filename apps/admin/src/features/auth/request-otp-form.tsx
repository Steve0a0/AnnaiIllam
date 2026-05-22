"use client";

import { useState } from "react";
import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { authService } from "@/services/auth.service";
import { getErrorMessage } from "@/lib/get-error-message";

export default function RequestOtpForm({
  onSuccess,
}: {
  onSuccess: (phone: string, devOtp?: string) => void;
}) {
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone.trim()) {
      setError("Please enter your phone number.");
      return;
    }

    // Backend expects digits only (10–15 chars), no +, spaces, or dashes
    const normalizedPhone = phone.trim().replace(/\D/g, "");
    if (normalizedPhone.length < 10 || normalizedPhone.length > 15) {
      setError("Enter a valid phone number (10–15 digits).");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await authService.requestOtp({ phone: normalizedPhone });

      // Backend returns OTP in local/dev environment
      const otp = (response?.data as { otp?: string } | undefined)?.otp;

      onSuccess(normalizedPhone, otp);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <Input
        label="Phone number"
        type="tel"
        placeholder="9876543210"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        autoComplete="tel"
        inputMode="tel"
        required
      />

      {error ? (
        <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? "Sending OTP…" : "Send OTP"}
      </Button>
    </form>
  );
}
