"use client";

const STAGES = [
  { key: "UPLOADED", label: "Received" },
  { key: "EXTRACTING_FRAMES", label: "Extracting frames" },
  { key: "DETECTING_FACES", label: "Detecting faces" },
  { key: "EVALUATING_BASELINE", label: "Baseline scoring" },
  { key: "OPTIMIZING", label: "Optimizing cloak" },
  { key: "HUMAN_CALIBRATION", label: "Your calibration" },
  { key: "APPLYING_TRANSFORMATION", label: "Applying profile" },
  { key: "RECONSTRUCTING", label: "Reconstructing" },
  { key: "VALIDATING", label: "Validating" },
  { key: "STORING_PROTECTED_VIDEO", label: "Storing" },
  { key: "DELETING_ORIGINAL", label: "Purging original" },
  { key: "COMPLETED", label: "Protected" },
];

export default function PipelineTrack({ stage, progress }: { stage: string; progress: number }) {
  const currentIdx = STAGES.findIndex((s) => s.key === stage);
  const failed = stage === "FAILED";

  return (
    <div className="scanline rounded-lg border border-graphite-700 bg-graphite-900 p-6">
      <div className="flex items-center justify-between mb-4">
        <span className="font-mono text-xs text-graphite-500 uppercase tracking-wider">Pipeline</span>
        <span className={`font-mono text-xs ${failed ? "text-alert-500" : "text-signal-400"}`}>
          {failed ? "FAILED" : `${progress}%`}
        </span>
      </div>
      <div className="space-y-1.5">
        {STAGES.map((s, i) => {
          const isPast = !failed && i < currentIdx;
          const isCurrent = !failed && i === currentIdx;
          return (
            <div key={s.key} className="flex items-center gap-3">
              <div
                className={`w-1.5 h-1.5 rounded-full shrink-0 transition-colors ${
                  isPast
                    ? "bg-signal-500"
                    : isCurrent
                    ? "bg-signal-400 shadow-[0_0_6px_1px_rgba(77,216,199,0.8)]"
                    : "bg-graphite-600"
                }`}
              />
              <span
                className={`font-mono text-sm transition-colors ${
                  isCurrent ? "text-signal-400" : isPast ? "text-graphite-400" : "text-graphite-600"
                }`}
              >
                {s.label}
              </span>
              {isCurrent && <span className="ml-auto text-[10px] text-graphite-500 animate-pulse">running…</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
