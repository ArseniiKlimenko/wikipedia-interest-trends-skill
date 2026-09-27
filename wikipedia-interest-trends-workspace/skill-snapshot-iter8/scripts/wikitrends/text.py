"""Text outputs: the agent-facing summary, the editable narrative draft, and claim checks."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .i18n import fmt_int, lang_name, pct, tr, wiki_phrase

HOME_COUNTRIES = {"pl": ["PL"], "cs": ["CZ"], "sk": ["SK"], "uk": ["UA"], "de": ["DE", "AT", "CH"], "fr": ["FR"],
                  "it": ["IT"], "es": ["ES", "MX", "AR", "CO"], "pt": ["BR", "PT"], "tr": ["TR"], "vi": ["VN"],
                  "ru": ["RU"], "ja": ["JP"], "ko": ["KR"], "zh": ["CN", "TW", "HK"], "fa": ["IR"], "he": ["IL"],
                  "id": ["ID"], "th": ["TH"], "nl": ["NL", "BE"], "sv": ["SE"], "fi": ["FI"], "hu": ["HU"],
                  "ro": ["RO", "MD"], "el": ["GR", "CY"], "bg": ["BG"], "hr": ["HR"], "sr": ["RS"], "ar": ["EG", "SA", "DZ", "MA", "IQ"],
                  "hi": ["IN"], "bn": ["BD", "IN"], "da": ["DK"], "no": ["NO"], "lt": ["LT"], "lv": ["LV"], "et": ["EE"],
                  "ka": ["GE"], "kk": ["KZ"], "az": ["AZ"], "uz": ["UZ"], "be": ["BY"], "hy": ["AM"]}
GRADE = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW", "n/a": "N/A"}
DIRECTION = {"up": "growing", "down": "declining", "flat": "no clear change", "unclear": "unclear"}


def _ci(s: dict, key: str = "growth_rel") -> str:
    if s.get(key) is None:
        return "n/a"
    lo, hi = s.get(key + "_lo"), s.get(key + "_hi")
    if lo is None or hi is None:
        return pct(s[key])
    return "%s [%s, %s]" % (pct(s[key]), pct(lo), pct(hi))


# ---- summary for the agent ---------------------------------------------------------------
def summary_md(a: dict, files: Dict[str, str]) -> str:
    p, prm = a["period"], a["params"]
    k = p["growth_window_months"]
    ok = [s for s in a["series"] if s["status"] == "ok"]
    L: List[str] = ["# Wikipedia interest analysis", ""]
    L.append("Period %s..%s (%d months). Growth = last %d months (%s..%s) vs previous %d (%s..%s)."
             % (p["start"], p["end"], p["months"], k, p["recent"][0], p["recent"][1], k,
                p["previous"][0], p["previous"][1]))
    L.append("Traffic: agent=%s%s, access=%s; redirects mode=%s."
             % (prm["agent"], " (humans; known bots excluded)" if prm["agent"] == "user" else "",
                prm["access"], prm["redirects"]))
    L += ["", "## Rules for your reply (`report` checks the narrative against them)",
          "- A 95% interval that crosses 0 means \"no clear change\": never call it growth, a rise or a positive trend.",
          "- Each row is a language edition of Wikipedia, not a country: write \"Vietnamese-language readers\", not "
          "\"Vietnam\" (country data are in \"Where readers are\").",
          "- Relative growth is already net of the whole-wiki change: do not subtract it again or compare the two.",
          "- Quote only numbers from this summary and signals.md (same sign); add no outside market facts without a source."]

    ch = a.get("changes")
    if ch:
        L += ["", "## Changes vs previous analysis (%s%s)" % (
            ch["previous"], "; found automatically, pass --previous none to skip" if ch.get("auto") else "")]
        L += ["- " + x for x in ch["params"]] or ["- same settings"]
        if ch["ranking"]:
            L.append("Ranking (previous -> now):")
            L += ["  - " + x for x in ch["ranking"]]
        L += ["- " + x for x in ch["growth"]]
        L.append("Use this section for the 'what changed' part of your reply; do not reuse sentences from the "
                 "earlier answer.")

    L += ["", "## Articles used"]
    for t in a["topics"]:
        for lang, arts in t["articles"].items():
            s = next((x for x in a["series"] if x["topic"] == t["label"] and x["lang"] == lang), {})
            detail = {d["title"]: d for d in s.get("articles", [])}
            parts = []
            for art in arts:
                d = detail.get(art["title"], {})
                extra = []
                if d.get("redirects_added"):
                    extra.append("+%d redirects" % d["redirects_added"])
                if len(arts) > 1 and d:
                    extra.append("%.0f%% of views" % (d["share_of_basket"] * 100))
                    if d.get("growth_rel") is not None:
                        extra.append("rel. growth %s" % pct(d["growth_rel"]))
                parts.append('"%s" (%s)%s' % (art["title"], art["ref"], (" [" + ", ".join(extra) + "]") if extra else ""))
            miss = t["missing"].get(lang) or []
            L.append("- %s · %s: %s%s" % (t["label"], lang, "; ".join(parts) if parts else "NO ARTICLE",
                                           ("; missing: " + ", ".join(miss)) if miss and parts else ""))

    L += ["", "## Results", "",
          "| Series | Views/mo | Per 1M wiki views | Views chg (spikes damped) | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Next 12m forecast [80%] | Confidence |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in a["series"]:
        if s["status"] != "ok":
            L.append("| %s | - | - | - | no article | - | - | - | - | - | N/A |" % s["name"])
            continue
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %.0f%% | %s | %s (%s) |" % (
            s["name"], fmt_int(s["views_recent_month_avg"]),
            "%.1f" % s["share_ppm_recent"] if s.get("share_ppm_recent") is not None else "n/a",
            pct(s.get("growth_abs")), _ci(s), pct(s.get("momentum_6m")), pct(s.get("trend_annual")),
            "%d/12" % s["months_up"] if s.get("months_up") is not None else "n/a",
            s["spike_share"] * 100, _fc(s), GRADE[s["confidence"]["grade"]], DIRECTION[s["confidence"]["direction"]]))
    ctx = ", ".join("%s %s" % (lang, pct(v["growth"])) for lang, v in a["project_totals"].items())
    L.append("")
    L.append("Whole-wiki human views, same comparison: %s." % ctx)
    L.append("Reading guide: Relative growth = change in the topic's share of all views of that wiki "
             "(main interest signal; already net of the whole-wiki change above, so never subtract that change "
             "again). Views chg = change in reader numbers after dampening short spikes (values with spike days "
             "kept are in Confidence notes when they differ by 5+ pp). "
             "Per 1M wiki views = intensity of interest, comparable across languages. Confidence = trust in "
             "the direction of relative growth.")

    L += ["", "## Confidence notes"]
    for s in a["series"]:
        c = s["confidence"]
        line = "- %s: %s, %s." % (s["name"], GRADE[c["grade"]], DIRECTION[c["direction"]])
        if c["good"]:
            line += " Supports: " + "; ".join(c["good"]) + "."
        if c["bad"]:
            line += " Concerns: " + "; ".join(c["bad"]) + "."
        if s.get("top_spikes"):
            line += " Largest spikes: " + ", ".join("%s (x%.1f)" % (x["date"], x["x_normal"]) for x in s["top_spikes"]) + "."
        if s.get("growth_note"):
            line += " Note: %s." % s["growth_note"]
        ws, wa = s.get("growth_rel_with_spikes"), s.get("growth_abs_with_spikes")
        if (ws is not None and s.get("growth_rel") is not None and abs(ws - s["growth_rel"]) >= 0.05) or \
                (wa is not None and s.get("growth_abs") is not None and abs(wa - s["growth_abs"]) >= 0.05):
            line += " With spike days kept: relative %s, views %s (headline figures dampen spikes)." % (pct(ws), pct(wa))
        L.append(line)

    L += _models_section(a)

    yearly = [(s["name"], y) for s in ok for y in s.get("yearly", [])]
    if yearly:
        L += ["", "## Year over year (each 12-month block vs the block before it; uses history before the period)"]
        for name, y in yearly:
            L.append("- %s: %s compared with %s: relative %s, views %s" % (
                name, y["to"], y["from"], pct(y["growth_rel"]), pct(y.get("growth_abs"))))
        L.append("The last line is the same comparison as the headline relative growth.")

    if a["comparisons"]:
        L += ["", "## Comparisons (difference in relative growth, percentage points)"]
        for c in a["comparisons"]:
            L.append("- %s: %s vs %s: %+.0f pp [%+.0f, %+.0f] -> %s" % (
                c["group"], c["a"], c["b"], c["diff"] * 100, c["lo"] * 100, c["hi"] * 100,
                "clear difference" if c["clear"] else "difference not statistically clear"))

    rk = a["ranking"]
    if rk["groups"]:
        w = rk["weights"]
        L += ["", "## Opportunity ranking (weights size=%g, growth=%g, intensity=%g; 1 = best)" % (
            w["size"], w["growth"], w["intensity"])]
        for g in rk["groups"]:
            if len(rk["groups"]) > 1:
                L.append("%s:" % g["group"])
            for i, r in enumerate(g["rows"], 1):
                L.append("%d. %s - score %.2f (size %s, growth %s, intensity %s; confidence %s)" % (
                    i, r["name"], r["score"] or 0, _rk(r["size_rank"]), _rk(r["growth_rank"]),
                    _rk(r["intensity_rank"]), r["confidence"]))
        L.append("Scores rank series within each group only (percentile ranks); change weights with --weights."
                 + (" The growth component uses the partially pooled growth (see above)." if a.get("pooling") else ""))

    if a.get("geo"):
        L += ["", "## Where readers are (approx. share of each wiki's views, %s)" % p["end"][:7]]
        for lang, rows in a["geo"].items():
            if not rows:
                continue
            home = HOME_COUNTRIES.get(lang)
            if home and not any(r["country"] in home for r in rows):
                L.append("- %s.wikipedia: %s is withheld from Wikimedia's country data for reader safety, so the "
                         "country split is not usable here. Most readers are presumably in %s; do not describe "
                         "this audience as diaspora." % (lang, "/".join(home), "/".join(home)))
                continue
            L.append("- %s.wikipedia: %s" % (lang, ", ".join("%s %.0f%%" % (r["country"], r["share"] * 100)
                                                         for r in rows[:6] if r["share"] >= 0.01)))
        L.append("Country data is approximate and omits countries Wikimedia withholds for privacy/safety.")

    tips = suggestions(a)
    if tips:
        L += ["", "## Suggestions (consider before concluding)"] + ["- " + x for x in tips]

    if a["warnings"]:
        L += ["", "## Warnings"] + ["- " + w for w in a["warnings"]]

    L += ["", "## Files (in %s)" % a["outdir"]] + ["- %s: %s" % (k2, v.rsplit("/", 1)[-1]) for k2, v in files.items()]
    L.append("")
    L.append("Next: edit narrative.md (write it in the user's language), then run: "
             "wt.py report \"%s\"" % a["outdir"])
    return "\n".join(L) + "\n"


def _fc(s: dict) -> str:
    f = s.get("forecast")
    if not f or f.get("next12") is None:
        return "n/a"
    return "%s [%s, %s]" % (pct(f["next12"]), pct(f["next12_lo80"]), pct(f["next12_hi80"]))


def _strength_word(v: float) -> str:
    return "strong" if v >= 0.64 else "moderate" if v >= 0.36 else "weak"


def _models_section(a: dict) -> List[str]:
    ok = [s for s in a["series"] if s["status"] == "ok"]
    L = []
    if ok:
        L += ["", "## Seasonality, forecast and regime changes (monthly share of wiki views, with up to %d months "
              "of history)" % max((s.get("history_months") or 0) for s in ok)]
        for s in ok:
            parts = []
            hist = s.get("history_months") or 0
            se = s.get("seasonality")
            if se and se.get("significant"):
                parts.append("seasonality %s (%.2f; repeats across %d years, p=%.3f): peaks %s; low %s" % (
                    _strength_word(se["strength"]), se["strength"], se.get("years", 0), se["p"],
                    ", ".join("%s %s" % (mn, pct(v)) for mn, v in se["peak"]),
                    ", ".join("%s %s" % (mn, pct(v)) for mn, v in se["low"])))
            elif se:
                parts.append("no reliable seasonality (the month pattern does not repeat across %d years, p=%.2f; "
                             "do not describe peaks)" % (se.get("years", 0), se["p"]))
            f = s.get("forecast")
            if f and f.get("next12") is not None:
                mae = ", ".join("%s %.3f" % (k_, v) for k_, v in sorted((f.get("backtest_mae") or {}).items()))
                verdict = "model: %s, chosen by a rolling-origin backtest (%d origins, %d months of history; MAE %s)" % (
                    f["method"], f.get("origins") or 0, f.get("history_months") or hist, mae)
                parts.append("forecast next 12 months vs last 12: %s [80%%: %s, %s] (%s)" % (
                    pct(f["next12"]), pct(f["next12_lo80"]), pct(f["next12_hi80"]), verdict))
                if forecast_conflicts(s):
                    parts.append("NOTE: the forecast points against the measured change (recent months break the "
                                 "yearly pattern); do not present it as the expected outcome")
            if not se and not f and s.get("growth_note") is None:
                parts.append("no seasonality or forecast: needs 36+ months of history (this series has %d)" % hist)
            for c in s.get("changepoints", []):
                parts.append("regime change %s: level %s, trend %s/yr -> %s/yr%s" % (
                    c["month"], pct(c["level_jump"]), pct(c["trend_before"]), pct(c["trend_after"]),
                    " (coincides with the %s)" % c["known_event"] if c.get("known_event") else ""))
            if parts:
                L.append("- %s: %s." % (s["name"], "; ".join(parts)))
        L.append("Forecasts extrapolate the recent pattern; they cannot foresee news or product launches.")
    if a.get("pooling"):
        L += ["", "## Partial pooling (empirical Bayes; steadies small, noisy wikis)"]
        for g in a["pooling"]:
            L.append("- %s: common trend %s, between-series spread tau=%.2f (k=%d)." % (
                g["group"], pct(g["mu"]), g["tau"], g["k"]))
        for s in ok:
            if s.get("growth_pooled") is not None:
                L.append("  - %s: raw %s -> pooled %s [%s, %s] (weight on own data %.2f)" % (
                    s["name"], pct(s["growth_rel"]), pct(s["growth_pooled"]), pct(s["growth_pooled_lo"]),
                    pct(s["growth_pooled_hi"]), s.get("pooling_weight", 0)))
        L.append("Pooled values shrink noisy estimates toward the group's common trend; with tau=0 the data are "
                 "consistent with one shared trend. Quote raw growth as the measurement, pooled as the robust estimate.")
    return L


def suggestions(a: dict) -> List[str]:
    """Data-driven hints that make a follow-up run more reliable."""
    out = []
    for s in a["series"]:
        if s["status"] != "ok":
            continue
        if len(s.get("articles", [])) == 1 and s.get("daily_avg_recent", 0) < 50:
            art = s["articles"][0]["title"]
            out.append("%s is measured by one article (\"%s\", ~%.0f views/day). If the user means a broad subject "
                       "(a course, field or skill), add 3-5 core subtopics: run `wt.py related %s:%s`, pick "
                       "relevant QIDs, and re-run analyze with them in the same --topic."
                       % (s["name"], art, s["daily_avg_recent"], s["lang"], art))
        if s.get("driven_by"):
            out.append("%s: the result flips without \"%s\"; report it as driven by that article or split the "
                       "basket into separate topics." % (s["name"], s["driven_by"]))
        if s["confidence"]["grade"] == "low" and a["period"]["months"] < 36:
            out.append("%s has LOW confidence; a 36-month run (--months 36) shows whether the direction persists."
                       % s["name"])
    out = out[:5]
    if not (Path(a.get("outdir", "")) / "signals.json").exists():
        kws = " ".join('--keyword %s="<local phrase>"' % l for l in a["params"]["langs"][:3])
        out.append("Check demand outside Wikipedia before recommending: wt.py signals \"%s\" --trends %s (Google "
                   "Trends for the same topic per country via its unofficial endpoint + App Store competition); then "
                   "re-run report." % (a.get("outdir", "<dir>"), kws))
    return out


def _rk(v):
    return "n/a" if v is None else "%.2f" % v


# ---- narrative draft (editable by the agent) ---------------------------------------------------
def _month_names(pairs, t) -> str:
    en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return ", ".join(t["months"][en.index(m)] if m in en else m for m, _ in pairs)


def forecast_conflicts(s: dict) -> bool:
    """True when a forecast range points against a measured direction (interval excluding zero)."""
    f = s.get("forecast") or {}
    d = s["confidence"]["direction"] if s.get("confidence") else "unclear"
    if f.get("next12_lo80") is None or d not in ("up", "down"):
        return False
    return (d == "up" and f["next12_hi80"] < 0) or (d == "down" and f["next12_lo80"] > 0)


def narrative_draft(a: dict, lang: str = "en") -> str:
    t = tr(lang)
    k = a["period"]["growth_window_months"]
    ok = [s for s in a["series"] if s["status"] == "ok"]
    measurable = [s for s in ok if s.get("growth_rel") is not None]
    topics = ", ".join(x["label"] for x in a["topics"])
    conf = lambda s: t["conf"][s["confidence"]["grade"]]  # noqa: E731
    dirw = lambda s: t["dir"][s["confidence"]["direction"]]  # noqa: E731

    answer = []
    groups = _narrative_groups(a, measurable)
    if len(measurable) == 1:
        s = measurable[0]
        answer.append(t["answer_single"].format(topic=s["topic"], wiki=wiki_phrase(s["lang"], lang), dir=dirw(s),
                                                g=pct(s["growth_rel"]), k=k, conf=conf(s)))
    if len(groups) == 1:
        members = groups[0]
        srt = sorted(members, key=lambda s: -s["growth_rel"])
        best, worst = srt[0], srt[-1]
        if best["confidence"]["direction"] == "up":
            key = "answer_multi"
        elif all(s["confidence"]["direction"] == "down" for s in members):
            key = "answer_all_down"
        elif best["confidence"]["direction"] == "down":
            key = "answer_overall_none"  # the best estimate is a clear decline, others are unclear
        else:
            key = "answer_none_clear"
        answer.append(t[key].format(best=best["name"], g1=pct(best["growth_rel"]), c1=conf(best),
                                    lo1=pct(best.get("growth_rel_lo")), hi1=pct(best.get("growth_rel_hi")),
                                    worst=worst["name"], g2=pct(worst["growth_rel"]), c2=conf(worst)))
        comp = next((c for c in a["comparisons"] if c["a"] == best["name"] and c["b"] == worst["name"]), None)
        if comp:
            key = "answer_diff_clear" if comp["clear"] else "answer_diff_unclear"
            answer.append(t[key].format(d="%+.0f" % (comp["diff"] * 100), lo="%+.0f" % (comp["lo"] * 100),
                                        hi="%+.0f" % (comp["hi"] * 100)))
    elif len(groups) > 1:  # several topics x languages: one overall sentence + one short line per topic
        ups = [s["name"] for s in measurable if s["confidence"]["direction"] == "up"]
        if ups:
            answer.append(t["answer_overall_up"].format(names=", ".join(ups)))
        elif all(s["confidence"]["direction"] == "down" for s in measurable):
            answer.append(t["answer_overall_down"])
        else:
            answer.append(t["answer_overall_none"])
        for members in groups[:4]:
            srt = sorted(members, key=lambda s: -s["growth_rel"])
            answer.append(t["answer_group"].format(topic=members[0]["topic"], best=srt[0]["name"],
                                                   g1=pct(srt[0]["growth_rel"]), d1=dirw(srt[0]),
                                                   worst=srt[-1]["name"], g2=pct(srt[-1]["growth_rel"]),
                                                   d2=dirw(srt[-1])))

    evidence = []
    listed = ok
    if len(ok) > 6:  # keep the page readable: extremes of each group, the table has the rest
        per = 2 if len(groups) <= 2 else 1
        keep = {x["id"] for g in groups for x in (sorted(g, key=lambda s: -s["growth_rel"])[:per] +
                                                  sorted(g, key=lambda s: s["growth_rel"])[:1])}
        cap = 4 if len(ok) > 8 else 5
        listed = [s for s in ok if s["id"] in keep][:cap] or ok[:cap]
    for s in listed:
        evidence.append(t["series_line"].format(
            name=s["name"], views=fmt_int(s["views_recent_month_avg"], lang), g=pct(s.get("growth_rel")),
            lo=pct(s.get("growth_rel_lo")), hi=pct(s.get("growth_rel_hi")), dir=dirw(s), conf=conf(s)))
    for s in a["series"]:
        if s["status"] != "ok":
            evidence.append(t["no_article_line"].format(name=s["name"], lang=s["lang"]))
    for s in (listed if len(listed) <= 2 else []):
        f = s.get("forecast") or {}
        if f.get("next12") is not None:
            key = "forecast_conflict_line" if forecast_conflicts(s) else "forecast_line"
            evidence.append(t[key].format(name=s["name"], g=pct(f["next12"]), lo=pct(f["next12_lo80"]),
                                          hi=pct(f["next12_hi80"]), hist=f.get("history_months", "?")))
        se = s.get("seasonality") or {}
        if se.get("significant") and se.get("strength", 0) >= 0.36:
            evidence.append(t["season_line"].format(name=s["name"], peak=_month_names(se["peak"], t),
                                                    low=_month_names(se["low"], t), years=se.get("years", "?")))
    ctx = [(l, v["growth"]) for l, v in a["project_totals"].items() if v.get("growth") is not None]
    if ctx:
        evidence.append(t["context_line"].format(k=k, items=", ".join("%s %s" % (l, pct(g)) for l, g in ctx)))

    rec = []
    w = a["ranking"]["weights"]
    by_id = {s["id"]: s for s in a["series"]}
    wtxt = "size=%g, growth=%g, intensity=%g" % (w["size"], w["growth"], w["intensity"])
    for g in a["ranking"]["groups"]:
        top = by_id.get(g["rows"][0]["id"], {})
        if not top.get("confidence"):
            continue
        if top["confidence"]["direction"] == "down":
            ups = [by_id[r["id"]]["name"] for r in g["rows"] if by_id[r["id"]]["confidence"]["direction"] == "up"]
            rec.append(t["rec_rank_down"].format(top=top["name"], weights=wtxt, g=pct(top.get("growth_rel")),
                                                 conf=conf(top), ups=t["rec_ups"].format(names=", ".join(ups))
                                                 if ups else t["rec_no_ups"]))
        else:
            rec.append(t["rec_rank"].format(top=top["name"], weights=wtxt, g=pct(top.get("growth_rel")),
                                            dir=dirw(top), conf=conf(top)))
    if not rec and measurable:
        s = measurable[0]
        rec.append(t["rec_single_up"] if s["confidence"]["direction"] == "up" and s["confidence"]["grade"] != "low"
                   else t["rec_single_other"])

    nxt = []
    low = [s["name"] for s in ok if s["confidence"]["grade"] in ("low", "n/a")]
    if low:
        nxt.append(t["next_low"].format(names=", ".join(low[:2]) + (t["and_more"].format(n=len(low) - 2)
                                                                   if len(low) > 2 else "")))
    nxt.append(t["next_validate"])
    if len(ok) <= 8:
        nxt.append(t["next_rerun"])

    changed = []
    ch = a.get("changes")
    if ch:
        def move(line):  # "name: #3 -> #1 (...)" -> 2; new entries count as large moves
            m_ = re.search(r"#(\d+) -> #(\d+)", line)
            return abs(int(m_.group(1)) - int(m_.group(2))) if m_ else 5
        moves = sorted(ch["ranking"], key=move, reverse=True)[:3 if len(ok) > 6 else 6]
        changed = [x for x in ch["params"] if not x.startswith("MEASUREMENT")] + moves

    title = t["default_title"].format(topics=topics)
    out = ["<!-- Draft generated from the data. Edit it in the user's language: keep the first section as the",
           "     short answer; any other '##' sections appear beside the chart. Numbers must match summary.md;",
           "     `wt.py report` checks numbers, signs, directions and confidence words against the analysis. -->",
           "# " + title, "",
           "## " + t["answer"], " ".join(answer) or "-", "",
           "## " + t["evidence"]] + ["- " + e for e in evidence] + ["",
           "## " + t["recommendation"]] + ["- " + r for r in rec] + ["",
           "## " + t["next_steps"]] + ["- " + n for n in nxt]
    if changed:
        out += ["", "## " + t["what_changed"]] + ["- " + c for c in changed]
    return "\n".join(out) + "\n"


def _narrative_groups(a: dict, measurable: List[dict]) -> List[List[dict]]:
    """Same grouping as comparisons: languages within each topic, or topics within one language."""
    langs = a["params"]["langs"]
    if len(langs) > 1:
        keys = [(t["label"], [s for s in measurable if s["topic"] == t["label"]]) for t in a["topics"]]
    else:
        keys = [(langs[0], measurable)]
    return [members for _, members in keys if len(members) >= 2]


# ---- narrative parsing & claim checks ---------------------------------------------------------------
def parse_narrative(text: str) -> Tuple[str, List[Tuple[str, List[str]]]]:
    """Return (title, [(heading, lines)]) from a small markdown file."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    title, sections, current = "", [], None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif line.startswith("## "):
            current = (line[3:].strip(), [])
            sections.append(current)
        elif line.strip() and current is not None:
            current[1].append(line.strip())
        elif line.strip() and current is None and title:
            current = ("", [line.strip()])
            sections.append(current)
    return title, sections


