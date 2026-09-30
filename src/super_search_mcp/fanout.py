"""Fan-out engine: parallel providers, kind-priority merge, receipts.

Ordering philosophy: fleet-local first (private, free, instant), then
curated knowledge, then the whole web (broad, billed, flaky). Phase 1 uses
this static kind order; the health ledger (db.py) already records per-call
outcomes so Phase 2 can switch to adaptive ordering without schema changes.
"""

from __future__ import annotations

import asyncio

from .db import health_summary, record_attempt
from .models import FanoutResult, ProviderReceipt, SearchHit, normalize_url

KIND_PRIORITY = ("fleet-local", "knowledge", "serp")


def merge_hits(per_provider: list[tuple[str, list[SearchHit]]]) -> list[SearchHit]:
    """Interleave by kind priority, dedupe by normalized URL. Pure (tested)."""
    buckets: dict[str, list[SearchHit]] = {}
    for provider_name, hits in per_provider:
        for h in hits:
            buckets.setdefault(h.kind or "serp", []).append(h)
    ordered: list[SearchHit] = []
    for kind in KIND_PRIORITY:
        ordered.extend(buckets.pop(kind, []))
    for rest in buckets.values():  # unknown kinds last, never dropped
        ordered.extend(rest)
    seen: set[str] = set()
    merged: list[SearchHit] = []
    for h in ordered:
        key = normalize_url(h.url)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(h)
    return merged


async def fanout(
    providers: list,
    query: str,
    limit: int = 10,
    kinds: tuple[str, ...] = ("fleet-local", "knowledge", "serp"),
    only: tuple[str, ...] = (),
    db_path=None,
    per_provider_limit: int = 10,
    time_filter: str = "any",
) -> FanoutResult:
    """Run selected providers concurrently, merge, record health, return all."""
    from .models import TIME_FILTERS

    filt = time_filter if time_filter in TIME_FILTERS else "any"
    selected = [p for p in providers if p.kind in kinds and (not only or p.name in only)]
    if not selected:
        return FanoutResult(query=query)

    async def run(p) -> tuple[str, list[SearchHit], ProviderReceipt]:
        try:
            hits, receipt = await p.search(query, per_provider_limit, time_filter=filt)
            return p.name, list(hits or []), receipt
        except Exception as e:  # provider bugs must not sink the fan-out
            return (
                p.name,
                [],
                ProviderReceipt(
                    provider=p.name,
                    kind=getattr(p, "kind", "?"),
                    ok=False,
                    error=f"provider crashed: {e}",
                ),
            )

    settled = await asyncio.gather(*[run(p) for p in selected])
    per_provider = [(name, hits) for name, hits, _ in settled]
    receipts = [r for _, _, r in settled]
    if db_path is not None:
        for r in receipts:
            record_attempt(
                db_path,
                provider=r.provider,
                kind=r.kind,
                ok=r.ok,
                latency_ms=r.latency_ms,
                count=r.count,
                blocked=r.blocked,
            )
    merged = merge_hits(per_provider)[: max(limit, 1)]
    return FanoutResult(query=query, hits=merged, receipts=receipts)


def health(db_path, window_hours: int = 24) -> list[dict]:
    """Read the rolling provider scoreboard (empty list when no data yet)."""
    return health_summary(db_path, window_hours=window_hours)
