"""Model contract tests: shapes, serialization, URL normalization."""

from super_search_mcp.models import (
    FanoutResult,
    ProviderReceipt,
    SearchHit,
    normalize_url,
)


def test_normalize_url() -> None:
    assert normalize_url("https://Example.com/Path/#frag") == "https://example.com/path"
    assert normalize_url("https://example.com") == "https://example.com"
    assert normalize_url("") == ""


def test_hit_and_receipt_serialize() -> None:
    hit = SearchHit(title="T", url="https://x.test", provider="p", kind="serp")
    d = hit.to_dict()
    assert d["title"] == "T" and d["provider"] == "p"
    r = ProviderReceipt(provider="p", kind="serp", ok=True, count=3)
    assert r.to_dict()["count"] == 3


def test_fanout_result_shape() -> None:
    fr = FanoutResult(query="q")
    d = fr.to_dict()
    assert d["query"] == "q" and d["total"] == 0 and d["hits"] == [] and d["receipts"] == []
