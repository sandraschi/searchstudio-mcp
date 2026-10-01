import { Activity } from "lucide-react";
import { useEffect, useState } from "react";
import { apiGet } from "@/api/client";

interface Attempt {
  provider: string;
  attempts: number;
  ok: number;
  blocked: number;
}

export default function ActivityPage() {
  const [rows, setRows] = useState<Attempt[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let live = true;
    apiGet<{ scoreboard: Attempt[] }>("/api/providers?window_hours=168")
      .then((d) => live && setRows(d.scoreboard ?? []))
      .catch((e) => live && setError(String(e)));
    return () => {
      live = false;
    };
  }, []);

  const total = rows.reduce((n, r) => n + r.attempts, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Activity size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Activity</h1>
        <span
          className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400"
          data-testid="activity-count"
        >
          {total} provider calls · 7d
        </span>
      </div>
      <p className="text-xs text-zinc-500">
        Every fan-out records one row per provider attempt. This is the usage
        trail - who searched, who answered, who blocked.
      </p>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {rows.length === 0 && !error ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-8 text-center text-sm text-zinc-500">
          Quiet here - no searches recorded in the last 7 days. Run one from the
          Search console.
        </div>
      ) : (
        <div className="space-y-2" data-testid="activity-list">
          {rows.map((r) => (
            <div
              key={r.provider}
              className="flex items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/50 px-4 py-2.5 text-sm"
            >
              <span className="font-mono text-xs text-zinc-200">
                {r.provider}
              </span>
              <span className="text-xs text-zinc-500">{r.attempts} calls</span>
              <span className="text-xs text-green-400">{r.ok} ok</span>
              {r.blocked > 0 && (
                <span className="text-xs text-amber-400">
                  {r.blocked} blocked
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
