# searchstudio-mcp - AGENTS.md

FastMCP Python server (Starlette backend) + React/Vite/Bun webapp. Infrastructure tier: consumed by other MCP servers. Desktop shell via Tauri NSIS (current-user, no admin); backend stays separate on :11226, the shell degrades gracefully when it is down.

## Ports (claimed, do not change)

- Backend (Starlette + MCP `/mcp`): **11226**
- Frontend (Vite): **11225**

## Commands

```powershell
uv sync --extra dev          # install (Python 3.11+)
uv run python -m super_search_mcp --serve --port 11226   # backend
uv run --extra dev pytest tests -q                       # tests (mocked, no network)
uv run --extra dev ruff check src tests                  # lint
just ci                      # full local gate
cd webapp; bun install; bun run dev                      # frontend
```

## Architecture

- `src/super_search_mcp/providers/` - one module per provider, shared `Provider` protocol (base.py). Every provider returns `(hits, receipt)`; receipts are mandatory even on total failure.
- `fanout.py` - parallel gather, kind-priority merge (fleet-local → knowledge → serp), URL-dedupe, health recording.
- `db.py` - SQLite health ledger, WAL mode, short transactions. Advisory only: ledger failures never fail searches.
- `server.py` - FastMCP portmanteau `searchops` + Prefab `provider_health_app`. All tools READ_ONLY + openWorldHint.
- `backend.py` - Starlette routes + `/mcp` mount with `lifespan=_mcp_http.lifespan` (3.4.4 pitfall).
- Adding a provider: new module in `providers/`, register in `providers/__init__.py`, keep the `(query, limit=...)` keyword-callable signature (dispatch contract test enforces it).

## Rules

- No em dashes anywhere (Unicode safety). ASCII prose.
- Max 5 files per commit; timestamped `.bak` before 3+ file edits.
- No stubs: unbuilt Phase 2/3 ops stay out of the tool surface until they work.
- Dead provider = error receipt, never silent zero. Keyless-missing = declared stub.
- Tests mock the network boundary (see test files); live verification is manual + documented.
