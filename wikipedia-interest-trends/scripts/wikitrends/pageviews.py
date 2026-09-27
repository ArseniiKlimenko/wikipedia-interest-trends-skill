"""Daily pageview series from the Wikimedia Analytics API, with month-level caching.

The API omits zero-view days and answers 404 when there is no data at all, so missing
days inside a fetched range are zeros. Only months that ended at least two days ago
are marked as cached (data loads can lag by up to a day).
"""
from __future__ import annotations

import datetime as dt
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple

import numpy as np

from .cache import Cache
from .net import MAX_CONCURRENCY, get_json, log

API = "https://wikimedia.org/api/rest_v1/metrics/pageviews"
DATA_START = dt.date(2015, 7, 1)


def article_sid(project: str, title: str, access: str, agent: str) -> str:
    return "pv|%s|%s|%s|%s" % (project, access, agent, title.replace(" ", "_"))


def aggregate_sid(project: str, access: str, agent: str) -> str:
    return "agg|%s|%s|%s" % (project, access, agent)


def _url(sid: str, start: dt.date, end: dt.date) -> str:
    kind, project, access, agent, *rest = sid.split("|", 4)
    if kind == "pv":
        title = urllib.parse.quote(rest[0], safe="")
        return "%s/per-article/%s/%s/%s/%s/daily/%s/%s" % (
            API, project, access, agent, title, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
    return "%s/aggregate/%s/%s/%s/daily/%s00/%s00" % (
        API, project, access, agent, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))


def month_key(d: dt.date) -> str:
    return d.strftime("%Y-%m")


def months_in(start: dt.date, end: dt.date) -> List[str]:
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append("%04d-%02d" % (y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def month_bounds(month: str) -> Tuple[dt.date, dt.date]:
    y, m = map(int, month.split("-"))
    first = dt.date(y, m, 1)
    nxt = dt.date(y + 1, 1, 1) if m == 12 else dt.date(y, m + 1, 1)
    return first, nxt - dt.timedelta(days=1)


def _is_final(month: str, today: dt.date) -> bool:
    return month_bounds(month)[1] <= today - dt.timedelta(days=2)


def _missing_ranges(missing: List[str], start: dt.date, end: dt.date) -> List[Tuple[dt.date, dt.date, List[str]]]:
    """Group consecutive missing months into fetch ranges clipped to [start, end]."""
    ranges, group = [], []
    for m in missing:
        if group:
            prev_end = month_bounds(group[-1])[1]
            if month_bounds(m)[0] != prev_end + dt.timedelta(days=1):
                ranges.append(group)
                group = []
        group.append(m)
    if group:
        ranges.append(group)
    return [(max(start, month_bounds(g[0])[0]), min(end, month_bounds(g[-1])[1]), g) for g in ranges]


def _fetch_range(task):
    sid, s, e, _months = task
    data = get_json(_url(sid, s, e))
    days = {}
    for item in (data or {}).get("items", []):
        ts = item["timestamp"]
        days["%s-%s-%s" % (ts[0:4], ts[4:6], ts[6:8])] = int(item["views"])
    return days


def fetch_daily(cache: Cache, sids: List[str], start: dt.date, end: dt.date,
                label: str = "series") -> Dict[str, np.ndarray]:
    """Return {sid: daily views array covering start..end inclusive}."""
    start = max(start, DATA_START)
    today = dt.date.today()
    months = months_in(start, end)
    tasks = []
    for sid in dict.fromkeys(sids):
        covered = cache.covered_months(sid, months)
        missing = [m for m in months if m not in covered]
        for s, e, group in _missing_ranges(missing, start, end):
            tasks.append((sid, s, e, group))
    if tasks:
        log("wikitrends: downloading %d %s range(s) from Wikimedia (cached afterwards)..." % (len(tasks), label))
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as pool:
            results = list(pool.map(_fetch_range, tasks))
        for (sid, s, e, group), days in zip(tasks, results):
            complete = [m for m in group if _is_final(m, today)
                        and month_bounds(m)[0] >= s and month_bounds(m)[1] <= e]
            cache.store(sid, days, complete)

    n = (end - start).days + 1
    index = {(start + dt.timedelta(days=i)).isoformat(): i for i in range(n)}
    out = {}
    for sid in dict.fromkeys(sids):
        arr = np.zeros(n, dtype=float)
        for day, views in cache.load_days(sid, start.isoformat(), end.isoformat()).items():
            i = index.get(day)
            if i is not None:
                arr[i] = views
        out[sid] = arr
    return out
