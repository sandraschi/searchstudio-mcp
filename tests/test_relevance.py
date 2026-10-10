"""Relevance check: fixtures are real hits captured live on 2026-10-11."""

from super_search_mcp import fanout as F
from super_search_mcp.models import ProviderReceipt, SearchHit
from super_search_mcp.relevance import hit_score, provider_passes, query_terms

Q = "sitagliptin first clinical trial"


def _h(title: str, url: str, provider: str = "p", kind: str = "serp", snippet: str = ""):
    return SearchHit(title=title, url=url, snippet=snippet, provider=provider, kind=kind)


# Junk returned for Q (soft-blocked Bing via OpenSERP, broken arXiv search).
JUNK = [
    _h(
        "100 Mcdonalds Hush Hush Menu jobs | Jora",
        "https://au.jora.com/Mcdonalds-Hush-Hush-Menu-jobs",
    ),
    _h(
        "Kirk Flatten - Retired Police Sergeant / City of La Crosse",
        "https://www.linkedin.com/in/x",
    ),
    _h(
        "DreamTrue: Action-Faithful Robot World Model with Counterfactual Post-Training",
        "https://arxiv.org/html/2610.12468v1",
        snippet="We present DreamTrue, a multi-view, cross-embodiment robot world model.",
    ),
]
# Real answers DuckDuckGo returned for Q.
GOOD = [
    _h(
        "Effect of Sitagliptin on Cardiovascular Outcomes in Type 2 Diabetes",
        "https://www.nejm.org/doi/full/10.1056/NEJMoa1501352",
    ),
    _h(
        "Study Details | NCT01462266 | Study of Sitagliptin for the Treatment",
        "https://clinicaltrials.gov/study/NCT01462266",
    ),
]


def test_query_terms_drop_fillers_and_fold() -> None:
    assert query_terms(Q) == ["sitagliptin", "clinical", "trial"]
    assert query_terms("Indische Restaurants im Alsergrund") == [
        "indische",
        "restaurants",
        "alsergrund",
    ]
    assert query_terms("DPP-4 inhibitor") == ["dpp", "4", "inhibitor"]  # digits kept
    assert query_terms("the of and") == []


def test_real_junk_is_unrelated_and_real_answers_are_related() -> None:
    terms = query_terms(Q)
    assert all(hit_score(terms, h) == 0 for h in JUNK)
    assert all(hit_score(terms, h) >= 1 for h in GOOD)
    assert provider_passes(Q, JUNK) is False
    assert provider_passes(Q, JUNK + GOOD[:1]) is True  # one real hit is enough


def test_unjudgeable_queries_pass() -> None:
    assert provider_passes("the of", JUNK) is True
    assert provider_passes(Q, []) is True


def test_accents_and_case_are_folded() -> None:
    hit = _h("Geschichte von Muenchen und Zuerich", "https://x.test")
    assert hit_score(query_terms("ZUERICH history"), hit) >= 1


def test_check_relevance_turns_junk_into_unrelated_fault() -> None:
    r = ProviderReceipt(provider="openserp-local", kind="serp", ok=True, count=3)
    name, hits, out = F._check_relevance(Q, "openserp-local", list(JUNK), r)
    assert hits == [] and out.ok is False and out.fault_kind == "unrelated"
    assert out.count == 3  # what the provider returned, stays honest
    assert "unrelated to your query" in out.user_message
    assert "openserp-local unrelated" in F.build_coverage([out])


def test_check_relevance_leaves_good_and_semantic_providers_alone() -> None:
    r = ProviderReceipt(provider="duckduckgo", kind="serp", ok=True, count=2)
    _, hits, out = F._check_relevance(Q, "duckduckgo", list(GOOD), r)
    assert out.ok is True and len(hits) == 2
    r2 = ProviderReceipt(provider="exa", kind="serp", ok=True, count=1)
    _, hits2, out2 = F._check_relevance(Q, "exa", [JUNK[0]], r2)
    assert out2.ok is True and len(hits2) == 1  # meaning-based search is exempt


def test_merge_ranks_relevant_web_hits_above_unrelated_fleet_hits() -> None:
    weak_wiki = _h(
        "Dulaglutide", "https://en.wikipedia.org/wiki/Dulaglutide", "wikipedia", "knowledge"
    )
    per = [
        ("wikipedia", [weak_wiki]),
        ("duckduckgo", [_h(GOOD[0].title, GOOD[0].url, "duckduckgo", "serp")]),
    ]
    merged = F.merge_hits(per, Q)
    assert merged[0].provider == "duckduckgo"  # relevance beats kind order
    assert F.merge_hits(per)[0].provider == "wikipedia"  # no query: kind order


async def test_openserp_skips_soft_blocked_engine(monkeypatch) -> None:
    from super_search_mcp.providers import openserp

    answers = {
        "bing": [{"title": JUNK[1].title, "url": JUNK[1].url}],
        "duckduckgo": [{"title": GOOD[0].title, "url": GOOD[0].url}],
    }

    class _Resp:
        def __init__(self, data: list) -> None:
            self._data = data

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"results": self._data}

    class _Client:
        def __init__(self, *a: object, **k: object) -> None:
            return None

        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *a: object) -> bool:
            return False

        async def get(self, url: str) -> _Resp:
            engine = url.split("/")[3]
            return _Resp(answers.get(engine, []))

    monkeypatch.setattr(openserp, "_client", _Client)
    p = openserp.OpenSerpProvider("http://127.0.0.1:7000", engines=("bing", "duckduckgo"))
    hits, receipt = await p.search(Q)
    assert receipt.ok is True and hits[0].url == GOOD[0].url

    p2 = openserp.OpenSerpProvider("http://127.0.0.1:7000", engines=("bing",))
    hits2, receipt2 = await p2.search(Q)
    assert hits2 == [] and receipt2.fault_kind == "unrelated"
    assert "bing" in receipt2.user_message
