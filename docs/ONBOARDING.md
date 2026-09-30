# Onboarding — SearchStudio

## What this is for

SearchStudio aggregates web search, curated knowledge, and your fleet's own
indexes behind one query. It is for anyone tired of single-engine flakiness:
agents needing fresh facts, humans digging on the webapp. It is not a browser,
not a crawler, not an answer engine (condensing arrives in Phase 3).

## Cost and accounts (money / CC)

| Question | Answer |
|----------|--------|
| Do I need an account? | No. Keyless providers work with zero signup |
| Free tier? | Yes: OpenSERP-local, DuckDuckGo, Wikipedia, arxiv-mcp are free forever |
| Credit card required? | No, unless you buy a SaaS key yourself (Tavily free 1k/mo needs signup, no card) |
| Ongoing cost? | Free at keyless tier; usage-metered only if you add paid keys |
| Who bills? | The key vendor (e.g. Tavily), never sandraschi |

## Prerequisites outside this repo

- Docker Desktop + openserp container — only for the OpenSERP-local provider (everything else works without it)
- arxiv-mcp backend on :10770 — only for fleet-local results (degrades gracefully when down)
- Ollama on :11434 with any chat model — only for the webapp Chat page
- Optional API keys: `TAVILY_API_KEY` (free 1k/mo at tavily.com), later Exa/Brave

## First-timer setup steps

1. Install via Option A (mcpb drag-drop) or C (clone + uv sync) from INSTALL.md.
2. Open the webapp Dashboard — provider cards show what is ready.
3. If a card says "not configured" and you want it: Settings page names the exact env var. Set it, restart the backend.
4. Sanity check below, then search.

## Pitfalls

- OpenSERP-local empty + "is Docker running?" hint: Docker Desktop must be up with the container on :7000 (BIOS virtualization must be enabled — no virtualization, no Docker, ever).
- Keys go in process env or host config, never the repo, never chat. Backend restart required after setting.
- Empty hits + failed receipts = nothing was searched, not "doesn't exist". Check Providers before concluding.
- Breaking news lives in one index for its first 48h — fan out wide, distrust unanimous silence.

## Sanity check

- `GET /api/health` → `success: true`, provider list with `configured` flags.
- Dashboard shows provider cards; Settings shows key status.
- Search "Hollabrunn" with Knowledge checked → Wikipedia hits with receipts.

## Declared doubles

- Tavily without a key returns a declared stub (`configured: false` + setup hint), counted in receipts. No silent fake results anywhere.
- No webapp mock content: status badges and empty states are honest live data.
