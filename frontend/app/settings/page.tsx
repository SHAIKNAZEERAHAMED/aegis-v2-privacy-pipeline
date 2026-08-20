"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import { isAuthed, clearSession } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthed()) router.push("/login");
  }, [router]);

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold mb-1">Settings</h1>
      <p className="text-graphite-500 text-sm mb-8">Session and privacy controls.</p>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5 space-y-4">
        <div>
          <p className="text-sm font-medium">Retention policy</p>
          <p className="text-graphite-500 text-sm mt-1">
            Raw captures are held only in a temporary workspace during processing and are
            deleted immediately after a protected version is confirmed playable. Only
            protected output is ever persisted.
          </p>
        </div>
        <div>
          <p className="text-sm font-medium">Human calibration</p>
          <p className="text-graphite-500 text-sm mt-1">
            Runs once per login session and applies to every capture made during that session.
            Sign out and back in to recalibrate.
          </p>
        </div>
        <button
          onClick={() => {
            clearSession();
            router.push("/login");
          }}
          className="px-4 py-2 rounded-md border border-alert-500/40 text-alert-500 text-sm hover:bg-alert-500/10 transition-colors"
        >
          Sign out
        </button>
      </div>
    </Shell>
  );
}
