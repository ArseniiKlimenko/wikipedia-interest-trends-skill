"""Offline tests for graph expansion, discovery and second signals (all network calls faked)."""
import datetime as dt
import json
import math
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

TMP = tempfile.TemporaryDirectory()
os.environ["WIKITRENDS_HOME"] = TMP.name

from wikitrends import analysis as an, discover, graph, signals, wiki  # noqa: E402


def fake_entities(_cache, qids):
    table = {
        "Q1": {"labels": {"en": "Seed"}, "sitelinks": {"plwiki": "Nasiono", "cswiki": "Semínko"}},
        "Q2": {"labels": {"en": "Child"}, "sitelinks": {"plwiki": "Dziecko", "cswiki": "Dítě"}},
        "Q3": {"labels": {"en": "Neighbour"}, "sitelinks": {"plwiki": "Sąsiad", "cswiki": "Soused"}},
        "Q4": {"labels": {"en": "City"}, "sitelinks": {"plwiki": "Miasto", "cswiki": "Město"}},
        "Q5": {"labels": {"en": "Polish only"}, "sitelinks": {"plwiki": "Tylko"}},
    }
    return {q: dict(table.get(q, {"missing": True}), id=q) for q in qids}


def fake_sparql(_cache, query):
    if "VALUES ?p" in query and "?item ?p wd:Q1" in query:
        return [{"item": "Q2", "p": "P279", "links": "40"}, {"item": "Q5", "p": "P361", "links": "10"}]
    if "VALUES ?p" in query:
        return []
    if "P2578" in query:
        return [{"t": "Q9"}]
    if "?c1" in query:  # class-chain check: Q3 is a kind of Q9, Q4 is not
        return [{"item": "Q3", "c1": "Q9"}, {"item": "Q4", "c1": "Q515"}]
    return []


class ExpandTests(unittest.TestCase):
    def test_basket_uses_verified_items_with_full_coverage(self):
        links = [{"title": "Sąsiad", "qid": "Q3", "views": 900}, {"title": "Miasto", "qid": "Q4", "views": 5000}]
        views = lambda _c, _l, titles, days=60: {t: {"views": {"Dziecko": 300, "Tylko": 800, "Sąsiad": 900,  # noqa: E731
                                                                 "Miasto": 5000, "Nasiono": 400}.get(t, 0)} for t in titles}
        with mock.patch.object(wiki, "get_entities", fake_entities), mock.patch.object(graph, "sparql", fake_sparql), \
                mock.patch.object(wiki, "linked_articles", lambda *a, **k: links), \
                mock.patch.object(wiki, "recent_views", views):
            r = graph.expand(None, "Q1", ["pl", "cs"], limit=5)
        self.assertEqual(r["basket"], ["Q1", "Q3", "Q2"])  # by views; Q5 lacks cs, Q4 is off-topic
        city = next(c for c in r["candidates"] if c["qid"] == "Q4")
        self.assertFalse(city["verified"])
        self.assertIn("Q1|Q3|Q2", r["suggested_topic"])

    def test_general_interest_pages_stay_out_of_the_basket(self):
        links = [{"title": "Sąsiad", "qid": "Q3", "views": 9000}]
        views = lambda _c, _l, titles, days=60: {t: {"views": {"Dziecko": 300, "Sąsiad": 9000,  # noqa: E731
                                                                 "Nasiono": 400}.get(t, 0)} for t in titles}
        with mock.patch.object(wiki, "get_entities", fake_entities), mock.patch.object(graph, "sparql", fake_sparql), \
                mock.patch.object(wiki, "linked_articles", lambda *a, **k: links), \
                mock.patch.object(wiki, "recent_views", views):
            r = graph.expand(None, "Q1", ["pl", "cs"], limit=5)
        self.assertEqual(r["basket"], ["Q1", "Q2"])  # "Neighbour" has > 3x the seed's views
        self.assertEqual([c["qid"] for c in r["too_broad"]], ["Q3"])


