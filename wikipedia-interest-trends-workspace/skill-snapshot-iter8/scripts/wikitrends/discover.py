"""Discover topics whose interest is growing.

Two candidate sources:
  * a whole language edition: the articles that were in Wikimedia's monthly top-1000 lists over
    the last few months (people, films, TV and similar news-driven pages are excluded by default
    using Wikidata "instance of");
  * one subject (`seed`): the sub-topics found by graph.expand().
Each candidate then gets the same growth measurement as `analyze` (24 months, relative growth
with a 95% interval, spike dampening, confidence grade), so "growing" means sustained growth in
the share of attention, not a one-day news spike.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from . import analysis as an, graph, stats, wiki
from .cache import Cache
from .net import get_json, log
from .pageviews import API, aggregate_sid, article_sid, fetch_daily

BURST_SHARE = 0.35  # >= 35% of the last year's views in its two biggest months = a burst, not a trend

EXCLUDE_TYPES = {  # instance-of classes that are mostly news, entertainment or navigation
    "Q5": "person", "Q15632617": "fictional person", "Q95074": "fictional character",
    "Q11424": "film", "Q5398426": "TV series", "Q3464665": "TV season", "Q21191270": "TV episode",
    "Q482994": "album", "Q134556": "single", "Q7366": "song", "Q105543609": "musical work",
    "Q27020041": "sports season", "Q16510064": "sporting event", "Q18608583": "recurring sporting event",
    "Q13406463": "list", "Q4167410": "disambiguation", "Q577": "year", "Q3186692": "calendar year",
    "Q40231": "election", "Q7889": "video game", "Q215380": "band", "Q476028": "football club",
    "Q1656682": "event", "Q13406554": "sports competition", "Q2991546": "football tournament",
    "Q847017": "sports club", "Q4438121": "sports organization", "Q64728935": "future event",
    "Q1190554": "occurrence", "Q15416": "television program", "Q7725310": "series of creative works",
    "Q2558591": "ranking list", "Q28873665": "rating system", "Q7058673": "reality TV", "Q13442814": "scholarly article",
}
FDR_Q = 0.10  # Benjamini-Hochberg false discovery rate for calling a candidate "growing"


def bh_qvalues(pvals: List[Optional[float]]) -> List[Optional[float]]:
    """Benjamini-Hochberg adjusted p-values (q-values); None stays None."""
    idx = [i for i, p in enumerate(pvals) if p is not None]
    out: List[Optional[float]] = [None] * len(pvals)
    if not idx:
        return out
    order = sorted(idx, key=lambda i: pvals[i])
    m = len(order)
    q_prev = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        q_prev = min(q_prev, pvals[i] * m / rank)
        out[i] = min(1.0, q_prev)
    return out


def top_articles(cache: Cache, lang: str, year: int, month: int) -> List[dict]:
    key = "top|%s|%04d-%02d" % (lang, year, month)
    hit = cache.kv_get(key, ttl_days=None)
    if hit is not None:
        return hit
    data = get_json("%s/top/%s/all-access/%04d/%02d/all-days" % (API, wiki.project_of(lang), year, month))
    rows = []
    if data and data.get("items"):
        rows = [{"title": a["article"].replace("_", " "), "views": int(a["views"])}
                for a in data["items"][0].get("articles", [])]
    cache.kv_set(key, rows)
    return rows


def siteinfo(cache: Cache, lang: str) -> dict:
    key = "siteinfo|%s" % lang
    hit = cache.kv_get(key, ttl_days=30)
    if hit is not None:
        return hit
    data = get_json(wiki.action_api(lang), {"action": "query", "meta": "siteinfo", "siprop": "general|namespaces|namespacealiases",
                                            "format": "json", "formatversion": 2}, allow_404=False) or {}
    q = data.get("query", {})
    names = set()
    for ns in q.get("namespaces", {}).values():
        if ns.get("id", 0) != 0:
            names.update(n for n in (ns.get("name"), ns.get("canonical")) if n)
    names.update(a["alias"] for a in q.get("namespacealiases", []))
    info = {"mainpage": q.get("general", {}).get("mainpage", ""), "namespaces": sorted(names)}
    cache.kv_set(key, info)
    return info


def instance_types(cache: Cache, qids: List[str]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for i in range(0, len(qids), 80):
        chunk = qids[i:i + 80]
        rows = graph.sparql(cache, "SELECT ?item ?t WHERE { VALUES ?item { %s } ?item wdt:P31 ?t }" %
                            " ".join("wd:" + q for q in chunk))
        for r in rows:
            out.setdefault(r["item"], []).append(r["t"])
    return out


def _last_complete_month(today: Optional[dt.date] = None) -> dt.date:
    _s, e, _n = an.resolve_period(24, None, None, today)
    return e


def candidates_from_top(cache: Cache, lang: str, top_months: int, limit: int, include_all: bool) -> List[dict]:
    end = _last_complete_month()
    info = siteinfo(cache, lang)
    prefixes = tuple(n + ":" for n in info["namespaces"])
    views: Dict[str, int] = {}
    y, m = end.year, end.month
    for _ in range(top_months):
        for row in top_articles(cache, lang, y, m):
            t = row["title"]
            if t in (info["mainpage"], "-") or t.startswith(prefixes):
                continue
            views[t] = views.get(t, 0) + row["views"]
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    ordered = sorted(views, key=lambda t: -views[t])[: limit * 3]
    tinfo = wiki.titles_info(cache, lang, ordered)
    rows, seen = [], set()
    for t in ordered:
        inf = tinfo.get(t) or {}
        title, qid = inf.get("title"), inf.get("qid")
        if not title or title in seen:
            continue
        seen.add(title)
        rows.append({"title": title, "qid": qid, "top_views": views[t]})
    if not include_all:  # drop kinds of people, entertainment, sport, lists (instance-of chain, 3 hops)
        excluded = graph.on_topic(cache, [r["qid"] for r in rows if r["qid"]], list(EXCLUDE_TYPES), depth=3,
                                  loose=True)
        rows = [r for r in rows if r["qid"] and r["qid"] not in excluded]
    return rows[:limit]


def candidates_from_seed(cache: Cache, lang: str, seed: str, limit: int) -> List[dict]:
    ex = graph.expand(cache, seed, [lang], limit=limit)
    rows = [{"title": c["titles"][lang], "qid": c["qid"], "label": c["label"]}
            for c in ex["candidates"] if c["verified"] and c["titles"].get(lang)]
    seed_title = wiki.get_entities(cache, [seed])[seed]["sitelinks"].get(wiki.site_of(lang))
    if seed_title:
        rows.insert(0, {"title": seed_title, "qid": seed, "label": ex["seed_label"]})
    return rows[:limit]


def discover(lang: str, seed: Optional[str] = None, months: int = 24, candidates: int = 60, top_months: int = 3,
             include_all: bool = False, out: Optional[str] = None, min_views: float = 90) -> dict:
    cache = Cache()
    lang = lang.strip().lower()
    start, end, _notes = an.resolve_period(months, None, None)
    if seed:
        rows = candidates_from_seed(cache, lang, seed, candidates)
        source = "sub-topics of %s from the Wikidata and link graphs" % seed
    else:
        rows = candidates_from_top(cache, lang, top_months, candidates, include_all)
        source = "articles in the monthly top-1000 of %s.wikipedia over the last %d months%s" % (
            lang, top_months, "" if include_all else " (people, films, TV, sport, lists excluded)")
    if not rows:
        raise an.UsageError("no candidates found")
    project = wiki.project_of(lang)
    sids = {r["title"]: article_sid(project, r["title"], "all-access", "user") for r in rows}
    log("wikitrends: measuring %d candidates (first run downloads their history; cached afterwards)" % len(rows))
    data = fetch_daily(cache, list(sids.values()), start, end, label="candidate")
    total = fetch_daily(cache, [aggregate_sid(project, "all-access", "user")], start, end, label="wiki-total")
    total = next(iter(total.values()))
    ax = an.time_axes(start, end)
    results = []
    for r in rows:
        arr = data[sids[r["title"]]]
        if arr.sum() <= 0:
            continue
        arrays = {(lang, r["title"]): arr}
        arts = [{"title": r["title"], "ref": r["qid"] or "%s:%s" % (lang, r["title"]), "name": r["title"]}]
        m = an._series_metrics(arts, lang, arrays, total, {}, ax["days"], ax["month_idx"], ax["n_months"],
                               ax["k"], ax["rec_mask"], ax["prev_mask"], ax["month_list"], with_models=False)
        m.pop("_samples", None)
        m.pop("_daily", None)
        m["status"] = "ok"
        conf = stats.grade_confidence(m)
        mon = np.array(m["monthly"]["views"][-12:], dtype=float)
        top2 = float(np.sort(mon)[-2:].sum() / mon.sum()) if mon.sum() > 0 else 0.0
        peak = ax["month_list"][-12:][int(np.argmax(mon))] if mon.sum() > 0 else None
        results.append({"title": r["title"], "qid": r["qid"], "views_month": m["views_recent_month_avg"],
                        "growth_rel": m.get("growth_rel"), "lo": m.get("growth_rel_lo"), "hi": m.get("growth_rel_hi"),
                        "growth_abs": m.get("growth_abs"), "spike_share": m["spike_share"],
                        "confidence": conf["grade"], "direction": conf["direction"], "concerns": conf["bad"][:2],
                        "p": m.get("growth_rel_p"), "top2_share": top2, "peak_month": peak, "burst": top2 >= BURST_SHARE})
    tier = {"high": 0, "medium": 1, "low": 2, "n/a": 3}
    big = [x for x in results if x["views_month"] >= min_views]
    for x, q in zip(big, bh_qvalues([x["p"] for x in big])):  # many candidates -> control false discoveries
        x["q"] = q
    up = [x for x in big if x["direction"] == "up"]
    growing = sorted([x for x in up if x["q"] is not None and x["q"] <= FDR_Q],
                     key=lambda x: (x["burst"], tier[x["confidence"]], -x["growth_rel"]))
    maybe = sorted([x for x in up if x not in growing], key=lambda x: -x["growth_rel"])
    shared: Dict[str, List[str]] = {}
    bursts = [x for x in big if x["burst"] and (x["growth_rel"] or 0) > 0]  # up in total, but short-lived
    for x in bursts:
        if x["peak_month"]:
            shared.setdefault(x["peak_month"], []).append(x["title"])
    shared = {k: v for k, v in shared.items() if len(v) >= 2}
    declining = sorted([x for x in big if x["direction"] == "down"], key=lambda x: (tier[x["confidence"]], x["growth_rel"]))
    res = {"lang": lang, "seed": seed, "source": source, "period": {"start": start.isoformat(), "end": end.isoformat()},
           "measured": len(results), "candidates": len(rows), "min_views": min_views,
           "too_small": len(results) - len(big), "no_data": len(rows) - len(results), "fdr_q": FDR_Q,
           "growing": growing, "maybe": maybe, "declining": declining, "shared_peaks": shared,
           "bursts": [x["title"] for x in bursts],
           "flat": sum(1 for x in big if x["direction"] in ("flat", "unclear"))}
    outdir = Path(out) if out else an.default_output_root() / ("discover_%s_%s" % (lang, seed or "top"))
    outdir.mkdir(parents=True, exist_ok=True)
    res["outdir"] = str(outdir.resolve())
    an.save_json(res, outdir / "discover.json")
    text = discover_md(res)
    (outdir / "discover.md").write_text(text, encoding="utf-8")
    return res


def _pct(x):
    return "n/a" if x is None else "%+.0f%%" % (x * 100)


def discover_md(r: dict, top: int = 15) -> str:
    L = ["# Growing topics in %s.wikipedia" % r["lang"], "",
         "Candidates: %s. Period %s..%s; relative growth = last 12 months vs previous 12 (share of all wiki "
         "views), 95%% interval, spike-dampened." % (r["source"], r["period"]["start"][:7], r["period"]["end"][:7]),
         "%d candidates: %d had no views, %d were below %d views/month and were skipped, %d were analysed: "
         "%d growing, %d up but not significant after the multiple-testing correction, %d declining, %d without a "
         "clear change." % (r.get("candidates", r["measured"]), r.get("no_data", 0), r["too_small"], r["min_views"],
                            r["measured"] - r["too_small"], len(r["growing"]), len(r.get("maybe", [])),
                            len(r["declining"]), r["flat"]),
         "'Growing' needs a 95%% interval above zero AND a Benjamini-Hochberg q <= %.2f across the analysed "
         "candidates (with ~60 candidates, a few would look 'up' by chance)." % r.get("fdr_q", FDR_Q), "",
         "Relative growth is already net of the whole-wiki traffic change; do not adjust it again.", "",
         "## Growing (95% interval above zero; sustained first, then by confidence and growth)", "",
         "| # | Article | QID | Views/mo | Relative growth [95% CI] | q | Spikes | Pattern | Confidence |",
         "|---|---|---|---|---|---|---|---|---|"]
    for i, x in enumerate(r["growing"][:top], 1):
        pattern = "burst, peak %s (%.0f%% of the year in 2 months)" % (x["peak_month"], x["top2_share"] * 100) \
            if x.get("burst") else "sustained"
        L.append("| %d | %s | %s | %s | %s [%s, %s] | %s | %.0f%% | %s | %s |" % (
            i, x["title"], x["qid"] or "-", "{:,.0f}".format(x["views_month"]), _pct(x["growth_rel"]), _pct(x["lo"]),
            _pct(x["hi"]), "%.3f" % x["q"] if x.get("q") is not None else "-", x["spike_share"] * 100, pattern,
            x["confidence"].upper()))
    if not r["growing"]:
        L.append("| - | none | | | | | | | |")
    if len(r["growing"]) > top:
        L.append("")
        L.append("+%d more growing rows in discover.json (%s)." % (
            len(r["growing"]) - top, ", ".join(x["title"] for x in r["growing"][top:top + 8])))
    if r.get("maybe"):
        L += ["", "Up but not significant after the correction (hypotheses only): " + ", ".join(
            "%s %s" % (x["title"], _pct(x["growth_rel"])) for x in r["maybe"][:8]) + "."]
    other_bursts = [b for b in r.get("bursts", []) if b not in {x["title"] for x in r["growing"]}]
    if other_bursts:
        L += ["", "Short bursts (most of the year's views in 2 months; not sustained growth): %s." % ", ".join(other_bursts[:10])]
    if r.get("shared_peaks"):
        L += ["", "## Shared peaks (bursts in the same month; check for a common cause)"]
        for month, titles in sorted(r["shared_peaks"].items()):
            L.append("- %s: %s." % (month, ", ".join(titles)))
        L.append("Bursts that peak in the same month may share one cause (a tournament, an election, a film "
                 "release, news). If they do, name it and treat the group as one short-lived event, not as "
                 "separate growth areas. Only 'sustained' rows are candidates for lasting content.")
    L += ["", "## Declining fastest", ""]
    for x in r["declining"][:5]:
        L.append("- %s (%s): %s [%s, %s], %s confidence" % (x["title"], x["qid"] or "-", _pct(x["growth_rel"]),
                                                            _pct(x["lo"]), _pct(x["hi"]), x["confidence"]))
    L += ["", "Next: turn promising QIDs into topics (group related ones) and run `wt.py analyze` for the full "
          "analysis, seasonality, forecast and report. LOW confidence rows are hypotheses, not findings.",
          "Files: %s/discover.json, discover.md" % r["outdir"]]
    return "\n".join(L) + "\n"
