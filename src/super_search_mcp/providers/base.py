"""Provider protocol: every provider kind speaks this interface.

A provider returns ``(hits, receipt)`` - results plus a mandatory receipt
describing what happened, even on total failure. Fan-out, merge, and health
consume only this contract.
"""

from __future__ import annotations

import time
from typing import Protocol

import httpx

from ..models import ProviderReceipt, SearchHit


class Provider(Protocol):
    name: str
    kind: str

    @property
    def configured(self) -> bool:
        """False = declared stub (missing key/service); caller reports, never fails silent."""
        ...

    async def search(
        self, query: str, limit: int = 10, time_filter: str = "any"
    ) -> tuple[list[SearchHit], ProviderReceipt]: ...


def _receipt(
    name: str,
    kind: str,
    *,
    ok: bool,
    hits: list[SearchHit],
    started_ms: int,
    error: str = "",
    blocked: bool = False,
    configured: bool = True,
    time_filter_applied: bool = False,
) -> ProviderReceipt:
    now_ms = int(time.time() * 1000)
    return ProviderReceipt(
        provider=name,
        kind=kind,
        ok=ok,
        latency_ms=max(0, now_ms - started_ms),
        count=len(hits),
        error=error,
        blocked=blocked,
        configured=configured,
        time_filter_applied=time_filter_applied,
    )


def _now_ms() -> int:
    return int(time.time() * 1000)


def _client(
    timeout_s: float = 20.0, user_agent: str = "searchstudio-mcp/0.1.0"
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout_s, connect=8.0),
        headers={"User-Agent": user_agent},
        follow_redirects=True,
    )
