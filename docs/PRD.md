# SearchStudio — Product Requirements Document

**Version:** 1.0 (2026-09-30) · **Status:** Phase 1 build in progress
**Repo:** `searchstudio-mcp` · **Alias:** `searchstudio` · **Ports:** FE 11225 / BE 11226
**Tier:** Infrastructure (no Tauri/NSIS — consumed by servers, webapp for diagnostics)

## 1. Vision

Every AI coding helper is only as good as its freshest fact, and web search
is the least reliable primitive in the fleet: intermittently blocked,
differently indexed per engine, silently empty when the pipe is dead. Solo
developers feel this worst — they hit it three times a year, re-learn the
maze every time, and have no team to absorb the flakiness.

SearchStudio is the Voicestudio play applied to search: aggregate the good
FOSS search tools, unify them behind one interface, and add the layer nobody
ships — parallel fan-out with adaptive ordering, per-provider health
receipts, and a built-in flakiness self-test. One query in, best available
answers out, with receipts showing which pipes answered and which blocked.

Target: the fleet's research front-end, and a public repo strangers star.

## 2. Audiences

| Level | Who | Contract |
|---|---|---|
| L1 | Fleet agents/devs (other MCP servers, opencode, Claude Desktop) | MCP tools always answer; degraded pipes reported, never silent |
| L2 | Technical users (webapp) | Search console, provider health, matrix harness, skill + chat |
| L3 | Future (Phase 3+) | AI-condensed answers, not links — local-first, cloud opt-in |

## 3. Provider taxonomy (the core design)

One `Provider` protocol, three kinds. Fan-out, merge, and health are
kind-agnostic: every provider returns the same result shape + receipt.

- **SERP** (whole web): OpenSERP-local (Docker :7000, keyless), DDG-direct
  (keyless HTTP fallback), Tavily (keyed, `TAVILY_API_KEY`; declared stub
  without key). Exa/Brave adapters later, same interface.
- **Knowledge** (curated, keyless APIs): Wikipedia (MediaWiki opensearch +
  extracts — local history to trivia), TVTropes (via tvtropes-mcp
  crossconnect, no re-scraping). Later, ranked: PubMed/Entrez, HN Algolia,
  StackExchange, SHARE/OSF, Nominatim, user-provided SearXNG.
- **Fleet-local** (our knowledge: free, private, instant — queried first):
  arxiv-mcp (`/api/preprints/search`, verified live), then mcd depot +
  memops RAG (endpoints to verify, Phase 2).

Ordering philosophy: fleet-local → curated knowledge → whole web. Private,
free, and fast before broad, billed, and flaky. Kind selection per call
(`kinds=all|web|knowledge|local`) plus per-provider include/exclude.

## 4. Tool surface (one portmanteau + two satellites)

`searchops(operation=...)` — operations:

| Operation | What | Phase |
|---|---|---|
| `super_search` | Parallel fan-out, merge/dedupe, receipts. Params: `query`, `kinds`, `providers`, `time_filter`, `domains`, `limit` (bounded, paginated), `mode` (balanced/any) | 1 |
| `provider_health` | Scoreboard: success rate, p50 latency, block rate, last check per provider | 1 |
| `self_test` | Flakiness matrix harness (queries × providers), appends to incident log | 1 |
| `aiwatcher_feed` | Narrow contract for aiwatcher gap-filling (breaking-news shaped) | 2 |
| `condense` | AI ranking/condensing of merged results (local Ollama default, cloud opt-in) | 3 |

Satellites: `searchops_status` (health + config as Prefab card), `searchops_help` (docs pointer). Annotations: READ_ONLY everywhere (no destructive ops exist).

## 5. Backend (Starlette 1.0 + FastMCP ≥3.4.4,<5)

- REST: `/api/health` (configured/providers/authenticated shape), `/api/capabilities` (mandatory), `/api/skills` + `/skill/{name}`, `/api/search` (mirrors super_search), `/api/providers`, `/api/matrix` (self-test trigger).
- MCP: same tools over stdio (local dev) and `/mcp` HTTP (fleet consumers). `lifespan=_mcp_http.lifespan` on the parent app (3.4.4 pitfall). No stdio+HTTP on one instance — stdio is a probe to the HTTP daemon.
- State: SQLite health DB (`data/`, gitignored), WAL mode, short transactions, per-provider locking (concurrency standard).
- Errors: dialogic returns (`success/error/error_type/suggestions`) everywhere; dead provider = reported exclusion, never silent zero; `_error_response` auto-logs tracebacks.
- No fakes: keyless Tavily = declared stub (`configured: false` + setup hint). Mocks only in tests, named fixtures.

## 6. Webapp (React + Vite + Tailwind, bun, `webapp/`)

Catch-them-all, infrastructure-flavored: Dashboard (hero, KPIs, provider-status CTA), **Search console** (domain page: query, kind/provider pickers, receipts view), Providers (status + matrix trigger), Activity (recent-search log = Inbox analog), Tools (surface reference), Skills (`/skills` + SKILL.md), Chat (skill-first, 4 personalities, Ollama), Settings (LLM + provider keys + key status), Help, Logs. Dark default, onboarding CTA → provider setup, MOCK-until-onboarded only if needed (status badges are honest empty states, not mocks).

## 7. Packaging & quality gates

- `just serve/test/lint/fmt/ci/mcpb-pack`; `ruff check + format`, `pyright src/`, pytest mocked (no live network in CI), `tsc --noEmit`, `biome check`, Playwright smoke (health + mount), `.github/workflows/ci.yml` Windows-only + local `just ci` green.
- `.mcpb`: manifest v0.2, wipe+recopy pack script, `.mcpbignore` at pack root, 3-4-100 prompts (real content), icon.png (stdlib-generated if needed), glama.json, llms.txt + llms-full.txt.
- Docs stack: README, INSTALL, AGENTS, CLAUDE, CHANGELOG, docs/{ONBOARDING,CONFIGURATION,DEVELOPMENT,ARCHITECTURE,TOOLS,TROUBLESHOOTING}, phases/roadmap section.
- Release discipline standard applies from day one (showstopper rule, 5-file commits).

## 8. Crossconnects (1-hop, soft degradation, opt-in)

- **aiwatcher-mcp → searchstudio** (Phase 2): breaking-news gap-filling via `aiwatcher_feed`; aiwatcher keeps its signature; down→current behavior, not errors.
- **memops → searchstudio** (Phase 3, optional): `adn_web_search` may delegate `provider=auto`; blast radius noted, deferred deliberately.
- **travelprep-mcp** (Phase 2 template): freshness checks (advisories, prices) via super_search + time/domain filters; documented once, reused fleet-wide.
- **tvtropes-mcp → searchstudio** (Phase 2): trivia/content queries served from their depot, no re-scrape.
- Registry: `fleet-registry.json` entry, INSTALL companion snippet in consumers, `/apps` badges per crossconnect standard.

## 9. Non-goals (Phase 1)

- Own page extractor (forward to provider-native content or `fetch`; no second front in the arms race).
- AI condensing (Phase 3), Tauri/NSIS (Infrastructure tier: never), RAG corpus (no index; health DB only), Exa/Brave adapters (interface-ready, Phase 2), memops delegation (Phase 3).

## 10. Success criteria

- Phase 1 done = assfix finds zero CRITICAL/HIGH on first run; `just ci` green; demo: one query, three provider kinds, receipts; docs complete; pushed.
- Adoption = aiwatcher crossconnected, one travel freshness check live.
- Public = Glama listed, HN "Show HN: Super Search Is All You Need" posted, stars counted without shame.
