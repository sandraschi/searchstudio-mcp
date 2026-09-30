"""Provider health ledger: SQLite, WAL mode, short transactions.

Every fan-out records one row per provider attempt (ok, latency, blocked).
`provider_health` reads the rolling scoreboard; Phase 2 uses it for adaptive
ordering. Thread-safe for concurrent stdio + HTTP clients: WAL journal,
`BEGIN IMMEDIATE` writes, one connection per call (no shared handles).
"""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path

logger = logging.getLogger("searchstudio.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS provider_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    provider TEXT NOT NULL,
    kind TEXT NOT NULL,
    ok INTEGER NOT NULL,
    latency_ms INTEGER NOT NULL,
    count INTEGER NOT NULL,
    blocked INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_provider_ts
    ON provider_attempts(provider, ts);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


def record_attempt(
    db_path: Path,
    *,
    provider: str,
    kind: str,
    ok: bool,
    latency_ms: int,
    count: int,
    blocked: bool = False,
) -> None:
    """Append one attempt row. Failures here never fail the search itself."""
    try:
        conn = _connect(db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT INTO provider_attempts "
                "(ts, provider, kind, ok, latency_ms, count, blocked) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (int(time.time()), provider, kind, int(ok), latency_ms, count, int(blocked)),
            )
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                logger.debug("ledger rollback failed", exc_info=True)
        finally:
            conn.close()
    except Exception:
        logger.debug("ledger write failed (advisory only)", exc_info=True)


def health_summary(db_path: Path, *, window_hours: int = 24) -> list[dict]:
    """Rolling scoreboard per provider: attempts, success rate, p50 latency, blocks."""
    try:
        conn = _connect(db_path)
        try:
            cutoff = int(time.time()) - window_hours * 3600
            rows = conn.execute(
                "SELECT provider, kind, ok, latency_ms, blocked FROM provider_attempts "
                "WHERE ts >= ? ORDER BY provider, ts",
                (cutoff,),
            ).fetchall()
        finally:
            conn.close()
    except Exception:
        return []
    by_provider: dict[str, dict] = {}
    for provider, kind, ok, latency_ms, blocked in rows:
        slot = by_provider.setdefault(
            provider,
            {"provider": provider, "kind": kind, "attempts": 0, "ok": 0, "lat": [], "blocked": 0},
        )
        slot["attempts"] += 1
        slot["ok"] += int(ok)
        slot["blocked"] += int(blocked)
        slot["lat"].append(latency_ms)
    out = []
    for slot in by_provider.values():
        lat = sorted(slot.pop("lat"))
        p50 = lat[len(lat) // 2] if lat else 0
        attempts = slot["attempts"]
        out.append(
            {
                **slot,
                "success_rate": round(slot["ok"] / attempts, 3) if attempts else 0.0,
                "p50_latency_ms": p50,
            }
        )
    return sorted(out, key=lambda s: s["provider"])
