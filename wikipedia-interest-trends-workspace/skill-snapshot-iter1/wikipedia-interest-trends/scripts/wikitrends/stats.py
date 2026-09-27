"""Statistics for pageview series: spike dampening, growth with bootstrap intervals,
robust trend, level-shift detection, and a rule-based confidence grade.

Everything is numpy-only and deterministic (fixed bootstrap seed), so re-running an
analysis gives identical numbers.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


# ---- spikes ---------------------------------------------------------------------------
def rolling_median(x: np.ndarray, window: int) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    half = window // 2
    if len(x) <= half + 1:
        return np.full_like(x, np.median(x) if len(x) else 0.0)
    padded = np.pad(x, half, mode="reflect")
    return np.median(sliding_window_view(padded, 2 * half + 1), axis=1)


def dampen_spikes(x: np.ndarray, window: int = 29, k: float = 5.0, min_ratio: float = 2.0,
                  min_excess: float = 10.0):
    """Replace short-lived spikes with the local median.

    A day counts as a spike when it is more than `k` robust SDs above the rolling median
    AND at least `min_ratio` times that median (and `min_excess` views above it).
    Sustained changes move the rolling median too, so they are *not* removed.
    Returns (cleaned, spike_mask, local_median).
    """
    x = np.asarray(x, dtype=float)
    med = rolling_median(x, window)
    mad = rolling_median(np.abs(x - med), window) * 1.4826
    sigma = np.maximum(mad, np.sqrt(np.maximum(med, 1.0)))  # Poisson floor for quiet pages
    threshold = np.maximum(med + k * sigma, med * min_ratio)
    spike = (x > threshold) & (x - med >= min_excess)
    return np.where(spike, med, x), spike, med


# ---- growth ---------------------------------------------------------------------------
def _block_indices(n: int, block: int, reps: int, rng) -> np.ndarray:
    block = max(1, min(block, n))
    n_blocks = int(math.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(reps, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(reps, -1)
    return idx[:, :n]


def ratio_growth(num_prev, den_prev, num_rec, den_rec, block: int = 28, reps: int = 2000, seed: int = 7):
    """Growth of sum(num)/sum(den) from the previous to the recent period.

    With den = project totals this is the change in the topic's share of all views
    ("relative growth"); with den = ones it is plain growth in views. The 95% interval
    comes from a moving-block bootstrap (28-day blocks keep weekly patterns and short
    bursts together), resampling numerator and denominator jointly.
    Returns dict(point, lo, hi, samples) or None when the previous period is empty.
    """
    num_prev, den_prev, num_rec, den_rec = (np.asarray(a, dtype=float) for a in (num_prev, den_prev, num_rec, den_rec))
    if num_prev.sum() <= 0 or den_prev.sum() <= 0 or den_rec.sum() <= 0:
        return None
    point = (num_rec.sum() / den_rec.sum()) / (num_prev.sum() / den_prev.sum()) - 1.0
    rng = np.random.default_rng(seed)
    ip = _block_indices(len(num_prev), block, reps, rng)
    ir = _block_indices(len(num_rec), block, reps, rng)
    with np.errstate(divide="ignore", invalid="ignore"):
        share_prev = num_prev[ip].sum(1) / den_prev[ip].sum(1)
        share_rec = num_rec[ir].sum(1) / den_rec[ir].sum(1)
        samples = share_rec / share_prev - 1.0
    samples = samples[np.isfinite(samples)]
    if len(samples) < reps * 0.5:
        return {"point": float(point), "lo": None, "hi": None, "samples": samples}
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return {"point": float(point), "lo": float(lo), "hi": float(hi), "samples": samples}


def diff_interval(samples_a: np.ndarray, samples_b: np.ndarray):
    """95% interval for growth_a - growth_b from independent bootstrap samples."""
    n = min(len(samples_a), len(samples_b))
    if n < 100:
        return None
    d = samples_a[:n] - samples_b[:n]
    lo, hi = np.percentile(d, [2.5, 97.5])
    return float(np.median(d)), float(lo), float(hi)


# ---- trend ----------------------------------------------------------------------------
def theil_sen_slope(y: Sequence[float]) -> float:
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < 3:
        return float("nan")
    i, j = np.triu_indices(n, 1)
    return float(np.median((y[j] - y[i]) / (j - i)))


def mann_kendall_p(y: Sequence[float]) -> float:
    """Two-sided p-value of the Mann-Kendall monotonic trend test (normal approx., ties corrected)."""
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < 4:
        return float("nan")
    i, j = np.triu_indices(n, 1)
    s = float(np.sign(y[j] - y[i]).sum())
    _, counts = np.unique(y, return_counts=True)
    ties = sum(c * (c - 1) * (2 * c + 5) for c in counts if c > 1)
    var = (n * (n - 1) * (2 * n + 5) - ties) / 18.0
    if var <= 0:
        return 1.0
    z = (s - 1) / math.sqrt(var) if s > 0 else (s + 1) / math.sqrt(var) if s < 0 else 0.0
    return float(2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2)))))


def annual_trend(monthly: Sequence[float]) -> Dict[str, Optional[float]]:
    """Theil-Sen slope of log(monthly values), expressed as % change per year."""
    m = np.asarray(monthly, dtype=float)
    if len(m) < 6 or (m <= 0).sum() > len(m) * 0.2:
        return {"annual": None, "p": None}
    logm = np.log(np.maximum(m, 1e-9))
    slope = theil_sen_slope(logm)
    return {"annual": float(math.exp(12 * slope) - 1), "p": mann_kendall_p(logm)}


# ---- structural problems ------------------------------------------------------------------
def level_shift(x: np.ndarray, window: int = 56, ratio: float = 3.0, min_level: float = 8.0):
    """Largest persistent, non-seasonal jump between the 8-week medians before and after a day.

    8-week windows ignore short bumps (e.g. a New-Year peak). A jump that repeats about a
    year earlier or later in the same direction (school holidays, seasons) is treated as
    seasonal and skipped. What remains usually means a rename or merge, a new article,
    bot traffic or a measurement change, or a genuine regime change.
    Returns {'index', 'before', 'after', 'ratio'} or None.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 2 * window + 1:
        return None
    med = np.median(sliding_window_view(x, window), axis=1)  # med[k] = median(x[k:k+window])
    t = np.arange(window, n - window + 1)
    before, after = med[t - window], med[t]
    logr = np.log((after + 1.0) / (before + 1.0))
    big = (np.abs(logr) >= math.log(ratio)) & (np.maximum(before, after) >= min_level)
    for k in np.argsort(-np.abs(logr)):
        if not big[k]:
            break
        seasonal = False
        for lag in (-365, 365):
            lo, hi = k + lag - 21, k + lag + 21
            if lo < 0 or hi >= len(t):
                continue
            need = max(0.5 * abs(logr[k]), math.log(2.0))
            other = logr[lo:hi + 1] * np.sign(logr[k])
            level = np.maximum(before[lo:hi + 1], after[lo:hi + 1])
            if ((other >= need) & (level >= min_level)).any():
                seasonal = True
                break
        if not seasonal:
            return {"index": int(t[k]), "before": float(before[k]), "after": float(after[k]),
                    "ratio": float(math.exp(logr[k]))}
    return None


