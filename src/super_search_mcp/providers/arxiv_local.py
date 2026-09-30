"""arxiv-mcp crossconnect provider (fleet-local, keyless).

Queries the sibling arxiv-mcp HTTP backend (preprint fan-out: arXiv plus
bioRxiv/medRxiv/ChemRxiv/Research Square/SocArXiv/PsyArXiv) and maps merged
papers to hits. Soft degradation: backend down means an error receipt, and
the fan-out continues with the other providers.
"""

from __future__ import annotations

import urllib.parse as _parse

from ..models import SearchHit
from .base import _client, _now_ms, _receipt

NAME = "arxiv-mcp"
KIND = "fleet-local"


def map_papers(papers: list) -> list[SearchHit]:
    """Map arxiv-mcp merged papers to hits. Pure function (tested)."""
    hits = []
    for p in papers or []:
        pid = p.get("paper_id") or ""
        url = p.get("html_url") or (
            f"https://arxiv.org/abs/{pid}" if pid and "/" not in pid else ""
        )
        title = p.get("title") or pid or "untitled"
        if not url:
            continue
        authors = ", ".join((p.get("authors") or [])[:3])
        summary = (p.get("summary") or "")[:300]
        snippet = f"{authors} — {summary}".strip(" —") if authors else summary
        hits.append(
            SearchHit(
                title=title,
                url=url,
                snippet=snippet,
                provider=NAME,
                kind=KIND,
                published=p.get("published"),
            )
        )
    return hits


class ArxivMcpProvider:
    name = NAME
    kind = KIND

    def __init__(self, base_url: str, timeout_s: float = 20.0):
        self._base_url = (base_url or "").rstrip("/")
        self._timeout_s = timeout_s

    @property
    def configured(self) -> bool:
        return True  # address known; liveness probed per call

    async def search(self, query: str, limit: int = 10) -> tuple[list[SearchHit], object]:
        started = _now_ms()
        q = (query or "").strip()
        if not q:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error="empty query"
            )
        url = (
            self._base_url
            + "/api/preprints/search?"
            + _parse.urlencode({"q": q, "limit": str(min(max(limit, 1), 25))})
        )
        try:
            async with _client(self._timeout_s) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=f"arxiv-mcp backend unreachable at {self._base_url}: {e}",
            )
        hits = map_papers(data.get("merged", []))[: max(limit, 1)]
        return hits, _receipt(NAME, KIND, ok=True, hits=hits, started_ms=started)
