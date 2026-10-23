import { CircleHelp } from "lucide-react";
import { useMemo, useState } from "react";

type TabId =
  | "overview"
  | "wrappee"
  | "api"
  | "troubleshoot"
  | "faq"
  | "providers"
  | "defenses";

const TABS: Array<{ id: TabId; label: string; desc: string }> = [
  {
    id: "overview",
    label: "Overview",
    desc: "What this app is and where everything lives",
  },
  {
    id: "wrappee",
    label: "Backend + data",
    desc: "Core backend, data store, how to verify",
  },
  {
    id: "api",
    label: "API + ports",
    desc: "Ports, env vars, endpoints, restart",
  },
  {
    id: "troubleshoot",
    label: "Troubleshoot",
    desc: "Symptom, cause, exact fix",
  },
  { id: "faq", label: "FAQ", desc: "Real questions with concrete answers" },
  {
    id: "providers",
    label: "Providers",
    desc: "Every provider name, explained",
  },
  {
    id: "defenses",
    label: "Defenses",
    desc: "Bot walls out there, and how we answer them",
  },
];

const PAGES: Array<[string, string]> = [
  [
    "Dashboard",
    "Hero + provider readiness cards + onboarding cue when optional providers are unset.",
  ],
  [
    "Search",
    "One query across all kinds, merged hits, per-provider receipts, coverage line.",
  ],
  [
    "Providers",
    "Rolling health scoreboard per provider: attempts, success rate, latency, blocks.",
  ],
  ["Activity", "7-day view of the SQLite attempt ledger."],
  [
    "Tools",
    "MCP surface: searchops portmanteau, models_lookup, provider_health_app Prefab card.",
  ],
  ["Skills", "Renders skill://super-search (SKILL.md) for agents and humans."],
  [
    "Chat",
    "Local-first chat via Ollama on :11434, 3 personalities plus custom prompt.",
  ],
  [
    "Settings",
    "Paste Tavily/Exa/Brave keys (server-side file, live) + Camoufox fallback switch.",
  ],
  [
    "Logs",
    "Where backend output and the SQLite ledger live (no log API, see below).",
  ],
  ["Help", "This page: the full contract per WEBAPP_HELP_STANDARD."],
];

const FIXES: Array<{ symptom: string; cause: string; fix: string }> = [
  {
    symptom: '"Search returned nothing at all" (empty hits list)',
    cause:
      "First documented 2026-10-11 (README live-run story): one engine answered with junk and the preprint pipe with unrelated papers, both correctly dropped. Empty hits with failed receipts means nothing was searched, not that nothing exists.",
    fix: "Read the receipts first (they name the failing pipe), then open Providers. Verify GET http://127.0.0.1:11226/api/health returns success true.",
  },
  {
    symptom:
      '"OpenSERP-local always fails" (receipt error mentions Docker or :7000)',
    cause:
      "Known since port claim 2026-10-03: OpenSERP-local needs Docker Desktop plus the openserp container on :7000. Dead service returns an error receipt, never a silent zero.",
    fix: "Start Docker Desktop (needs BIOS virtualization), run the openserp container on :7000. Verify: GET http://127.0.0.1:7000/google/search?text=test&limit=1.",
  },
  {
    symptom:
      '"Tavily says not configured" (receipt configured false + setup hint)',
    cause:
      "By design since v0.1.0 (assessment 2026-09-30): Tavily/Exa/Brave without a key return a declared stub, counted in receipts. Not an error.",
    fix: "Free key at tavily.com (1k/mo, no card). Paste it on the Settings page (active immediately, no restart) or set TAVILY_API_KEY in env and restart the backend. Keyless providers keep working meanwhile.",
  },
  {
    symptom: '"Wikipedia 403 errors"',
    cause:
      "Documented since v0.1.0: Wikimedia blocks generic User-Agents. The backend already sends a courtesy UA identifying the app.",
    fix: "No action unless receipts show it again after 2026-10-11: then Wikimedia changed policy. Report with timestamp and receipt text.",
  },
  {
    symptom: '"Backend will not start / port busy" (:11226 in use)',
    cause:
      "Zombie pile-up pattern (fleet-wide): a stale backend still owns :11226 after a crash or a killed window.",
    fix: "Run start.ps1 (it clears port zombies first). If a foreign process holds the port, stop that first. Never taskkill an NSSM child: sc.exe stop <svc> then sc.exe start <svc>, then verify a NEW pid owns the port.",
  },
  {
    symptom: '"command not found: uv" or "bun missing"',
    cause:
      "Naked PC without dev tools (first-install path, documented in INSTALL.md).",
    fix: "Run start.bat (winget-installs uv, Node, Bun, just via Require-Command). Close and reopen the terminal so PATH refreshes, then retry.",
  },
  {
    symptom: '"Chat says no LLM" (Chat page disabled state)',
    cause:
      "Chat is local-first by design: it needs Ollama on :11434 with at least one chat model. No cloud fallback in this repo.",
    fix: "Install Ollama (winget install Ollama.Ollama), then ollama pull qwen3:8b (or any chat model). Verify GET http://127.0.0.1:11434/api/tags answers, then reload Chat.",
  },
];

