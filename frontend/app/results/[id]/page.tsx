"use client";
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import Shell from "@/components/Shell";
import { api, isAuthed } from "@/lib/api";

export default function ResultsPage() {
  const router = useRouter();
  const params = useParams();
  const videoId = params.id as string;
  const [video, setVideo] = useState<any>(null);

  useEffect(() => {
    if (!isAuthed()) {
      router.push("/login");
      return;
    }
    api.getVideo(videoId).then(setVideo).catch(() => {});
  }, [videoId, router]);

  if (!video) {
    return (
      <Shell>
        <p className="text-graphite-500 font-mono text-sm">Loading…</p>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="max-w-lg mx-auto text-center">
        <span className="font-mono text-xs text-signal-400 uppercase tracking-widest">Protected</span>
        <h1 className="font-display text-2xl font-semibold mt-2 mb-8">Your video is ready</h1>

        <div className="rounded-lg border border-graphite-700 bg-graphite-900 overflow-hidden mb-6">
          <video src={api.downloadUrl(videoId)} controls className="w-full aspect-video object-cover" />
        </div>

        <div className="flex justify-center gap-4">
          <a
            href={api.downloadUrl(videoId)}
            download
            className="px-6 py-2.5 rounded-md bg-signal-500 text-graphite-950 font-semibold hover:bg-signal-400 transition-colors"
          >
            Download
          </a>
          <Link
            href="/capture"
            className="px-6 py-2.5 rounded-md border border-graphite-600 text-graphite-300 hover:border-signal-400 hover:text-signal-400 transition-colors"
          >
            New capture
          </Link>
        </div>

        <p className="text-graphite-600 text-xs font-mono mt-8">
          The original recording has been deleted. Only this protected version is stored.
        </p>
      </div>
    </Shell>
  );
}
