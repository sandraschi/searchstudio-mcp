import { CircleHelp } from "lucide-react";

const FAQ: Array<[string, string]> = [
  [
    "Which providers are free?",
    "OpenSERP-local (needs Docker), DuckDuckGo, Wikipedia, and arxiv-mcp cost nothing. Tavily/Exa/Brave need keys.",
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
    "Process env (TAVILY_API_KEY etc.), never the repo, never chat. Restart the backend after setting.",
  ],
  [
    "What is mode=any?",
    "Fastest provider kind with hits wins; full receipts still returned. Use under heavy blocking.",
  ],
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
      <p className="text-xs text-zinc-600">
        Deeper analysis: patterns/WEB_SEARCH_IS_IFFY.md in mcp-central-docs.
        Provider detail: integrations/openserp/README.md.
      </p>
    </div>
  );
}
