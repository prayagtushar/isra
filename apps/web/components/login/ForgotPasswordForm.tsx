"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Mail, CheckCircle } from "lucide-react";
import { BackToHome } from "./BackToHome";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error || "Request failed.");
        setLoading(false);
        return;
      }

      setSubmitted(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <div className="mx-auto w-full max-w-sm space-y-5 rounded-2xl border border-line bg-panel p-6 text-center shadow-[var(--shadow-panel)] sm:p-8">
        <div className="mb-2 flex justify-start">
          <BackToHome />
        </div>
        <CheckCircle className="mx-auto h-10 w-10 text-[accent]" />
        <div className="space-y-2">
          <h1 className="text-xl font-semibold tracking-tight">Check your email</h1>
          <p className="text-sm text-muted">
            If an account exists for {email}, we sent a password reset link.
          </p>
        </div>
        <Link href="/login" className="inline-block text-sm text-ink hover:underline">Back to sign in</Link>
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
        <h1 className="text-xl font-semibold tracking-tight">Reset password</h1>
        <p className="text-sm text-muted">
          Enter your email and we’ll send you a reset link.
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-1.5">
          <label htmlFor="email" className="label">Email</label>
          <div className="relative">
            <Mail
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint"
            />
            <input
              id="email"
              name="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              className="h-11 w-full rounded-xl border border-line bg-base pl-9 pr-4 text-sm text-ink outline-none transition-colors placeholder:text-faint focus:border-ink focus:ring-1 focus:ring-ink"
              placeholder="you@example.com"
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
          disabled={loading || !email}
        >
          {loading ? "Sending…" : "Send reset link"}
        </Button>
      </div>

      <Link href="/login" className="block text-center text-sm text-muted hover:text-ink">Back to sign in</Link>
    </form>
  );
}
