"""Local SQLite cache.

Pageview counts for finished days never change, so every complete month is cached
permanently and re-used by later, related queries (another language, a longer period,
a different basket). Metadata that can change (Wikidata sitelinks, redirects,
search results) is cached with a time-to-live.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS series (sid TEXT NOT NULL, day TEXT NOT NULL, views INTEGER NOT NULL,
                                   PRIMARY KEY (sid, day)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS coverage (sid TEXT NOT NULL, month TEXT NOT NULL,
                                     PRIMARY KEY (sid, month)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL, ts REAL NOT NULL);
"""


def home_dir() -> Path:
    """Directory for the cache (the launcher exports WIKITRENDS_HOME)."""
    cand = os.environ.get("WIKITRENDS_HOME") or os.path.join(os.path.expanduser("~/.cache"), "wikitrends")
    try:
        os.makedirs(cand, exist_ok=True)
        return Path(cand)
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "wikitrends"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


class Cache:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else home_dir() / "cache.sqlite"
        self._lock = threading.Lock()
        self._con = sqlite3.connect(str(self.path), timeout=60, check_same_thread=False)
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.execute("PRAGMA synchronous=NORMAL")
        self._con.executescript(_SCHEMA)
        self._con.commit()

    # ---- key/value metadata -------------------------------------------------
    def kv_get(self, key: str, ttl_days: Optional[float] = 30):
        with self._lock:
            row = self._con.execute("SELECT value, ts FROM kv WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        if ttl_days is not None and time.time() - row[1] > ttl_days * 86400:
            return None
        return json.loads(row[0])

    def kv_set(self, key: str, value) -> None:
        with self._lock:
            self._con.execute("INSERT OR REPLACE INTO kv VALUES (?,?,?)",
                              (key, json.dumps(value, ensure_ascii=False), time.time()))
            self._con.commit()

    # ---- daily series ---------------------------------------------------------
    def covered_months(self, sid: str, months: Iterable[str]) -> set:
        months = list(months)
        if not months:
            return set()
        with self._lock:
            rows = self._con.execute(
                "SELECT month FROM coverage WHERE sid=? AND month BETWEEN ? AND ?",
                (sid, min(months), max(months))).fetchall()
        return {r[0] for r in rows}

    def load_days(self, sid: str, first_day: str, last_day: str) -> Dict[str, int]:
        with self._lock:
            rows = self._con.execute(
                "SELECT day, views FROM series WHERE sid=? AND day BETWEEN ? AND ?",
                (sid, first_day, last_day)).fetchall()
        return dict(rows)

    def store(self, sid: str, days: Dict[str, int], complete_months: List[str]) -> None:
        with self._lock:
            self._con.executemany("INSERT OR REPLACE INTO series VALUES (?,?,?)",
                                  [(sid, d, int(v)) for d, v in days.items()])
            self._con.executemany("INSERT OR IGNORE INTO coverage VALUES (?,?)",
                                  [(sid, m) for m in complete_months])
            self._con.commit()

    # ---- housekeeping -------------------------------------------------------------
    def info(self) -> dict:
        with self._lock:
            n_series = self._con.execute("SELECT COUNT(DISTINCT sid) FROM coverage").fetchone()[0]
            n_days = self._con.execute("SELECT COUNT(*) FROM series").fetchone()[0]
            n_kv = self._con.execute("SELECT COUNT(*) FROM kv").fetchone()[0]
        size = self.path.stat().st_size if self.path.exists() else 0
        return {"path": str(self.path), "series": n_series, "day_rows": n_days,
                "metadata_entries": n_kv, "size_mb": round(size / 1e6, 2)}

    def clear(self, what: str = "all") -> None:
        with self._lock:
            if what in ("all", "pageviews"):
                self._con.execute("DELETE FROM series")
                self._con.execute("DELETE FROM coverage")
            if what in ("all", "metadata"):
                self._con.execute("DELETE FROM kv")
            self._con.commit()
            self._con.execute("VACUUM")
