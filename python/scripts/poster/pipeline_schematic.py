"""
pipeline_schematic.py
=====================

Draft the pipeline schematic for the SLR poster, in two styles:
  (A) Linear flow with stages and arrows (journal-paper style)
  (B) Stage-grouped diagram with parallel inputs feeding a damage-function
      translation stage and three impact sectors (EPA-FrEDI-doc style)

Marcus picks one (or asks for a hybrid) when he reviews. Outputs:
    outputs/poster/pipeline_linear.{png,pdf}
    outputs/poster/pipeline_stages.{png,pdf}

Per CLAUDE.md "Writing prose: I draft main text" — these are figure
mockups with internal labels only. Marcus will adapt and reposition
on the final poster.
"""
from __future__ import annotations
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Palette (rough EPA-document earth tones; tweak as Marcus prefers)
# ---------------------------------------------------------------------------
PALETTE = {
    "emissions":   "#5C3317",   # brown
    "climate":     "#1F4E79",   # navy
    "slr":         "#2E7D32",   # green
    "damage_fn":   "#B7950B",   # ochre
    "impacts":     "#A6361C",   # rust
    "text":        "#0F0F0F",
    "arrow":       "#444444",
    "card_bg":     "#F7F4EE",
}

# Default font sizes assume the poster renders this image at ~12"×8" panel size
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   11,
    "axes.titlesize": 14,
})

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def box(ax, x, y, w, h, label, sub=None, color="#1F4E79", txtcolor="white",
        fontsize=12, sub_fontsize=9):
    """Place a rounded rectangle with header + optional sub-text."""
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.02,rounding_size=0.06",
                         linewidth=1.2, edgecolor=color, facecolor=color,
                         alpha=0.92)
    ax.add_patch(box)
    if sub:
        ax.text(x + w / 2, y + h * 0.62, label,
                ha="center", va="center", color=txtcolor,
                fontsize=fontsize, fontweight="bold")
        ax.text(x + w / 2, y + h * 0.28, sub,
                ha="center", va="center", color=txtcolor,
                fontsize=sub_fontsize, style="italic")
    else:
        ax.text(x + w / 2, y + h * 0.5, label,
                ha="center", va="center", color=txtcolor,
                fontsize=fontsize, fontweight="bold")


def arrow(ax, x0, y0, x1, y1, color=None, width=2.5, style="-|>"):
    a = FancyArrowPatch((x0, y0), (x1, y1),
                        arrowstyle=style, mutation_scale=18,
                        linewidth=width, color=color or PALETTE["arrow"])
    ax.add_patch(a)


