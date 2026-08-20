"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import { api, isAuthed } from "@/lib/api";

const MAX_SECONDS = 6;

export default function CapturePage() {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const [permission, setPermission] = useState<"idle" | "granted" | "denied">("idle");
  const [recording, setRecording] = useState(false);
  const [countdown, setCountdown] = useState(MAX_SECONDS);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthed()) router.push("/login");
  }, [router]);

  async function requestCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setPermission("granted");
    } catch {
      setPermission("denied");
    }
  }

  function startRecording() {
    if (!streamRef.current) return;
    chunksRef.current = [];
    const recorder = new MediaRecorder(streamRef.current, { mimeType: "video/webm" });
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "video/webm" });
      setRecordedBlob(blob);
    };
    mediaRecorderRef.current = recorder;
    recorder.start();
    setRecording(true);
    setCountdown(MAX_SECONDS);

    const interval = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          clearInterval(interval);
          recorder.stop();
          setRecording(false);
          return 0;
        }
        return c - 1;
      });
    }, 1000);
  }

  function stopEarly() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  function retake() {
    setRecordedBlob(null);
    setCountdown(MAX_SECONDS);
  }

  async function submit() {
    if (!recordedBlob) return;
    setUploading(true);
    setError("");
    try {
      const video = await api.uploadVideo(recordedBlob);
      await api.startProcessing(video.id);
      router.push(`/processing/${video.id}`);
    } catch (err: any) {
      setError(err.message || "Upload failed");
      setUploading(false);
    }
  }

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold mb-1">New capture</h1>
      <p className="text-graphite-500 text-sm mb-8">
        Max {MAX_SECONDS} seconds, targeting 24fps. The original is only used to build your
        protected version — it's deleted the moment that's confirmed working.
      </p>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 overflow-hidden">
        <div className="aspect-video bg-graphite-950 relative flex items-center justify-center">
          {permission !== "granted" && !recordedBlob && (
            <div className="text-center px-6">
              {permission === "denied" ? (
                <p className="text-alert-500 text-sm">
                  Camera permission is required to record. Please allow camera access in your
                  browser settings and try again.
                </p>
              ) : (
                <button
                  onClick={requestCamera}
                  className="px-5 py-2.5 rounded-md bg-signal-500 text-graphite-950 font-semibold hover:bg-signal-400 transition-colors"
                >
                  Enable camera
                </button>
              )}
            </div>
          )}

          {recordedBlob ? (
            <video src={URL.createObjectURL(recordedBlob)} controls className="w-full h-full object-cover" />
          ) : (
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              className={`w-full h-full object-cover ${permission === "granted" ? "" : "hidden"}`}
            />
          )}

          {recording && (
            <div className="absolute top-4 right-4 flex items-center gap-2 bg-graphite-950/80 px-3 py-1.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-alert-500 animate-pulse" />
              <span className="font-mono text-sm">{countdown}s</span>
            </div>
          )}
        </div>

        <div className="p-5 flex items-center justify-center gap-3">
          {permission === "granted" && !recordedBlob && !recording && (
            <button
              onClick={startRecording}
              className="px-6 py-2.5 rounded-md bg-alert-500 text-white font-semibold hover:opacity-90 transition-opacity"
            >
              ● Record
            </button>
          )}
          {recording && (
            <button
              onClick={stopEarly}
              className="px-6 py-2.5 rounded-md border border-graphite-600 text-graphite-300 hover:border-alert-500 hover:text-alert-500 transition-colors"
            >
              Stop
            </button>
          )}
          {recordedBlob && !uploading && (
            <>
              <button
                onClick={retake}
                className="px-6 py-2.5 rounded-md border border-graphite-600 text-graphite-300 hover:border-signal-400 transition-colors"
              >
                Retake
              </button>
              <button
                onClick={submit}
                className="px-6 py-2.5 rounded-md bg-signal-500 text-graphite-950 font-semibold hover:bg-signal-400 transition-colors"
              >
                Start protection
              </button>
            </>
          )}
          {uploading && <p className="text-graphite-500 font-mono text-sm">Uploading…</p>}
        </div>
      </div>

      {error && <p className="text-alert-500 text-sm mt-4">{error}</p>}
    </Shell>
  );
}
