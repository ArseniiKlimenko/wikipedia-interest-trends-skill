"""Automatic article baskets from the Wikidata graph and the article link graph.

`expand(seed)` collects candidate sub-topics of a Wikidata item from two sources:
  * the Wikidata graph: items that are a subclass / part / facet / instance of the seed, or that
    the seed "has part" or "studies" (P279, P361, P1269, P31, P527, P2578);
  * the link graph: articles linked both ways with the seed article in the first language.
Link neighbours are kept as on-topic only when Wikidata confirms that they are a kind of the seed
or of something the seed studies (P31/P279* path), which drops cities, universities and people
that merely co-occur with the topic. Candidates are ranked by recent views and checked for article
coverage in every requested language, so the suggested basket compares like with like.
"""
from __future__ import annotations

import hashlib
from typing import Dict, List, Optional

from . import wiki
from .cache import Cache
from .net import ApiError, get_json, log

SPARQL = "https://query.wikidata.org/sparql"
RELATIONS = [  # (property, label, direction): "in" = ?item P seed, "out" = seed P ?item
    ("P279", "subclass of it", "in"), ("P361", "part of it", "in"), ("P1269", "facet of it", "in"),
    ("P31", "instance of it", "in"), ("P527", "it has part", "out"), ("P2578", "it studies", "out"),
]
BROADER = [("P279", "broader class", "out"), ("P361", "whole it is part of", "out")]


def sparql(cache: Cache, query: str, ttl_days: float = 30) -> List[Dict[str, str]]:
    key = "sparql|" + hashlib.sha1(query.encode("utf-8")).hexdigest()
    hit = cache.kv_get(key, ttl_days=ttl_days)
    if hit is not None:
        return hit
    data = get_json(SPARQL, {"query": query, "format": "json"}, allow_404=False, timeout=45, retries=2) or {}
    rows = [{k: v["value"].rsplit("/", 1)[-1] if v.get("type") == "uri" else v["value"] for k, v in b.items()}
            for b in data.get("results", {}).get("bindings", [])]
    cache.kv_set(key, rows)
    return rows


def graph_neighbours(cache: Cache, qid: str, limit: int = 150, relations=RELATIONS) -> List[dict]:
    """Items directly related to `qid` (two small queries: incoming and outgoing properties)."""
    labels = {(p, d): lab for p, lab, d in relations}
    out, seen = [], set()
    for direction in ("in", "out"):
        props = [p for p, _l, d in relations if d == direction]
        if not props:
            continue
        values = " ".join("wdt:" + p for p in props)
        pattern = "?item ?p wd:%s ." % qid if direction == "in" else "wd:%s ?p ?item ." % qid
        q = ("SELECT ?item ?p ?links WHERE { VALUES ?p { %s } %s ?item wikibase:sitelinks ?links . "
             "FILTER(?links >= 3) } ORDER BY DESC(?links) LIMIT %d" % (values, pattern, limit))
        try:
            rows = sparql(cache, q)
        except ApiError as exc:
            log("wikitrends: Wikidata graph query failed (%s)" % exc)
            rows = []
        for r in rows:
            if r["item"] in seen or not r["item"].startswith("Q"):
                continue
            seen.add(r["item"])
            out.append({"qid": r["item"], "relation": labels.get((r["p"], direction), r["p"]),
                        "sitelinks": int(r["links"])})
    out.sort(key=lambda r: -r["sitelinks"])
    return out[:limit]


def studied_classes(cache: Cache, qid: str) -> List[str]:
    try:
        rows = sparql(cache, "SELECT ?t WHERE { wd:%s wdt:P2578 ?t }" % qid)
    except ApiError:
        rows = []
    return [r["t"] for r in rows if r["t"].startswith("Q")]


def on_topic(cache: Cache, qids: List[str], targets: List[str], depth: int = 4, loose: bool = False) -> set:
    """QIDs that are a target, or whose instance-of/subclass-of chain reaches one within `depth` hops.

    After the first hop only subclass-of is followed, unless `loose` (then instance-of too, which
    catches e.g. "2030 World Cup" -> "FIFA World Cup" -> instance of "recurring sporting event").
    """
    tset = set(targets)
    ok = set(q for q in qids if q in tset)
    rest = [q for q in dict.fromkeys(qids) if q not in ok]
    step = "wdt:P31|wdt:P279" if loose else "wdt:P279"
    chain = "?item wdt:P31|wdt:P279 ?c1 ."
    for i in range(2, depth + 1):
        chain += " OPTIONAL { ?c%d %s ?c%d ." % (i - 1, step, i)
    chain += " }" * (depth - 1)
    for i in range(0, len(rest), 40):
        chunk = rest[i:i + 40]
        q = "SELECT ?item %s WHERE { VALUES ?item { %s } %s }" % (
            " ".join("?c%d" % k for k in range(1, depth + 1)), " ".join("wd:" + x for x in chunk), chain)
        try:
            for r in sparql(cache, q):
                if any(r.get("c%d" % k) in tset for k in range(1, depth + 1)):
                    ok.add(r["item"])
        except ApiError as exc:
            log("wikitrends: topic check skipped for %d items (%s)" % (len(chunk), exc))
    return ok


