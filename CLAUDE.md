# searchstudio-mcp — CLAUDE.md

SearchStudio: parallel multi-provider fan-out (web, knowledge, fleet-local) with per-provider health receipts.

## Quick start for Claude Code sessions

- Backend: `uv run python -m super_search_mcp --serve --port 11226` (health: `GET /api/health`)
- Frontend: `cd webapp && bun install && bun run dev` (port 11225, proxies `/api` → backend)
- Tests: `uv run --extra dev pytest tests -q` (mocked, offline-safe)
- Full gate: `just ci`

## Key files

- `src/super_search_mcp/fanout.py` — merge + dispatch (keyword args only, see dispatch test)
- `src/super_search_mcp/providers/` — one module per provider
- `src/super_search_mcp/server.py` — MCP tools (portmanteau + Prefab)
- `src/super_search_mcp/backend.py` — Starlette REST + `/mcp`
- `docs/PRD.md` — vision, phases, roadmap

## Conventions

- ASCII-only prose (no em dashes). 5 files max per commit. `.bak` backups before 3+ file edits.
- Receipts mandatory: every provider outcome recorded, failures dialogic (`success/error/error_type/suggestions`).
- Never commit `.env`, `data/`, `node_modules/`, `.venv/`, `*.bak*`.
