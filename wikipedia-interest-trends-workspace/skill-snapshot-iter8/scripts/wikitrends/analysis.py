"""Run an analysis: resolve articles, fetch data, compute metrics, write outputs."""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from . import __version__, models, stats, wiki
from .cache import Cache
from .i18n import lang_name
from .net import log
from .pageviews import DATA_START, aggregate_sid, article_sid, fetch_daily, month_bounds, months_in

ITEM_RE = re.compile(r"^(Q\d+)$|^([a-z][a-z0-9-]{1,15}):(.+)$")
DEFAULT_WEIGHTS = "size=1,growth=1,intensity=0.5"

# Known measurement changes in the pageview data (date range, explanation).
KNOWN_EVENTS = [
    (dt.date(2025, 4, 15), dt.date(2025, 7, 15),
     "coincides with Wikimedia's bot-detection update (May-June 2025), which reclassified part of the "
     "earlier 'human' views as automated; a jump here may be partly a measurement artifact"),
]
# two-month windows before/after that update, used to measure each series' step across it
EVENT_WINDOWS = ((dt.date(2025, 3, 1), dt.date(2025, 4, 30)), (dt.date(2025, 7, 1), dt.date(2025, 8, 31)))
EVENT_FLAG = 0.25  # flag series whose seasonally adjusted step differs from their wiki's by >= 25%
MODEL_MONTHS = 48  # history fetched for seasonality, forecasts and year-over-year blocks
LANG_RE = re.compile(r"^(?:[a-z]{2,3}(?:-[a-z0-9]{2,12})*|simple)$")
SKILL_DIR = Path(__file__).resolve().parents[2]


def default_output_root() -> Path:
    """./wikitrends-output in the user's working directory, but never inside the skill folder."""
    from .cache import home_dir
    cwd = Path.cwd().resolve()
    if cwd == SKILL_DIR or SKILL_DIR in cwd.parents:
        return home_dir() / "output"
    return cwd / "wikitrends-output"


