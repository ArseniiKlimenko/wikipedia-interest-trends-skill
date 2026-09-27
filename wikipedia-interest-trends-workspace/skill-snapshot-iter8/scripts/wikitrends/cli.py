"""Command-line interface. Run through the launcher: python3 scripts/wt.py <command> ..."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

from . import __version__

EPILOG = """examples:
  wt.py resolve "intermittent fasting" --langs pl,cs
  wt.py analyze --topic "Intermittent fasting=Q1666254" --langs pl,cs --months 24 --report-lang uk
  wt.py report wikitrends-output/intermittent-fasting_pl-cs_202310_202509
  wt.py related uk:Астрономія --limit 20
  wt.py expand Q333 --langs uk,pl
  wt.py discover uk --seed Q333
  wt.py signals wikitrends-output/<folder> --keyword pl="nauka angielskiego"
"""


def _langs(text: str):
    return [x.strip().lower() for x in text.replace(" ", ",").split(",") if x.strip()]


def cmd_resolve(args) -> int:
    from . import wiki
    from .cache import Cache
    cache = Cache()
    langs = _langs(args.langs) if args.langs else []
    all_out = []
    for query in args.query:
        cands = wiki.search_entities(cache, query, args.search_lang, limit=args.limit + 4)
        if not cands:
            for alt in langs:
                if alt != args.search_lang:
                    cands = wiki.search_entities(cache, query, alt, limit=args.limit + 4)
                    if cands:
                        break
        ents = wiki.get_entities(cache, [c["id"] for c in cands]) if cands else {}
        rows = []
        for c in cands:
            e = ents.get(c["id"], {})
            if e.get("missing"):
                continue
            n_wiki = wiki.wikipedia_sitelink_count(e)
            if n_wiki == 0:
                continue
            desc = c.get("description") or e.get("descriptions", {}).get("en", "")
            titles = {l: e.get("sitelinks", {}).get(wiki.site_of(l)) for l in langs}
            is_disambig = "disambiguation" in desc.lower() or "wikimedia" in desc.lower()
            rows.append({"qid": c["id"], "label": c.get("label") or wiki.label_of(e), "description": desc,
                         "wikipedias": n_wiki, "titles": titles, "disambiguation": is_disambig})
        rows.sort(key=lambda r: (r["disambiguation"], -sum(1 for v in r["titles"].values() if v), -r["wikipedias"]))
        rows = rows[:args.limit]
        best = next((r for r in rows if not r["disambiguation"]), None)
        if best:  # languages without a linked article: search that wiki directly
            e = ents.get(best["qid"], {})
            for l, title in best["titles"].items():
                if title:
                    continue
                queries = [q for q in dict.fromkeys([e.get("labels", {}).get(l), best["label"]]) if q]
                hits = []
                for q in queries[:2]:
                    hits += [h["title"] for h in wiki.search_wiki(cache, l, q)]
                best.setdefault("local_search", {})[l] = list(dict.fromkeys(hits))[:5]
        all_out.append({"query": query, "candidates": rows})
    if args.json:
        print(json.dumps(all_out, ensure_ascii=False, indent=1))
        return 0 if any(b["candidates"] for b in all_out) else 1
    for block in all_out:
        print('"%s"' % block["query"])
        if not block["candidates"]:
            print("  no Wikidata items with Wikipedia articles found; try English wording or --search-lang <code>")
        for i, r in enumerate(block["candidates"], 1):
            flag = "  [disambiguation page - do not use]" if r["disambiguation"] else ""
            print("  %d. %s  %s - %s  [%d Wikipedias]%s" % (i, r["qid"], r["label"], r["description"][:90],
                                                            r["wikipedias"], flag))
            if r["titles"]:
                print("       " + " | ".join("%s: %s" % (l, t or "(no article)") for l, t in r["titles"].items()))
            for l, hits in (r.get("local_search") or {}).items():
                print("       %s has no linked article; %s.wikipedia search finds: %s" % (
                    l, l, ", ".join(hits) if hits else "nothing"))
                if hits:
                    print("         -> only if one truly covers the topic, add it as %s:<Title> and call it a proxy" % l)
        print()
    first = next((b["candidates"][0] for b in all_out if b["candidates"]), None)
    if first:
        print('Use as: --topic "%s=%s"  (combine several QIDs with |)' % (first["label"], first["qid"]))
        return 0
    return 1


def cmd_related(args) -> int:
    from . import wiki
    from .cache import Cache
    if ":" not in args.article:
        print("give the seed article as lang:Title, e.g. uk:Астрономія", file=sys.stderr)
        return 2
    lang, title = args.article.split(":", 1)
    cache = Cache()
    info = wiki.titles_info(cache, lang, [title])[title]
    if not info["title"]:
        print("article not found: %s" % args.article, file=sys.stderr)
        return 1
    rows = wiki.linked_articles(cache, lang, info["title"], days=args.days, mutual=not args.all_links)
    rows = [r for r in rows if (r["views"] or 0) > 0][:args.limit]
    print("Articles %s %s:%s, ranked by views in the last %d days:"
          % ("linked from" if args.all_links else "linked both ways with", lang, info["title"], args.days))
    for i, r in enumerate(rows, 1):
        print("%3d. %-45s %-11s %10s" % (i, r["title"][:45], r["qid"] or "-", "{:,}".format(r["views"] or 0)))
    print("\nRecent views only show current size; run analyze on promising QIDs to measure growth.")
    return 0


def cmd_expand(args) -> int:
    from . import graph
    from .cache import Cache
    langs = _langs(args.langs)
    try:
        r = graph.expand(Cache(), args.qid, langs, limit=args.limit)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    print("Sub-topics of %s (%s); views over the last %d days in %s.wikipedia (seed article: %s views)" % (
        r["seed"], r["seed_label"], r["days"], r["lang0"], "{:,}".format(r["seed_views"])))
    print("| # | QID | Label | Relation to the seed | Articles in %s | Views |" % ",".join(langs))
    print("|---|---|---|---|---|---|")
    shown = [c for c in r["candidates"] if c["verified"] and not c.get("broad")][:args.show]
    for i, c in enumerate(shown, 1):
        print("| %d | %s | %s | %s | %d/%d | %s |" % (i, c["qid"], c["label"], "; ".join(c["sources"]), c["coverage"],
                                                    len(langs), "{:,}".format(c["views"] or 0)))
    unverified = [c for c in r["candidates"] if not c["verified"]][:8]
    if unverified:
        print("\nAlso linked but not confirmed as on-topic by Wikidata (check before using): " +
              ", ".join("%s %s" % (c["qid"], c["label"]) for c in unverified))
    if r.get("too_broad"):
        print("\nLeft out of the basket as too general (more than %.1fx the views of the seed article, so they mostly "
              "measure general curiosity): %s. Add one back only if the user's topic really includes it."
              % (graph.BROAD_FACTOR, ", ".join("%s %s (%s)" % (c["qid"], c["label"], "{:,}".format(c["views"]))
                                               for c in r["too_broad"][:6])))
    if r["broader"]:
        print("Broader topics (for a wider basket): " + ", ".join(b["qid"] for b in r["broader"][:6]))
    print("\nSuggested basket (%s):" % r["coverage_note"])
    print('  --topic "%s"' % r["suggested_topic"])
    if r.get("heavy"):
        print("Check these large items (each is 20%%+ of the basket's views and also draws general-interest readers): "
              "%s. Keep them only if they match the user's meaning; `analyze` reports if one article drives the "
              "result." % ", ".join("%s %s %.0f%%" % (h["qid"], h["label"], h["share"] * 100) for h in r["heavy"]))
    print("Drop items that do not match the user's meaning, then run analyze with it.")
    print("To see which of these sub-topics grow (each measured separately): wt.py discover %s --seed %s"
          % (r["lang0"] or langs[0], r["seed"]))
    return 0


def cmd_discover(args) -> int:
    from . import analysis as an, discover
    from .net import contact_warning, set_quiet
    set_quiet(args.quiet)
    contact_warning()
    try:
        r = discover.discover(args.lang, seed=args.seed, months=args.months, candidates=args.candidates,
                              top_months=args.top_months, include_all=args.include_all, out=args.out,
                              min_views=args.min_views)
    except an.UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    print(discover.discover_md(r))
    return 0


def cmd_signals(args) -> int:
    from . import analysis as an, signals
    from .net import set_quiet
    set_quiet(args.quiet)
    if not (Path(args.dir) / "analysis.json").exists():
        print("error: %s has no analysis.json - run analyze first" % args.dir, file=sys.stderr)
        return 2
    try:
        o = signals.run(args.dir, keywords=args.keyword, geos=args.geo, trends_csv=args.trends_csv,
                        use_trends=args.trends and not args.no_trends, use_appstore=not args.no_appstore)
    except an.UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    print(signals.signals_md(o))
    print("Saved signals.json / signals.md in %s; `report` will add a second-signal line to the PDF." % args.dir)
    return 0


def cmd_analyze(args) -> int:
    from . import analysis as an, charts, text
    from .net import contact_warning, set_quiet
    set_quiet(args.quiet)
    contact_warning()
    try:
        a = an.run(args.topic, _langs(args.langs), months=args.months, start=args.start, end=args.end,
                   agent=args.agent, access=args.access, redirects=args.redirects,
                   max_redirects=args.max_redirects, weights=args.weights, report_lang=args.report_lang,
                   out=args.out, geo=not args.no_geo, previous=args.previous)
    except an.UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    outdir = Path(a["outdir"])
    daily = a.pop("_daily", {})
    files = {"summary": str(outdir / "summary.md"), "analysis": str(outdir / "analysis.json"),
             "monthly data": str(outdir / "data.csv")}
    if any(s["status"] == "ok" for s in a["series"]):
        charts.trend_chart(a, outdir / "trend.png", args.report_lang)
        charts.growth_chart(a, outdir / "growth.png", args.report_lang)
        charts.daily_chart(a, daily, outdir / "daily.png", args.report_lang)
        files.update({"trend chart": str(outdir / "trend.png"), "growth chart": str(outdir / "growth.png"),
                      "daily diagnostic chart": str(outdir / "daily.png")})
    draft = text.narrative_draft(a, args.report_lang)
    (outdir / "narrative.md").write_text(draft, encoding="utf-8")
    a["draft_sha1"] = hashlib.sha1(draft.encode("utf-8")).hexdigest()
    files["narrative draft (edit, then run report)"] = str(outdir / "narrative.md")
    a["files"] = files
    an.save_json(a, outdir / "analysis.json")
    summary = text.summary_md(a, files)
    (outdir / "summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


def cmd_report(args) -> int:
    from . import analysis as an, charts, report, text
    outdir = Path(args.dir)
    path = outdir / "analysis.json"
    if not path.exists():
        print("error: %s not found - run analyze first" % path, file=sys.stderr)
        return 2
    a = an.load_json(path)
    lang = args.lang or a["params"].get("report_lang", "en")
    narrative_path = Path(args.narrative) if args.narrative else outdir / "narrative.md"
    narrative = narrative_path.read_text(encoding="utf-8") if narrative_path.exists() else text.narrative_draft(a, lang)
    title, sections = text.parse_narrative(narrative)
    trend_png, growth_png = outdir / "trend.png", outdir / "growth.png"
    if lang != a["params"].get("report_lang") or not trend_png.exists() or not growth_png.exists():
        trend_png, growth_png = outdir / ("trend_%s.png" % lang), outdir / ("growth_%s.png" % lang)
        charts.trend_chart(a, trend_png, lang)
        charts.growth_chart(a, growth_png, lang)
    out_pdf = Path(args.out) if args.out else outdir / "report.pdf"
    report.build_pdf(a, title, sections, trend_png, growth_png, out_pdf, lang)
    pages = report.page_count(out_pdf)
    print("PDF written: %s (%d page%s)" % (out_pdf.resolve(), pages, "" if pages == 1 else "s"))
    scale = getattr(report.build_pdf, "last_scale", 1.0)
    if scale < 0.85:
        print("Layout: the text is long, so the page was scaled to %.0f%%. Shorten narrative.md (answer <= 3 "
              "sentences, <= 5 evidence bullets) and re-run report for a more readable page." % (scale * 100))
    sig_path = outdir / "signals.json"
    signals = json.loads(sig_path.read_text(encoding="utf-8")) if sig_path.exists() else None
    res = text.check_narrative(a, narrative, signals, lang)
    if a.get("draft_sha1") and hashlib.sha1(narrative.encode("utf-8")).hexdigest() == a["draft_sha1"]:
        res["warnings"].insert(0, "narrative.md is still the unedited draft: rewrite it for the user's question "
                                  "(in the user's language) and re-run report")
    if res["errors"]:
        print("Claim check found %d problem(s); fix them in %s and re-run report (exit code 1):"
              % (len(res["errors"]), narrative_path))
        for i in res["errors"]:
            print("  - " + i)
    else:
        print("Claim check: percentages, signs, directions and confidence levels match the analysis.")
    if res["warnings"]:
        print("Warnings (review; fix if the text is wrong):")
        for w in res["warnings"]:
            print("  - " + w)
    return 1 if res["errors"] else 0


def cmd_check(args) -> int:
    from .cache import Cache
    from .net import USER_AGENT, get_json
    print("wikitrends %s, Python %s on %s" % (__version__, platform.python_version(), platform.platform()))
    for mod in ("numpy", "matplotlib", "reportlab"):
        try:
            m = __import__(mod)
            print("  %s %s" % (mod, getattr(m, "__version__", getattr(m, "Version", "?"))))
        except ImportError:
            print("  %s MISSING" % mod)
    print("cache: %s" % json.dumps(Cache().info()))
    print("user-agent: %s" % USER_AGENT)
    if not os.environ.get("WIKITRENDS_CONTACT"):
        print("WARNING: WIKITRENDS_CONTACT is not set, so the User-Agent carries a generic contact. Wikimedia asks "
              "API clients for a way to reach the operator: export WIKITRENDS_CONTACT=<your email or project URL>.")
    try:
        d = get_json("https://wikimedia.org/api/rest_v1/metrics/pageviews/aggregate/en.wikipedia/all-access/user/monthly/2024010100/2024020100")
        print("API: ok (%s items)" % len((d or {}).get("items", [])))
    except Exception as exc:
        print("API: FAILED - %s" % exc)
        return 1
    return 0


def cmd_selftest(args) -> int:
    import unittest
    tests = Path(__file__).resolve().parents[2] / "tests"
    suite = unittest.defaultTestLoader.discover(str(tests), top_level_dir=str(tests))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


def cmd_cache(args) -> int:
    from .cache import Cache
    c = Cache()
    if args.action == "clear":
        c.clear(args.what)
        print("cleared %s" % args.what)
    print(json.dumps(c.info(), indent=1))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wt.py", description="Wikipedia interest trends: topic demand research "
                                "from Wikimedia pageviews.", epilog=EPILOG,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("resolve", help="find Wikidata items (QIDs) and article titles for topics")
    r.add_argument("query", nargs="+", help="topic names; English usually works best")
    r.add_argument("--langs", default="", help="language codes to show titles for, e.g. pl,cs")
    r.add_argument("--search-lang", default="en", help="language of the query text (default en)")
    r.add_argument("--limit", type=int, default=5)
    r.add_argument("--json", action="store_true")
    r.set_defaults(fn=cmd_resolve)

    rl = sub.add_parser("related", help="articles linked from a seed article, ranked by recent views")
    rl.add_argument("article", help="lang:Title, e.g. uk:Астрономія")
    rl.add_argument("--limit", type=int, default=25)
    rl.add_argument("--days", type=int, default=60, choices=range(1, 61), metavar="1-60")
    rl.add_argument("--all-links", action="store_true", help="keep one-way links too (noisier)")
    rl.set_defaults(fn=cmd_related)

    a = sub.add_parser("analyze", help="fetch pageviews, compute growth and confidence, write outputs")
    a.add_argument("--topic", action="append", required=True,
                   help='"Label=Q1|Q2|pl:Title" (repeat for several topics)')
    a.add_argument("--langs", required=True, help="Wikipedia language codes, e.g. pl,cs,uk")
    a.add_argument("--months", type=int, help="number of full months ending last month (default 24)")
    a.add_argument("--start", help="first month YYYY-MM (overrides --months)")
    a.add_argument("--end", help="last month YYYY-MM (default: last complete month)")
    a.add_argument("--agent", default="user", choices=["user", "all-agents", "automated", "spider"])
    a.add_argument("--access", default="all-access", choices=["all-access", "desktop", "mobile-web", "mobile-app"])
    a.add_argument("--redirects", default="auto", choices=["auto", "all", "none"],
                   help="add views of redirects: auto = only for likely renames (default)")
    a.add_argument("--max-redirects", type=int, default=20)
    a.add_argument("--weights", help="ranking weights, default size=1,growth=1,intensity=0.5")
    a.add_argument("--report-lang", default="en", choices=["en", "uk"], help="labels for charts/draft/PDF")
    a.add_argument("--out", help="output directory (default ./wikitrends-output/<slug>; never inside the skill folder)")
    a.add_argument("--no-geo", action="store_true", help="skip reader-country context")
    a.add_argument("--previous", help="earlier output folder (or analysis.json) to list what changed, for follow-ups "
                   "(default: found automatically in the same --out folder or from the last run in this directory "
                   "within 12 h; 'none' disables)")
    a.add_argument("--quiet", action="store_true", help="hide progress messages")
    a.set_defaults(fn=cmd_analyze)

    rp = sub.add_parser("report", help="render the one-page PDF from an analysis directory")
    rp.add_argument("dir", help="analysis output directory")
    rp.add_argument("--narrative", help="markdown file (default <dir>/narrative.md)")
    rp.add_argument("--lang", choices=["en", "uk"], help="label language (default: the analysis setting)")
    rp.add_argument("--out", help="PDF path (default <dir>/report.pdf)")
    rp.set_defaults(fn=cmd_report)

    e = sub.add_parser("expand", help="suggest an article basket for a topic from the Wikidata and link graphs")
    e.add_argument("qid", help="seed Wikidata item, e.g. Q333")
    e.add_argument("--langs", required=True, help="languages the basket must cover, e.g. uk,pl")
    e.add_argument("--limit", type=int, default=6, help="sub-topics to put in the suggested basket")
    e.add_argument("--show", type=int, default=20, help="rows to list")
    e.add_argument("--json", action="store_true")
    e.set_defaults(fn=cmd_expand)

    d = sub.add_parser("discover", help="find growing topics in a wiki (top articles) or inside a subject (--seed)")
    d.add_argument("lang", help="Wikipedia language code")
    d.add_argument("--seed", help="Wikidata item: measure its sub-topics instead of the top lists")
    d.add_argument("--months", type=int, default=24)
    d.add_argument("--candidates", type=int, default=60, help="how many candidates to measure")
    d.add_argument("--top-months", type=int, default=3, help="monthly top-1000 lists to pool")
    d.add_argument("--min-views", type=float, default=90, help="skip candidates below this many views/month")
    d.add_argument("--include-all", action="store_true", help="keep people, films, TV, sport, lists, events")
    d.add_argument("--out", help="output directory")
    d.add_argument("--quiet", action="store_true")
    d.set_defaults(fn=cmd_discover)

    sg = sub.add_parser("signals", help="second signals for an analysis: Google Trends and the App Store")
    sg.add_argument("dir", help="analysis output directory")
    sg.add_argument("--keyword", action="append", help="lang=search phrase for the App Store (and Trends fallback)")
    sg.add_argument("--geo", action="append", help="lang=CC[,CC] countries to check, e.g. es=ES,MX")
    sg.add_argument("--trends-csv", action="append", help="lang=path to a Google Trends CSV export")
    sg.add_argument("--trends", action="store_true",
                    help="also query Google Trends through its unofficial web endpoints (see references/"
                         "discovery-and-signals.md for the terms-of-service caveat)")
    sg.add_argument("--no-trends", action="store_true", help=argparse.SUPPRESS)
    sg.add_argument("--no-appstore", action="store_true")
    sg.add_argument("--quiet", action="store_true")
    sg.set_defaults(fn=cmd_signals)

    c = sub.add_parser("check", help="check the environment and API access")
    c.set_defaults(fn=cmd_check)

    t = sub.add_parser("selftest", help="run the offline unit and pipeline tests")
    t.set_defaults(fn=cmd_selftest)

    ca = sub.add_parser("cache", help="show or clear the local cache")
    ca.add_argument("action", choices=["info", "clear"])
    ca.add_argument("--what", default="all", choices=["all", "pageviews", "metadata"])
    ca.set_defaults(fn=cmd_cache)
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    try:
        code = args.fn(args)
    except KeyboardInterrupt:
        code = 130
    except Exception as exc:  # show a short, actionable message instead of a traceback
        from .net import ApiError
        if isinstance(exc, ApiError):
            print("error: Wikimedia API problem - %s" % exc, file=sys.stderr)
            code = 3
        else:
            raise
    sys.exit(code)