const FAQS: Array<[string, string]> = [
  [
    "Where is my data?",
    "Provider attempts only: data/searchstudio.sqlite3 (SQLite WAL, attempt ledger: timestamp, provider, ok, latency, count, blocked). No corpus, no index, no user content. Keys: data/provider_keys.json (gitignored, never returned by any API). Prefs: data/preferences.json (Camoufox switch). Catalog cache: data/modelsdev_catalog.json. Delete the sqlite file to reset history; the backend recreates it.",
  ],
  [
    "How do I add a provider key (Tavily / Exa / Brave)?",
    "Settings page: paste into the password input, Save (writes data/provider_keys.json server-side, active on the next search, no restart), then Test (one live limit=1 call, valid/invalid verdict with latency). Or set TAVILY_API_KEY / EXA_API_KEY / BRAVE_API_KEY in process env (wins over the file, needs backend restart). Never the repo, never chat.",
  ],
  [
    "How do I rebuild or resync?",
    "Health ledger: delete data/searchstudio.sqlite3 and restart the backend (fresh scoreboard). Model catalog: models_lookup with refresh true, or wait at most 24h (a failed refresh with a usable cache serves stale data and says so in the receipt). No other state exists: no sessions, no background tasks.",
  ],
  [
    "How do clients connect (Claude / agents / REST)?",
    "Claude Desktop: INSTALL.md Option C snippet (command uv, args --directory <repo> run python -m super_search_mcp, env PYTHONUNBUFFERED 1), then restart Claude. Agents over HTTP: MCP streamable HTTP at http://127.0.0.1:11226/mcp. Fleet REST: GET /api/search?q=... (same handlers as the portmanteau). Skill: resource skill://super-search, also GET /skill/super-search.",
  ],
  [
    "Which service restarts after a code change?",
    "Backend: restart the Starlette process on :11226 (start.ps1, or the service manager when service-installed). Frontend: Vite on :11225 hot-reloads, no restart needed. Provider keys and the Camoufox switch are read live on every search, no restart.",
  ],
  [
    "Where are the logs?",
    "No /api/logs endpoint in this repo. Backend console output (the start.ps1 window, or the NSSM service log when service-managed) plus full server-side tracebacks on tool failure. Provider history: the SQLite ledger, surfaced on the Activity page (7-day view). Start at the Logs page, it lists exactly these three.",
  ],
  [
    "Which providers are free?",
    "OpenSERP-local (needs Docker), DuckDuckGo, Wikipedia, arxiv-mcp and arxiv-depot cost nothing. Tavily, Exa and Brave need keys.",
  ],
  [
    "Search returned nothing. Is that real?",
    "Only if receipts show providers answered. Empty hits plus failed receipts means nothing was searched, so check Providers and /api/health first.",
  ],
  [
    "Why does one engine work and another fail?",
    "Independent indexes, query parsing, and bot-luck per engine per minute. Fan-out exists for exactly this: disagreement preserved is a feature.",
  ],
  [
    "Do I need Docker?",
    "Only for OpenSERP-local (the self-hosted engine pool on :7000). DuckDuckGo and Wikipedia answer with zero setup; the arxiv-mcp sibling, browser-mcp, Ollama, and all keys are likewise independent - a missing one only ever costs its own provider, reported in its receipt.",
  ],
  [
    "What needs to be installed besides SearchStudio itself?",
    "Nothing is mandatory. OpenSERP-local needs Docker Desktop plus the openserp container on :7000. The two fleet-local providers need the arxiv-mcp backend on :10770 (down = named error receipt, the rest keeps working). The breaker chain needs browser-mcp on :10780 (off in Settings or via empty BROWSER_MCP_URL). Chat needs Ollama on :11434 with any chat model. Tavily / Exa / Brave keys add providers; unset means a declared stub. Dashboard cards plus GET /api/health show what is ready before you search.",
  ],
  [
    "What is mode=any?",
    "Fastest provider kind with hits wins; full receipts still returned. Use under heavy blocking when one good answer beats a merged best-of-all.",
  ],
  [
    "What is unrelated in a receipt?",
    "The provider answered, but not one hit mentions the query (an engine serving junk to automated traffic, or a broken upstream search). Its hits are dropped on purpose and count still shows what it returned. Meaning-based providers (Exa, arxiv library) are exempt from the check.",
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
    what: "Fresh preprint search across 7 servers (arXiv plus bioRxiv, medRxiv, ChemRxiv, Research Square, SocArXiv, PsyArXiv) via the sibling backend. Needs the sibling on :10770, degrades gracefully when down.",
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
    what: "The free encyclopedia via its official API: entities, places, techniques, history. Starting point, never the final citation. Matches multi-word queries loosely.",
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
    what: "Privacy search engine queried directly: independent index and bot-luck from Google, which is exactly why it is in the fan-out. Retries through the authorized breaker chain when bot-challenged (receipt marks the leg in via).",
    key: "None",
    url: "https://duckduckgo.com",
  },
  {
    name: "Tavily",
    what: "AI-native search API built for LLM agents: ranked results plus page content, recency filters honored server-side (day/week/month/year). The quality pipe for hard questions (research, comparisons, decisions). Free Researcher plan (1,000 credits/mo, no card); paid from $30/mo or about $0.008/credit pay-as-you-go, pricing page rules.",
    key: "TAVILY_API_KEY (free 1k/mo, no card)",
    url: "https://tavily.com",
  },
  {
    name: "Exa",
    what: "Neural search API: finds by meaning, not just keywords, plus full-page extraction and research-paper search. The semantic counterpart to Tavily for idea-shaped questions. Free tier, then pay-as-you-go credits with no subscription. Exempt from the junk check because good hits need not share query words.",
    key: "EXA_API_KEY",
    url: "https://dashboard.exa.ai/api-keys",
  },
  {
    name: "Brave",
    what: "Independent-index search API (no Google/Bing dependency): clean snippets with server-side recency (day/week/month/year). The raw-ranked counterpart to Tavily when you want a second index, not a second opinion. About $5 per 1,000 queries with a small monthly free credit.",
    key: "BRAVE_API_KEY",
    url: "https://brave.com/search/api",
  },
];

