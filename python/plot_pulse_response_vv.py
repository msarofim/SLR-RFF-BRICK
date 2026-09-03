"""Pulse sea-level response figures for the van Vuuren markers (Ladrillo, stage 2).

Three figures, from outputs/pulse_ladrillo_paths_* written by julia/scope_slr_pulse_vv.jl:

  1. CO2 -- focal marker with its full p05-p95 band, other markers as dotted medians
  2. CH4 -- the same
  3. both species on ONE per-tonne-CO2e basis, focal marker medians only

⚠ EVERY LABEL DERIVES FROM A NAMED CONSTANT below. Changing a filter, a window or a
basis without changing its label is the recurring bug class this guards against.

⚠ THE CO2e BASIS IS A CHOICE, NOT A FACT. Figure 3 divides the CH4 response by a
GWP100 and the number is stated in the axis label, not buried here: a different metric
moves that curve by ~3x (AR6 GWP20 = 82.5, GWP100 = 29.8) without changing one model
result. GWP100 is the default because it is the reporting convention, NOT because it is
the right metric for a sea-level response -- SLR integrates warming, so a metric built
on a 100-yr radiative-forcing integral is not obviously the matched one.

⚠ THE PLOTTED RANGE STARTS AT 2031, and that hides something real rather than by
accident: the response is EXACTLY zero before 2030 by construction, but a small
NEGATIVE reach-back appears from 2026 because Ladrillo's Greenland shape law reads a
CENTRED 30-yr running mean of GMST. It is <= 1.3e-04 cm for the CO2 pulse. Stated in
the figure footnote; see memory pulse_reachback_is_the_shape_window.
"""
import os, subprocess
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterSciNotation

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, FIGS = os.path.join(REPO, "outputs"), os.path.join(REPO, "figures")
SUFFIX = "_2030_spliced_L24_tap4p69K_V5p64m_tau800.csv"

# ---- the analysis choices, each with the label that reports it ---------------
FOCAL         = "M"
FOCAL_LABEL   = "vvM (middle marker)"
COMPONENT     = "total"
PULSE_YEAR    = 2030
PLOT_Y0, PLOT_Y1 = 2031, 2300
SPECIES = {"CO2": dict(size="10Gt", pulse_Gt=10.0, unit="GtCO$_2$", pretty="CO$_2$"),
           "CH4": dict(size="1Gt",  pulse_Gt=1.0,  unit="GtCH$_4$", pretty="CH$_4$")}
# AR6 WG1 Ch7 Table 7.15, fossil CH4, 100-yr. STATED in the axis label of figure 3.
GWP_NAME, GWP_VALUE, GWP_SOURCE = "GWP100", 29.8, "AR6 fossil CH$_4$"
# From the FaIR stage's own DOUBLING gate, 2026-09-03. Not a literature constant.
CH4_DOUBLING = 2.0332

# markers ordered by BASELINE dT@2100 -- the NAME order is not the forcing order
MARKER_ORDER = ["VL", "LN", "L", "ML", "HL", "M", "H"]
MARKER_DT    = {"VL": 1.640, "LN": 1.721, "L": 1.817, "ML": 2.348,
                "HL": 2.858, "M": 2.885, "H": 3.317}
ORDER_NOTE   = "markers ordered by baseline $\\Delta$T@2100, not by name"

BAND_LABEL   = "5th–95th percentile across 2000 posterior draws × 841 FaIR configs"
YLAB         = "sea-level response to the pulse (cm per {unit}, rel 1995–2014)"
YLAB_CO2E    = f"sea-level response (cm per Gt CO$_2$e, {GWP_NAME})"
TITLE        = "Sea-level response to a {pretty} pulse at {yr}, van Vuuren markers"
TITLE3       = "CO$_2$ vs CH$_4$ pulse on a common CO$_2$e basis — " + FOCAL_LABEL

# palette: validated categorical slots 1 & 2; context markers on a recessive gray
# ordinal ramp WITH direct labels, so identity never rests on color alone.
C_FOCAL, C_BAND = "#2a78d6", "#2a78d6"
C_CO2, C_CH4    = "#2a78d6", "#eb6834"
# Ordinal gray ramp, LIGHT = coolest marker -> DARK = warmest. The lightest step must
# still clear ~3:1 on the white surface: these lines carry direct labels, and a label
# below the contrast floor deletes the identity channel the gray ramp deliberately
# gives up. (First version started at #c9c8c3, ~1.9:1 -- too light to read.)
GRAY_RAMP       = ["#949289", "#7f7d75", "#6a6861", "#55534d", "#403e3a", "#2b2a27"]
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8880"

