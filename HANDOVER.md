---
updated: 2026-10-11T01:45:00+02:00
agent: claude
status: in-progress
tags: [searchstudio-mcp, search, research, fastmcp, webapp, handover, high]
---

# Handover - searchstudio-mcp

## What's happening right now

Phase 1 engine with 7 providers, fleet-standard fault receipts on every provider
(EXTERNAL_FAULT_TRANSPARENCY), a relevance check that catches junk answers (fault
kind `unrelated`), relevance-ranked merging, and a Camoufox browser fallback for
DuckDuckGo with a Settings switch. Direction is unchanged: **search in every
field** (web, places, academic, news, own fleet) with **research workflows** on
top. Full reasoning and work plan: `docs/ASSESSMENT_2026-09-30.md` (WP0-WP9).
WP0-WP3 are done; WP4 is next. Working tree clean, `main` in sync with origin.

## Last concrete action (2026-10-11, Claude)

- Live test of `sitagliptin first clinical trial` exposed **silent junk**: Bing
  via OpenSERP returned McDonald's menu pages, arxiv-mcp returned unrelated new
  preprints, both `ok(10)`; the fleet-local-first merge put the junk on top.
- `cdf8344`: `relevance.py` (cheap literal check, no LLM; EN/DE stopwords,
  accent folding; `exa` and `arxiv-depot` exempt as meaning-based). Providers
  with only unrelated hits get fault kind `unrelated` and their hits dropped;
  merge ranks by relevance, kind order breaks ties; OpenSERP skips an engine
  that answers with junk. +8 tests from the captured live junk (69 total green).
  Same live query afterwards: NEJM, TECOS, Januvia sources on top.
- mcd `36b018df`: `unrelated` added to EXTERNAL_FAULT_TRANSPARENCY. Fleet
  audit: searchstudio is the only consumer of the fault kinds.
- arxiv-mcp root cause (raw multi-word query + newest-first sort) filed as a
  separate task, running in another session; a later live run already showed
  arxiv-mcp `ok(0)` for the query instead of junk.
- `878d218`: **WP3 done.** README rewritten (pitch first, real live example,
  works-today vs planned table, honest install), provider glossary moved to
  `docs/ONBOARDING.md` (also fixed: keys via Settings need no restart), INSTALL
  bundle filename. `check-readme-structure.ps1 -Strict` passes.

## Earlier (2026-10-10, Claude)

- Pushed the 5 fault-envelope commits that had sat unpushed since 2026-10-02
  (`d310524`..`9113399`), after testing them in a clean worktree.
- `8fd0b84`: `SyncOnStart = $true` in `fleet-start.config.ps1` (read by
  mcd `scripts/Invoke-FleetWebappStart.ps1`).
- `f6d40e6`: **Camoufox fallback** in `providers/ddg.py`. Only on a DDG bot
  challenge: one render through browser-mcp (`BROWSER_MCP_URL`, default
  `http://127.0.0.1:10780`), bounded by the provider timeout. A rescued result is
  never shown as direct: receipt `ok: true, blocked: true, via: "camoufox"` plus a
  user_message; coverage line says `duckduckgo ok(n) via camoufox after block`.
  New receipt field `via` (empty = direct) in `models.py` / `providers/base.py`.
- `0fbb98e`: **Settings checkbox** "Allow browser fallback (Camoufox) when a
  provider blocks us". On by default (Sandra's decision 2026-10-10). Stored in
  gitignored `data/preferences.json`, read live per search. API
  `GET/POST /api/settings/fallbacks`. `BROWSER_MCP_URL` set to empty is an
  operator hard-off that wins (UI shows it locked). Blocked receipts say whether
  the fallback was off (and where) or tried and failed.
- Verified: 61 pytest, ruff check + format, pyright, tsc, biome, Playwright
  smoke; checkbox exercised in a browser (toggle, persists across reload, no
  console errors). Test preference file removed afterwards, so the live setting
  is the default (on).
- Note: the previous handover called the DDG parser-drift fix uncommitted. It was
  already in `bdc65ca` (now pushed).

## Next step

WP3b competitor read (assessment section 7: web-search-plus-mcp and
open-webSearch, write `docs/COMPETITION.md`), then WP4: router + places vertical,
with the Starlette-to-FastAPI migration of `backend.py` as a separate first
commit. Needs no decisions.

## Blockers

Decided by Sandra (rest still open):
- DONE #6 product surface: public repo with brilliant webapp.
- DONE #1 naming: unify on searchstudio (repo-scoped).
- DONE #3 LLM backends: three modes confirmed; sampling stays permitted (kept
  for Claude Desktop), never the only path.
- DONE (2026-10-10) Camoufox fallback: wanted, used only when necessary, on by
  default, user can switch it off in Settings.
- DEFERRED #2 fetch path: Jina must be evaluated as an mcd integration first.
  Critical path for any research work (WP7/WP8).
- OPEN #4 skill_build vs memops boundary, #5 research ownership, release
  question. Agent recommendation (2026-10-02): crossconnect, not duplication
  (searchstudio owns fan-out/fetch/evidence/loop/verify; memops owns
  notes/RAG/packaging and calls /api/search with local fallback).
- OPEN durable anti-rot: CI grep-gate for hardcoded-year patterns.

## Context the next agent needs

- Keep the engine: `fanout.py`, receipts and `db.py` are the right foundation.
  Build fields and research on top; do not rewrite the engine.
- **Receipts must never hide a rescue or a fallback.** Any new fallback route sets
  `via`, keeps `blocked: true` when the direct path was refused, and appears in
  the coverage line. Do not make the Camoufox evasion itself more aggressive
  (fingerprint tuning, retries); it stays one bounded attempt on the blocked path.
- **Every provider answer goes through the relevance check** (`relevance.py`).
  A new meaning-based provider (embeddings, neural search) must be added to
  `SEMANTIC_PROVIDERS`, or its good hits get flagged `unrelated`. New test
  fixtures need hits that mention their query (see `test_time_filter.py`).
- Tests that touch DDG must pass a temp `data_dir` to `DuckDuckGoProvider`
  (see `_ddg_blocked_search` in `tests/test_providers.py`), or they read the real
  `data/preferences.json`.
- Backend is not a service: start with the fleet launcher or
  `uv run python -m super_search_mcp --serve --port 11226`; webapp
  `cd webapp; bun run dev` (port 11225).
- Repo rule "no stubs": new operations appear in the tool surface only once they
  work end to end.
- memops research code: planning is still fixed text and `[UNICODE]` junk
  remains. Do not copy it; call it when the #5 crossconnect lands.
- Sampling with tools (SEP-1577) only works in Claude Desktop. Every research
  workflow must also run with the server's own models (Ollama/API) and in
  host-driven mode (assessment 9.4).
- Inject the real current date into every LLM prompt; never let a model supply dates.
- Backend framework: fleet standard is FastAPI + Pydantic v2. Do not migrate
  during WP3; migrate `backend.py` at the start of WP4.
- Canonical fleet registry: `mcp-central-docs/operations/fleet-registry.json`.
- Naming is split (`searchstudio-mcp` / `super_search_mcp` / `super-search` /
  `searchops` / `SUPER_SEARCH_*`). Unify per decision #1, in its own planned
  change, not mixed into feature commits.
- No git tags and no GitHub releases yet. Cutting a release publishes something,
  so ask Sandra first.
- Fleet rules: max **10** files per commit or script run (no per-session cap since
  2026-10-09), `.bak` before 3+ file edits, ASCII-only prose, all gates green
  before every commit. Ports 11225 (FE) / 11226 (BE) are claimed.
