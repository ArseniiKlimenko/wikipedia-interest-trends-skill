"""Second demand signals next to Wikipedia: Google Trends and the Apple App Store.

Google Trends
  * The topic is the Wikidata item's Freebase ID (P646), which Google Trends accepts as a
    language-independent "topic", so the same concept is measured in each country. Without a
    Freebase ID the local article title is used as a search term (less comparable).
  * Only with --trends: fetched from Google Trends' public web endpoints. They are unofficial,
    rate-limited, and automated querying may conflict with Google's terms of service, so the skill
    sends a few cached requests (7 days) with pauses. The sanctioned alternative is a CSV export from
    trends.google.com passed with --trends-csv lang=path; the same growth metric is computed.
  * A basket of several Wikidata items is represented by the Freebase topic of its first item;
    the output says which topic was used.
  * Countries: those with >= 15% of the language edition's readers (from the analysis' country
    data, at most 3), else the language's main home country; override with --geo.
  * Values are an index (0-100) relative to the peak in the requested window, so only changes
    within one series are meaningful: last 12 months vs the previous 12, with a block-bootstrap
    95% interval, compared with the Wikipedia direction for the same language.
App Store
  * Apple's official iTunes Search API (no key): apps returned for a keyword in a country store.
    Supply and traction proxies: number of apps, ratings of the top apps, how many were updated in
    the last 12 months, and how many top apps are recent entrants. No search-volume data exists in
    this API, so this measures competition and category activity, not demand directly.
Language edition -> country uses the main home country of the language (override with --geo).
"""
from __future__ import annotations

import csv
import datetime as dt
import http.cookiejar
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from . import analysis as an, graph, stats, wiki
from .cache import Cache
from .net import PLAIN_USER_AGENT, log
from .text import HOME_COUNTRIES

TRENDS = "https://trends.google.com/trends"
# App Store genres that are almost never the product for a knowledge topic; apps from them count only
# when the keyword is in the app's name
GENERIC_GENRES = {"Social Networking", "Music", "Photo & Video", "Entertainment", "Shopping", "Games", "Finance",
                  "Travel", "Navigation", "Food & Drink", "Business", "Weather", "Developer Tools", "Sports",
                  "Graphics & Design", "News"}
ITUNES = "https://itunes.apple.com/search"


class SignalError(RuntimeError):
    pass


# ---- Google Trends -----------------------------------------------------------------------------
class _Trends:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.warm = False

    def _get(self, url: str) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": PLAIN_USER_AGENT, "Accept-Language": "en-US"})
        for attempt in range(3):
            try:
                with self.opener.open(req, timeout=40) as r:
                    return r.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt < 2:
                    wait = 8 * (attempt + 1)
                    log("wikitrends: Google Trends rate limit; waiting %ds" % wait)
                    time.sleep(wait)
                    continue
                raise SignalError("Google Trends HTTP %d" % exc.code)
            except (urllib.error.URLError, OSError) as exc:
                raise SignalError("Google Trends unreachable (%s)" % exc)
        raise SignalError("Google Trends rate-limited")

    @staticmethod
    def _json(body: str) -> dict:
        i = body.find("{")
        if i < 0:
            raise SignalError("unexpected Google Trends response")
        return json.loads(body[i:])

    def timeline(self, keyword: str, geo: str, start: dt.date, end: dt.date) -> List[Tuple[str, float]]:
        if not self.warm:
            self._get("%s/?geo=%s" % (TRENDS, geo))
            self.warm = True
        req = {"comparisonItem": [{"keyword": keyword, "geo": geo,
                                   "time": "%s %s" % (start.isoformat(), end.isoformat())}],
               "category": 0, "property": ""}
        explore = self._json(self._get("%s/api/explore?%s" % (TRENDS, urllib.parse.urlencode(
            {"hl": "en-US", "tz": "0", "req": json.dumps(req)}))))
        widget = next((w for w in explore.get("widgets", []) if w.get("id") == "TIMESERIES"), None)
        if not widget:
            raise SignalError("no time series for %s in %s" % (keyword, geo))
        data = self._json(self._get("%s/api/widgetdata/multiline?%s" % (TRENDS, urllib.parse.urlencode(
            {"hl": "en-US", "tz": "0", "req": json.dumps(widget["request"]), "token": widget["token"]}))))
        out = []
        for p in data.get("default", {}).get("timelineData", []):
            if p.get("isPartial"):
                continue
            day = dt.datetime.utcfromtimestamp(int(p["time"])).date().isoformat()
            out.append((day, float(p["value"][0])))
        return out


