# Changelog — SearchStudio

## [0.1.0] — 2026-09-30 (Phase 1 scaffold)

### Added
- Parallel fan-out across 5 providers in 3 kinds (fleet-local: arxiv-mcp; knowledge: Wikipedia; serp: OpenSERP-local, DuckDuckGo, Tavily keyed-or-stub)
- Kind-priority merge with URL dedupe; per-provider receipts on every call
- SQLite health ledger (WAL) + scoreboard + flakiness self-test matrix
- MCP: `searchops` portmanteau + `provider_health_app` Prefab card; Starlette REST mirror + `/mcp`
- Webapp (10 pages): dashboard, search console, providers, activity, tools, skills, chat, settings, help, logs
- Search skill (`skill://super-search`), skill-first chat, 4 personalities
- Docs stack, onboarding, CI (Windows-only), mcpb layout + 3-4-100 prompts
