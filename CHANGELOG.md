# Changelog - SearchStudio

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
