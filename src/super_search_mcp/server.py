"""SearchStudio MCP server: portmanteau + model catalog lookup + Prefab card.

Tool surface (deliberately small - Phase 1):
- ``searchops`` - super_search | provider_health | self_test
- ``models_lookup`` - models.dev catalog filter (tool_call + min context, by $/1M)
- ``provider_health_app`` - Prefab card twin of provider_health (app=True)

All tools are READ_ONLY with openWorldHint (they reach external networks).
Phase 2/3 operations (aiwatcher_feed, condense) are NOT advertised until
they exist - no stubs, per TOOL_DESIGN_STANDARDS §15.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP
from fastmcp.tools import ToolResult
from prefab_ui import PrefabApp
from prefab_ui.components import Div, Heading, Text

from . import fanout as _fanout
from .config import settings
from .db import _connect
from .models import FanoutResult
from .providers import build_providers
from .providers.modelsdev import _iter_models, filter_models, load_catalog

logger = logging.getLogger("searchstudio")

_READ_ONLY = {"readOnlyHint": True, "openWorldHint": True}


def _db_path():
    from pathlib import Path

    return Path(settings.data_dir) / "searchstudio.sqlite3"


@asynccontextmanager
async def lifespan(app):
    """Shallow startup probe: settings resolve, data dir writable. No network."""
    try:
        db_path = _db_path()
        conn = _connect(db_path)
        conn.close()
        logger.info("searchstudio ready (db=%s)", db_path)
    except Exception:
        logger.exception("startup probe failed")
        raise
    yield


mcp = FastMCP("searchstudio", lifespan=lifespan)


@mcp.resource("skill://super-search")
def get_super_search_skill() -> str:
    """SearchStudio search-expert skill (SKILL.md content)."""
    path = Path(__file__).parent / "skills" / "super-search" / "SKILL.md"
    return path.read_text(encoding="utf-8")


def _parse_csv(value: str, allowed: set[str]) -> tuple[str, ...]:
    parts = [p.strip().lower() for p in (value or "").split(",") if p.strip()]
    return tuple(p for p in parts if p in allowed)


@mcp.tool(annotations=_READ_ONLY)
async def searchops(
    operation: Literal["super_search", "provider_health", "self_test"] = "super_search",
    query: str = "",
    kinds: str = "fleet-local,knowledge,serp",
    providers: str = "",
    time_filter: str = "any",
    limit: int = 10,
    mode: Literal["balanced", "any"] = "balanced",
    window_hours: int = 24,
) -> dict:
    """Parallel multi-provider search with health receipts (SearchStudio).

    ALSO KNOWN AS "super search" / super_search: when the user says
    "super search ...", "super_search ...", or "searchops ...", call this
    tool with operation="super_search" and the rest as query.

    Fans out across fleet-local knowledge (arxiv-mcp), curated sources
    (Wikipedia), and web search (OpenSERP-local, DuckDuckGo, Tavily) in
    parallel, merges by kind priority (local first), and reports one receipt
    per provider - dead pipes are skipped AND reported, never silent zeros.

    Args:
        operation: super_search (default) | provider_health | self_test.
        query: Search text. Required for super_search.
        kinds: CSV subset of fleet-local,knowledge,serp (default all).
        providers: CSV provider allowlist, e.g. "wikipedia,tavily". Empty = all.
        time_filter: any (default) | day | week | month | year. Tavily passes
            it natively, the sibling takes hours, OpenSERP appends an after:
            operator; DuckDuckGo and Wikipedia run unfiltered and say so.
            Every receipt carries time_filter_applied.
        limit: Max merged hits, 1..50 (default 10). Documented cap.
        mode: balanced (merged best-of-all, default) | any (fastest kind
            with hits wins, full receipts still returned).
        window_hours: provider_health lookback (default 24).

    Returns:
        super_search: {query, total, hits[], receipts[], coverage} - hits bounded by
        limit; receipts carry per-provider ok/latency_ms/count/error/blocked plus
        fault_kind/user_message/what_to_do/retry_in (fleet standard
        EXTERNAL_FAULT_TRANSPARENCY.md); coverage is the one-line what-was-searched summary.
        provider_health: {providers[]} rolling scoreboard + configured flags.
        self_test: {matrix[]} 3 canonical probes x providers with receipts.
        Failures: {success False, error, error_type, suggestions}.
    """
    providers_all = build_providers(settings)
    names = {p.name for p in providers_all}
    kinds_all = {"fleet-local", "knowledge", "serp"}
    try:
        if operation == "super_search":
            if not query.strip():
                return {
                    "success": False,
                    "error": "query is required for super_search",
                    "error_type": "validation",
                    "suggestions": ["Pass a non-empty query string."],
                }
            result: FanoutResult = await _fanout.fanout(
                providers_all,
                query,
                limit=min(max(limit, 1), 50),
                kinds=_parse_csv(kinds, kinds_all) or tuple(kinds_all),
                only=_parse_csv(providers, names),
                db_path=_db_path(),
                time_filter=time_filter,
            )
            payload = result.to_dict()
            if mode == "any":
                for kind in ("fleet-local", "knowledge", "serp"):
                    kind_hits = [h for h in payload["hits"] if h["kind"] == kind]
                    if kind_hits:
                        payload["hits"] = kind_hits
                        payload["total"] = len(kind_hits)
                        payload["mode_winner_kind"] = kind
                        break
            payload["time_filter"] = time_filter
            return {"success": True, **payload}
        if operation == "provider_health":
            return {
                "success": True,
                "window_hours": window_hours,
                "providers": _fanout.health(_db_path(), window_hours=window_hours),
                "configured": {p.name: p.configured for p in providers_all},
                "note": "Empty scoreboard means no searches recorded yet - run super_search first.",
            }
        if operation == "self_test":
            probes = [
                "quantum computing breakthrough",
                "Hollabrunn local history",
                "best sourdough hydration percentage",
            ]
            matrix = []
            for probe in probes:
                res = await _fanout.fanout(
                    providers_all,
                    probe,
                    limit=3,
                    kinds=tuple(kinds_all),
                    only=(),
                    db_path=_db_path(),
                )
                matrix.append(
                    {
                        "probe": probe,
                        "total": len(res.hits),
                        "by_provider": {r.provider: r.count for r in res.receipts},
                        "failed": [r.provider for r in res.receipts if not r.ok],
                    }
                )
            return {"success": True, "matrix": matrix}
        return {
            "success": False,
            "error": f"unknown operation: {operation}",
            "error_type": "validation",
            "suggestions": ["Use super_search, provider_health, or self_test."],
        }
    except Exception as e:
        logger.exception("searchops failed")
        return {
            "success": False,
            "error": str(e),
            "error_type": "general",
            "suggestions": ["Check backend logs; retry once (transient blocks are normal)."],
        }


@mcp.tool(annotations=_READ_ONLY)
async def models_lookup(
    query: str = "",
    needs_tool_call: bool = False,
    min_context: int = 0,
    max_input_cost: float = 0.0,
    open_weights_only: bool = False,
    limit: int = 20,
    refresh: bool = False,
) -> dict:
    """Filter the models.dev catalog by capability, context, and price.

    Answers "which models have tool_call + context >= X, cheapest first?"
    from the cached community catalog (refreshed at most once per TTL).
    Keyless and READ_ONLY; dead catalog with no cache returns down, never
    silent zeros.

    Args:
        query (str): Free-text filter on model id/name/description. Empty = all.
        needs_tool_call (bool): Keep only models with tool_call support.
        min_context (int): Minimum context window in tokens (0 = no floor).
        max_input_cost (float): Max input $/1M tokens (0 = no cap).
        open_weights_only (bool): Keep only open-weights models.
        limit (int): Max rows, 1..50 (default 20). Documented cap.
        refresh (bool): Force a catalog refresh instead of using the cache.

    Returns:
        {success, query, total, items[], meta{cached_at_ms, stale, source}} -
        items sorted by input $/1M ascending (unknown price last), bounded by
        limit. Failures: {success False, error, error_type, suggestions}.

    Examples:
        await models_lookup(needs_tool_call=True, min_context=200000, limit=10)
        await models_lookup(query="claude", max_input_cost=5.0)
    """
    try:
        payload, meta = await load_catalog(
            settings.data_dir,
            settings.modelsdev_catalog_url,
            settings.default_timeout_s,
            settings.modelsdev_cache_hours,
            force_refresh=refresh,
        )
        if payload is None:
            return {
                "success": False,
                "error": f"models.dev catalog unreachable: {meta['error']}",
                "error_type": "down",
                "suggestions": [
                    "Retry shortly (transient fetch failure).",
                    "Check MODELSDEV_CATALOG_URL and outbound network access.",
                ],
            }
        rows = filter_models(
            payload,
            query=query or "",
            needs_tool_call=needs_tool_call,
            min_context=max(min_context, 0),
            max_input_cost=max(max_input_cost, 0.0),
            open_weights_only=open_weights_only,
            limit=min(max(limit, 1), 50),
        )
        return {
            "success": True,
            "query": query or "",
            "total": len(rows),
            "items": rows,
            "meta": {
                "scanned": len(_iter_models(payload)),
                "cached_at_ms": meta["cached_at_ms"],
                "stale": meta["stale"],
                "refresh_error": meta["error"],
                "source": settings.modelsdev_catalog_url,
            },
        }
    except Exception as e:
        logger.exception("models_lookup failed")
        return {
            "success": False,
            "error": str(e),
            "error_type": "general",
            "suggestions": ["Check backend logs; retry once."],
        }


@mcp.tool(annotations=_READ_ONLY, app=True)
async def provider_health_app(window_hours: int = 24) -> ToolResult:
    """Provider health scoreboard as a Prefab card (in-chat UI)."""
    rows = _fanout.health(_db_path(), window_hours=window_hours)
    providers_all = build_providers(settings)
    children = [
        Heading(content="Provider health"),
        Text(content=f"{len(rows)} providers with data in the last {window_hours}h."),
    ]
    for row in rows:
        ok_pct = row["success_rate"] * 100
        children.append(
            Text(
                content=f"{row['provider']}: {ok_pct:.0f}% ok, "
                f"p50 {row['p50_latency_ms']}ms "
                f"({row['ok']}/{row['attempts']}, {row['blocked']} blocked)"
            )
        )
    for p in providers_all:
        if not p.configured:
            children.append(
                Text(content=f"{p.name}: not configured - keyless providers still work.")
            )
    view = Div(children=children)
    app = PrefabApp(title="SearchStudio provider health", view=view)
    summary = (
        "; ".join(f"{r['provider']} {r['success_rate'] * 100:.0f}% ok" for r in rows)
        or "no search data recorded yet"
    )
    return ToolResult(content=summary, structured_content=app)
