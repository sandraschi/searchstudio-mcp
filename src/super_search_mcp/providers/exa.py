"""Exa provider (serp, keyed with declared stub).

Neural search API: POST api.exa.ai/search with x-api-key. Freshness via
startPublishedDate (ISO, computed from the real clock). Verified 2026-09-30
in the Exa API spec. Without EXA_API_KEY: declared stub, fan-out continues.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ..models import SearchHit
from .base import _client, _now_ms, _receipt

NAME = "exa"
KIND = "serp"
API_URL = "https://api.exa.ai/search"
FILTER_DAYS = {"day": 1, "week": 7, "month": 30, "year": 365}


def map_response(data: dict) -> list[SearchHit]:
    """Map an Exa search response to hits. Pure function (tested)."""
    hits = []
    for r in (data or {}).get("results", []):
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
                snippet=str(r.get("text") or "")[:500],
                provider=NAME,
                kind=KIND,
                published=r.get("publishedDate"),
                score=r.get("score"),
            )
        )
    return hits


class ExaProvider:
    name = NAME
    kind = KIND

    def __init__(self, api_key: str = "", timeout_s: float = 20.0):
        self._api_key = (api_key or "").strip()
        self._timeout_s = timeout_s

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
                error="Exa not configured (EXA_API_KEY unset). Keyless providers still ran.",
                configured=False,
            )
        q = (query or "").strip()
        if not q:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error="empty query"
            )
        payload: dict = {"query": q, "numResults": min(max(limit, 1), 10)}
        filt = (time_filter or "any").lower()
        if filt in FILTER_DAYS:
            since = datetime.now(UTC) - timedelta(days=FILTER_DAYS[filt])
            payload["startPublishedDate"] = since.isoformat()
        try:
            async with _client(self._timeout_s) as client:
                resp = await client.post(
                    API_URL,
                    json=payload,
                    headers={"x-api-key": self._api_key},
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
                error=f"Exa request failed: {e}",
            )
        hits = map_response(data)[: max(limit, 1)]
        return hits, _receipt(
            NAME,
            KIND,
            ok=True,
            hits=hits,
            started_ms=started,
            time_filter_applied=filt in FILTER_DAYS,
        )