def first_active_index(x: np.ndarray, min_views: float = 1.0) -> int:
    nz = np.nonzero(np.asarray(x) >= min_views)[0]
    return int(nz[0]) if len(nz) else len(x)


# ---- monthly helpers ------------------------------------------------------------------------
def monthly_sums(x: np.ndarray, month_index: np.ndarray, n_months: int) -> np.ndarray:
    return np.bincount(month_index, weights=np.asarray(x, dtype=float), minlength=n_months)


def months_above_last_year(monthly: np.ndarray) -> Optional[int]:
    m = np.asarray(monthly, dtype=float)
    if len(m) < 24:
        return None
    return int((m[-12:] > m[-24:-12]).sum())


# ---- confidence -------------------------------------------------------------------------------
def direction_of(lo: Optional[float], hi: Optional[float], point: float) -> str:
    if lo is None or hi is None:
        return "unclear"
    if lo > 0:
        return "up"
    if hi < 0:
        return "down"
    return "flat"


def grade_confidence(m: dict) -> dict:
    """Rule-based confidence in the direction of relative growth for one series.

    Evidence checked: interval excludes zero, raw vs relative agreement, month-by-month
    consistency, dependence on spikes, level shifts, volume, and (for baskets) whether
    one article drives the result. Returns {grade, direction, good[], bad[]}.
    """
    rel = m.get("growth_rel")
    if rel is None:
        return {"grade": "n/a", "direction": "unclear", "good": [],
                "bad": [m.get("growth_note") or "growth cannot be computed for this period"]}
    lo, hi = m.get("growth_rel_lo"), m.get("growth_rel_hi")
    direction = direction_of(lo, hi, rel)
    good, bad, severe = [], [], False

    daily = m.get("daily_avg_recent", 0.0)
    low_volume = daily < 20
    if daily < 5:
        bad.append("very low volume (~%.0f views/day), numbers are noisy" % daily)
        severe = True
    elif low_volume:
        bad.append("low volume (~%.0f views/day)" % daily)
    else:
        good.append("solid volume (~%.0f views/day)" % daily)

    shift = m.get("level_shift")
    if shift and shift.get("kind") == "late_start":
        bad.append("the article only gets views from %s (created or renamed mid-period), so growth "
                   "partly reflects its appearance" % shift["date"])
        severe = True
    elif shift:
        msg = "sudden persistent level change around %s (x%.2g)" % (shift["date"], shift["ratio"])
        if shift.get("known_event"):
            msg += ": " + shift["known_event"]
        else:
            msg += ": check for a rename, merge, bot traffic or a real event"
        if shift.get("trend_after") is not None:
            msg += "; trend after it: %+.0f%%/yr" % (shift["trend_after"] * 100)
        bad.append(msg)
        severe = True

    if direction == "flat":
        width = (hi - lo) if (lo is not None and hi is not None) else 9.9
        if width <= 0.25 and not severe:
            grade = "medium"
            good.append("95%% interval is narrow (%+.0f%% to %+.0f%%), so any change is small" % (lo * 100, hi * 100))
        else:
            grade = "low"
            bad.append("95%% interval is wide (%+.0f%% to %+.0f%%)" % ((lo or 0) * 100, (hi or 0) * 100))
        return {"grade": grade, "direction": direction, "good": good, "bad": bad}

    sign = 1 if direction == "up" else -1
    good.append("95%% interval excludes zero (%+.0f%% to %+.0f%%)" % (lo * 100, hi * 100))
    fails = 1 if low_volume else 0

    raw = m.get("growth_abs")
    if raw is not None:
        if raw * sign > 0:
            good.append("raw views move the same way (%+.0f%%)" % (raw * 100))
        else:
            fails += 1
            bad.append("raw views move the other way (%+.0f%%): the change is relative to a %s wiki"
                       % (raw * 100, "shrinking" if (m.get("project_growth") or 0) < 0 else "growing"))

    up = m.get("months_up")
    if up is not None:
        agree = up if sign > 0 else 12 - up
        if agree >= 8:
            good.append("%d of the last 12 months moved the same way year-over-year" % agree)
        else:
            fails += 1
            bad.append("only %d of the last 12 months moved that way year-over-year" % agree)

    share = m.get("spike_share", 0.0)
    if share >= 0.25:
        fails += 1
        bad.append("%.0f%% of views came from short spikes" % (share * 100))
    else:
        good.append("spikes are only %.0f%% of views" % (share * 100))

    with_spikes = m.get("growth_rel_with_spikes")
    if with_spikes is not None and with_spikes * sign <= 0:
        fails += 1
        bad.append("the direction flips when spike days are kept (%+.0f%%)" % (with_spikes * 100))

    trend = m.get("trend_annual")
    if trend is not None and trend * sign < 0:
        fails += 1
        bad.append("the long-run monthly trend points the other way (%+.0f%%/yr)" % (trend * 100))

    if m.get("driven_by"):
        fails += 1
        bad.append("the result depends on one article (%s)" % m["driven_by"])

    if severe or fails >= 3:
        grade = "low"
    elif fails >= 1:
        grade = "medium"
    else:
        grade = "high"
    return {"grade": grade, "direction": direction, "good": good, "bad": bad}


# ---- ranking ------------------------------------------------------------------------------------
def percentile_ranks(values: List[Optional[float]]) -> List[Optional[float]]:
    """0..1 rank (1 = best) among non-missing values; ties share the average rank."""
    idx = [i for i, v in enumerate(values) if v is not None]
    out: List[Optional[float]] = [None] * len(values)
    if not idx:
        return out
    if len(idx) == 1:
        out[idx[0]] = 1.0
        return out
    vals = np.array([values[i] for i in idx], dtype=float)
    order = vals.argsort().argsort().astype(float)
    for v in np.unique(vals):  # average ties
        mask = vals == v
        order[mask] = order[mask].mean()
    for pos, i in enumerate(idx):
        out[i] = float(order[pos] / (len(idx) - 1))
    return out