def commit():
    try:
        return subprocess.check_output(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                                       text=True).strip()
    except Exception:
        return "unknown"

PROV = ("Ladrillo L24 (tapped Greenland cell 4.69 K / 5.64 m / $\\tau$=800), joint arm, spliced forcing  |  "
        "FaIR 2.2.4 (calib 1.6.0) + CMIP7, 841 configs  |  2000 posterior draws  |  commit {c}")
FOOT = ("Response is exactly zero before " + str(PULSE_YEAR) + " by construction; a negative reach-back "
        "$\\leq$1.3e–04 cm appears from 2026 via Ladrillo's centred 30-yr Greenland smoother (not plotted).")

def _spread(ax, items, fontsize=9.5, pad=1.25):
    """Greedy vertical de-collision of right-edge direct labels, in DISPLAY space.

    The context markers are a recessive gray ramp on purpose, so the direct label IS
    the identity channel -- overlapping labels do not merely look untidy, they delete
    the only way to tell four of the seven lines apart. Nudging in display points
    (not data units) keeps the spacing correct on a log axis, where equal data gaps
    are unequal on screen. Returns [(y_data_of_anchor, y_display_offset_pts, ...)].
    """
    # ⚠ THE TRANSFORM RETURNS PIXELS, NOT POINTS, and at dpi=200 the two differ 2.8x.
    # A separation "in points" compared against pixel coordinates silently under-spaces
    # by that factor and the labels still overlap -- which is exactly what the first
    # version of this did. Derive the floor from the font size and the figure's own dpi.
    min_px = fontsize * ax.figure.dpi / 72.0 * pad
    tr = ax.transData
    inv = ax.transData.inverted()
    pts = sorted(((tr.transform((x, y))[1], i) for i, (x, y, *_ ) in enumerate(items)))
    placed = {}
    last = None
    for ydisp, i in pts:                      # bottom -> top, push up when too close
        yy = ydisp if last is None else max(ydisp, last + min_px)
        placed[i] = yy
        last = yy
    return {i: inv.transform((0, yy))[1] for i, yy in placed.items()}

def load(marker, sp):
    f = os.path.join(OUT, f"pulse_ladrillo_paths_vv{marker}_{sp}_{SPECIES[sp]['size']}{SUFFIX}")
    d = pd.read_csv(f)
    d = d[d.component == COMPONENT].set_index("year").sort_index()
    return d[(d.index >= PLOT_Y0) & (d.index <= PLOT_Y1)]