# Claim check: every number, sign, direction word and confidence word in the narrative is compared
# with the analysis. Errors make `report` exit with code 1 (the PDF is still written).
GROWTH_RE = re.compile(r"(grow|grew|growth|rise[sn]?\b|rising|rose\b|increas|upward|\bup\b|gain|positive|expand|"
                       r"зріс|зрос|росте|ростуть|збільш|підвищ|приріст|позитивн|підйом|пожвав)", re.I)
DECLINE_RE = re.compile(r"(declin|\bfall|\bfell\b|drop|decreas|downward|\bdown\b|shrink|negative|спад|падін|падає|"
                        r"впав|впала|знизи|зниж|зменш|скороч|негативн)", re.I)
NEGATION_RE = re.compile(r"(\bno\b|\bnot\b|n't\b|\bwithout\b|\bnone\b|\bneither\b|\bне\b|\bні\b|\bбез\b|жоден|"
                         r"жодн|\bнема)", re.I)
METRIC_NAME_RE = re.compile(r"(relative|pooled|відносн\w*|об.?єднан\w*)\s+(growth|change|зростанн\w*|змін\w*)"
                            r"|(size|розмір\w*( аудиторії)?)\s*,\s*(growth|зростанн\w*)"
                            r"|(growth|зростанн\w*)\s+(and|та|і|й)\s+(intensity|інтенсивн\w*)"
                            r"|(growth|зростанн\w*)\s*=\s*\d|(weight|ваг)\w*[^.;]{0,30}(growth|зростанн\w*)", re.I)