_client: Optional[_Trends] = None


def trends_timeline(cache: Cache, keyword: str, geo: str, start: dt.date, end: dt.date) -> List[Tuple[str, float]]:
    global _client
    key = "gt|%s|%s|%s|%s" % (keyword, geo, start, end)
    hit = cache.kv_get(key, ttl_days=7)
    if hit is not None:
        return [tuple(x) for x in hit]
    _client = _client or _Trends()
    rows = _client.timeline(keyword, geo, start, end)
    cache.kv_set(key, rows)
    time.sleep(1.5)  # be gentle with an unofficial endpoint
    return rows


def parse_trends_csv(path: str) -> List[Tuple[str, float]]:
    """Read a Google Trends 'multiTimeline.csv' export (first data column)."""
    rows = []
    with open(path, encoding="utf-8-sig") as fh:
        for rec in csv.reader(fh):
            if len(rec) < 2 or not re.match(r"^\d{4}-\d{2}(-\d{2})?$", rec[0].strip()):
                continue
            v = rec[1].strip().replace("<1", "0.5")
            try:
                day = rec[0].strip() if len(rec[0].strip()) == 10 else rec[0].strip() + "-01"
                rows.append((day, float(v)))
            except ValueError:
                continue
    if not rows:
        raise SignalError("no data rows found in %s" % path)
    return rows


def series_growth(points: List[Tuple[str, float]], recent: Tuple[str, str], previous: Tuple[str, str]) -> Optional[dict]:
    """Last-12 vs previous-12 change of an index series (weekly or monthly points)."""
    def pick(lo, hi):
        return np.array([v for d, v in points if lo <= d[:7] <= hi], dtype=float)
    prev, rec = pick(*previous), pick(*recent)
    if len(prev) < 3 or len(rec) < 3 or prev.sum() <= 0:
        return None
    n = min(len(prev), len(rec))
    prev, rec = prev[-n:], rec[:n] if len(rec) > n else rec
    block = 4 if n >= 30 else 2
    g = stats.ratio_growth(prev, np.ones_like(prev), rec, np.ones_like(rec), block=block)
    if not g:
        return None
    return {"growth": g["point"], "lo": g["lo"], "hi": g["hi"],
            "direction": stats.direction_of(g["lo"], g["hi"], g["point"]), "points": len(points),
            "resolution": "weekly" if n >= 30 else "monthly"}


def freebase_ids(cache: Cache, qids: List[str]) -> Dict[str, str]:
    if not qids:
        return {}
    rows = graph.sparql(cache, "SELECT ?item ?mid WHERE { VALUES ?item { %s } ?item wdt:P646 ?mid }" %
                        " ".join("wd:" + q for q in qids))
    return {r["item"]: r["mid"] for r in rows}


# ---- App Store ---------------------------------------------------------------------------------------
def relevance_patterns(term: str, also: Optional[List[str]] = None) -> List[re.Pattern]:
    """Word-start patterns for the keyword and extra words (5-letter stems; short words match whole words,
    so "post" does not match "InPost")."""
    words = " ".join([term] + list(also or []))
    return [re.compile(r"\b%s" % re.escape(w[:5].lower()) if len(w) >= 5 else r"\b%s\b" % re.escape(w.lower()))
            for w in re.findall(r"\w+", words) if len(w) >= 3] or [re.compile(re.escape(term.lower()))]


