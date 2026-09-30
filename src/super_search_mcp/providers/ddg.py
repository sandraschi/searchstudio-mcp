"""DuckDuckGo direct provider (serp, keyless).

Scrapes lite.duckduckgo.com result pages with defensive regex parsing.
Markup drifts without notice: parse failures degrade to empty-with-receipt,
never exceptions. Blocking shows up as anomaly/challenge pages or HTTP 202.
"""

from __future__ import annotations

import html as _html
import re
import urllib.parse as _parse

from ..models import SearchHit
from .base import _client, _now_ms, _receipt

NAME = "duckduckgo"
KIND = "serp"

_LINK_RE = re.compile(r'<a[^>]*class="result-link"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)
_SNIPPET_RE = re.compile(r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>', re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_BLOCKED_MARKERS = ("anomaly-modal", "challenge-form", "not a robot")


def _clean(raw: str) -> str:
    return _TAG_RE.sub("", _html.unescape(raw or "")).strip()


def _real_url(href: str) -> str:
    """Unwrap DDG redirect links (//duckduckgo.com/l/?uddg=<real>&...)."""
    href = _html.unescape(href or "").strip()
    if "uddg=" in href:
        try:
            qs = _parse.parse_qs(_parse.urlsplit(href).query)
            if qs.get("uddg"):
                return qs["uddg"][0]
        except ValueError:
            pass
    if href.startswith("//"):
        return "https:" + href
    return href


def parse_lite_html(body: str) -> list[tuple[str, str, str]]:
    """Parse lite DDG markup into (title, url, snippet) triples. Pure function (tested)."""
    links = [(m.group(1), _clean(m.group(2))) for m in _LINK_RE.finditer(body or "")]
    snippets = [_clean(m.group(1)) for m in _SNIPPET_RE.finditer(body or "")]
    out = []
    for i, (href, title) in enumerate(links):
        url = _real_url(href)
        if not url or not title:
            continue
        out.append((title, url, snippets[i] if i < len(snippets) else ""))
    return out


class DuckDuckGoProvider:
    name = NAME
    kind = KIND

    def __init__(self, timeout_s: float = 20.0):
        self._timeout_s = timeout_s

    @property
    def configured(self) -> bool:
        return True  # keyless; availability is probed per call, not assumed

    async def search(self, query: str, limit: int = 10) -> tuple[list[SearchHit], object]:
        started = _now_ms()
        q = (query or "").strip()
        if not q:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error="empty query"
            )
        url = "https://lite.duckduckgo.com/lite/?" + _parse.urlencode({"q": q})
        try:
            async with _client(self._timeout_s) as client:
                resp = await client.get(url)
        except Exception as e:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error=f"request failed: {e}"
            )
        body = resp.text or ""
        if resp.status_code != 200 or any(m in body for m in _BLOCKED_MARKERS):
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=f"HTTP {resp.status_code} or bot challenge page",
                blocked=True,
            )
        hits = [
            SearchHit(title=t, url=u, snippet=s, provider=NAME, kind=KIND)
            for t, u, s in parse_lite_html(body)[: max(limit, 1)]
        ]
        return hits, _receipt(NAME, KIND, ok=True, hits=hits, started_ms=started)
