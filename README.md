# SearchStudio

**Search that tells you when it's failing you.** One query goes to several search
providers at once - web engines, Wikipedia, your own paper library - and you get the
merged results plus a receipt for every provider: who answered, who was blocked,
who returned junk, and how long each took. When a pipe dies, it says so. It never
quietly hands you nothing, or nonsense, and calls it a result.

[![Status](https://img.shields.io/badge/status-early%20development-orange)]()
[![FastMCP](https://img.shields.io/badge/FastMCP-%3E%3D3.4.4-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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

## What You Can Do

- Search the web (OpenSERP, DuckDuckGo, optional Tavily/Exa), Wikipedia and arXiv
  preprints with one query, in parallel
- Read the coverage line and receipts: answered, blocked, unrelated, down, or
  missing a key - every provider, every time
- Restrict to recent results (day/week/month/year); providers that cannot filter
  by date say so instead of pretending
- Keep searching when DuckDuckGo blocks automated traffic: an optional browser
  fallback (Camoufox) retries once, clearly marked in the receipt, and can be
  switched off in Settings
- Check provider health over time and run a quick self-test across all providers
- Use it from Claude or any MCP client (stdio or HTTP), or from the webapp: search
  console, provider health, activity, settings (keys, fallback), chat with a local
  Ollama model (3 personalities plus a custom prompt)

## Status

| Works today | Planned |
|---|---|
| Parallel search across 7 providers with receipts and a coverage line | Search by field: places, academic databases, your own repos, news |
| Fault reporting per the fleet standard, including junk detection (`unrelated`) | Reading full pages, not just snippets |
| Relevance-ranked merge | Research workflows on top (first: a skill builder) |
| Date filters, provider health, self-test | First downloadable release (`.mcpb`) |
| Browser fallback for DuckDuckGo with a Settings switch | Brave provider |
| Webapp, MCP over stdio and HTTP, `skill://super-search` resource | Crossconnects with aiwatcher, travelprep, memory |

Known weak spots: Wikipedia matches multi-word queries loosely, and OpenSERP needs
Docker. Provider names and setup are explained in [docs/ONBOARDING.md](docs/ONBOARDING.md).

## Install

No release has been published yet; a one-click Claude Desktop bundle (`.mcpb`) is
planned. Until then, follow [INSTALL.md](INSTALL.md) to set it up from source. No API
keys are needed to start: OpenSERP (with Docker), DuckDuckGo and Wikipedia work
without any account.

## Example Prompts

> Super-search "sitagliptin first clinical trial" and show me which providers answered.

> Search the last week only for news about the AMD acquisition.

> Which search providers are healthy right now, and which were blocked today?

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
| [Onboarding](docs/ONBOARDING.md) | Every provider explained, keys (all optional), Docker for OpenSERP |
| [Configuration](docs/CONFIGURATION.md) | Env vars, stored keys, browser fallback switch |
| [Tool Reference](docs/TOOLS.md) | MCP operations, receipts, fault kinds |
| [Architecture](docs/ARCHITECTURE.md) | System design, data flow, ports |
| [Product requirements](docs/PRD.md) | Vision, phases |
| [Development](docs/DEVELOPMENT.md) | Contributing, local setup |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |

## Requirements

- Windows 10/11 (or any OS for stdio use)
- Claude Desktop, or any MCP client
- Docker Desktop, optional: only for the OpenSERP provider
- No API keys required: Tavily and Exa keys add providers, nothing more

## License

MIT - see [LICENSE](LICENSE).
