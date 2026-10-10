# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TAVILY_API_KEY` | (unset) | Tavily AI-native search. Unset = declared stub |
| `EXA_API_KEY` | (unset) | Exa neural search. Phase 2 adapter reads it when built |
| `BRAVE_API_KEY` | (unset) | Brave grounding search. Phase 2 adapter reads it when built |
| `OPENSERP_BASE_URL` | `http://127.0.0.1:7000` | Self-hosted OpenSERP service |
| `ARXIV_MCP_BASE_URL` | `http://127.0.0.1:10770` | Sibling arxiv-mcp backend |
| `SUPER_SEARCH_DATA_DIR` | `data` | SQLite health ledger location |
| `SUPER_SEARCH_BACKEND_PORT` | `11226` | Backend bind port (`PORT` also honored) |
| `SUPER_SEARCH_FRONTEND_PORT` | `11225` | Informational (Vite owns its port) |
| `BROWSER_MCP_URL` | `http://127.0.0.1:10780` | browser-mcp bridge for the Camoufox fallback. Set to empty = fallback hard off (wins over Settings) |

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

## Browser fallback (Camoufox) switch

When DuckDuckGo answers with a bot challenge, SearchStudio can retry once by
rendering the page in a Camoufox browser through browser-mcp. This gets around
the provider's bot check, which the provider may not want, so it is a user
choice: Settings > "Allow browser fallback (Camoufox)". On by default.

- Stored in the gitignored `data/preferences.json`, read live on every search
  (no restart). API: `GET/POST /api/settings/fallbacks` (`{"browser_fallback": true|false}`).
- `BROWSER_MCP_URL` set to empty is an operator hard-off and wins over the
  checkbox (the Settings page shows it as locked).
- Every use is visible: a rescued result reports `ok: true, blocked: true,
  via: "camoufox"`, and the coverage line says `via camoufox after block`. When
  the fallback is off, the blocked receipt says so and why.
