"""Configuration: env-driven, live-read, keyless-first.

Every provider works without credentials except Tavily/Exa/Brave, which
degrade to declared stubs (configured=False + setup hint) when unset.
Secrets live in env or the host config — never in this repo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


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
