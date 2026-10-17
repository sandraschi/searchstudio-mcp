"""Models.dev provider (knowledge, keyless).

A cached copy of the community model catalog (https://models.dev/catalog.json:
per-provider serving details plus provider-agnostic model facts) is kept in
the data dir and refreshed at most once per TTL. Free-text ``search`` matches
the query against model id / name / description for fan-out; the structured
``filter_models`` helper powers the ``models_lookup`` tool (tool_call flag +
minimum context, sorted by input $/1M).

No key, no account. A dead catalog fetch with a usable cache serves stale
data and says so in the receipt; with no cache at all it reports ``down``.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ..models import SearchHit
from .base import _client, _now_ms, _receipt

NAME = "modelsdev"
KIND = "knowledge"
DEFAULT_CATALOG_URL = "https://models.dev/catalog.json"
CACHE_FILE_NAME = "modelsdev_catalog.json"
INF_COST = float("inf")


def _cache_path(data_dir: str | Path) -> Path:
    return Path(data_dir) / CACHE_FILE_NAME


def _providers_of(payload: Any) -> dict:
    """Accept api.json shape ({provider: {...}}) and catalog.json shape.

    catalog.json carries provider endpoints and model facts in one response;
    both shapes expose a {provider_id: provider_entry} mapping, either at
    the top level or under a "providers" key.
    """
    if isinstance(payload, dict):
        nested = payload.get("providers")
        if isinstance(nested, dict):
            return nested
        if any(isinstance(v, dict) and "models" in v for v in payload.values()):
            return payload
    return {}


def _iter_models(payload: Any) -> list[tuple[str, dict, dict]]:
    """Yield (provider_id, provider_entry, model_entry) triples.

    Model entries may be a {model_id: entry} dict or a list of entries
    carrying their own id. Entries always get an "id" key set.
    """
    out: list[tuple[str, dict, dict]] = []
    for provider_id, pentry in _providers_of(payload).items():
        if not isinstance(pentry, dict):
            continue
        models = pentry.get("models", {})
        items: list[tuple[str, dict]] = []
        if isinstance(models, dict):
            items = [(mid, m) for mid, m in models.items() if isinstance(m, dict)]
        elif isinstance(models, list):
            items = [
                (str(m.get("id", "")), m) for m in models if isinstance(m, dict) and m.get("id")
            ]
        for model_id, mentry in items:
            merged = dict(mentry)
            merged.setdefault("id", model_id)
            out.append((str(provider_id), pentry, merged))
    return out


def _num(value: Any) -> float | None:
    return value if isinstance(value, (int, float)) else None


def model_row(provider_id: str, pentry: dict, mentry: dict) -> dict:
    """Flatten one catalog entry to the stable lookup row. Pure (tested)."""
    limit = mentry.get("limit", {}) if isinstance(mentry.get("limit"), dict) else {}
    cost = mentry.get("cost", {}) if isinstance(mentry.get("cost"), dict) else {}
    modalities = mentry.get("modalities", {}) if isinstance(mentry.get("modalities"), dict) else {}
    return {
        "provider": provider_id,
        "provider_name": pentry.get("name", provider_id),
        "model_id": str(mentry.get("id", "")),
        "model_name": str(mentry.get("name", mentry.get("id", ""))),
        "description": str(mentry.get("description", "") or ""),
        "family": str(mentry.get("family", "") or ""),
        "input_cost": _num(cost.get("input")),
        "output_cost": _num(cost.get("output")),
        "context": _num(limit.get("context")),
        "max_output": _num(limit.get("output")),
        "tool_call": bool(mentry.get("tool_call", False)),
        "reasoning": bool(mentry.get("reasoning", False)),
        "structured_output": bool(mentry.get("structured_output", False)),
        "temperature": bool(mentry.get("temperature", False)),
        "attachment": bool(mentry.get("attachment", False)),
        "modalities_in": list(modalities.get("input", []) or []),
        "modalities_out": list(modalities.get("output", []) or []),
        "open_weights": bool(mentry.get("open_weights", False)),
        "knowledge": str(mentry.get("knowledge", "") or ""),
        "release_date": str(mentry.get("release_date", "") or ""),
        "canonical_model_id": str(mentry.get("canonical_model_id", "") or ""),
        "doc_url": str(pentry.get("doc", "") or "https://models.dev/"),
    }


def _matches(row: dict, terms: list[str]) -> bool:
    if not terms:
        return True
    text = f"{row['model_id']} {row['model_name']} {row['description']} {row['family']}".lower()
    return any(t in text for t in terms)


def filter_models(
    payload: Any,
    query: str = "",
    needs_tool_call: bool = False,
    min_context: int = 0,
    max_input_cost: float = 0.0,
    open_weights_only: bool = False,
    limit: int = 20,
) -> list[dict]:
    """Filter + sort catalog rows. Pure function (tested).

    Sort is input $/1M ascending (unknown price sorts last), then output
    $/1M, then model id. max_input_cost <= 0 means no price cap.
    """
    terms = [t for t in query.lower().split() if t]
    rows = []
    for provider_id, pentry, mentry in _iter_models(payload):
        row = model_row(provider_id, pentry, mentry)
        if needs_tool_call and not row["tool_call"]:
            continue
        if open_weights_only and not row["open_weights"]:
            continue
        if min_context and (row["context"] is None or row["context"] < min_context):
            continue
        if max_input_cost > 0 and (row["input_cost"] is None or row["input_cost"] > max_input_cost):
            continue
        if not _matches(row, terms):
            continue
        rows.append(row)
    rows.sort(
        key=lambda r: (
            r["input_cost"] if r["input_cost"] is not None else INF_COST,
            r["output_cost"] if r["output_cost"] is not None else INF_COST,
            r["model_id"],
        )
    )
    return rows[: max(limit, 1)]


def format_snippet(row: dict) -> str:
    """One-line price + capability summary for fan-out hits. Pure (tested)."""
    in_c = f"${row['input_cost']:.2f}" if row["input_cost"] is not None else "price n/a"
    out_c = f"${row['output_cost']:.2f}" if row["output_cost"] is not None else "price n/a"
    ctx = int(row["context"]) if row["context"] is not None else "n/a"
    flags = (
        "/".join(
            name
            for name, on in (
                ("tool_call", row["tool_call"]),
                ("reasoning", row["reasoning"]),
                ("structured_output", row["structured_output"]),
            )
            if on
        )
        or "no tool/reasoning flags"
    )
    mods_in = "+".join(row["modalities_in"]) or "text"
    return (
        f"{in_c} in / {out_c} out per 1M; ctx {ctx}; {flags}; "
        f"in: {mods_in}; open_weights {'yes' if row['open_weights'] else 'no'}; "
        f"knowledge {row['knowledge'] or 'n/a'}"
    )


def map_rows(rows: list[dict]) -> list[SearchHit]:
    """Map lookup rows to fan-out hits. Pure function (tested)."""
    hits = []
    for row in rows:
        hits.append(
            SearchHit(
                title=f"{row['model_name']} ({row['provider']}/{row['model_id']})",
                url=row["doc_url"] or "https://models.dev/",
                snippet=format_snippet(row),
                provider=NAME,
                kind=KIND,
            )
        )
    return hits


def read_cache(data_dir: str | Path) -> tuple[Any | None, int]:
    """Return (payload, fetched_at_ms); (None, 0) when no usable cache."""
    try:
        raw = json.loads(_cache_path(data_dir).read_text(encoding="utf-8"))
        payload, fetched_at = raw.get("payload"), int(raw.get("fetched_at_ms", 0))
        if _providers_of(payload):
            return payload, fetched_at
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return None, 0


def write_cache(data_dir: str | Path, payload: Any) -> int:
    """Persist payload; returns fetched_at_ms. Raises on IO failure."""
    path = _cache_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    now_ms = int(time.time() * 1000)
    path.write_text(
        json.dumps({"fetched_at_ms": now_ms, "payload": payload}),
        encoding="utf-8",
    )
    return now_ms


async def load_catalog(
    data_dir: str | Path,
    catalog_url: str = DEFAULT_CATALOG_URL,
    timeout_s: float = 20.0,
    ttl_hours: float = 24.0,
    force_refresh: bool = False,
) -> tuple[Any | None, dict]:
    """Return (payload, meta). Meta: {cached_at_ms, stale, error}.

    Uses the cache when fresh; refreshes when stale/missing/forced. A failed
    refresh with a usable cache serves stale data with meta["stale"] True and
    the error noted. (None, meta) only when nothing usable exists.
    """
    cached, cached_at = read_cache(data_dir)
    age_ms = int(time.time() * 1000) - cached_at if cached_at else INF_COST
    fresh = cached is not None and age_ms < ttl_hours * 3600 * 1000
    if cached is not None and fresh and not force_refresh:
        return cached, {"cached_at_ms": cached_at, "stale": False, "error": ""}
    try:
        async with _client(timeout_s) as client:
            resp = await client.get(catalog_url)
            resp.raise_for_status()
            payload = resp.json()
        if not _providers_of(payload):
            raise ValueError("catalog payload has no provider mapping")
        fetched_at = write_cache(data_dir, payload)
        return payload, {"cached_at_ms": fetched_at, "stale": False, "error": ""}
    except Exception as e:  # noqa: BLE001 - error text goes to the receipt
        if cached is not None:
            return cached, {
                "cached_at_ms": cached_at,
                "stale": True,
                "error": f"refresh failed ({e}); serving cache",
            }
        return None, {"cached_at_ms": 0, "stale": False, "error": str(e)}


class ModelsDevProvider:
    """models.dev catalog as a knowledge provider (keyless, cached)."""

    name = NAME
    kind = KIND

    def __init__(
        self,
        data_dir: str | Path = "data",
        catalog_url: str = DEFAULT_CATALOG_URL,
        timeout_s: float = 20.0,
        cache_hours: float = 24.0,
    ):
        self._data_dir = data_dir
        self._catalog_url = catalog_url or DEFAULT_CATALOG_URL
        self._timeout_s = timeout_s
        self._cache_hours = cache_hours

    @property
    def configured(self) -> bool:
        return True

    async def search(
        self, query: str, limit: int = 10, time_filter: str = "any"
    ) -> tuple[list[SearchHit], object]:
        # The catalog carries no per-entry publish dates: accepted, unapplied.
        started = _now_ms()
        q = (query or "").strip()
        if not q:
            return [], _receipt(
                NAME, KIND, ok=False, hits=[], started_ms=started, error="empty query"
            )
        payload, meta = await load_catalog(
            self._data_dir, self._catalog_url, self._timeout_s, self._cache_hours
        )
        if payload is None:
            return [], _receipt(
                NAME,
                KIND,
                ok=False,
                hits=[],
                started_ms=started,
                error=f"catalog unreachable and no cache: {meta['error']}",
                fault_kind="down",
                user_message="The models.dev catalog is unreachable and no cache exists.",
                what_to_do="Try again shortly; other providers already ran.",
            )
        rows = filter_models(payload, query=q, limit=limit)
        hits = map_rows(rows)
        note = f" Served from stale cache ({meta['error']})." if meta["stale"] else ""
        receipt = _receipt(NAME, KIND, ok=True, hits=hits, started_ms=started)
        if note:
            receipt.user_message = f"Catalog refresh failed - results may be up to a day old.{note}"
        return hits, receipt
