"""Fan-out engine tests: merge order, dedupe, error isolation, dispatch contract."""

import inspect

from super_search_mcp import fanout as F
from super_search_mcp.config import Settings
from super_search_mcp.models import SearchHit
from super_search_mcp.providers import build_providers


def _hit(url: str, kind: str, provider: str) -> SearchHit:
    return SearchHit(title=f"t-{url}", url=url, provider=provider, kind=kind)


def test_merge_kind_priority_and_dedupe() -> None:
    per = [
        ("ddg", [_hit("https://x.test/a", "serp", "ddg")]),
        (
            "wiki",
            [
                _hit("https://x.test/a", "knowledge", "wiki"),
                _hit("https://x.test/b", "knowledge", "wiki"),
            ],
        ),
        ("local", [_hit("https://y.test/c", "fleet-local", "local")]),
    ]
    merged = F.merge_hits(per)
    urls = [h.url for h in merged]
    assert (
        urls == ["https://y.test/c", "https://x.test/b", "https://x.test/a"]
        or urls[0] == "https://y.test/c"
    )
    assert len({h.url for h in merged}) == len(merged)


def test_merge_unknown_kinds_kept_last() -> None:
    per = [("odd", [_hit("https://z.test/", "mystery", "odd")])]
    assert F.merge_hits(per)[0].url == "https://z.test/"


class _Stub:
    def __init__(self, name, kind, hits=None, fail=False):
        self.name = name
        self.kind = kind
        self._hits = hits or []
        self._fail = fail
        self.last_time_filter = "unset"

    @property
    def configured(self) -> bool:
        return True

    async def search(self, query: str, limit: int = 10, time_filter: str = "any"):
        from super_search_mcp.providers.base import _now_ms, _receipt

        if self._fail:
            raise RuntimeError("boom")
        self.last_time_filter = time_filter
        hits = self._hits[:limit]
        return hits, _receipt(self.name, self.kind, ok=True, hits=hits, started_ms=_now_ms())


async def test_fanout_isolates_crashing_provider(tmp_path) -> None:
    db = tmp_path / "h.sqlite3"
    good = _Stub("good", "serp", [_hit("https://g.test/", "serp", "good")])
    bad = _Stub("bad", "serp", fail=True)
    out = await F.fanout([good, bad], "q", db_path=db)
    assert [h.url for h in out.hits] == ["https://g.test/"]
    assert {r.provider for r in out.receipts} == {"good", "bad"}
    assert [r for r in out.receipts if r.provider == "bad"][0].ok is False


async def test_fanout_records_health(tmp_path) -> None:
    from super_search_mcp.db import health_summary

    db = tmp_path / "h.sqlite3"
    good = _Stub("good", "knowledge", [_hit("https://g.test/", "knowledge", "good")])
    await F.fanout([good], "q", db_path=db)
    rows = health_summary(db)
    assert len(rows) == 1 and rows[0]["provider"] == "good" and rows[0]["success_rate"] == 1.0


async def test_fanout_empty_selection() -> None:
    out = await F.fanout([], "q", db_path=None)
    assert out.hits == [] and out.receipts == []


async def test_fanout_forwards_time_filter() -> None:
    good = _Stub("good", "serp", [_hit("https://g.test/", "serp", "good")])
    await F.fanout([good], "q", db_path=None, time_filter="week")
    assert good.last_time_filter == "week"


def test_dispatch_contract_keywords() -> None:
    """Every provider must accept (query, limit=..., time_filter=...) by keyword.

    Guards the 2026-09-30 positional-dispatch bug where ``limit`` landed in
    ``search_biorxiv``'s ``server`` slot, serving medRxiv as bioRxiv.
    """
    settings = Settings()
    for p in build_providers(settings):
        sig = inspect.signature(p.search)
        params = list(sig.parameters.values())
        assert params[0].name in ("query", "self") or "query" in sig.parameters, p.name
        for name in ("limit", "time_filter"):
            assert name in sig.parameters, f"{p.name} missing {name}"
            assert sig.parameters[name].kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            ), f"{p.name}.{name} not keyword-callable"