AFTER_NEGATION_RE = re.compile(r"^\W{0,3}\w*\W{0,3}(\w+\W+){0,5}?(немає|нема|відсутн|none|not found)\b", re.I)
WIKI_TOTAL_RE = re.compile(r"(whole[- ]wiki|whole wikipedia|all (human )?views|total views|total traffic|overall|"
                           r"wiki-wide|site-wide|the site|the wiki as a whole|загал|усі перегляди|всі перегляди|"
                           r"усіх переглядів|всіх переглядів|розділ\w* в цілому|цілого розділу|всього розділу|"
                           r"усього розділу|по сайту|всього сайту|по розділу|трафік\w* розділу)", re.I)
SIGNAL_RE = re.compile(r"(forecast|прогноз|trends|app store|google|магазин)", re.I)
GEO_CONTEXT_RE = re.compile(r"(reader|traffic|visitor|countr|trends|app store|store|search|geo|share of views|"
                            r"читач|трафік|відвідув|країн|магазин|пошук|google)", re.I)
CONF_EN = re.compile(r"\b(high|medium|moderate|low)\s+confidence|confidence\W{0,3}(?:is\s+)?(high|medium|moderate|low)\b", re.I)
CONF_UK = re.compile(r"(висок|середн|помірн|низьк)\w*\s+(?:рів\w+\s+)?(?:довір|надійн)|(?:довір|надійн)\w*\W{0,3}"
                     r"(?:—\s*|-\s*)?(висок|середн|помірн|низьк)", re.I)
