"""Settings preferences: browser fallback switch (file + env precedence + API)."""

import dataclasses

import pytest

from super_search_mcp import config as C


def test_fallback_defaults_on(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("BROWSER_MCP_URL", raising=False)
    assert C.browser_fallback_allowed(str(tmp_path)) == (True, "default")


def test_fallback_file_choice_wins_over_default(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("BROWSER_MCP_URL", raising=False)
    C.save_pref(str(tmp_path), "browser_fallback", False)
    assert C.browser_fallback_allowed(str(tmp_path)) == (False, "file")
    C.save_pref(str(tmp_path), "browser_fallback", True)
    assert C.browser_fallback_allowed(str(tmp_path)) == (True, "file")


def test_empty_env_is_hard_off(monkeypatch, tmp_path) -> None:
    C.save_pref(str(tmp_path), "browser_fallback", True)
    monkeypatch.setenv("BROWSER_MCP_URL", "  ")
    assert C.browser_fallback_allowed(str(tmp_path)) == (False, "env")


def test_save_pref_rejects_bad_input(tmp_path) -> None:
    with pytest.raises(ValueError):
        C.save_pref(str(tmp_path), "evil", True)
    with pytest.raises(ValueError):
        C.save_pref(str(tmp_path), "browser_fallback", "yes")


def test_corrupt_prefs_read_empty(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("BROWSER_MCP_URL", raising=False)
    C.prefs_file_path(str(tmp_path)).write_text("{not json", encoding="utf-8")
    assert C.load_prefs(str(tmp_path)) == {}
    assert C.browser_fallback_allowed(str(tmp_path)) == (True, "default")


def test_fallback_endpoints(monkeypatch, tmp_path) -> None:
    from starlette.testclient import TestClient

    from super_search_mcp import backend

    monkeypatch.delenv("BROWSER_MCP_URL", raising=False)
    monkeypatch.setattr(
        backend, "settings", dataclasses.replace(backend.settings, data_dir=str(tmp_path))
    )
    client = TestClient(backend.build_app(), raise_server_exceptions=False)
    r = client.get("/api/settings/fallbacks")
    assert r.status_code == 200
    assert r.json()["browser_fallback"] is True and r.json()["source"] == "default"
    r = client.post("/api/settings/fallbacks", json={"browser_fallback": False})
    assert r.status_code == 200
    assert r.json()["browser_fallback"] is False and r.json()["source"] == "file"
    assert C.load_prefs(str(tmp_path)) == {"browser_fallback": False}
    r = client.post("/api/settings/fallbacks", json={"browser_fallback": "nope"})
    assert r.status_code == 400
    monkeypatch.setenv("BROWSER_MCP_URL", "")
    r = client.post("/api/settings/fallbacks", json={"browser_fallback": True})
    assert r.json()["browser_fallback"] is False and r.json()["source"] == "env"
