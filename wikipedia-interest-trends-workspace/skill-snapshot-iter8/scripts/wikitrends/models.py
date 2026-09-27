"""Time-series models for monthly series (numpy only, deterministic).

* seasonal_decompose - robust additive decomposition of a log series (trend, seasonal, remainder)
* forecast           - damped-trend Holt-Winters (ETS A,Ad,A) on logs, simulated 80% intervals,
                       and a hold-out backtest against the seasonal-naive forecast
* changepoints       - PELT with a piecewise-linear cost on the seasonally adjusted log series
* partial_pool       - empirical-Bayes shrinkage of growth estimates across related series
                       (random-effects / DerSimonian-Laird), which stabilises small wikis
Everything works on log values, so additive effects are multiplicative in views.
"""
from __future__ import annotations

import math
from itertools import product
from typing import Dict, List, Optional, Sequence

import numpy as np

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ---- seasonal decomposition --------------------------------------------------------------------
def _centered_ma12(x: np.ndarray) -> np.ndarray:
    """2x12 moving average; the six points at each edge are extended with a linear fit."""
    w = np.r_[0.5, np.ones(11), 0.5] / 12.0
    core = np.convolve(x, w, mode="valid")  # length n-12, centred on index 6..n-7
    out = np.full(len(x), np.nan)
    out[6:6 + len(core)] = core
    for side in ("left", "right"):
        idx = np.arange(6, 6 + min(12, len(core))) if side == "left" else \
            np.arange(6 + len(core) - min(12, len(core)), 6 + len(core))
        a, b = np.polyfit(idx, out[idx], 1)
        fill = np.arange(0, 6) if side == "left" else np.arange(6 + len(core), len(x))
        out[fill] = a * fill + b
    return out


MIN_SEASONAL_MONTHS = 36  # with 2 years, noise alone gives "moderate" seasonality in most series
MIN_FORECAST_MONTHS = 36  # a rolling-origin backtest needs 24 months of training + hold-out


def season_test(detr: np.ndarray, sims: int = 999, seed: int = 5) -> float:
    """p-value for "the calendar pattern repeats from year to year".

    The detrended series is cut into consecutive 12-month profiles (aligned on the calendar);
    the statistic is the mean pairwise correlation between the years' profiles. Under the null,
    each year's profile is rotated by a random number of months, which keeps its shape and
    autocorrelation but breaks the calendar alignment.
    """
    n = len(detr) // 12 * 12
    if n < 24:
        return 1.0
    prof = np.asarray(detr[len(detr) - n:], dtype=float).reshape(-1, 12)
    prof = prof - prof.mean(axis=1, keepdims=True)
    J = len(prof)

    def stat(P):
        c = np.corrcoef(P)
        return float(np.nanmean(c[np.triu_indices(J, 1)]))
    obs = stat(prof)
    if not np.isfinite(obs):
        return 1.0
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(sims):
        shifts = np.r_[0, rng.integers(0, 12, size=J - 1)]
        P = np.array([np.roll(prof[j], shifts[j]) for j in range(J)])
        hits += stat(P) >= obs - 1e-12
    return (1 + hits) / (1 + sims)


