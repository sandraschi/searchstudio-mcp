set -e

serve:
    uv run python -m super_search_mcp --serve

stdio:
    uv run python -m super_search_mcp --stdio

test:
    uv run --extra dev pytest tests -q

lint:
    uv run --extra dev ruff check src tests
    uv run --extra dev ruff format --check src tests
    cd webapp && bun run lint

fmt:
    uv run --extra dev ruff check --fix src tests
    uv run --extra dev ruff format src tests
    cd webapp && bun x @biomejs/biome check --write src

type-check:
    uv run --extra dev pyright src
    cd webapp && bun run check

ci: lint type-check test
    cd webapp && bun run build

mcpb-pack:
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File scripts/mcpb-pack.ps1
