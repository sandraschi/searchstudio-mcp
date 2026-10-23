"""Starlette backend: REST for the webapp + fleet consumers, MCP over /mcp.

Lifespan pitfall (FastMCP 3.4.4+): the parent app MUST carry
``lifespan=_mcp_http.lifespan`` or POST /mcp/ crashes with 500.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from . import fanout as _fanout
from .config import settings
from .db import _connect
from .providers import build_providers
from .server import lifespan, mcp

logger = logging.getLogger("searchstudio")


def _configured_map() -> dict[str, bool]:
    return {p.name: p.configured for p in build_providers(settings)}


async def health(request):
    try:
        conn = _connect(_db_file())
        conn.close()
        db_ok: bool | str = True
    except Exception as e:
        db_ok = str(e)
    return JSONResponse(
        {
            "success": True,
            "service": "searchstudio-mcp",
            "version": "0.1.0",
            "configured": any(_configured_map().values()),
            "authenticated": True,  # no user auth on this plane; provider keys are server-side
            "db": "ok" if db_ok is True else f"error: {db_ok}",
            "providers": [
                {"name": p.name, "kind": p.kind, "configured": p.configured}
                for p in build_providers(settings)
            ],
        }
    )


def _db_file() -> Path:
    return Path(settings.data_dir) / "searchstudio.sqlite3"


async def capabilities(request):
    return JSONResponse(
        {
            "service": "searchstudio-mcp",
            "mcp_tools": ["searchops", "provider_health_app"],
            "rest": [
                "/api/health",
                "/api/capabilities",
                "/api/skills",
                "/skill/{name}",
                "/api/search",
                "/api/providers",
                "/api/matrix",
                "/api/provider-keys",
                "/api/provider-keys/test",
                "/api/settings/fallbacks",
            ],
            "provider_kinds": ["fleet-local", "knowledge", "serp"],
        }
    )


async def skills(request):
    return JSONResponse(
        {"skills": [{"name": "super-search", "title": "SearchStudio search expert"}]}
    )


async def skill_content(request):
    name = request.path_params.get("name", "")
    if name != "super-search":
        return JSONResponse({"success": False, "error": f"unknown skill: {name}"}, status_code=404)
    path = Path(__file__).parent / "skills" / "super-search" / "SKILL.md"
    if not path.exists():
        return JSONResponse({"success": False, "error": "skill file missing"}, status_code=500)
    return JSONResponse(
        {"success": True, "name": name, "content": path.read_text(encoding="utf-8")}
    )


async def api_search(request):
    q = request.query_params.get("q", "")
    kinds = request.query_params.get("kinds", "fleet-local,knowledge,serp")
    providers = request.query_params.get("providers", "")
    try:
        limit = min(max(int(request.query_params.get("limit", "10")), 1), 50)
    except ValueError:
        limit = 10
    mode = request.query_params.get("mode", "balanced")
    if mode not in ("balanced", "any"):
        mode = "balanced"
    time_filter = request.query_params.get("time_filter", "any")
    from .server import searchops

    return JSONResponse(
        await searchops(
            operation="super_search",
            query=q,
            kinds=kinds,
            providers=providers,
            limit=limit,
            mode=mode,  # type: ignore[arg-type]
            time_filter=time_filter,
        )
    )


async def api_providers(request):
    window = int(request.query_params.get("window_hours", "24") or 24)
    return JSONResponse(
        {
            "success": True,
            "scoreboard": _fanout.health(_db_file(), window_hours=window),
            "configured": _configured_map(),
        }
    )


async def api_matrix(request):
    from .server import searchops

    return JSONResponse(await searchops(operation="self_test"))


async def api_provider_keys(request):
    """GET: key status (set/unset + source, never values)."""
    from .config import MANAGED_KEY_NAMES, resolve_key

    return JSONResponse(
        {
            "success": True,
            "keys": [
                {"name": name, "set": bool(key), "source": source}
                for name in MANAGED_KEY_NAMES
                for key, source in [resolve_key(settings, name)]
            ],
        }
    )


async def api_provider_keys_save(request):
    """POST {name, key}: store a UI-entered key (allowlisted names only)."""
    from .config import save_file_key

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "invalid JSON body"}, status_code=400)
    name = (body.get("name") or "").strip()
    key = body.get("key") or ""
    try:
        save_file_key(settings.data_dir, name, key)
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    return JSONResponse({"success": True, "name": name, "source": "file"})


async def api_provider_keys_delete(request):
    """DELETE ?name=: remove a UI-stored key (env-set keys are unaffected)."""
    from .config import delete_file_key

    name = (request.query_params.get("name") or "").strip()
    try:
        removed = delete_file_key(settings.data_dir, name)
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    return JSONResponse({"success": True, "name": name, "removed": removed})


async def api_provider_keys_test(request):
    """POST {name}: spend one minimal call to check the key is valid.

    Uses the resolved key (env first, stored file second) for a limit=1
    probe query. Only the keyed search providers support it (Tavily/Exa/Brave).
    """
    from .config import resolve_key

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "invalid JSON body"}, status_code=400)
    name = (body.get("name") or "").strip()
    provider: Any = None
    if name == "TAVILY_API_KEY":
        from .providers.tavily import TavilyProvider

        key, source = resolve_key(settings, name)
        provider = TavilyProvider(api_key=key)
    elif name == "EXA_API_KEY":
        from .providers.exa import ExaProvider

        key, source = resolve_key(settings, name)
        provider = ExaProvider(api_key=key)
    elif name == "BRAVE_API_KEY":
        from .providers.brave import BraveProvider

        key, source = resolve_key(settings, name)
        provider = BraveProvider(api_key=key)
    else:
        return JSONResponse(
            {"success": False, "error": f"no live test for {name or '(empty)'}"},
            status_code=400,
        )
    if not key:
        return JSONResponse(
            {"success": False, "error": f"{name} is unset (no env, no stored key)"},
            status_code=400,
        )
    try:
        hits, receipt = await provider.search("test", limit=1)
    except Exception as e:
        return JSONResponse({"success": False, "error": f"probe crashed: {e}"})
    return JSONResponse(
        {
            "success": True,
            "name": name,
            "source": source,
            "valid": bool(receipt.ok),
            "latency_ms": receipt.latency_ms,
            "detail": receipt.error or f"{receipt.count} hit(s) returned",
        }
    )


def _fallback_status() -> dict:
    from . import breakers
    from .config import browser_fallback_allowed

    allowed, source = browser_fallback_allowed(settings.data_dir)
    return {
        "success": True,
        "browser_fallback": allowed,
        "source": source,
        "engine": breakers.breaker_engine(),
        "legs": breakers.breaker_legs(),
    }


async def api_fallbacks(request):
    """GET: browser fallback (Camoufox) switch + where the value comes from."""
    return JSONResponse(_fallback_status())


async def api_fallbacks_save(request):
    """POST {browser_fallback: bool}: store the Settings checkbox.

    Env hard-off (BROWSER_MCP_URL empty) still wins; the response reports the
    effective value so the UI never shows a state that is not in force.
    """
    from .config import save_pref

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "invalid JSON body"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"success": False, "error": "expected a JSON object"}, status_code=400)
    try:
        save_pref(settings.data_dir, "browser_fallback", body.get("browser_fallback"))
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    return JSONResponse(_fallback_status())


async def _sibling_full_text(base_url: str, paper_id: str) -> str:
    """Fetch sibling full-text markdown. Raises on any failure (caller reports)."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=8.0)) as client:
        resp = await client.get(
            f"{base_url.rstrip('/')}/api/paper/full-text",
            params={"paper_id": paper_id},
        )
        resp.raise_for_status()
        return str(resp.json().get("markdown") or "")