def shift_months(d: dt.date, months: int) -> dt.date:
    total = d.year * 12 + d.month - 1 + months
    return dt.date(total // 12, total % 12 + 1, 1)


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
        out: Optional[str] = None, geo: bool = True, previous: Optional[str] = None) -> dict:
    cache = Cache()
    langs = list(dict.fromkeys(l.strip().lower() for l in langs if l.strip()))
    if not langs:
        raise UsageError("give at least one language code, e.g. --langs pl,cs")
    bad = [l for l in langs if not LANG_RE.match(l)]
    if bad:
        raise UsageError("not a Wikipedia language code: %s (use codes like pl, cs, pt, zh-yue)" % ", ".join(bad))
    topics = [parse_topic(s) for s in topic_specs]
    weight_map = parse_weights(weights)
    start_date, end_date, warnings = resolve_period(months, start, end)
    month_list = months_in(start_date, end_date)
    n_months = len(month_list)
    hist_start = max(DATA_START, min(start_date, shift_months(dt.date(end_date.year, end_date.month, 1),
                                                                -(MODEL_MONTHS - 1))))
    off = (start_date - hist_start).days
    outdir = Path(out) if out else None
    auto_previous = False
    if previous is not None and previous.strip().lower() in ("", "none", "no"):
        previous = ""  # explicitly disabled
    elif previous is None and outdir is not None and (outdir / "analysis.json").exists():
        # a re-run into the same folder is a follow-up: keep the old result and compare with it
        import shutil
        shutil.copyfile(outdir / "analysis.json", outdir / "analysis.previous.json")
        previous, auto_previous = str(outdir / "analysis.previous.json"), True

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
            if info.get("disambiguation"):
                warnings.append("%s:%s is a disambiguation page (it lists several meanings), so its views do not "
                                "measure one topic; it was left out. Pick the specific article with resolve."
                                % (lang, info["title"]))
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

    # 3. download daily data (wiki totals first, so a wrong language code fails clearly). History
    #    before the period (up to MODEL_MONTHS in total) feeds seasonality, forecasts and yearly blocks.
    agg_sids = {lang: aggregate_sid(wiki.project_of(lang), access, agent) for lang in langs}
    agg = fetch_daily(cache, list(agg_sids.values()), hist_start, end_date, label="wiki-total")
    totals_full = {lang: agg[agg_sids[lang]] for lang in langs}
    for lang in langs:
        if totals_full[lang][off:].sum() <= 0:
            raise UsageError("no pageview data for %s.wikipedia - is '%s' a valid Wikipedia language code?"
                             % (lang, lang))
    pairs = sorted({(lang, a["title"]) for t in topics for lang in langs for a in t["articles"][lang]})
    if not pairs:
        raise UsageError("none of the topics has an article in the requested languages")
    art_sid = {p: article_sid(wiki.project_of(p[0]), p[1], access, agent) for p in pairs}
    data = fetch_daily(cache, list(art_sid.values()), hist_start, end_date, label="article")
    arrays_full = {p: data[art_sid[p]].copy() for p in pairs}

    # 4. redirects: add views of redirect titles (renamed articles, alternative spellings)
    redirect_info = {p: {"used": 0, "total": 0} for p in pairs}
    if redirects != "none":
        if redirects == "all":
            candidates = list(pairs)
        else:  # auto: only where a rename is likely (sudden jump or late start)
            candidates = [p for p in pairs if stats.level_shift(arrays_full[p]) is not None
                          or (arrays_full[p][off:].sum() > 0 and stats.first_active_index(arrays_full[p][off:]) > 31)]
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
                rdata = fetch_daily(cache, list(red_sids.values()), hist_start, end_date, label="redirect")
                for (title, rt), sid in red_sids.items():
                    arrays_full[(lang, title)] += rdata[sid]
    arrays = {p: v[off:] for p, v in arrays_full.items()}
    totals = {lang: v[off:] for lang, v in totals_full.items()}
    hax = time_axes(hist_start, end_date)
    hist = {"arrays": arrays_full, "off": off, "days": hax["days"], "month_list": hax["month_list"],
            "month_idx": hax["month_idx"], "n_months": hax["n_months"]}

    # 5. metrics
    ax = time_axes(start_date, end_date)
    days, month_idx, k, rec_mask, prev_mask = ax["days"], ax["month_idx"], ax["k"], ax["rec_mask"], ax["prev_mask"]
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
            # names always say "<lang>.wikipedia": the unit is a language edition, not a country
            if multi_topic and multi_lang:
                name = "%s · %s.wikipedia" % (t["label"], lang)
            elif multi_topic:
                name = t["label"]
            elif multi_lang:
                name = "%s.wikipedia (%s)" % (lang, lang_name(lang, report_lang))
            else:
                name = "%s · %s.wikipedia" % (t["label"], lang)
            base = {"id": "%s|%s" % (t["key"], lang), "name": name, "topic": t["label"], "lang": lang,
                    "wiki": wiki.project_of(lang), "missing_items": t["missing"][lang]}
            if not arts:
                base.update({"status": "no_article", "confidence": {"grade": "n/a", "direction": "unclear",
                             "good": [], "bad": ["no article in %s.wikipedia" % lang]}})
                series.append(base)
                continue
            m = _series_metrics(arts, lang, arrays, totals[lang], redirect_info, days, month_idx, n_months,
                                k, rec_mask, prev_mask, month_list, hist=dict(hist, total=totals_full[lang]))
            samples[base["id"]] = m.pop("_samples")  # ratio_growth() result (bootstrap samples, monthly ratios)
            d = m.pop("_daily")
            daily[base["id"]] = {"dates": [x.isoformat() for x in days], "raw": d[0], "clean": d[1], "spike": d[2]}
            base.update(m)
            base["status"] = "ok"
            base["confidence"] = stats.grade_confidence(base)
            series.append(base)

    ok = [s for s in series if s["status"] == "ok"]
    pooling = _apply_pooling(topics, langs, series)
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

    wiki_steps = {lang: event_step(totals_full[lang], np.ones_like(totals_full[lang]), hist_start)
                  for lang in langs}
    for lo_d, hi_d, text in KNOWN_EVENTS:
        if start_date < lo_d and end_date > hi_d:
            steps = ", ".join("%s %+.0f%%" % (l, v["rel"] * 100) for l, v in wiki_steps.items() if v)
            flagged = [s_["name"] for s_ in ok if (s_.get("event_step") or {}).get("flag")]
            notes.append({"code": "known_event", "steps": steps or "n/a"})
            warnings.append(
                "The period includes Wikimedia's bot-detection update (May-June 2025), which reclassified part of "
                "the earlier 'human' views as automated. Measured step of whole-wiki human views across it "
                "(Jul-Aug vs Mar-Apr 2025, seasonally adjusted with 2024 where available): %s. Relative growth "
                "nets out a step that a topic shares with its wiki. %s"
                % (steps or "n/a", "Series whose own step differs by %d%% or more: %s (see Confidence notes)."
                   % (EVENT_FLAG * 100, "; ".join(flagged)) if flagged else
                   "No series moved differently from its wiki by %d%% or more, so the update is unlikely to "
                   "drive these results; do not cite it as an explanation." % (EVENT_FLAG * 100)))

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
            "event_step": wiki_steps.get(lang),
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
        "series": series, "comparisons": comparisons, "ranking": ranking, "geo": geo_rows, "pooling": pooling,
        "project_totals": project_totals, "warnings": list(dict.fromkeys(warnings)), "notes": notes,
    }
    if outdir is None:
        outdir = default_output_root() / _default_slug(topics, langs, start_date, end_date)
        if previous is None and (outdir / "analysis.json").exists():
            import shutil
            shutil.copyfile(outdir / "analysis.json", outdir / "analysis.previous.json")
            previous, auto_previous = str(outdir / "analysis.previous.json"), True
    if previous is None:
        previous = _recent_related(topics, outdir)
        auto_previous = bool(previous)
    if previous:
        analysis["changes"] = compare_with_previous(analysis, previous)
        analysis["changes"]["auto"] = auto_previous
    outdir.mkdir(parents=True, exist_ok=True)
    _remember(topics, outdir)
    analysis["outdir"] = str(outdir.resolve())
    _write_csv(analysis, outdir / "data.csv")
    analysis["_daily"] = daily  # in-memory only (diagnostic chart); not written to analysis.json
    return analysis


