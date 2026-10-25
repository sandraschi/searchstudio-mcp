"""DuckDuckGo direct provider (serp, keyless).

Scrapes lite.duckduckgo.com result pages with defensive regex parsing.
Markup drifts without notice: parse failures degrade to empty-with-receipt,
never exceptions. Blocking shows up as anomaly/challenge pages or HTTP 202.
On the blocked path only, the authorized breaker chain runs
(breakers.run_breakers: bridge render, then FlareSolverr when armed) before
reporting blocked, unless switched off (Settings checkbox, or BROWSER_MCP_URL
set to empty as an operator hard-off).
"""

from __future__ import annotations

import html as _html
import re
import urllib.parse as _parse

from ..breakers import LEG_LABELS, run_breakers
from ..config import browser_fallback_allowed
from ..models import SearchHit
from .base import _client, _now_ms, _receipt

NAME = "duckduckgo"
KIND = "serp"

_ANCHOR_RE = re.compile(r"<a\s[^>]*?>(.*?)</a>", re.S | re.I)
_HREF_RE = re.compile(r"href\s*=\s*[\"']([^\"']+)[\"']", re.I)
_CLASS_RE = re.compile(r"class\s*=\s*[\"']([^\"']*)[\"']", re.I)
_SNIPPET_RE = re.compile(
    r"<td[^>]*class\s*=\s*[\"']result-snippet[\"'][^>]*>(.*?)</td>", re.S | re.I
)
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
    """Parse lite DDG markup into (title, url, snippet) triples. Pure function (tested).

    Tolerant to DDG markup drift: single or double quotes, href/class in any
    order (verified 2026-10-01 live HTML uses ``class='result-link'`` with
    href-before-class). Sponsored ``more info`` boilerplate links are skipped.
    """
    if not body:
        return []
    snippets = [_clean(m.group(1)) for m in _SNIPPET_RE.finditer(body)]
    out: list[tuple[str, str, str]] = []
    snippet_idx = 0
    for anchor in _ANCHOR_RE.finditer(body):
        tag = anchor.group(0)
        inner = anchor.group(1)
        cls = _CLASS_RE.search(tag)
        if not cls or "result-link" not in cls.group(1).split():
            continue
        href_m = _HREF_RE.search(tag)
        if not href_m:
            continue
        title = _clean(inner)
        if not title or title.lower() == "more info":
            continue
        url = _real_url(href_m.group(1))
        if not url or not title:
            continue
        snippet = snippets[snippet_idx] if snippet_idx < len(snippets) else ""
        # Snippets list includes sponsored rows too, so advance in lockstep
        # with result-link order (sponsored + organic share the same markup).
        snippet_idx += 1
        out.append((title, url, snippet))
    return out


def _fallback_note(allowed: bool, source: str) -> str:
    """Why the breakers did not rescue a blocked search (receipt text)."""
    if allowed:
        return " The authorized breaker legs were tried and did not help."
    if source == "env":
        return " Browser fallback is off (BROWSER_MCP_URL is empty)."
    return " Browser fallback is off in Settings."


class DuckDuckGoProvider:
    name = NAME
    kind = KIND

    def __init__(self, timeout_s: float = 20.0, data_dir: str = "data"):
        self._timeout_s = timeout_s
        self._data_dir = data_dir  # where the Settings preferences file lives

    @property
    def configured(self) -> bool:
        return True  # keyless; availability is probed per call, not assumed

    async def search(
        self, query: str, limit: int = 10, time_filter: str = "any"
    ) -> tuple[list[SearchHit], object]:
        # No date parameter exists on the lite endpoint (verified 2026-09-30
        # against the official params list): the filter is accepted and
        # reported unapplied, never silently dropped.
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
            short = f"duckduckgo request failed ({type(e).__name__})"
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=short,
                fault_kind="down",
                user_message="DuckDuckGo isn't reachable right now.",
                what_to_do="Try again shortly; other providers already ran.",
            )
        body = resp.text or ""
        if resp.status_code != 200 or any(m in body for m in _BLOCKED_MARKERS):
            allowed, source = browser_fallback_allowed(self._data_dir)
            breaker_hits: list[SearchHit] = []
            via = ""
            if allowed:
                breaker_hits, via = await run_breakers(
                    url,
                    parse_lite_html,
                    NAME,
                    KIND,
                    limit=limit,
                    timeout_s=self._timeout_s,
                )
            if breaker_hits:
                # Rescued, not direct: keep blocked=True so the health ledger
                # still counts the block, and say which route answered.
                label = LEG_LABELS.get(via, via)
                return breaker_hits, _receipt(
                    NAME,
                    KIND,
                    ok=True,
                    hits=breaker_hits,
                    started_ms=started,
                    blocked=True,
                    via=via,
                    user_message=(
                        "DuckDuckGo blocked direct access; these results came "
                        f"through the {label} (authorized breaker fallback)."
                    ),
                )
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=f"HTTP {resp.status_code} or bot challenge page",
                blocked=True,
                fault_kind="blocked",
                user_message="DuckDuckGo showed a bot challenge - they think we're a bot today."
                + _fallback_note(allowed, source),
                what_to_do="Usually clears within the hour; use other providers meanwhile.",
                retry_in="~1 hour",
            )
        triples = parse_lite_html(body)
        # Anti-silent-zero: 200 + result markup present but nothing parsed =
        # parser drift, not "no results". Report as failure so health drops.
        if not triples and ("result-link" in body or "result-snippet" in body):
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error="parse miss: result markup present but 0 triples extracted",
                fault_kind="bug",
                user_message="DuckDuckGo changed their layout and our parser missed - our bug.",
                what_to_do="Logged automatically; other providers continued.",
            )
        hits = [
            SearchHit(title=t, url=u, snippet=s, provider=NAME, kind=KIND)
            for t, u, s in triples[: max(limit, 1)]
        ]
        return hits, _receipt(NAME, KIND, ok=True, hits=hits, started_ms=started)
