"""Unit tests for seasonal decomposition, forecasting, changepoints and partial pooling."""
import math
import unittest

import numpy as np

from wikitrends import models

MONTHS = ["%04d-%02d" % (2023 + i // 12, i % 12 + 1) for i in range(36)]


def seasonal_series(trend=0.01, amp=0.3, noise=0.03, seed=1, n=36):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    return math.log(100) + trend * t + amp * np.sin(2 * np.pi * t / 12) + rng.normal(0, noise, n)


class SeasonalityTests(unittest.TestCase):
    def test_strong_seasonality_and_peak_month(self):
        d = models.seasonal_decompose(seasonal_series(), MONTHS)
        self.assertGreater(d["strength"], 0.8)
        self.assertIn(d["peak"][0][0], ("Mar", "Apr", "May"))  # sin peaks at month index 3 = April
        self.assertIn(d["low"][0][0], ("Sep", "Oct", "Nov"))

    def test_no_seasonality_is_weak(self):
        d = models.seasonal_decompose(seasonal_series(amp=0.0, noise=0.05), MONTHS)
        self.assertLess(d["strength"], 0.5)

    def test_too_short(self):
        self.assertIsNone(models.seasonal_decompose(seasonal_series(n=20), MONTHS[:20]))
        self.assertIsNone(models.seasonal_decompose(seasonal_series(n=24), MONTHS[:24]))  # 2 years = noise

    def test_significance(self):
        self.assertTrue(models.seasonal_decompose(seasonal_series(), MONTHS)["significant"])
        rng = np.random.default_rng(4)
        hits = 0
        for _ in range(60):  # no seasonality: the repetition test should rarely fire
            e = np.zeros(36)
            for i in range(1, 36):
                e[i] = 0.5 * e[i - 1] + rng.normal(0, 0.08)
            hits += models.seasonal_decompose(4 + e, MONTHS)["significant"]
        self.assertLessEqual(hits, 8)


class ForecastTests(unittest.TestCase):
    def test_no_untested_forecast_on_short_series(self):
        self.assertIsNone(models.forecast(seasonal_series(n=24), MONTHS[:24]))
        self.assertGreaterEqual(models.forecast(seasonal_series(), MONTHS)["origins"], 2)

    def test_growing_series_forecasts_growth(self):
        f = models.forecast(seasonal_series(trend=0.02), MONTHS)
        self.assertGreater(f["next12_vs_last12"], 0.05)
        self.assertLess(f["next12_lo80"], f["next12_vs_last12"])
        self.assertGreater(f["next12_hi80"], f["next12_vs_last12"])
        self.assertEqual(len(f["median"]), 12)
        self.assertEqual(f["months"][0], "2026-01")

    def test_declining_series_forecasts_decline(self):
        f = models.forecast(seasonal_series(trend=-0.03), MONTHS)
        self.assertLess(f["next12_vs_last12"], -0.1)

    def test_method_is_chosen_by_backtest(self):
        f = models.forecast(seasonal_series(), MONTHS)
        self.assertIn(f["chosen"], ("ets", "snaive", "snaive_drift"))
        self.assertEqual(min(f["backtest_mae"], key=f["backtest_mae"].get), f["chosen"])


class ChangepointTests(unittest.TestCase):
    def test_step_is_found(self):
        rng = np.random.default_rng(2)
        x = np.r_[np.full(18, 4.0), np.full(18, 3.5)] + rng.normal(0, 0.03, 36)
        cps = models.changepoints(x, MONTHS)
        self.assertEqual(len(cps), 1)
        self.assertIn(cps[0]["month"], ("2024-06", "2024-07", "2024-08"))
        self.assertLess(cps[0]["level_jump"], -0.3)

    def test_smooth_trend_has_no_break(self):
        rng = np.random.default_rng(3)
        self.assertEqual(models.changepoints(4 - 0.02 * np.arange(36) + rng.normal(0, 0.03, 36), MONTHS), [])

    def test_false_alarm_rate_with_autocorrelated_noise(self):
        rng = np.random.default_rng(5)
        alarms = 0
        for _ in range(40):
            e = np.zeros(36)
            for i in range(1, 36):
                e[i] = 0.5 * e[i - 1] + rng.normal(0, 0.06)
            alarms += bool(models.changepoints(-0.02 * np.arange(36) + e, MONTHS))
        self.assertLessEqual(alarms, 4)


class PoolingTests(unittest.TestCase):
    def test_noisy_estimate_shrinks_toward_group(self):
        est = [{"g": 0.10, "lo": 0.05, "hi": 0.15}, {"g": -0.30, "lo": -0.35, "hi": -0.25},
               {"g": 0.05, "lo": 0.0, "hi": 0.10}, {"g": 0.9, "lo": -0.2, "hi": 2.5}]
        r = models.partial_pool(est)
        noisy = r["items"][3]
        self.assertLess(noisy["g"], 0.9)
        self.assertLess(noisy["weight"], r["items"][0]["weight"])
        self.assertGreater(r["tau"], 0)

    def test_needs_three(self):
        self.assertIsNone(models.partial_pool([{"g": 0.1, "lo": 0.0, "hi": 0.2}, None]))


if __name__ == "__main__":
    unittest.main()
