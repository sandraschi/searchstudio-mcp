# Development Setup

## Tools Required

Install all of these before continuing:

```bash
# Windows (winget)
winget install astral-sh.uv
winget install Git.Git
winget install Oven-sh.Bun
winget install Casey.Just

# Verify
uv --version
git --version
bun --version
just --version
```

## Setup

```bash
git clone https://github.com/sandraschi/searchstudio-mcp
cd searchstudio-mcp
uv sync --extra dev
cd webapp && bun install
```

## Common Tasks

```bash
just serve     # backend on :11226
just test      # pytest (mocked, offline)
just lint      # ruff + biome
just fmt       # autofix both
just type-check # pyright src + tsc
just ci        # full local gate (mirrors CI)
just mcpb-pack # Claude Desktop bundle
```

## Code Standards

- Fleet standards: `mcp-central-docs/standards/` (tool design, webapp SOTA, packaging).
- ASCII-only prose (no em dashes). 5 files max per commit.
- Providers: one module each, `(hits, receipt)` contract, keyword-callable `(query, limit=...)`.
- Tests mock the network; live verification is manual and documented in commit messages.

## Declared doubles

- `tests/`: httpx/monkeypatched fixtures only, named per test. No live network in CI.
- Tavily stub without key is product behavior (declared in receipts), not a test double.
