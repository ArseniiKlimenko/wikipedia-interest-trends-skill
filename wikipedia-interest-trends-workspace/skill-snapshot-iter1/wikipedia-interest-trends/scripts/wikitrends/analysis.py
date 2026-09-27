"""Run an analysis: resolve articles, fetch data, compute metrics, write outputs."""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from . import __version__, stats, wiki
from .cache import Cache
from .i18n import lang_name
from .net import log
from .pageviews import DATA_START, aggregate_sid, article_sid, fetch_daily, month_bounds, months_in

ITEM_RE = re.compile(r"^(Q\d+)$|^([a-z][a-z0-9-]{1,15}):(.+)$")
DEFAULT_WEIGHTS = "size=1,growth=1,intensity=0.5"

# Known measurement changes in the pageview data (date range, explanation).
KNOWN_EVENTS = [
    (dt.date(2025, 4, 15), dt.date(2025, 7, 15),
     "coincides with Wikimedia's bot-detection update (May-June 2025): earlier 'human' views were "
     "probably partly automated, so the drop is at least partly a measurement artifact"),
]


class UsageError(ValueError):
    pass


# ---- parsing ----------------------------------------------------------------------------
def parse_topic(spec: str) -> dict:
    """'Label=Q1|Q2|pl:Title' -> {'label': 'Label', 'items': ['Q1', 'Q2', 'pl:Title']}."""
    label, body = None, spec.strip()
    if "=" in body:
        left, right = body.split("=", 1)
        if not ITEM_RE.match(left.strip()):
            label, body = left.strip() or None, right
    items: List[str] = []
    for part in re.split(r"[|,]", body):
        p = part.strip()
        if not p:
            continue
        if ITEM_RE.match(p):
            items.append(p)
        elif items and not ITEM_RE.match(items[-1]).group(1):  # comma inside a title
            items[-1] += "," + part
        else:
            raise UsageError(
                "cannot parse topic item %r. Use Wikidata IDs (Q1666254) or lang:Title (pl:Post przerywany). "
                "Find IDs with: wt.py resolve \"%s\" --langs <codes>" % (p, p))
    if not items:
        raise UsageError("topic %r has no items" % spec)
    return {"label": label, "items": items}


def parse_month(text: str) -> Tuple[int, int]:
    m = re.match(r"^(\d{4})-?(\d{2})(?:-?\d{2})?$", text.strip())
    if not m:
        raise UsageError("dates must look like YYYY-MM (got %r)" % text)
    return int(m.group(1)), int(m.group(2))