LAST_ANALYSIS_HOURS = 12


def _remember(topics, outdir: Path) -> None:
    """Record this run so a follow-up question in the same working directory can be compared with it."""
    from .cache import home_dir
    try:
        (home_dir() / "last_analysis.json").write_text(json.dumps({
            "cwd": str(Path.cwd().resolve()), "outdir": str(outdir.resolve()), "time": dt.datetime.now().timestamp(),
            "items": sorted({it for t in topics for it in t["items"]})}), encoding="utf-8")
    except OSError:
        pass


def _recent_related(topics, outdir: Path) -> Optional[str]:
    """The previous analysis from the same working directory (last 12 hours) that shares a topic item."""
    from .cache import home_dir
    try:
        last = json.loads((home_dir() / "last_analysis.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    items = {it for t in topics for it in t["items"]}
    prev_dir = Path(last.get("outdir", ""))
    if (last.get("cwd") == str(Path.cwd().resolve()) and prev_dir.resolve() != outdir.resolve()
            and dt.datetime.now().timestamp() - last.get("time", 0) < LAST_ANALYSIS_HOURS * 3600
            and items & set(last.get("items", [])) and (prev_dir / "analysis.json").exists()):
        return str(prev_dir / "analysis.json")
    return None


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


def _series_keys(a: dict) -> Dict[str, Tuple]:
    """series id -> (topic items, lang), a key that survives relabelling between runs."""
    items = {t["key"]: tuple(sorted(t["items"])) for t in a["topics"]}
    return {s["id"]: (items[s["id"].split("|")[0]], s["lang"]) for s in a["series"]}


def compare_with_previous(a: dict, previous: str) -> dict:
    """What changed relative to an earlier analysis (for follow-up questions)."""
    path = Path(previous)
    path = path / "analysis.json" if path.is_dir() else path
    if not path.exists():
        found = sorted(Path(previous).glob("**/analysis.json")) if Path(previous).is_dir() else []
        if not found:
            raise UsageError("--previous: no analysis.json found in %s" % previous)
        path = found[0]
    prev = load_json(path)
    out = {"previous": str(path), "params": [], "ranking": [], "growth": [], "measurement_changed": False}
    pp, np_ = prev["params"], a["params"]
    added = [l for l in np_["langs"] if l not in pp["langs"]]
    removed = [l for l in pp["langs"] if l not in np_["langs"]]
    if added:
        out["params"].append("languages added: %s" % ", ".join(added))
    if removed:
        out["params"].append("languages removed: %s" % ", ".join(removed))
    if pp.get("weights") != np_.get("weights"):
        fmt = lambda w: "size=%g, growth=%g, intensity=%g" % (w["size"], w["growth"], w["intensity"])  # noqa: E731
        out["params"].append("ranking weights: %s -> %s" % (fmt(pp["weights"]), fmt(np_["weights"])))
    if (prev["period"]["start"], prev["period"]["end"]) != (a["period"]["start"], a["period"]["end"]):
        out["params"].append("period: %s..%s -> %s..%s" % (prev["period"]["start"][:7], prev["period"]["end"][:7],
                                                          a["period"]["start"][:7], a["period"]["end"][:7]))
    prev_topics = {tuple(sorted(t["items"])): t["label"] for t in prev["topics"]}
    new_topics = {tuple(sorted(t["items"])): t["label"] for t in a["topics"]}
    if set(prev_topics) != set(new_topics):
        out["measurement_changed"] = True
        out["params"].append("MEASUREMENT CHANGED: topics before = %s; now = %s. Tell the user why, or re-run with "
                             "the previous topics to keep results comparable." % (
                                 "; ".join("%s=%s" % (v, "|".join(k)) for k, v in prev_topics.items()),
                                 "; ".join("%s=%s" % (v, "|".join(k)) for k, v in new_topics.items())))

    def ranks(an):
        keys = _series_keys(an)
        res = {}
        for g in an["ranking"]["groups"]:
            for i, r in enumerate(g["rows"], 1):
                res[keys[r["id"]]] = (i, r["score"], r["name"])
        return res
    pr, nr = ranks(prev), ranks(a)
    for key, (rank, score, name) in sorted(nr.items(), key=lambda kv: (kv[0][0], kv[1][0])):
        if key in pr:
            old_rank, old_score, _ = pr[key]
            out["ranking"].append("%s: #%d -> #%d (score %.2f -> %.2f)" % (name, old_rank, rank, old_score or 0, score or 0))
        else:
            out["ranking"].append("%s: new, #%d (score %.2f)" % (name, rank, score or 0))
    pk, nk = _series_keys(prev), _series_keys(a)
    prev_by_key = {pk[s["id"]]: s for s in prev["series"]}
    for s in a["series"]:
        o = prev_by_key.get(nk[s["id"]])
        if o and o.get("growth_rel") is not None and s.get("growth_rel") is not None \
                and abs(o["growth_rel"] - s["growth_rel"]) > 0.005:
            out["growth"].append("%s: relative growth %+.0f%% -> %+.0f%%" % (s["name"], o["growth_rel"] * 100,
                                                                             s["growth_rel"] * 100))
    return out


def time_axes(start_date: dt.date, end_date: dt.date) -> dict:
    """Day list, month index per day, growth-window length k and the recent/previous masks."""
    month_list = months_in(start_date, end_date)
    n_months = len(month_list)
    days = [start_date + dt.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    month_pos = {m: i for i, m in enumerate(month_list)}
    month_idx = np.array([month_pos[d.strftime("%Y-%m")] for d in days])
    k = 12 if n_months >= 24 else n_months // 2
    rec_mask = month_idx >= n_months - k
    prev_mask = (month_idx >= n_months - 2 * k) & (month_idx < n_months - k)
    return {"days": days, "month_list": month_list, "n_months": n_months, "month_idx": month_idx, "k": k,
            "rec_mask": rec_mask, "prev_mask": prev_mask}


def _default_slug(topics, langs, start_date, end_date) -> str:
    names = "+".join(slugify(t["label"]) or t["key"] for t in topics)[:48].strip("+-") or "topics"
    return "%s_%s_%s_%s" % (names, "-".join(langs)[:30], start_date.strftime("%Y%m"), end_date.strftime("%Y%m"))


def event_step(num: np.ndarray, den: np.ndarray, day0: dt.date) -> Optional[dict]:
    """Step of sum(num)/sum(den) across the 2025 bot-detection update (Jul-Aug vs Mar-Apr 2025),
    divided by the same ratio a year earlier when that history exists (seasonal adjustment)."""
    def ratio(lo, hi):
        i, j = (lo - day0).days, (hi - day0).days + 1
        if i < 0 or j > len(num):
            return None
        d = den[i:j].sum()
        return num[i:j].sum() / d if d > 0 else None
    (b0, b1), (a0, a1) = EVENT_WINDOWS
    before, after = ratio(b0, b1), ratio(a0, a1)
    if not before or after is None:
        return None
    r = after / before
    back = lambda d: d.replace(year=d.year - 1)  # noqa: E731
    pb, pa = ratio(back(b0), back(b1)), ratio(back(a0), back(a1))
    adjusted = bool(pb and pa)
    if adjusted:
        r = r / (pa / pb)
    return {"rel": float(r - 1), "adjusted": adjusted}


def _series_metrics(arts, lang, arrays, total, redirect_info, days, month_idx, n_months, k, rec_mask, prev_mask,
                    month_list, with_models: bool = True, hist: Optional[dict] = None):
    """Metrics of one series (a basket of articles in one wiki) for the analysed period.

    `hist` (optional) carries the same series with extra history before the period
    ({arrays, total, off, days, month_list, month_idx, n_months}); it feeds the models, the
    year-over-year blocks, the bot-update step and the seasonal check of level shifts."""
    if hist:
        off = hist["off"]
        raw_full = np.sum([hist["arrays"][(lang, a["title"])] for a in arts], axis=0)
        total_full = hist["total"]
        clean_full, spike_full, med_full = stats.dampen_spikes(raw_full)
        raw, clean, spike, med = raw_full[off:], clean_full[off:], spike_full[off:], med_full[off:]
        h_days, h_months, h_idx, h_n = hist["days"], hist["month_list"], hist["month_idx"], hist["n_months"]
    else:
        off = 0
        raw = np.sum([arrays[(lang, a["title"])] for a in arts], axis=0)
        clean, spike, med = stats.dampen_spikes(raw)
        raw_full, clean_full, total_full = raw, clean, total
        h_days, h_months, h_idx, h_n = days, month_list, month_idx, n_months
    ones = np.ones_like(raw)
    m: dict = {"articles": [], "_samples": None, "_daily": (raw, clean, spike), "short_window": n_months < 24}

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

    shift = stats.level_shift(raw_full, min_index=off)
    m["level_shift"] = None
    if shift:
        sday = days[shift["index"] - off]
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
        mp = month_idx[prev_mask] - (n_months - 2 * k)  # month 0..k-1 within each comparison period
        mr = month_idx[rec_mask] - (n_months - k)
        rel = stats.ratio_growth(clean[prev_mask], total[prev_mask], clean[rec_mask], total[rec_mask],
                                 month_prev=mp, month_rec=mr)
        abs_ = stats.ratio_growth(clean[prev_mask], ones[prev_mask], clean[rec_mask], ones[rec_mask],
                                  month_prev=mp, month_rec=mr)
    if rel:
        m.update(growth_rel=rel["point"], growth_rel_lo=rel["lo"], growth_rel_hi=rel["hi"], growth_rel_p=rel["p"])
        m["_samples"] = rel
        m["growth_rel_with_spikes"] = float((raw[rec_mask].sum() / total[rec_mask].sum())
                                            / (raw[prev_mask].sum() / total[prev_mask].sum()) - 1) \
            if raw[prev_mask].sum() > 0 else None
    else:
        m.update(growth_rel=None, growth_rel_lo=None, growth_rel_hi=None, growth_rel_p=None,
                 growth_rel_with_spikes=None)
        if m["growth_note"] is None:
            m["growth_note"] = "no views in the comparison period"
    if abs_:
        m.update(growth_abs=abs_["point"], growth_abs_lo=abs_["lo"], growth_abs_hi=abs_["hi"])
        m["growth_abs_with_spikes"] = float(raw[rec_mask].sum() / raw[prev_mask].sum() - 1) \
            if raw[prev_mask].sum() > 0 else None
    else:
        m.update(growth_abs=None, growth_abs_lo=None, growth_abs_hi=None, growth_abs_with_spikes=None)

    mon_raw = stats.monthly_sums(raw, month_idx, n_months)
    mon_clean = stats.monthly_sums(clean, month_idx, n_months)
    mon_total = stats.monthly_sums(total, month_idx, n_months)
    with np.errstate(divide="ignore", invalid="ignore"):
        share = np.where(mon_total > 0, mon_clean / mon_total * 1e6, 0.0)
        share_raw = np.where(mon_total > 0, mon_raw / mon_total * 1e6, 0.0)
    trend = stats.annual_trend(share[max(0, first // 31):] if first > 0 else share)
    m["trend_annual"], m["trend_p"] = trend["annual"], trend["p"]
    if m["level_shift"] and m["level_shift"].get("kind") != "late_start":
        after_month = int(month_idx[min(len(days) - 1, days.index(dt.date.fromisoformat(m["level_shift"]["date"])) + 31)])
        if n_months - after_month >= 8:
            m["level_shift"]["trend_after"] = stats.annual_trend(share[after_month:])["annual"]
    m["months_up"] = stats.months_above_last_year(share) if m["growth_note"] is None else None

    def block_share(lo, hi):  # same definition as the headline: sum(dampened) / sum(wiki total)
        tot = mon_total[lo:hi].sum()
        return mon_clean[lo:hi].sum() / tot if tot > 0 else 0.0

    m["momentum_6m"] = None
    if n_months >= 18 and block_share(n_months - 18, n_months - 12) > 0:
        m["momentum_6m"] = float(block_share(n_months - 6, n_months) / block_share(n_months - 18, n_months - 12) - 1)

    # history (period + up to MODEL_MONTHS before it): yearly blocks, models, bot-update step
    h_clean = stats.monthly_sums(clean_full, h_idx, h_n)
    h_total = stats.monthly_sums(total_full, h_idx, h_n)
    with np.errstate(divide="ignore", invalid="ignore"):
        h_share = np.where(h_total > 0, h_clean / h_total * 1e6, 0.0)
    h_first = stats.first_active_index(raw_full)
    h_first_month = int(h_idx[h_first]) if h_first < len(h_days) else h_n
    m["history_months"] = h_n - h_first_month

    def h_block(lo, hi):
        tot = h_total[lo:hi].sum()
        return h_clean[lo:hi].sum() / tot if tot > 0 else 0.0
    m["yearly"] = []
    for j in range(h_n // 12 - 1, 0, -1):
        a0, a1 = h_n - 12 * (j + 1), h_n - 12 * j
        b1 = a1 + 12
        if a0 >= h_first_month and h_block(a0, a1) > 0:
            m["yearly"].append({"from": "%s..%s" % (h_months[a0], h_months[a1 - 1]),
                                "to": "%s..%s" % (h_months[a1], h_months[b1 - 1]),
                                "growth_rel": float(h_block(a1, b1) / h_block(a0, a1) - 1),
                                "growth_abs": float(h_clean[a1:b1].sum() / h_clean[a0:a1].sum() - 1)
                                if h_clean[a0:a1].sum() > 0 else None})
    m["monthly"] = {"views": [float(v) for v in mon_raw], "views_clean": [float(v) for v in mon_clean],
                    "share_ppm": [float(v) for v in share], "share_ppm_raw": [float(v) for v in share_raw]}
    m.update(_model_metrics(h_share, h_months, h_idx, h_first, len(h_days)) if with_models and m["growth_note"] is None
             else {"seasonality": None, "forecast": None, "changepoints": []})

    m["event_step"] = None
    ev = event_step(clean_full, total_full, h_days[0]) if len(h_days) else None
    if ev:
        lo_d, hi_d = EVENT_WINDOWS[0][0], EVENT_WINDOWS[1][1]
        in_period = days[int(np.argmax(prev_mask))] <= lo_d and hi_d <= days[-1]
        ev["flag"] = bool(in_period and m["growth_note"] is None and m["daily_avg_recent"] >= 10
                          and abs(math.log1p(ev["rel"])) >= math.log1p(EVENT_FLAG))
        m["event_step"] = ev

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


def _model_metrics(share, month_list, month_idx, first, n_days) -> dict:
    """Seasonality, 12-month forecast and changepoints of the monthly share (see models.py)."""
    out = {"seasonality": None, "forecast": None, "changepoints": []}
    fm = int(month_idx[first]) if first < n_days else len(month_list)
    ys = np.asarray(share[fm:], dtype=float)
    ms = list(month_list[fm:])
    if len(ys) < models.MIN_SEASONAL_MONTHS or (ys <= 0).mean() > 0.1:
        return out  # < 36 months: seasonality and forecasts cannot be told apart from noise
    logs = np.log(np.maximum(ys, ys[ys > 0].min() * 0.5))
    dec = models.seasonal_decompose(logs, ms)
    if dec:
        out["seasonality"] = {"strength": dec["strength"], "p": dec["p"], "significant": dec["significant"],
                              "years": dec["years"], "peak": dec["peak"], "low": dec["low"],
                              "indices": [float(v) for v in dec["indices"]]}
    fc = models.forecast(logs, ms)
    if fc:
        out["forecast"] = {"method": fc["method"], "chosen": fc["chosen"], "next12": fc["next12_vs_last12"],
                           "next12_lo80": fc["next12_lo80"],
                           "next12_hi80": fc["next12_hi80"], "skill": fc["skill"], "months": fc["months"],
                           "origins": fc["origins"], "history_months": fc["history_months"],
                           "backtest_mae": fc["backtest_mae"],
                           "median": [float(math.exp(v)) for v in fc["median"]],
                           "lo80": [float(math.exp(v)) for v in fc["lo80"]],
                           "hi80": [float(math.exp(v)) for v in fc["hi80"]]}
    cps = models.changepoints(logs - dec["seasonal"] if dec else logs, ms)
    for c in cps:
        y, mo = int(c["month"][:4]), int(c["month"][5:7])
        for lo_d, hi_d, _text in KNOWN_EVENTS:
            if dt.date(lo_d.year, lo_d.month, 1) <= dt.date(y, mo, 1) <= hi_d:
                c["known_event"] = "Wikimedia bot-detection update (May-June 2025)"
    out["changepoints"] = cps
    return out


def _apply_pooling(topics, langs, series) -> List[dict]:
    """Empirical-Bayes partial pooling of relative growth within each comparison group."""
    by_id = {s["id"]: s for s in series}
    info = []
    for group, ids in _groups(topics, langs):
        members = [by_id[i] for i in ids if by_id[i]["status"] == "ok"]
        est = [{"g": s["growth_rel"], "lo": s.get("growth_rel_lo"), "hi": s.get("growth_rel_hi")}
               if s.get("growth_rel") is not None else None for s in members]
        res = models.partial_pool(est)
        if not res:
            continue
        for s, it in zip(members, res["items"]):
            if it:
                s.update(growth_pooled=it["g"], growth_pooled_lo=it["lo"], growth_pooled_hi=it["hi"],
                         pooling_weight=it["weight"])
        info.append({"group": group, "mu": res["mu"], "tau": res["tau"], "k": res["k"]})
    return info


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
        valid = [i for i in ids if by_id[i].get("growth_rel") is not None and samples.get(i)]
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
                "growth": [s.get("growth_pooled", s.get("growth_rel")) for s in ok],
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
                    "share_per_million", "share_per_million_spike_dampened"])
        for s in analysis["series"]:
            if s["status"] != "ok":
                continue
            tot = analysis["project_totals"][s["lang"]]["monthly"]
            for i, month in enumerate(analysis["months"]):
                w.writerow([s["name"], s["topic"], s["lang"], month, int(s["monthly"]["views"][i]),
                            int(round(s["monthly"]["views_clean"][i])), int(tot[i]),
                            round(s["monthly"].get("share_ppm_raw", s["monthly"]["share_ppm"])[i], 3),
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
