import { Search } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  apiGet,
  type Hit,
  type PaperText,
  type ProviderInfo,
  type Receipt,
} from "@/api/client";
import { cn } from "@/lib/cn";

const KINDS = [
  { id: "fleet-local", label: "Fleet-local" },
  { id: "knowledge", label: "Knowledge" },
  { id: "serp", label: "Web" },
];

const FULLTEXT_DISPLAY_LIMIT = 12000;

function PaperHitCard({ hit }: { hit: Hit }) {
  // Title click toggles the abstract (stays in search context); full text
  // loads lazily behind its own button via the backend proxy.
  const [abstractOpen, setAbstractOpen] = useState(false);
  const [textOpen, setTextOpen] = useState(false);
  const [textState, setTextState] = useState<
    "idle" | "loading" | "done" | "error"
  >("idle");
  const [markdown, setMarkdown] = useState("");
  const [textError, setTextError] = useState("");
  const [textTruncated, setTextTruncated] = useState(false);

  const loadFullText = useCallback(async () => {
    if (!hit.paper_id) return;
    if (textState === "done") {
      setTextOpen((v) => !v);
      return;
    }
    setTextOpen(true);
    setTextState("loading");
    setTextError("");
    try {
      const res = await apiGet<PaperText>(
        `/api/paper/full-text?paper_id=${encodeURIComponent(hit.paper_id)}`,
      );
      if (!res.success) {
        setTextState("error");
        setTextError(res.error || "No text returned.");
        return;
      }
      setMarkdown(res.markdown ?? "");
      setTextTruncated(!!res.truncated);
      setTextState("done");
    } catch (e) {
      setTextState("error");
      setTextError(e instanceof Error ? e.message : "Fetch failed.");
    }
  }, [hit.paper_id, textState]);

  const shown =
    markdown.length > FULLTEXT_DISPLAY_LIMIT
      ? `${markdown.slice(0, FULLTEXT_DISPLAY_LIMIT)}\n\n[cut for display - open in arxiv-mcp for the rest]`
      : markdown;

  return (
    <div
      data-testid="paper-hit"
      className="block rounded-xl border border-zinc-800 bg-zinc-900/50 p-3"
    >
      <button
        type="button"
        onClick={() => setAbstractOpen((v) => !v)}
        data-testid="paper-abstract-toggle"
        title="Click to show/hide the abstract"
        className="block w-full text-left text-sm font-medium text-zinc-100 hover:underline"
      >
        <span className="mr-1 inline-block w-3 text-zinc-500">
          {abstractOpen ? "-" : "+"}
        </span>
        {hit.title}
      </button>
      <p className="mt-1 flex flex-wrap gap-1.5 text-[11px] text-zinc-500">
        {hit.server && (
          <span className="rounded bg-amber-900/40 px-1.5 py-0.5 text-amber-300">
            {hit.server}
          </span>
        )}
        <span className="rounded bg-zinc-800 px-1.5 py-0.5">
          {hit.provider}
        </span>
        {hit.published && <span>{hit.published}</span>}
        {hit.categories && hit.categories.length > 0 && (
          <span className="truncate">{hit.categories.join(", ")}</span>
        )}
      </p>
      {hit.authors && hit.authors.length > 0 && (
        <p className="mt-1 text-xs text-zinc-400">{hit.authors.join(", ")}</p>
      )}
      {abstractOpen && hit.snippet && (
        <p
          data-testid="paper-abstract"
          className="mt-1 text-xs leading-relaxed text-zinc-400"
        >
          {hit.snippet}
        </p>
      )}
      <p className="mt-1.5 flex flex-wrap gap-3 text-[11px]">
        <button
          type="button"
          onClick={() => setAbstractOpen((v) => !v)}
          className="text-primary hover:underline"
        >
          Abstract
        </button>
        {hit.paper_id && (
          <button
            type="button"
            onClick={loadFullText}
            data-testid="paper-fulltext-toggle"
            className="text-primary hover:underline"
          >
            {textState === "loading" ? "Loading…" : "Full text"}
          </button>
        )}
        {hit.pdf_url && (
          <a
            href={hit.pdf_url}
            target="_blank"
            rel="noreferrer"
            className="text-primary hover:underline"
          >
            PDF
          </a>
        )}
        <a
          href={hit.url}
          target="_blank"
          rel="noreferrer"
          className="text-primary hover:underline"
        >
          Paper page
        </a>
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
      {textOpen && textState === "loading" && (
        <p className="mt-1 text-[11px] text-zinc-500">Fetching full text…</p>
      )}
      {textOpen && textState === "error" && (
        <p className="mt-1 text-[11px] text-red-400">{textError}</p>
      )}
      {textOpen && textState === "done" && (
        <pre
          data-testid="paper-fulltext"
          className="mt-1 max-h-96 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-950 p-2 text-[11px] leading-relaxed text-zinc-300"
        >
          {shown}
          {textTruncated && "\n\n[backend capped at 100k chars]"}
        </pre>
      )}
    </div>
  );
}

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
  const [allProviders, setAllProviders] = useState<ProviderInfo[]>([]);
  const [providerSel, setProviderSel] = useState<string[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<{ providers: ProviderInfo[] }>("/api/providers")
      .then((d) => setAllProviders(d.providers))
      .catch(() => setAllProviders([]));
  }, []);

  const run = useCallback(
    async (q: string) => {
      const text = q.trim();
      if (!text || kinds.length === 0) return;
      setLoading(true);
      setError("");
      const subset =
        providerSel !== null && providerSel.length < allProviders.length
          ? `&providers=${providerSel.map(encodeURIComponent).join(",")}`
          : "";
      try {
        const data = await apiGet<SearchResponse>(
          `/api/search?q=${encodeURIComponent(text)}&kinds=${kinds.join(",")}&limit=${limit}&time_filter=${timeFilter}${subset}`,
        );
        setResult(data);
      } catch (e) {
        setError(String(e));
      } finally {
        setLoading(false);
      }
    },
    [kinds, limit, timeFilter, providerSel, allProviders.length],
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
        {allProviders.length > 0 && (
          <div
            className="flex flex-wrap items-center gap-3 text-xs"
            data-testid="provider-filter"
          >
            <span className="text-zinc-500">Providers:</span>
            {allProviders.map((p) => {
              const active =
                providerSel === null || providerSel.includes(p.name);
              return (
                <label
                  key={p.name}
                  title={
                    p.configured ? p.name : `${p.name} (needs key/service)`
                  }
                  className="flex cursor-pointer items-center gap-1.5 text-zinc-300"
                >
                  <input
                    type="checkbox"
                    checked={active}
                    onChange={() =>
                      setProviderSel((prev) => {
                        const all = allProviders.map((x) => x.name);
                        const cur = prev === null ? all : prev;
                        const next = cur.includes(p.name)
                          ? cur.filter((x) => x !== p.name)
                          : [...cur, p.name];
                        return next.length === all.length ? null : next;
                      })
                    }
                    className="rounded border-zinc-600"
                  />
                  {p.name}
                  {!p.configured && <span className="text-amber-500">*</span>}
                </label>
              );
            })}
            <span className="text-zinc-600">(* needs key/service)</span>
          </div>
        )}
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
              return <PaperHitCard key={`${h.provider}:${h.url}`} hit={h} />;
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
