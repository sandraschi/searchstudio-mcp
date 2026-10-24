import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "@/api/client";
import GogglesSection from "@/components/GogglesSection";
import { cn } from "@/lib/cn";

interface ProviderConfig {
  name: string;
  title: string;
  tagline: string;
  keyName: string;
  keyUrl: string;
  endpoint: string;
  auth: string;
  params: string[];
  cost: string;
  useCases: string[];
  receiptNotes: string[];
  docsUrl: string;
}

const CONFIG: Record<string, ProviderConfig> = {
  brave: {
    name: "brave",
    title: "Brave",
    tagline:
      "Independent-index search (no Google/Bing dependency): clean snippets with server-side recency, plus ranking lenses you control.",
    keyName: "BRAVE_API_KEY",
    keyUrl: "https://brave.com/search/api",
    endpoint: "GET https://api.search.brave.com/res/v1/web/search",
    auth: "X-Subscription-Token header",
    params: [
      "count: capped at 20 per call",
      "freshness: pd / pw / pm / py mapped from day / week / month / year, honored server-side",
      "goggles: your enabled lens URLs, sent only when you enable them",
    ],
    cost: "About $5 per 1,000 queries with a small monthly free credit. Lenses cost nothing extra.",
    useCases: [
      "A second index, not a second opinion (raw-ranked counterpart to Tavily)",
      "Source curation: boost docs, downrank farms, discard junk domains via Goggles",
      "Freshness-sensitive queries (recency is server-side, not appended text)",
    ],
    receiptNotes: [
      "ok with hits: check goggles_applied - empty means default Brave ranking",
      "unconfigured stub when no key: fan-out continues without it",
    ],
    docsUrl: "https://brave.com/search/api",
  },
  exa: {
    name: "exa",
    title: "Exa",
    tagline:
      "Neural search: finds by meaning, not keywords. Tavily's semantic counterpart for idea-shaped questions and papers.",
    keyName: "EXA_API_KEY",
    keyUrl: "https://dashboard.exa.ai/api-keys",
    endpoint: "POST https://api.exa.ai/search",
    auth: "x-api-key header",
    params: [
      "numResults: capped at 10 per call",
      "startPublishedDate: computed from the real clock when you filter by time",
      "Response text + publishedDate + score mapped to snippet / published / score",
    ],
    cost: "Free tier to start, then pay-as-you-go credits with no subscription. Our adapter sends plain search calls (no paid answer/crawl add-ons).",
    useCases: [
      "You know the idea but not the words",
      "Research papers (Exa's paper index plus neural matching)",
      "When keyword engines return confident junk - meaning match sidesteps it",
    ],
    receiptNotes: [
      "Meaning-based hits are exempt from the junk check (good hits need not share query words)",
      "unconfigured stub when no key: fan-out continues without it",
    ],
    docsUrl: "https://exa.ai",
  },
  tavily: {
    name: "tavily",
    title: "Tavily",
    tagline:
      "AI-native ranked search built for LLM agents: ranked results plus page content, recency honored server-side. The quality pipe.",
    keyName: "TAVILY_API_KEY",
    keyUrl: "https://tavily.com",
    endpoint: "POST https://api.tavily.com/search",
    auth: "Bearer token header",
    params: [
      "max_results: capped at 10 per call",
      "include_answer: false, include_raw_content: false (snippets only - full pages are a Phase 3 enrichment)",
      "time_range: day / week / month / year, honored server-side",
      "Our adapter uses basic depth (1 credit per search, not 2)",
    ],
    cost: "Free Researcher plan (1,000 credits/month, no card). Paid from $30/month (4,000 credits), or about $0.008/credit pay-as-you-go.",
    useCases: [
      "Hard questions: research, comparisons, decisions (spend it here, not on navigational lookups)",
      "Freshness-sensitive queries (real server-side filter, receipt says time_filter_applied)",
      "Grounding answers with ranked + content snippets",
    ],
    receiptNotes: [
      "Score and published_date mapped from the API (relevance-ranked merge uses them)",
      "unconfigured stub when no key: fan-out continues without it",
    ],
    docsUrl: "https://docs.tavily.com",
  },
};

export default function ProviderPage({ name }: { name: string }) {
  const cfg = CONFIG[name];
  const [configured, setConfigured] = useState<boolean | null>(null);

  useEffect(() => {
    apiGet<{ configured?: Record<string, boolean> }>("/api/providers")
      .then((d) => setConfigured(!!d.configured?.[name]))
      .catch(() => setConfigured(null));
  }, [name]);

  if (!cfg) {
    return <p className="text-sm text-red-400">Unknown provider: {name}</p>;
  }

  return (
    <div className="space-y-4" data-testid={`provider-page-${name}`}>
      <div className="flex items-center gap-2">
        <h1 className="text-2xl font-bold tracking-tight">{cfg.title}</h1>
        {configured !== null && (
          <span
            className={cn(
              "rounded px-2 py-0.5 text-xs",
              configured
                ? "bg-green-900/40 text-green-300"
                : "bg-amber-900/40 text-amber-300",
            )}
          >
            {configured ? "key set" : "no key"}
          </span>
        )}
      </div>
      <p className="text-sm leading-relaxed text-zinc-300">{cfg.tagline}</p>

      {!configured && (
        <p className="rounded-xl border border-amber-800 bg-amber-950/30 p-3 text-xs text-amber-200">
          No {cfg.keyName} set: this provider returns a declared stub and the
          fan-out continues without it.{" "}
          <Link to="/settings" className="underline">
            Add the key in Settings
          </Link>{" "}
          (live, no restart).
        </p>
      )}

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
          How we call it
        </h2>
        <p className="mt-1 font-mono text-xs text-zinc-200">{cfg.endpoint}</p>
        <p className="mt-1 text-xs text-zinc-400">Auth: {cfg.auth}</p>
        <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-zinc-400">
          {cfg.params.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
          Cost
        </h2>
        <p className="mt-1 text-xs leading-relaxed text-zinc-400">{cfg.cost}</p>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
          When to use it
        </h2>
        <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-zinc-400">
          {cfg.useCases.map((u) => (
            <li key={u}>{u}</li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
          Reading its receipts
        </h2>
        <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-zinc-400">
          {cfg.receiptNotes.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
        <p className="mt-2 text-xs text-zinc-500">
          <a
            href={cfg.docsUrl}
            target="_blank"
            rel="noreferrer"
            className="text-primary hover:underline"
          >
            Vendor docs
          </a>{" "}
          ·{" "}
          <Link
            to={`/search?providers=${cfg.name}`}
            className="text-primary hover:underline"
          >
            Try {cfg.title}-only search
          </Link>
        </p>
      </div>

      {name === "brave" && <GogglesSection />}
    </div>
  );
}