def resolve_period(months: Optional[int], start: Optional[str], end: Optional[str],
                   today: Optional[dt.date] = None):
    today = today or dt.date.today()
    last_complete = today.replace(day=1) - dt.timedelta(days=1)
    if today.day <= 2:  # the last day of the previous month may still be loading
        last_complete = last_complete.replace(day=1) - dt.timedelta(days=1)
    notes = []
    if end:
        y, m = parse_month(end)
        end_date = month_bounds("%04d-%02d" % (y, m))[1]
        if end_date > last_complete:
            end_date = last_complete
            notes.append("End month is not complete yet; the period ends %s." % end_date.isoformat())
    else:
        end_date = last_complete
    if start:
        y, m = parse_month(start)
        start_date = dt.date(y, m, 1)
    else:
        n = months or 24
        total = end_date.year * 12 + end_date.month - 1 - (n - 1)
        start_date = dt.date(total // 12, total % 12 + 1, 1)
    if start_date < DATA_START:
        start_date = DATA_START
        notes.append("Pageview data starts in July 2015; the period was clipped.")
    if start_date > end_date:
        raise UsageError("start is after end")
    if len(months_in(start_date, end_date)) < 4:
        raise UsageError("use a period of at least 4 months (24+ recommended)")
    return start_date, end_date, notes


def parse_weights(text: Optional[str]) -> Dict[str, float]:
    weights = {"size": 1.0, "growth": 1.0, "intensity": 0.5}
    for part in (text or DEFAULT_WEIGHTS).split(","):
        if not part.strip():
            continue
        if "=" not in part:
            raise UsageError("weights look like size=1,growth=2,intensity=0.5")
        k, v = part.split("=", 1)
        k = k.strip()
        if k not in weights:
            raise UsageError("unknown weight %r (use size, growth, intensity)" % k)
        weights[k] = float(v)
    return weights


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()


# ---- main entry -------------------------------------------------------------------------
def run(topic_specs: List[str], langs: List[str], months: Optional[int] = None, start: Optional[str] = None,
        end: Optional[str] = None, agent: str = "user", access: str = "all-access", redirects: str = "auto",
        max_redirects: int = 20, weights: Optional[str] = None, report_lang: str = "en",
        out: Optional[str] = None, geo: bool = True) -> dict:
    cache = Cache()
    langs = [l.strip().lower() for l in langs if l.strip()]
    if not langs:
        raise UsageError("give at least one language code, e.g. --langs pl,cs")
    topics = [parse_topic(s) for s in topic_specs]
    weight_map = parse_weights(weights)
    start_date, end_date, warnings = resolve_period(months, start, end)
    month_list = months_in(start_date, end_date)
    n_months = len(month_list)

    # 1. resolve lang:Title items to Wikidata items (so they map to every language)
    by_lang: Dict[str, List[str]] = {}
    for t in topics:
        for it in t["items"]:
            if not it.startswith("Q"):
                lang, title = it.split(":", 1)
                by_lang.setdefault(lang, []).append(title.strip())
    title_infos = {lang: wiki.titles_info(cache, lang, titles) for lang, titles in by_lang.items()}
    for t in topics:
        refs = []
        for it in t["items"]:
            if it.startswith("Q"):
                refs.append({"qid": it, "home": None})
                continue
            lang, title = it.split(":", 1)
            info = title_infos[lang][title.strip()]
            if not info["title"]:
                warnings.append("Article not found: %s:%s (check spelling or use resolve)." % (lang, title.strip()))
                continue
            refs.append({"qid": info["qid"], "home": (lang, info["title"])})
        t["refs"] = refs

    qids = [r["qid"] for t in topics for r in t["refs"] if r["qid"]]
    entities = wiki.get_entities(cache, qids) if qids else {}

    # 2. article list per topic and language
    for ti, t in enumerate(topics):
        t["key"] = "t%d" % ti
        t["articles"] = {}
        t["missing"] = {}
        for lang in langs:
            arts, missing = [], []
            for r in t["refs"]:
                ent = entities.get(r["qid"]) if r["qid"] else None
                if r["qid"] and ent and not ent.get("missing"):
                    title = ent["sitelinks"].get(wiki.site_of(lang))
                    name = wiki.label_of(ent, [report_lang, "en"])
                    if title:
                        arts.append({"ref": r["qid"], "title": title, "name": name})
                    else:
                        missing.append("%s (%s)" % (name, r["qid"]))
                elif r["home"]:
                    if r["home"][0] == lang:
                        arts.append({"ref": "%s:%s" % r["home"], "title": r["home"][1], "name": r["home"][1]})
                    else:
                        missing.append("%s:%s" % r["home"])
                else:
                    warnings.append("Wikidata item %s does not exist." % r["qid"])
            seen, uniq = set(), []
            for a in arts:
                if a["title"] not in seen:
                    seen.add(a["title"])
                    uniq.append(a)
            t["articles"][lang] = uniq
            t["missing"][lang] = missing
        if not t["label"]:
            first = next((r for r in t["refs"]), None)
            if first and first["qid"] and first["qid"] in entities and not entities[first["qid"]].get("missing"):
                t["label"] = wiki.label_of(entities[first["qid"]], [report_lang, "en"])
            elif first and first["home"]:
                t["label"] = first["home"][1]
            else:
                t["label"] = t["key"]

    # 3. download daily data (articles + wiki totals)
    pairs = sorted({(lang, a["title"]) for t in topics for lang in langs for a in t["articles"][lang]})
    if not pairs:
        raise UsageError("none of the topics has an article in the requested languages")
    art_sid = {p: article_sid(wiki.project_of(p[0]), p[1], access, agent) for p in pairs}
    data = fetch_daily(cache, list(art_sid.values()), start_date, end_date, label="article")
    agg_sids = {lang: aggregate_sid(wiki.project_of(lang), access, agent) for lang in langs}
    agg = fetch_daily(cache, list(agg_sids.values()), start_date, end_date, label="wiki-total")
    arrays = {p: data[art_sid[p]].copy() for p in pairs}
    totals = {lang: agg[agg_sids[lang]] for lang in langs}
    for lang in langs:
        if totals[lang].sum() <= 0:
            raise UsageError("no data for %s.wikipedia - is '%s' a valid Wikipedia language code?" % (lang, lang))

    # 4. redirects: add views of redirect titles (renamed articles, alternative spellings)
    redirect_info = {p: {"used": 0, "total": 0} for p in pairs}
    if redirects != "none":
        if redirects == "all":
            candidates = list(pairs)
        else:  # auto: only where a rename is likely (sudden jump or late start)
            candidates = [p for p in pairs if stats.level_shift(arrays[p]) is not None
                          or (arrays[p].sum() > 0 and stats.first_active_index(arrays[p]) > 31)]
        for lang in sorted({p[0] for p in candidates}):
            titles = [p[1] for p in candidates if p[0] == lang]
            reds = wiki.get_redirects(cache, lang, titles)
            red_sids = {}
            for title in titles:
                lst = reds.get(title, [])
                redirect_info[(lang, title)] = {"used": min(len(lst), max_redirects), "total": len(lst)}
                for rt in lst[:max_redirects]:
                    red_sids[(title, rt)] = article_sid(wiki.project_of(lang), rt, access, agent)
            if red_sids:
                rdata = fetch_daily(cache, list(red_sids.values()), start_date, end_date, label="redirect")
                for (title, rt), sid in red_sids.items():
                    arrays[(lang, title)] += rdata[sid]

    # 5. metrics
    days = [start_date + dt.timedelta(days=i) for i in range(len(next(iter(arrays.values()))))]
    month_pos = {m: i for i, m in enumerate(month_list)}
    month_idx = np.array([month_pos[d.strftime("%Y-%m")] for d in days])
    k = 12 if n_months >= 24 else n_months // 2
    rec_mask = month_idx >= n_months - k
    prev_mask = (month_idx >= n_months - 2 * k) & (month_idx < n_months - k)
    notes = []  # structured, localisable notes for the PDF
    if n_months < 24:
        notes.append({"code": "short_period", "k": k})
        warnings.append("Period shorter than 24 months: growth compares the last %d vs previous %d months, "
                        "so seasonality can bias it." % (k, k))

    multi_topic, multi_lang = len(topics) > 1, len(langs) > 1
    series, samples, daily = [], {}, {}
    for t in topics:
        for lang in langs:
            arts = t["articles"][lang]
            if multi_topic and multi_lang:
                name = "%s (%s)" % (t["label"], lang)
            elif multi_topic:
                name = t["label"]
            elif multi_lang:
                name = "%s (%s)" % (lang, lang_name(lang, report_lang))
            else:
                name = "%s (%s)" % (t["label"], lang)
            base = {"id": "%s|%s" % (t["key"], lang), "name": name, "topic": t["label"], "lang": lang,
                    "wiki": wiki.project_of(lang), "missing_items": t["missing"][lang]}
            if not arts:
                base.update({"status": "no_article", "confidence": {"grade": "n/a", "direction": "unclear",
                             "good": [], "bad": ["no article in %s.wikipedia" % lang]}})
                series.append(base)
                continue
            m = _series_metrics(arts, lang, arrays, totals[lang], redirect_info, days, month_idx, n_months,
                                k, rec_mask, prev_mask, month_list)
            samples[base["id"]] = m.pop("_samples")
            d = m.pop("_daily")
            daily[base["id"]] = {"dates": [x.isoformat() for x in days], "raw": d[0], "clean": d[1], "spike": d[2]}
            base.update(m)
            base["status"] = "ok"
            base["confidence"] = stats.grade_confidence(base)
            series.append(base)

    ok = [s for s in series if s["status"] == "ok"]
    comparisons = _comparisons(topics, langs, series, samples)
    ranking = _ranking(topics, langs, series, weight_map)
    geo_rows = {}
    if geo:
        for lang in langs:
            try:
                geo_rows[lang] = wiki.top_countries(cache, lang, end_date.year, end_date.month)
            except Exception as exc:  # geography is optional context
                log("wikitrends: country data unavailable for %s (%s)" % (lang, exc))

    for t in topics:
        for lang in langs:
            if t["missing"][lang] and t["articles"][lang]:
                notes.append({"code": "basket_incomplete", "topic": t["label"], "lang": lang,
                              "missing": ", ".join(t["missing"][lang])})
                warnings.append("Basket for '%s' in %s is incomplete (no article for: %s); cross-language "
                                "levels are less comparable." % (t["label"], lang, ", ".join(t["missing"][lang])))
            if not t["articles"][lang]:
                notes.append({"code": "no_article", "topic": t["label"], "lang": lang})
                hint = _local_candidates(cache, t, entities, lang)
                warnings.append("'%s' has no article in %s.wikipedia: interest cannot be measured there "
                                "(also a sign of a content gap).%s" % (t["label"], lang, hint))
    for p, info in redirect_info.items():
        if info["total"] > info["used"]:
            warnings.append("%s:%s has %d redirects; only %d were included." % (p[0], p[1], info["total"], info["used"]))

    for lo_d, hi_d, text in KNOWN_EVENTS:
        if start_date < lo_d and end_date > hi_d:
            notes.append({"code": "known_event"})
            warnings.append("The period spans %s..%s, which %s. Relative growth reduces this effect; "
                            "series flagged with a level shift there deserve extra caution."
                            % (lo_d.isoformat(), hi_d.isoformat(), text.replace("coincides with", "includes")))

    for s_ in series:
        shift = s_.get("level_shift")
        if shift:
            code = "late_start" if shift.get("kind") == "late_start" else \
                "level_shift_known" if shift.get("known_event") else "level_shift"
            notes.append({"code": code, "name": s_["name"], "date": shift["date"],
                          "ratio": "%.2g" % shift["ratio"] if shift.get("ratio") else ""})

    project_totals = {}
    for lang in langs:
        tot = totals[lang]
        project_totals[lang] = {
            "growth": float(tot[rec_mask].sum() / tot[prev_mask].sum() - 1) if tot[prev_mask].sum() > 0 else None,
            "monthly": [float(v) for v in stats.monthly_sums(tot, month_idx, n_months)],
        }

    analysis = {
        "tool": "wikipedia-interest-trends", "version": __version__,
        "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "params": {"topics": topic_specs, "langs": langs, "agent": agent, "access": access,
                   "redirects": redirects, "weights": weight_map, "report_lang": report_lang},
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat(), "months": n_months,
                   "growth_window_months": k,
                   "recent": [month_list[n_months - k], month_list[-1]],
                   "previous": [month_list[n_months - 2 * k], month_list[n_months - k - 1]]},
        "months": month_list,
        "topics": [{"key": t["key"], "label": t["label"], "items": t["items"],
                    "articles": t["articles"], "missing": t["missing"]} for t in topics],
        "series": series, "comparisons": comparisons, "ranking": ranking, "geo": geo_rows,
        "project_totals": project_totals, "warnings": list(dict.fromkeys(warnings)), "notes": notes,
    }
    outdir = Path(out) if out else Path.cwd() / "wikitrends-output" / _default_slug(topics, langs, start_date, end_date)
    outdir.mkdir(parents=True, exist_ok=True)
    analysis["outdir"] = str(outdir.resolve())
    _write_csv(analysis, outdir / "data.csv")
    analysis["_daily"] = daily  # in-memory only (diagnostic chart); not written to analysis.json
    return analysis


