"use client";
import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import { api, isAuthed } from "@/lib/api";

export default function CalibrationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const videoId = searchParams.get("video_id") || "";

  const [round, setRound] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [frameKey, setFrameKey] = useState(0); // cache-bust the image each round

  useEffect(() => {
    if (!isAuthed()) router.push("/login");
  }, [router]);

  async function answer(recognizable: boolean) {
    setSubmitting(true);
    try {
      await api.submitCalibration(videoId, recognizable);
      if (recognizable) {
        // wait a moment for the backend to compute the next, stronger frame
        setTimeout(() => {
          setRound((r) => r + 1);
          setFrameKey((k) => k + 1);
          setSubmitting(false);
        }, 1800);
      } else {
        router.push(`/processing/${videoId}`);
      }
    } catch {
      setSubmitting(false);
    }
  }

  return (
    <Shell>
      <div className="max-w-lg mx-auto text-center">
        <span className="font-mono text-xs text-signal-400 uppercase tracking-widest">
          Human calibration · round {round}
        </span>
        <h1 className="font-display text-2xl font-semibold mt-2 mb-2">Can you still recognize this face?</h1>
        <p className="text-graphite-500 text-sm mb-8">
          This appears once per session. Your answer sets how far we push the protection —
          we go right up to the edge of what's still recognizable to a person, then stop
          one step before that.
        </p>

        <div className="rounded-lg border border-graphite-700 bg-graphite-900 overflow-hidden mb-8">
          <img
            key={frameKey}
            src={`${api.calibrationFrameUrl(videoId)}&r=${frameKey}`}
            alt="Calibration frame"
            className="w-full aspect-video object-cover"
          />
        </div>

        <div className="flex justify-center gap-4">
          <button
            disabled={submitting}
            onClick={() => answer(true)}
            className="px-6 py-2.5 rounded-md border border-graphite-600 text-graphite-300 hover:border-signal-400 hover:text-signal-400 transition-colors disabled:opacity-50"
          >
            Yes, still recognizable
          </button>
          <button
            disabled={submitting}
            onClick={() => answer(false)}
            className="px-6 py-2.5 rounded-md bg-signal-500 text-graphite-950 font-semibold hover:bg-signal-400 transition-colors disabled:opacity-50"
          >
            No, not anymore
          </button>
        </div>
        {submitting && <p className="text-graphite-600 font-mono text-xs mt-4">computing next round…</p>}
      </div>
    </Shell>
  );
}
