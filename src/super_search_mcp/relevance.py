"""Cheap literal relevance check: catch providers that answer with junk.

Search engines sometimes answer automated traffic with confident nonsense
instead of a visible block (a "soft block"), and upstream search bugs do the
same. Measured 2026-10-11: for "sitagliptin first clinical trial", Bing via
OpenSERP returned McDonald's menu pages and arxiv-mcp returned unrelated
brand-new preprints, all reported ok. This module flags such answers so the
receipt says "unrelated" instead of "ok" (fault kind in
EXTERNAL_FAULT_TRANSPARENCY.md).

No LLM, no network, pure functions (tested). Deliberately lenient: a false
"unrelated" hides good results, which is worse than letting mild noise
through. Providers that search by meaning (SEMANTIC_PROVIDERS) are exempt,
because their good hits need not contain the query's words.
"""

from __future__ import annotations

import re
import unicodedata

from .models import SearchHit

# Providers whose relevant hits may share no words with the query.
SEMANTIC_PROVIDERS = frozenset({"exa", "arxiv-depot"})

# Function words and generic search fillers (English + German) that carry no
# topic. Kept short on purpose: every entry here makes the check weaker.
_STOPWORDS = frozenset(
    """
    a an and are as at be by for from how in into is it its of on or that the
    this to was what when where which who why with about best first latest new
    top vs versus near me my our your
    der die das und oder ein eine einer eines im in ist mit von zu zum zur fur
    fuer auf aus bei den dem des nach uber ueber wie was wo wer
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _fold(text: str) -> str:
    """Casefold and strip accents so 'Muenchen'/'Munchen' style variants meet."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def query_terms(query: str) -> list[str]:
    """Topic-bearing terms of a query, in order, without duplicates."""
    out: list[str] = []
    for tok in _TOKEN_RE.findall(_fold(query)):
        if tok in _STOPWORDS:
            continue
        if len(tok) < 3 and not any(c.isdigit() for c in tok):
            continue
        if tok not in out:
            out.append(tok)
    return out


def _anchor(terms: list[str]) -> str:
    """The most specific-looking term: the longest (first one on ties)."""
    return max(terms, key=len) if terms else ""


def hit_score(terms: list[str], hit: SearchHit) -> int:
    """0 = unrelated, 1 = related, 2 = strongly related.

    Related means the hit text (title, snippet, URL) contains the anchor
    term or at least half of the query terms; strongly related means both.
    """
    if not terms:
        return 0
    text = _fold(f"{hit.title} {hit.snippet} {hit.url}")
    has_anchor = _anchor(terms) in text
    matched = sum(1 for t in terms if t in text)
    half = matched * 2 >= len(terms)
    return int(has_anchor) + int(half)


def provider_passes(query: str, hits: list[SearchHit]) -> bool:
    """True unless the provider returned hits and not one of them is related.

    Queries with no topic terms (only stopwords) cannot be judged and pass.
    """
    terms = query_terms(query)
    if not terms or not hits:
        return True
    return any(hit_score(terms, h) > 0 for h in hits)