def _local_candidates(cache, topic, entities, lang) -> str:
    """Search the target wiki for articles that cover the topic but are not linked in Wikidata."""
    queries = []
    for r in topic["refs"]:
        ent = entities.get(r["qid"]) if r["qid"] else None
        if ent and not ent.get("missing"):
            queries += [ent["labels"].get(lang), ent["labels"].get("en")]
    queries = [q for q in dict.fromkeys(queries) if q][:2]
    found = []
    for q in queries:
        try:
            found += [x["title"] for x in wiki.search_wiki(cache, lang, q)]
        except Exception:  # hints are optional
            pass
    found = list(dict.fromkeys(found))[:5]
    if not found:
        return ""
    return (" Search in %s.wikipedia for %s suggests: %s. If one of them really covers the topic, add it as "
            "%s:<Title> and state that it is a proxy." % (lang, " / ".join('"%s"' % q for q in queries),
                                                          ", ".join(found), lang))


def _default_slug(topics, langs, start_date, end_date) -> str:
    names = "+".join(slugify(t["label"]) or t["key"] for t in topics)[:48].strip("+-") or "topics"
    return "%s_%s_%s_%s" % (names, "-".join(langs)[:30], start_date.strftime("%Y%m"), end_date.strftime("%Y%m"))


def _series_metrics(arts, lang, arrays, total, redirect_info, days, month_idx, n_months, k, rec_mask, prev_mask,
                    month_list):
    raw = np.sum([arrays[(lang, a["title"])] for a in arts], axis=0)
    clean, spike, med = stats.dampen_spikes(raw)
    ones = np.ones_like(raw)
    m: dict = {"articles": [], "_samples": np.array([]), "_daily": (raw, clean, spike)}

    m["views_recent_month_avg"] = float(raw[rec_mask].sum() / k)
    m["views_prev_month_avg"] = float(raw[prev_mask].sum() / k)
    m["daily_avg_recent"] = float(raw[rec_mask].mean())
    m["share_ppm_recent"] = float(raw[rec_mask].sum() / total[rec_mask].sum() * 1e6) if total[rec_mask].sum() else None
    m["project_growth"] = float(total[rec_mask].sum() / total[prev_mask].sum() - 1) if total[prev_mask].sum() else None
    m["spike_share"] = float((raw - clean).sum() / raw.sum()) if raw.sum() > 0 else 0.0
    m["spike_days"] = int(spike.sum())
    order = np.argsort(-(raw - med) * spike)[:3]
    m["top_spikes"] = [{"date": days[i].isoformat(), "views": int(raw[i]), "x_normal": round(float(raw[i] / max(med[i], 1)), 1)}
                       for i in order if spike[i]]

    shift = stats.level_shift(raw)
    m["level_shift"] = None
    if shift:
        sday = days[shift["index"]]
        m["level_shift"] = {"date": sday.isoformat(), "ratio": round(shift["ratio"], 2),
                            "before": round(shift["before"], 1), "after": round(shift["after"], 1)}
        for lo_d, hi_d, text in KNOWN_EVENTS:
            if lo_d <= sday <= hi_d:
                m["level_shift"]["known_event"] = text

    first = stats.first_active_index(raw)
    rec_start = int(np.argmax(rec_mask))
    prev_start = int(np.argmax(prev_mask))
    m["growth_note"] = None
    if first >= rec_start:
        m["growth_note"] = "no views before %s (article new or renamed): growth cannot be computed" % (
            days[first].isoformat() if first < len(days) else "the end of the period")
    elif first > prev_start + 31:
        m["level_shift"] = {"date": days[first].isoformat(), "ratio": None, "kind": "late_start",
                            "before": 0.0, "after": float(np.median(raw[first:first + 28]))}

    rel = abs_ = None
    if m["growth_note"] is None:
        rel = stats.ratio_growth(clean[prev_mask], total[prev_mask], clean[rec_mask], total[rec_mask])
        abs_ = stats.ratio_growth(clean[prev_mask], ones[prev_mask], clean[rec_mask], ones[rec_mask])
    if rel:
        m.update(growth_rel=rel["point"], growth_rel_lo=rel["lo"], growth_rel_hi=rel["hi"])
        m["_samples"] = rel["samples"]
        m["growth_rel_with_spikes"] = float((raw[rec_mask].sum() / total[rec_mask].sum())
                                            / (raw[prev_mask].sum() / total[prev_mask].sum()) - 1) \
            if raw[prev_mask].sum() > 0 else None
    else:
        m.update(growth_rel=None, growth_rel_lo=None, growth_rel_hi=None, growth_rel_with_spikes=None)
        if m["growth_note"] is None:
            m["growth_note"] = "no views in the comparison period"
    if abs_:
        m.update(growth_abs=abs_["point"], growth_abs_lo=abs_["lo"], growth_abs_hi=abs_["hi"])
    else:
        m.update(growth_abs=None, growth_abs_lo=None, growth_abs_hi=None)

    mon_raw = stats.monthly_sums(raw, month_idx, n_months)
    mon_clean = stats.monthly_sums(clean, month_idx, n_months)
    mon_total = stats.monthly_sums(total, month_idx, n_months)
    with np.errstate(divide="ignore", invalid="ignore"):
        share = np.where(mon_total > 0, mon_clean / mon_total * 1e6, 0.0)
    trend = stats.annual_trend(share[max(0, first // 31):] if first > 0 else share)
    m["trend_annual"], m["trend_p"] = trend["annual"], trend["p"]
    if m["level_shift"] and m["level_shift"].get("kind") != "late_start":
        after_month = int(month_idx[min(len(days) - 1, days.index(dt.date.fromisoformat(m["level_shift"]["date"])) + 31)])
        if n_months - after_month >= 8:
            m["level_shift"]["trend_after"] = stats.annual_trend(share[after_month:])["annual"]
    m["months_up"] = stats.months_above_last_year(share) if m["growth_note"] is None else None
    m["momentum_6m"] = None
    if n_months >= 18 and share[-18:-12].sum() > 0:
        m["momentum_6m"] = float(share[-6:].mean() / share[-18:-12].mean() - 1)
    m["yearly"] = []
    if n_months >= 36:
        years = n_months // 12
        for j in range(years - 1, 0, -1):
            a0, a1 = n_months - 12 * (j + 1), n_months - 12 * j
            b1 = a1 + 12
            if share[a0:a1].sum() > 0:
                m["yearly"].append({"from": "%s..%s" % (month_list[a0], month_list[a1 - 1]),
                                    "to": "%s..%s" % (month_list[a1], month_list[b1 - 1]),
                                    "growth_rel": float(share[a1:b1].mean() / share[a0:a1].mean() - 1),
                                    "growth_abs": float(mon_clean[a1:b1].sum() / mon_clean[a0:a1].sum() - 1)
                                    if mon_clean[a0:a1].sum() > 0 else None})
    m["monthly"] = {"views": [float(v) for v in mon_raw], "views_clean": [float(v) for v in mon_clean],
                    "share_ppm": [float(v) for v in share]}

    # per-article contribution and leave-one-out stability
    total_recent = raw[rec_mask].sum() or 1.0
    m["driven_by"] = None
    for a in arts:
        arr = arrays[(lang, a["title"])]
        info = redirect_info.get((lang, a["title"]), {"used": 0, "total": 0})
        g = None
        if arr[prev_mask].sum() > 0:
            ac, _, _ = stats.dampen_spikes(arr)
            g = float((ac[rec_mask].sum() / total[rec_mask].sum()) / (ac[prev_mask].sum() / total[prev_mask].sum()) - 1) \
                if ac[prev_mask].sum() > 0 else None
        m["articles"].append({"title": a["title"], "ref": a["ref"], "redirects_added": info["used"],
                              "views_recent_month_avg": float(arr[rec_mask].sum() / k),
                              "share_of_basket": float(arr[rec_mask].sum() / total_recent),
                              "growth_rel": g})
    m["top_article_share"] = max(a["share_of_basket"] for a in m["articles"])
    if len(arts) >= 2 and rel:
        for a in arts:
            rest = raw - arrays[(lang, a["title"])]
            rc, _, _ = stats.dampen_spikes(rest)
            if rc[prev_mask].sum() <= 0:
                continue
            g = (rc[rec_mask].sum() / total[rec_mask].sum()) / (rc[prev_mask].sum() / total[prev_mask].sum()) - 1
            if np.sign(g) != np.sign(rel["point"]) and abs(rel["point"]) > 0.02:
                m["driven_by"] = a["title"]
                break
    return m


def _groups(topics, langs) -> List[Tuple[str, List[str]]]:
    """Series that should be compared/ranked together: languages within a topic, or topics within
    a single language."""
    if len(langs) > 1:
        return [("topic: %s" % t["label"], ["%s|%s" % (t["key"], l) for l in langs]) for t in topics]
    return [("%s.wikipedia" % langs[0], ["%s|%s" % (t["key"], langs[0]) for t in topics])]


def _comparisons(topics, langs, series, samples) -> List[dict]:
    by_id = {s["id"]: s for s in series}
    out = []
    for group, ids in _groups(topics, langs):
        valid = [i for i in ids if by_id[i].get("growth_rel") is not None and len(samples.get(i, [])) > 0]
        if len(valid) < 2:
            continue
        valid.sort(key=lambda i: -by_id[i]["growth_rel"])
        leader = valid[0]
        for other in valid[1:]:
            d = stats.diff_interval(samples[leader], samples[other])
            if not d:
                continue
            out.append({"group": group, "a": by_id[leader]["name"], "b": by_id[other]["name"],
                        "diff": by_id[leader]["growth_rel"] - by_id[other]["growth_rel"],
                        "lo": d[1], "hi": d[2], "clear": d[1] > 0})
    return out


def _ranking(topics, langs, series, weights: Dict[str, float]) -> dict:
    by_id = {s["id"]: s for s in series}
    groups = []
    for group, ids in _groups(topics, langs):
        ok = [by_id[i] for i in ids if by_id[i]["status"] == "ok"]
        if len(ok) < 2:
            continue
        comp = {"size": [s["views_recent_month_avg"] for s in ok],
                "growth": [s.get("growth_rel") for s in ok],
                "intensity": [s.get("share_ppm_recent") for s in ok]}
        ranks = {c: stats.percentile_ranks(v) for c, v in comp.items()}
        rows = []
        for i, s in enumerate(ok):
            num = den = 0.0
            for c, w in weights.items():
                if w and ranks[c][i] is not None:
                    num += w * ranks[c][i]
                    den += w
            rows.append({"name": s["name"], "id": s["id"], "score": round(num / den, 3) if den else None,
                         "size_rank": ranks["size"][i], "growth_rank": ranks["growth"][i],
                         "intensity_rank": ranks["intensity"][i], "confidence": s["confidence"]["grade"]})
        rows.sort(key=lambda r: -(r["score"] or 0))
        groups.append({"group": group, "rows": rows})
    return {"weights": weights, "groups": groups}


def _write_csv(analysis: dict, path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["series", "topic", "lang", "month", "views", "views_spike_dampened", "wiki_total_views",
                    "share_per_million"])
        for s in analysis["series"]:
            if s["status"] != "ok":
                continue
            tot = analysis["project_totals"][s["lang"]]["monthly"]
            for i, month in enumerate(analysis["months"]):
                w.writerow([s["name"], s["topic"], s["lang"], month, int(s["monthly"]["views"][i]),
                            int(round(s["monthly"]["views_clean"][i])), int(tot[i]),
                            round(s["monthly"]["share_ppm"][i], 3)])


def _clean_json(o):
    if isinstance(o, dict):
        return {k: _clean_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean_json(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        o = o.item()
    if isinstance(o, float) and not np.isfinite(o):
        return None
    return o


def save_json(analysis: dict, path: Path) -> None:
    path.write_text(json.dumps(_clean_json(analysis), ensure_ascii=False, indent=1), encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
