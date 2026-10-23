"""Provider registry: construct the Phase 1 set from settings."""

from __future__ import annotations

from ..config import resolve_key
from .arxiv_depot import ArxivDepotProvider
from .arxiv_local import ArxivMcpProvider
from .brave import BraveProvider
from .ddg import DuckDuckGoProvider
from .exa import ExaProvider
from .modelsdev import ModelsDevProvider
from .openserp import OpenSerpProvider
from .tavily import TavilyProvider
from .wikipedia import WikipediaProvider


def build_providers(settings) -> list:
    """Phase 1 providers. Keyless always active; Tavily/Exa/Brave degrade to stubs.

    SaaS keys resolve live per call (env wins, UI-stored file second), so
    keys entered in Settings take effect without a backend restart.
    """
    tavily_key, _ = resolve_key(settings, "TAVILY_API_KEY")
    exa_key, _ = resolve_key(settings, "EXA_API_KEY")
    brave_key, _ = resolve_key(settings, "BRAVE_API_KEY")
    return [
        ArxivMcpProvider(
            base_url=settings.arxiv_mcp_base_url, timeout_s=settings.default_timeout_s
        ),
        ArxivDepotProvider(
            base_url=settings.arxiv_mcp_base_url, timeout_s=settings.default_timeout_s
        ),
        WikipediaProvider(timeout_s=settings.default_timeout_s),
        ModelsDevProvider(
            data_dir=settings.data_dir,
            catalog_url=settings.modelsdev_catalog_url,
            timeout_s=settings.default_timeout_s,
            cache_hours=settings.modelsdev_cache_hours,
        ),
        OpenSerpProvider(base_url=settings.openserp_base_url, timeout_s=settings.default_timeout_s),
        DuckDuckGoProvider(timeout_s=settings.default_timeout_s, data_dir=settings.data_dir),
        TavilyProvider(api_key=tavily_key, timeout_s=settings.default_timeout_s),
        ExaProvider(api_key=exa_key, timeout_s=settings.default_timeout_s),
        BraveProvider(api_key=brave_key, timeout_s=settings.default_timeout_s),
    ]
