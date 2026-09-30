"""Tavily provider (serp, keyed with declared stub).

With ``TAVILY_API_KEY`` set: AI-native search (answer + results + optional
page content). Without it: a declared stub receipt (configured=False, setup
hint) — the fan-out continues with the keyless providers. No silent zeros.
"""

from __future__ import annotations

from ..models import SearchHit
from .base import _client, _now_ms, _receipt

NAME = "tavily"
KIND = "serp"
API_URL = "https://api.tavily.com/search"


def map_response(data: dict) -> list[SearchHit]:
    """Map a Tavily search response to hits. Pure function (tested)."""
    hits = []
    for r in (data or {}).get("results", []):
        if not isinstance(r, dict):
            continue
        url = r.get("url") or ""
        title = r.get("title") or url
        if not url:
            continue
        snippet = r.get("content") or ""
        hits.append(
            SearchHit(
                title=str(title),
                url=str(url),
                snippet=str(snippet)[:500],
                provider=NAME,
                kind=KIND,
                published=r.get("published_date"),
                score=r.get("score"),
            )
        )
    return hits


class TavilyProvider:
    name = NAME
    kind = KIND

    def __init__(self, api_key: str = "", timeout_s: float = 20.0):
        self._api_key = (api_key or "").strip()
        self._timeout_s = timeout_s

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    async def search(self, query: str, limit: int = 10) -> tuple[list[SearchHit], object]:
        started = _now_ms()
        if not self._api_key:
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error="Tavily not configured (TAVILY_API_KEY unset). Keyless providers still ran.",
                configured=False,
            )
        q = (query or "").strip()
        if not q:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error="empty query"
            )
        payload = {
            "query": q,
            "max_results": min(max(limit, 1), 10),
            "include_answer": False,
            "include_raw_content": False,
        }
        try:
            async with _client(self._timeout_s) as client:
                resp = await client.post(
                    API_URL,
                    json=payload,
                    headers={"Authorization": f"Bearer {self._api_key}"},
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
                error=f"Tavily request failed: {e}",
            )
        hits = map_response(data)[: max(limit, 1)]
        return hits, _receipt(NAME, KIND, ok=True, hits=hits, started_ms=started)
