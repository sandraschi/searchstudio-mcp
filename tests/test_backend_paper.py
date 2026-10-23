"""Paper full-text proxy tests: validation, sibling failure, happy path, cap."""

from __future__ import annotations

import json
from types import SimpleNamespace

from super_search_mcp import backend as _backend


def _req(pid: str | None):
    params = {} if pid is None else {"paper_id": pid}
    return SimpleNamespace(query_params=params)


def _body(resp) -> dict:
    return json.loads(resp.body.decode())


async def test_full_text_requires_paper_id() -> None:
    resp = await _backend.api_paper_full_text(_req(""))
    assert resp.status_code == 400
    assert _body(resp)["success"] is False


async def test_full_text_reports_sibling_failure(monkeypatch) -> None:
    async def _boom(base: str, pid: str) -> str:
        raise RuntimeError("down")

    monkeypatch.setattr(_backend, "_sibling_full_text", _boom)
    resp = await _backend.api_paper_full_text(_req("1706.03762"))
    assert _body(resp) == {
        "success": False,
        "paper_id": "1706.03762",
        "error": "sibling full-text fetch failed: down",
    }


async def test_full_text_reports_empty_markdown(monkeypatch) -> None:
    async def _empty(base: str, pid: str) -> str:
        return ""

    monkeypatch.setattr(_backend, "_sibling_full_text", _empty)
    resp = await _backend.api_paper_full_text(_req("1706.03762"))
    body = _body(resp)
    assert body["success"] is False and "no text" in body["error"]


async def test_full_text_happy_path_and_cap(monkeypatch) -> None:
    async def _long(base: str, pid: str) -> str:
        return "x" * 100_005

    monkeypatch.setattr(_backend, "_sibling_full_text", _long)
    resp = await _backend.api_paper_full_text(_req("1706.03762"))
    body = _body(resp)
    assert body["success"] is True and body["truncated"] is True
    assert len(body["markdown"]) == 100_000
