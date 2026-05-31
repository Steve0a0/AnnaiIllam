"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authService } from "@/services/auth.service";
import { authStorage } from "@/lib/auth-storage";
import { useAuthStore } from "@/store/auth-store";
import { getErrorMessage } from "@/lib/get-error-message";
import { cn } from "@/lib/cn";

function EyeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.75"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.75"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
      <path d="M10.73 10.73a3 3 0 004.54 4.54" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const inputBase =
  "w-full rounded-[10px] bg-white border-2 border-neutral-200 px-4 py-3.5 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-accent focus:ring-2 focus:ring-accent/10";

export default function LoginForm() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);

  const emailInvalid = emailTouched && email.trim() !== "" && !EMAIL_RE.test(email.trim());
  const canSubmit = !loading && email.trim() !== "" && password !== "";

  // ── submit logic unchanged ──────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail.includes("@") || !normalizedEmail.split("@")[1]?.includes(".")) {
      setError("Enter a valid email address.");
      return;
    }
    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await authService.login({ email: normalizedEmail, password });
      const authData = response.data;

      authStorage.setTokens(authData.access_token, authData.refresh_token);
      authStorage.setUser(authData.user);

      setAuth({
        accessToken: authData.access_token,
        refreshToken: authData.refresh_token,
        user: authData.user,
      });

      router.replace("/dashboard");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };
  // ────────────────────────────────────────────────────────────────────────

  return (
    <form onSubmit={handleSubmit} noValidate>

      {/* Error banner */}
      {error && (
        <div
          className="mb-5 flex items-start gap-2.5 rounded-lg border border-danger-500/40 bg-danger-50 px-3.5 py-3"
          role="alert"
          aria-atomic="true"
        >
          <svg className="mt-px h-4 w-4 shrink-0 text-danger-700" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
            <path d="M8 5v3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <circle cx="8" cy="11.25" r=".875" fill="currentColor" />
          </svg>
          <span className="text-[13px] font-medium leading-snug text-danger-700">{error}</span>
        </div>
      )}

      {/* Email */}
      <div className="mb-4">
        <label className="mb-1.5 block text-[13px] font-semibold text-foreground" htmlFor="email">
          Email address
        </label>
        <input
          id="email"
          type="email"
          name="email"
          autoComplete="email"
          placeholder="you@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onBlur={() => setEmailTouched(true)}
          aria-invalid={emailInvalid || undefined}
          aria-describedby={emailInvalid ? "email-error" : undefined}
          required
          className={cn(
            inputBase,
            emailInvalid && "border-danger-500 focus:border-danger-500 focus:ring-danger-500/10",
          )}
        />
        {emailInvalid && (
          <span id="email-error" className="mt-1.5 block text-xs font-medium text-danger-700" role="alert">
            Please enter a valid email address.
          </span>
        )}
      </div>

      {/* Password */}
      <div className="mb-2">
        <label className="mb-1.5 block text-[13px] font-semibold text-foreground" htmlFor="password">
          Password
        </label>
        <div className="relative">
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            name="password"
            autoComplete="current-password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className={cn(inputBase, "pr-12")}
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            aria-label={showPassword ? "Hide password" : "Show password"}
            aria-pressed={showPassword}
            aria-controls="password"
            className="absolute right-3 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {showPassword ? <EyeOffIcon /> : <EyeIcon />}
          </button>
        </div>
      </div>

      {/* Forgot password */}
      <div className="mb-6 flex justify-end">
        <a
          href="#"
          className="text-xs font-medium text-accent hover:underline focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          Forgot password?
        </a>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={!canSubmit}
        className="flex min-h-[52px] w-full items-center justify-center gap-2 rounded-[10px] bg-primary px-4 py-3.5 text-[15px] font-bold tracking-[0.01em] text-primary-foreground transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
      >
        {loading ? (
          <span
            className="block h-[18px] w-[18px] animate-spin rounded-full border-[2.5px] border-white/30 border-t-white"
            aria-hidden="true"
          />
        ) : (
          "Sign In"
        )}
      </button>

      <p className="mt-5 text-center text-xs text-muted-foreground">
        Having trouble? Contact your administrator
      </p>

    </form>
  );
}