CONF_MAP = {"high": "high", "висок": "high", "medium": "medium", "moderate": "medium", "середн": "medium",
            "помірн": "medium", "low": "low", "низьк": "low"}
PCT_RE = re.compile(r"(?<![\w.,])([+\-−–]?\s?)(\d+(?:[.,]\d+)?)\s?(%|pp\b|п\.\s?п\.|p\.p\.|в\.п\.)")
NUM_RE = re.compile(r"(?<![\w.,\-−–/])(\d{1,3}(?:[ ,  ]\d{3})+|\d+(?:[.,]\d+)?)\s?"
                    r"(k\b|K\b|тис\.?|thousand|M\b|млн|million|B\b|млрд|billion|x\b|×|раз[аи]?\b)?(?![\w%])")
INTERVAL_CTX = re.compile(r"(interval|\bci\b|ді\b|діапазон|range|інтервал|confiden|довір|percentile|прогноз|forecast)", re.I)
RU_RE = re.compile(r"[ыэъё]|\b(имеет|январ\w*|феврал\w*|который|которая|также|если|однако|только|является|можно|"
                   r"нужно|очень|сейчас|интерес|рост\b)\b", re.I)
CJK_RE = re.compile(r"[぀-ヿ㐀-鿿가-힯]")
_UK_NAMES = {"PL": "Польщ", "CZ": "Чехі", "SK": "Словаччин", "UA": "Україн(?!сь)", "DE": "Німеччин",
             "AT": "Австрі", "CH": "Швейцарі", "FR": "Франці", "IT": "Італі", "ES": "Іспані", "MX": "Мексик",
             "AR": "Аргентин", "CO": "Колумбі", "BR": "Бразилі", "PT": "Португалі", "TR": "Туреччин",
             "VN": "В'єтнам(?!сь)", "RU": "Росі", "JP": "Японі", "KR": "Коре[яї]", "CN": "Кита[йю]", "ID": "Індонезі",
             "NL": "Нідерланд", "SE": "Швеці", "RO": "Румуні", "GR": "Греці", "HU": "Угорщин", "IN": "Інді[яї]",
             "IR": "Іран", "IL": "Ізраїл", "EG": "Єгипт", "BG": "Болгарі", "HR": "Хорвааті", "RS": "Сербі",
             "FI": "Фінлянді", "DK": "Дані[яї]", "NO": "Норвегі", "TH": "Таїланд", "GE": "Грузі", "KZ": "Казахстан",
             "BY": "Білорус(?!ьк)"}
