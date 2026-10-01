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

Returns `{success, query, total, hits[], receipts[]}` (`mode_winner_kind` in `any` mode).
Failure: `{success: False, error, error_type, suggestions}`.

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
