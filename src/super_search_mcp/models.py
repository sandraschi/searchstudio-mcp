"""Shared result contract: every provider kind returns these shapes.

Fan-out, merge, health, and the webapp consume this contract only — they
never touch provider internals. All dicts are JSON-serializable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

ProviderKind = Literal["serp", "knowledge", "fleet-local"]


@dataclass
class SearchHit:
    """One normalized result from any provider."""

    title: str
    url: str
    snippet: str = ""
    provider: str = ""
    kind: str = ""  # ProviderKind
    published: str | None = None
    score: float | None = None  # provider-native relevance when available

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProviderReceipt:
    """What happened when we asked one provider. Always present, even on failure."""

    provider: str
    kind: str
    ok: bool
    latency_ms: int = 0
    count: int = 0
    error: str = ""
    blocked: bool = False  # engine refused us (rate limit/captcha/IP), not a bug
    configured: bool = True  # False = declared stub (missing key/service)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FanoutResult:
    """Merged fan-out output: hits + one receipt per provider attempted."""

    query: str
    hits: list[SearchHit] = field(default_factory=list)
    receipts: list[ProviderReceipt] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "total": len(self.hits),
            "hits": [h.to_dict() for h in self.hits],
            "receipts": [r.to_dict() for r in self.receipts],
        }


def normalize_url(url: str) -> str:
    """Dedupe key: lowercase scheme/host, strip trailing slash + fragment."""
    u = (url or "").strip().lower().split("#", 1)[0]
    if u.endswith("/") and len(u) > 8:
        u = u[:-1]
    return u
