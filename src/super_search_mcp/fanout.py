"""Fan-out engine: parallel providers, kind-priority merge, receipts.

Ordering philosophy: relevance first, then fleet-local (private, free,
instant), curated knowledge, and the whole web (broad, billed, flaky). Hits
are ranked by a cheap literal relevance score (relevance.py); kind order breaks
ties. Providers whose every hit is unrelated to the query are reported as
fault kind "unrelated" and their hits are dropped (2026-10-11: soft-blocked
Bing and a broken upstream search topped results with junk while ok).
"""

from __future__ import annotations

import asyncio

from .db import health_summary, record_attempt
from .models import FanoutResult, ProviderReceipt, SearchHit, normalize_url
from .relevance import SEMANTIC_PROVIDERS, hit_score, provider_passes, query_terms

KIND_PRIORITY = ("fleet-local", "knowledge", "serp")
KIND_LABEL = {"fleet-local": "Fleet-local", "knowledge": "Knowledge", "serp": "Web"}


def _short(r: ProviderReceipt) -> str:
    """Compact per-provider status: 'name ok(n)' or 'name fault_kind'."""
    if r.ok:
        via = f" via {r.via} after block" if r.via else ""
        return f"{r.provider} ok({r.count}){via}"
    return f"{r.provider} {r.fault_kind or 'failed'}"


def build_coverage(receipts: list[ProviderReceipt]) -> str:
    """One honest line: what was searched, what failed and why. Pure (tested).

    Example: "Fleet-local: arxiv-mcp ok(3), arxiv-depot ok(0). Knowledge:
    wikipedia ok(5). Web: duckduckgo ok(10); openserp-local down; tavily
    unconfigured." Absence of this line is itself a defect (standard
    EXTERNAL_FAULT_TRANSPARENCY.md).
    """
    by_kind: dict[str, list[ProviderReceipt]] = {}
    for r in receipts or []:
        by_kind.setdefault(r.kind or "?", []).append(r)
    groups: list[str] = []
    for kind in KIND_PRIORITY:
        parts = [_short(r) for r in by_kind.pop(kind, [])]
        if parts:
            groups.append(f"{KIND_LABEL[kind]}: {', '.join(parts)}")
    for kind, rest in by_kind.items():  # unknown kinds last, never dropped
        groups.append(f"{kind}: {', '.join(_short(r) for r in rest)}")
    return ". ".join(groups) + ("." if groups else "")


def merge_hits(per_provider: list[tuple[str, list[SearchHit]]], query: str = "") -> list[SearchHit]:
    """Rank by relevance, then kind priority; dedupe by normalized URL. Pure (tested).

    Without a query (or with only stopwords) every score is equal and the
    order is plain kind priority. Hits from semantic providers count as at
    least "related", since they need not share words with the query.
    """
    buckets: dict[str, list[SearchHit]] = {}
    for provider_name, hits in per_provider:
        for h in hits:
            buckets.setdefault(h.kind or "serp", []).append(h)
    by_kind: list[SearchHit] = []
    for kind in KIND_PRIORITY:
        by_kind.extend(buckets.pop(kind, []))
    for rest in buckets.values():  # unknown kinds last, never dropped
        by_kind.extend(rest)
    terms = query_terms(query)

    def score(h: SearchHit) -> int:
        s = hit_score(terms, h)
        return max(s, 1) if h.provider in SEMANTIC_PROVIDERS else s

    # sorted() is stable: equal scores keep the kind-priority order above.
    ordered = sorted(by_kind, key=lambda h: -score(h)) if terms else by_kind
    seen: set[str] = set()
    merged: list[SearchHit] = []
    for h in ordered:
        key = normalize_url(h.url)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(h)
    return merged


def _check_relevance(
    query: str, name: str, hits: list[SearchHit], receipt: ProviderReceipt
) -> tuple[str, list[SearchHit], ProviderReceipt]:
    """Turn an ok receipt whose hits are all unrelated into fault kind "unrelated".

    The hits are dropped so junk never reaches the merged list; the receipt
    keeps count = what the provider returned, so the numbers stay honest.
    """
    if not receipt.ok or not hits or name in SEMANTIC_PROVIDERS:
        return name, hits, receipt
    if provider_passes(query, hits):
        return name, hits, receipt
    receipt.ok = False
    receipt.fault_kind = "unrelated"
    receipt.error = f"relevance check: none of {len(hits)} hits mention the query"
    receipt.user_message = (
        f"{name} answered with results unrelated to your query - ignored "
        "(likely a soft block or an upstream search problem, not your query)."
    )
    receipt.what_to_do = "Nothing to do; results from the other providers are shown."
    return name, [], receipt


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
        return FanoutResult(
            query=query,
            coverage="No providers selected (check kinds/providers filters) - "
            "nothing was searched.",
        )

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
                    fault_kind="bug",
                    user_message=f"{p.name} crashed - our bug, not your query.",
                    what_to_do="Reported in logs; other providers continued.",
                ),
            )

    settled = await asyncio.gather(*[run(p) for p in selected])
    settled = [_check_relevance(query, name, hits, r) for name, hits, r in settled]
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
    merged = merge_hits(per_provider, query)[: max(limit, 1)]
    return FanoutResult(
        query=query, hits=merged, receipts=receipts, coverage=build_coverage(receipts)
    )


def health(db_path, window_hours: int = 24) -> list[dict]:
    """Read the rolling provider scoreboard (empty list when no data yet)."""
    return health_summary(db_path, window_hours=window_hours)
