# SearchStudio

**Search that tells you when it's failing you.** One query goes to several search
providers at once - web engines, Wikipedia, your own paper library - and you get the
merged results plus a receipt for every provider: who answered, who was blocked,
who returned junk, and how long each took. When a pipe dies, it says so. It never
quietly hands you nothing, or nonsense, and calls it a result.

[![Status](https://img.shields.io/badge/status-early%20development-orange)]()
[![FastMCP](https://img.shields.io/badge/FastMCP-%3E%3D3.4.4-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Contents

- [Why](#why) - the flaky-search problem this solves
- [Preview](#preview) - webapp screenshots
- [The arms race](#the-arms-race) - bot walls and our three labeled moves
- [What You Can Do](#what-you-can-do) - features today
- [Status](#status) - works today vs planned
- [Install](#install) - one path, details in INSTALL.md
- [Example Prompts](#example-prompts) - copy-paste starters
- [Fleet Crossconnects](#fleet-crossconnects) - sibling servers
- [Documentation](#documentation) - full doc map
- [Requirements](#requirements) - what you need
- [License](#license)

## Why

Every developer eventually needs search in their projects, and search is the least
reliable building block there is: engines block automated traffic, serve junk
instead of an error, or go quiet without notice. And "search" is a wide field. All
of these are searches:

- "papers about the first sitagliptin trials" (academic)
- "Indian restaurants in Alsergrund" (places)
- "what changed in the AMD acquisition this week" (news)
- "tell me about our robotics repos" (your own stuff)

SearchStudio's goal is one dependable interface for all of them. **Today it covers
the web, Wikipedia and arXiv preprints well; places, academic databases and your own
repos are planned** - see [Status](#status).

## Preview

| Search console | Provider health |
|---|---|
| ![Search console](docs/screenshots/search.png) | ![Provider health](docs/screenshots/providers.png) |
| *One query, several provider kinds, a receipt per provider.* | *Success rate, latency and block rate per provider.* |

## A real example

Live run, 2026-10-11, query `sitagliptin first clinical trial`, top 6 of the merged
results:

```text
Coverage: Fleet-local: arxiv-mcp ok(0), arxiv-depot ok(10). Knowledge: wikipedia
ok(10). Web: openserp-local ok(10), duckduckgo ok(10), tavily unconfigured,
exa unconfigured.

1. Effect of Sitagliptin on Cardiovascular Outcomes in Type 2 Diabetes   nejm.org
2. Chapter 7 Case History: JANUVIA (Sitagliptin)                         sciencedirect.com
3. The Discovery and Development of Sitagliptin Phosphate                benchchem.com
4. TECOS, Merck's Cardiovascular Safety Trial of JANUVIA (sitagliptin)   merck.com
5. Discovery of JANUVIA (Sitagliptin), a Selective ... Inhibitor         researchgate.net
6. (S)-Sitagliptin Phosphate: Initial Preclinical Studies                benchchem.com
```

The same query minutes earlier, before that night's fixes, is why the receipts
matter: one web engine answered with McDonald's menu pages and the preprint search
with unrelated robotics papers, both claiming success. SearchStudio now checks every answer against the query.
Junk is reported as `unrelated` and dropped, and the merged list is ranked by
relevance, not by which provider happened to answer.

## The arms race

Web search is defended territory: rate limits, bot-challenge pages (DDG
anomaly/challenge screens, Cloudflare-style JS barriers and CAPTCHAs), soft
blocks (HTTP 200 with confident junk), and markup drift. Without an authorized
breaker we report `blocked`, never zero results; junk is flagged `unrelated`
and dropped (meaning-based Exa/arxiv-depot exempt); parse misses are our `bug`.

"Breaker" is our word for an authorized second try: it fires only after the
direct fetch fails, every rescue is labeled with its leg, and nothing runs
unless you switch it on. **Camoufox** (bridge render) is a Firefox fork built
for undetectability - the challenge detects automation, not humans, so it is
simply never challenged: nothing is "solved", the puzzle never appears.
**FlareSolverr** (sidecar) drives undetected Chrome through Cloudflare IUAM
challenges and returns cleared HTML. Up to a point, by design: passive
detection is evaded, active puzzles (image CAPTCHAs, checkbox Turnstile) are
NOT solved - those stay `blocked`, keyed APIs are the paid way through.
Ground rules: one attempt per leg, no hammering, no silent zeros, no unlabeled
bypasses. Evaluated 2026-10-23, not wired: CapSolver, 2Captcha, CapMonster,
nodriver. Full writeup: Help page, Defenses tab.

## What You Can Do

- Search the web (OpenSERP, DuckDuckGo, optional Tavily/Exa/Brave), Wikipedia and arXiv
  preprints with one query, in parallel
- Read the coverage line and receipts: answered, blocked, unrelated, down, or
  missing a key - every provider, every time
- Restrict to recent results (day/week/month/year); providers that cannot filter
  by date say so instead of pretending
- Keep searching when DuckDuckGo blocks automated traffic: an optional browser
  fallback (Camoufox) retries once, clearly marked in the receipt, and can be
  switched off in Settings
- Check provider health over time and run a quick self-test across all providers
- Look up AI models by capability and price (models.dev catalog: tool_call +
  context floor, cheapest first) via `models_lookup`, or by name in super-search
- Use it from Claude or any MCP client (stdio or HTTP), or from the webapp: search
  console, provider health, activity, settings (keys, fallback), chat with a local
  Ollama model (3 personalities plus a custom prompt)

## Status

| Works today | Planned |
|---|---|
| Parallel search across 9 providers with receipts and a coverage line | Search by field: places, academic databases, your own repos, news |
| Fault reporting per the fleet standard, including junk detection (`unrelated`) | Reading full pages, not just snippets |
| Relevance-ranked merge | Research workflows on top (first: a skill builder) |
| Date filters, provider health, self-test | First downloadable release (`.mcpb`) |
| Authorized breaker chain (bridge render, FlareSolverr leg) with a Settings switch | Reading full pages, not just snippets |
| Webapp, MCP over stdio and HTTP, `skill://super-search` resource | Crossconnects with aiwatcher, travelprep, memory |

Known weak spots: Wikipedia matches multi-word queries loosely, and OpenSERP needs
Docker. Provider names and setup are explained in [docs/ONBOARDING.md](docs/ONBOARDING.md).

## Install

Claude Desktop (Windows) one-click:

```powershell
irm https://github.com/sandraschi/searchstudio-mcp/releases/latest/download/install.ps1 | iex
```

The `.mcpb` registers the MCP server in Claude Desktop only and does not
install the webapp (infrastructure tier: no NSIS installer, webapp is for
diagnostics). Other clients: [INSTALL.md](INSTALL.md) Option C
(`uvx --from git+https://github.com/sandraschi/searchstudio-mcp` style
manual config). No API keys are needed to start: OpenSERP (with Docker),
DuckDuckGo and Wikipedia work without any account.

## Example Prompts

> Super-search "sitagliptin first clinical trial" and show me which providers answered.

> Search the last week only for news about the AMD acquisition.

> Which search providers are healthy right now, and which were blocked today?

> Which models have tool_call and 200k+ context, cheapest first?

## Fleet Crossconnects

| Companion | Direction | Status |
|---|---|---|
| [arxiv-mcp](https://github.com/sandraschi/arxiv-mcp) | searchstudio -> arxiv-mcp | Live: preprint search and your saved paper library |
| [aiwatcher-mcp](https://github.com/sandraschi/aiwatcher-mcp) | aiwatcher -> searchstudio | Planned: breaking-news gap filling |
| [travelprep-mcp](https://github.com/sandraschi/travelprep-mcp) | travelprep -> searchstudio | Planned: freshness checks (advisories, prices) |
| [advanced-memory-mcp](https://github.com/sandraschi/advanced-memory-mcp) | memory -> searchstudio | Planned: memory search delegates web search here |

Companions are optional; SearchStudio runs without any of them.

## Documentation

| Doc | Contents |
|---|---|
| [Installation](INSTALL.md) | All install methods, prerequisites |
| [Onboarding](docs/ONBOARDING.md) | Prerequisites per provider (Docker, siblings, Ollama), keys (all optional) |
| [Architecture](docs/ARCHITECTURE.md) | System design, data flow, ports |
| [Configuration](docs/CONFIGURATION.md) | Env vars, stored keys, browser fallback switch |
| [Tool Reference](docs/TOOLS.md) | MCP operations, receipts, fault kinds |
| [Development](docs/DEVELOPMENT.md) | Contributing, local setup |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |
| [Product requirements](docs/PRD.md) | Vision, phases |

## Requirements

Core (to run anything): Windows 10/11 (any OS for stdio use), Claude Desktop
or any MCP client. No API keys required.

Providers (each optional - a missing one is a named receipt, never a silent
zero; see [docs/ONBOARDING.md](docs/ONBOARDING.md) for setup):

- OpenSERP-local: Docker Desktop + openserp container on `:7000`
- arxiv-mcp sibling backend on `:10770`: feeds both fleet-local providers
  (fresh preprint search + your saved paper library)
- browser-mcp on `:10780`: only for the one-shot Camoufox retry when
  DuckDuckGo shows a bot challenge (off in Settings or via empty
  `BROWSER_MCP_URL`)
- Chat page only: Ollama on `:11434` with any chat model
- Keys (all optional): `TAVILY_API_KEY` / `EXA_API_KEY` add providers;
  `BRAVE_API_KEY` goes live: independent-index search with server-side recency

## License

MIT - see [LICENSE](LICENSE).
