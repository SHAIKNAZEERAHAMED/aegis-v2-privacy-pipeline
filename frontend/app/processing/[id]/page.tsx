"use client";
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Shell from "@/components/Shell";
import PipelineTrack from "@/components/PipelineTrack";
import { api, isAuthed } from "@/lib/api";

export default function ProcessingPage() {
  const router = useRouter();
  const params = useParams();
  const videoId = params.id as string;

  const [status, setStatus] = useState({ status: "PENDING", progress: 0, stage: "UPLOADED", error_message: null as string | null });

  useEffect(() => {
    if (!isAuthed()) {
      router.push("/login");
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const s = await api.getStatus(videoId);
        if (cancelled) return;
        setStatus(s);

        if (s.calibration_pending) {
          router.push(`/calibration?video_id=${videoId}`);
          return;
        }
        if (s.stage === "COMPLETED") {
          router.push(`/results/${videoId}`);
          return;
        }
        if (s.stage === "FAILED") {
          return; // show error state, no more polling
        }
        timer = setTimeout(poll, 1500);
      } catch {
        timer = setTimeout(poll, 2500);
      }
    }
    poll();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [videoId, router]);

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold mb-1">Processing</h1>
      <p className="text-graphite-500 text-sm mb-8">
        This runs asynchronously — feel free to leave and come back via your vault.
      </p>

      <PipelineTrack stage={status.stage} progress={status.progress} />

      {status.stage === "FAILED" && (
        <div className="mt-6 rounded-lg border border-alert-500/40 bg-alert-500/5 p-5">
          <p className="text-alert-500 font-mono text-sm mb-1">Processing failed</p>
          <p className="text-graphite-400 text-sm">{status.error_message || "Unknown error."}</p>
          <button
            onClick={() => router.push("/capture")}
            className="mt-4 px-4 py-2 rounded-md border border-graphite-600 text-sm hover:border-signal-400 hover:text-signal-400 transition-colors"
          >
            Try another capture
          </button>
        </div>
      )}
    </Shell>
  );
}
