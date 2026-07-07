"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Eye, EyeOff, Lock, CheckCircle } from "lucide-react";
import { BackToHome } from "./BackToHome";

export function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (!token) {
      setError("Reset token is missing.");
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      setLoading(false);
      return;
    }

    if (password !== confirm) {
      setError("Passwords do not match.");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error || "Reset failed.");
        setLoading(false);
        return;
      }

      setSuccess(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="mx-auto w-full max-w-sm space-y-5 rounded-2xl border border-line bg-panel p-6 text-center shadow-[var(--shadow-panel)] sm:p-8">
        <div className="mb-2 flex justify-start">
          <BackToHome />
        </div>
        <CheckCircle className="mx-auto h-10 w-10 text-[accent]" />
        <div className="space-y-2">
          <h1 className="text-xl font-semibold tracking-tight">Password updated</h1>
          <p className="text-sm text-muted">Your password has been reset. You can now sign in.</p>
        </div>
        <Button variant="primary" size="md" asChild className="w-full rounded-xl">
          <Link href="/login">Sign in</Link>
        </Button>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mx-auto w-full max-w-sm space-y-5 rounded-2xl border border-line bg-panel p-6 shadow-[var(--shadow-panel)] sm:p-8"
    >
      <div className="space-y-1.5 text-center">
        <div className="mb-4 flex justify-start">
          <BackToHome />
        </div>
        <h1 className="text-xl font-semibold tracking-tight">Set new password</h1>
        <p className="text-sm text-muted">Choose a new password for your account.</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-1.5">
          <label htmlFor="password" className="label">New password</label>
          <div className="relative">
            <Lock
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint"
            />
            <input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              required
              minLength={8}
              className="h-11 w-full rounded-xl border border-line bg-base pl-9 pr-10 text-sm text-ink outline-none transition-colors placeholder:text-faint focus:border-ink focus:ring-1 focus:ring-ink"
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword((s) => !s)}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-faint hover:text-ink"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="confirm" className="label">Confirm password</label>
          <div className="relative">
            <Lock
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint"
            />
            <input
              id="confirm"
              name="confirm"
              type={showPassword ? "text" : "password"}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              required
              className="h-11 w-full rounded-xl border border-line bg-base pl-9 pr-4 text-sm text-ink outline-none transition-colors placeholder:text-faint focus:border-ink focus:ring-1 focus:ring-ink"
              placeholder="••••••••"
            />
          </div>
        </div>

        {error && (
          <p className="rounded-lg bg-red-500/10 px-3 py-2 text-center text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}

        <Button
          type="submit"
          variant="primary"
          size="md"
          className="h-11 w-full rounded-xl"
          disabled={loading || !password || !confirm}
        >
          {loading ? "Updating…" : "Update password"}
        </Button>
      </div>
    </form>
  );
}
