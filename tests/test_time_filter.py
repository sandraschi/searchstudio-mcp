"""WP2 tests: time_filter reaches supporting providers; others declare unapplied.

All network is mocked via httpx.MockTransport. No live calls in CI.
"""

import json

import httpx

from super_search_mcp.providers import arxiv_local, ddg, exa, openserp, tavily, wikipedia


def _client_with(handler, calls: list):
    def make(timeout_s: float = 20.0, user_agent: str = "x"):
        def wrapped(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return handler(request)

        return httpx.AsyncClient(transport=httpx.MockTransport(wrapped))

    return make


def _json_response(payload: dict) -> httpx.Response:
    return httpx.Response(
        200,
        content=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )


async def test_tavily_sends_time_range(monkeypatch) -> None:
    calls: list = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        assert body["time_range"] == "week"
        return _json_response({"results": []})

    monkeypatch.setattr(tavily, "_client", _client_with(handler, calls))
    p = tavily.TavilyProvider(api_key="tvly-test")
    hits, receipt = await p.search("news", limit=5, time_filter="week")
    assert hits == [] and receipt.ok is True
    assert receipt.time_filter_applied is True
    assert len(calls) == 1


async def test_tavily_omits_time_range_on_any(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        assert "time_range" not in body
        return _json_response({"results": []})

    monkeypatch.setattr(tavily, "_client", _client_with(handler, []))
    p = tavily.TavilyProvider(api_key="tvly-test")
    _, receipt = await p.search("news", time_filter="any")
    assert receipt.time_filter_applied is False


async def test_arxiv_sends_hours(monkeypatch) -> None:
    calls: list = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert "hours=168" in str(request.url)
        return _json_response({"merged": []})

    monkeypatch.setattr(arxiv_local, "_client", _client_with(handler, calls))
    p = arxiv_local.ArxivMcpProvider(base_url="http://127.0.0.1:10770")
    _, receipt = await p.search("test", time_filter="week")
    assert receipt.ok is True and receipt.time_filter_applied is True


async def test_arxiv_omits_hours_on_any(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "hours" not in str(request.url)
        return _json_response({"merged": []})

    monkeypatch.setattr(arxiv_local, "_client", _client_with(handler, []))
    p = arxiv_local.ArxivMcpProvider(base_url="http://127.0.0.1:10770")
    _, receipt = await p.search("test", time_filter="any")
    assert receipt.time_filter_applied is False


async def test_openserp_appends_after_operator(monkeypatch) -> None:
    calls: list = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert "after" in str(request.url)
        return _json_response(
            {"results": [{"title": "T", "url": "https://t.test", "snippet": "s"}]}
        )

    monkeypatch.setattr(openserp, "_client", _client_with(handler, calls))
    p = openserp.OpenSerpProvider(base_url="http://127.0.0.1:7000")
    hits, receipt = await p.search("news", time_filter="month")
    assert len(hits) == 1 and receipt.time_filter_applied is True


async def test_ddg_reports_unapplied(monkeypatch) -> None:
    body = (
        '<a rel="nofollow" class="result-link" '
        'href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fa.test%2F">A</a>'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=body)

    monkeypatch.setattr(ddg, "_client", _client_with(handler, []))
    p = ddg.DuckDuckGoProvider()
    hits, receipt = await p.search("test", time_filter="week")
    assert len(hits) == 1 and receipt.ok is True
    assert receipt.time_filter_applied is False


async def test_wikipedia_reports_unapplied(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(
            {"query": {"pages": {"1": {"title": "T", "fullurl": "https://w.test", "extract": "e"}}}}
        )

    monkeypatch.setattr(wikipedia, "_client", _client_with(handler, []))
    p = wikipedia.WikipediaProvider()
    hits, receipt = await p.search("test", time_filter="day")
    assert len(hits) == 1 and receipt.time_filter_applied is False


async def test_exa_sends_start_published_date(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        assert "startPublishedDate" in body
        assert request.headers["x-api-key"] == "exa-test"
        return _json_response({"results": []})

    monkeypatch.setattr(exa, "_client", _client_with(handler, []))
    p = exa.ExaProvider(api_key="exa-test")
    _, receipt = await p.search("news", time_filter="week")
    assert receipt.ok is True and receipt.time_filter_applied is True


async def test_exa_omits_date_on_any(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        assert "startPublishedDate" not in body
        return _json_response({"results": []})

    monkeypatch.setattr(exa, "_client", _client_with(handler, []))
    p = exa.ExaProvider(api_key="exa-test")
    _, receipt = await p.search("news", time_filter="any")
    assert receipt.time_filter_applied is False