def seasonal_decompose(y: Sequence[float], months: Sequence[str], iterations: int = 3) -> Optional[dict]:
    """Decompose a log series with at least 36 monthly points.

    Returns trend, seasonal (per point), indices (per calendar month, mean 0), remainder,
    strength (0..1, share of seasonal+remainder variance explained by seasonality), `p` (the
    year-to-year repetition test above; seasonality counts only when p < 0.05), the peak and
    low calendar months with their effect in % versus an average month.
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < MIN_SEASONAL_MONTHS or not np.all(np.isfinite(y)):
        return None
    moy = np.array([int(m[5:7]) - 1 for m in months])
    seasonal = np.zeros(n)
    idx = np.zeros(12)
    for _ in range(iterations):
        trend = _centered_ma12(y - seasonal)
        detr = y - trend
        idx = np.array([np.median(detr[moy == k]) if (moy == k).any() else 0.0 for k in range(12)])
        idx -= idx.mean()
        seasonal = idx[moy]
    trend = _centered_ma12(y - seasonal)
    rem = y - trend - seasonal
    denom = np.var(seasonal + rem)
    strength = float(max(0.0, 1.0 - np.var(rem) / denom)) if denom > 0 else 0.0
    order = np.argsort(idx)
    effect = lambda k: float(math.exp(idx[k]) - 1)  # noqa: E731
    p = season_test(y - trend)
    return {"trend": trend, "seasonal": seasonal, "remainder": rem, "indices": idx, "strength": strength,
            "p": p, "significant": bool(p < 0.05), "years": n // 12,
            "peak": [(MONTH_NAMES[k], effect(k)) for k in order[::-1][:2]],
            "low": [(MONTH_NAMES[k], effect(k)) for k in order[:2]]}


# ---- forecasting -----------------------------------------------------------------------------------
def _hw_filter(y, alpha, beta, gamma, phi, m, seasonal):
    n = len(y)
    if seasonal:
        l = y[:m].mean()
        b = (y[m:2 * m].mean() - y[:m].mean()) / m if n >= 2 * m else 0.0
        s = list(y[:m] - l)
    else:
        l, b, s = y[0], (y[min(n - 1, 3)] - y[0]) / min(n - 1, 3) if n > 1 else 0.0, [0.0] * m
    errors = []
    start = m if seasonal else 1
    for t in range(start, n):
        st = s[t - m] if seasonal else 0.0
        yhat = l + phi * b + st
        e = y[t] - yhat
        errors.append(e)
        l_new = l + phi * b + alpha * e
        b = phi * b + beta * e
        if seasonal:
            s.append(st + gamma * e)
        l = l_new
    return l, b, s, np.array(errors)


def _hw_forecast(l, b, s, phi, m, h, seasonal):
    out, damp = [], 0.0
    n_s = len(s)
    for i in range(1, h + 1):
        damp += phi ** i
        st = s[n_s - m + (i - 1) % m] if seasonal else 0.0
        out.append(l + damp * b + st)
    return np.array(out)


def _fit(y, m, seasonal):
    grid = product((0.1, 0.2, 0.35, 0.5, 0.7), (0.01, 0.05, 0.15), (0.01, 0.1, 0.3) if seasonal else (0.0,),
                   (0.8, 0.9, 0.98))
    best = None
    for a, bt, g, ph in grid:
        if bt > a:
            continue
        l, b, s, e = _hw_filter(y, a, bt, g, ph, m, seasonal)
        sse = float(np.sum(e[1:] ** 2)) if len(e) > 1 else float("inf")
        if best is None or sse < best[0]:
            best = (sse, (a, bt, g, ph), (l, b, s), e)
    return best


def _snaive_path(y, h, drift):
    """Seasonal naive: repeat the value 12 months earlier, optionally plus the mean yearly change."""
    out = []
    ext = list(y)
    for _ in range(h):
        ext.append(ext[-12] + drift)
        out.append(ext[-1])
    return np.array(out)


def _method_forecast(method, y, h):
    m = 12
    if method == "ets":
        seasonal = len(y) >= 24
        _, (a, bt, g, ph), (l, b, s), _ = _fit(y, m, seasonal)
        return _hw_forecast(l, b, s, ph, m, h, seasonal)
    drift = float(np.mean(y[12:] - y[:-12])) if method == "snaive_drift" and len(y) > 12 else 0.0
    return _snaive_path(y, h, drift)


def forecast(y: Sequence[float], months: Sequence[str], horizon: int = 12, sims: int = 2000,
             seed: int = 11) -> Optional[dict]:
    """Forecast a monthly log series `horizon` months ahead.

    Candidates: ETS(A,Ad,A) (damped-trend Holt-Winters), seasonal naive (repeat last year) and
    seasonal naive with drift (plus the average year-over-year change). The one with the lowest
    mean absolute error on a rolling-origin backtest (6-month forecasts from up to 3 origins, each
    trained on >= 24 months) is used; series shorter than 36 months get no forecast. `skill` = 1 - MAE(ETS) / MAE(seasonal naive); > 0 means the smoothing model beats
    "same as last year". Returns median path and 80% band (log values) and the expected change
    of the next 12 months versus the last 12 with an 80% interval.
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < MIN_FORECAST_MONTHS or not np.all(np.isfinite(y)):
        return None  # too short to test any model against "same as last year"
    m = 12
    seasonal = True
    methods = ["ets", "snaive", "snaive_drift"] if seasonal else ["ets"]
    hold, errors = 6, {k: [] for k in methods}
    min_train = 24 if seasonal else 12
    for origin in (n - 18, n - 12, n - 6):
        if origin < min_train:
            continue
        train, test = y[:origin], y[origin:origin + hold]
        for k in methods:
            errors[k].append(float(np.mean(np.abs(_method_forecast(k, train, len(test)) - test))))
    mae = {k: float(np.mean(v)) for k, v in errors.items() if v}
    origins = len(errors["ets"])
    chosen = min(mae, key=mae.get) if mae else "ets"
    skill = float(1 - mae["ets"] / mae["snaive"]) if "ets" in mae and mae.get("snaive") else None

    rng = np.random.default_rng(seed)
    if chosen == "ets":
        sse, (a, bt, g, ph), (l, b, s), resid = _fit(y, m, seasonal)
        point = _hw_forecast(l, b, s, ph, m, horizon, seasonal)
        pool = resid[1:] if len(resid) > 2 else np.array([0.0])
        pool = pool - pool.mean()
        paths = np.empty((sims, horizon))
        for i in range(sims):
            li, bi, si = l, b, list(s)
            draws = rng.choice(pool, size=horizon)
            for hh in range(horizon):
                st = si[len(si) - m] if seasonal else 0.0
                yhat = li + ph * bi + st
                e = draws[hh]
                paths[i, hh] = yhat + e
                li, bi = li + ph * bi + a * e, ph * bi + bt * e
                if seasonal:
                    si.append(st + g * e)
    else:
        yoy = y[12:] - y[:-12]
        drift = float(yoy.mean()) if chosen == "snaive_drift" else 0.0
        point = _snaive_path(y, horizon, drift)
        noise = yoy - yoy.mean()
        # a whole year's deviation is shared by all 12 months ahead, so draw one per path
        shift = rng.choice(noise, size=(sims, 1)) if len(noise) else np.zeros((sims, 1))
        month_noise = rng.choice(noise, size=(sims, horizon)) * 0.5 if len(noise) else 0.0
        paths = point[None, :] + shift + month_noise
    lo, med, hi = np.percentile(paths, [10, 50, 90], axis=0)

    last12 = np.exp(y[-12:]).sum()
    if horizon >= 12:
        future = np.exp(paths[:, :12]).sum(axis=1) / last12 - 1
        change = float(np.exp(point[:12]).sum() / last12 - 1)
        c_lo, c_hi = (float(v) for v in np.percentile(future, [10, 90]))
    else:
        change = c_lo = c_hi = None

    y0, m0 = int(months[-1][:4]), int(months[-1][5:7])
    future_months = []
    for i in range(1, horizon + 1):
        k = (m0 - 1 + i)
        future_months.append("%04d-%02d" % (y0 + k // 12, k % 12 + 1))
    names = {"ets": "ETS(A,Ad,A) on log" if seasonal else "damped Holt on log",
             "snaive": "seasonal naive (repeat last year)",
             "snaive_drift": "seasonal naive + average yearly change"}
    return {"method": names[chosen], "chosen": chosen, "backtest_mae": mae,
            "months": future_months, "median": med, "lo80": lo, "hi80": hi, "point": point,
            "next12_vs_last12": change, "next12_lo80": c_lo, "next12_hi80": c_hi, "skill": skill,
            "origins": origins, "history_months": n}


# ---- changepoints ------------------------------------------------------------------------------------
def _linear_cost_factory(x: np.ndarray):
    n = len(x)
    t = np.arange(n, dtype=float)
    cs = {k: np.r_[0.0, np.cumsum(v)] for k, v in
          {"1": np.ones(n), "t": t, "tt": t * t, "x": x, "xx": x * x, "tx": t * x}.items()}

    def cost(i, j):  # RSS of a least-squares line on x[i:j]
        S = lambda k: cs[k][j] - cs[k][i]  # noqa: E731
        n_ = S("1")
        st, stt, sx, sxx, stx = S("t"), S("tt"), S("x"), S("xx"), S("tx")
        var_t = stt - st * st / n_
        cov = stx - st * sx / n_
        var_x = sxx - sx * sx / n_
        rss = var_x - (cov * cov / var_t if var_t > 1e-12 else 0.0)
        return max(rss, 0.0)
    return cost


def changepoints(x: Sequence[float], months: Sequence[str], min_seg: int = 6, penalty_mult: float = 6.0,
                 min_change: float = 0.15) -> List[dict]:
    """Breaks in level or slope of a (seasonally adjusted) log series, found with PELT.

    Each segment is a straight line; a break costs `penalty_mult * log(n)` noise variances.
    The noise scale comes from second differences (robust to the breaks themselves), inflated
    by the lag-1 autocorrelation of residuals from a global line, because monthly noise is
    rarely independent. With these settings about 3% of trend-only series with AR(1) noise
    get a false break, while level steps of ~40% and trend reversals are found 85-97% of the time.
    Breaks whose level jump and yearly-slope change are both below `min_change` are dropped.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 2 * min_seg or not np.all(np.isfinite(x)):
        return []
    d2 = np.diff(x, 2)
    sigma = float(np.median(np.abs(d2 - np.median(d2))) * 1.4826 / math.sqrt(6)) if len(d2) else 0.0
    t = np.arange(n)
    r = x - np.polyval(np.polyfit(t, x, 1), t)
    rho = float(np.corrcoef(r[:-1], r[1:])[0, 1]) if np.std(r) > 0 else 0.0
    rho = min(max(rho if np.isfinite(rho) else 0.0, 0.0), 0.8)
    sigma = max(sigma * math.sqrt((1 + rho) / (1 - rho)), 0.02)
    beta = penalty_mult * math.log(n) * sigma ** 2
    cost = _linear_cost_factory(x)
    F = [-beta] + [math.inf] * n
    last = [0] * (n + 1)
    cands = [0]
    for tau in range(min_seg, n + 1):
        best, arg = math.inf, None
        for s in cands:
            if tau - s >= min_seg:
                v = F[s] + cost(s, tau) + beta
                if v < best:
                    best, arg = v, s
        if arg is None:
            continue
        F[tau], last[tau] = best, arg
        cands = [s for s in cands if tau - s < min_seg or F[s] + cost(s, tau) <= F[tau]]
        cands.append(tau)
    cps, t = [], n
    while t > 0:
        s = last[t]
        if s > 0:
            cps.append(s)
        t = s
    cps = sorted(set(cps))
    out = []
    bounds = [0] + cps + [n]
    fits = []
    for i in range(len(bounds) - 1):
        seg = np.arange(bounds[i], bounds[i + 1])
        slope, icpt = np.polyfit(seg, x[seg], 1) if len(seg) > 1 else (0.0, x[seg[0]])
        fits.append((slope, icpt))
    for i, c in enumerate(cps):
        (s1, i1), (s2, i2) = fits[i], fits[i + 1]
        jump = (s2 * c + i2) - (s1 * c + i1)
        before = math.exp(12 * s1) - 1
        after = math.exp(12 * s2) - 1
        if abs(math.exp(jump) - 1) < min_change and abs(after - before) < min_change:
            continue
        out.append({"month": months[c], "level_jump": float(math.exp(jump) - 1),
                    "trend_before": float(before), "trend_after": float(after)})
    return out


# ---- partial pooling -----------------------------------------------------------------------------------
def partial_pool(estimates: List[Optional[dict]]) -> Optional[dict]:
    """Empirical-Bayes shrinkage of growth rates (random-effects model on log(1+g)).

    `estimates`: list of {"g", "lo", "hi"} (95% interval) or None. Noisy estimates (small wikis)
    move toward the group mean; precise ones barely move. Needs >= 3 usable estimates.
    Returns {"mu", "tau", "k", "items": [{"g", "lo", "hi", "weight"} or None]}.
    """
    use = []
    for e in estimates:
        if e and e.get("lo") is not None and e.get("hi") is not None and e["lo"] > -1 and e["hi"] > -1:
            y = math.log1p(e["g"])
            se = (math.log1p(e["hi"]) - math.log1p(e["lo"])) / (2 * 1.96)
            use.append((y, max(se, 1e-4)))
        else:
            use.append(None)
    valid = [u for u in use if u]
    if len(valid) < 3:
        return None
    ys = np.array([u[0] for u in valid])
    ses = np.array([u[1] for u in valid])
    w = 1 / ses ** 2
    mu_fe = float(np.sum(w * ys) / np.sum(w))
    q = float(np.sum(w * (ys - mu_fe) ** 2))
    denom = float(np.sum(w) - np.sum(w ** 2) / np.sum(w))
    tau2 = max(0.0, (q - (len(ys) - 1)) / denom) if denom > 0 else 0.0
    wr = 1 / (ses ** 2 + tau2)
    mu = float(np.sum(wr * ys) / np.sum(wr))
    items = []
    for u in use:
        if not u:
            items.append(None)
            continue
        y, se = u
        if tau2 <= 0:
            theta, sd, weight = mu, math.sqrt(1 / np.sum(wr)), 0.0
        else:
            weight = tau2 / (tau2 + se ** 2)
            theta = weight * y + (1 - weight) * mu
            sd = math.sqrt(tau2 * se ** 2 / (tau2 + se ** 2))
        items.append({"g": math.expm1(theta), "lo": math.expm1(theta - 1.96 * sd),
                      "hi": math.expm1(theta + 1.96 * sd), "weight": float(weight)})
    return {"mu": math.expm1(mu), "tau": math.sqrt(tau2), "k": len(valid), "items": items}
