"""Provider registry: construct the Phase 1 set from settings."""

from __future__ import annotations

from .arxiv_depot import ArxivDepotProvider
from .arxiv_local import ArxivMcpProvider
from .ddg import DuckDuckGoProvider
from .exa import ExaProvider
from .openserp import OpenSerpProvider
from .tavily import TavilyProvider
from .wikipedia import WikipediaProvider


def build_providers(settings) -> list:
    """Phase 1 providers. Keyless always active; Tavily/Exa degrade to stubs."""
    return [
        ArxivMcpProvider(
            base_url=settings.arxiv_mcp_base_url, timeout_s=settings.default_timeout_s
        ),
        ArxivDepotProvider(
            base_url=settings.arxiv_mcp_base_url, timeout_s=settings.default_timeout_s
        ),
        WikipediaProvider(timeout_s=settings.default_timeout_s),
        OpenSerpProvider(base_url=settings.openserp_base_url, timeout_s=settings.default_timeout_s),
        DuckDuckGoProvider(timeout_s=settings.default_timeout_s),
        TavilyProvider(api_key=settings.tavily_api_key, timeout_s=settings.default_timeout_s),
        ExaProvider(api_key=settings.exa_api_key, timeout_s=settings.default_timeout_s),
    ]
