"""Tavily provider (serp, keyed with declared stub).

With ``TAVILY_API_KEY`` set: AI-native search (answer + results + optional
page content). Without it: a declared stub receipt (configured=False, setup
hint) - the fan-out continues with the keyless providers. No silent zeros.
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
                error="Tavily not configured (TAVILY_API_KEY unset). Keyless providers still ran.",
                configured=False,
                fault_kind="unconfigured",
                user_message="No Tavily key yet.",
                what_to_do="Get one at tavily.com and set TAVILY_API_KEY. The rest keeps working.",
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
        # Verified 2026-09-30 in the Tavily API spec: time_range takes
        # day/week/month/year - exactly our filter vocabulary.
        filt = (time_filter or "any").lower()
        if filt in ("day", "week", "month", "year"):
            payload["time_range"] = filt
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
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status:
                short = f"HTTP {status} from tavily"
            else:
                short = f"tavily failed ({type(e).__name__})"
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=short,
                fault_kind="down",
                user_message="Tavily request failed.",
                what_to_do="Check the key and try again; other providers already ran.",
            )
        hits = map_response(data)[: max(limit, 1)]
        return hits, _receipt(
            NAME,
            KIND,
            ok=True,
            hits=hits,
            started_ms=started,
            time_filter_applied=filt in ("day", "week", "month", "year"),
        )
