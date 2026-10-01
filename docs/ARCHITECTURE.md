# Architecture - SearchStudio

## Data flow

```
caller (agent / webapp / fleet server)
  │  MCP stdio ──► FastMCP portmanteau (server.py)
  │  HTTP     ──► Starlette REST (backend.py) ──► same handlers
  ▼
fanout() - asyncio.gather over selected providers (kinds filter)
  ├─ fleet-local: arxiv-mcp ──► sibling HTTP :10770 (soft-degrade on down)
  ├─ knowledge:   Wikipedia ──► MediaWiki API (courtesy UA, no key)
  └─ serp:        OpenSERP-local ──► Docker :7000 (any-engine-wins inside)
                  DuckDuckGo     ──► lite HTML scrape (defensive parse)
                  Tavily         ──► SaaS API (key) or declared stub
  ▼
merge (kind priority fleet-local → knowledge → serp, URL dedupe)
  ▼
health ledger (SQLite WAL, advisory writes) + receipts per provider
  ▼
{query, total, hits[], receipts[]} - bounded by limit (1..50)
```

## Ports and protocols

- Backend **11226**: Starlette REST (`/api/*`) + MCP streamable HTTP (`/mcp`, lifespan-shared).
- Frontend **11225**: Vite dev (proxy `/api`, `/skill` → backend) or `dist/` build.
- MCP stdio: full in-process functionality (no daemon needed); SQLite-WAL tolerates concurrent stdio + HTTP writers.

## State

- `data/searchstudio.sqlite3`: provider attempt ledger only (ts, provider, kind, ok, latency, count, blocked). No corpus, no index, no user data.
- All other state is per-call. No sessions, no background tasks.

## Key invariants

- Every provider outcome produces a receipt, success or failure.
- Provider bugs (exceptions) are caught at the fan-out boundary and reported, never propagated.
- Dispatch is keyword-only (`fn(query, limit=..., hours=...)`) - positional dispatch across heterogeneous signatures caused the 2026-09-30 biorxiv incident elsewhere; the contract test pins this.
- No network in lifespan probe (settings + DB writability only).
