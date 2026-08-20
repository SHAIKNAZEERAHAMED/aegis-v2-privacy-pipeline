"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearSession } from "@/lib/api";

export default function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  function logout() {
    clearSession();
    router.push("/login");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-graphite-700 bg-graphite-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-signal-400 shadow-[0_0_8px_2px_rgba(44,194,174,0.6)]" />
            <span className="font-display font-semibold tracking-tight text-lg">Aegis</span>
          </Link>
          <nav className="flex items-center gap-6 text-sm font-mono text-graphite-500">
            <Link href="/dashboard" className="hover:text-signal-400 transition-colors">dashboard</Link>
            <Link href="/videos" className="hover:text-signal-400 transition-colors">vault</Link>
            <Link href="/settings" className="hover:text-signal-400 transition-colors">settings</Link>
            <button onClick={logout} className="hover:text-alert-500 transition-colors">sign out</button>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-10">{children}</main>
      <footer className="border-t border-graphite-800 py-6 text-center text-xs font-mono text-graphite-600">
        Resistance measured against configured recognition evaluators — not a claim of permanent or universal immunity.
      </footer>
    </div>
  );
}