export default function HelpPage() {
  const [tab, setTab] = useState<TabId>("overview");
  const [query, setQuery] = useState("");
  const q = query.trim().toLowerCase();

  const fixes = useMemo(() => {
    if (!q) return FIXES;
    return FIXES.filter((f) =>
      `${f.symptom} ${f.cause} ${f.fix}`.toLowerCase().includes(q),
    );
  }, [q]);

  const faqs = useMemo(() => {
    if (!q) return FAQS;
    return FAQS.filter(([t, a]) => `${t} ${a}`.toLowerCase().includes(q));
  }, [q]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <CircleHelp size={22} className="text-zinc-200" />
        <h1 className="text-2xl font-bold tracking-tight">Help</h1>
      </div>

      <div className="border-b border-zinc-800" data-testid="help-tabs">
        <div className="flex flex-wrap gap-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              data-testid={`help-tab-${t.id}`}
              title={t.desc}
              className={`border-b-2 px-3 py-2 text-left ${
                tab === t.id
                  ? "border-amber-400 text-zinc-100"
                  : "border-transparent text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <span className="block text-sm font-medium">{t.label}</span>
              <span className="block text-[11px] text-zinc-500">{t.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {tab === "overview" && (
        <div className="space-y-3">
          <p className="text-sm leading-relaxed text-zinc-300">
            SearchStudio sends one query to several search providers at once
            (web engines, Wikipedia, your fleet paper indexes) and returns
            merged results with a receipt per provider. When a pipe dies it says
            so: answered, blocked, unrelated, down, or unconfigured. No silent
            zeros, ever.
          </p>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-xs leading-relaxed text-zinc-400">
            <p className="font-mono text-zinc-200">
              Architecture (one line each)
            </p>
            <ul className="mt-1 list-inside list-disc">
              <li>
                UI: Vite dev server on 11225 (this page, proxies /api and /skill
                to the backend).
              </li>
              <li>
                API: Starlette REST plus MCP streamable HTTP on 11226 (routes
                under /api/*, MCP at /mcp).
              </li>
              <li>
                Data: SQLite attempt ledger only, no corpus (see Backend + data
                tab).
              </li>
            </ul>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-xs leading-relaxed text-zinc-400">
            <p className="font-mono text-zinc-200">
              What needs to be running (besides this app)
            </p>
            <ul className="mt-1 list-inside list-disc">
              <li>
                Nothing, for the core: DuckDuckGo plus Wikipedia answer with
                zero setup.
              </li>
              <li>
                Docker plus openserp container on :7000: only for the
                OpenSERP-local provider (missing = error receipt naming Docker).
              </li>
              <li>
                arxiv-mcp backend on :10770: only for the two fleet-local
                providers, preprint search and your paper library (down = named
                error receipt, the rest keeps working).
              </li>
              <li>
                browser-mcp on :10780: only for the one-shot Camoufox retry when
                DuckDuckGo shows a bot challenge (off in Settings or via empty
                BROWSER_MCP_URL).
              </li>
              <li>
                Ollama on :11434 with any chat model: only for the Chat page.
              </li>
              <li>
                Keys Tavily / Exa / Brave: all optional, unset = declared stub.
                Full detail: Backend + data tab, API tab env table, and
                docs/ONBOARDING.md.
              </li>
            </ul>
          </div>
          <div className="space-y-2">
            {PAGES.map(([name, purpose]) => (
              <div
                key={name}
                className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3"
              >
                <p className="text-sm font-medium text-zinc-100">{name}</p>
                <p className="mt-0.5 text-xs text-zinc-400">{purpose}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "wrappee" && (
        <div className="space-y-3">
          <p className="text-sm leading-relaxed text-zinc-300">
            SearchStudio wraps no host app. The &quot;wrapped thing&quot; is its
            own core backend plus data store: a Starlette REST + FastMCP server
            (one portmanteau searchops, plus models_lookup and the
            provider_health_app Prefab card) with a SQLite health ledger.
          </p>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-xs leading-relaxed text-zinc-400">
            <p className="font-mono text-zinc-200">Where data lives</p>
            <ul className="mt-1 list-inside list-disc">
              <li>
                data/searchstudio.sqlite3: provider attempt ledger only (ts,
                provider, kind, ok, latency, count, blocked). WAL mode, advisory
                writes never fail a search.
              </li>
              <li>
                data/provider_keys.json: Settings-page keys (gitignored, never
                logged, never returned by any API; status endpoints report
                set/unset plus source only).
              </li>
              <li>
                data/preferences.json: Camoufox fallback switch (gitignored,
                read live, BROWSER_MCP_URL empty wins as operator hard-off).
              </li>
              <li>
                data/modelsdev_catalog.json: cached models.dev catalog (at most
                one refresh per 24h).
              </li>
            </ul>
            <p className="mt-2 font-mono text-zinc-200">
              Which process owns it
            </p>
            <p>
              Starlette backend on :11226 (start.ps1, or the NSSM service when
              service-managed). MCP stdio runs the same handlers in-process;
              SQLite WAL tolerates concurrent stdio plus HTTP writers.
            </p>
            <p className="mt-2 font-mono text-zinc-200">
              External prerequisites (not owned, only called)
            </p>
            <ul className="mt-1 list-inside list-disc">
              <li>
                :7000 OpenSERP-local (your Docker): missing = error receipt
                naming Docker. Verify: GET
                http://127.0.0.1:7000/google/search?text=test&amp;limit=1.
              </li>
              <li>
                :10770 arxiv-mcp sibling: feeds both fleet-local providers. Down
                = named error receipt with the URL, fan-out continues.
              </li>
              <li>
                :10780 browser-mcp: Camoufox fallback bridge. Empty
                BROWSER_MCP_URL is an operator hard-off and wins over the
                Settings checkbox; the page shows the switch as locked.
              </li>
              <li>
                :11434 Ollama: Chat page only. Verify: GET
                http://127.0.0.1:11434/api/tags answers.
              </li>
              <li>
                Keys Tavily / Exa / Brave: unset = declared stub with a setup
                hint, counted in receipts. Dashboard cards and Settings show
                set/unset plus source (env wins over file).
              </li>
            </ul>
            <p className="mt-2 font-mono text-zinc-200">
              How to verify it is reachable
            </p>
            <p>
              GET /api/health returns success true plus the provider list with
              configured flags. Dashboard shows the same as provider cards;
              Settings shows key status and the fallback switch. First-timer
              setup (Docker, keys, BIOS virtualization gotcha) lives in
              docs/ONBOARDING.md in the repo.
            </p>
            <p className="mt-2">
              <a
                href="https://github.com/sandraschi/searchstudio-mcp/blob/main/docs/ONBOARDING.md"
                target="_blank"
                rel="noreferrer"
                className="text-primary hover:underline"
              >
                Open docs/ONBOARDING.md on GitHub
              </a>
            </p>
          </div>
        </div>
      )}

      {tab === "api" && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
            Ports (verified against operations/WEBAPP_PORTS.md 2026-10-03)
          </h2>
          <div className="overflow-x-auto rounded-xl border border-zinc-800">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-500">
                  <th className="p-2">Port</th>
                  <th className="p-2">Owner</th>
                  <th className="p-2">Notes</th>
                </tr>
              </thead>
              <tbody className="text-zinc-300">
                <tr className="border-b border-zinc-800/50">
                  <td className="p-2 font-mono">11225</td>
                  <td className="p-2">searchstudio-mcp frontend (Vite)</td>
                  <td className="p-2">
                    This UI. Proxies /api and /skill to 11226 (vite.config.ts).
                    strictPort true.
                  </td>
                </tr>
                <tr>
                  <td className="p-2 font-mono">11226</td>
                  <td className="p-2">
                    searchstudio-mcp backend (Starlette + MCP /mcp)
                  </td>
                  <td className="p-2">
                    REST /api/* plus MCP streamable HTTP at /mcp
                    (lifespan-shared). PORT or SUPER_SEARCH_BACKEND_PORT env
                    also honored.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-xs text-zinc-500">
            External dependencies (not owned, only called - each is optional and
            degrades to a named receipt): :7000 OpenSERP-local (your Docker;
            verify GET
            http://127.0.0.1:7000/google/search?text=test&amp;limit=1), :10770
            arxiv-mcp sibling (two fleet-local providers; down = error receipt
            with the URL), :10780 browser-mcp (Camoufox fallback bridge; empty
            URL = hard off), :11434 Ollama (Chat page only; verify GET
            http://127.0.0.1:11434/api/tags).
          </p>

          <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
            Env vars (unset default is correct unless noted)
          </h2>
          <div className="overflow-x-auto rounded-xl border border-zinc-800">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-500">
                  <th className="p-2">Name</th>
                  <th className="p-2">Effect</th>
                </tr>
              </thead>
              <tbody className="text-zinc-300">
                {[
                  [
                    "TAVILY_API_KEY",
                    "Tavily keyed search. Unset = declared stub, everything else keeps working.",
                  ],
                  ["EXA_API_KEY", "Exa neural search. Unset = declared stub."],
                  [
                    "BRAVE_API_KEY",
                    "Brave independent-index search + server-side recency. Unset = declared stub.",
                  ],
                  [
                    "OPENSERP_BASE_URL",
                    "Self-hosted OpenSERP service (default http://127.0.0.1:7000).",
                  ],
                  [
                    "ARXIV_MCP_BASE_URL",
                    "Sibling arxiv-mcp backend (default http://127.0.0.1:10770).",
                  ],
                  [
                    "SUPER_SEARCH_DATA_DIR",
                    "Ledger + key + prefs location (default data).",
                  ],
                  [
                    "SUPER_SEARCH_BACKEND_PORT",
                    "Backend bind port (default 11226; PORT also honored).",
                  ],
                  [
                    "SUPER_SEARCH_FRONTEND_PORT",
                    "Informational: Vite owns its port (11225).",
                  ],
                  [
                    "BROWSER_MCP_URL",
                    "Camoufox fallback bridge (default http://127.0.0.1:10780). Empty = hard off, wins over Settings.",
                  ],
                ].map(([k, v]) => (
                  <tr key={k} className="border-b border-zinc-800/50">
                    <td className="p-2 font-mono">{k}</td>
                    <td className="p-2">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
            Key endpoints (all verified in src/super_search_mcp/backend.py)
          </h2>
          <ul className="list-inside list-disc space-y-1 text-xs text-zinc-400">
            <li>
              <span className="font-mono">GET /api/health</span>: success,
              version, db, providers with configured flags.
            </li>
            <li>
              <span className="font-mono">GET /api/capabilities</span>: MCP
              tools, REST list, provider kinds.
            </li>
            <li>
              <span className="font-mono">GET /api/skills</span> +{" "}
              <span className="font-mono">GET /skill/super-search</span>: skill
              list and SKILL.md content.
            </li>
            <li>
              <span className="font-mono">GET /api/search?q=</span>: same
              handlers as searchops super_search (kinds, providers, limit, mode,
              time_filter query params).
            </li>
            <li>
              <span className="font-mono">
                GET /api/providers?window_hours=24
              </span>
              : health scoreboard plus configured map.
            </li>
            <li>
              <span className="font-mono">GET /api/matrix</span>: self-test
              matrix (same as searchops self_test).
            </li>
            <li>
              <span className="font-mono">
                GET/POST/DELETE /api/provider-keys
              </span>{" "}
              + <span className="font-mono">POST /api/provider-keys/test</span>:
              key status/save/clear (never values) plus one-call key validity
              probe.
            </li>
            <li>
              <span className="font-mono">
                GET/POST /api/settings/fallbacks
              </span>
              : Camoufox switch, reports effective value.
            </li>
            <li>
              <span className="font-mono">POST /mcp</span>: MCP streamable HTTP
              (same tools Claude Desktop uses over stdio).
            </li>
          </ul>
          <p className="text-xs text-zinc-500">
            No VITE_ variables anywhere (verified: vite.config.ts only proxies
            /api and /skill). No /api/logs endpoint (see Logs page note in FAQ).
          </p>

          <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
            Start and restart
          </h2>
          <p className="text-xs leading-relaxed text-zinc-400">
            Normal: run start.ps1 (clears :11225/:11226 zombies first), wait for
            the backend readiness poll, open http://127.0.0.1:11225.
            Backend-only: start.ps1 -BackendOnly. If service-managed: sc.exe
            stop then sc.exe start (never taskkill the child), then verify a NEW
            pid owns :11226 before declaring it back.
          </p>
        </div>
      )}

      {tab === "troubleshoot" && (
        <div className="space-y-3" data-testid="help-fixes">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter fixes (try docker, port, key, chat)..."
            data-testid="help-search"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
          />
          <p className="text-xs text-zinc-500">
            {fixes.length} of {FIXES.length} fixes shown. Every entry traces to
            a documented incident or design record with its first-seen date.
          </p>
          {fixes.map((f) => (
            <div
              key={f.symptom}
              className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
            >
              <p className="text-sm font-medium text-zinc-100">{f.symptom}</p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">
                <span className="text-zinc-500">Cause: </span>
                {f.cause}
              </p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">
                <span className="text-zinc-500">Fix: </span>
                {f.fix}
              </p>
            </div>
          ))}
          {fixes.length === 0 && (
            <p className="text-xs text-zinc-500">No fixes match that filter.</p>
          )}
        </div>
      )}

      {tab === "faq" && (
        <div className="space-y-3" data-testid="help-faq">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter questions (try key, logs, data, docker)..."
            data-testid="help-search"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
          />
          <p className="text-xs text-zinc-500">
            {faqs.length} of {FAQS.length} questions shown.
          </p>
          {faqs.map(([t, a]) => (
            <details
              key={t}
              data-testid="faq-item"
              className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
            >
              <summary className="cursor-pointer text-sm font-medium text-zinc-100">
                {t}
              </summary>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">{a}</p>
            </details>
          ))}
          {faqs.length === 0 && (
            <p className="text-xs text-zinc-500">
              No questions match that filter.
            </p>
          )}
        </div>
      )}

      {tab === "providers" && (
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
          <p className="text-xs text-zinc-600">
            Deeper analysis: patterns/WEB_SEARCH_IS_IFFY.md in mcp-central-docs.
            Full provider reference: docs/PROVIDERS.md in this repo. Source of
            truth for mechanics: docs/ARCHITECTURE.md and docs/TOOLS.md.
          </p>
        </div>
      )}

      {tab === "defenses" && (
        <div className="space-y-3">
          <p className="text-sm leading-relaxed text-zinc-300">
            Web search is an arms race. Sites defend against automated traffic
            because bots cost them bandwidth, skew their metrics, and scrape the
            content they sell ads against. Every defense below is routine on the
            modern web. SearchStudio expects them, names them in receipts,
            routes around what it can, runs a breaker where you authorize one,
            and pays (via keyed APIs) where you prefer not to.
            &quot;Breaker&quot; is our word for an authorized second-try path:
            it fires only after the direct fetch fails, every rescue is labeled
            with its leg, and nothing runs unless you switch it on.
          </p>

          <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
            The walls you will meet
          </h2>
          <div className="space-y-2">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <p className="text-sm font-medium text-zinc-100">
                Rate limits and hard refusals (HTTP 429, 202, empty sets)
              </p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">
                Too many requests from one IP, too fast, and the engine stops
                answering. OpenSERP self-hosted traffic and direct DuckDuckGo
                scrapes both hit this. Receipt: ok false, fault_kind blocked or
                down, with what_to_do and retry_in (DuckDuckGo blocks usually
                clear within the hour).
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <p className="text-sm font-medium text-zinc-100">
                Bot-challenge and barrier pages
              </p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">
                Instead of results you get an interstitial: DuckDuckGo shows
                anomaly-modal, challenge-form, or &quot;not a robot&quot; pages;
                larger sites sit behind Cloudflare-style barriers (JavaScript
                proof-of-work, CAPTCHAs, browser checks). Our DuckDuckGo parser
                detects these markers explicitly: with no authorized breaker the
                answer is reported blocked, never zero results. The breaker
                chain below is the authorized answer for DuckDuckGo-class
                challenges; an armed FlareSolverr sidecar covers IUAM-class
                Cloudflare barriers. Our posture is pragmatic, not preachy:
                solvers and breakers run when you authorize them (Settings
                switch, env), always marked, always bounded. Keyed APIs remain
                the no-fuss path where you prefer not to break anything.
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <p className="text-sm font-medium text-zinc-100">
                Soft blocks: confident junk instead of an error
              </p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">
                The nastiest wall: HTTP 200 with results that have nothing to do
                with your query. Measured 2026-10-11 for &quot;sitagliptin first
                clinical trial&quot;: one engine answered with McDonald&apos;s
                menu pages. Our literal relevance check (anchor term plus half
                the query terms, deliberately lenient) flags all-junk answers as
                fault_kind unrelated, drops the hits, and keeps the count of
                what was returned. Meaning-based providers (Exa, arxiv-depot)
                are exempt since their good hits need not share query words.
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <p className="text-sm font-medium text-zinc-100">
                Markup drift: the moving target
              </p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">
                Result HTML changes without notice (DuckDuckGo&apos;s lite
                markup moved href and class order in 2026-10-01 live HTML). A
                200 with result markup present but zero parsed triples is
                reported as fault_kind bug (&quot;our parser missed, our
                bug&quot;), not as &quot;no results&quot;, so health drops and
                the real cause is visible.
              </p>
            </div>
          </div>

          <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
            How SearchStudio answers (three moves, all labeled)
          </h2>
          <div className="space-y-2">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <p className="text-sm font-medium text-zinc-100">
                1. Engine rotation inside OpenSERP-local
              </p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">
                The self-hosted OpenSERP service (your Docker, :7000) is asked
                engine by engine: google, bing, duckduckgo, yandex, ecosia.
                First engine with genuinely related hits wins. An engine whose
                hits are all unrelated (a soft block, e.g. Bing on 2026-10-11)
                is skipped and the next engine is tried. One engine&apos;s bad
                day never sinks the provider. Date filtering appends an after:
                operator (Google and Bing honor it; others ignore it gracefully
                and the receipt says the operator was transmitted, not that
                every engine filtered).
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <p className="text-sm font-medium text-zinc-100">
                2. The authorized breaker chain for DuckDuckGo blocks
              </p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">
                Only on the blocked path, legs in order. First a bridge render
                through browser-mcp (engine from BROWSER_MCP_ENGINE: camoufox
                default, playwright, obscura, auto). Camoufox is a Firefox fork
                built for undetectability: fingerprint resistance (canvas,
                audio, fonts), no webdriver flag, human-like behavior. The
                challenge detects automation, not humans, so an undetectable
                browser is simply never challenged: nothing is
                &quot;solved&quot;, the puzzle never appears. Second, when
                FLARESOLVERR_URL arms the sidecar, a FlareSolverr session:
                undetected Chrome driven through Cloudflare&apos;s IUAM
                JavaScript challenges, clearance cookies harvested, cleared HTML
                returned. What FlareSolverr does not do: interactive CAPTCHAs,
                current Turnstile checkboxes, IP-reputation bans. One attempt
                per leg, bounded by the provider timeout so the fan-out budget
                stays max(legs). A rescue is reported ok true but blocked true
                with via naming the leg, so the health ledger still counts the
                block and the coverage line says e.g. &quot;via camoufox after
                block&quot;. Your machine, your choice: legs run only when the
                Settings switch is on (hard off when BROWSER_MCP_URL is empty).
                Settings shows the armed legs live.
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <p className="text-sm font-medium text-zinc-100">
                3. Pay where the wall is legitimate: keyed APIs
              </p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">
                Tavily (ranked, recency-native) and Exa (meaning match,
                semantic) sell clean access: no scraping, no challenges, date
                filters honored server-side. Without a key they are declared
                stubs (configured false plus a setup hint), never fake failures.
                Wikipedia needs no key at all: one courtesy User-Agent
                identifying the app satisfies Wikimedia policy. The rule is
                simple: scrape only what is offered freely (DDG lite, MediaWiki
                API), rotate what is flaky, and buy what is guarded.
              </p>
            </div>
          </div>

          <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
            Why the race never ends (and what that means for you)
          </h2>
          <p className="text-xs leading-relaxed text-zinc-400">
            Every bypass above has a shelf life. Challenge markup changes, rate
            limits tighten, a compliant engine starts serving junk, and
            today&apos;s fallback is tomorrow&apos;s block. That is why no
            single trick is the design: the durable answer is fan-out across
            independent indexes, a receipt for every provider every time, and a
            health ledger that shows which pipes are dying this week. Ground
            rules: solvers and breakers run only when you authorize them
            (Settings switch, env hard-off); one attempt per leg, no hammering;
            no silent zeros; no unlabeled bypasses. Up to a point, by design:
            passive detection (fingerprints, automation flags, JS walls) is
            evaded by driving a real undetectable browser; active puzzles (image
            CAPTCHAs, checkbox Turnstile) are NOT solved and stay blocked, with
            keyed APIs as the paid way through. A wall with no authorized path
            stays visible in the coverage line until you authorize one or a
            keyed API replaces the scrape. Sharpest knives evaluated 2026-10-23
            and not yet wired: CapSolver (cheapest Turnstile tokens), 2Captcha
            (widest coverage), CapMonster (cheapest reCAPTCHA v2), and nodriver
            (top 2026 Cloudflare benchmark). Token solvers stay out until a flow
            presents solvable widgets: a key with no firing path would be a
            stub.
          </p>
        </div>
      )}
    </div>
  );
}