_EN_NAMES = {"PL": "Poland", "CZ": "Czech Republic|Czechia", "SK": "Slovakia", "UA": "Ukraine", "DE": "Germany",
             "AT": "Austria", "CH": "Switzerland", "FR": "France", "IT": "Italy", "ES": "Spain", "MX": "Mexico",
             "AR": "Argentina", "CO": "Colombia", "BR": "Brazil", "PT": "Portugal", "TR": "Turkey|Türkiye",
             "VN": "Vietnam|Viet Nam", "RU": "Russia", "JP": "Japan", "KR": "Korea", "CN": "China", "ID": "Indonesia",
             "NL": "Netherlands", "SE": "Sweden", "RO": "Romania", "GR": "Greece", "HU": "Hungary", "IN": "India",
             "IR": "Iran", "IL": "Israel", "EG": "Egypt", "BG": "Bulgaria", "HR": "Croatia", "RS": "Serbia",
             "FI": "Finland", "DK": "Denmark", "NO": "Norway", "TH": "Thailand", "GE": "Georgia", "KZ": "Kazakhstan",
             "BY": "Belarus"}


def _norm(text: str) -> str:
    return text.replace("ʼ", "'").replace("’", "'").replace("`", "'")


def _known_values(a: dict, signals: Optional[dict] = None):
    """Computed values as (value in %, kind, series id or None, lang or None); kind 'g' = signed change,
    's' = unsigned share/level."""
    vals: List[Tuple[float, str, Optional[str], Optional[str]]] = []

    def add(v, kind, sid=None, lang=None, scale=100.0):
        if isinstance(v, (int, float)) and v == v:
            vals.append((float(v) * scale, kind, sid, lang))

    for s in a["series"]:
        sid, lang = s["id"], s["lang"]
        for key in ("growth_rel", "growth_rel_lo", "growth_rel_hi", "growth_abs", "growth_abs_lo", "growth_abs_hi",
                    "growth_rel_with_spikes", "growth_abs_with_spikes", "momentum_6m", "trend_annual",
                    "growth_pooled", "growth_pooled_lo", "growth_pooled_hi"):
            add(s.get(key), "g", sid, lang)
        for key in ("spike_share", "top_article_share"):
            add(s.get(key), "s", sid, lang)
        for y in s.get("yearly", []):
            add(y.get("growth_rel"), "g", sid, lang)
            add(y.get("growth_abs"), "g", sid, lang)
        for d in s.get("articles", []):
            add(d.get("growth_rel"), "g", sid, lang)
            add(d.get("share_of_basket"), "s", sid, lang)
        if s.get("months_up") is not None:
            add(s["months_up"] / 12.0, "s", sid, lang)
        f = s.get("forecast") or {}
        for key in ("next12", "next12_lo80", "next12_hi80"):
            add(f.get(key), "g", sid, lang)
        se = s.get("seasonality") or {}
        for _mn, v in (se.get("peak") or []) + (se.get("low") or []):
            add(v, "g", sid, lang)
        for c in s.get("changepoints", []):
            for key in ("level_jump", "trend_before", "trend_after"):
                add(c.get(key), "g", sid, lang)
        add((s.get("event_step") or {}).get("rel"), "g", sid, lang)
    by_name = {s["name"]: s["id"] for s in a["series"]}
    for g in a.get("pooling", []):
        add(g.get("mu"), "g")
    for c in a["comparisons"]:
        for key in ("diff", "lo", "hi"):
            add(c[key], "g", by_name.get(c["a"]))
            add(c[key], "g", by_name.get(c["b"]))
    for lang, v in a["project_totals"].items():
        add(v.get("growth"), "g", None, lang)
        add((v.get("event_step") or {}).get("rel"), "g", None, lang)
    for lang, rows in (a.get("geo") or {}).items():
        for r in rows:
            add(r["share"], "s", None, lang)
    for r in (signals or {}).get("rows", []):
        tr_ = r.get("trends") or {}
        for key in ("growth", "lo", "hi"):
            add(tr_.get(key), "g", None, r.get("lang"))
        ap = r.get("appstore") or {}
        for key in ("leader_share", "new_ratings_share"):
            add(ap.get(key), "s", None, r.get("lang"))
    return vals


