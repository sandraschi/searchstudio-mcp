set windows-shell := ["pwsh.exe", "-NoProfile", "-Command"]

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

# Desktop shell: webapp (Tauri API base baked in) + NSIS bundle.
# Backend stays separate: start it first (`just serve`), the shell degrades
# gracefully when :11226 is down.
tauri-build:
    cd webapp && $env:VITE_API_BASE = 'http://127.0.0.1:11226'; bun run build
    cd webapp/src-tauri && cargo tauri build --bundles nsis