# ---------------------------------------------------------------------------
# (A) Linear flow — top-to-bottom strip
# ---------------------------------------------------------------------------
def draw_linear():
    fig, ax = plt.subplots(figsize=(7, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.set_aspect("equal")
    ax.axis("off")

    # Stages, top-to-bottom
    stages = [
        # (label, sub, color, y)
        ("RFF-SP emissions",
         "10,000-member probabilistic\nsocioeconomic + emissions ensemble",
         PALETTE["emissions"], 12.0),
        ("FaIR v2.2.4 climate model",
         "841 calibrated configs × stochastic seeds\n→ probabilistic GMST(t) + OHC(t)",
         PALETTE["climate"],   9.5),
        ("MimiBRICK SLR + Wong importance weighting",
         "10,000-member BRICK posterior;\nWong (2025) AR(1) likelihood vs. observed GMSL",
         PALETTE["slr"],       7.0),
        ("Probabilistic GMSL(t) — cm rel. year 2000",
         "13,500-tuple 4-way H-S decomp; 2020–2300 horizon\n(emissions / climate cfg / internal var / BRICK)",
         PALETTE["slr"],       4.5),
        ("FrEDI damage-function translation",
         "11-yr rolling avg × interpolation between 6 Sweet et al. (2022)\nNCA5 nodes: 30, 50, 100, 150, 200, 300 cm GMSL",
         PALETTE["damage_fn"], 2.0),
        ("State-level economic + physical damages",
         "Coastal Properties  •  HTF Transportation  •  HTF Mortality (Sheahan)",
         PALETTE["impacts"],  -0.5),
    ]

    box_w, box_h = 8.6, 1.6
    for label, sub, color, y in stages:
        box(ax, x=0.7, y=y, w=box_w, h=box_h,
            label=label, sub=sub, color=color, fontsize=12, sub_fontsize=9)

    # Arrows between stages
    for i in range(len(stages) - 1):
        y_top = stages[i][3]
        y_bot = stages[i + 1][3] + box_h
        arrow(ax, 5.0, y_top, 5.0, y_bot)

    fig.tight_layout()
    fig.savefig(OUT / "pipeline_linear.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "pipeline_linear.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'pipeline_linear.png'}")


# ---------------------------------------------------------------------------
# (B) Stage-grouped — 3-column parallel inputs → damage-function row → 3 sectors
# ---------------------------------------------------------------------------
def draw_stages():
    # Slightly taller figure to fit a methods-description band along the bottom.
    fig, ax = plt.subplots(figsize=(13, 9.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(-1.6, 9)
    ax.set_aspect("equal")
    ax.axis("off")

    # Row 1: three parallel input streams
    col_w, col_h = 4.0, 1.8
    cols = [
        ("EMISSIONS",
         "• RFF-SP probabilistic ensemble\n• 10 000 socioeconomic +\n  emissions trajectories\n• Rennert et al. 2022",
         PALETTE["emissions"], 0.5),
        ("CLIMATE",
         "• FaIR v2.2.4, 841 v1.4.1-calibrated configs\n• Stochastic internal variability\n• GMST(t), OHC(t) trajectories\n• Smith et al. 2024",
         PALETTE["climate"], 5.0),
        ("SEA LEVEL",
         "• MimiBRICK 10k posterior subsample\n• Importance weighting (Wong 2026)\n• 1850–2300 horizon",
         PALETTE["slr"], 9.5),
    ]
    y0 = 7.0
    for name, sub, color, x in cols:
        box(ax, x=x, y=y0, w=col_w, h=col_h,
            label=name, sub=sub, color=color, fontsize=16, sub_fontsize=11.5)

    # Row 2: damage-function translation row
    df_y = 4.0
    df_x, df_w, df_h = 0.5, 13.0, 1.6

    # TOP CONNECTION (3 inputs → damage box): three short colored arrows drop
    # from each input box to a horizontal bracket that visually groups them,
    # then a single thick arrow drops from the bracket midpoint into the
    # damage box.  This conveys joint ingestion of emissions + climate + SLR
    # into FrEDI rather than three independent pipelines.
    top_bracket_y = df_y + df_h + 0.55
    bracket_x_left  = cols[0][3] + col_w / 2     # center of EMISSIONS column
    bracket_x_right = cols[-1][3] + col_w / 2    # center of SEA LEVEL column
    # Colored vertical arrows from each input box down to the bracket
    for _, _, color, x in cols:
        x_top = x + col_w / 2
        arrow(ax, x_top, y0, x_top, top_bracket_y, color=color, width=2.2)
    # Horizontal bracket
    ax.plot([bracket_x_left, bracket_x_right],
            [top_bracket_y, top_bracket_y],
            color=PALETTE["arrow"], linewidth=2.8, solid_capstyle="round",
            zorder=4)
    # Single thick arrow from bracket midpoint down to damage box top
    arrow(ax, 7.0, top_bracket_y, 7.0, df_y + df_h, width=3.0)

    box(ax, x=df_x, y=df_y, w=df_w, h=df_h,
        label="DAMAGE-FUNCTION TRANSLATION (FrEDI)",
        sub=("Sweet et al. (2022) NCA5 scenarios as interpolation nodes "
             "(0, 30, 50, 100, 150, 200, 250, 300 cm by 2100)\n"
             "11-year rolling average to smooth capital-investment lumps  •  "
             "Linear interpolation between bracketing SLR-cm scenarios per year"),
        color=PALETTE["damage_fn"], fontsize=16, sub_fontsize=11.5)

    # Row 3: three impact sectors
    imp_y = 0.8
    imp_top_y = imp_y + 1.8
    impacts = [
        ("Coastal Properties",
         "Neumann (2021) + Lorie (2020)\nNCPM benefit-cost decisions:\narmor / elevate / nourish / abandon\nVariant: Reactive",
         0.5),
        ("HTF Transportation",
         "Fant (2021)\nPassenger + freight delay costs;\nelevated-road & seawall protection\nVariant: Reasonably Anticipated",
         5.0),
        ("HTF Elder Mortality",
         "Sheahan et al. (2025)\nMueller (2024) flood-depth → mortality\nrelationship; ICLUS pop × BenMAP\nVSL = $7.9M (1990$)",
         9.5),
    ]
    for name, sub, x in impacts:
        box(ax, x=x, y=imp_y, w=col_w, h=1.8,
            label=name, sub=sub, color=PALETTE["impacts"],
            fontsize=14, sub_fontsize=10.5)

    # BOTTOM CONNECTION (damage box → 3 impacts): single thick arrow drops
    # from damage box to a horizontal bracket above the three impact boxes;
    # bracket has short downward ticks meeting the top of each impact box.
    bot_bracket_y = imp_top_y + 0.55
    imp_centers = [imp[2] + col_w / 2 for imp in impacts]
    # Single thick arrow from damage box bottom to bracket midpoint
    arrow(ax, 7.0, df_y, 7.0, bot_bracket_y, width=3.0)
    # Horizontal bracket spanning the three impact-box centers
    ax.plot([imp_centers[0], imp_centers[-1]],
            [bot_bracket_y, bot_bracket_y],
            color=PALETTE["arrow"], linewidth=2.8, solid_capstyle="round",
            zorder=4)
    # Three short arrows from bracket down to each impact box top
    for x_c in imp_centers:
        arrow(ax, x_c, bot_bracket_y, x_c, imp_top_y, width=2.0)

    # Bottom: outputs label
    ax.text(7.0, 0.3, "  →  STATE-LEVEL DAMAGES PER (YEAR, SCENARIO, ADAPTATION VARIANT)  ←",
            ha="center", va="center", fontsize=12, fontweight="bold",
            color=PALETTE["text"], style="italic")

    # Methods description block — pre-wrapped with textwrap.fill so the box
    # sizes correctly around the actual text (matplotlib's wrap=True is
    # unreliable; rendered text was overflowing the box previously).
    methods_text = (
        "METHODS:  Each RFF-SP emissions trajectory drives a stochastic FaIR "
        "climate run; GMST(t) and OHC(t) feed MimiBRICK to give a "
        "probabilistic global SLR trajectory.  BRICK draws are importance-"
        "weighted against observed GMSL (Wong 2026 AR(1) likelihood).  "
        "Per-year global SLR "
        "is matched to bracketing Sweet (2022) NCA5 nodes; FrEDI interpolates "
        "linearly between bracket-specific damage functions and applies an "
        "11-yr rolling average to smooth lumpy capital investments.  "
        "Output: per-(year, sector, state, scenario, adaptation variant) "
        "damages in 2015 USD."
    )
    wrapped = textwrap.fill(methods_text, width=125)
    n_lines = wrapped.count("\n") + 1
    line_h = 0.25                       # axis-units per line at fontsize 10.5
    methods_box_h = 0.50 + line_h * n_lines
    methods_box_y = -1.75
    rect = FancyBboxPatch((0.5, methods_box_y), 13.0, methods_box_h,
                          boxstyle="round,pad=0.04,rounding_size=0.08",
                          facecolor="#FAF7F0", edgecolor=PALETTE["text"],
                          linewidth=0.7, alpha=0.85)
    ax.add_patch(rect)
    ax.text(7.0, methods_box_y + methods_box_h / 2, wrapped,
            ha="center", va="center", fontsize=10.5, color=PALETTE["text"],
            family="DejaVu Sans")
    # Extend axis ylim to accommodate the box.
    ax.set_ylim(methods_box_y - 0.2, 9)

    fig.tight_layout()
    fig.savefig(OUT / "pipeline_stages.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "pipeline_stages.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'pipeline_stages.png'}")


# ---------------------------------------------------------------------------
def main():
    draw_linear()
    draw_stages()


if __name__ == "__main__":
    main()