def _known_absolute(a: dict, signals: Optional[dict] = None) -> List[float]:
    out: List[float] = [1000.0, 1e6, 2000.0]
    for s in a["series"]:
        for key in ("views_recent_month_avg", "views_prev_month_avg", "daily_avg_recent", "share_ppm_recent"):
            if s.get(key) is not None:
                out.append(float(s[key]))
        mon = s.get("monthly") or {}
        for key in ("views", "views_clean"):
            vals = mon.get(key) or []
            out += [float(v) for v in vals]
            if vals:
                out += [float(sum(vals)), float(sum(vals[-12:])), float(sum(vals[-24:-12]))]
        for d in s.get("articles", []):
            out.append(float(d.get("views_recent_month_avg") or 0))
        out += [float(x["views"]) for x in s.get("top_spikes", [])]
        ls = s.get("level_shift") or {}
        out += [float(ls[k]) for k in ("before", "after") if ls.get(k) is not None]
    for v in a["project_totals"].values():
        out += [float(x) for x in v.get("monthly", [])]
        if v.get("monthly"):
            out += [float(sum(v["monthly"][-12:])), float(sum(v["monthly"][-12:])) / 12]
    for r in (signals or {}).get("rows", []):
        ap = r.get("appstore") or {}
        for key in ("apps_found", "apps_relevant", "top_ratings_total", "top_ratings_median", "top_n"):
            if ap.get(key) is not None:
                out.append(float(ap[key]))
        out += [float(x["ratings"]) for x in ap.get("top", [])]
    return out


def _known_ratios(a: dict) -> List[float]:
    out = []
    for s in a["series"]:
        for key in ("growth_rel", "growth_abs", "growth_rel_with_spikes", "growth_abs_with_spikes"):
            if s.get(key) is not None:
                out += [1 + s[key], 1 / (1 + s[key]) if s[key] > -1 else 0]
        ls = s.get("level_shift") or {}
        if ls.get("ratio"):
            out += [ls["ratio"], 1 / ls["ratio"] if ls["ratio"] else 0]
        out += [x["x_normal"] for x in s.get("top_spikes", [])]
        if s.get("views_prev_month_avg"):
            out.append(s["views_recent_month_avg"] / s["views_prev_month_avg"])
    ok = [s for s in a["series"] if s.get("views_recent_month_avg")]
    for x in ok:  # "X is 3 times larger than Y"
        for y in ok:
            if x is not y and y["views_recent_month_avg"]:
                out.append(x["views_recent_month_avg"] / y["views_recent_month_avg"])
                if x.get("share_ppm_recent") and y.get("share_ppm_recent"):
                    out.append(x["share_ppm_recent"] / y["share_ppm_recent"])
    return out


