"""Brave provider (serp, keyed with declared stub).

Independent index (no Google/Bing dependency) via api.search.brave.com:
GET /res/v1/web/search with X-Subscription-Token. Freshness via the
freshness param (pd/pw/pm/py), honored server-side - verified against the
Brave Search API reference 2026-10-23. Without BRAVE_API_KEY: declared stub,
fan-out continues.
"""

from __future__ import annotations

from ..models import SearchHit
from .base import _client, _now_ms, _receipt

NAME = "brave"
KIND = "serp"
API_URL = "https://api.search.brave.com/res/v1/web/search"
FILTER_VALUES = {"day": "pd", "week": "pw", "month": "pm", "year": "py"}


def map_response(data: dict) -> list[SearchHit]:
    """Map a Brave web/search response to hits. Pure function (tested)."""
    hits = []
    web = (data or {}).get("web", {})
    results = web.get("results", []) if isinstance(web, dict) else []
    for r in results:
        if not isinstance(r, dict):
            continue
        url = r.get("url") or ""
        title = r.get("title") or url
        if not url:
            continue
        hits.append(
            SearchHit(
                title=str(title),
                url=str(url),
                snippet=str(r.get("description") or "")[:500],
                provider=NAME,
                kind=KIND,
                published=r.get("age"),
            )
        )
    return hits


class BraveProvider:
    name = NAME
    kind = KIND

    def __init__(self, api_key: str = "", timeout_s: float = 20.0, goggles: list | None = None):
        self._api_key = (api_key or "").strip()
        self._timeout_s = timeout_s
        self._goggles = [g for g in (goggles or []) if isinstance(g, str) and g]

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    async def search(
        self, query: str, limit: int = 10, time_filter: str = "any"
    ) -> tuple[list[SearchHit], object]:
        started = _now_ms()
        if not self._api_key:
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error="Brave not configured (BRAVE_API_KEY unset). Keyless providers still ran.",
                configured=False,
                fault_kind="unconfigured",
                user_message="No Brave key yet.",
                what_to_do="Get one at brave.com/search/api and set BRAVE_API_KEY.",
            )
        q = (query or "").strip()
        if not q:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error="empty query"
            )
        filt = (time_filter or "any").lower()
        params: dict = {"q": q, "count": min(max(limit, 1), 20)}
        if filt in FILTER_VALUES:
            params["freshness"] = FILTER_VALUES[filt]
        if self._goggles:
            params["goggles"] = list(self._goggles)
        try:
            async with _client(self._timeout_s) as client:
                resp = await client.get(
                    API_URL,
                    params=params,
                    headers={"X-Subscription-Token": self._api_key},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=f"Brave request failed: {e}",
                fault_kind="down",
                user_message="Brave request failed.",
                what_to_do="Check the key and try again; other providers already ran.",
            )
        hits = map_response(data)[: max(limit, 1)]
        return hits, _receipt(
            NAME,
            KIND,
            ok=True,
            hits=hits,
            started_ms=started,
            time_filter_applied=filt in FILTER_VALUES,
            goggles_applied=list(self._goggles),
        )