BROAD_FACTOR = 3.0  # sub-topics with > 3x the seed article's views are left out of the suggested basket


def expand(cache: Cache, seed: str, langs: List[str], limit: int = 6, days: int = 60) -> dict:
    ents = wiki.get_entities(cache, [seed])
    ent = ents.get(seed, {})
    if not ent or ent.get("missing"):
        raise ValueError("Wikidata item %s not found" % seed)
    seed_label = wiki.label_of(ent, [langs[0], "en"])
    lang0 = next((l for l in langs if wiki.site_of(l) in ent["sitelinks"]), None)
    title0 = ent["sitelinks"].get(wiki.site_of(lang0)) if lang0 else None

    cands: Dict[str, dict] = {}
    for g in graph_neighbours(cache, seed):
        cands[g["qid"]] = {"qid": g["qid"], "sources": [g["relation"]], "sitelinks": g["sitelinks"]}
    broader = graph_neighbours(cache, seed, limit=10, relations=BROADER)

    link_rows = wiki.linked_articles(cache, lang0, title0, days=days, mutual=True) if title0 else []
    link_qids = [r["qid"] for r in link_rows if r.get("qid")]
    targets = [seed] + studied_classes(cache, seed)
    verified = on_topic(cache, link_qids[:150], targets) if link_qids else set()
    for q in link_qids[:150]:
        c = cands.setdefault(q, {"qid": q, "sources": [], "sitelinks": None})
        c["sources"].append("linked both ways" + (" + kind of topic" if q in verified else " (unverified)"))

    cands.pop(seed, None)
    entities = wiki.get_entities(cache, list(cands))
    titles0 = {}
    for q, c in cands.items():
        e = entities.get(q, {})
        if e.get("missing"):
            c["drop"] = True
            continue
        c["label"] = wiki.label_of(e, [langs[0], "en"])
        c["titles"] = {l: e.get("sitelinks", {}).get(wiki.site_of(l)) for l in langs}
        c["coverage"] = sum(1 for v in c["titles"].values() if v)
        c["sitelinks"] = c["sitelinks"] or wiki.wikipedia_sitelink_count(e)
        c["verified"] = any(not s.startswith("linked") or "kind of topic" in s for s in c["sources"])
        if lang0 and c["titles"].get(lang0):
            titles0[c["titles"][lang0]] = q
    views = wiki.recent_views(cache, lang0, list(titles0), days) if lang0 and titles0 else {}
    for title, q in titles0.items():
        cands[q]["views"] = (views.get(title) or {}).get("views") or 0
    rows = [c for c in cands.values() if not c.get("drop")]
    for c in rows:
        c.setdefault("views", 0)
    rows.sort(key=lambda c: (not c["verified"], -(c["views"] or 0)))

    seed_views = 0
    if lang0 and title0:
        seed_views = (wiki.recent_views(cache, lang0, [title0], days).get(title0) or {}).get("views") or 0
    for c in rows:  # far more popular than the subject itself = general-interest page (e.g. "Earth" for astronomy)
        c["broad"] = bool(seed_views and (c["views"] or 0) > BROAD_FACTOR * seed_views)
    full = [c for c in rows if c["verified"] and c["coverage"] == len(langs) and c["views"] > 0 and not c["broad"]]
    basket = [seed] + [c["qid"] for c in full[:limit]]
    basket_views = seed_views + sum(c["views"] or 0 for c in full[:limit])
    heavy = [{"qid": c["qid"], "label": c["label"], "share": (c["views"] or 0) / basket_views}
             for c in full[:limit] if basket_views and (c["views"] or 0) / basket_views >= 0.2]
    return {"seed": seed, "seed_label": seed_label, "lang0": lang0, "days": days, "seed_views": seed_views,
            "candidates": rows, "broader": [{"qid": b["qid"], "relation": b["relation"]} for b in broader],
            "too_broad": [{"qid": c["qid"], "label": c["label"], "views": c["views"]}
                          for c in rows if c["broad"] and c["verified"]],
            "basket": basket, "heavy": heavy,
            "suggested_topic": "%s=%s" % (seed_label, "|".join(basket)),
            "coverage_note": "only items with articles in all of %s are suggested" % ", ".join(langs)}


def label_for(cache: Cache, qid: str, langs: List[str]) -> Optional[str]:
    e = wiki.get_entities(cache, [qid]).get(qid, {})
    return None if e.get("missing") else wiki.label_of(e, langs)