async def api_paper_full_text(request):
    """GET /api/paper/full-text?paper_id= : proxy the sibling's markdown.

    Lazy-loads the full text for a paper card. Caps at 100k chars so one
    giant paper cannot blow up the webapp DOM; the card says when capped.
    """
    pid = (request.query_params.get("paper_id") or "").strip()
    if not pid:
        return JSONResponse({"success": False, "error": "paper_id is required"}, status_code=400)
    try:
        md = await _sibling_full_text(settings.arxiv_mcp_base_url, pid)
    except Exception as e:
        return JSONResponse(
            {"success": False, "paper_id": pid, "error": f"sibling full-text fetch failed: {e}"}
        )
    if not md:
        return JSONResponse(
            {"success": False, "paper_id": pid, "error": "sibling returned no text"}
        )
    capped, text = (True, md[:100_000]) if len(md) > 100_000 else (False, md)
    return JSONResponse({"success": True, "paper_id": pid, "markdown": text, "truncated": capped})


async def api_goggles(request):
    """GET /api/goggles: all lenses (prepared + custom) with enabled flags."""
    from .goggles import load_store

    return JSONResponse({"success": True, **load_store(settings.data_dir)})


async def api_goggles_save(request):
    """POST /api/goggles {name, url?, notes?, enabled?}: upsert a lens.

    Enabling requires a public https URL; otherwise the lens would silently
    do nothing. Returns {success, entry?} or {success: False, error}.
    """
    from .goggles import upsert_entry

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "invalid JSON body"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"success": False, "error": "expected a JSON object"}, status_code=400)
    entry, err = upsert_entry(
        settings.data_dir,
        body.get("name", ""),
        url=body.get("url", ""),
        notes=body.get("notes", ""),
        enabled=body.get("enabled"),
    )
    if err:
        return JSONResponse({"success": False, "error": err}, status_code=400)
    return JSONResponse({"success": True, "entry": entry})


