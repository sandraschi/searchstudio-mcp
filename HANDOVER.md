---
updated: 2026-09-30T20:17:29+02:00
agent: claude
status: in-progress
tags: [searchstudio-mcp, search, research, fastmcp, webapp, handover, high]
---

# Handover - searchstudio-mcp

## What's happening right now

The repo is a few hours old. The Phase 1 engine works: parallel fan-out over 5 providers,
a mandatory receipt for every provider, a SQLite health ledger, the webapp and mcpb packaging.
Claude did a read-only assessment; opencode takes over the fixes. The direction has
changed from "web meta-search" to **search in every field** (web, places, academic, news,
own fleet) with **research workflows** on top (skill builder first), running on local
Ollama, API models or Claude Desktop sampling. Full reasoning, competition analysis and
work plan: `docs/ASSESSMENT_2026-09-30.md` (sections 1-9, work packages WP0-WP9).

## Last concrete action

- WP2 done (opencode): `time_filter` is real — Tavily native, sibling hours,
  OpenSERP after:, DDG/Wikipedia declared-unapplied, receipt flag,
  freshness UI, 25 tests green, pushed. Live-proved against the real APIs.
- WP1 done (opencode): skill:// registered + tested, dead button, promise
  order, README/INSTALL honesty pass, pushed.

## Next step

WP3: README rewrite per assessment 3.4 (vision first, live input-output
example, status table, glossary to ONBOARDING, working Quick Install).
Needs no decisions.

## Blockers

Decided by Sandra 2026-09-30 (rest still open):
- DONE #6 product surface: public repo with brilliant webapp.
- DONE #1 naming: unify on searchstudio (repo-scoped).
- DONE #3 LLM backends: three modes confirmed.
- DEFERRED #2 fetch path: Jina must be evaluated as an mcd integration first.
- OPEN #4 skill_build vs memops boundary, #5 research ownership, release question.

## Context the next agent needs

- Keep the engine: `fanout.py`, receipts and `db.py` are the right foundation. Build
  fields and research on top; do not rewrite the engine.
- Repo rule "no stubs": new operations appear in the tool surface only once they work
  end to end. `time_filter` today breaks this rule quietly (the param is accepted and
  ignored); WP2 fixes it.
- Do not copy memops' research code (`advanced-memory-mcp` research_orchestrator /
  make_skill_advanced): the planning is fixed text, the years are hardcoded and stale, and
  the output is full of `[UNICODE]` junk. Assessment 9.1 has the details. A separate fix
  task exists for memops itself.
- Sampling with tools (SEP-1577) only works in Claude Desktop. Every research workflow
  must also run with the server's own models (Ollama/API) and in host-driven mode
  (assessment 9.4). Never make sampling the only path.
- Inject the real current date into every LLM prompt; never let a model supply dates.
- Backend framework: the fleet standard is now FastAPI + Pydantic v2 (reversed
  2026-09-30). Do not migrate during WP0-WP3; migrate `backend.py` at the start of WP4
  (details in the assessment's WP4).
- Canonical fleet registry: `mcp-central-docs/operations/fleet-registry.json` (not the
  small copy in opencode-cli-mcp).
- Naming is split (`searchstudio-mcp` / `super_search_mcp` / `super-search` /
  `searchops` / `SUPER_SEARCH_*`). Do not rename without Sandra's go-ahead.
- There are no git tags and no GitHub releases, although README Quick Install points to
  Releases. Cutting a release publishes something, so ask Sandra first.
- Fleet rules: max 5 files per commit, `.bak` before 3+ file edits, ASCII-only prose,
  `just ci` green before every commit. Ports 11225 (FE) / 11226 (BE) are claimed.
