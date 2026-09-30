"""Provider unit tests: pure mappers offline; network never touched in CI."""

from super_search_mcp.providers.arxiv_local import map_papers
from super_search_mcp.providers.ddg import _real_url, parse_lite_html
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
