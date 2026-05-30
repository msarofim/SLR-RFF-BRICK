"""
lorie_panel.py
==============

Render the "how FrEDI's coastal damage functions are built" panel for the
SLR poster, anchored on Lorie et al. (2020) NCPM methodology plus the
FrEDI 11-year rolling-average smoothing step (EPA 2024 FrEDI Technical
Documentation).

Three sub-figures within one wide panel (~14" × 8"):
  (1) NCPM benefit-cost decision logic (text block, paraphrased from
      Lorie 2020 Section 2.4.2 and Figure 2)
  (2) Total adaptation + residual storm-surge cost stacks for Tampa &
      Virginia Beach under S1 (optimal BCR=1) vs. S4 (sub-optimal BCR=4),
      recreated from Lorie 2020 Table 1.
  (3) 11-year rolling-average smoothing — synthetic before/after illustration
      showing how FrEDI smooths NCPM's decadal capital-investment lumps
      into a continuous annual damage signal.

Output:
  outputs/poster/lorie_panel.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
COLORS = {
    "armor":          "#1F4E79",
    "elevate":        "#2E86AB",
    "nourish":        "#F4D35E",
    "abandon":        "#D62828",
    "residual":       "#E67E22",
    "smoothed":       "#1F4E79",
    "raw":            "#9C9C9C",
    "text_box":       "#FAF7F0",
    "text_border":    "#1F4E79",
}

# ---------------------------------------------------------------------------
# Lorie 2020 Table 1 data (discounted at 3%, 2015$ millions, total costs
# 2001-2100). Columns: Armor, Elevate, Nourish, Abandon, Residual Damage.
# Values inferred from Lorie 2020 Fig 4 (the actual proportions; total
# matches Table 1 columns). Headline totals from Table 1 are exact.
# ---------------------------------------------------------------------------
LORIE_FIG4 = {
    # (site, SLR_m, S): (armor, elevate, nourish, abandon, residual)
    ("Tampa", 0.5, "S1"):  (1100,   50, 1700,    40, 4684),
    ("Tampa", 0.5, "S4"):  ( 900,   30, 1700,   100, 5710),
    ("Tampa", 1.5, "S1"):  (1850,  100, 2200,    50, 5366),
    ("Tampa", 1.5, "S4"):  (1400,   80, 2200,   220, 6563),
    ("Virginia Beach", 0.5, "S1"):  (650,   20, 100,    20, 1966),
    ("Virginia Beach", 0.5, "S4"):  (550,   15, 100,    50, 2184),
    ("Virginia Beach", 1.5, "S1"):  (1300,   40, 200,    40, 2354),
    ("Virginia Beach", 1.5, "S4"):  (1000,   30, 200,   180, 2874),
}

# Lorie Table 1 totals (discounted, 2015$ millions) for header
LORIE_TOTALS = {
    ("Tampa", 0.5, "S1"): 7574,  ("Tampa", 0.5, "S4"): 8440,
    ("Tampa", 1.5, "S1"): 9566,  ("Tampa", 1.5, "S4"): 10453,
    ("Virginia Beach", 0.5, "S1"): 2756,  ("Virginia Beach", 0.5, "S4"): 2899,
    ("Virginia Beach", 1.5, "S1"): 3934,  ("Virginia Beach", 1.5, "S4"): 4284,
}


# ---------------------------------------------------------------------------
def draw_decision_logic(ax):
    """Panel A: NCPM decision logic, text block."""
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # Title
    ax.text(0.5, 0.96, "A.  NCPM benefit-cost decision logic",
            ha="center", va="top", fontsize=13, fontweight="bold",
            color=COLORS["text_border"])
    ax.text(0.5, 0.91, "(per 150-m grid cell, decade-by-decade  — Lorie 2020 §2.4.2)",
            ha="center", va="top", fontsize=9.5, style="italic", color="#555555")

    # Decision tree — three numbered NCPM steps. S=2 dropped per poster review
    # (May 17); the S=4 plain-English gloss that previously appeared at the
    # bottom of this panel is now covered in the layout caption (May 18).
    txt = [
        ("1.", "If cell not at risk from 100-yr storm"),
        ("",   "   surge over next decade →  no action."),
        ("",   ""),
        ("2.", "Else: compare 30-yr discounted avoided"),
        ("",   "   damages (EAD reduction) vs. cost of"),
        ("",   "   adaptation.  If BCR ≥ S  → armor or"),
        ("",   "   elevate."),
        ("",   "   Tested at S=1 (optimal) and S=4"),
        ("",   "   (sub-optimal)."),
        ("",   ""),
        ("3.", "Else: if 10-yr expected damages >"),
        ("",   "   property value → abandon."),
        ("",   "   Otherwise no adaptation."),
    ]

    y0 = 0.82
    for marker, line in txt:
        ax.text(0.02, y0, marker, fontsize=10, fontweight="bold",
                color=COLORS["text_border"], family="DejaVu Sans Mono",
                va="top", clip_on=True)
        ax.text(0.09, y0, line, fontsize=9.5, va="top",
                color="#222222", family="DejaVu Sans", clip_on=True)
        y0 -= 0.052

    # (Previously: sub-optimal cost-penalty callout box. Removed because
    # Panel B's "+9% / +11% / +5% / +8%" annotations on the bar chart already
    # convey the S=4 vs S=1 penalty quantitatively without redundancy.)


def draw_cost_stacks(ax):
    """Panel B: stacked-bar cost decomposition for Tampa & VA Beach × S1/S4."""
    # 8 bar positions: Tampa(0.5 S1, 0.5 S4, 1.5 S1, 1.5 S4) ; VB(...)
    labels = [
        ("Tampa\n0.5 m", "S1"), ("Tampa\n0.5 m", "S4"),
        ("Tampa\n1.5 m", "S1"), ("Tampa\n1.5 m", "S4"),
        ("VA Beach\n0.5 m", "S1"), ("VA Beach\n0.5 m", "S4"),
        ("VA Beach\n1.5 m", "S1"), ("VA Beach\n1.5 m", "S4"),
    ]
    keys = [
        ("Tampa", 0.5, "S1"), ("Tampa", 0.5, "S4"),
        ("Tampa", 1.5, "S1"), ("Tampa", 1.5, "S4"),
        ("Virginia Beach", 0.5, "S1"), ("Virginia Beach", 0.5, "S4"),
        ("Virginia Beach", 1.5, "S1"), ("Virginia Beach", 1.5, "S4"),
    ]
    n = len(keys)
    x = np.arange(n)

    armor    = np.array([LORIE_FIG4[k][0] for k in keys])
    elevate  = np.array([LORIE_FIG4[k][1] for k in keys])
    nourish  = np.array([LORIE_FIG4[k][2] for k in keys])
    abandon  = np.array([LORIE_FIG4[k][3] for k in keys])
    residual = np.array([LORIE_FIG4[k][4] for k in keys])
    total    = np.array([LORIE_TOTALS[k] for k in keys])

    # Stack
    w = 0.7
    b0 = np.zeros(n)
    for vals, color, lbl in [(armor,   COLORS["armor"],    "Armor"),
                             (elevate, COLORS["elevate"],  "Elevate"),
                             (nourish, COLORS["nourish"],  "Nourish"),
                             (abandon, COLORS["abandon"],  "Abandon"),
                             (residual, COLORS["residual"], "Residual storm surge")]:
        ax.bar(x, vals, w, bottom=b0, color=color, label=lbl,
               edgecolor="white", linewidth=0.6)
        b0 = b0 + vals

    # Mark sub-optimality penalty
    for i in range(0, n, 2):
        s1_total = total[i]
        s4_total = total[i + 1]
        penalty = (s4_total - s1_total) / s1_total * 100
        ax.text(x[i] + 0.5, max(s1_total, s4_total) + 250,
                f"+{penalty:.0f}%", ha="center", va="bottom",
                fontsize=9, color="#D62828", fontweight="bold")

    # Group dividers (between Tampa and VA Beach)
    ax.axvline(3.5, color="#888888", linestyle="--", linewidth=0.7, alpha=0.6)

    # Bottom labels with two rows
    ax.set_xticks(x)
    ax.set_xticklabels([f"{site}\n{s}" for site, s in labels], fontsize=8.5)

    ax.set_ylabel("Discounted total cost 2001-2100 (2015 USD millions)",
                  fontsize=10)
    ax.set_title("B.  Adaptation + residual storm-surge costs",
                 fontsize=13, fontweight="bold", color=COLORS["text_border"],
                 loc="center")
    ax.set_ylim(0, max(total) * 1.18)
    ax.grid(axis="y", alpha=0.3, linewidth=0.5)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.92)


# ---------------------------------------------------------------------------
# Panel C: stylized "why a pulse-capex damage function is wonky" concept.
# Two stacked graphs (annual cost vs time; implied damage function vs SLR).
# All data SYNTHETIC. Five scenarios + colors mirror the Sweet/Panel-F set.
# ---------------------------------------------------------------------------
_C_YEAR0, _C_YEAR1 = 2020, 2150
_C_YEARS = np.arange(_C_YEAR0, _C_YEAR1 + 1)
_C_YEAR_EVAL = 2100
_C_SCEN = {
    "Low":     dict(slr2100=30.0,  color="#1f78b4", lead=(2, 3),  label="Low"),
    "IntLow":  dict(slr2100=55.0,  color="#33a02c", lead=(3, 4),  label="Int-Low"),
    "Int":     dict(slr2100=95.0,  color="#fdbf6f", lead=(4, 2),  label="Intermediate"),
    "IntHigh": dict(slr2100=150.0, color="#ff7f00", lead=(6, 9),  label="Int-High"),
    "High":    dict(slr2100=200.0, color="#e31a1c", lead=(9, 13), label="High"),
}
_C_T1_CM, _C_T2_CM = 40.0, 100.0
_C_FLOW_K = 0.22
_C_CAPEX = (10.0, 24.0)
_C_CAPEX_HW = 2
_C_AMORT_WIN = 15
_C_P_ACCEL = 1.7


def _c_slr(slr2100):
    t100 = _C_YEAR_EVAL - _C_YEAR0
    return slr2100 * ((_C_YEARS - _C_YEAR0) / t100) ** _C_P_ACCEL


def _c_cross(slr, thr):
    return None if slr.max() < thr else int(np.argmax(slr >= thr))


def _c_capex(slr, lead):
    capex = np.zeros_like(slr)
    for thr, lead_yr, cx in zip((_C_T1_CM, _C_T2_CM), lead, _C_CAPEX):
        cross = _c_cross(slr, thr)
        if cross is None:
            continue
        peak = max(cross - lead_yr, 0)
        for off in range(-_C_CAPEX_HW, _C_CAPEX_HW + 1):
            j = peak + off
            if 0 <= j < len(capex):
                capex[j] += cx * (1.0 - abs(off) / (_C_CAPEX_HW + 1))
    return capex


def _c_roll(a, win):
    pad = win // 2
    ap = np.pad(a, (pad, pad), mode="edge")
    return np.convolve(ap, np.ones(win) / win, mode="valid")[:len(a)]


def draw_pulse_capex_concept(ax_top, ax_bot):
    """Panel C (two stacked axes): lumpy-capex annual cost over time (top) and
    the implied non-monotonic damage function vs the smoothed one (bottom)."""
    i_eval = int(np.where(_C_YEARS == _C_YEAR_EVAL)[0][0])
    anc_raw, anc_sm = {}, {}
    for name, sp in _C_SCEN.items():
        slr = _c_slr(sp["slr2100"])
        cost = _C_FLOW_K * slr + _c_capex(slr, sp["lead"])
        smooth = _C_FLOW_K * slr + _c_roll(_c_capex(slr, sp["lead"]), _C_AMORT_WIN)
        ax_top.plot(_C_YEARS, cost, color=sp["color"], lw=1.6,
                    label=sp["label"], zorder=3)
        anc_raw[name] = (slr[i_eval], cost[i_eval])
        anc_sm[name] = (slr[i_eval], smooth[i_eval])
        if name == "Int":
            ax_top.plot(_C_YEARS, smooth, color="#333", lw=1.4, ls=":",
                        label="Int, smoothed", zorder=4)

    ax_top.axvline(_C_YEAR_EVAL, color="#777", lw=0.7, ls="--", zorder=1)
    ax_top.set_xlim(_C_YEAR0, _C_YEAR1)
    ax_top.set_ylim(bottom=0)
    ax_top.set_xlabel("Year", fontsize=9)
    ax_top.set_ylabel("Annual cost (damage + capex)", fontsize=9)
    ax_top.set_title("C.  Lumpy adaptation capex → annual cost over time",
                     fontsize=12, fontweight="bold", color=COLORS["text_border"])
    ax_top.legend(fontsize=7, loc="upper left", framealpha=0.9, ncol=2)
    ax_top.grid(alpha=0.3, lw=0.5)
    ax_top.text(0.985, 0.96, "Stylized — synthetic data", fontsize=7.5,
                color="#777", style="italic", transform=ax_top.transAxes,
                ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFEF0",
                          edgecolor="#CCC", linewidth=0.6))

    names = list(_C_SCEN.keys())
    xs = np.array([anc_raw[n][0] for n in names])
    ys_raw = np.array([anc_raw[n][1] for n in names])
    ys_sm = np.array([anc_sm[n][1] for n in names])
    order = np.argsort(xs)
    xs_o = xs[order]
    grid = np.linspace(xs_o.min(), xs_o.max(), 400)
    ax_bot.plot(grid, np.interp(grid, xs_o, ys_raw[order]),
                color="#b2182b", lw=2.0, zorder=3, label="From pulse capex (wonky)")
    ax_bot.plot(grid, np.interp(grid, xs_o, ys_sm[order]),
                color="#333", lw=1.8, ls=":", zorder=4, label="From smoothed cost")
    for n in names:
        sx, sy = anc_raw[n]
        ax_bot.scatter([sx], [sy], color=_C_SCEN[n]["color"], s=70,
                       edgecolor="white", linewidth=1.1, zorder=5)
        smx, smy = anc_sm[n]
        ax_bot.scatter([smx], [smy], facecolor="white",
                       edgecolor=_C_SCEN[n]["color"], s=58, linewidth=1.4, zorder=5)
    for thr in (_C_T1_CM, _C_T2_CM):
        ax_bot.axvline(thr, color="#bbb", lw=0.7, ls="--", zorder=1)
    ax_bot.set_xlim(0, xs_o.max() * 1.02)
    ax_bot.set_ylim(bottom=0)
    ax_bot.set_xlabel(f"Sea-level rise at {_C_YEAR_EVAL} (cm)", fontsize=9)
    ax_bot.set_ylabel(f"Annual cost at {_C_YEAR_EVAL}", fontsize=9)
    ax_bot.set_title("Implied damage function — cost vs SLR",
                     fontsize=11, fontweight="bold", color=COLORS["text_border"])
    ax_bot.annotate("filled = lumpy anchor; open = smoothed.\n"
                    "Mid-capex scenario → non-monotonic.",
                    xy=(0.97, 0.05), xycoords="axes fraction", fontsize=6.6,
                    color="#b2182b", ha="right", va="bottom")
    ax_bot.legend(fontsize=7, loc="upper left", framealpha=0.9)
    ax_bot.grid(alpha=0.3, lw=0.5)


def main():
    fig = plt.figure(figsize=(19, 7.5))
    # A and B tightened (slightly narrower) to give the more complex two-graph
    # Panel C its own column with a nested 2-row sub-gridspec. wspace=0.40
    # keeps panel B's y-tick labels clear of panel A's decision-logic text.
    gs = fig.add_gridspec(1, 3, width_ratios=[0.85, 1.05, 1.15], wspace=0.42)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    gs_c = gs[0, 2].subgridspec(2, 1, hspace=0.45)
    ax3_top = fig.add_subplot(gs_c[0, 0])
    ax3_bot = fig.add_subplot(gs_c[1, 0])

    draw_decision_logic(ax1)
    draw_cost_stacks(ax2)
    draw_pulse_capex_concept(ax3_top, ax3_bot)

    # Internal suptitle dropped per poster review (May 17 2026); the panel
    # label in the poster layout serves as the title.
    # (No tight_layout: the nested sub-gridspec in column 3 is incompatible
    # with it; gridspec wspace/hspace + bbox_inches="tight" handle spacing.)
    fig.subplots_adjust(left=0.04, right=0.985, top=0.94, bottom=0.10)
    fig.savefig(OUT / "lorie_panel.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "lorie_panel.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'lorie_panel.png'}")


if __name__ == "__main__":
    main()
