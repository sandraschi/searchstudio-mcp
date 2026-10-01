"""Starlette backend: REST for the webapp + fleet consumers, MCP over /mcp.

Lifespan pitfall (FastMCP 3.4.4+): the parent app MUST carry
``lifespan=_mcp_http.lifespan`` or POST /mcp/ crashes with 500.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
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
    ]
    app = Starlette(routes=routes, lifespan=_lifespan_all)
    app.mount("/mcp", _mcp_http)
    return app
