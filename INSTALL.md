# Installing SearchStudio

> **First time?** Complete [docs/ONBOARDING.md](docs/ONBOARDING.md) before expecting live results — it covers the optional provider setup (Docker for OpenSERP-local, API keys for Tavily).

## Prerequisites

Install these if you don't have them already:

| Tool | Purpose | Install |
|------|---------|---------|
| Claude Desktop | Required host (Option A/B) | [download](https://claude.ai/download) |
| Git | Clone repo (Option C/D only) | `winget install Git.Git` |
| Python + uv | Run server (Option C/D only) | `winget install astral-sh.uv` |
| Bun | Webapp (Option C/D only) | `winget install Oven-sh.Bun` |
| Docker Desktop | OpenSERP-local provider (optional) | `winget install Docker.DockerDesktop` |

> Windows: all installs via [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
> macOS: use `brew install` equivalents
> Linux: use your distro package manager

## Option A — Drag and Drop (Recommended, pending first release)

> No GitHub releases exist yet — this path activates with v0.1.0. Until then, use Option C/D.

1. Go to [Releases](https://github.com/sandraschi/searchstudio-mcp/releases/latest)
2. Download `searchstudio-{version}.mcpb`
3. Open Claude Desktop → drag the file onto the window
   *Or*: Settings → MCP Servers → Install from file

## Option B — mcpb CLI

```bash
# Requires Node.js
npx @anthropic-ai/mcpb install https://github.com/sandraschi/searchstudio-mcp
```

## Option C — Manual Configuration

1. Clone: `git clone https://github.com/sandraschi/searchstudio-mcp`
2. Install deps: `cd searchstudio-mcp && uv sync`
3. Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "searchstudio": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\searchstudio-mcp", "run", "python", "-m", "super_search_mcp"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```

Config file location:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

4. Restart Claude Desktop

## Option D — Developer Mode

For contributing or running from source with live reload.
See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Verify Installation

After installing, open Claude Desktop and type:
> "Super-search the AMD World Labs acquisition and show me which providers answered."

You should see: merged hits grouped with per-provider receipts (who answered, who blocked, latencies).

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.
