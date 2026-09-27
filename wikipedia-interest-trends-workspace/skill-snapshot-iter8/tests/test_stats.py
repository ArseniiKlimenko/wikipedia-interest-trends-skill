"""Unit tests for the statistics and parsing helpers (offline, synthetic data)."""
import datetime as dt
import unittest

import numpy as np

from wikitrends import analysis, stats, text


def weekly_series(n, level, seed=0):
    rng = np.random.default_rng(seed)
    week = 1 + 0.15 * np.sin(np.arange(n) * 2 * np.pi / 7)
    return rng.poisson(level * week).astype(float)


class SpikeTests(unittest.TestCase):
    def test_single_spike_is_removed(self):
        x = weekly_series(200, 100)
        x[120] = 2000
        clean, spike, _ = stats.dampen_spikes(x)
        self.assertTrue(spike[120])
        self.assertLess(clean[120], 200)
        self.assertLess(spike.sum(), 5)

    def test_sustained_change_is_not_a_spike(self):
        x = np.concatenate([weekly_series(150, 100, 1), weekly_series(150, 300, 2)])
        _, spike, _ = stats.dampen_spikes(x)
        self.assertLess(spike[160:].sum(), 5)


class GrowthTests(unittest.TestCase):
    def test_doubling_share_gives_plus_100(self):
        prev, rec = weekly_series(365, 50, 3), weekly_series(365, 100, 4)
        tot = np.full(365, 1e6)
        g = stats.ratio_growth(prev, tot, rec, tot)
        self.assertAlmostEqual(g["point"], 1.0, delta=0.08)
        self.assertLess(g["lo"], g["point"])
        self.assertGreater(g["hi"], g["point"])
        self.assertGreater(g["lo"], 0.7)

    def test_relative_growth_removes_wiki_wide_decline(self):
        prev, rec = weekly_series(365, 100, 5), weekly_series(365, 80, 6)
        g = stats.ratio_growth(prev, np.full(365, 1e6), rec, np.full(365, 0.8e6))
        self.assertAlmostEqual(g["point"], 0.0, delta=0.05)
        self.assertLess(g["lo"], 0)
        self.assertGreater(g["hi"], 0)

    def test_persistent_noise_rarely_gives_false_growth(self):
        rng = np.random.default_rng(11)
        months = np.repeat(np.arange(12), 31)[:365]
        false = 0
        for _ in range(60):
            e = np.zeros(730)
            for i in range(1, 730):
                e[i] = 0.9 * e[i - 1] + rng.normal(0, 0.1)
            x = rng.poisson(300 * np.exp(e)).astype(float)
            g = stats.ratio_growth(x[:365], np.ones(365), x[365:], np.ones(365), month_prev=months, month_rec=months)
            false += g["lo"] > 0 or g["hi"] < 0
        self.assertLessEqual(false, 7)  # ~5% expected; the old unpaired bootstrap gave ~16%

    def test_diff_interval_keeps_pairs_aligned(self):
        rng = np.random.default_rng(2)
        a = stats.ratio_growth(rng.poisson(50, 365), np.ones(365), rng.poisson(60, 365), np.ones(365))
        b = stats.ratio_growth(rng.poisson(50, 365), np.ones(365), rng.poisson(50, 365), np.ones(365))
        a["samples"][:30] = np.nan  # undefined resamples must not shift the pairing
        d, lo, hi = stats.diff_interval(a, b)
        self.assertAlmostEqual(d, a["point"] - b["point"])
        self.assertLess(lo, d)
        self.assertGreater(hi, d)
        self.assertEqual(len(a["samples"]), len(b["samples"]))

    def test_empty_previous_period(self):
        self.assertIsNone(stats.ratio_growth(np.zeros(10), np.ones(10), np.ones(10), np.ones(10)))


