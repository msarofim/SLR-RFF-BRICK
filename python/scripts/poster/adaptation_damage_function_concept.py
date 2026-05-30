"""
adaptation_damage_function_concept.py
=====================================

STYLIZED / conceptual figure for poster Panel G. Two stacked stylized graphs
illustrating why a damage function built from lumpy (pulse) adaptation capital
expenditures is "wonky" (non-monotonic), whereas one built from smoothed
expenditures is smooth.

ALL DATA HERE ARE SYNTHETIC and illustrative — no model output is read. The
five scenarios + their colors mirror the Sweet et al. NCA5 scenarios used in
Panel F so the two panels read as a matched pair.

Top graph  — annual cost vs TIME, one line per scenario (Sweet-style fan):
             flow damage rising ∝ SLR, REDUCED after each one-time adaptation
             capital expenditure (a built defense lowers ongoing damage), plus
             the two capex bumps themselves (~40 cm and ~100 cm SLR thresholds).
             Higher-SLR scenarios reach the thresholds sooner AND trigger the
             capex a few years EARLIER relative to the threshold (more
             anticipatory adaptation). Dotted black: the 11-yr-smoothed
             (amortized) annual cost for the representative (Int) scenario.

Bottom graph — annual cost vs SEA-LEVEL RISE at a single year (YEAR_EVAL),
             built exactly like Panel F's right figure: each scenario
             contributes ONE colored anchor dot = (its SLR at YEAR_EVAL, its
             annual cost at YEAR_EVAL); the damage function interpolates
             through those 5 dots.
             Solid (wonky, non-monotonic): dots from the raw pulse-capex cost —
             because at YEAR_EVAL different scenarios sit at different points in
             their capex cycle (one mid-spike, one in a post-adaptation dip),
             the anchors are not monotonic in SLR, so the interpolated curve is
             wonky. Dotted (smooth): dots from the smoothed cost → smooth,
             monotone damage function.

Output:
  outputs/poster/G_adaptation_damage_concept.{png,pdf}
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

EDGE = "#1F4E79"

YEAR0, YEAR1 = 2020, 2150
YEARS = np.arange(YEAR0, YEAR1 + 1)
T = YEARS - YEAR0
YEAR_EVAL = 2100               # year at which the bottom-panel dots are read

# Five scenarios: SLR at 2100 (cm) + Panel-F colors + capex lead (yrs before
# each threshold crossing). Higher scenarios → larger lead (more anticipatory).
# slr2100 chosen so that at YEAR_EVAL the MIDDLE scenario (Int) is caught right
# in its 2nd capex spike, popping its damage-function anchor above the higher-
# SLR scenarios → a genuinely non-monotonic raw damage function. Higher
# scenarios crossed both thresholds years ago (capex done → back on the flow
# trend); lower scenarios never reach the 2nd threshold.
SCEN = {
    "Low":     dict(slr2100=30.0,  color="#1f78b4", lead=(2, 3),  label="Low"),
    "IntLow":  dict(slr2100=55.0,  color="#33a02c", lead=(3, 4),  label="Int-Low"),
    "Int":     dict(slr2100=95.0,  color="#fdbf6f", lead=(4, 2),  label="Intermediate"),
    "IntHigh": dict(slr2100=150.0, color="#ff7f00", lead=(6, 9),  label="Int-High"),
    "High":    dict(slr2100=200.0, color="#e31a1c", lead=(9, 13), label="High"),
}
REP = "Int"                    # scenario used for the smoothed time overlay

T1_CM, T2_CM = 40.0, 100.0     # the two adaptation thresholds
FLOW_K = 0.22                  # $ (arb.) per cm of SLR — flow damage (monotone)
CAPEX = (10.0, 24.0)           # one-time adaptation capital costs
CAPEX_HALFWIDTH = 2            # narrow triangular spike: ± this many years
AMORT_WIN = 15                 # capex amortization window (smoothed expenditure)
SMOOTH_WIN = 15                # rolling-average window for the time-axis overlay
P_ACCEL = 1.7                  # SLR acceleration exponent


def slr_curve(slr2100):
    """Accelerating SLR; hits slr2100 exactly at YEAR_EVAL, continues to YEAR1."""
    t100 = YEAR_EVAL - YEAR0
    return slr2100 * (T / t100) ** P_ACCEL


def first_cross(slr, thresh):
    if slr.max() < thresh:
        return None
    return int(np.argmax(slr >= thresh))


def capex_stream(slr, lead):
    """Lumpy one-time capex: a narrow triangular spike placed `lead` years
    before each SLR-threshold crossing. Flow damage is NOT reduced afterward —
    the lumpiness lives entirely in the capex (matches the brief: 'damages rise
    in proportion to SLR ... with two one-time capital expenditures')."""
    capex = np.zeros_like(slr)
    for thr, lead_yr, cx in zip((T1_CM, T2_CM), lead, CAPEX):
        cross = first_cross(slr, thr)
        if cross is None:
            continue
        peak = max(cross - lead_yr, 0)
        hw = CAPEX_HALFWIDTH
        for off in range(-hw, hw + 1):
            j = peak + off
            if 0 <= j < len(capex):
                capex[j] += cx * (1.0 - abs(off) / (hw + 1))
    return capex


def annual_cost_raw(slr, lead):
    """Flow damage (∝ SLR, monotone) + lumpy capex spikes."""
    return FLOW_K * slr + capex_stream(slr, lead)


def annual_cost_smoothed(slr, lead):
    """Flow damage + AMORTIZED capex (the same capital spread smoothly over
    AMORT_WIN years) — the 'smoothed expenditure' version."""
    return FLOW_K * slr + rolling(capex_stream(slr, lead), AMORT_WIN)


def rolling(a, win):
    pad = win // 2
    ap = np.pad(a, (pad, pad), mode="edge")
    return np.convolve(ap, np.ones(win) / win, mode="valid")[:len(a)]


def main():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5.4, 7.0))
    i_eval = int(np.where(YEARS == YEAR_EVAL)[0][0])

    # ---------- TOP: annual cost vs time, one line per scenario ----------
    anchors_raw = {}    # name -> (slr@eval, cost@eval)
    anchors_smooth = {}
    for name, sp in SCEN.items():
        slr = slr_curve(sp["slr2100"])
        cost = annual_cost_raw(slr, sp["lead"])
        smooth = annual_cost_smoothed(slr, sp["lead"])
        ax1.plot(YEARS, cost, color=sp["color"], lw=1.8, label=sp["label"], zorder=3)
        anchors_raw[name] = (slr[i_eval], cost[i_eval])
        anchors_smooth[name] = (slr[i_eval], smooth[i_eval])
        if name == REP:
            ax1.plot(YEARS, smooth, color="#333333", lw=1.5, ls=":",
                     label="Int, smoothed", zorder=4)

    ax1.axvline(YEAR_EVAL, color="#777", lw=0.8, ls="--", zorder=1)
    ax1.text(YEAR_EVAL + 1, ax1.get_ylim()[1] * 0.96, f"{YEAR_EVAL}",
             fontsize=7.5, color="#555", va="top")
    ax1.set_xlim(YEAR0, YEAR1)
    ax1.set_ylim(bottom=0)
    ax1.set_xlabel("Year", fontsize=9)
    ax1.set_ylabel("Annual cost (damage + capex)", fontsize=9)
    ax1.set_title("Annual cost over time — lumpy adaptation capex",
                  fontsize=10, fontweight="bold", color=EDGE)
    ax1.annotate("capex ~40 cm", xy=(0.20, 0.42), xycoords="axes fraction",
                 fontsize=7, color="#444", ha="center")
    ax1.annotate("capex ~100 cm", xy=(0.55, 0.78), xycoords="axes fraction",
                 fontsize=7, color="#444", ha="center")
    ax1.legend(fontsize=7, loc="upper left", framealpha=0.9, ncol=2)
    ax1.grid(alpha=0.3, lw=0.5)

    # ---------- BOTTOM: damage function at YEAR_EVAL (Panel-F style) ----------
    names = list(SCEN.keys())
    xs = np.array([anchors_raw[n][0] for n in names])
    ys_raw = np.array([anchors_raw[n][1] for n in names])
    ys_sm = np.array([anchors_smooth[n][1] for n in names])
    order = np.argsort(xs)
    xs_o = xs[order]

    # Interpolate through the 5 scenario anchors (linear, like FrEDI brackets).
    grid = np.linspace(xs_o.min(), xs_o.max(), 400)
    ax2.plot(grid, np.interp(grid, xs_o, ys_raw[order]),
             color="#b2182b", lw=2.0, zorder=3, label="From pulse capex (wonky)")
    ax2.plot(grid, np.interp(grid, xs_o, ys_sm[order]),
             color="#333333", lw=1.8, ls=":", zorder=4, label="From smoothed cost")
    # Colored anchor dots, one per scenario (inherited from the top-panel lines):
    #   filled = raw (lumpy) cost anchor; open ring = smoothed-cost anchor.
    for n in names:
        sx, sy = anchors_raw[n]
        ax2.scatter([sx], [sy], color=SCEN[n]["color"], s=85,
                    edgecolor="white", linewidth=1.2, zorder=5)
        smx, smy = anchors_smooth[n]
        ax2.scatter([smx], [smy], facecolor="white", edgecolor=SCEN[n]["color"],
                    s=70, linewidth=1.6, zorder=5)
    for thr in (T1_CM, T2_CM):
        ax2.axvline(thr, color="#bbb", lw=0.8, ls="--", zorder=1)

    ax2.set_xlim(0, xs_o.max() * 1.02)
    ax2.set_ylim(bottom=0)
    ax2.set_xlabel(f"Sea-level rise at {YEAR_EVAL} (cm)", fontsize=9)
    ax2.set_ylabel(f"Annual cost at {YEAR_EVAL}", fontsize=9)
    ax2.set_title("Implied damage function — cost vs SLR",
                  fontsize=10, fontweight="bold", color=EDGE)
    ax2.annotate("filled = lumpy-capex anchor;  open ring = smoothed anchor.\n"
                 "Mid-capex scenario pops the curve non-monotonic.",
                 xy=(0.97, 0.06), xycoords="axes fraction", fontsize=6.8,
                 color="#b2182b", ha="right", va="bottom")
    ax2.legend(fontsize=7.5, loc="upper left", framealpha=0.9)
    ax2.grid(alpha=0.3, lw=0.5)

    fig.tight_layout(pad=0.6)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"G_adaptation_damage_concept.{ext}", dpi=300,
                    bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'G_adaptation_damage_concept'}.{{png,pdf}}")
    print("  anchors at", YEAR_EVAL, "(SLR cm, raw cost, smoothed cost):")
    for n in names:
        print(f"    {n:8s}: SLR={anchors_raw[n][0]:6.1f}  raw={anchors_raw[n][1]:6.2f}"
              f"  smooth={anchors_smooth[n][1]:6.2f}")


if __name__ == "__main__":
    main()