def app_is_relevant(app: dict, pats: List[re.Pattern]) -> bool:
    """Keyword in the app name, or in the description for apps outside generic genres (social, music, games...)."""
    name = (app.get("trackName") or "").lower()
    if any(p.search(name) for p in pats):
        return True
    if app.get("primaryGenreName") in GENERIC_GENRES:
        return False
    return any(p.search((app.get("description") or "").lower()) for p in pats)


def appstore_search(cache: Cache, term: str, country: str, limit: int = 50, also: Optional[List[str]] = None) -> List[dict]:
    """Apps for `term` in a country store. `also`: extra words (e.g. the English topic name) that
    also count as relevant, because many store listings are not translated."""
    key = "itunes4|%s|%s|%d|%s" % (country.lower(), term.lower(), limit, "|".join(also or []).lower())
    hit = cache.kv_get(key, ttl_days=7)
    if hit is not None:
        return hit
    url = ITUNES + "?" + urllib.parse.urlencode({"term": term, "country": country.lower(), "entity": "software",
                                                  "limit": limit})
    req = urllib.request.Request(url, headers={"User-Agent": PLAIN_USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429) and attempt < 2:
                time.sleep(10 * (attempt + 1))
                continue
            raise SignalError("App Store search HTTP %d" % exc.code)
        except (urllib.error.URLError, OSError) as exc:
            raise SignalError("App Store search unreachable (%s)" % exc)
    pats = relevance_patterns(term, also)
    apps = [{"name": a.get("trackName"), "ratings": int(a.get("userRatingCount") or 0),
             "relevant": app_is_relevant(a, pats),
             "rating": a.get("averageUserRating"), "released": (a.get("releaseDate") or "")[:10],
             "updated": (a.get("currentVersionReleaseDate") or "")[:10], "genre": a.get("primaryGenreName"),
             "price": a.get("price"), "seller": a.get("sellerName")} for a in data.get("results", [])]
    cache.kv_set(key, apps)
    time.sleep(3.0)  # Apple allows roughly 20 calls per minute
    return apps


def appstore_metrics(apps: List[dict], today: Optional[dt.date] = None, top: int = 25) -> dict:
    """Metrics over apps whose name or description mentions the keyword (search results can drift)."""
    today = today or dt.date.today()
    found = len(apps)
    apps = [a for a in apps if a.get("relevant", True)]
    year_ago = (today - dt.timedelta(days=365)).isoformat()
    two_years = (today - dt.timedelta(days=730)).isoformat()
    top_apps = sorted(apps, key=lambda a: -a["ratings"])[:top]
    ratings = [a["ratings"] for a in top_apps]
    total = sum(ratings)
    warning = None
    if found == 0 or not apps:
        warning = ("no relevant apps for this keyword: this reflects the wording (store listings are often in "
                   "English or use other words), not missing demand; try another --keyword before concluding anything")
    elif found >= 10 and len(apps) / found < 0.5:
        warning = "most search results were unrelated apps (%d of %d kept), so these numbers are rough" % (len(apps), found)
    return {
        "warning": warning,
        "apps_found": found,
        "apps_relevant": len(apps),
        "top_ratings_total": total,
        "top_ratings_median": float(np.median(ratings)) if ratings else 0.0,
        "updated_last_12m": sum(1 for a in top_apps if a["updated"] >= year_ago),
        "new_last_24m": sum(1 for a in top_apps if a["released"] >= two_years),
        "new_ratings_share": (sum(a["ratings"] for a in top_apps if a["released"] >= two_years) / total) if total else 0.0,
        "leader_share": (max(ratings) / total) if total else 0.0,
        "top": [{k: a[k] for k in ("name", "ratings", "rating", "released")} for a in top_apps[:5]],
        "top_n": len(top_apps),
    }


# ---- orchestration --------------------------------------------------------------------------------------
def _kv_list(items: List[str], what: str) -> Dict[str, str]:
    out = {}
    for it in items or []:
        if "=" not in it:
            raise an.UsageError("%s must look like lang=value (got %r)" % (what, it))
        k, v = it.split("=", 1)
        out[k.strip().lower()] = v.strip()
    return out


def _agreement(wiki_dir: str, other_dir: str) -> str:
    if other_dir in ("unclear",) or wiki_dir in ("unclear",):
        return "unclear"
    if wiki_dir == other_dir:
        return "agree" if wiki_dir != "flat" else "both flat"
    if "flat" in (wiki_dir, other_dir):
        return "partly (one shows no clear change)"
    return "DISAGREE"


def default_geos(a: dict, lang: str) -> List[str]:
    """Countries to check for a language edition: >= 15% of its readers (max 3), else its home country."""
    rows = (a.get("geo") or {}).get(lang) or []
    big = [r["country"] for r in rows if r.get("share", 0) >= 0.15][:3]
    return big or (HOME_COUNTRIES.get(lang) or ["US"])[:1]


def run(analysis_dir: str, keywords: Optional[List[str]] = None, geos: Optional[List[str]] = None,
        trends_csv: Optional[List[str]] = None, use_trends: bool = False, use_appstore: bool = True) -> dict:
    cache = Cache()
    a = an.load_json(Path(analysis_dir) / "analysis.json")
    kw = _kv_list(keywords, "--keyword")
    gmap = {k: [c.strip().upper() for c in v.split(",") if c.strip()] for k, v in _kv_list(geos, "--geo").items()}
    csvs = _kv_list(trends_csv, "--trends-csv")
    period = a["period"]
    start, end = dt.date.fromisoformat(period["start"]), dt.date.fromisoformat(period["end"])
    qids = [it for t in a["topics"] for it in t["items"] if it.startswith("Q")]
    mids = freebase_ids(cache, qids) if use_trends else {}
    ents = wiki.get_entities(cache, qids) if qids else {}
    out = {"period": period, "rows": [], "errors": [], "notes": []}
    trends_down = False
    for t in a["topics"]:
        first = next((it for it in t["items"] if it.startswith("Q")), None)
        mid = mids.get(first) if first else None
        if use_trends and mid and len(t["items"]) > 1:
            out["notes"].append("Google Trends for '%s' uses one topic, %s (%s = %s), for the whole basket of %d "
                                "items; the other items are not in the Trends series."
                                % (t["label"], mid, first, wiki.label_of(ents.get(first, {}), ["en"]) if ents.get(first)
                                   else first, len(t["items"])))
        for lang in a["params"]["langs"]:
            s = next((x for x in a["series"] if x["topic"] == t["label"] and x["lang"] == lang), None)
            wiki_dir = s["confidence"]["direction"] if s else "unclear"
            ent = ents.get(first, {}) if first else {}
            title = (ent.get("sitelinks") or {}).get(wiki.site_of(lang))
            local = re.sub(r"\s*\(.*?\)\s*$", "", title) if title else None
            term = kw.get(lang) or local or t["label"]
            for geo in gmap.get(lang) or default_geos(a, lang):
                row = {"topic": t["label"], "lang": lang, "geo": geo, "wiki_growth": s.get("growth_rel") if s else None,
                       "wiki_direction": wiki_dir, "trends": None, "appstore": None}
                if lang in csvs:
                    try:
                        g = series_growth(parse_trends_csv(csvs[lang]), tuple(period["recent"]), tuple(period["previous"]))
                        row["trends"] = dict(g or {}, source="CSV export", query=csvs[lang])
                    except (SignalError, OSError) as exc:
                        out["errors"].append("%s %s trends CSV: %s" % (lang, geo, exc))
                elif use_trends and not trends_down:
                    query = mid or term
                    try:
                        pts = trends_timeline(cache, query, geo, start, end)
                        g = series_growth(pts, tuple(period["recent"]), tuple(period["previous"]))
                        row["trends"] = dict(g or {}, source="topic %s" % mid if mid else "search term",
                                             query=query)
                    except SignalError as exc:
                        out["errors"].append("Google Trends unavailable (%s). Export the chart as CSV from "
                                             "trends.google.com and pass --trends-csv %s=path" % (exc, lang))
                        trends_down = True
                if row["trends"] and row["trends"].get("direction"):
                    row["agreement"] = _agreement(wiki_dir, row["trends"]["direction"])
                if use_appstore:
                    try:
                        en = (ent.get("labels") or {}).get("en")
                        apps = appstore_search(cache, term, geo, also=[en] if en and en.lower() != term.lower() else None)
                        row["appstore"] = dict(appstore_metrics(apps), term=term)
                        if row["appstore"].get("warning"):
                            out["errors"].append("App Store %s '%s': %s" % (geo, term, row["appstore"]["warning"]))
                    except SignalError as exc:
                        out["errors"].append("App Store %s: %s" % (geo, exc))
                out["rows"].append(row)
    an.save_json(out, Path(analysis_dir) / "signals.json")
    md = signals_md(out)
    (Path(analysis_dir) / "signals.md").write_text(md, encoding="utf-8")
    return out


def _pct(x):
    return "n/a" if x is None else "%+.0f%%" % (x * 100)


def signals_md(o: dict) -> str:
    p = o["period"]
    L = ["# Second demand signals", "",
         "Same comparison as Wikipedia: %s..%s vs %s..%s." % (p["recent"][0], p["recent"][1], p["previous"][0],
                                                              p["previous"][1]), "",
         "## Google Trends vs Wikipedia (relative growth)", "",
         "| Topic | Lang -> country | Google Trends change [95% CI] | Query | Wikipedia | Agreement |",
         "|---|---|---|---|---|---|"]
    for r in o["rows"]:
        tr = r.get("trends") or {}
        gt = "%s [%s, %s]" % (_pct(tr.get("growth")), _pct(tr.get("lo")), _pct(tr.get("hi"))) if tr.get("growth") is not None else "n/a"
        L.append("| %s | %s -> %s | %s | %s | %s (%s) | %s |" % (
            r["topic"], r["lang"], r["geo"], gt, tr.get("source", "-"), _pct(r.get("wiki_growth")),
            r["wiki_direction"], r.get("agreement", "-")))
    if o.get("notes"):
        L += [""] + ["Note: " + n for n in o["notes"]]
    if not any(r.get("trends") for r in o["rows"]):
        L += ["", "Google Trends was not queried (add --trends for the unofficial endpoint, or --trends-csv "
                  "lang=path with an export from trends.google.com)."]
    L += ["", "## App Store (%s store search; competition and traction, not search volume)" % "iTunes", "",
          "| Topic | Country | Keyword | Relevant / found | Top-25 ratings | Updated in 12 mo | New (<=24 mo) in top 25 | Leader share | Top apps |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in o["rows"]:
        ap = r.get("appstore")
        if not ap:
            continue
        L.append("| %s | %s | %s | %d / %d | %s | %d/%d | %d (%.0f%% of ratings) | %.0f%% | %s |" % (
            r["topic"], r["geo"], ap["term"], ap.get("apps_relevant", ap["apps_found"]), ap["apps_found"],
            "{:,}".format(ap["top_ratings_total"]),
            ap["updated_last_12m"], ap["top_n"], ap["new_last_24m"], ap["new_ratings_share"] * 100,
            ap["leader_share"] * 100, "; ".join("%s (%s)" % (x["name"], "{:,}".format(x["ratings"])) for x in ap["top"][:3])))
    L += ["", "How to read:",
          "- Agreement: both signals moving the same way makes the conclusion much stronger. DISAGREE often means "
          "readers moved from Wikipedia to search/AI answers (Trends up, Wikipedia down) or a Wikipedia-specific "
          "effect; say so instead of picking one.",
          "- Google Trends is an index relative to its own peak (0-100); compare directions, not levels, across countries.",
          "- App Store numbers describe competition: many rated apps = proven demand but crowded; few recent entrants "
          "with a large rating share = hard to break in; many new apps gaining ratings = open, moving market.",
          "- The App Store API has no search volume; keyword results depend on the exact wording (try the local phrase)."]
    if o["errors"]:
        L += ["", "## Problems (read before using these numbers)"] + ["- " + e for e in dict.fromkeys(o["errors"])]
    return "\n".join(L) + "\n"