class TrendAndShiftTests(unittest.TestCase):
    def test_theil_sen_on_exponential_growth(self):
        m = 100 * 1.02 ** np.arange(24)
        tr = stats.annual_trend(m)
        self.assertAlmostEqual(tr["annual"], 1.02 ** 12 - 1, delta=0.01)
        self.assertLess(tr["p"], 0.01)

    def test_level_shift_detected(self):
        x = np.concatenate([weekly_series(300, 20, 7), weekly_series(300, 90, 8)])
        shift = stats.level_shift(x)
        self.assertIsNotNone(shift)
        self.assertAlmostEqual(shift["index"], 300, delta=20)

    def test_seasonal_drop_is_not_a_level_shift(self):
        days = np.arange(365 * 3)
        in_summer = ((days % 365) > 150) & ((days % 365) < 240)
        x = np.where(in_summer, 20.0, 100.0) + weekly_series(len(days), 5, 9)
        self.assertIsNone(stats.level_shift(x))

    def test_months_above_last_year(self):
        m = np.concatenate([np.full(12, 10.0), np.full(12, 12.0)])
        self.assertEqual(stats.months_above_last_year(m), 12)


class ConfidenceTests(unittest.TestCase):
    base = {"growth_rel": 0.2, "growth_rel_lo": 0.1, "growth_rel_hi": 0.3, "growth_abs": 0.1,
            "months_up": 11, "spike_share": 0.02, "growth_rel_with_spikes": 0.22, "trend_annual": 0.15,
            "daily_avg_recent": 300, "level_shift": None, "driven_by": None}

    def test_clean_growth_is_high(self):
        c = stats.grade_confidence(dict(self.base))
        self.assertEqual((c["grade"], c["direction"]), ("high", "up"))

    def test_interval_crossing_zero_is_flat(self):
        c = stats.grade_confidence(dict(self.base, growth_rel_lo=-0.05))
        self.assertEqual(c["direction"], "flat")

    def test_level_shift_forces_low(self):
        c = stats.grade_confidence(dict(self.base, level_shift={"date": "2025-05-14", "ratio": 0.3}))
        self.assertEqual(c["grade"], "low")

    def test_problems_accumulate(self):
        c = stats.grade_confidence(dict(self.base, daily_avg_recent=10, growth_abs=-0.05, months_up=5))
        self.assertEqual(c["grade"], "low")


class ParsingTests(unittest.TestCase):
    def test_parse_topic(self):
        t = analysis.parse_topic("Astronomy=Q333|Q318|uk:Сонце")
        self.assertEqual(t, {"label": "Astronomy", "items": ["Q333", "Q318", "uk:Сонце"]})

    def test_parse_topic_title_with_comma(self):
        t = analysis.parse_topic("en:Washington, D.C.")
        self.assertEqual(t["items"], ["en:Washington, D.C."])

    def test_parse_topic_rejects_free_text(self):
        with self.assertRaises(analysis.UsageError):
            analysis.parse_topic("intermittent fasting")

    def test_period_defaults_to_last_complete_months(self):
        s, e, _ = analysis.resolve_period(24, None, None, today=dt.date(2026, 9, 26))
        self.assertEqual((s, e), (dt.date(2024, 9, 1), dt.date(2026, 8, 31)))

    def test_weights(self):
        self.assertEqual(analysis.parse_weights("growth=2")["growth"], 2.0)
        with self.assertRaises(analysis.UsageError):
            analysis.parse_weights("price=1")

    def test_narrative_parsing(self):
        title, sections = text.parse_narrative("<!-- x -->\n# T\n\n## A\nline one\n\n## B\n- item\n")
        self.assertEqual(title, "T")
        self.assertEqual(sections, [("A", ["line one"]), ("B", ["- item"])])

    def test_claim_check_flags_unknown_numbers(self):
        a = {"params": {"langs": ["pl"]}, "topics": [{"label": "T", "items": ["Q1"]}],
             "series": [{"id": "t0|pl", "lang": "pl", "name": "T · pl.wikipedia", "topic": "T", "growth_rel": 0.153,
                         "confidence": {"grade": "high", "direction": "up"}}],
             "comparisons": [], "project_totals": {}, "geo": {}, "ranking": {"groups": []}}
        self.assertEqual(text.check_claims(a, "grew +15% (95% CI)"), [])
        self.assertEqual(len(text.check_claims(a, "grew 40%")), 1)


if __name__ == "__main__":
    unittest.main()
