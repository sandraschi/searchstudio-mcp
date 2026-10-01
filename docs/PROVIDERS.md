# Providers — SearchStudio sub-readme

What each provider is, what it costs, where its key comes from, and how to
think about it. For the fan-out mechanics see ARCHITECTURE.md; for flakiness
see patterns/WEB_SEARCH_IS_IFFY.md in mcp-central-docs.

## Fleet-local (queried first: private, free, instant)

### arxiv-mcp — fresh preprint search

The sibling [arxiv-mcp](https://github.com/sandraschi/arxiv-mcp) backend
searches 7 preprint servers live: arXiv itself plus bioRxiv, medRxiv,
ChemRxiv, Research Square, SocArXiv, and PsyArXiv. No key; needs the sibling
on `ARXIV_MCP_BASE_URL` (default :10770). Down sibling = error receipt
naming the URL, fan-out continues. Freshness maps onto the sibling's native
`hours` parameter.

### arxiv-depot — your paper library

The same sibling's personally ingested papers: full text you saved, searched
by keyword (FTS5), meaning (LanceDB semantic), or hybrid RRF. Empty library
returns ok/0 (genuinely searched). Falls back to keyword mode when the
vector index is missing. Your papers, not the world's — different answers
from the same sibling.

## Knowledge (curated APIs, keyless)

### Wikipedia — the encyclopedia

Official MediaWiki API, single round trip, intro extracts with canonical
URLs. No key; courtesy User-Agent identifies the app per Wikimedia policy.
Entities, places, techniques, history. Starting point, never the citation.

## SERP (whole web, broadest and flakiest)

### openserp-local — self-hosted meta-search

Free open-source [OpenSERP](https://github.com/karust/openserp) in your
Docker (6 engines: Google, Bing, Yandex, Baidu, DuckDuckGo, Ecosia; first
hits win). No key; needs Docker + container on :7000. Dead service produces
an error receipt asking about Docker explicitly. Keep the image fresh
(monthly pulls) — stale scrapers fail exactly like engine blocks. Freshness
via appended `after:` operator (Google/Bing honor it; others ignore it).

### duckduckgo — the independent index

Privacy engine queried directly ([duckduckgo.com](https://duckduckgo.com)).
No key. Independent index *and* independent bot-luck from Google — answers
when others block and blocks when others answer. No date parameter exists
on the lite endpoint (verified against their params page): runs unfiltered,
says so. Short plain queries; it mangles long natural language.

### tavily — AI-native ranked search

[Tavily](https://tavily.com) built for LLM agents: ranked results plus page
content, native recency (`time_range` day/week/month/year) and news topics.
Key: `TAVILY_API_KEY` (free 1k/mo, no card). Without it: declared stub,
everything else keeps working. Spend it on hard questions (research,
comparisons, decisions), not navigational lookups keyless pipes answer free.

### exa — neural search by meaning

[Exa](https://exa.ai) (keys at the [dashboard](https://dashboard.exa.ai/api-keys)):
finds by meaning, not keywords — the semantic counterpart to Tavily's
ranking. Freshness via `startPublishedDate`. Same declared-stub contract
without a key.

### brave — grounding search (Phase 2)

[Brave Search API](https://brave.com/search/api): clean grounding snippets.
Adapter lands in Phase 2; key name `BRAVE_API_KEY` is already reserved and
accepted by the key store. Same stub contract until then.

## Choosing between them

- One question, best effort: defaults (everything).
- Entities/history: knowledge first.
- Fresh news: serp, Tavily/Exa if keyed, `mode=any`, re-run over hours.
- Papers: preprint search for the world's new work, paper library for yours.
- Forums/lived experience: DuckDuckGo carries what ranked APIs filter out.
- Paranoid verification: same query twice with different provider pairs;
  disagreement preserved is a feature.
