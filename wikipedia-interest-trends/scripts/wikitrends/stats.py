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
# two-sided 97.5% quantiles of Student's t (df 1..30); larger df use 1.96 + 2.4/df
_T975 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145,
         2.131, 2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048,
         2.045, 2.042]


def t975(df: int) -> float:
    return _T975[df - 1] if 1 <= df <= 30 else 1.96 + 2.4 / max(df, 1)


def t_pvalue(t: float, df: int) -> float:
    """Two-sided p-value of a t statistic (normal approximation with a df correction)."""
    if not np.isfinite(t) or df < 1:
        return 1.0
    z = abs(t) * (1 - 1 / (4.0 * df)) / math.sqrt(1 + t * t / (2.0 * df))
    return float(2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))))


def _circular_blocks(n: int, block: int, reps: int, rng) -> np.ndarray:
    """Day indices of `reps` circular block-bootstrap resamples of length n."""
    block = max(1, min(block, n))
    n_blocks = int(math.ceil(n / block))
    starts = rng.integers(0, n, size=(reps, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % n
    return idx.reshape(reps, -1)[:, :n]


def autocorr_inflation(d: np.ndarray) -> float:
    """Standard-error inflation sqrt((1+r)/(1-r)) from the lag-1 autocorrelation r (clipped to 0..0.7)."""
    d = np.asarray(d, dtype=float)
    if len(d) < 4 or np.std(d) == 0:
        return 1.0
    e = d - d.mean()
    r = float(np.sum(e[1:] * e[:-1]) / np.sum(e * e))
    r = min(max(r if np.isfinite(r) else 0.0, 0.0), 0.7)
    return math.sqrt((1 + r) / (1 - r))


def monthly_log_ratios(num_prev, den_prev, num_rec, den_rec, month_prev, month_rec) -> Optional[np.ndarray]:
    """log(share in month m of the recent period / share in month m of the previous period), m = 0..k-1.

    Month m of both periods is the same calendar month, so seasonality cancels out."""
    if month_prev is None or month_rec is None:
        return None
    k = int(max(np.max(month_prev), np.max(month_rec))) + 1
    out = []
    for m in range(k):
        a, b = month_rec == m, month_prev == m
        if not a.any() or not b.any() or den_rec[a].sum() <= 0 or den_prev[b].sum() <= 0:
            return None
        s_rec = (num_rec[a].sum() + 0.5) / den_rec[a].sum()  # +0.5 keeps empty months finite
        s_prev = (num_prev[b].sum() + 0.5) / den_prev[b].sum()
        out.append(math.log(s_rec / s_prev))
    return np.array(out)


def ratio_growth(num_prev, den_prev, num_rec, den_rec, block: int = 28, reps: int = 2000, seed: int = 7,
                 month_prev=None, month_rec=None):
    """Growth of sum(num)/sum(den) from the previous to the recent period.

    With den = project totals this is the change in the topic's share of all views
    ("relative growth"); with den = ones it is plain growth in views.

    The 95% interval is the union of two intervals, so it stays honest when the noise is
    persistent (a common failure of plain bootstraps on web traffic):
      * a paired circular block bootstrap: day i of the recent period is resampled together
        with day i of the previous period (the same season), in 28-day blocks, numerator and
        denominator jointly; pairing removes seasonality from the noise;
      * a t-interval on the k monthly log-ratios (same calendar month, recent vs previous),
        with its standard error inflated for their lag-1 autocorrelation.
    Every series of an analysis uses the same block indices (they depend only on the length,
    block and seed), so bootstrap samples of two series are paired across series too, and
    diff_interval() keeps shocks they share (the wiki total, holidays).
    Returns dict(point, lo, hi, samples, p, monthly) or None when the previous period is empty.
    `samples` has length `reps` (NaN where a resample is undefined); `p` is a two-sided p-value
    for "no change" (the larger of the bootstrap and t-test p-values).
    """
    num_prev, den_prev, num_rec, den_rec = (np.asarray(a, dtype=float) for a in (num_prev, den_prev, num_rec, den_rec))
    if num_prev.sum() <= 0 or den_prev.sum() <= 0 or den_rec.sum() <= 0:
        return None
    point = (num_rec.sum() / den_rec.sum()) / (num_prev.sum() / den_prev.sum()) - 1.0
    n = min(len(num_prev), len(num_rec))
    rng = np.random.default_rng(seed)
    idx = _circular_blocks(n, block, reps, rng)
    with np.errstate(divide="ignore", invalid="ignore"):
        share_prev = num_prev[:n][idx].sum(1) / den_prev[:n][idx].sum(1)
        share_rec = num_rec[:n][idx].sum(1) / den_rec[:n][idx].sum(1)
        samples = share_rec / share_prev - 1.0
    samples[~np.isfinite(samples)] = np.nan
    fin = samples[np.isfinite(samples)]
    out = {"point": float(point), "lo": None, "hi": None, "samples": samples, "p": None, "monthly": None}
    if len(fin) < reps * 0.5:
        return out
    lo, hi = (float(v) for v in np.percentile(fin, [2.5, 97.5]))
    p_boot = min(1.0, 2 * min(float(np.mean(fin <= 0)), float(np.mean(fin >= 0))) + 1.0 / reps)
    p = p_boot
    d = monthly_log_ratios(num_prev, den_prev, num_rec, den_rec,
                           None if month_prev is None else np.asarray(month_prev),
                           None if month_rec is None else np.asarray(month_rec))
    if d is not None and len(d) >= 4 and point > -1:
        se = float(np.std(d, ddof=1) / math.sqrt(len(d))) * autocorr_inflation(d)
        c = math.log1p(point)
        tq = t975(len(d) - 1)
        lo, hi = min(lo, math.expm1(c - tq * se)), max(hi, math.expm1(c + tq * se))
        p = max(p, t_pvalue(c / se, len(d) - 1) if se > 0 else 0.0)
        out["monthly"] = [float(v) for v in d]
    out.update(lo=lo, hi=hi, p=float(p))
    return out


def diff_interval(a: dict, b: dict):
    """95% interval for growth_a - growth_b (in growth units) from two ratio_growth() results.

    Bootstrap samples are paired (same resampled days for both series); monthly log-ratio
    differences give a second, autocorrelation-inflated t-interval; the union is returned
    as (difference, lo, hi)."""
    sa, sb = np.asarray(a.get("samples", []), dtype=float), np.asarray(b.get("samples", []), dtype=float)
    if len(sa) != len(sb) or len(sa) < 100:
        return None
    both = np.isfinite(sa) & np.isfinite(sb)
    if both.sum() < 100:
        return None
    dd = sa[both] - sb[both]
    lo, hi = (float(v) for v in np.percentile(dd, [2.5, 97.5]))
    diff = a["point"] - b["point"]
    ma, mb = a.get("monthly"), b.get("monthly")
    if ma and mb and len(ma) == len(mb) and len(ma) >= 4 and a["point"] > -1 and b["point"] > -1:
        z = np.array(ma) - np.array(mb)
        se = float(np.std(z, ddof=1) / math.sqrt(len(z))) * autocorr_inflation(z)
        L = math.log1p(a["point"]) - math.log1p(b["point"])
        tq = t975(len(z) - 1)
        base = 1 + b["point"]
        lo, hi = min(lo, base * math.expm1(L - tq * se)), max(hi, base * math.expm1(L + tq * se))
    return float(diff), float(lo), float(hi)


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
def level_shift(x: np.ndarray, window: int = 56, ratio: float = 3.0, min_level: float = 8.0, min_index: int = 0):
    """Largest persistent, non-seasonal jump between the 8-week medians before and after a day.

    `x` may include extra history before the analysed period; only jumps at index >= min_index
    are reported, but the history lets the seasonal check look a year back.

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
        if t[k] < min_index:
            continue
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

    short = m.get("short_window")
    if short:
        bad.append("the period is shorter than 24 months, so seasonality is not controlled (confidence capped at LOW)")
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

    ev = m.get("event_step")
    if ev and ev.get("flag"):
        step = ev["rel"]
        if step * sign > 0:
            fails += 1
            bad.append("around the May-June 2025 bot-detection update this series moved %+.0f%% relative to its wiki "
                       "(%s); part of the %s may be a measurement artifact"
                       % (step * 100, "seasonally adjusted" if ev.get("adjusted") else "not seasonally adjusted",
                          "decline" if sign < 0 else "rise"))
        else:
            bad.append("around the May-June 2025 bot-detection update this series moved %+.0f%% relative to its "
                       "wiki, against the measured direction" % (step * 100))

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
