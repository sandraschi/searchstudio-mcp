"""Provider unit tests: pure mappers offline; network never touched in CI."""

from super_search_mcp.providers.arxiv_depot import (
    clean_snippet,
)
from super_search_mcp.providers.arxiv_depot import (
    map_hits as map_depot_hits,
)
from super_search_mcp.providers.arxiv_local import map_papers
from super_search_mcp.providers.ddg import _real_url, parse_lite_html
from super_search_mcp.providers.exa import ExaProvider
from super_search_mcp.providers.exa import map_response as map_exa_response
from super_search_mcp.providers.openserp import map_results
from super_search_mcp.providers.tavily import TavilyProvider, map_response
from super_search_mcp.providers.wikipedia import map_pages


def test_ddg_unwraps_redirects() -> None:
    href = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage&rut=abc"
    assert _real_url(href) == "https://example.com/page"
    assert _real_url("https://example.com/x") == "https://example.com/x"


def test_ddg_parses_lite_markup() -> None:
    link = (
        '<a rel="nofollow" class="result-link" '
        'href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fa.test%2F">A Title</a>'
    )
    body = link + '<td class="result-snippet">A snippet.</td>'
    out = parse_lite_html(body)
    assert out == [("A Title", "https://a.test/", "A snippet.")]
    assert parse_lite_html("<html>nothing</html>") == []


def test_ddg_parses_live_single_quote_href_first() -> None:
    # Live lite.duckduckgo.com 2026-10-01: href-before-class, single quotes.
    link = (
        '<a rel="nofollow" '
        '"//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.hollabrunn.gv.at%2F&rut=abc" '
        "class='result-link'>Stadtgemeinde Hollabrunn</a>"
    )
    link = link.replace('"//duckduckgo', 'href="//duckduckgo')
    body = link + "<td class='result-snippet'>Offizielle Seite.</td>"
    out = parse_lite_html(body)
    assert out == [
        (
            "Stadtgemeinde Hollabrunn",
            "https://www.hollabrunn.gv.at/",
            "Offizielle Seite.",
        )
    ]


def test_ddg_skips_more_info_boilerplate() -> None:
    body = (
        '<a rel="nofollow" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fa.test%2F" '
        "class='result-link'>A Title</a>"
        "<td class='result-snippet'>A snippet.</td>"
        '<a rel="nofollow" href="https://duckduckgo.com/help-pages/" '
        'rel="nofollow" class="result-link">more info</a>'
    )
    out = parse_lite_html(body)
    assert out == [("A Title", "https://a.test/", "A snippet.")]


def test_wikipedia_maps_pages() -> None:
    pages = {
        "1": {
            "title": "Hollabrunn",
            "fullurl": "https://en.wikipedia.org/wiki/Hollabrunn",
            "extract": "A town in Austria.",
        },
        "2": {"title": "No URL"},
    }
    out = map_pages(pages)
    assert len(out) == 1 and out[0].title == "Hollabrunn" and out[0].provider == "wikipedia"


def test_arxiv_maps_merged() -> None:
    papers = [
        {
            "paper_id": "1706.03762",
            "title": "Attention",
            "summary": "S",
            "authors": ["A", "B"],
            "published": "2017-06-12",
            "html_url": "https://arxiv.org/abs/1706.03762",
        },
        {"paper_id": "", "title": "", "html_url": ""},
    ]
    out = map_papers(papers)
    assert len(out) == 1 and out[0].url.endswith("/abs/1706.03762")


async def test_arxiv_surfaces_backend_errors() -> None:
    from super_search_mcp.providers import arxiv_local
    from super_search_mcp.providers.arxiv_local import ArxivMcpProvider

    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "merged": [],
                "errors": {"arxiv_timeout": "arXiv API exceeded 10s; retry shortly"},
            }

    class _Client:
        def __init__(self, *a: object, **k: object) -> None:
            return None

        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *a: object) -> bool:
            return False

        async def get(self, url: str) -> _Resp:
            return _Resp()

    real = arxiv_local._client
    arxiv_local._client = _Client  # type: ignore[assignment]
    try:
        hits, receipt = await ArxivMcpProvider("http://127.0.0.1:1").search("x")
    finally:
        arxiv_local._client = real
    assert hits == [] and receipt.ok is False and "arxiv_timeout" in receipt.error
    assert receipt.fault_kind == "rate_limited"
    assert receipt.retry_in == "~5 minutes"
    assert "Wait" in receipt.what_to_do


