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
        snippet = f"{authors} - {summary}".strip(" -") if authors else summary
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

    async def search(
        self, query: str, limit: int = 10, time_filter: str = "any"
    ) -> tuple[list[SearchHit], object]:
        started = _now_ms()
        q = (query or "").strip()
        if not q:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error="empty query"
            )
        # The sibling endpoint takes hours natively: map our vocabulary onto it.
        hours_map = {"day": 24, "week": 24 * 7, "month": 24 * 30, "year": 24 * 365}
        filt = (time_filter or "any").lower()
        params = {"q": q, "limit": str(min(max(limit, 1), 25))}
        if filt in hours_map:
            params["hours"] = str(hours_map[filt])
        url = self._base_url + "/api/preprints/search?" + _parse.urlencode(params)
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
                fault_kind="down",
                user_message="arxiv-mcp backend isn't reachable.",
                what_to_do="Start the arxiv-mcp backend (start.bat); other providers already ran.",
            )
        hits = map_papers(data.get("merged", []))[: max(limit, 1)]
        backend_errors = data.get("errors") or {}
        if not hits and backend_errors:
            # Backend answered but every leg failed (throttle/slowness): report
            # its own messages instead of a bare empty ok:true.
            detail = "; ".join(f"{k}: {v}" for k, v in backend_errors.items())
            keys = " ".join(backend_errors.keys()).lower()
            if "arxiv_timeout" in keys or "rate" in keys or "429" in detail:
                fault, retry = "rate_limited", "~5 minutes"
                todo = "Wait ~5 min; each retry extends the cooldown. Other providers already ran."
            elif "fanout" in keys:
                fault, retry = "slow", "~2 minutes"
                todo = "Wait ~2 min or narrow to fewer servers. Other providers already ran."
            else:
                fault, retry = "down", ""
                todo = "Wait a few minutes and retry; other providers already ran."
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=f"arxiv-mcp searched but failed: {detail}",
                fault_kind=fault,
                user_message=f"arXiv backend searched but failed: {detail}",
                what_to_do=todo,
                retry_in=retry,
                time_filter_applied=filt in hours_map,
            )
        return hits, _receipt(
            NAME,
            KIND,
            ok=True,
            hits=hits,
            started_ms=started,
            time_filter_applied=filt in hours_map,
        )
