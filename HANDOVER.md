---
updated: 2026-10-02T12:50:00+02:00
agent: claude
status: in-progress
tags: [searchstudio-mcp, search, research, fastmcp, webapp, handover, high]
---

# Handover - searchstudio-mcp

## What's happening right now

Phase 1 engine plus keys management, Exa, and arxiv-depot providers (7 providers
total). Direction is **search in every field** (web, places, academic, news, own
fleet) with **research workflows** on top. Full reasoning, competition analysis
and work plan: `docs/ASSESSMENT_2026-09-30.md` (sections 1-9, work packages
WP0-WP9). Live dogfooding on 2026-10-02 proved the receipts design twice: a DDG
silent-zero was detected, diagnosed, and fixed in one place.

## Last concrete action (2026-10-02)

- **DDG parser-drift fix** (`providers/ddg.py`): live lite HTML uses single quotes
  + href-before-class, regex expected double quotes + class-before-href, so every
  query parsed 0 hits with ok:true. Parser is now quote/order tolerant, skips
  "more info" boilerplate, and a 200-with-markup-but-0-triples now returns
  ok:false "parse miss" instead of a silent zero. +2 regression tests, 45 green.
- **Tool alias hint** (`server.py`): description now states "super search" /
  super_search / searchops all route here with operation=super_search (option A;
  full rename still needs Sandra's go-ahead per HANDOVER rule).
- **memops stale-date sweep** (advanced-memory-mcp): 13 hardcoded "2025-12-02"
  runtime timestamps in `make_skill_advanced.py` now use `_vienna_now()`;
  researcher.py example years bumped +2 (genuine Mueller 2014 kept);
  skill-creator "Oct 2024 training cutoff" gap notice made timeless.
  `research_orchestrator` [UNICODE] junk NOT touched (separate fix task).
- **Upstream-clone hygiene** (advanced-memory-mcp): reverted trailing-newline
  noise in temp-anthropic-courses/skills; kept one intentional edit:
  webapp-testing/SKILL.md example ports now 13010/13011 (verified unclaimed
  fleet-wide, NOT registered - throwaway example ports).
- **Live research demo**: "quantum entanglement" dossier via super_search +
  direct page fetch (Wikipedia summary API 403'd twice; arxiv-depot returned 3
  keyword-junk hits - retrieval quality signal for WP5).
- **Needs restarts**: searchstudio backend + advanced-memory NSSM daemon still
  run pre-fix code. DDG currently reports count:0 until restarted.

## Next step

WP3: README rewrite per assessment 3.4 (vision first, live input-output
example, status table, glossary to ONBOARDING, working Quick Install).
Needs no decisions. Then WP4 router + places vertical (includes the
Starlette-to-FastAPI migration as a separate first commit).

## Blockers

Decided by Sandra 2026-09-30 (rest still open):
- DONE #6 product surface: public repo with brilliant webapp.
- DONE #1 naming: unify on searchstudio (repo-scoped).
- DONE #3 LLM backends: three modes confirmed.
- DEFERRED #2 fetch path: Jina must be evaluated as an mcd integration first.
  This is now the critical path for any research work (WP7/WP8 need it).
- OPEN #4 skill_build vs memops boundary, #5 research ownership, release question.
  Agent recommendation recorded 2026-10-02: **crossconnect, not duplication**
  (searchstudio owns fan-out/fetch/evidence/loop/verify; memops owns
  notes/RAG/packaging and calls /api/search with local fallback). First commit
  would be ~2 files: route memops topic research via 127.0.0.1:11226 with
  fallback. Awaiting Sandra's call on #5 before touching either side.
- OPEN durable anti-rot: CI grep-gate for hardcoded-year patterns (same shape
  as the ASCII hygiene gate), else the stale-date sweep repeats yearly.

## Context the next agent needs

- Keep the engine: `fanout.py`, receipts and `db.py` are the right foundation. Build
  fields and research on top; do not rewrite the engine.
- Repo rule "no stubs": new operations appear in the tool surface only once they work
  end to end.
- memops research code status changed: timestamps and query years are fixed (see
  above); planning is still fixed text and `[UNICODE]` junk remains. Do not copy
  it; call it when the #5 crossconnect lands.
- Sampling with tools (SEP-1577) only works in Claude Desktop. Every research workflow
  must also run with the server's own models (Ollama/API) and in host-driven mode
  (assessment 9.4). Never make sampling the only path.
- Inject the real current date into every LLM prompt; never let a model supply dates.
- Backend framework: the fleet standard is now FastAPI + Pydantic v2 (reversed
  2026-09-30). Do not migrate during WP3; migrate `backend.py` at the start of WP4
  (details in the assessment's WP4).
- Canonical fleet registry: `mcp-central-docs/operations/fleet-registry.json` (not the
  small copy in opencode-cli-mcp).
- Naming is split (`searchstudio-mcp` / `super_search_mcp` / `super-search` /
  `searchops` / `SUPER_SEARCH_*`). Do not rename without Sandra's go-ahead.
- There are no git tags and no GitHub releases, although README Quick Install points to
  Releases. Cutting a release publishes something, so ask Sandra first.
- Fleet rules: max 5 files per commit, `.bak` before 3+ file edits, ASCII-only prose,
  `just ci` green before every commit. Ports 11225 (FE) / 11226 (BE) are claimed.

(End of file)
