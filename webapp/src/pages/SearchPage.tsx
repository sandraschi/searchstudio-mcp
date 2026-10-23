import { Search } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { apiGet, type Hit, type Receipt } from "@/api/client";
import { cn } from "@/lib/cn";

const KINDS = [
  { id: "fleet-local", label: "Fleet-local" },
  { id: "knowledge", label: "Knowledge" },
  { id: "serp", label: "Web" },
];

interface SearchResponse {
  success: boolean;
  total: number;
  hits: Hit[];
  receipts: Receipt[];
  error?: string;
}

export default function SearchPage() {
  const [params] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") ?? "");
  const [kinds, setKinds] = useState<string[]>([
    "fleet-local",
    "knowledge",
    "serp",
  ]);
  const [limit, setLimit] = useState(10);
  const [timeFilter, setTimeFilter] = useState("any");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState("");

  const run = useCallback(
    async (q: string) => {
      const text = q.trim();
      if (!text || kinds.length === 0) return;
      setLoading(true);
      setError("");
      try {
        const data = await apiGet<SearchResponse>(
          `/api/search?q=${encodeURIComponent(text)}&kinds=${kinds.join(",")}&limit=${limit}&time_filter=${timeFilter}`,
        );
        setResult(data);
      } catch (e) {
        setError(String(e));
      } finally {
        setLoading(false);
      }
    },
    [kinds, limit, timeFilter],
  );

  const ranDeepLink = useRef(false);

  useEffect(() => {
    if (ranDeepLink.current) return;
    ranDeepLink.current = true;
    const q = params.get("q");
    if (q) {
      setQuery(q);
      run(q);
    }
  }, [params, run]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Search size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Search console</h1>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 space-y-3">
        <div className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run(query)}
            placeholder="Ask anything fresh…"
            data-testid="search-input"
            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={() => run(query)}
            disabled={loading}
            data-testid="search-button"
            className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <span className="text-zinc-500">Kinds:</span>
          {KINDS.map((k) => (
            <label
              key={k.id}
              className="flex cursor-pointer items-center gap-1.5 text-zinc-300"
            >
              <input
                type="checkbox"
                checked={kinds.includes(k.id)}
                onChange={() =>
                  setKinds((prev) =>
                    prev.includes(k.id)
                      ? prev.filter((x) => x !== k.id)
                      : [...prev, k.id],
                  )
                }
                className="rounded border-zinc-600"
              />
              {k.label}
            </label>
          ))}
          <span className="text-zinc-500">Limit:</span>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1 text-xs"
          >
            {[5, 10, 20, 30, 50].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <span className="text-zinc-500">Freshness:</span>
          <select
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value)}
            data-testid="time-filter"
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1 text-xs"
          >
            <option value="any">Any time</option>
            <option value="day">Past day</option>
            <option value="week">Past week</option>
            <option value="month">Past month</option>
            <option value="year">Past year</option>
          </select>
        </div>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {result && (
        <>
          <p className="text-xs text-zinc-500" data-testid="search-count">
            {result.total} hits · {result.receipts.filter((r) => r.ok).length}/
            {result.receipts.length} providers answered
          </p>
          <div className="space-y-2" data-testid="search-results">
            {result.hits.map((h) => {
              // Paper hits (fleet-local: arxiv-mcp, arxiv-depot) get the rich
              // card: server badge, authors, expandable abstract, PDF link,
              // and a handoff into the sibling arxiv-mcp webapp (claimed
              // port 10771, see operations/WEBAPP_PORTS.md). Everything else
              // keeps the flat link card.
              const isPaper = h.kind === "fleet-local";
              if (!isPaper) {
                return (
                  <a
                    key={`${h.provider}:${h.url}`}
                    href={h.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 hover:border-zinc-600"
                  >
                    <p className="text-sm font-medium text-zinc-100">
                      {h.title}
                    </p>
                    <p className="mt-0.5 line-clamp-2 text-xs text-zinc-400">
                      {h.snippet}
                    </p>
                    <p className="mt-1 flex gap-2 text-[11px] text-zinc-500">
                      <span className="rounded bg-zinc-800 px-1.5 py-0.5">
                        {h.provider}
                      </span>
                      <span className="rounded bg-zinc-800 px-1.5 py-0.5">
                        {h.kind}
                      </span>
                      <span className="truncate">{h.url}</span>
                    </p>
                  </a>
                );
              }
              return (
                <div
                  key={`${h.provider}:${h.url}`}
                  data-testid="paper-hit"
                  className="block rounded-xl border border-zinc-800 bg-zinc-900/50 p-3"
                >
                  <a
                    href={h.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-medium text-zinc-100 hover:underline"
                  >
                    {h.title}
                  </a>
                  <p className="mt-1 flex flex-wrap gap-1.5 text-[11px] text-zinc-500">
                    {h.server && (
                      <span className="rounded bg-amber-900/40 px-1.5 py-0.5 text-amber-300">
                        {h.server}
                      </span>
                    )}
                    <span className="rounded bg-zinc-800 px-1.5 py-0.5">
                      {h.provider}
                    </span>
                    {h.published && <span>{h.published}</span>}
                    {h.categories && h.categories.length > 0 && (
                      <span className="truncate">
                        {h.categories.join(", ")}
                      </span>
                    )}
                  </p>
                  {h.authors && h.authors.length > 0 && (
                    <p className="mt-1 text-xs text-zinc-400">
                      {h.authors.join(", ")}
                    </p>
                  )}
                  {h.snippet && (
                    <details className="mt-1">
                      <summary className="cursor-pointer text-[11px] text-zinc-500">
                        Abstract
                      </summary>
                      <p className="mt-0.5 text-xs leading-relaxed text-zinc-400">
                        {h.snippet}
                      </p>
                    </details>
                  )}
                  <p className="mt-1.5 flex flex-wrap gap-3 text-[11px]">
                    <a
                      href={h.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary hover:underline"
                    >
                      Paper page
                    </a>
                    {h.pdf_url && (
                      <a
                        href={h.pdf_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary hover:underline"
                      >
                        PDF
                      </a>
                    )}
                    <a
                      href="http://127.0.0.1:10771/search"
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary hover:underline"
                      title="Open the sibling arxiv-mcp webapp search"
                    >
                      Open in arxiv-mcp
                    </a>
                  </p>
                </div>
              );
            })}
            {result.hits.length === 0 && (
              <p className="text-sm text-zinc-500">
                No hits. Check the receipts below - if no provider answered,
                nothing was searched.
              </p>
            )}
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-3">
            <p className="text-xs font-medium text-zinc-400">Receipts</p>
            <div className="mt-1 space-y-1">
              {result.receipts.map((r) => (
                <p
                  key={r.provider}
                  className="flex flex-wrap gap-x-2 text-[11px] text-zinc-500"
                >
                  <span
                    className={cn(
                      "font-mono",
                      r.ok ? "text-green-400" : "text-red-400",
                    )}
                  >
                    {r.provider}
                  </span>
                  <span>
                    {r.ok ? `${r.count} hits, ${r.latency_ms}ms` : r.error}
                  </span>
                  {r.blocked && (
                    <span className="text-amber-400">(blocked)</span>
                  )}
                  {!r.configured && (
                    <span className="text-amber-400">(not configured)</span>
                  )}
                  {r.ok && timeFilter !== "any" && (
                    <span className="text-zinc-500">
                      {r.time_filter_applied
                        ? "(freshness applied)"
                        : "(unfiltered)"}
                    </span>
                  )}
                </p>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
