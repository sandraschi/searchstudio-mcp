"""Models.dev provider tests: pure mappers/filters offline; network never touched."""

from super_search_mcp.providers import modelsdev
from super_search_mcp.providers.modelsdev import (
    ModelsDevProvider,
    filter_models,
    format_snippet,
    load_catalog,
    map_rows,
    model_row,
    write_cache,
)

_FIXTURE = {
    "anthropic": {
        "name": "Anthropic",
        "doc": "https://docs.anthropic.com/",
        "models": {
            "claude-opus-4-6": {
                "name": "Claude Opus 4.6",
                "description": "Frontier coding model",
                "family": "claude",
                "tool_call": True,
                "reasoning": True,
                "structured_output": True,
                "limit": {"context": 200000, "output": 32000},
                "cost": {"input": 5.00, "output": 25.00},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "open_weights": False,
                "knowledge": "2025-11",
                "release_date": "2026-02-01",
            },
            "claude-cheap": {
                "name": "Claude Cheap",
                "description": "Budget model without tools",
                "tool_call": False,
                "limit": {"context": 1000000},
                "cost": {"input": 0.50, "output": 2.00},
                "modalities": {"input": ["text"], "output": ["text"]},
                "open_weights": False,
            },
        },
    },
    "openai": {
        "name": "OpenAI",
        "doc": "https://platform.openai.com/docs/models",
        "models": {
            "gpt-x": {
                "name": "GPT X",
                "description": "Open weights all-rounder",
                "tool_call": True,
                "limit": {"context": 400000},
                "cost": {"input": 3.00, "output": 12.00},
                "modalities": {"input": ["text"], "output": ["text"]},
                "open_weights": True,
            }
        },
    },
}


def test_iter_models_handles_both_shapes() -> None:
    assert len(modelsdev._iter_models(_FIXTURE)) == 3
    assert len(modelsdev._iter_models({"providers": _FIXTURE})) == 3
    assert modelsdev._iter_models({"junk": 1}) == []
    assert modelsdev._iter_models([1, 2]) == []


def test_model_row_defaults_missing_cost() -> None:
    row = model_row("p", {}, {"id": "m"})
    assert row["input_cost"] is None and row["context"] is None
    assert row["tool_call"] is False and row["doc_url"] == "https://models.dev/"


def test_filter_tool_call_and_context_sorted_by_price() -> None:
    rows = filter_models(_FIXTURE, needs_tool_call=True, min_context=200000)
    assert [r["model_id"] for r in rows] == ["gpt-x", "claude-opus-4-6"]
    assert all(r["tool_call"] and r["context"] >= 200000 for r in rows)


def test_filter_query_and_caps() -> None:
    rows = filter_models(_FIXTURE, query="claude")
    assert {r["model_id"] for r in rows} == {"claude-opus-4-6", "claude-cheap"}
    rows = filter_models(_FIXTURE, max_input_cost=1.0)
    assert [r["model_id"] for r in rows] == ["claude-cheap"]
    rows = filter_models(_FIXTURE, open_weights_only=True)
    assert [r["model_id"] for r in rows] == ["gpt-x"]


def test_format_snippet_and_map_rows() -> None:
    rows = filter_models(_FIXTURE, query="opus")
    assert len(rows) == 1
    snippet = format_snippet(rows[0])
    assert "$5.00" in snippet and "tool_call" in snippet and "ctx 200000" in snippet
    hits = map_rows(rows)
    assert len(hits) == 1
    assert hits[0].provider == "modelsdev" and hits[0].kind == "knowledge"
    assert "opus" in (hits[0].title + hits[0].snippet).lower()


async def test_provider_empty_query_needs_no_network() -> None:
    hits, receipt = await ModelsDevProvider(data_dir="no-such-dir").search("")
    assert hits == [] and receipt.ok is False


async def test_load_catalog_serves_fresh_cache_offline(tmp_path) -> None:
    write_cache(tmp_path, _FIXTURE)
    payload, meta = await load_catalog(tmp_path, catalog_url="http://127.0.0.1:1/")
    assert payload is not None and meta["stale"] is False
    assert len(modelsdev._iter_models(payload)) == 3


async def test_load_catalog_reports_down_without_cache() -> None:
    hits, receipt = await ModelsDevProvider(
        data_dir="no-such-dir", catalog_url="http://127.0.0.1:1/"
    ).search("claude")
    assert hits == [] and receipt.ok is False and receipt.fault_kind == "down"


def test_registry_includes_modelsdev() -> None:
    from super_search_mcp.config import settings
    from super_search_mcp.providers import build_providers

    names = {p.name for p in build_providers(settings)}
    assert "modelsdev" in names


def test_config_defaults() -> None:
    from super_search_mcp.config import settings

    assert settings.modelsdev_catalog_url == "https://models.dev/catalog.json"
    assert settings.modelsdev_cache_hours == 24.0
