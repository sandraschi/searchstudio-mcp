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