async def api_goggles_delete(request):
    """DELETE /api/goggles {name}: delete a custom lens (prepared are kept)."""
    from .goggles import delete_entry

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "invalid JSON body"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"success": False, "error": "expected a JSON object"}, status_code=400)
    ok, err = delete_entry(settings.data_dir, body.get("name", ""))
    if not ok:
        return JSONResponse({"success": False, "error": err}, status_code=400)
    return JSONResponse({"success": True})


def build_app() -> Starlette:
    _mcp_http = mcp.http_app(path="/")

    @asynccontextmanager
    async def _lifespan_all(app: Starlette) -> AsyncIterator[None]:
        async with lifespan(app):
            async with _mcp_http.lifespan(app):
                yield

    routes = [
        Route("/api/health", health),
        Route("/api/capabilities", capabilities),
        Route("/api/skills", skills),
        Route("/skill/{name}", skill_content),
        Route("/api/search", api_search),
        Route("/api/providers", api_providers),
        Route("/api/matrix", api_matrix),
        Route("/api/provider-keys", api_provider_keys, methods=["GET"]),
        Route("/api/provider-keys", api_provider_keys_save, methods=["POST"]),
        Route("/api/provider-keys", api_provider_keys_delete, methods=["DELETE"]),
        Route("/api/provider-keys/test", api_provider_keys_test, methods=["POST"]),
        Route("/api/settings/fallbacks", api_fallbacks, methods=["GET"]),
        Route("/api/settings/fallbacks", api_fallbacks_save, methods=["POST"]),
        Route("/api/paper/full-text", api_paper_full_text, methods=["GET"]),
        Route("/api/goggles", api_goggles, methods=["GET"]),
        Route("/api/goggles", api_goggles_save, methods=["POST"]),
        Route("/api/goggles", api_goggles_delete, methods=["DELETE"]),
    ]
    app = Starlette(routes=routes, lifespan=_lifespan_all)
    # Tauri desktop shell: production builds call the backend directly (no
    # Vite proxy inside the shell), so the Tauri origins must be allowed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "tauri://localhost",
            "http://tauri.localhost",
            "https://tauri.localhost",
        ],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )
    app.mount("/mcp", _mcp_http)
    return app

