"""Claim check: the narrative mistakes seen in cheap-model runs must be caught, correct text must pass."""
import unittest

from wikitrends import signals, text


def series(sid, lang, name, g, lo, hi, grade, direction, views, abs_g):
    return {"id": sid, "lang": lang, "name": name, "topic": "Fasting", "status": "ok", "growth_rel": g,
            "growth_rel_lo": lo, "growth_rel_hi": hi, "growth_abs": abs_g, "views_recent_month_avg": views,
            "views_prev_month_avg": views * 1.5, "daily_avg_recent": views / 30, "spike_share": 0.02,
            "confidence": {"grade": grade, "direction": direction, "good": [], "bad": []}, "articles": [],
            "monthly": {"views": [views] * 24, "views_clean": [views] * 24}}


A = {"params": {"langs": ["pl", "cs"]}, "topics": [{"label": "Fasting", "items": ["Q1"]}],
     "series": [series("t0|pl", "pl", "pl.wikipedia (Polish)", -0.34, -0.45, -0.20, "high", "down", 950, -0.42),
                series("t0|cs", "cs", "cs.wikipedia (Czech)", 0.02, -0.08, 0.15, "medium", "flat", 1200, -0.07)],
     "comparisons": [], "pooling": [], "geo": {},
     "project_totals": {"pl": {"growth": -0.13, "monthly": [1e8] * 24}, "cs": {"growth": -0.09, "monthly": [2e7] * 24}},
     "ranking": {"groups": []}}


def check(txt, lang="en"):
    return text.check_narrative(A, txt, None, lang)


class ClaimCheckTests(unittest.TestCase):
    def test_correct_text_passes(self):
        r = check("## Answer\nIn Polish Wikipedia relative interest is declining (-34%, 95% CI -45% to -20%; "
                  "high confidence). cs.wikipedia (Czech): +2% [-8%, +15%], no clear change; medium confidence.\n"
                  "- pl.wikipedia: 950 views/month.\n- For context, all views of each wiki changed: pl -13%, cs -9%.")
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["warnings"], [])

    def test_wrong_sign(self):
        self.assertTrue(any("wrong sign" in e for e in check("pl.wikipedia: +34% relative growth.")["errors"]))

    def test_decline_called_growth(self):
        self.assertTrue(check("In Polish Wikipedia interest grew 34%.")["errors"])

    def test_interval_crossing_zero_called_positive(self):
        errs = check("Czech Wikipedia is the only positive trend (+2%, interval -8% to +15%).")["errors"]
        self.assertTrue(any("crosses zero" in e for e in errs), errs)

    def test_number_of_another_series(self):
        errs = check("Czech Wikipedia: relative growth -13%.")["errors"]
        self.assertTrue(any("not a value of" in e for e in errs), errs)

    def test_wrong_confidence(self):
        errs = check("For Polish Wikipedia the confidence is medium.")["errors"]
        self.assertTrue(any("confidence" in e for e in errs), errs)
        errs = check("Польська Вікіпедія: довіра середня.", "uk")["errors"]
        self.assertTrue(any("HIGH" in e for e in errs), errs)

    def test_invented_market_share(self):
        self.assertTrue(check("Duolingo controls only 36% of the market.")["errors"])

    def test_interval_levels_and_index_are_allowed(self):
        self.assertEqual(check("Forecast with an 80% range; 95% CI; index = 100%.")["errors"], [])

    def test_warnings(self):
        w = check("Poland is the best market for us.")["warnings"]
        self.assertTrue(any("country" in x for x in w), w)
        self.assertEqual(check("Most pl.wikipedia readers are in Poland.")["warnings"], [])
        self.assertTrue(check("There are 38 million speakers.")["warnings"])
        self.assertTrue(check("Relative growth -34% is more than the whole-wiki drop of -13%.")["warnings"])
        self.assertTrue(check("Интерес имеет сезонность.", "uk")["warnings"])

    def test_negation_is_not_a_growth_claim(self):
        self.assertEqual(check("Czech Wikipedia shows no clear growth (+2%, 95% CI -8% to +15%).")["errors"], [])
        self.assertEqual(check("Чеська Вікіпедія: відносне зростання +2% [-8%; +15%], без явних змін.", "uk")["errors"], [])

    def test_backward_compatible_wrapper(self):
        self.assertEqual(text.check_claims(A, "pl.wikipedia: -34%."), [])


class AppStoreRelevanceTests(unittest.TestCase):
    def test_word_start_and_generic_genres(self):
        pats = signals.relevance_patterns("post", ["fasting"])
        self.assertFalse(signals.app_is_relevant({"trackName": "InPost", "description": "parcel lockers"}, pats))
        self.assertFalse(signals.app_is_relevant({"trackName": "Chat", "primaryGenreName": "Social Networking",
                                                  "description": "share a post"}, pats))
        self.assertTrue(signals.app_is_relevant({"trackName": "Zero: Fasting Tracker",
                                                 "primaryGenreName": "Health & Fitness"}, pats))

    def test_zero_relevant_apps_warns(self):
        m = signals.appstore_metrics([{"name": "X", "ratings": 5, "rating": 4, "released": "2020-01-01",
                                       "updated": "2020-01-01", "relevant": False}])
        self.assertIn("not missing demand", m["warning"])


if __name__ == "__main__":
    unittest.main()