def _aliases(a: dict) -> Dict[str, List[re.Pattern]]:
    """Regexes that identify each series in free text (series name, language code, language name)."""
    from .i18n import LANG_NAMES
    common = {"it", "de", "es", "is", "no", "be", "to", "in", "as", "id", "he", "an", "am", "or", "so", "et",
              "la", "da", "ms", "hi", "ca", "eu", "gl", "uk", "en", "pt", "fa", "ar"}
    langs = a["params"]["langs"]
    topics = a["topics"]
    out: Dict[str, List[re.Pattern]] = {}
    for s in a["series"]:
        lang = s["lang"]
        pats = [re.escape(_norm(s["name"]))]
        lang_pats = [r"\b%s\.wikipedia" % re.escape(lang), r"\(%s\)" % re.escape(lang), r"\b%swiki\b" % re.escape(lang),
                     r"\b%s:" % re.escape(lang)]
        if lang not in common:
            lang_pats.append(r"\b%s\b" % re.escape(lang))
        names = LANG_NAMES.get(lang)
        if names:
            lang_pats.append(r"\b%s\b" % re.escape(names[0].lower()))
            uk = _norm(names[1])
            if len(uk) > 5 and uk.endswith(("ська", "цька")):
                lang_pats.append(re.escape(uk[:-2]))
            elif len(uk) >= 4:
                lang_pats.append(re.escape(uk))
        if len(langs) > 1 and len(topics) > 1:  # needs the topic too, unless the name itself is quoted
            topic = re.escape(_norm(s["topic"]).lower())
            pats += ["(?=.*%s)(?=.*(?:%s))" % (topic, "|".join(lang_pats))]
        elif len(langs) > 1:
            pats += lang_pats
        else:
            pats += [re.escape(_norm(s["topic"]).lower())] if len(topics) > 1 else lang_pats + [re.escape(_norm(s["topic"]).lower())]
        out[s["id"]] = [re.compile(p_, re.I) for p_ in pats]
    return out


def _clauses(body: str) -> List[Tuple[int, str]]:
    """(line number, clause) pairs: sentences and ';'-separated parts of each line."""
    out = []
    for n, line in enumerate(body.splitlines()):
        line = line.strip()
        if not line or line.startswith("#") and not line.startswith("##"):
            continue
        line = re.sub(r"^##\s*", "", line)
        for part in re.split(r"(?<=[.!?;])\s+", line):
            if part.strip():
                out.append((n, part.strip()))
    return out


def _direction_words(clause: str, regex: re.Pattern, names: List[str] = ()) -> bool:
    text = METRIC_NAME_RE.sub(" ", clause)
    for nm in names:  # series names and topic labels may contain such words ("Growing", "Rise of ...")
        text = re.sub(re.escape(nm), " ", text, flags=re.I)
    for m in regex.finditer(text):
        before = text[max(0, m.start() - 30):m.start()]
        if not NEGATION_RE.search(before) and not AFTER_NEGATION_RE.search(text[m.end():m.end() + 40]):
            return True
    return False


