"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Shell from "@/components/Shell";
import { api, isAuthed } from "@/lib/api";

export default function VideosPage() {
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

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Delete this protected video permanently?")) return;
    await api.deleteVideo(id);
    setVideos((v) => v.filter((x) => x.id !== id));
  }

  return (
    <Shell>
      <h1 className="font-display text-2xl font-semibold mb-1">Vault</h1>
      <p className="text-graphite-500 text-sm mb-8">All your protected videos. Originals are never stored here.</p>

      {loading && <p className="text-graphite-600 font-mono text-sm">Loading…</p>}
      {!loading && videos.length === 0 && (
        <p className="text-graphite-600 text-sm py-10 text-center">
          Nothing here yet. <Link href="/capture" className="text-signal-400 hover:underline">Make your first capture.</Link>
        </p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {videos.map((v) => (
          <Link
            key={v.id}
            href={v.status === "COMPLETED" ? `/results/${v.id}` : `/processing/${v.id}`}
            className="rounded-lg border border-graphite-700 bg-graphite-900 overflow-hidden hover:border-signal-400/50 transition-colors"
          >
            <div className="aspect-video bg-graphite-950 flex items-center justify-center">
              {v.status === "COMPLETED" ? (
                <video src={api.downloadUrl(v.id)} className="w-full h-full object-cover" muted />
              ) : (
                <span className="font-mono text-xs text-graphite-600">{v.status}</span>
              )}
            </div>
            <div className="p-3 flex items-center justify-between">
              <span className="font-mono text-xs text-graphite-500">{v.id.slice(0, 8)}</span>
              <button
                onClick={(e) => handleDelete(v.id, e)}
                className="text-xs text-graphite-600 hover:text-alert-500 transition-colors"
              >
                delete
              </button>
            </div>
          </Link>
        ))}
      </div>
    </Shell>
  );
}
