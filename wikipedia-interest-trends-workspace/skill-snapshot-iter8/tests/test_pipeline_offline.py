"""End-to-end test of analyze -> report against a fake Wikimedia API (no network).

Synthetic world:
  Q100 "Growing": pl grows +50%/year in share, cs is flat
  Q200 "Renamed": the pl article was renamed ~300 days ago; old views live under a redirect
  Q300 "Czech only": has no Polish article
"""
import contextlib
import datetime as dt
import io
import json
import math
import os
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

TODAY = dt.date.today()
CUTOFF = TODAY - dt.timedelta(days=300)
BASE = dt.date(2020, 1, 1)


def _level(title: str, day: dt.date) -> float:
    t = (day - BASE).days
    wiggle = (1 + 0.12 * math.sin(2 * math.pi * t / 7)) * (1 + 0.05 * math.sin(t * 1.7))
    if title == "Rosnący":
        return 100 * 1.5 ** (t / 365.0) * wiggle
    if title in ("Rostoucí", "Přejmenovaný"):
        return 80 * wiggle
    if title == "Nowy tytuł":
        return (120 if day >= CUTOFF else 0) * wiggle
    if title == "Stary tytuł":
        return (3 if day >= CUTOFF else 120) * wiggle
    if title == "Jen česky":
        return 50 * wiggle
    return -1  # unknown article


ENTITIES = {
    "Q100": {"en": "Growing", "sitelinks": {"plwiki": "Rosnący", "cswiki": "Rostoucí"}},
    "Q200": {"en": "Renamed", "sitelinks": {"plwiki": "Nowy tytuł", "cswiki": "Přejmenovaný"}},
    "Q300": {"en": "Czech only", "sitelinks": {"cswiki": "Jen česky"}},
}


def _days(start: str, end: str):
    s = dt.datetime.strptime(start[:8], "%Y%m%d").date()
    e = dt.datetime.strptime(end[:8], "%Y%m%d").date()
    while s <= e:
        yield s
        s += dt.timedelta(days=1)


def fake_get_json(url, params=None, **_kw):
    params = params or {}
    if "wikidata.org" in url and params.get("action") == "wbgetentities":
        ents = {}
        for q in params["ids"].split("|"):
            e = ENTITIES[q]
            ents[q] = {"id": q, "labels": {"en": {"value": e["en"]}}, "descriptions": {},
                       "sitelinks": {k: {"title": v} for k, v in e["sitelinks"].items()}}
        return {"entities": ents}
    if "/per-article/" in url:
        project, access, agent, title, gran, start, end = url.split("/per-article/")[1].split("/")
        title = urllib.parse.unquote(title).replace("_", " ")
        if _level(title, TODAY) < 0:
            return None
        items = [{"timestamp": d.strftime("%Y%m%d00"), "views": int(round(_level(title, d)))} for d in _days(start, end)]
        return {"items": [i for i in items if i["views"] > 0]}
    if "/aggregate/" in url:
        start, end = url.rstrip("/").split("/")[-2:]
        return {"items": [{"timestamp": d.strftime("%Y%m%d00"),
                           "views": int(1e7 * (1 + 0.1 * math.sin(2 * math.pi * (d - BASE).days / 7)))}
                          for d in _days(start, end)]}
    if "/top-by-country/" in url:
        return {"items": [{"countries": [{"country": "PL", "views_ceil": 9000}, {"country": "DE", "views_ceil": 1000}]}]}
    if url.endswith("/w/api.php"):
        if params.get("prop") == "redirects":
            pages = [{"title": t, "redirects": [{"title": "Stary tytuł"}] if t == "Nowy tytuł" else []}
                     for t in params["titles"].split("|")]
            return {"query": {"pages": pages}}
        if params.get("list") == "search":
            return {"query": {"search": [{"title": "Podobny artykuł"}]}}
    raise AssertionError("unexpected request: %s %s" % (url, params))


class OfflinePipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ["WIKITRENDS_HOME"] = cls.tmp.name
        from wikitrends import cli, pageviews, wiki
        cls.out = Path(cls.tmp.name) / "out"
        with mock.patch.object(wiki, "get_json", fake_get_json), \
                mock.patch.object(pageviews, "get_json", fake_get_json):
            args = cli.build_parser().parse_args([
                "analyze", "--topic", "Growing=Q100", "--topic", "Renamed=Q200", "--topic", "Czech only=Q300",
                "--langs", "pl,cs", "--months", "24", "--out", str(cls.out), "--quiet"])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                cls.code = args.fn(args)
            cls.summary = buf.getvalue()
            fargs = cli.build_parser().parse_args([
                "analyze", "--topic", "Growing=Q100", "--topic", "Renamed=Q200", "--langs", "pl,cs",
                "--months", "24", "--weights", "growth=2", "--previous", str(cls.out),
                "--out", str(Path(cls.tmp.name) / "followup"), "--quiet"])
            buf3 = io.StringIO()
            with contextlib.redirect_stdout(buf3):
                fargs.fn(fargs)
            cls.followup = buf3.getvalue()
            rargs = cli.build_parser().parse_args(["report", str(cls.out)])
            buf2 = io.StringIO()
            with contextlib.redirect_stdout(buf2):
                cls.report_code = rargs.fn(rargs)
            cls.report_out = buf2.getvalue()
        cls.a = json.loads((cls.out / "analysis.json").read_text(encoding="utf-8"))
        cls.by = {s["id"]: s for s in cls.a["series"]}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_exit_codes_and_files(self):
        self.assertEqual(self.code, 0)
        self.assertEqual(self.report_code, 0)
        for name in ("analysis.json", "summary.md", "data.csv", "trend.png", "growth.png", "narrative.md", "report.pdf"):
            self.assertTrue((self.out / name).exists(), name)

    def test_growth_detected_with_high_confidence(self):
        s = self.by["t0|pl"]
        self.assertAlmostEqual(s["growth_rel"], 0.5, delta=0.06)
        self.assertEqual(s["confidence"]["direction"], "up")
        self.assertEqual(s["confidence"]["grade"], "high")

    def test_flat_series(self):
        self.assertEqual(self.by["t0|cs"]["confidence"]["direction"], "flat")

    def test_rename_repaired_with_redirects(self):
        s = self.by["t1|pl"]
        self.assertIsNone(s["growth_note"])
        self.assertEqual(s["articles"][0]["redirects_added"], 1)
        self.assertLess(abs(s["growth_rel"]), 0.1)

    def test_missing_article_reported_with_search_hint(self):
        self.assertEqual(self.by["t2|pl"]["status"], "no_article")
        self.assertTrue(any("Podobny artykuł" in w for w in self.a["warnings"]))

    def test_one_page_report_and_clean_claims(self):
        self.assertIn("(1 page)", self.report_out)
        self.assertIn("match the analysis", self.report_out)

    def test_followup_lists_changes(self):
        self.assertIn("## Changes vs previous analysis", self.followup)
        self.assertIn("ranking weights", self.followup)
        self.assertIn("MEASUREMENT CHANGED", self.followup)  # the 'Czech only' topic was dropped

    def test_summary_mentions_key_sections(self):
        for part in ("## Results", "## Confidence notes", "## Comparisons", "## Opportunity ranking"):
            self.assertIn(part, self.summary)


if __name__ == "__main__":
    unittest.main()
