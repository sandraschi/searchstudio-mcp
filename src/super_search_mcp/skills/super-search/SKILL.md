# Super-Search Skill — SearchStudio search expert

SearchStudio fans one query out in parallel across web search, curated
knowledge, and fleet-local sources, then merges results with per-provider
health receipts. Use it whenever fresh or external facts are needed.

## Tool surface

- `searchops(operation="super_search", query, kinds, providers, limit, mode)` —
  the workhorse. Kinds: `fleet-local` (arxiv-mcp depot), `knowledge`
  (Wikipedia), `serp` (OpenSERP-local, DuckDuckGo, Tavily). `mode=any`
  returns the fastest kind with hits; `mode=balanced` (default) merges all.
- `searchops(operation="provider_health", window_hours)` — rolling
  scoreboard: success rate, p50 latency, blocks per provider.
- `searchops(operation="self_test")` — flakiness matrix (3 probes × providers).
- `provider_health_app` — Prefab card twin for in-chat display.

## Best practices

- Default `kinds` to all; narrow only when the user scopes (medical →
  knowledge + fleet-local rarely helps; say what you excluded).
- `limit` 1..50, default 10. Results are bounded; ask before widening.
- Read `receipts` on every call: a provider with `ok=false` was skipped,
  not searched. Never present merged results as exhaustive when receipts
  show exclusions. Never treat empty hits as "doesn't exist" — check
  whether any provider actually answered first.
- Breaking news (<48h): expect single-provider coverage; fan out wide and
  distrust unanimous silence.
- Tavily without `TAVILY_API_KEY` is a declared stub — keyless providers
  (OpenSERP-local, DuckDuckGo, Wikipedia, arxiv-mcp) still run.

## Configuration

- `OPENSERP_BASE_URL` (default http://127.0.0.1:7000) — needs Docker + openserp container.
- `ARXIV_MCP_BASE_URL` (default http://127.0.0.1:10770) — needs arxiv-mcp backend.
- `TAVILY_API_KEY` — optional, unlocks the Tavily provider. Never commit keys.
- `SUPER_SEARCH_DATA_DIR` — SQLite health ledger location (default `data/`).
