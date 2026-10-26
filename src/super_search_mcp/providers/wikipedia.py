"""Wikipedia provider (knowledge, keyless).

MediaWiki API, single round trip via generator=search: titles, intro
extracts, and canonical URLs. No key, generous courtesy limits, stable
schema - the most reliable pipe in the building.
"""

from __future__ import annotations

import urllib.parse as _parse

from ..models import SearchHit
from .base import _client, _now_ms, _receipt

NAME = "wikipedia"
KIND = "knowledge"
API = "https://en.wikipedia.org/w/api.php"
# Wikimedia blocks generic/bot-like User-Agents (403). Identify the app plus
# a contact point per the Wikimedia User-Agent policy.
WIKIMEDIA_UA = (
    "SearchStudio/0.1.0 (local fleet research tool; https://github.com/sandraschi/searchstudio-mcp)"
)


def _page_index(page) -> float:
    if isinstance(page, dict):
        try:
            return float(page.get("index", float("inf")))
        except (TypeError, ValueError):
            return float("inf")
    return float("inf")


def map_pages(pages: dict) -> list[SearchHit]:
    """Map MediaWiki generator=search pages to hits. Pure function (tested)."""
    hits = []
    # MediaWiki does not return pages in rank order (formatversion=1: alpha
    # by title, formatversion=2: by page id). Rank lives in page["index"].
    ordered = sorted((pages or {}).values(), key=_page_index)
    for page in ordered:
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

    async def search(
        self, query: str, limit: int = 10, time_filter: str = "any"
    ) -> tuple[list[SearchHit], object]:
        # generator=search carries no date metadata: accepted, unapplied, reported.
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
            async with _client(self._timeout_s, WIKIMEDIA_UA) as client:
                resp = await client.get(self._api + "?" + _parse.urlencode(params))
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status:
                short = f"HTTP {status} from wikipedia"
            else:
                short = f"wikipedia failed ({type(e).__name__})"
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=short,
                fault_kind="down",
                user_message="Wikipedia isn't reachable right now.",
                what_to_do="Try again shortly; other providers already ran.",
            )
        if isinstance(data, dict) and data.get("error"):
            err = data.get("error")
            if isinstance(err, dict):
                info = err.get("info", "MediaWiki error")
            else:
                info = str(err)
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=f"wikipedia API error: {info}"[:300],
                fault_kind="down",
                user_message="Wikipedia answered with an error, not results.",
                what_to_do="Try a shorter or simpler query; other providers already ran.",
            )
        hits = map_pages((data.get("query") or {}).get("pages", {}))[: max(limit, 1)]
        return hits, _receipt(NAME, KIND, ok=True, hits=hits, started_ms=started)