class DiscoverTests(unittest.TestCase):
    def test_top_candidates_are_filtered(self):
        tops = [{"title": "Strona główna", "views": 10 ** 6}, {"title": "Specjalna:Szukaj", "views": 10 ** 5},
                {"title": "Aktor X", "views": 9000}, {"title": "Dieta", "views": 5000}]
        info = {t["title"]: {"title": t["title"], "qid": q} for t, q in zip(tops, ["Q10", "Q11", "Q12", "Q13"])}
        with mock.patch.object(discover, "top_articles", lambda *a: tops), \
                mock.patch.object(discover, "siteinfo", lambda *a: {"mainpage": "Strona główna", "namespaces": ["Specjalna"]}), \
                mock.patch.object(wiki, "titles_info", lambda _c, _l, titles: {t: info[t] for t in titles}), \
                mock.patch.object(graph, "on_topic", lambda *a, **k: {"Q12"}):
            rows = discover.candidates_from_top(None, "pl", 1, 10, include_all=False)
        self.assertEqual([r["title"] for r in rows], ["Dieta"])

    def test_growing_candidate_is_ranked(self):
        start, end, _ = an.resolve_period(24, None, None)
        n = (end - start).days + 1
        t = np.arange(n)
        grow = 50 * 1.6 ** (t / 365.0) * (1 + 0.1 * np.sin(t))
        flat = 80 * (1 + 0.1 * np.sin(t))
        burst = flat.copy()
        burst[n - 75:n - 20] *= 12  # a two-month event in the last year
        rows = [{"title": "Rośnie", "qid": "Q20"}, {"title": "Stoi", "qid": "Q21"},
                {"title": "Mecz A", "qid": "Q22"}, {"title": "Mecz B", "qid": "Q23"}]

        def fake_fetch(_cache, sids, s, e, label=""):
            out = {}
            for sid in sids:
                out[sid] = np.full(n, 1e6) if sid.startswith("agg") else \
                    grow if "Rośnie" in sid else burst if "Mecz" in sid else flat
            return out
        with mock.patch.object(discover, "candidates_from_top", lambda *a: rows), \
                mock.patch.object(discover, "fetch_daily", fake_fetch):
            r = discover.discover("pl", out=str(Path(TMP.name) / "disc"))
        self.assertEqual(r["growing"][0]["title"], "Rośnie")  # sustained growth ranks above bursts
        self.assertAlmostEqual(r["growing"][0]["growth_rel"], 0.6, delta=0.08)
        self.assertFalse(r["growing"][0]["burst"])
        self.assertTrue(all(x["burst"] for x in r["growing"][1:]))
        self.assertTrue(all(x["q"] <= discover.FDR_Q for x in r["growing"]))
        self.assertEqual(sorted(next(iter(r["shared_peaks"].values()))), ["Mecz A", "Mecz B"])
        self.assertTrue((Path(TMP.name) / "disc" / "discover.md").exists())


class SignalTests(unittest.TestCase):
    def test_trends_csv_and_growth(self):
        path = Path(TMP.name) / "multiTimeline.csv"
        lines = ["Category: All categories", "", "Week,intermittent fasting: (Poland)"]
        d = dt.date(2024, 9, 1)
        for i in range(104):
            lines.append("%s,%s" % ((d + dt.timedelta(weeks=i)).isoformat(), "<1" if i == 0 else 20 + (i >= 52) * 10))
        path.write_text("\n".join(lines), encoding="utf-8")
        pts = signals.parse_trends_csv(str(path))
        self.assertEqual(pts[0][1], 0.5)
        g = signals.series_growth(pts, ("2025-09", "2026-08"), ("2024-09", "2025-08"))
        self.assertAlmostEqual(g["growth"], 0.5, delta=0.06)
        self.assertEqual(g["direction"], "up")

    def test_appstore_metrics(self):
        today = dt.date(2026, 9, 27)
        apps = [{"name": "A", "ratings": 900, "rating": 4.5, "released": "2015-01-01", "updated": "2026-05-01", "relevant": True},
                {"name": "B", "ratings": 100, "rating": 4.0, "released": "2025-06-01", "updated": "2026-08-01", "relevant": True},
                {"name": "Game", "ratings": 10 ** 6, "rating": 4.8, "released": "2018-01-01", "updated": "2026-09-01", "relevant": False}]
        m = signals.appstore_metrics(apps, today)
        self.assertEqual((m["apps_found"], m["apps_relevant"], m["top_ratings_total"]), (3, 2, 1000))
        self.assertEqual((m["updated_last_12m"], m["new_last_24m"]), (2, 1))
        self.assertAlmostEqual(m["leader_share"], 0.9)

    def test_agreement(self):
        self.assertEqual(signals._agreement("down", "up"), "DISAGREE")
        self.assertEqual(signals._agreement("up", "up"), "agree")
        self.assertTrue(signals._agreement("flat", "up").startswith("partly"))

    def test_run_writes_signals(self):
        folder = Path(TMP.name) / "an"
        folder.mkdir(exist_ok=True)
        a = {"period": {"start": "2024-09-01", "end": "2026-08-31", "recent": ["2025-09", "2026-08"],
                        "previous": ["2024-09", "2025-08"]},
             "params": {"langs": ["pl"]}, "topics": [{"label": "Fasting", "items": ["Q1"]}],
             "series": [{"topic": "Fasting", "lang": "pl", "growth_rel": -0.2, "confidence": {"direction": "down"}}]}
        (folder / "analysis.json").write_text(json.dumps(a), encoding="utf-8")
        weekly = [((dt.date(2024, 9, 1) + dt.timedelta(weeks=i)).isoformat(), 20.0 + (i >= 52) * 10) for i in range(104)]
        with mock.patch.object(signals, "freebase_ids", lambda *a: {"Q1": "/m/abc"}), \
                mock.patch.object(wiki, "get_entities", fake_entities), \
                mock.patch.object(signals, "trends_timeline", lambda *a: weekly), \
                mock.patch.object(signals, "appstore_search", lambda *a, **k: [
                    {"name": "A", "ratings": 50, "rating": 4, "released": "2025-01-01", "updated": "2026-01-01", "relevant": True}]):
            o = signals.run(str(folder), use_trends=True)
        row = o["rows"][0]
        self.assertEqual(row["geo"], "PL")
        self.assertEqual(row["trends"]["source"], "topic /m/abc")
        self.assertEqual(row["agreement"], "DISAGREE")
        self.assertTrue((folder / "signals.md").exists())


if __name__ == "__main__":
    unittest.main()
