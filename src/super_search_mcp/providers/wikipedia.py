"""Wikipedia provider (knowledge, keyless).

MediaWiki API, single round trip via generator=search: titles, intro
extracts, and canonical URLs. No key, generous courtesy limits, stable
schema — the most reliable pipe in the building.
"""

from __future__ import annotations

import urllib.parse as _parse

from ..models import SearchHit
from .base import _client, _now_ms, _receipt

NAME = "wikipedia"
KIND = "knowledge"
API = "https://en.wikipedia.org/w/api.php"


def map_pages(pages: dict) -> list[SearchHit]:
    """Map MediaWiki generator=search pages to hits. Pure function (tested)."""
    hits = []
    for page in (pages or {}).values():
        title = page.get("title", "")
        url = page.get("fullurl", "")
        if not title or not url:
            continue
        hits.append(
            SearchHit(
                title=title,
                url=url,
                snippet=(page.get("extract") or "").strip(),
                provider=NAME,
                kind=KIND,
            )
        )
    return hits


class WikipediaProvider:
    name = NAME
    kind = KIND

    def __init__(self, timeout_s: float = 20.0, language: str = "en"):
        self._timeout_s = timeout_s
        self._api = f"https://{language}.wikipedia.org/w/api.php"

    @property
    def configured(self) -> bool:
        return True

    async def search(self, query: str, limit: int = 10) -> tuple[list[SearchHit], object]:
        started = _now_ms()
        q = (query or "").strip()
        if not q:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error="empty query"
            )
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": q,
            "gsrlimit": str(min(max(limit, 1), 20)),
            "prop": "extracts|info",
            "inprop": "url",
            "exintro": "1",
            "explaintext": "1",
            "exchars": "500",
            "format": "json",
        }
        try:
            async with _client(self._timeout_s) as client:
                resp = await client.get(self._api + "?" + _parse.urlencode(params))
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error=f"request failed: {e}"
            )
        hits = map_pages((data.get("query") or {}).get("pages", {}))[: max(limit, 1)]
        return hits, _receipt(NAME, KIND, ok=True, hits=hits, started_ms=started)
