"""Breaker chain tests: engine choice, FlareSolverr leg, all-miss behavior.

Fake HTTP clients (same pattern as test_providers.py) - no network, no
browser, no sidecar. Env is monkeypatched per test; live env never leaks in.
"""

from __future__ import annotations

from super_search_mcp import breakers


def _triples(html: str) -> list[tuple[str, str, str]]:
    return [("t", "https://a.test/", "s")] if "HIT" in html else []


class _Resp:
    def __init__(self, status: int = 200, data: dict | None = None) -> None:
        self.status_code = status
        self._data = data or {}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._data


def _fake_client(posts: list, handler) -> type:
    class _Client:
        def __init__(self, *a: object, **k: object) -> None:
            return None

        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *a: object) -> bool:
            return False

        async def post(self, url: str, json: dict) -> _Resp:
            posts.append((url, json))
            return handler(url, json)

    return _Client


async def test_browser_leg_rescue_reports_engine(monkeypatch) -> None:
    posts: list = []
    breakers._client = _fake_client(  # type: ignore[assignment]
        posts, lambda url, js: _Resp(200, {"success": True, "html": "HIT"})
    )
    try:
        hits, via = await breakers.run_breakers(
            "http://x.test/", _triples, "ddg", "serp", limit=5, timeout_s=20.0
        )
    finally:
        from super_search_mcp.providers import base

        breakers._client = base._client  # type: ignore[assignment]
    assert len(hits) == 1 and hits[0].url == "https://a.test/"
    assert via == "camoufox" and posts[0][1]["engine"] == "camoufox"


async def test_engine_env_passes_through_to_bridge(monkeypatch) -> None:
    monkeypatch.setenv("BROWSER_MCP_ENGINE", "playwright")
    posts: list = []
    breakers._client = _fake_client(  # type: ignore[assignment]
        posts, lambda url, js: _Resp(200, {"success": True, "html": "HIT"})
    )
    try:
        _, via = await breakers.run_breakers("http://x.test/", _triples, "ddg", "serp")
    finally:
        from super_search_mcp.providers import base

        breakers._client = base._client  # type: ignore[assignment]
    assert via == "playwright" and posts[0][1]["engine"] == "playwright"


async def test_unknown_engine_falls_back_to_camoufox(monkeypatch) -> None:
    monkeypatch.setenv("BROWSER_MCP_ENGINE", "selenium")
    assert breakers.breaker_engine() == "camoufox"


async def test_flaresolverr_leg_fires_after_browser_miss(monkeypatch) -> None:
    monkeypatch.setenv("FLARESOLVERR_URL", "http://127.0.0.1:8191/v1")
    posts: list = []

    def _handler(url: str, js: dict) -> _Resp:
        if "8191" in url:
            assert js["cmd"] == "request.get"
            return _Resp(200, {"status": "ok", "solution": {"response": "HIT"}})
        return _Resp(200, {"success": False})

    breakers._client = _fake_client(posts, _handler)  # type: ignore[assignment]
    try:
        hits, via = await breakers.run_breakers("http://x.test/", _triples, "ddg", "serp")
    finally:
        from super_search_mcp.providers import base

        breakers._client = base._client  # type: ignore[assignment]
    assert len(hits) == 1 and via == "flaresolverr"
    assert len(posts) == 2


async def test_flaresolverr_disarmed_by_default(monkeypatch) -> None:
    monkeypatch.delenv("FLARESOLVERR_URL", raising=False)
    posts: list = []
    breakers._client = _fake_client(  # type: ignore[assignment]
        posts, lambda url, js: _Resp(200, {"success": False})
    )
    try:
        hits, via = await breakers.run_breakers("http://x.test/", _triples, "ddg", "serp")
    finally:
        from super_search_mcp.providers import base

        breakers._client = base._client  # type: ignore[assignment]
    assert hits == [] and via == "" and len(posts) == 1


async def test_all_legs_miss_returns_empty_via(monkeypatch) -> None:
    monkeypatch.setenv("FLARESOLVERR_URL", "http://127.0.0.1:8191/v1")
    breakers._client = _fake_client(  # type: ignore[assignment]
        [], lambda url, js: _Resp(200, {"success": False})
    )
    try:
        hits, via = await breakers.run_breakers("http://x.test/", _triples, "ddg", "serp")
    finally:
        from super_search_mcp.providers import base

        breakers._client = base._client  # type: ignore[assignment]
    assert hits == [] and via == ""


def test_breaker_legs_listing(monkeypatch) -> None:
    monkeypatch.delenv("FLARESOLVERR_URL", raising=False)
    assert breakers.breaker_legs() == ["browser"]
    monkeypatch.setenv("FLARESOLVERR_URL", "http://127.0.0.1:8191/v1")
    assert breakers.breaker_legs() == ["browser", "flaresolverr"]
