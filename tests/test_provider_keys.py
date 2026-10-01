"""Provider key store tests: env-wins resolution, validation, endpoints."""

from super_search_mcp import config as C
from super_search_mcp.config import Settings


def test_resolve_prefers_env(tmp_path, monkeypatch) -> None:
    C.save_file_key(str(tmp_path), "TAVILY_API_KEY", "tvly-file")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-env")
    key, source = C.resolve_key(_settings_at(str(tmp_path)), "TAVILY_API_KEY")
    assert (key, source) == ("tvly-env", "env")


def _settings_at(data_dir: str) -> Settings:
    s = Settings()
    s.__dict__["data_dir"] = data_dir
    return s


def test_resolve_falls_back_to_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    C.save_file_key(str(tmp_path), "TAVILY_API_KEY", "tvly-file")
    key, source = C.resolve_key(_settings_at(str(tmp_path)), "TAVILY_API_KEY")
    assert (key, source) == ("tvly-file", "file")


def test_resolve_unset(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    key, source = C.resolve_key(_settings_at(str(tmp_path)), "EXA_API_KEY")
    assert (key, source) == ("", "unset")


def test_save_rejects_unmanaged_name(tmp_path) -> None:
    import pytest

    with pytest.raises(ValueError):
        C.save_file_key(str(tmp_path), "EVIL_VAR", "x")
    with pytest.raises(ValueError):
        C.save_file_key(str(tmp_path), "TAVILY_API_KEY", "")


def test_save_delete_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    s = _settings_at(str(tmp_path))
    assert C.resolve_key(s, "BRAVE_API_KEY") == ("", "unset")
    C.save_file_key(str(tmp_path), "BRAVE_API_KEY", "brv-123")
    assert C.resolve_key(s, "BRAVE_API_KEY") == ("brv-123", "file")
    assert C.delete_file_key(str(tmp_path), "BRAVE_API_KEY") is True
    assert C.resolve_key(s, "BRAVE_API_KEY") == ("", "unset")
    assert C.delete_file_key(str(tmp_path), "BRAVE_API_KEY") is False


def test_corrupt_file_reads_empty(tmp_path) -> None:
    C.key_file_path(str(tmp_path)).parent.mkdir(parents=True, exist_ok=True)
    C.key_file_path(str(tmp_path)).write_text("{not json", encoding="utf-8")
    assert C.load_file_keys(str(tmp_path)) == {}


def test_endpoints_validate() -> None:
    from starlette.testclient import TestClient

    from super_search_mcp.backend import build_app

    client = TestClient(build_app(), raise_server_exceptions=False)
    r = client.get("/api/provider-keys")
    assert r.status_code == 200
    names = {k["name"] for k in r.json()["keys"]}
    assert {"TAVILY_API_KEY", "EXA_API_KEY", "BRAVE_API_KEY"} <= names
    assert all("key" not in k or k["key"] == "" for k in r.json()["keys"])
    r = client.post("/api/provider-keys", json={"name": "EVIL", "key": "x"})
    assert r.status_code == 400
    r = client.post("/api/provider-keys", json={"name": "TAVILY_API_KEY", "key": ""})
    assert r.status_code == 400
    r = client.delete("/api/provider-keys", params={"name": "EVIL"})
    assert r.status_code == 400
