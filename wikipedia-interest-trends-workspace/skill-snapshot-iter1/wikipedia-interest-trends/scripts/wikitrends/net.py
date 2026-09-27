"""HTTP access to Wikimedia APIs.

Wikimedia rate-limits per client identity: requests whose User-Agent has no contact
information get ~10 requests/minute, identified clients ~200/minute, and at most
3 concurrent requests are recommended. This module therefore
  * sends a descriptive User-Agent with a contact URL/email (WIKITRENDS_CONTACT),
  * limits concurrency to 3 and throughput with a sliding window shared by all
    processes on this machine (parallel agents do not trip the limit together),
  * honours Retry-After on HTTP 429 for every process, and retries 5xx errors.
"""
from __future__ import annotations

import gzip
import json
import os
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from . import __version__
from .cache import home_dir

CONTACT = os.environ.get("WIKITRENDS_CONTACT", "https://agentskills.io")
USER_AGENT = ("wikipedia-interest-trends/%s (%s; Agent Skill for Wikipedia pageview research) "
              "python-urllib/%d.%d" % (__version__, CONTACT, sys.version_info[0], sys.version_info[1]))
MAX_PER_MINUTE = int(os.environ.get("WIKITRENDS_MAX_RPM", "150"))
MAX_CONCURRENCY = 3

_semaphore = threading.BoundedSemaphore(MAX_CONCURRENCY)
_quiet = False


class ApiError(RuntimeError):
    pass


def set_quiet(value: bool) -> None:
    global _quiet
    _quiet = value


def log(msg: str) -> None:
    if not _quiet:
        print(msg, file=sys.stderr, flush=True)


class _SharedRateLimiter:
    """Sliding-window limiter stored in SQLite so separate processes share it."""

    def __init__(self, path):
        self.path = str(path)
        self._local = threading.local()

    def _con(self):
        con = getattr(self._local, "con", None)
        if con is None:
            con = sqlite3.connect(self.path, timeout=30, isolation_level=None)
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("CREATE TABLE IF NOT EXISTS hits (ts REAL NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value REAL)")
            self._local.con = con
        return con

    def acquire(self) -> None:
        while True:
            now = time.time()
            wait = 0.5
            con = self._con()
            try:
                con.execute("BEGIN IMMEDIATE")
                row = con.execute("SELECT value FROM state WHERE key='blocked_until'").fetchone()
                if row and row[0] > now:
                    wait = row[0] - now
                    con.execute("COMMIT")
                else:
                    con.execute("DELETE FROM hits WHERE ts < ?", (now - 60,))
                    count, oldest = con.execute("SELECT COUNT(*), MIN(ts) FROM hits").fetchone()
                    if count < MAX_PER_MINUTE:
                        con.execute("INSERT INTO hits VALUES (?)", (now,))
                        con.execute("COMMIT")
                        return
                    con.execute("COMMIT")
                    wait = max(0.2, oldest + 60 - now)
            except sqlite3.OperationalError:
                try:
                    con.execute("ROLLBACK")
                except sqlite3.OperationalError:
                    pass
            time.sleep(min(wait, 5.0))

    def block_for(self, seconds: float) -> None:
        con = self._con()
        try:
            con.execute("INSERT OR REPLACE INTO state VALUES ('blocked_until', ?)", (time.time() + seconds,))
        except sqlite3.OperationalError:
            pass


_limiter = _SharedRateLimiter(home_dir() / "ratelimit.sqlite")


def get_json(url: str, params: Optional[dict] = None, *, allow_404: bool = True, timeout: float = 40):
    """GET a JSON document. Returns None on 404 when allow_404 (Wikimedia uses 404 for 'no data')."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    last_error = None
    for attempt in range(7):
        _limiter.acquire()
        wait = None
        with _semaphore:
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT, "Accept": "application/json", "Accept-Encoding": "gzip"})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read()
                    if resp.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    return json.loads(raw.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code == 404 and allow_404:
                    return None
                if exc.code in (429, 500, 502, 503, 504):
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    try:
                        wait = float(retry_after) if retry_after else min(60.0, 3.0 * 2 ** attempt)
                    except ValueError:
                        wait = min(60.0, 3.0 * 2 ** attempt)
                    wait = min(wait, 120.0)
                    last_error = "HTTP %d" % exc.code
                    if exc.code == 429:
                        _limiter.block_for(wait)
                        log("wikitrends: Wikimedia asked us to slow down; waiting %.0fs (normal, keep waiting)" % wait)
                else:
                    body = exc.read()[:300].decode("utf-8", "replace") if exc.fp else ""
                    raise ApiError("HTTP %d for %s %s" % (exc.code, url, body))
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                last_error = str(exc)
                wait = min(30.0, 2.0 * 2 ** attempt)
        if wait is not None:
            time.sleep(wait)
    raise ApiError("giving up after retries (%s): %s" % (last_error, url))
