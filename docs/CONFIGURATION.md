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

## Settings-page keys (no restart needed)

The webapp Settings page accepts `TAVILY_API_KEY`, `EXA_API_KEY`, and
`BRAVE_API_KEY` through password inputs. They are stored in the gitignored
server-side file `data/provider_keys.json` (never logged, never returned by
any API - status endpoints report set/unset + source only) and take effect
immediately: providers resolve keys live on every call. Explicitly set
process env always wins over the stored file. Clearing removes the stored
entry (env-set keys are unaffected).
