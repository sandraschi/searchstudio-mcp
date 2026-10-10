# Onboarding - SearchStudio

## What this is for

SearchStudio sends one query to several search providers at once (web engines,
Wikipedia, your fleet's own paper indexes) and returns merged results with a
receipt per provider. It is for anyone tired of single-engine flakiness: agents
needing fresh facts, humans digging in the webapp. It is not a browser, not a
crawler, and not an answer engine (summarizing results is planned, not built).

## Cost and accounts (money / CC)

| Question | Answer |
|----------|--------|
| Do I need an account? | No. Keyless providers work with zero signup |
| Free tier? | Yes: OpenSERP-local, DuckDuckGo, Wikipedia and arxiv-mcp are free |
| Credit card required? | No, unless you buy a SaaS key yourself (Tavily: free 1k calls/month, signup, no card) |
| Ongoing cost? | Free at the keyless tier; usage-metered only if you add paid keys |
| Who bills? | The key vendor (e.g. Tavily, Exa), never sandraschi |

## Prerequisites outside this repo

- Docker Desktop + openserp container - only for the OpenSERP-local provider (everything else works without it)
- arxiv-mcp backend on :10770 - only for the two arXiv providers (degrades gracefully when down)
- browser-mcp on :10780 - only for the optional Camoufox fallback when DuckDuckGo blocks us
- Ollama on :11434 with any chat model - only for the webapp Chat page
- Optional API keys: `TAVILY_API_KEY` (tavily.com), `EXA_API_KEY` (exa.ai)

## First-timer setup steps

1. Install from source following [INSTALL.md](../INSTALL.md) (no release has been published yet).
2. Open the webapp Dashboard - provider cards show what is ready.
3. Want a keyed provider? Paste the key on the Settings page. It takes effect on the next search, no restart.
4. Run the sanity check below, then search.

## Pitfalls

- OpenSERP-local empty with an "is Docker running?" hint: Docker Desktop must be up with the container on :7000 (BIOS virtualization must be enabled - no virtualization, no Docker).
- Keys belong in the Settings page (stored in a gitignored server-side file) or in process env, never in the repo or in chat. Env wins when both are set.
- Empty hits with failed receipts mean nothing was searched, not "doesn't exist". Check the receipts before concluding.
- A provider marked `unrelated` answered with results that have nothing to do with your query (an engine serving junk to automated traffic, or a broken upstream search). Its results are dropped on purpose.
- Breaking news lives in one index for its first 48 hours - search wide and distrust unanimous silence.

## Sanity check

- `GET /api/health` -> `success: true`, provider list with `configured` flags.
- Dashboard shows provider cards; Settings shows key status and the browser fallback switch.
- Search "Hollabrunn" with Knowledge checked -> Wikipedia hits with receipts.

## Declared doubles

- Tavily or Exa without a key returns a declared stub (`configured: false` + setup hint), counted in receipts. No silent fake results anywhere.
- No webapp mock content: status badges and empty states are honest live data.

## Providers explained

Beginner-friendly guide to every name you will see in receipts.

### Web search (SERP)

SERP means Search Engine Results Page, the generic term for web search: you send
words, an engine sends back ranked links. Receipts group these as "Web".

- **OpenSERP** - free, open-source software ([karust/openserp](https://github.com/karust/openserp))
  that you run yourself in Docker. It queries several engines (Google, Bing,
  DuckDuckGo, Yandex, Ecosia) and returns clean data. SearchStudio tries the engines
  in order and skips any engine that answers with junk. If Docker is down, the
  receipt says so.
- **DuckDuckGo** - the privacy-focused engine ([duckduckgo.com](https://duckduckgo.com)),
  queried directly, no key. It has its own index and its own blocking luck, which is
  why it is in the mix. When it shows a bot challenge, SearchStudio can retry once
  through a Camoufox browser (switch in Settings; the receipt marks it
  `via camoufox`).
- **Tavily** - AI-oriented search API ([tavily.com](https://tavily.com)) with ranked
  results and page content. Needs a free key.
- **Exa** - search by meaning rather than keywords ([exa.ai](https://exa.ai)). Needs a
  key. Because it matches meaning, it is exempt from the junk check.
- **Brave** - privacy search API with clean snippets. Planned, not built.

### Knowledge

- **Wikipedia** - queried through its official API, no key. Best for people, places,
  techniques and history. A starting point, never the final citation. It matches
  multi-word queries loosely, so expect related-but-not-exact articles.

### Fleet-local (your own sources)

- **arXiv preprints** (`arxiv-mcp`) - the sibling
  [arxiv-mcp](https://github.com/sandraschi/arxiv-mcp) searches fresh preprints
  (arXiv plus bioRxiv, medRxiv and others). Needs the arxiv-mcp backend running.
- **arXiv paper library** (`arxiv-depot`) - the same sibling's library of papers you
  saved yourself, searched by keyword and meaning. Your papers, not the world's.
- **Memory vault** - your notes in
  [advanced-memory-mcp](https://github.com/sandraschi/advanced-memory-mcp). Planned
  crossconnect, not built.
