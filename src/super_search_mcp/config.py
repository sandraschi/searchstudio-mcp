"""Configuration: env-driven, live-read, keyless-first.

Every provider works without credentials except Tavily/Exa/Brave, which
degrade to declared stubs (configured=False + setup hint) when unset.
Secrets live in env or the host config - never in this repo.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


# API keys the Settings page may store. Closed allowlist: the key API
# rejects anything else, so a compromised caller cannot plant arbitrary env.
MANAGED_KEY_NAMES = ("TAVILY_API_KEY", "EXA_API_KEY", "BRAVE_API_KEY")
KEY_FILE_NAME = "provider_keys.json"


def key_file_path(data_dir: str | Path) -> Path:
    return Path(data_dir) / KEY_FILE_NAME


def _is_stored_key(k: object, v: object) -> bool:
    return k in MANAGED_KEY_NAMES and isinstance(v, str) and bool(v.strip())


def load_file_keys(data_dir: str | Path) -> dict[str, str]:
    """Read UI-stored keys (gitignored). Corrupt file reads as empty, never crashes."""
    try:
        raw = key_file_path(data_dir).read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}
        return {k: v for k, v in data.items() if _is_stored_key(k, v)}
    except (OSError, ValueError):
        return {}


def save_file_key(data_dir: str | Path, name: str, key: str) -> None:
    """Persist one UI-entered key. Raises ValueError on bad name/empty key."""
    if name not in MANAGED_KEY_NAMES:
        raise ValueError(f"refusing to store unmanaged key name: {name}")
    key = (key or "").strip()
    if not key or len(key) > 500:
        raise ValueError("key must be 1..500 chars")
    path = key_file_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    stored = load_file_keys(data_dir)
    stored[name] = key
    path.write_text(json.dumps(stored, indent=2), encoding="utf-8")


def delete_file_key(data_dir: str | Path, name: str) -> bool:
    """Remove one UI-stored key. Returns True when something was removed."""
    if name not in MANAGED_KEY_NAMES:
        raise ValueError(f"refusing to delete unmanaged key name: {name}")
    path = key_file_path(data_dir)
    stored = load_file_keys(data_dir)
    if name not in stored:
        return False
    del stored[name]
    path.write_text(json.dumps(stored, indent=2), encoding="utf-8")
    return True


# Non-secret user preferences the Settings page may store. Closed allowlist,
# boolean values only.
PREFS_FILE_NAME = "preferences.json"
MANAGED_PREFS = ("browser_fallback",)


def prefs_file_path(data_dir: str | Path) -> Path:
    return Path(data_dir) / PREFS_FILE_NAME


def load_prefs(data_dir: str | Path) -> dict[str, bool]:
    """Read UI-stored preferences. Corrupt file reads as empty, never crashes."""
    try:
        data = json.loads(prefs_file_path(data_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k in MANAGED_PREFS and isinstance(v, bool)}


def save_pref(data_dir: str | Path, name: str, value: object) -> None:
    """Persist one preference. Raises ValueError on unknown name or non-bool value."""
    if name not in MANAGED_PREFS:
        raise ValueError(f"refusing to store unmanaged preference: {name}")
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be true or false")
    path = prefs_file_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    stored = load_prefs(data_dir)
    stored[name] = value
    path.write_text(json.dumps(stored, indent=2), encoding="utf-8")


def browser_fallback_allowed(data_dir: str | Path) -> tuple[bool, str]:
    """May a blocked provider retry through the Camoufox browser fallback?

    Returns (allowed, source). Precedence: BROWSER_MCP_URL explicitly set to
    empty = hard off for operators ("env"); else the Settings checkbox
    ("file"); else on ("default"). Live-read on every call, no restart.
    """
    env_val = os.environ.get("BROWSER_MCP_URL")
    if env_val is not None and not env_val.strip():
        return False, "env"
    stored = load_prefs(data_dir).get("browser_fallback")
    if stored is not None:
        return stored, "file"
    return True, "default"


def resolve_key(settings: Settings, name: str) -> tuple[str, str]:
    """Return (key, source) with env winning over the UI-stored file.

    Live-read on every call: keys entered in Settings take effect without
    a backend restart. Env explicitly set always wins (12-factor first).
    """
    env_val = os.environ.get(name, "").strip()
    if env_val:
        return env_val, "env"
    file_val = load_file_keys(settings.data_dir).get(name, "")
    if file_val:
        return file_val, "file"
    return "", "unset"


@dataclass(frozen=True)
class Settings:
    backend_port: int = int(_env("SUPER_SEARCH_BACKEND_PORT", "") or _env("PORT", "") or 11226)
    frontend_port: int = int(_env("SUPER_SEARCH_FRONTEND_PORT", "") or 11225)
    data_dir: str = _env("SUPER_SEARCH_DATA_DIR", "") or "data"
    openserp_base_url: str = _env("OPENSERP_BASE_URL", "") or "http://127.0.0.1:7000"
    arxiv_mcp_base_url: str = _env("ARXIV_MCP_BASE_URL", "") or "http://127.0.0.1:10770"
    tavily_api_key: str = field(default_factory=lambda: _env("TAVILY_API_KEY"))
    exa_api_key: str = field(default_factory=lambda: _env("EXA_API_KEY"))
    brave_api_key: str = field(default_factory=lambda: _env("BRAVE_API_KEY"))
    default_timeout_s: float = 20.0
    max_results: int = 50


settings = Settings()
