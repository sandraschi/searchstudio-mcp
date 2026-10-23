"""Goggles store + Brave wiring tests. No network (tmp data dir, fake HTTP)."""

from __future__ import annotations

from super_search_mcp import goggles as _g
from super_search_mcp.providers.brave import BraveProvider


def test_store_seeds_prepared(tmp_path) -> None:
    store = _g.load_store(str(tmp_path))
    names = [e["name"] for e in store["entries"]]
    assert len(names) >= 5 and all(e["enabled"] is False for e in store["entries"])
    assert all(e["url"] == "" for e in store["entries"])


def test_enable_without_url_refused(tmp_path) -> None:
    entry, err = _g.upsert_entry(str(tmp_path), "no-pinterest", enabled=True)
    assert entry is None and "public URL" in err


def test_enable_with_url_works(tmp_path) -> None:
    entry, err = _g.upsert_entry(
        str(tmp_path),
        "no-pinterest",
        url="https://raw.githubusercontent.com/x/y/main/no-pinterest.goggle",
        enabled=True,
    )
    assert err == "" and entry["enabled"] is True
    assert _g.enabled_goggle_urls(str(tmp_path)) == [entry["url"]]


def test_bad_url_rejected(tmp_path) -> None:
    entry, err = _g.upsert_entry(str(tmp_path), "mine", url="not-a-url")
    assert entry is None and "https://" in err


def test_builtin_cannot_be_deleted(tmp_path) -> None:
    ok, err = _g.delete_entry(str(tmp_path), "no-pinterest")
    assert ok is False and "cannot be deleted" in err


def test_custom_round_trip(tmp_path) -> None:
    entry, err = _g.upsert_entry(str(tmp_path), "mine", url="https://example.com/m.goggle")
    assert err == "" and entry["builtin"] is False
    ok, err = _g.delete_entry(str(tmp_path), "mine")
    assert ok is True and err == ""


class _Resp:
    def __init__(self, data: dict) -> None:
        self._data = data

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._data


async def test_brave_sends_goggles_and_reports_them(monkeypatch) -> None:
    from super_search_mcp.providers import brave as _b

    posts: list = []

    class _Client:
        def __init__(self, *a: object, **k: object) -> None:
            return None

        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *a: object) -> bool:
            return False

        async def post(self, url: str, json: dict) -> _Resp:
            posts.append((url, json))
            return _Resp({})

        async def get(self, url: str, params: dict = None, headers: dict = None) -> _Resp:
            posts.append((url, params))
            return _Resp({"web": {"results": []}})

    real = _b._client
    _b._client = _Client  # type: ignore[assignment]
    try:
        p = BraveProvider(api_key="k", goggles=["https://x.test/g.goggle"])
        hits, receipt = await p.search("q")
    finally:
        _b._client = real
    assert posts[0][1]["goggles"] == ["https://x.test/g.goggle"]
    assert receipt.ok is True and receipt.goggles_applied == ["https://x.test/g.goggle"]
    assert hits == []
