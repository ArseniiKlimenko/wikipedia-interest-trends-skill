"""Wikidata / MediaWiki metadata: topic search, cross-language titles, redirects, geography."""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from .cache import Cache
from .net import MAX_CONCURRENCY, get_json

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
PAGEVIEWS_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews"
_SITE_EXCEPTIONS = {"be-tarask": "be_x_oldwiki"}
QID_RE = re.compile(r"^Q\d+$")


def site_of(lang: str) -> str:
    return _SITE_EXCEPTIONS.get(lang, lang.replace("-", "_") + "wiki")


def project_of(lang: str) -> str:
    return "%s.wikipedia" % lang


def action_api(lang: str) -> str:
    return "https://%s.wikipedia.org/w/api.php" % lang


def _chunks(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# ---- Wikidata ------------------------------------------------------------------------
def search_entities(cache: Cache, query: str, lang: str = "en", limit: int = 8) -> List[dict]:
    key = "wdsearch|%s|%d|%s" % (lang, limit, query.strip().lower())
    hit = cache.kv_get(key, ttl_days=30)
    if hit is not None:
        return hit
    data = get_json(WIKIDATA_API, {"action": "wbsearchentities", "search": query, "language": lang,
                                   "uselang": lang, "type": "item", "limit": limit, "format": "json"},
                    allow_404=False) or {}
    out = [{"id": r["id"], "label": r.get("label", ""), "description": r.get("description", "")}
           for r in data.get("search", [])]
    cache.kv_set(key, out)
    return out


def get_entities(cache: Cache, qids: List[str]) -> Dict[str, dict]:
    """qid -> {labels, descriptions, sitelinks} (compact); missing items get {'missing': True}."""
    result, todo = {}, []
    for q in dict.fromkeys(qids):
        hit = cache.kv_get("wdent|" + q, ttl_days=30)
        if hit is None:
            todo.append(q)
        else:
            result[q] = hit
    for batch in _chunks(todo, 50):
        data = get_json(WIKIDATA_API, {"action": "wbgetentities", "ids": "|".join(batch),
                                       "props": "labels|descriptions|sitelinks", "format": "json"},
                        allow_404=False) or {}
        entities = data.get("entities", {})
        for q in batch:
            ent = entities.get(q)
            if ent is None:  # merged item: the API keys it by the target id
                ent = next((e for e in entities.values() if e.get("id") and q in (e.get("redirects") or {}).values()), None)
            if not ent or "missing" in ent:
                compact = {"missing": True}
            else:
                compact = {
                    "id": ent.get("id", q),
                    "labels": {k: v["value"] for k, v in ent.get("labels", {}).items()},
                    "descriptions": {k: v["value"] for k, v in ent.get("descriptions", {}).items()},
                    "sitelinks": {k: v["title"] for k, v in ent.get("sitelinks", {}).items()},
                }
            cache.kv_set("wdent|" + q, compact)
            result[q] = compact
    return result


def label_of(entity: dict, langs=("en",)) -> str:
    labels = entity.get("labels", {})
    for lang in list(langs) + ["en"]:
        if lang in labels:
            return labels[lang]
    return next(iter(labels.values()), entity.get("id", "?"))


def wikipedia_sitelink_count(entity: dict) -> int:
    return sum(1 for s in entity.get("sitelinks", {}) if s.endswith("wiki") and s not in
               ("commonswiki", "specieswiki", "metawiki", "wikidatawiki", "mediawikiwiki", "sourceswiki"))


# ---- MediaWiki -----------------------------------------------------------------------
def titles_info(cache: Cache, lang: str, titles: List[str]) -> Dict[str, dict]:
    """Normalise titles (follow redirects) -> {input: {'title': canonical or None, 'qid': ...}}."""
    out, todo = {}, []
    for t in dict.fromkeys(titles):
        hit = cache.kv_get("title|%s|%s" % (lang, t), ttl_days=30)
        if hit is None:
            todo.append(t)
        else:
            out[t] = hit
    for batch in _chunks(todo, 50):
        data = get_json(action_api(lang), {"action": "query", "titles": "|".join(batch), "redirects": 1,
                                           "prop": "pageprops", "ppprop": "wikibase_item",
                                           "format": "json", "formatversion": 2}, allow_404=False) or {}
        q = data.get("query", {})
        norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
        redir = {r["from"]: r["to"] for r in q.get("redirects", [])}
        pages = {p["title"]: p for p in q.get("pages", [])}
        for t in batch:
            final = norm.get(t, t)
            final = redir.get(final, final)
            page = pages.get(final)
            if not page or page.get("missing") or page.get("invalid"):
                info = {"title": None, "qid": None}
            else:
                info = {"title": page["title"], "qid": (page.get("pageprops") or {}).get("wikibase_item")}
            cache.kv_set("title|%s|%s" % (lang, t), info)
            out[t] = info
    return out


def search_wiki(cache: Cache, lang: str, query: str, limit: int = 4) -> List[dict]:
    """Full-text search inside one Wikipedia (finds articles not linked to the Wikidata item)."""
    key = "wsearch|%s|%d|%s" % (lang, limit, query.strip().lower())
    hit = cache.kv_get(key, ttl_days=30)
    if hit is not None:
        return hit
    data = get_json(action_api(lang), {"action": "query", "list": "search", "srsearch": query, "srnamespace": 0,
                                       "srlimit": limit, "srprop": "", "format": "json", "formatversion": 2},
                    allow_404=False) or {}
    rows = [{"title": r["title"]} for r in data.get("query", {}).get("search", [])]
    cache.kv_set(key, rows)
    return rows


def get_redirects(cache: Cache, lang: str, titles: List[str]) -> Dict[str, List[str]]:
    """title -> list of main-namespace redirect titles pointing at it."""
    out, todo = {}, []
    for t in dict.fromkeys(titles):
        hit = cache.kv_get("redir|%s|%s" % (lang, t), ttl_days=30)
        if hit is None:
            todo.append(t)
        else:
            out[t] = hit
    for batch in _chunks(todo, 50):
        found = {t: [] for t in batch}
        params = {"action": "query", "titles": "|".join(batch), "prop": "redirects", "rdnamespace": 0,
                  "rdlimit": "max", "rdprop": "title", "format": "json", "formatversion": 2}
        cont = {}
        for _ in range(20):
            data = get_json(action_api(lang), dict(params, **cont), allow_404=False) or {}
            for page in data.get("query", {}).get("pages", []):
                if page["title"] in found:
                    found[page["title"]].extend(r["title"] for r in page.get("redirects", []))
            if "continue" not in data:
                break
            cont = data["continue"]
        for t, reds in found.items():
            cache.kv_set("redir|%s|%s" % (lang, t), reds)
            out[t] = reds
    return out


def top_countries(cache: Cache, lang: str, year: int, month: int) -> List[dict]:
    """Approximate share of a language edition's views by country (one month)."""
    key = "geo|%s|%04d-%02d" % (lang, year, month)
    hit = cache.kv_get(key, ttl_days=None)
    if hit is not None:
        return hit
    data = get_json("%s/top-by-country/%s/all-access/%04d/%02d" % (PAGEVIEWS_API, project_of(lang), year, month))
    rows = []
    if data and data.get("items"):
        countries = data["items"][0].get("countries", [])
        total = float(sum(c.get("views_ceil") or 0 for c in countries)) or 1.0
        rows = [{"country": c["country"], "share": round((c.get("views_ceil") or 0) / total, 4)}
                for c in countries[:8]]
    cache.kv_set(key, rows)
    return rows


def _collect(lang: str, params: dict, extract, max_calls: int = 10) -> list:
    out, cont = [], {}
    for _ in range(max_calls):
        data = get_json(action_api(lang), dict(params, **cont), allow_404=False) or {}
        out += extract(data)
        if "continue" not in data:
            break
        cont = data["continue"]
    return out


def linked_articles(cache: Cache, lang: str, title: str, days: int = 60, mutual: bool = True) -> List[dict]:
    """Neighbouring articles of `title` with their views over the last `days` days and QIDs.

    With mutual=True only articles that link to the seed AND are linked from it are kept:
    this drops generic links (cities, institutions) and keeps topical neighbours.
    """
    key = "links|%s|%s|%d|%d" % (lang, title, days, mutual)
    hit = cache.kv_get(key, ttl_days=7)
    if hit is not None:
        return hit
    base = {"format": "json", "formatversion": 2}
    out_links = _collect(lang, dict(base, action="query", prop="links", titles=title, plnamespace=0, pllimit="max"),
                         lambda d: [l["title"] for p in d.get("query", {}).get("pages", []) for l in p.get("links", [])])
    candidates = list(dict.fromkeys(out_links))
    if mutual:
        back = set(_collect(lang, dict(base, action="query", list="backlinks", bltitle=title, blnamespace=0,
                                       bllimit="max", blfilterredir="nonredirects"),
                            lambda d: [b["title"] for b in d.get("query", {}).get("backlinks", [])], max_calls=10))
        both = [t for t in candidates if t in back]
        if len(both) >= 5:
            candidates = both
    rows = {t: {"title": t, "views": None, "qid": None} for t in candidates}
    for batch in _chunks(candidates, 50):
        def extract(d):
            for p in d.get("query", {}).get("pages", []):
                r = rows.get(p["title"])
                if r is None:
                    continue
                if p.get("pageprops", {}).get("wikibase_item"):
                    r["qid"] = p["pageprops"]["wikibase_item"]
                if p.get("pageviews") is not None:
                    r["views"] = int(sum(v or 0 for v in p["pageviews"].values()))
            return []
        _collect(lang, dict(base, action="query", titles="|".join(batch), prop="pageviews|pageprops",
                            ppprop="wikibase_item", pvipdays=days), extract, max_calls=10)
    result = sorted(rows.values(), key=lambda r: -(r["views"] or 0))
    cache.kv_set(key, result)
    return result


def parallel_map(fn, items):
    items = list(items)
    if len(items) <= 1:
        return [fn(i) for i in items]
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as pool:
        return list(pool.map(fn, items))
