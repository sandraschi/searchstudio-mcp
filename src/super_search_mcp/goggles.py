"""Goggles store: Brave custom-reranker lenses with CRUD.

A Goggle is a small text file (Brave's DSL: $boost/$downrank/$discard rules)
hosted at a public URL and passed per-request to the Brave API, which applies
it server-side. Prepared entries ship with ready-to-publish DSL text; a
prepared lens activates once it has a public URL (published via
search.brave.com/goggles, a gist, or any raw file URL) pasted into its URL
field. Enabling without a URL is refused - a lens with no URL would silently
do nothing, and we do not ship silent states.

User state lives in data/goggles.json (gitignored, like keys and prefs).
"""

from __future__ import annotations

import json
from pathlib import Path

STORE_FILE = "goggles.json"

# Curated starter lenses. DSL follows the official quickstart
# (github.com/brave/goggles-quickstart): mandatory ! header lines, one
# instruction per line, $boost/$downrank/$discard actions.
PREPARED = [
    {
        "name": "no-pinterest",
        "description": "Discard Pinterest boards from image-heavy queries.",
        "dsl": (
            "! name: No Pinterest\n"
            "! description: Discard Pinterest boards.\n"
            "! public: false\n"
            "! author: SearchStudio\n"
            "\n"
            "$discard,site=pinterest.com\n"
            "$discard,site=pin.it\n"
        ),
    },
    {
        "name": "tech-blogs-boost",
        "description": "Boost independent tech writing over content farms.",
        "dsl": (
            "! name: Tech blogs boost\n"
            "! description: Boost independent tech writing.\n"
            "! public: false\n"
            "! author: SearchStudio\n"
            "\n"
            "/blog/$site=stackoverflow.blog,$boost=2\n"
            "/blog/$site=martinfowler.com,$boost=2\n"
            "$site=danluu.com,$boost=2\n"
            "$site=ciechanow.ski,$boost=2\n"
        ),
    },
    {
        "name": "docs-first",
        "description": "Boost official documentation domains.",
        "dsl": (
            "! name: Docs first\n"
            "! description: Boost official documentation.\n"
            "! public: false\n"
            "! author: SearchStudio\n"
            "\n"
            "$site=docs.python.org,$boost=3\n"
            "$site=developer.mozilla.org,$boost=3\n"
            "$site=docs.rs,$boost=2\n"
            "$site=pytorch.org,$boost=2\n"
        ),
    },
    {
        "name": "academic-boost",
        "description": "Boost universities and journals for research queries.",
        "dsl": (
            "! name: Academic boost\n"
            "! description: Boost universities and journals.\n"
            "! public: false\n"
            "! author: SearchStudio\n"
            "\n"
            "$site=edu,$boost=2\n"
            "$site=ac.uk,$boost=2\n"
            "$site=nature.com,$boost=2\n"
            "$site=science.org,$boost=2\n"
        ),
    },
    {
        "name": "no-ai-farms",
        "description": "Discard known AI-content-farm domains.",
        "dsl": (
            "! name: No AI farms\n"
            "! description: Discard AI content farms.\n"
            "! public: false\n"
            "! author: SearchStudio\n"
            "\n"
            "$discard,site=dataconomy.com\n"
        ),
    },
]


def _store_path(data_dir: str) -> Path:
    return Path(data_dir or "data") / STORE_FILE


def _blank_entry(name: str, description: str, dsl: str) -> dict:
    return {
        "name": name,
        "url": "",
        "notes": "",
        "enabled": False,
        "builtin": True,
        "description": description,
        "dsl": dsl,
    }


def load_store(data_dir: str) -> dict:
    """Load the store, seeding prepared entries on first run. Never raises."""
    path = _store_path(data_dir)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = raw.get("entries", []) if isinstance(raw, dict) else []
    except Exception:
        entries = []
    have = {e.get("name") for e in entries if isinstance(e, dict)}
    for p in PREPARED:
        if p["name"] not in have:
            entries.append(_blank_entry(p["name"], p["description"], p["dsl"]))
    return {"entries": entries}


def _write_store(data_dir: str, store: dict) -> None:
    path = _store_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2), encoding="utf-8")


def _valid_url(url: str) -> bool:
    u = (url or "").strip()
    return u.startswith("https://") and len(u) > len("https://x")


def upsert_entry(
    data_dir: str, name: str, url: str = "", notes: str = "", enabled: bool | None = None
) -> tuple[dict | None, str]:
    """Create or update a custom entry. Returns (entry, error)."""
    name = (name or "").strip().lower().replace(" ", "-")
    if not name:
        return None, "name is required"
    store = load_store(data_dir)
    entries = store["entries"]
    found = next((e for e in entries if e.get("name") == name), None)
    if found is None:
        if any(p["name"] == name for p in PREPARED):
            found = _blank_entry(name, "", "")
            entries.append(found)
        else:
            found = {
                "name": name,
                "url": "",
                "notes": "",
                "enabled": False,
                "builtin": False,
                "description": "",
                "dsl": "",
            }
            entries.append(found)
    if url is not None and url != "":
        if not _valid_url(url):
            return None, "url must be a public https:// URL"
        found["url"] = url.strip()
    if notes is not None:
        found["notes"] = notes
    if enabled is not None:
        if enabled and not found.get("url"):
            return None, "a lens needs a public URL before it can be enabled"
        found["enabled"] = bool(enabled)
    _write_store(data_dir, store)
    return found, ""


def delete_entry(data_dir: str, name: str) -> tuple[bool, str]:
    """Delete a custom entry. Builtin prepared entries cannot be deleted."""
    name = (name or "").strip()
    store = load_store(data_dir)
    entries = store["entries"]
    found = next((e for e in entries if e.get("name") == name), None)
    if found is None:
        return False, "unknown lens"
    if found.get("builtin"):
        return False, "prepared lenses cannot be deleted (clear the URL to park one)"
    store["entries"] = [e for e in entries if e.get("name") != name]
    _write_store(data_dir, store)
    return True, ""


def enabled_goggle_urls(data_dir: str) -> list[str]:
    """URLs of enabled entries with valid URLs, in store order."""
    store = load_store(data_dir)
    out = []
    for e in store["entries"]:
        if e.get("enabled") and _valid_url(e.get("url", "")):
            out.append(e["url"].strip())
    return out
