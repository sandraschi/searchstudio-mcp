import { HeartPulse, Play } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { apiGet } from "@/api/client";
import { cn } from "@/lib/cn";

interface Row {
  provider: string;
  kind: string;
  attempts: number;
  ok: number;
  blocked: number;
  success_rate: number;
  p50_latency_ms: number;
}

export default function ProvidersPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [configured, setConfigured] = useState<Record<string, boolean>>({});
  const [matrix, setMatrix] = useState<Array<{
    probe: string;
    total: number;
    failed: string[];
  }> | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await apiGet<{
        scoreboard: Row[];
        configured: Record<string, boolean>;
      }>("/api/providers?window_hours=24");
      setRows(data.scoreboard ?? []);
      setConfigured(data.configured ?? {});
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function runMatrix() {
    setRunning(true);
    setMatrix(null);
    try {
      const data = await apiGet<{
        matrix: Array<{ probe: string; total: number; failed: string[] }>;
      }>("/api/matrix");
      setMatrix(data.matrix ?? []);
      load();
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <HeartPulse size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Providers</h1>
        <button
          type="button"
          onClick={runMatrix}
          disabled={running}
          data-testid="matrix-run"
          className="ml-auto flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 hover:border-zinc-500 disabled:opacity-50"
        >
          <Play size={13} /> {running ? "Probing…" : "Run flakiness matrix"}
        </button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div
        className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
        data-testid="provider-cards"
      >
        {Object.keys(configured).map((name) => {
          const row = rows.find((r) => r.provider === name);
          const ok = configured[name];
          return (
            <div
              key={name}
              className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
            >
              <p className="font-mono text-sm text-zinc-100">{name}</p>
              <p
                className={cn(
                  "mt-1 text-xs",
                  ok ? "text-green-400" : "text-amber-400",
                )}
              >
                {ok ? "ready" : "not configured"}
              </p>
              {row ? (
                <div className="mt-2 grid grid-cols-3 gap-1 text-center">
                  <div className="rounded bg-zinc-950 p-1.5">
                    <p className="text-sm font-semibold">
                      {(row.success_rate * 100).toFixed(0)}%
                    </p>
                    <p className="text-[10px] text-zinc-500">success</p>
                  </div>
                  <div className="rounded bg-zinc-950 p-1.5">
                    <p className="text-sm font-semibold">
                      {row.p50_latency_ms}ms
                    </p>
                    <p className="text-[10px] text-zinc-500">p50</p>
                  </div>
                  <div className="rounded bg-zinc-950 p-1.5">
                    <p className="text-sm font-semibold">{row.blocked}</p>
                    <p className="text-[10px] text-zinc-500">blocked</p>
                  </div>
                </div>
              ) : (
                <p className="mt-2 text-[11px] text-zinc-600">
                  No attempts recorded in 24h.
                </p>
              )}
            </div>
          );
        })}
      </div>

      {matrix && (
        <div
          className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
          data-testid="matrix-results"
        >
          <p className="text-sm font-medium">Flakiness matrix</p>
          {matrix.map((m) => (
            <p key={m.probe} className="mt-1 text-xs text-zinc-400">
              "{m.probe}" - {m.total} hits
              {m.failed.length > 0 && (
                <span className="text-red-400">
                  {" "}
                  · failed: {m.failed.join(", ")}
                </span>
              )}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