def style(ax, ylab, title, subtitle):
    ax.set_title(title, fontsize=13, color=INK, pad=30, loc="left", weight="medium")
    ax.text(0, 1.012, subtitle, transform=ax.transAxes, fontsize=9.5, color=INK2, va="bottom")
    ax.set_xlabel("year", fontsize=10, color=INK2)
    ax.set_ylabel(ylab, fontsize=10, color=INK2)
    ax.grid(True, which="major", lw=0.6, color="#e6e5e1", zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#d8d7d2")
    ax.tick_params(colors=INK2, labelsize=9)
    ax.set_xlim(PLOT_Y0, PLOT_Y1 + 26)

def band_figure(sp):
    m = SPECIES[sp]
    fig, ax = plt.subplots(figsize=(10.2, 6.2), dpi=200)
    ctx = [k for k in MARKER_ORDER if k != FOCAL]
    ends = []
    for i, k in enumerate(ctx):                       # context medians, dotted
        d = load(k, sp)
        y = d.med_diff_cm / m["pulse_Gt"]
        ax.plot(d.index, y, ls=":", lw=1.6, color=GRAY_RAMP[i], zorder=2)
        ends.append((d.index[-1], y.iloc[-1], k, GRAY_RAMP[i], 8.5, "medium"))
    d = load(FOCAL, sp)                                # focal band + median
    lo, hi = d.p05_diff_cm / m["pulse_Gt"], d.p95_diff_cm / m["pulse_Gt"]
    med = d.med_diff_cm / m["pulse_Gt"]
    ax.fill_between(d.index, lo, hi, color=C_BAND, alpha=0.16, lw=0, zorder=3,
                    label=BAND_LABEL)
    ax.plot(d.index, med, lw=2.4, color=C_FOCAL, zorder=4, label=f"{FOCAL_LABEL} median")
    ax.plot([], [], ls=":", lw=1.6, color=GRAY_RAMP[3],
            label=f"other markers, median only ({ORDER_NOTE})")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(LogFormatterSciNotation())
    sub = (f"{m['pulse_Gt']:.0f} {m['unit']} pulse, per {m['unit']}  |  {COMPONENT} sea level  |  "
           f"log scale spans the band's own {(hi/med).max():.0f}× skew")
    style(ax, YLAB.format(unit=m["unit"]), TITLE.format(pretty=m["pretty"], yr=PULSE_YEAR), sub)
    leg = ax.legend(loc="lower right", fontsize=9, frameon=True, framealpha=0.95,
                    edgecolor="#e0dfda", borderpad=0.8)
    leg.get_frame().set_linewidth(0.6)
    for t in leg.get_texts():
        t.set_color(INK2)
    ends.append((d.index[-1], med.iloc[-1], FOCAL, C_FOCAL, 9.5, "bold"))
    fig.canvas.draw()
    ypos = _spread(ax, ends)
    for i, (x, _y, k, col, fs, wt) in enumerate(ends):
        ax.annotate(f"vv{k}", (x, ypos[i]), xytext=(7, 0), textcoords="offset points",
                    fontsize=fs, color=col, va="center", weight=wt, annotation_clip=False)
    note = FOOT
    if sp == "CH4":
        note += (f"\n⚠ The 1 GtCH$_4$ pulse is SUPERLINEAR (FaIR doubling ratio {CH4_DOUBLING}) "
                 "and is 260% of one year's CH$_4$ emission — 'per Gt' is not a marginal rate.")
    fig.text(0.008, 0.028, note, fontsize=7.4, color=INK3, va="bottom")
    fig.text(0.008, 0.002, PROV.format(c=commit()), fontsize=7.0, color=INK3, va="bottom")
    fig.tight_layout(rect=[0, 0.075, 1, 1])
    p = os.path.join(FIGS, f"pulse_slr_response_{sp}_vv_markers.png")
    fig.savefig(p, facecolor="white"); plt.close(fig)
    return p

def co2e_figure():
    fig, ax = plt.subplots(figsize=(10.2, 6.2), dpi=200)
    for sp, col in (("CO2", C_CO2), ("CH4", C_CH4)):
        m = SPECIES[sp]
        d = load(FOCAL, sp)
        denom = m["pulse_Gt"] * (GWP_VALUE if sp == "CH4" else 1.0)
        y = d.med_diff_cm / denom
        lab = (f"{m['pretty']} pulse" if sp == "CO2"
               else f"{m['pretty']} pulse × {GWP_NAME} = {GWP_VALUE}")
        ax.plot(d.index, y, lw=2.4, color=col, zorder=4, label=lab)
        ax.annotate(m["pretty"], (d.index[-1], y.iloc[-1]), xytext=(7, 0),
                    textcoords="offset points", fontsize=10.5, color=col,
                    va="center", weight="bold")
    sub = (f"{FOCAL_LABEL}, medians only  |  {COMPONENT} sea level  |  "
           "equal-CO$_2$e pulses, so the gap is the metric's mismatch with sea level")
    style(ax, YLAB_CO2E, TITLE3, sub)
    leg = ax.legend(loc="upper left", fontsize=9.5, frameon=True, framealpha=0.95,
                    edgecolor="#e0dfda", borderpad=0.8)
    leg.get_frame().set_linewidth(0.6)
    for t in leg.get_texts():
        t.set_color(INK2)
    fig.text(0.008, 0.030,
             f"⚠ {GWP_NAME} = {GWP_VALUE} ({GWP_SOURCE}) is a CHOICE and it sets the CH$_4$ curve's height: "
             f"AR6 GWP20 = 82.5 would divide it by 2.8. A radiative-forcing metric is not matched to a\n"
             f"    sea-level response, which integrates warming — so the CH$_4$-above-CO$_2$ gap is a "
             f"statement about the METRIC, not only about the gases.\n" + FOOT,
             fontsize=7.4, color=INK3, va="bottom")
    fig.text(0.008, 0.002, PROV.format(c=commit()), fontsize=7.0, color=INK3, va="bottom")
    fig.tight_layout(rect=[0, 0.095, 1, 1])
    p = os.path.join(FIGS, "pulse_slr_response_co2e_comparison.png")
    fig.savefig(p, facecolor="white"); plt.close(fig)
    return p

if __name__ == "__main__":
    os.makedirs(FIGS, exist_ok=True)
    for p in (band_figure("CO2"), band_figure("CH4"), co2e_figure()):
        print("wrote", p)
