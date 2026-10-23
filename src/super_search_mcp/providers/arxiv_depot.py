"""arxiv-depot provider (fleet-local, keyless): the sibling's paper library.

Queries arxiv-mcp's /api/depot/search — the user's personally ingested
papers (FTS5 keyword, LanceDB semantic, or hybrid RRF), NOT fresh preprint
search (that is the sibling arxiv-mcp provider). Your library vs the
world's new papers: different questions, different answers.

Resilience: hybrid mode 503s when the sibling's vector index is missing;
fall back to fts once and say so. Freshness maps onto the sibling's native
max_age_days. An empty personal library returns ok/0 (genuinely searched),
never an error.
"""

from __future__ import annotations

import re
import urllib.parse as _parse

from ..models import SearchHit
from .base import _client, _now_ms, _receipt

NAME = "arxiv-depot"
KIND = "fleet-local"
MARK_RE = re.compile(r"</?mark>")
MAX_AGE_DAYS = {"day": 1, "week": 7, "month": 30, "year": 365}


def clean_snippet(raw: str, limit: int = 300) -> str:
    """Strip FTS highlight marks, collapse whitespace. Pure (tested)."""
    text = MARK_RE.sub("", raw or "")
    return " ".join(text.split())[:limit]


def map_hits(hits: list) -> list[SearchHit]:
    """Map depot records to hits. Pure function (tested)."""
    out = []
    for h in hits or []:
        if not isinstance(h, dict):
            continue
        arxiv_id = h.get("arxiv_id") or ""
        title = (h.get("title") or arxiv_id or "untitled").strip()
        url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
        if not url:
            continue
        out.append(
            SearchHit(
                title=title,
                url=url,
                snippet=clean_snippet(h.get("snippet") or ""),
                provider=NAME,
                kind=KIND,
                paper_id=arxiv_id,
            )
        )
    return out


class ArxivDepotProvider:
    name = NAME
    kind = KIND

    def __init__(self, base_url: str, timeout_s: float = 20.0):
        self._base_url = (base_url or "").rstrip("/")
        self._timeout_s = timeout_s

    @property
    def configured(self) -> bool:
        return True  # address known; liveness probed per call

    async def _query(self, client, params: dict):
        url = self._base_url + "/api/depot/search?" + _parse.urlencode(params)
        resp = await client.get(url)
        if resp.status_code == 503:
            return None  # vector index missing; caller retries fts
        resp.raise_for_status()
        return resp.json()

    async def search(
        self, query: str, limit: int = 10, time_filter: str = "any"
    ) -> tuple[list[SearchHit], object]:
        started = _now_ms()
        q = (query or "").strip()
        if not q:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error="empty query"
            )
        filt = (time_filter or "any").lower()
        params = {"q": q, "limit": str(min(max(limit, 1), 25)), "mode": "hybrid"}
        if filt in MAX_AGE_DAYS:
            params["max_age_days"] = str(MAX_AGE_DAYS[filt])
        try:
            async with _client(self._timeout_s) as client:
                data = await self._query(client, params)
                if data is None:  # hybrid 503 -> fts fallback, declared below
                    params["mode"] = "fts"
                    data = await self._query(client, params)
                if data is None:
                    return [], _receipt(
                        NAME,
                        KIND,
                        ok=False,
                        hits=[],
                        started_ms=started,
                        error="depot vector index missing and fts fallback failed",
                        fault_kind="unconfigured",
                        user_message="Paper depot has nothing searchable yet.",
                        what_to_do="Ingest papers into the depot first.",
                    )
        except Exception as e:
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=f"arxiv-mcp backend unreachable at {self._base_url}: {e}",
                fault_kind="down",
                user_message="arxiv-mcp backend isn't reachable.",
                what_to_do="Start the arxiv-mcp backend (start.bat); other providers already ran.",
            )
        hits = map_hits(data.get("hits", []))[: max(limit, 1)]
        return hits, _receipt(
            NAME,
            KIND,
            ok=True,
            hits=hits,
            started_ms=started,
            time_filter_applied=filt in MAX_AGE_DAYS,
        )
