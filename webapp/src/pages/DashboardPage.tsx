import { ArrowRight, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, type ProviderInfo } from "@/api/client";

interface Health {
  success: boolean;
  version: string;
  db: string;
  providers: ProviderInfo[];
}

const QUICK = [
  "AMD World Labs acquisition",
  "Hollabrunn local history",
  "best sourdough hydration percentage",
];

export default function DashboardPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let live = true;
    apiGet<Health>("/api/health")
      .then((h) => live && setHealth(h))
      .catch((e) => live && setError(String(e)));
    return () => {
      live = false;
    };
  }, []);

  const configured = (health?.providers ?? []).filter((p) => p.configured);
  const unconfigured = (health?.providers ?? []).filter((p) => !p.configured);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-800 bg-gradient-to-b from-zinc-900 to-zinc-950 p-6 md:p-8">
        <p className="text-xs uppercase tracking-widest text-zinc-500">
          SearchStudio
        </p>
        <h1 className="mt-1 text-3xl md:text-4xl font-bold tracking-tight">
          Super search is all you need.
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-400">
          One query fans out across fleet-local knowledge, curated sources, and
          web search - merged, deduped, with receipts per provider.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {QUICK.map((q) => (
            <Link
              key={q}
              to={`/search?q=${encodeURIComponent(q)}`}
              className="rounded-full border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 hover:border-zinc-500 hover:text-zinc-100"
            >
              {q}
            </Link>
          ))}
        </div>
        <Link
          to="/search"
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white"
        >
          <Search size={16} /> Open search console <ArrowRight size={16} />
        </Link>
        {unconfigured.length > 0 && (
          <Link
            to="/settings"
            data-testid="onboarding-cue"
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-500"
          >
            Complete provider setup - {unconfigured.length} optional provider
            {unconfigured.length === 1 ? "" : "s"} unconfigured
          </Link>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-400">Backend unreachable: {error}</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {(health?.providers ?? []).map((p) => (
          <div
            key={p.name}
            className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3"
          >
            <p className="font-mono text-xs text-zinc-200">{p.name}</p>
            <p className="text-[11px] text-zinc-500">{p.kind}</p>
            <p
              className={`mt-1 text-xs ${p.configured ? "text-green-400" : "text-amber-400"}`}
            >
              {p.configured ? "ready" : "not configured"}
            </p>
          </div>
        ))}
      </div>

      <p className="text-xs text-zinc-600">
        {configured.length} of {(health?.providers ?? []).length} providers
        ready
        {health ? ` · backend v${health.version} · db ${health.db}` : ""}.
        Keyless providers work with zero setup.
      </p>
    </div>
  );
}
