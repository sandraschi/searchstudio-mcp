import { CircleHelp } from "lucide-react";

const FAQ: Array<[string, string]> = [
  [
    "Which providers are free?",
    "OpenSERP-local (needs Docker), DuckDuckGo, Wikipedia, arxiv-mcp and arxiv-depot cost nothing. Tavily/Exa need keys; Brave arrives later.",
  ],
  [
    "Search returned nothing. Is that real?",
    "Only if receipts show providers answered. Empty hits + failed receipts means nothing was searched - check Providers.",
  ],
  [
    "Why does one engine work and another fail?",
    "Independent indexes, query parsing, and bot-luck per engine per minute. Fan-out exists for exactly this.",
  ],
  [
    "Do I need Docker?",
    "Only for OpenSERP-local. Everything else works without it.",
  ],
  [
    "Where do keys go?",
    "Paste them in Settings (active immediately, stored server-side, never shown back) or set process env (wins on conflict, needs backend restart). Never the repo, never chat.",
  ],
  [
    "How do I know a key works?",
    "Settings has a Test button per key: one minimal live call, valid/invalid verdict with latency. No guessing.",
  ],
  [
    "What is mode=any?",
    "Fastest provider kind with hits wins; full receipts still returned. Use under heavy blocking.",
  ],
];

const PROVIDERS: Array<{
  name: string;
  what: string;
  key: string;
  url: string;
}> = [
  {
    name: "arxiv-mcp",
    what: "Fresh preprint search across 7 servers (arXiv itself plus bioRxiv, medRxiv, ChemRxiv, Research Square, SocArXiv, PsyArXiv) via the sibling backend.",
    key: "None (needs the sibling on :10770)",
    url: "https://github.com/sandraschi/arxiv-mcp",
  },
  {
    name: "arxiv-depot",
    what: "Your personally saved papers (ingested full text) from the same sibling: keyword, semantic, or hybrid search over your library. Your papers, not the world's.",
    key: "None (same sibling)",
    url: "https://github.com/sandraschi/arxiv-mcp",
  },
  {
    name: "Wikipedia",
    what: "The free encyclopedia via its official API: entities, places, techniques, history. Starting point, never the final citation.",
    key: "None",
    url: "https://www.wikipedia.org",
  },
  {
    name: "OpenSERP-local",
    what: "Self-hosted open-source search (Google, Bing, Yandex, Baidu, DuckDuckGo, Ecosia engines) running in your Docker. Free replacement for paid search APIs.",
    key: "None (needs Docker + container on :7000)",
    url: "https://github.com/karust/openserp",
  },
  {
    name: "DuckDuckGo",
    what: "Privacy search engine queried directly: independent index and bot-luck from Google, which is exactly why it is in the fan-out.",
    key: "None",
    url: "https://duckduckgo.com",
  },
  {
    name: "Tavily",
    what: "AI-native search API built for LLM agents: ranked results plus page content, recency filters. The quality pipe for hard questions.",
    key: "TAVILY_API_KEY (free 1k/mo, no card)",
    url: "https://tavily.com",
  },
  {
    name: "Exa",
    what: "Neural search API: finds by meaning, not just keywords. The semantic counterpart to Tavily's ranking.",
    key: "EXA_API_KEY",
    url: "https://dashboard.exa.ai/api-keys",
  },
];

export default function HelpPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <CircleHelp size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Help</h1>
      </div>
      <div className="space-y-2">
        {FAQ.map(([q, a]) => (
          <div
            key={q}
            className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
          >
            <p className="text-sm font-medium text-zinc-100">{q}</p>
            <p className="mt-1 text-xs leading-relaxed text-zinc-400">{a}</p>
          </div>
        ))}
      </div>
      <div className="space-y-2" data-testid="help-providers">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
          Providers, explained
        </h2>
        {PROVIDERS.map((p) => (
          <div
            key={p.name}
            className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
          >
            <p className="font-mono text-sm text-zinc-100">{p.name}</p>
            <p className="mt-1 text-xs leading-relaxed text-zinc-400">
              {p.what}
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              Key: {p.key} ·{" "}
              <a
                href={p.url}
                target="_blank"
                rel="noreferrer"
                className="text-primary hover:underline"
              >
                {p.url.replace("https://", "")}
              </a>
            </p>
          </div>
        ))}
      </div>
      <p className="text-xs text-zinc-600">
        Deeper analysis: patterns/WEB_SEARCH_IS_IFFY.md in mcp-central-docs.
        Full provider reference: docs/PROVIDERS.md in this repo. OpenSERP
        detail: integrations/openserp/README.md.
      </p>
    </div>
  );
}
