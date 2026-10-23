"""Authorized breaker chain: sharp knives, sheathed until the user says go.

When a provider hits a bot wall (challenge page, HTTP 202, barrier markup),
the direct fetch has already failed. These legs are the authorized second
tries, in order:

1. browser leg: re-render the URL through the browser-mcp bridge. The engine
   is operator-chosen via BROWSER_MCP_ENGINE (camoufox default; playwright,
   obscura, auto pass straight through to the bridge). 2026 benchmarks put
   nodriver first on live Cloudflare targets with Camoufox and Patchright
   close behind; the bridge owns the browsers, we only pick the engine.
2. flaresolverr leg: FlareSolverr sidecar (Cloudflare IUAM-class solver) at
   FLARESOLVERR_URL. Empty (default) = leg disarmed.

Authorization: legs fire only inside providers that already checked
browser_fallback_allowed() (Settings checkbox, BROWSER_MCP_URL hard-off).
Every rescue is labeled with its leg in the receipt `via` field and the
health ledger still counts the block. One attempt per leg, bounded by the
provider timeout so the fan-out budget stays max(legs).

Deliberately absent: CAPTCHA token APIs (CapSolver, 2Captcha, CapMonster).
Evaluated 2026-10-23: CapSolver cheapest Turnstile ($1.20/1k), 2Captcha
widest coverage, CapMonster cheapest reCAPTCHA v2 ($0.60/1k). None is wired
because no flow in our providers presents a solvable widget (no sitekey to
feed a createTask call); a key with no firing path would be a stub, and we
do not ship stubs. When a direct-fetch flow with sitekeys appears, it slots
in here as a further leg behind the same authorization switch.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable

import httpx

from .models import SearchHit


def _now_ms() -> int:
    return int(time.time() * 1000)


def _client(timeout_s: float = 20.0) -> httpx.AsyncClient:
    # Local copy of the provider HTTP helper (providers/base.py): importing
    # it here would cycle through providers/__init__ -> ddg -> breakers.
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout_s, connect=8.0),
        headers={"User-Agent": "searchstudio-mcp/0.1.0"},
        follow_redirects=True,
    )


BROWSER_ENGINES = ("camoufox", "playwright", "obscura", "auto")
DEFAULT_ENGINE = "camoufox"

LEG_LABELS = {
    "camoufox": "Camoufox browser",
    "playwright": "Playwright render",
    "obscura": "Obscura fetch",
    "auto": "browser-mcp auto ladder",
    "flaresolverr": "FlareSolverr session",
}


def breaker_engine() -> str:
    """Operator-chosen bridge engine, live-read. Unknown = default."""
    eng = os.environ.get("BROWSER_MCP_ENGINE", "").strip().lower()
    return eng if eng in BROWSER_ENGINES else DEFAULT_ENGINE


def flaresolverr_url() -> str:
    """FlareSolverr sidecar base URL. Empty = leg disarmed."""
    return os.environ.get("FLARESOLVERR_URL", "").strip().rstrip("/")


def breaker_legs() -> list[str]:
    """Ordered leg names actually armed right now (for status display)."""
    legs = ["browser"]
    if flaresolverr_url():
        legs.append("flaresolverr")
    return legs


def _browser_base() -> str:
    return os.environ.get("BROWSER_MCP_URL", "http://127.0.0.1:10780").strip().rstrip("/")


async def _browser_leg(
    url: str,
    parse: Callable[[str], list[tuple[str, str, str]]],
    provider: str,
    kind: str,
    limit: int,
    timeout_s: float,
) -> list[SearchHit]:
    """Render the URL through the browser-mcp bridge. [] on any failure."""
    base = _browser_base()
    if not base:
        return []
    try:
        async with _client(timeout_s) as client:
            resp = await client.post(
                f"{base}/api/fetch",
                json={"url": url, "engine": breaker_engine(), "include_html": True},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []
    if not data.get("success") or not data.get("html"):
        return []
    try:
        triples = parse(data["html"])
    except Exception:
        return []
    return [
        SearchHit(title=t, url=u, snippet=s, provider=provider, kind=kind)
        for t, u, s in triples[: max(limit, 1)]
    ]


async def _flaresolverr_leg(
    url: str,
    parse: Callable[[str], list[tuple[str, str, str]]],
    provider: str,
    kind: str,
    limit: int,
    timeout_s: float,
) -> list[SearchHit]:
    """Clear the URL through a FlareSolverr sidecar. [] on any failure."""
    base = flaresolverr_url()
    if not base:
        return []
    try:
        async with _client(timeout_s) as client:
            resp = await client.post(
                base,
                json={
                    "cmd": "request.get",
                    "url": url,
                    "maxTimeout": int(timeout_s * 1000),
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []
    try:
        html = data.get("solution", {}).get("response", "")
    except AttributeError:
        return []
    if not isinstance(html, str) or not html:
        return []
    try:
        triples = parse(html)
    except Exception:
        return []
    return [
        SearchHit(title=t, url=u, snippet=s, provider=provider, kind=kind)
        for t, u, s in triples[: max(limit, 1)]
    ]


async def run_breakers(
    url: str,
    parse: Callable[[str], list[tuple[str, str, str]]],
    provider: str,
    kind: str,
    limit: int = 10,
    timeout_s: float = 20.0,
) -> tuple[list[SearchHit], str]:
    """Try each armed leg in order. Returns (hits, leg); ([], "") if all fail.

    parse maps raw HTML to (title, url, snippet) triples (the caller's own
    parser, so this module stays provider-agnostic). The second leg only
    fires when the first misses and at least 5s of budget remain, so one
    provider never costs more than ~2x its timeout.
    """
    started = _now_ms()
    hits = await _browser_leg(url, parse, provider, kind, limit, timeout_s)
    if hits:
        return hits, breaker_engine()
    elapsed_s = (_now_ms() - started) / 1000.0
    remaining = timeout_s - elapsed_s
    if flaresolverr_url() and remaining >= 5.0:
        hits = await _flaresolverr_leg(url, parse, provider, kind, limit, remaining)
        if hits:
            return hits, "flaresolverr"
    return [], ""
