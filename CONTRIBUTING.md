# Contributing to searchstudio-mcp

Small fleet repo, one maintainer plus collaborators, zero patience for process theatre. These rules exist so your contribution gets merged instead of stalled.

## Issues first

- **Search before you file.** Duplicates get closed.
- **One issue, one request.** Two features = two issues.
- **Bug reports need the reproducer**: the query, the provider/kinds used, and the receipt error text. Without those, most reports cannot be reproduced.
- **Feature requests need a use case**: what are you searching for that the current providers miss?

## Pull requests

- **File the issue first** (unless it's a trivial fix: typo, broken link, lint). The issue is where scope gets agreed before code exists.
- **Keep diffs small.** One concern per PR. Max 5 files per commit.
- **Tests required.** New behavior without a test is a draft, not a PR. Run `uv run pytest tests -q` before pushing (tests mock the network boundary — no live calls in the suite).
- **Lint green:** `uv run ruff check src tests`; if you touched the webapp, `biome check` and `tsc --noEmit` in `webapp/`.
- **The maintainer merges.** Don't merge your own PR.

## Search rules: the hard parts

- **Every provider returns `(hits, receipt)` — receipts are mandatory even on total failure.** A dead provider is an error receipt, never a silent zero.
- **Never invent provider data.** No results = empty hits + honest receipt, not plausible-looking filler.
- **Timestamped `.bak` before any edit touching 3+ files.** Cleanup when satisfied.
- **No em dashes anywhere** (Unicode safety). ASCII prose.

## What this repo never does

- **No live network calls in tests.** Mock the provider boundary; live verification is manual + documented.
- **No hardcoded API keys or tokens**, in code or examples. Keys come from env, always optional.
- **No fake receipts.** A missing key is a declared stub, never a fabricated success.
