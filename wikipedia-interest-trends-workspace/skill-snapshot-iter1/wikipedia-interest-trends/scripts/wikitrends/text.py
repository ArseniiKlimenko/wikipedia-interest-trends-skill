"""Text outputs: the agent-facing summary, the editable narrative draft, and claim checks."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

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
          "| Series | Views/mo | Per 1M wiki views | Views chg | Relative growth [95% CI] | Last 6m YoY | Trend/yr | Months up | Spikes | Confidence |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for s in a["series"]:
        if s["status"] != "ok":
            L.append("| %s | - | - | - | no article | - | - | - | - | N/A |" % s["name"])
            continue
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %.0f%% | %s (%s) |" % (
            s["name"], fmt_int(s["views_recent_month_avg"]),
            "%.1f" % s["share_ppm_recent"] if s.get("share_ppm_recent") is not None else "n/a",
            pct(s.get("growth_abs")), _ci(s), pct(s.get("momentum_6m")), pct(s.get("trend_annual")),
            "%d/12" % s["months_up"] if s.get("months_up") is not None else "n/a",
            s["spike_share"] * 100, GRADE[s["confidence"]["grade"]], DIRECTION[s["confidence"]["direction"]]))
    ctx = ", ".join("%s %s" % (lang, pct(v["growth"])) for lang, v in a["project_totals"].items())
    L.append("")
    L.append("Whole-wiki human views, same comparison: %s." % ctx)
    L.append("Reading guide: Relative growth = change in the topic's share of all views of that wiki "
             "(main interest signal; removes Wikipedia-wide traffic trends). Views chg = raw reader numbers. "
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
        L.append(line)

    yearly = [(s["name"], y) for s in ok for y in s.get("yearly", [])]
    if yearly:
        L += ["", "## Year over year (relative growth; views change)"]
        for name, y in yearly:
            L.append("- %s: %s -> %s: %s; %s" % (name, y["from"], y["to"], pct(y["growth_rel"]), pct(y.get("growth_abs"))))

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
        L.append("Scores rank series within each group only (percentile ranks); change weights with --weights.")

    if a.get("geo"):
        L += ["", "## Where readers are (approx. share of each wiki's views, %s)" % p["end"][:7]]
        for lang, rows in a["geo"].items():
            if rows:
                line = "- %s.wikipedia: %s" % (lang, ", ".join("%s %.0f%%" % (r["country"], r["share"] * 100)
                                                             for r in rows[:6] if r["share"] >= 0.01))
                home = HOME_COUNTRIES.get(lang)
                if home and not any(r["country"] in home for r in rows):
                    line += " (home country %s not reported - likely withheld by Wikimedia for reader safety; " \
                            "shares describe the remaining traffic only)" % "/".join(home)
                L.append(line)
        L.append("Country data is approximate and omits countries Wikimedia withholds for privacy/safety.")

    if a["warnings"]:
        L += ["", "## Warnings"] + ["- " + w for w in a["warnings"]]

    L += ["", "## Files (in %s)" % a["outdir"]] + ["- %s: %s" % (k2, v.rsplit("/", 1)[-1]) for k2, v in files.items()]
    L.append("")
    L.append("Next: edit narrative.md (write it in the user's language), then run: "
             "wt.py report \"%s\"" % a["outdir"])
    return "\n".join(L) + "\n"


def _rk(v):
    return "n/a" if v is None else "%.2f" % v


# ---- narrative draft (editable by the agent) ---------------------------------------------------
def narrative_draft(a: dict, lang: str = "en") -> str:
    t = tr(lang)
    k = a["period"]["growth_window_months"]
    ok = [s for s in a["series"] if s["status"] == "ok"]
    measurable = [s for s in ok if s.get("growth_rel") is not None]
    topics = ", ".join(x["label"] for x in a["topics"])
    conf = lambda s: t["conf"][s["confidence"]["grade"]]  # noqa: E731

    answer = []
    groups = _narrative_groups(a, measurable)
    if len(measurable) == 1:
        s = measurable[0]
        answer.append(t["answer_single"].format(topic=s["topic"], wiki=wiki_phrase(s["lang"], lang),
                                                dir=t["dir"][s["confidence"]["direction"]],
                                                g=pct(s["growth_rel"]), k=k, conf=conf(s)))
    for members in groups:
        srt = sorted(members, key=lambda s: -s["growth_rel"])
        best, worst = srt[0], srt[-1]
        key = "answer_all_down" if best["growth_rel"] < 0 else "answer_multi"
        answer.append(t[key].format(best=best["name"], g1=pct(best["growth_rel"]), c1=conf(best),
                                    worst=worst["name"], g2=pct(worst["growth_rel"]), c2=conf(worst)))
        comp = next((c for c in a["comparisons"] if c["a"] == best["name"] and c["b"] == worst["name"]), None)
        if comp and len(groups) == 1:
            key = "answer_diff_clear" if comp["clear"] else "answer_diff_unclear"
            answer.append(t[key].format(d="%+.0f" % (comp["diff"] * 100), lo="%+.0f" % (comp["lo"] * 100),
                                        hi="%+.0f" % (comp["hi"] * 100)))

    evidence = []
    listed = ok
    if len(ok) > 6:  # keep the page readable: extremes of each group, the table has the rest
        keep = {x["id"] for g in groups for x in (sorted(g, key=lambda s: -s["growth_rel"])[:2] +
                                                  sorted(g, key=lambda s: s["growth_rel"])[:1])}
        listed = [s for s in ok if s["id"] in keep] or ok[:6]
    for s in listed:
        evidence.append(t["series_line"].format(
            name=s["name"], views=fmt_int(s["views_recent_month_avg"], lang), g=pct(s.get("growth_rel")),
            lo=pct(s.get("growth_rel_lo")), hi=pct(s.get("growth_rel_hi")), conf=conf(s)))
    for s in a["series"]:
        if s["status"] != "ok":
            evidence.append("%s: %s" % (s["name"], s["confidence"]["bad"][0]))

    rec = []
    w = a["ranking"]["weights"]
    for g in a["ranking"]["groups"]:
        rec.append(t["rec_rank"].format(top=g["rows"][0]["name"],
                                        weights="size=%g, growth=%g, intensity=%g" % (w["size"], w["growth"], w["intensity"])))
    if not rec and measurable:
        s = measurable[0]
        rec.append(t["rec_single_up"] if s["confidence"]["direction"] == "up" and s["confidence"]["grade"] != "low"
                   else t["rec_single_other"])

    nxt = []
    low = [s["name"] for s in ok if s["confidence"]["grade"] in ("low", "n/a")]
    if low:
        nxt.append(t["next_low"].format(names=", ".join(low)))
    nxt.append(t["next_validate"])
    nxt.append(t["next_rerun"])

    title = t["default_title"].format(topics=topics)
    out = ["<!-- Draft generated from the data. Edit it in the user's language: keep the first section as the",
           "     short answer; any other '##' sections appear beside the chart. Numbers must match summary.md;",
           "     `wt.py report` checks every percentage against the analysis. -->",
           "# " + title, "",
           "## " + t["answer"], " ".join(answer) or "-", "",
           "## " + t["evidence"]] + ["- " + e for e in evidence] + ["",
           "## " + t["recommendation"]] + ["- " + r for r in rec] + ["",
           "## " + t["next_steps"]] + ["- " + n for n in nxt]
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


def _known_percentages(a: dict) -> List[float]:
    vals: List[float] = []

    def add(v, scale=100.0):
        if isinstance(v, (int, float)) and v == v:
            vals.append(abs(v * scale))

    for s in a["series"]:
        for key in ("growth_rel", "growth_rel_lo", "growth_rel_hi", "growth_abs", "growth_abs_lo", "growth_abs_hi",
                    "growth_rel_with_spikes", "momentum_6m", "trend_annual", "project_growth", "spike_share",
                    "top_article_share"):
            add(s.get(key))
        for y in s.get("yearly", []):
            add(y.get("growth_rel"))
            add(y.get("growth_abs"))
        for d in s.get("articles", []):
            add(d.get("growth_rel"))
            add(d.get("share_of_basket"))
        if s.get("months_up") is not None:
            add(s["months_up"] / 12.0)
    for c in a["comparisons"]:
        for key in ("diff", "lo", "hi"):
            add(c[key])
    for v in a["project_totals"].values():
        add(v.get("growth"))
    for rows in (a.get("geo") or {}).values():
        for r in rows:
            add(r["share"])
    for g in a["ranking"]["groups"]:
        for r in g["rows"]:
            add(r.get("score"))
    vals += [95.0, 100.0]
    return vals


PCT_RE = re.compile(r"([+\-−–]?\s?\d+(?:[.,]\d+)?)\s?(%|pp\b|п\.\s?п\.|p\.p\.)")


def check_claims(a: dict, narrative: str) -> List[str]:
    """Warn about percentages in the narrative that match no computed metric (tolerance ~1 pp)."""
    known = _known_percentages(a)
    issues = []
    body = re.sub(r"<!--.*?-->", "", narrative, flags=re.S)
    for m in PCT_RE.finditer(body):
        num = m.group(1).replace("−", "-").replace("–", "-").replace(" ", "").replace(",", ".")
        try:
            v = abs(float(num))
        except ValueError:
            continue
        if not any(abs(v - kv) <= max(1.01, 0.05 * kv) for kv in known):
            ctx = body[max(0, m.start() - 40):m.end() + 10].replace("\n", " ")
            issues.append("'%s%s' matches no computed metric (context: ...%s...)" % (m.group(1).strip(), m.group(2), ctx))
    if re.search(r"\bTODO\b", body):
        issues.append("narrative still contains TODO")
    return issues
