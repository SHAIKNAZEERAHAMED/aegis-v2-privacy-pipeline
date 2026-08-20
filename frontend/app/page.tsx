import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
        <span className="font-mono text-xs text-signal-400 tracking-widest uppercase mb-6">
          Research proof of concept
        </span>
        <h1 className="font-display text-5xl md:text-6xl font-semibold tracking-tight max-w-2xl leading-tight">
          Legible to people.
          <br />
          <span className="text-signal-400">Illegible to recognition models.</span>
        </h1>
        <p className="mt-6 max-w-lg text-graphite-400 leading-relaxed">
          Aegis captures six seconds of video, then iteratively degrades the face
          just enough to defeat automated recognition — while staying calibrated
          to what a human can still recognize. Only the protected output is ever stored.
        </p>
        <div className="mt-10 flex gap-4">
          <Link
            href="/signup"
            className="px-6 py-3 rounded-md bg-signal-500 text-graphite-950 font-semibold hover:bg-signal-400 transition-colors"
          >
            Get started
          </Link>
          <Link
            href="/login"
            className="px-6 py-3 rounded-md border border-graphite-600 text-graphite-300 hover:border-signal-400 hover:text-signal-400 transition-colors"
          >
            Sign in
          </Link>
        </div>
      </div>
      <footer className="py-6 text-center text-xs font-mono text-graphite-600">
        Resistance is measured against configured recognition evaluators — not a claim of permanent or universal immunity.
      </footer>
    </div>
  );
}