def check_narrative(a: dict, narrative: str, signals: Optional[dict] = None, lang: str = "en") -> Dict[str, List[str]]:
    """Compare the narrative with the analysis. Returns {"errors": [...], "warnings": [...]}.

    Errors: a percentage that matches no computed value (for the series the sentence names), a sign
    that is flipped, a direction word that contradicts the data (e.g. "growth" for an interval that
    crosses zero), a wrong confidence level. Warnings: countries used for language editions, plain
    numbers or multipliers not found in the data, comparisons of relative growth with the whole-wiki
    change, Russian or CJK characters in an English/Ukrainian text, an unfinished draft."""
    errors: List[str] = []
    warns: List[str] = []
    body = _norm(re.sub(r"<!--.*?-->", "", narrative, flags=re.S))
    known = _known_values(a, signals)
    absolute = _known_absolute(a, signals)
    ratios = _known_ratios(a)
    aliases = _aliases(a)
    by_id = {s["id"]: s for s in a["series"]}
    measurable = [s for s in a["series"] if s.get("growth_rel") is not None]

    names = sorted({_norm(x) for s in a["series"] for x in (s["name"], s["topic"])}, key=len, reverse=True)

    def near(v, kv):
        return abs(abs(v) - abs(kv)) <= max(1.01, 0.05 * abs(kv))

    last_line, carried = -1, []
    for line_no, clause in _clauses(body):
        low = clause.lower()
        mentioned = [sid for sid, pats in aliases.items() if any(p_.search(low) for p_ in pats)]
        if not mentioned and line_no == last_line:
            mentioned = carried  # "X: 950/month; relative growth -34%; ..." - later parts still talk about X
        last_line, carried = line_no, mentioned
        mlangs = {by_id[i]["lang"] for i in mentioned}
        cands = [k_ for k_ in known if not mentioned or k_[2] in mentioned or (k_[2] is None and (k_[3] in mlangs or k_[3] is None))]
        short = clause if len(clause) <= 110 else clause[:107] + "..."
        for m in PCT_RE.finditer(clause):
            sign_txt, num = m.group(1).strip(), m.group(2).replace(",", ".")
            try:
                v = float(num)
            except ValueError:
                continue
            ctx = clause[max(0, m.start() - 30):m.end() + 30]
            if v in (80.0, 95.0, 90.0) and INTERVAL_CTX.search(ctx):
                continue
            if v == 100.0 and re.search(r"(=\s*100|index|індекс|base|баз)", ctx, re.I):
                continue
            sign = 0 if not sign_txt else (1 if sign_txt == "+" else -1)
            hits = [k_ for k_ in cands if near(v, k_[0]) and (sign == 0 or k_[1] == "s" or abs(k_[0]) < 0.5
                                                              or (k_[0] > 0) == (sign > 0))]
            label = "'%s%s%s'" % (sign_txt, m.group(2), m.group(3))
            if not hits:
                flipped = [k_ for k_ in cands if k_[1] == "g" and near(v, k_[0]) and abs(k_[0]) >= 0.5]
                elsewhere = [k_ for k_ in known if near(v, k_[0])]
                if sign and flipped:
                    errors.append("%s has the wrong sign: the data say %+.0f%% (in: \"%s\")" % (label, flipped[0][0], short))
                elif mentioned and elsewhere:
                    errors.append("%s is not a value of %s (it belongs to another series or metric) (in: \"%s\")"
                                  % (label, ", ".join(by_id[i]["name"] for i in mentioned), short))
                else:
                    errors.append("%s matches no computed metric (in: \"%s\")" % (label, short))
                continue
            if sign == 0 and all(k_[1] == "g" for k_ in hits) and not SIGNAL_RE.search(clause):
                if _direction_words(clause, GROWTH_RE, names) and all(k_[0] < -0.5 for k_ in hits) \
                        and not _direction_words(clause, DECLINE_RE, names):
                    errors.append("%s is a decline in the data, but the sentence calls it growth (in: \"%s\")" % (label, short))
                elif _direction_words(clause, DECLINE_RE, names) and all(k_[0] > 0.5 for k_ in hits) \
                        and not _direction_words(clause, GROWTH_RE, names):
                    errors.append("%s is an increase in the data, but the sentence calls it a decline (in: \"%s\")" % (label, short))

        # direction words about one named series (no number needed)
        if len(mentioned) == 1 and not SIGNAL_RE.search(clause) and not WIKI_TOTAL_RE.search(clause):
            s = by_id[mentioned[0]]
            d = s["confidence"]["direction"] if s.get("confidence") else "unclear"
            up_w, down_w = _direction_words(clause, GROWTH_RE, names), _direction_words(clause, DECLINE_RE, names)
            if up_w and not down_w and d in ("flat", "down"):
                errors.append("the sentence describes %s as growing, but its 95%% interval %s: write '%s' "
                              "(in: \"%s\")" % (s["name"], "crosses zero" if d == "flat" else "is below zero",
                                                 "no clear change" if d == "flat" else "declining", short))
            elif down_w and not up_w and (d == "up" or (d == "flat" and (s.get("growth_rel") or 0) > 0)):
                errors.append("the sentence describes %s as declining, but %s (in: \"%s\")"
                              % (s["name"], "it grows" if d == "up" else "its estimate is positive and the interval "
                                 "crosses zero ('no clear change')", short))
            for rx in (CONF_EN, CONF_UK):
                for cm in rx.finditer(low):
                    word = next(g_ for g_ in cm.groups() if g_)
                    level = next((v_ for k_, v_ in CONF_MAP.items() if word.lower().startswith(k_)), None)
                    grade = s["confidence"]["grade"]
                    if level and grade in ("high", "medium", "low") and level != grade:
                        errors.append("the confidence for %s is %s, not %s (in: \"%s\")" % (s["name"], grade.upper(),
                                                                                            level.upper(), short))

        # relative growth compared with the whole-wiki change (double counting)
        if WIKI_TOTAL_RE.search(clause) and re.search(r"(more than|less than|faster|slower|than the|compared|"
                                                      r"більш\w*,? ніж|менш\w*,? ніж|швидше|повільніше|порівняно)", low):
            if any(PCT_RE.finditer(clause)):
                warns.append("this sentence compares relative growth with the whole-wiki change; relative growth is "
                             "already net of that change, so the comparison double-counts it (in: \"%s\")" % short)

        # countries used for language editions
        if not GEO_CONTEXT_RE.search(clause):
            for lang_ in a["params"]["langs"]:
                for cc in HOME_COUNTRIES.get(lang_, [])[:2]:
                    for pat in (_EN_NAMES.get(cc), _UK_NAMES.get(cc)):
                        if pat and re.search(r"\b(?:%s)" % pat, clause):
                            warns.append("'%s' is a country, but the data describe the %s-language Wikipedia (%s); "
                                         "name the language audience unless you cite country data (in: \"%s\")"
                                         % (re.search(r"\b(?:%s)\w*" % pat, clause).group(0), lang_, lang_, short))

        # plain numbers and multipliers
        for m in NUM_RE.finditer(clause):
            raw_num, unit = m.group(1), (m.group(2) or "")
            if re.match(r"^(19|20)\d{2}$", raw_num) or m.end() < len(clause) and clause[m.end():m.end() + 1] in "%-":
                continue
            try:
                v = float(re.sub(r"[ ,  ]", "", raw_num) if re.search(r"\d[ ,  ]\d{3}", raw_num)
                          else raw_num.replace(",", "."))
            except ValueError:
                continue
            ul = unit.lower().rstrip(".")
            if ul in ("x", "×") or ul.startswith("раз"):
                if not any(abs(v - r_) <= max(0.06 * r_, 0.051) for r_ in ratios if r_):
                    warns.append("'%s %s' does not match a ratio in the data (in: \"%s\")" % (raw_num, unit, short))
                continue
            mult = {"k": 1e3, "тис": 1e3, "thousand": 1e3, "m": 1e6, "млн": 1e6, "million": 1e6, "b": 1e9,
                    "млрд": 1e9, "billion": 1e9}.get(ul, 1.0)
            v *= mult
            if v < 100:
                continue
            step = mult * (10 ** -len(raw_num.split(".")[1]) if "." in raw_num else 1) * 0.5 if mult > 1 else 0.5
            if not any(abs(v - kv) <= max(0.03 * kv, step, 0.5) for kv in absolute):
                warns.append("'%s%s' is not a number from the analysis or signals (in: \"%s\"); if it comes from "
                             "outside, cite the source, otherwise remove it" % (raw_num, (" " + unit) if unit else "", short))

    if lang == "uk" and RU_RE.search(body):
        hits = sorted({m.group(0) for m in RU_RE.finditer(body)})[:6]
        warns.append("Russian letters or words in a Ukrainian text: %s" % ", ".join(hits))
    if not any(l_ in ("zh", "ja", "ko") for l_ in a["params"]["langs"]) and CJK_RE.search(body):
        warns.append("Chinese/Japanese/Korean characters in the text: %s" % "".join(CJK_RE.findall(body))[:20])
    if re.search(r"\bTODO\b", body):
        errors.append("narrative still contains TODO")
    return {"errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warns))}


def check_claims(a: dict, narrative: str) -> List[str]:
    """Backward-compatible wrapper: the error list of check_narrative()."""
    return check_narrative(a, narrative)["errors"]
