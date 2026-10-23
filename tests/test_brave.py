"""Brave provider tests: stub without key, response mapping. No network."""

from __future__ import annotations

from super_search_mcp.providers.brave import BraveProvider, map_response


def test_brave_stub_without_key() -> None:
    assert BraveProvider(api_key="").configured is False


async def test_brave_stub_async() -> None:
    p = BraveProvider(api_key="")
    hits, receipt = await p.search("anything")
    assert hits == [] and receipt.ok is False and receipt.configured is False


def test_brave_maps_response() -> None:
    data = {
        "query": {"original": "q"},
        "web": {
            "results": [
                {
                    "title": "T",
                    "url": "https://b.test",
                    "description": "D" * 600,
                    "age": "2 days ago",
                },
                {"title": "x"},
            ]
        },
    }
    out = map_response(data)
    assert len(out) == 1 and len(out[0].snippet) == 500
    assert out[0].published == "2 days ago"
    assert out[0].provider == "brave" and out[0].kind == "serp"


def test_brave_maps_empty_without_web() -> None:
    assert map_response({}) == []
    assert map_response({"web": {}}) == []
