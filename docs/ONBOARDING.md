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

Each item below feeds specific providers. All are optional: a missing one
costs only its own providers, reported as a named receipt, never a silent
zero. Core search (DuckDuckGo plus Wikipedia) works with none of them.

- Docker Desktop + openserp container - only for the OpenSERP-local provider.
  Missing: error receipt naming Docker. Verify: `GET http://127.0.0.1:7000/google/search?text=test&limit=1`.
- arxiv-mcp backend on :10770 - only for the two fleet-local providers
  (fresh preprint search + your saved paper library). Missing: named error
  receipt with the URL, fan-out continues. Verify: the sibling answers on
  :10770; else Dashboard marks both cards unconfigured.
- browser-mcp on :10780 - only for the first breaker leg (bridge render of a
  blocked DuckDuckGo page). Missing or switched off: blocked receipts say so
  and why. Verify: Settings fallback row shows the effective value;
  `BROWSER_MCP_URL` set to empty is an operator hard-off and shows as locked.
  Engine is operator-set via `BROWSER_MCP_ENGINE` (`camoufox` default,
  `playwright`, `obscura`, `auto`).
- FlareSolverr sidecar at `FLARESOLVERR_URL` - only for the second breaker leg
  (IUAM-class Cloudflare barriers). Unset (default) = leg disarmed. Run the
  FlareSolverr Docker image and point the env var at its `/v1` endpoint.
- Ollama on :11434 with any chat model - only for the webapp Chat page.
  Missing: Chat shows its disabled state, search is unaffected. Verify:
  `GET http://127.0.0.1:11434/api/tags` answers. Install:
  `winget install Ollama.Ollama`, then `ollama pull qwen3:8b`.
- Optional API keys: `TAVILY_API_KEY` (tavily.com), `EXA_API_KEY` (exa.ai),
  `BRAVE_API_KEY` (brave.com/search/api). Unset = declared stub for that
  provider only, everything else keeps working. Set on the Settings page (live, no restart) or in
  process env (wins on conflict, needs backend restart).

## First-timer setup steps

1. Install from source following [INSTALL.md](../INSTALL.md) (no release has been published yet).
2. Start what you want to use: Docker Desktop with the openserp container
   (:7000) for OpenSERP-local; the arxiv-mcp backend (:10770) for the two
   fleet-local providers; browser-mcp (:10780) for the breaker chain (plus a
   FlareSolverr sidecar and `FLARESOLVERR_URL` for the second leg);
   Ollama (:11434) for Chat. Skip any of them to run without those
   providers. Token solvers (CapSolver, 2Captcha) are deliberately
   unwired: no flow presents solvable widgets.
3. Open the webapp Dashboard - provider cards show what is ready before you
   search (unconfigured cards are expected for anything you skipped).
4. Want a keyed provider? Paste the key on the Settings page. It takes effect on the next search, no restart.
5. Run the sanity check below, then search.

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
  why it is in the mix. When it shows a bot challenge, SearchStudio can run its
  authorized breaker chain (bridge render, then FlareSolverr when armed;
  switch in Settings; every rescue marked with its `via` leg).
- **Tavily** - search API purpose-built for AI agents and RAG
  ([tavily.com](https://tavily.com), [pricing](https://www.tavily.com/pricing),
  [docs](https://docs.tavily.com)). Ranked results plus full page content
  (extract), with recency filters (day/week/month/year) and news topics
  honored server-side: SearchStudio passes your `time_filter` straight through
  and the receipt reports `time_filter_applied: true` (real filtering, not an
  appended query operator). In SearchStudio it is the quality pipe: spend it
  on hard questions (research, comparisons, decisions), not navigational
  lookups the keyless pipes answer free. Plans: free Researcher plan (1,000
  credits/month, no card); paid from Project $30/month (4,000 credits) and
  Bootstrap $100/month (15,000 credits), or pay-as-you-go around
  $0.008/credit (basic search 1 credit, advanced 2). Prices change, so the
  pricing page rules. Key goes in `TAVILY_API_KEY`.
- **Exa** - search by meaning, not keywords ([exa.ai](https://exa.ai),
  [pricing](https://exa.ai/pricing)). Neural search over the web plus
  full-page extraction, research-paper search, answer-with-citations, and
  monitors. In SearchStudio it is Tavily's semantic counterpart: when you know
  the idea but not the words, or you need papers, Exa finds what keyword
  engines miss - and its hits are exempt from the junk check for exactly that
  reason. Plans: free tier to start, then pay-as-you-go credits with no
  subscription and no minimum (load credits, pay per request). Key at the
  [dashboard](https://dashboard.exa.ai/api-keys), goes in `EXA_API_KEY`.
- **Brave** - independent-index search API ([brave.com/search/api](https://brave.com/search/api),
  [pricing](https://api-dashboard.search.brave.com/app/documentation)): 40B+ pages,
  no Google/Bing dependency, clean snippets with server-side recency
  (`pd`/`pw`/`pm`/`py`, passed straight through like Tavily/Exa), plus Goggles
  rerankers for source curation. In SearchStudio it is the raw-ranked
  counterpart to Tavily: a second index, not a second opinion. Plans: about
  $5 per 1,000 queries with a small monthly free credit. Key goes in
  `BRAVE_API_KEY`; the Settings Test button spends one `count=1` probe.

### Knowledge

- **Wikipedia** - queried through its official API, no key. Best for people, places,
  techniques and history. A starting point, never the final citation. It matches
  multi-word queries loosely, so expect related-but-not-exact articles.

### Fleet-local (your own sources)

- **arXiv preprints** (`arxiv-mcp`) - the sibling
  [arxiv-mcp](https://github.com/sandraschi/arxiv-mcp) fans one query out to
  7 preprint servers in parallel, not just arXiv: the arXiv API plus bioRxiv
  and medRxiv (biology/medicine, Cold Spring Harbor API), ChemRxiv and
  Research Square (chemistry plus multidisciplinary), SocArXiv and PsyArXiv
  (social sciences, psychology, OSF API). SearchStudio asks for all 7 every
  time; slow servers report their own named faults instead of failing the
  search. Needs the arxiv-mcp backend running.
- **arXiv paper library** (`arxiv-depot`) - the same sibling's library of papers you
  saved yourself, searched by keyword and meaning. Your papers, not the world's.
- **Memory vault** - your notes in
  [advanced-memory-mcp](https://github.com/sandraschi/advanced-memory-mcp). Planned
  crossconnect, not built.
