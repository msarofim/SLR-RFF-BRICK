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


def draw_smoothing(ax):
    """Panel C: 11-year rolling-average illustration."""
    # Synthetic series: lumpy decadal capital investments + light annual
    # residual damage, then a smoothed continuous signal.
    years = np.arange(2001, 2101)
    np.random.seed(2026)

    # Underlying smooth signal (climate-driven costs grow with SLR)
    smooth = 50 + 0.35 * (years - 2000) + 0.013 * (years - 2000) ** 2  # millions

    # Lumpy capital investments at decadal armor decisions
    raw = smooth.copy()
    decade_starts = [2010, 2020, 2030, 2040, 2050, 2060, 2070, 2080, 2090]
    pulse_sizes   = [180,  260,  300,  370,  340,  280,  500,  430,  420]
    for ds, p in zip(decade_starts, pulse_sizes):
        idx = ds - 2001
        if 0 <= idx < len(years):
            raw[idx] += p

    # 11-year centered rolling average (the FrEDI smoothing step)
    half_window = 5
    smoothed = np.copy(raw)
    for i in range(len(years)):
        lo = max(0, i - half_window)
        hi = min(len(years), i + half_window + 1)
        smoothed[i] = np.mean(raw[lo:hi])

    ax.plot(years, raw, color=COLORS["raw"], linewidth=1.0,
            label="Raw decadal capital lumps", marker="o", markersize=3,
            alpha=0.7)
    ax.plot(years, smoothed, color=COLORS["smoothed"], linewidth=2.4,
            label="FrEDI 11-yr rolling average")

    # ("Discrete armor decision" annotation removed per poster review May 18 —
    # it cluttered the top of the plot and is already implicit from the
    # raw-vs-smoothed contrast.)

    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Annual cost (2015 USD millions)", fontsize=10)
    ax.set_title("C.  Stylized illustration of FrEDI's\n"
                 "  11-year rolling-average smoothing",
                 fontsize=13, fontweight="bold", color=COLORS["text_border"],
                 loc="center")
    ax.grid(alpha=0.3, linewidth=0.5)
    # Legend placed in lower-right so it doesn't compete with the stylized
    # callout box at top-right.
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.92)
    ax.set_xlim(2001, 2100)
    # Pad ylim so the callout has clearance above the highest data line.
    cur_ymin, cur_ymax = ax.get_ylim()
    ax.set_ylim(cur_ymin, cur_ymax * 1.15)
    # Compact "stylized" flag at top-right inside the axes (rendered after
    # ylim is set so the box doesn't get squeezed).
    ax.text(0.98, 0.97,
            "Stylized illustration —\nsynthetic data",
            fontsize=8, color="#777", style="italic",
            transform=ax.transAxes, ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFEF0",
                      edgecolor="#CCC", linewidth=0.6))


def main():
    fig = plt.figure(figsize=(18, 7.5))
    # wspace=0.40 gives the y-axis tick labels of panel B clear room from
    # panel A's decision-logic text. Previously wspace=0.25 left them
    # overlapping with the body of panel A on the right edge.
    gs = fig.add_gridspec(1, 3, width_ratios=[0.95, 1.15, 1.0], wspace=0.40)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])

    draw_decision_logic(ax1)
    draw_cost_stacks(ax2)
    draw_smoothing(ax3)

    # Internal suptitle dropped per poster review (May 17 2026); the panel
    # label in the poster layout serves as the title.
    fig.tight_layout(rect=[0, 0.01, 1, 0.98])
    fig.savefig(OUT / "lorie_panel.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "lorie_panel.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'lorie_panel.png'}")


if __name__ == "__main__":
    main()
