"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Shell from "@/components/Shell";
import { api, isAuthed } from "@/lib/api";

export default function Dashboard() {
  const router = useRouter();
  const [videos, setVideos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthed()) {
      router.push("/login");
      return;
    }
    api
      .listVideos()
      .then(setVideos)
      .finally(() => setLoading(false));
  }, [router]);

  const completed = videos.filter((v) => v.status === "COMPLETED").length;

  return (
    <Shell>
      <div className="mb-10">
        <h1 className="font-display text-3xl font-semibold">Dashboard</h1>
        <p className="text-graphite-500 mt-1">Capture a new clip, or review your protected vault.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
        <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
          <p className="text-xs font-mono text-graphite-500 uppercase">Protected videos</p>
          <p className="font-display text-3xl mt-2">{loading ? "—" : completed}</p>
        </div>
        <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
          <p className="text-xs font-mono text-graphite-500 uppercase">Capture limit</p>
          <p className="font-display text-3xl mt-2 text-signal-400">6s</p>
        </div>
        <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
          <p className="text-xs font-mono text-graphite-500 uppercase">Target rate</p>
          <p className="font-display text-3xl mt-2">24fps</p>
        </div>
      </div>

      <Link
        href="/capture"
        className="block rounded-lg border border-signal-500/40 bg-signal-500/5 p-8 text-center hover:bg-signal-500/10 transition-colors mb-10"
      >
        <span className="font-display text-xl font-semibold text-signal-400">+ New capture</span>
        <p className="text-graphite-500 text-sm mt-1">Record up to 6 seconds and start the protection pipeline.</p>
      </Link>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-mono text-sm text-graphite-500 uppercase tracking-wider">Recent</h2>
          <Link href="/videos" className="text-sm text-signal-400 hover:underline">
            View all →
          </Link>
        </div>
        {videos.slice(0, 3).map((v) => (
          <Link
            key={v.id}
            href={v.status === "COMPLETED" ? `/results/${v.id}` : `/processing/${v.id}`}
            className="flex items-center justify-between border-b border-graphite-800 py-3 hover:bg-graphite-900/50 px-2 -mx-2 rounded"
          >
            <span className="font-mono text-sm text-graphite-400">{v.id.slice(0, 8)}</span>
            <span
              className={`text-xs font-mono ${
                v.status === "COMPLETED" ? "text-signal-400" : v.status === "FAILED" ? "text-alert-500" : "text-graphite-500"
              }`}
            >
              {v.status}
            </span>
          </Link>
        ))}
        {!loading && videos.length === 0 && (
          <p className="text-graphite-600 text-sm py-6 text-center">No captures yet.</p>
        )}
      </div>
    </Shell>
  );
}