async def test_arxiv_prefers_structured_faults() -> None:
    from super_search_mcp.providers import arxiv_local
    from super_search_mcp.providers.arxiv_local import ArxivMcpProvider

    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "merged": [],
                "errors": {"arxiv_timeout": "backend words"},
                "faults": [
                    {
                        "service": "arXiv API",
                        "kind": "rate_limited",
                        "our_fault": False,
                        "retry_in": "~5 minutes",
                        "user_message": "structured words",
                        "what_to_do": "structured todo",
                    }
                ],
            }

    class _Client:
        def __init__(self, *a: object, **k: object) -> None:
            return None

        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *a: object) -> bool:
            return False

        async def get(self, url: str) -> _Resp:
            return _Resp()

    real = arxiv_local._client
    arxiv_local._client = _Client  # type: ignore[assignment]
    try:
        hits, receipt = await ArxivMcpProvider("http://127.0.0.1:1").search("x")
    finally:
        arxiv_local._client = real
    assert hits == [] and receipt.ok is False
    assert receipt.fault_kind == "rate_limited"
    assert receipt.user_message == "structured words"
    assert receipt.what_to_do == "structured todo"


def test_coverage_line_summarizes_mixed_outcomes() -> None:
    from super_search_mcp.fanout import build_coverage
    from super_search_mcp.models import ProviderReceipt

    receipts = [
        ProviderReceipt(provider="arxiv-mcp", kind="fleet-local", ok=True, count=3),
        ProviderReceipt(provider="arxiv-depot", kind="fleet-local", ok=True, count=0),
        ProviderReceipt(provider="wikipedia", kind="knowledge", ok=True, count=5),
        ProviderReceipt(provider="duckduckgo", kind="serp", ok=True, count=10),
        ProviderReceipt(
            provider="openserp-local",
            kind="serp",
            ok=False,
            fault_kind="down",
            error="ConnectError",
        ),
        ProviderReceipt(
            provider="tavily",
            kind="serp",
            ok=False,
            configured=False,
            fault_kind="unconfigured",
        ),
    ]
    line = build_coverage(receipts)
    assert "Fleet-local: arxiv-mcp ok(3), arxiv-depot ok(0)" in line
    assert "Knowledge: wikipedia ok(5)" in line
    assert "duckduckgo ok(10)" in line
    assert "openserp-local down" in line
    assert "tavily unconfigured" in line


def test_coverage_line_names_fallback_route() -> None:
    from super_search_mcp.fanout import build_coverage
    from super_search_mcp.models import ProviderReceipt

    receipts = [
        ProviderReceipt(
            provider="duckduckgo", kind="serp", ok=True, count=3, blocked=True, via="camoufox"
        )
    ]
    assert "duckduckgo ok(3) via camoufox after block" in build_coverage(receipts)


_LITE_HIT = (
    '<a rel="nofollow" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fa.test%2F" '
    "class='result-link'>A Title</a><td class='result-snippet'>Snip</td>"
)


async def _ddg_blocked_search(post_json: dict | None) -> tuple[list, object]:
    """DDG search where the direct GET hits a bot challenge; POST = browser-mcp."""
    from super_search_mcp.providers import ddg

    class _Resp:
        def __init__(self, status: int, text: str = "", data: dict | None = None) -> None:
            self.status_code = status
            self.text = text
            self._data = data or {}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._data

    class _Client:
        def __init__(self, *a: object, **k: object) -> None:
            return None

        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *a: object) -> bool:
            return False

        async def get(self, url: str) -> _Resp:
            return _Resp(200, text="<div class='anomaly-modal'>not a robot</div>")

        async def post(self, url: str, json: dict) -> _Resp:
            if post_json is None:
                raise AssertionError("fallback must not be called when disabled")
            assert json["engine"] == "camoufox"
            return _Resp(200, data=post_json)

    real = ddg._client
    ddg._client = _Client  # type: ignore[assignment]
    try:
        return await ddg.DuckDuckGoProvider().search("x")
    finally:
        ddg._client = real


