"use client";

import { useEffect, useState } from "react";

interface HealthData {
  status: string;
  version: string;
  mode?: string;
  environment?: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/v1/health`, {
        headers: {
          Accept: "application/json",
        },
      });
      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }
      const data = await res.json();
      setHealth(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to connect to API");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-slate-950 text-slate-100 font-sans">
      <div className="w-full max-w-xl p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl space-y-6">
        <div className="border-b border-slate-800 pb-4">
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Allcited</span>
            <span className="text-xs font-mono uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">
              Phase 0
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Document Q&A with receipts · Next.js 14 frontend connectivity
          </p>
        </div>

        <div className="space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Backend API Health Status
          </h2>

          {loading && (
            <div className="flex items-center gap-3 text-slate-400 text-sm py-4">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
              <span>Connecting to /v1/health...</span>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-950/50 border border-red-800/60 rounded-xl text-red-200 text-sm space-y-1">
              <p className="font-semibold">Connection Error:</p>
              <p className="font-mono text-xs text-red-300">{error}</p>
            </div>
          )}

          {health && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono text-sm space-y-2">
              <div className="flex justify-between items-center text-xs text-slate-500 pb-2 border-b border-slate-800">
                <span>GET /v1/health</span>
                <span className="text-emerald-400 font-semibold">200 OK</span>
              </div>
              <pre className="text-emerald-400 text-xs overflow-x-auto">
                {JSON.stringify(health, null, 2)}
              </pre>
            </div>
          )}

          <button
            onClick={fetchHealth}
            disabled={loading}
            className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm rounded-xl transition-colors disabled:opacity-50"
          >
            {loading ? "Checking..." : "Re-check Health"}
          </button>
        </div>
      </div>
    </main>
  );
}
