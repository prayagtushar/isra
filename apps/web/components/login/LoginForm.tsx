"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Eye, EyeOff, Lock, Mail } from "lucide-react";
import { BackToHome } from "./BackToHome";

interface LoginFormProps {
  redirect?: string;
}

export function LoginForm({ redirect = "/chat" }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/auth/signin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error || "Invalid email or password.");
        setLoading(false);
        return;
      }

      window.location.href = redirect;
    } catch {
      setError("Something went wrong. Please try again.");
      setLoading(false);
    }
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
        <h1 className="text-xl font-semibold tracking-tight">Sign in to ISRA</h1>
        <p className="text-sm text-muted">Welcome back. Enter your details.</p>
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

        <div className="space-y-1.5">
          <label htmlFor="password" className="label">Password</label>
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
              autoComplete="current-password"
              required
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
          disabled={loading || !email || !password}
        >
          {loading ? "Signing in…" : "Sign in"}
        </Button>
      </div>

      <div className="flex items-center justify-between text-sm">
        <Link href="/signup" className="text-muted hover:text-ink">Create account</Link>
        <Link href="/forgot-password" className="text-muted hover:text-ink">Forgot password?</Link>
      </div>
    </form>
  );
}
