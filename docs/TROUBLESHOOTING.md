# Troubleshooting

## Search returns nothing at all
**Cause**: No provider answered (dead Docker, arxiv-mcp down, network out)
**Fix**: Check the receipts in the response — they name the failing pipe. Verify `GET /api/health`, then Providers page.

## OpenSERP-local always fails
**Cause**: Docker Desktop down or openserp container missing
**Fix**: Start Docker Desktop (needs BIOS virtualization), run the openserp container on :7000. Verify: `GET http://127.0.0.1:7000/google/search?text=test&limit=1`.

## Tavily says not configured
**Cause**: `TAVILY_API_KEY` unset — expected, not an error
**Fix**: Free key at tavily.com (1k/mo), set in env, restart backend. Keyless providers keep working meanwhile.

## Wikipedia 403 errors
**Cause**: Wikimedia blocks generic User-Agents
**Fix**: Already handled (courtesy UA with repo contact). If it recurs, Wikimedia changed policy — check receipts, report with timestamp.

## Backend won't start / port busy
**Cause**: Stale process owns :11226 (zombie pile-up pattern)
**Fix**: `start.ps1` clears port zombies first; if a foreign process holds it, stop that first. Never `taskkill` an NSSM child.

## "command not found: uv" / bun missing
**Cause**: Naked PC without dev tools
**Fix**: `start.bat` winget-installs uv, Node, Bun, just via Require-Command. Reopen the shell after install so PATH refreshes.

## Chat says no LLM
**Cause**: Ollama not running or no model installed
**Fix**: Install Ollama, `ollama pull qwen3:8b` (or any chat model), ensure :11434 answers. Chat is local-first by design.
