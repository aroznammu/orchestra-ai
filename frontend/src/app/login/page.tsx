"use client";

import { login, loginWithApiKey, register } from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import { AlertCircle, KeyRound, Loader2, Mail, UserPlus } from "lucide-react";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

type Mode = "login" | "signup";
type Tab = "credentials" | "apikey";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [tab, setTab] = useState<Tab>("credentials");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [tenantName, setTenantName] = useState("");
  const [apiKey, setApiKey] = useState("");

  async function handleCredentials(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleSignup(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register(email, password, fullName, tenantName);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleApiKey(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await loginWithApiKey(apiKey);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid API key");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-xl font-bold text-white">
            O
          </div>
          <h1 className="mt-4 text-2xl font-bold text-zinc-50">
            OrchestraAI Cloud
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            {mode === "login"
              ? "Sign in to your dashboard"
              : "Create your account"}
          </p>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-2xl">
          {mode === "login" && (
            <div className="mb-6 flex rounded-lg border border-zinc-800 bg-zinc-900 p-0.5">
              <button
                onClick={() => { setTab("credentials"); setError(null); }}
                className={cn(
                  "flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  tab === "credentials"
                    ? "bg-indigo-600 text-white shadow"
                    : "text-zinc-400 hover:text-zinc-200",
                )}
              >
                <Mail className="h-4 w-4" />
                Email &amp; Password
              </button>
              <button
                onClick={() => { setTab("apikey"); setError(null); }}
                className={cn(
                  "flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  tab === "apikey"
                    ? "bg-indigo-600 text-white shadow"
                    : "text-zinc-400 hover:text-zinc-200",
                )}
              >
                <KeyRound className="h-4 w-4" />
                API Key
              </button>
            </div>
          )}

          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-800/50 bg-red-950/30 p-3 text-sm text-red-400">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {mode === "signup" ? (
            <form onSubmit={handleSignup} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  placeholder="you@company.com"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">
                  Password
                </label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  placeholder="Minimum 8 characters"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">
                  Workspace Name
                  <span className="ml-1 text-zinc-500 font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={tenantName}
                  onChange={(e) => setTenantName(e.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  placeholder="My Company"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
                Create Account
              </button>
            </form>
          ) : tab === "credentials" ? (
            <form onSubmit={handleCredentials} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  placeholder="you@company.com"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  placeholder="Enter your password"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                Sign in
              </button>
            </form>
          ) : (
            <form onSubmit={handleApiKey} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">
                  API Key
                </label>
                <input
                  type="password"
                  required
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm font-mono text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  placeholder="orch_xxxxxxxxxxxxxxxx"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                Authenticate
              </button>
            </form>
          )}

          <div className="mt-4 text-center text-sm">
            {mode === "login" ? (
              <p className="text-zinc-500">
                Don&apos;t have an account?{" "}
                <button
                  onClick={() => { setMode("signup"); setError(null); }}
                  className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
                >
                  Sign up
                </button>
              </p>
            ) : (
              <p className="text-zinc-500">
                Already have an account?{" "}
                <button
                  onClick={() => { setMode("login"); setError(null); }}
                  className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
                >
                  Sign in
                </button>
              </p>
            )}
          </div>
        </div>

        <p className="text-center text-xs text-zinc-600">
          OrchestraAI Cloud &mdash; Guardrailed AI Marketing
        </p>
      </div>
    </div>
  );
}
