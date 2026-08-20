"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, setSession } from "@/lib/api";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.signup(email, password);
      setSession(res.access_token, res.session_id);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <h1 className="font-display text-2xl font-semibold mb-1">Create account</h1>
        <p className="text-graphite-500 text-sm mb-8">Set up access to Aegis.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-graphite-500 mb-1.5">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md bg-graphite-900 border border-graphite-700 px-3 py-2.5 text-sm focus:border-signal-400 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-mono text-graphite-500 mb-1.5">Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md bg-graphite-900 border border-graphite-700 px-3 py-2.5 text-sm focus:border-signal-400 outline-none"
            />
          </div>
          {error && <p className="text-alert-500 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-md bg-signal-500 text-graphite-950 font-semibold hover:bg-signal-400 transition-colors disabled:opacity-50"
          >
            {loading ? "Creating…" : "Create account"}
          </button>
        </form>
        <p className="mt-6 text-sm text-graphite-500">
          Already have an account?{" "}
          <Link href="/login" className="text-signal-400 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
