# Changelog - SearchStudio

## [0.2.0] - 2026-10-23

### Added
- Paper cards in search: server badge, authors, expandable abstract, lazy
  full text via `GET /api/paper/full-text`, PDF link, Open in arxiv-mcp
- `paper_id` (+ `server/authors/pdf_url/categories`) through the hit contract
- Brave/Exa/Tavily provider pages (mechanics, cost, use-cases, try-it links); Brave hosts the Goggles manager: prepared lenses, custom CRUD, DIY editor, export/import;
  enabled lenses ride Brave searches, named in receipts (`goggles_applied`)
- Per-provider checkboxes on the search page (leave all on = everything)
- arxiv-mcp provider requests all 7 preprint servers (was 3 via sibling default)
- Defenses tab: honest single-click-checkbox explainer; FAQ paper-hit entry

## [0.1.0] - 2026-10-23 (first release)

### Added
- Parallel fan-out across 9 providers in 3 kinds (fleet-local: arxiv-mcp preprint
  search + your paper library; knowledge: Wikipedia, models.dev catalog; serp:
  OpenSERP-local, DuckDuckGo, Tavily, Exa, Brave - last three keyed-or-stub)
- Brave independent-index provider: server-side recency, clean snippets,
  Settings key row + Test button
- Authorized breaker chain for bot walls: bridge render engine choice
  (`camoufox`/`playwright`/`obscura`/`auto`) + FlareSolverr sidecar leg,
  every rescue labeled with its leg, Settings switch + env hard-off
- Kind-priority merge with URL dedupe; per-provider receipts on every call;
  junk detection (`unrelated`); real date filtering per provider
- SQLite health ledger (WAL) + scoreboard + flakiness self-test matrix
- MCP: `searchops` portmanteau + `models_lookup` + `provider_health_app` Prefab
  card; Starlette REST mirror + `/mcp`
- Webapp (10 pages): dashboard, search console, providers, activity, tools,
  skills, chat, settings, help (incl. Defenses tab), logs
- Search skill (`skill://super-search`), skill-first chat, 4 personalities
- Docs stack, onboarding, Windows CI, mcpb layout + 3-4-100 prompts
