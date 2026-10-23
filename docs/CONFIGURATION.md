# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TAVILY_API_KEY` | (unset) | Tavily ranked search + extract, recency-native. Free 1k credits/mo; paid from $30/mo or ~$0.008/credit ([pricing](https://www.tavily.com/pricing)). Unset = declared stub |
| `EXA_API_KEY` | (unset) | Exa neural search by meaning + page extraction. Free tier, then pay-as-you-go ([pricing](https://exa.ai/pricing)). Unset = declared stub |
| `BRAVE_API_KEY` | (unset) | Brave independent-index search + server-side recency. ~$5/1k queries, small monthly free credit ([pricing](https://api-dashboard.search.brave.com/app/documentation)). Unset = declared stub |
| `OPENSERP_BASE_URL` | `http://127.0.0.1:7000` | Self-hosted OpenSERP service |
| `ARXIV_MCP_BASE_URL` | `http://127.0.0.1:10770` | Sibling arxiv-mcp backend |
| `SUPER_SEARCH_DATA_DIR` | `data` | SQLite health ledger location |
| `SUPER_SEARCH_BACKEND_PORT` | `11226` | Backend bind port (`PORT` also honored) |
| `SUPER_SEARCH_FRONTEND_PORT` | `11225` | Informational (Vite owns its port) |
| `BROWSER_MCP_URL` | `http://127.0.0.1:10780` | browser-mcp bridge for breaker legs. Set to empty = breaker chain hard off (wins over Settings) |
| `BROWSER_MCP_ENGINE` | `camoufox` | Bridge render engine: `camoufox` (default), `playwright`, `obscura`, or `auto`. Unknown values fall back to `camoufox`. Live-read, no restart |
| `FLARESOLVERR_URL` | (unset) | FlareSolverr sidecar base (e.g. `http://127.0.0.1:8191/v1`). Unset = second breaker leg disarmed |

## Setting Variables

In `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "searchstudio": {
      "env": {
        "TAVILY_API_KEY": "tvly-your-key"
      }
    }
  }
}
```

Or copy `.env.example` to `.env` for local dev (gitignored - the backend starter loads it when configured).

## Why keys live in JSON, not .env

Fair question with a mechanical answer: a running process reads its
`os.environ` once at startup. Keys in `.env` (or host config) therefore
need a backend restart to take effect, and hand-editing files is exactly
the friction the Settings page removes. `data/provider_keys.json` is read
live on every search instead: paste, save, search immediately, no restart.
Explicitly set process env still wins on conflict (12-factor first), and
`.env` remains the documented manual path for automation and containers.
Both are gitignored; neither is ever returned by any API.

## Settings-page keys (no restart needed)

The webapp Settings page accepts `TAVILY_API_KEY`, `EXA_API_KEY`, and
`BRAVE_API_KEY` through password inputs. They are stored in the gitignored
server-side file `data/provider_keys.json` (never logged, never returned by
any API - status endpoints report set/unset + source only) and take effect
immediately: providers resolve keys live on every call. Explicitly set
process env always wins over the stored file. Clearing removes the stored
entry (env-set keys are unaffected).

## Breaker chain (authorized second tries)

When DuckDuckGo answers with a bot challenge, SearchStudio runs its breaker
legs in order before reporting blocked: first a bridge render (engine from
`BROWSER_MCP_ENGINE`, `camoufox` default), then FlareSolverr when
`FLARESOLVERR_URL` is set. This gets around the provider's bot check, so it
is a user choice: Settings > "Allow browser fallback". On by default.

- Stored in the gitignored `data/preferences.json`, read live on every search
  (no restart). API: `GET/POST /api/settings/fallbacks` (`{"browser_fallback": true|false}`).
- `BROWSER_MCP_URL` set to empty is an operator hard-off and wins over the
  checkbox (the Settings page shows it as locked).
- Every use is visible: a rescued result reports `ok: true, blocked: true`
  plus `via` naming the leg (`camoufox`, `playwright`, `obscura`, `auto`,
  or `flaresolverr`), and the coverage line says e.g.
  `via camoufox after block`. When the chain is off, the blocked receipt
  says so and why. One attempt per leg, bounded by the provider timeout.

Deliberately unwired: CAPTCHA token APIs (CapSolver, 2Captcha, CapMonster).
Evaluated 2026-10-23, none wired because no flow presents a solvable widget;
a key with no firing path would be a stub. They slot in as a further leg
behind the same switch when a sitekey flow appears.
