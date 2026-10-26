"""OpenSERP-local provider (serp, keyless, Docker-backed).

Talks to the self-hosted OpenSERP service (default http://127.0.0.1:7000).
Engines are tried in order, first success wins (mode=any *inside* the
provider). An engine whose hits are all unrelated to the query (a soft block,
see relevance.py) does not count as success: the next engine is tried. A
dead local service is the classic fleet failure - it returns an error
receipt naming Docker explicitly, never a silent zero.

Freshness: OpenSERP has no date parameter, so time_filter appends an
``after:YYYY-MM-DD`` operator (computed from the real clock) to the query
text. Google/Bing honor it; other engines ignore unknown operators
gracefully. applied=True therefore means "operator transmitted", with
engine variance documented here, not "every engine filtered".
"""

from __future__ import annotations

import urllib.parse as _parse
from datetime import UTC, datetime, timedelta

from ..models import SearchHit
from ..relevance import provider_passes
from .base import _client, _now_ms, _receipt

NAME = "openserp-local"
KIND = "serp"
ENGINES = ("google", "bing", "duckduckgo", "yandex", "ecosia")


def map_results(results: list) -> list[SearchHit]:
    """Map OpenSERP result objects (defensive across schema drifts). Pure (tested)."""
    hits = []
    for r in results or []:
        if not isinstance(r, dict):
            continue
        url = r.get("url") or r.get("link") or ""
        title = r.get("title") or url
        if not url:
            continue
        hits.append(
            SearchHit(
                title=str(title),
                url=str(url),
                snippet=str(r.get("snippet") or r.get("description") or r.get("content") or ""),
                provider=NAME,
                kind=KIND,
            )
        )
    return hits


class OpenSerpProvider:
    name = NAME
    kind = KIND

    def __init__(self, base_url: str, timeout_s: float = 20.0, engines: tuple = ENGINES):
        self._base_url = (base_url or "").rstrip("/")
        self._timeout_s = timeout_s
        self._engines = engines

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
        filt = (time_filter or "any").lower()
        applied = False
        if filt in ("day", "week", "month", "year"):
            days = {"day": 1, "week": 7, "month": 30, "year": 365}[filt]
            cutoff = (datetime.now(UTC) - timedelta(days=days)).date().isoformat()
            q = f"{q} after:{cutoff}"
            applied = True
        params = _parse.urlencode({"text": q, "limit": str(min(max(limit, 1), 20))})
        last_error = "no engines configured"
        unrelated: list[str] = []  # engines that answered with junk
        try:
            async with _client(self._timeout_s) as client:
                for engine in self._engines:
                    try:
                        resp = await client.get(f"{self._base_url}/{engine}/search?{params}")
                        resp.raise_for_status()
                        data = resp.json()
                    except Exception as e:
                        status = getattr(getattr(e, "response", None), "status_code", None)
                        detail = f"HTTP {status}" if status else type(e).__name__
                        last_error = f"{engine}: {detail}"
                        continue
                    results = data.get("results", data if isinstance(data, list) else [])
                    hits = map_results(results)[: max(limit, 1)]
                    if hits and not provider_passes(query, hits):
                        # Soft block: confident junk instead of a refusal
                        # (Bing, 2026-10-11). Try the next engine.
                        unrelated.append(engine)
                        last_error = f"{engine}: results unrelated to the query"
                        continue
                    if hits:
                        return hits, _receipt(
                            NAME,
                            KIND,
                            ok=True,
                            hits=hits,
                            started_ms=started,
                            time_filter_applied=applied,
                        )
                    last_error = f"{engine}: empty result set"
        except Exception as e:
            short = f"openserp request failed ({type(e).__name__})"
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=short,
                fault_kind="down",
                user_message="OpenSERP service isn't reachable.",
                what_to_do="Start Docker Desktop with the openserp container on :7000.",
            )
        unreachable = (
            "unreachable" in last_error or "ConnectError" in last_error or "Connect" in last_error
        )
        if unreachable:
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=f"OpenSERP-local gave nothing ({last_error}).",
                fault_kind="down",
                user_message="OpenSERP isn't reachable - it needs Docker running.",
                what_to_do="Start Docker there; no key needed. DuckDuckGo still works.",
            )
        if unrelated:
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=f"OpenSERP-local gave nothing usable ({last_error}).",
                fault_kind="unrelated",
                user_message=(
                    f"OpenSERP engines ({', '.join(unrelated)}) answered with results "
                    "unrelated to your query - likely soft blocks. Ignored."
                ),
                what_to_do="Nothing to do; results from the other providers are shown.",
            )
        return [], _receipt(
            NAME,
            KIND,
            ok=False,
            hits=[],
            started_ms=started,
            error=f"OpenSERP-local gave nothing ({last_error}).",
            blocked=True,
            fault_kind="blocked",
            user_message="OpenSERP engines refused or returned nothing.",
            what_to_do="Check the openserp container logs; other providers already ran.",
        )
