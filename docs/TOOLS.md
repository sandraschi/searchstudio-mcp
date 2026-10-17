# Tool Reference - SearchStudio (`searchops`)

All tools are READ_ONLY + openWorldHint. No destructive operations exist.

## searchops(operation="super_search", ...)

Parallel fan-out, merged hits, per-provider receipts.

| Param | Type | Default | Notes |
|---|---|---|---|
| `query` | str | (required) | Search text |
| `kinds` | str | `fleet-local,knowledge,serp` | CSV subset |
| `providers` | str | `""` (all) | CSV allowlist, e.g. `wikipedia,tavily` |
| `time_filter` | str | `any` | Freshness window: any/day/week/month/year. Tavily passes it natively, sibling takes hours, OpenSERP appends after:; DDG/Wikipedia run unfiltered and say so. Receipts carry `time_filter_applied` |
| `limit` | int | `10` | 1..50 merged hits |
| `mode` | `balanced` \| `any` | `balanced` | `any` = fastest kind with hits wins (receipts still full) |

Returns `{success, query, total, hits[], receipts[], coverage}` (`mode_winner_kind` in `any` mode).
Failure: `{success: False, error, error_type, suggestions}`.
Receipts carry `fault_kind` (`rate_limited|slow|blocked|unrelated|down|unconfigured|bug`),
`user_message`, `what_to_do`, `retry_in` alongside the technical `error`.
`unrelated` = the provider answered, but not one hit mentions the query (a soft
block or a broken upstream search); its hits are dropped and `count` still shows
what it returned. Meaning-based providers (Exa, arXiv library) are exempt.
Merged hits are ranked by a literal relevance score first, kind order second.
`via` names the fallback route when one answered (empty = direct): DuckDuckGo
falls back to a Camoufox render through browser-mcp (`BROWSER_MCP_URL`, empty
disables) only after a bot challenge, and then reports `ok: true, blocked: true,
via: "camoufox"`;
`coverage` is the one-line what-was-searched summary (fleet standard
EXTERNAL_FAULT_TRANSPARENCY.md).

`modelsdev` is the 8th fan-out provider (knowledge, keyless): free-text search
over the cached models.dev catalog (8,900+ models, refreshed at most once per
24h into `data/modelsdev_catalog.json`). Hits carry price/context/capability
snippets. No date metadata exists in the catalog, so it runs unfiltered and
says so (`time_filter_applied: false`). A failed refresh with a usable cache
serves stale data and notes it in the receipt; with no cache it reports
`down`.

## models_lookup(...)

Structured catalog filter: "which models have tool_call + context >= X,
cheapest first?" Same cache as the `modelsdev` provider.

| Param | Type | Default | Notes |
|---|---|---|---|
| `query` | str | `""` (all) | Free-text filter on id/name/description |
| `needs_tool_call` | bool | `false` | Keep only tool_call models |
| `min_context` | int | `0` | Minimum context window in tokens |
| `max_input_cost` | float | `0` (no cap) | Max input $/1M tokens |
| `open_weights_only` | bool | `false` | Keep only open-weights models |
| `limit` | int | `20` | 1..50 rows, sorted by input $/1M ascending |
| `refresh` | bool | `false` | Force a catalog refresh |

Returns `{success, query, total, items[], meta{scanned, cached_at_ms, stale,
refresh_error, source}}`. Catalog source override: `MODELSDEV_CATALOG_URL`.

## searchops(operation="provider_health", window_hours=24)

Rolling scoreboard per provider: attempts, success_rate, p50_latency_ms,
blocked count, plus live `configured` flags. Empty scoreboard = no searches
recorded yet (message says so explicitly).

## searchops(operation="self_test")

Three canonical probes (evergreen, local-history, niche) across all
providers. Returns `{matrix[{probe, total, by_provider, failed}]}`.

## provider_health_app(window_hours=24)

Prefab card twin of provider_health (`app=True`). Plain-text summary fallback
plus in-chat card; failures render as error cards (`is_error=True`).