async def test_ddg_camoufox_rescue_is_reported_not_hidden(monkeypatch) -> None:
    monkeypatch.setenv("BROWSER_MCP_URL", "http://127.0.0.1:1")
    hits, receipt = await _ddg_blocked_search({"success": True, "html": _LITE_HIT})
    assert len(hits) == 1 and hits[0].url == "https://a.test/"
    assert receipt.ok is True and receipt.count == 1
    assert receipt.blocked is True and receipt.via == "camoufox"
    assert receipt.fault_kind == "" and "Camoufox" in receipt.user_message


async def test_ddg_failed_fallback_keeps_blocked_receipt(monkeypatch) -> None:
    monkeypatch.setenv("BROWSER_MCP_URL", "http://127.0.0.1:1")
    hits, receipt = await _ddg_blocked_search({"success": False})
    assert hits == [] and receipt.ok is False
    assert receipt.blocked is True and receipt.fault_kind == "blocked"
    assert receipt.via == ""


async def test_ddg_fallback_disabled_by_empty_env(monkeypatch) -> None:
    monkeypatch.setenv("BROWSER_MCP_URL", "")
    hits, receipt = await _ddg_blocked_search(None)
    assert hits == [] and receipt.fault_kind == "blocked" and receipt.via == ""


async def test_crash_receipt_is_bug_kind() -> None:
    from super_search_mcp import fanout

    class _Boom:
        name = "boom"
        kind = "serp"

        async def search(self, query: str, limit: int = 10, time_filter: str = "any"):
            raise RuntimeError("kaput")

    res = await fanout.fanout([_Boom()], "q", limit=5)
    assert res.hits == [] and len(res.receipts) == 1
    r = res.receipts[0]
    assert r.ok is False and r.fault_kind == "bug"
    assert "boom" in res.coverage and "bug" in res.coverage


async def test_empty_selection_coverage_says_nothing_searched() -> None:
    from super_search_mcp import fanout

    res = await fanout.fanout([], "q")
    assert res.coverage.startswith("No providers selected")


def test_openserp_defensive_mapping() -> None:
    rows = [
        {"title": "T", "url": "https://u.test", "snippet": "s"},
        {"title": "T2", "link": "https://v.test", "description": "d"},
        {"nope": True},
        "junk",
    ]
    out = map_results(rows)
    assert [h.url for h in out] == ["https://u.test", "https://v.test"]


async def test_tavily_stub_async() -> None:
    p = TavilyProvider(api_key="")
    hits, receipt = await p.search("anything")
    assert hits == [] and receipt.ok is False and receipt.configured is False


def test_tavily_maps_response() -> None:
    data = {
        "results": [
            {"title": "T", "url": "https://t.test", "content": "C" * 600, "score": 0.9},
            {"title": "x"},
        ]
    }
    out = map_response(data)
    assert len(out) == 1 and len(out[0].snippet) == 500 and out[0].score == 0.9


def test_exa_stub_without_key() -> None:
    assert ExaProvider(api_key="").configured is False


async def test_exa_stub_async() -> None:
    p = ExaProvider(api_key="")
    hits, receipt = await p.search("anything")
    assert hits == [] and receipt.ok is False and receipt.configured is False


def test_exa_maps_response() -> None:
    data = {
        "results": [
            {
                "title": "T",
                "url": "https://e.test",
                "text": "C" * 600,
                "publishedDate": "2026-09-01",
                "score": 0.7,
            },
            {"title": "x"},
        ]
    }
    out = map_exa_response(data)
    assert len(out) == 1 and len(out[0].snippet) == 500
    assert out[0].published == "2026-09-01" and out[0].score == 0.7


def test_depot_cleans_marks() -> None:
    assert clean_snippet("a <mark>highlighted</mark> bit") == "a highlighted bit"


def test_depot_maps_records() -> None:
    recs = [
        {"arxiv_id": "1706.03762", "title": "Attention", "snippet": "x <mark>y</mark> z"},
        {"arxiv_id": "", "title": ""},
        "junk",
    ]
    out = map_depot_hits(recs)
    assert len(out) == 1
    assert out[0].url == "https://arxiv.org/abs/1706.03762"
    assert out[0].snippet == "x y z" and out[0].provider == "arxiv-depot"
