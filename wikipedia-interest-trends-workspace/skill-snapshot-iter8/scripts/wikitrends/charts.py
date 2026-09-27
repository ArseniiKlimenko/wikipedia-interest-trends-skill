"""Static charts (PNG) for summaries and the PDF report.

Colour follows the series (fixed categorical order, never cycled), lines are thin,
grid and axes are recessive, and there is never a second y-axis: absolute views and
the relative index are two separate panels.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from .i18n import pct, tr  # noqa: E402

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#ffffff", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
MAX_LINES = 8


def _style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
        "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "legend.frameon": False,
        "xtick.major.size": 0, "ytick.major.size": 0,
    })


def _compact(v, _pos=None):
    v = float(v)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= div:
            s = "%.1f" % (v / div)
            return (s[:-2] if s.endswith(".0") else s) + suf
    return "%g" % v


def shown_series(series: List[dict]) -> List[dict]:
    """Measurable series drawn as lines: all of them, or the 8 largest (never cycle colours)."""
    ok = [s for s in series if s.get("status") == "ok"]
    if len(ok) <= MAX_LINES:
        return ok
    top = sorted(ok, key=lambda s: -s["views_recent_month_avg"])[:MAX_LINES]
    return [s for s in ok if s in top]


def colors_for(series: List[dict]) -> Dict[str, str]:
    """Stable colour per drawn series id, in the order the series were requested."""
    return {s["id"]: PALETTE[i] for i, s in enumerate(shown_series(series))}


def _month_ticks(ax, months: List[str]):
    n = len(months)
    step = 3 if n <= 24 else 6 if n <= 48 else 12
    ticks = [i for i in range(n) if int(months[i][5:]) % step == 1 or step == 1]
    ax.set_xticks(ticks)
    ax.set_xticklabels([("%s.%s" % (months[i][5:], months[i][2:4])) for i in ticks])
    ax.set_xlim(-0.5, n - 0.5)


def trend_chart(analysis: dict, path: Path, lang: str = "en") -> Path:
    _style()
    t = tr(lang)
    months = analysis["months"]
    n = len(months)
    k = analysis["period"]["growth_window_months"]
    ok = [s for s in analysis["series"] if s["status"] == "ok"]
    cmap = colors_for(analysis["series"])
    shown = shown_series(analysis["series"])
    base_len = 12 if n >= 24 else max(1, n // 2)

    fc_len = max((len(s["forecast"]["median"]) for s in shown if s.get("forecast")), default=0)
    with_fc = 0 < fc_len and len(shown) <= 4
    fc_months = next((s["forecast"]["months"] for s in shown if s.get("forecast")), [])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.4, 2.55))
    x = np.arange(n)
    for ax in (ax1, ax2):
        ax.axvspan(n - k - 0.5, n - 0.5, color="#f0efec", zorder=0, lw=0)
    values = []
    for s in shown:
        v = np.array(s["monthly"]["views"], dtype=float)
        values.append(v[v > 0])
        ax1.plot(x, v, color=cmap[s["id"]], lw=1.6, solid_capstyle="round", label=s["name"])
        share = np.array(s["monthly"]["share_ppm"], dtype=float)
        base = share[:base_len][share[:base_len] > 0].mean() if (share[:base_len] > 0).any() else np.nan
        if np.isfinite(base) and base > 0:
            ax2.plot(x, share / base * 100, color=cmap[s["id"]], lw=1.6, solid_capstyle="round")
            f = s.get("forecast")
            if with_fc and f:
                fx = np.arange(n - 1, n + len(f["median"]))
                med = np.r_[share[-1], f["median"]] / base * 100
                lo = np.r_[share[-1], f["lo80"]] / base * 100
                hi = np.r_[share[-1], f["hi80"]] / base * 100
                ax2.fill_between(fx, lo, hi, color=cmap[s["id"]], alpha=0.12, lw=0)
                ax2.plot(fx, med, color=cmap[s["id"]], lw=1.3, ls=(0, (3, 2)))
    allv = np.concatenate(values) if values else np.array([1.0])
    if len(allv) and allv.max() / max(allv.min(), 1) > 30:
        ax1.set_yscale("log")
    else:
        ax1.set_ylim(bottom=0)
    ax1.yaxis.set_major_formatter(FuncFormatter(_compact))
    ax2.axhline(100, color=AXIS, lw=0.9, zorder=1)
    ax1.set_title(t["chart_views"])
    ax2.set_title(t["chart_index"].format(k=base_len) + ((" + " + t["chart_fc"]) if with_fc else ""), fontsize=7.5)
    _month_ticks(ax1, months)
    _month_ticks(ax2, list(months) + (list(fc_months) if with_fc else []))
    for ax in (ax1, ax2):
        ax.grid(axis="x", visible=False)
    if len(ok) > len(shown):  # never hide series silently
        ax2.text(1.0, 1.0, t["chart_hidden"].format(n=len(shown), m=len(ok)), transform=ax2.transAxes,
                 ha="right", va="bottom", fontsize=6.3, color=MUTED)
    if len(shown) > 1:
        fig.legend(*ax1.get_legend_handles_labels(), loc="lower center", ncol=min(len(shown), 4),
                   fontsize=7, handlelength=1.4, borderaxespad=0.2)
        fig.tight_layout(rect=(0, 0.1 if len(shown) <= 4 else 0.17, 1, 1))
    else:
        fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def growth_chart(analysis: dict, path: Path, lang: str = "en") -> Path:
    _style()
    t = tr(lang)
    k = analysis["period"]["growth_window_months"]
    cmap = colors_for(analysis["series"])
    rows = [s for s in analysis["series"] if s["status"] == "ok" and s.get("growth_rel") is not None]
    rows.sort(key=lambda s: s["growth_rel"])
    single_hue = len([s for s in analysis["series"] if s["status"] == "ok"]) > len(PALETTE)
    h = 0.9 + 0.32 * max(len(rows), 1)
    fig, ax = plt.subplots(figsize=(3.5, min(h, 4.2)))
    alpha = {"high": 1.0, "medium": 0.75, "low": 0.45, "n/a": 0.3}
    y = np.arange(len(rows))
    lo_all, hi_all = [0.0], [0.0]
    for i, s in enumerate(rows):
        g = s["growth_rel"] * 100
        lo = (s.get("growth_rel_lo") if s.get("growth_rel_lo") is not None else s["growth_rel"]) * 100
        hi = (s.get("growth_rel_hi") if s.get("growth_rel_hi") is not None else s["growth_rel"]) * 100
        color = cmap[s["id"]] if (not single_hue and s["id"] in cmap) else PALETTE[0]
        ax.barh(i, g, height=0.5, color=color, alpha=alpha.get(s["confidence"]["grade"], 0.5), lw=0)
        ax.plot([lo, hi], [i, i], color=INK2, lw=0.9, solid_capstyle="butt")
        ax.plot([lo, lo], [i - 0.12, i + 0.12], color=INK2, lw=0.9)
        ax.plot([hi, hi], [i - 0.12, i + 0.12], color=INK2, lw=0.9)
        lo_all.append(lo)
        hi_all.append(hi)
    span = max(hi_all) - min(lo_all) or 10.0
    for i, s in enumerate(rows):
        hi = (s.get("growth_rel_hi") if s.get("growth_rel_hi") is not None else s["growth_rel"]) * 100
        label = "%s · %s" % (pct(s["growth_rel"]), t["conf"][s["confidence"]["grade"]])
        ax.text(max(hi, 0) + span * 0.03, i, label, va="center", ha="left", fontsize=6.8, color=INK2)
    ax.axvline(0, color=AXIS, lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels([s["name"] for s in rows], fontsize=7, color=INK)
    ax.set_xlim(min(lo_all) - span * 0.08, max(hi_all) + span * 0.55)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: "%+.0f%%" % v if v else "0"))
    ax.grid(axis="y", visible=False)
    ax.set_title(t["chart_growth"], fontsize=7.5)
    ax.set_xlabel(t["chart_growth_x"].format(k=k), fontsize=6.5)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def daily_chart(analysis: dict, daily: Dict[str, dict], path: Path, lang: str = "en") -> Path:
    """Diagnostic small multiples: raw daily views, spike-dampened line, flagged spikes."""
    _style()
    t = tr(lang)
    ok = [s for s in analysis["series"] if s["status"] == "ok" and s["id"] in daily][:6]
    if not ok:
        return path
    cmap = colors_for(analysis["series"])
    fig, axes = plt.subplots(len(ok), 1, figsize=(7.4, 1.25 * len(ok) + 0.3), squeeze=False, sharex=True)
    for ax, s in zip(axes[:, 0], ok):
        d = daily[s["id"]]
        x = np.arange(len(d["raw"]))
        ax.plot(x, d["raw"], color="#c3c2b7", lw=0.6)
        ax.plot(x, d["clean"], color=cmap.get(s["id"], PALETTE[0]), lw=1.0)
        sp = np.nonzero(d["spike"])[0]
        if len(sp):
            ax.scatter(sp, np.asarray(d["raw"])[sp], s=6, color=INK2, zorder=3, lw=0)
        if s.get("level_shift"):
            try:
                idx = d["dates"].index(s["level_shift"]["date"])
                ax.axvline(idx, color="#e34948", lw=0.9)
            except ValueError:
                pass
        ax.set_title(s["name"], fontsize=7)
        ax.yaxis.set_major_formatter(FuncFormatter(_compact))
        ax.set_ylim(bottom=0)
    dates = daily[ok[0]["id"]]["dates"]
    ticks = [i for i, dstr in enumerate(dates) if dstr.endswith("-01") and int(dstr[5:7]) in (1, 4, 7, 10)]
    axes[-1, 0].set_xticks(ticks)
    axes[-1, 0].set_xticklabels([dates[i][:7] for i in ticks])
    fig.suptitle(t["chart_daily"], x=0.01, ha="left", fontsize=8, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
