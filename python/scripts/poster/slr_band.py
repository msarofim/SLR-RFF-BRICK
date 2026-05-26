"""
slr_band.py
===========

Render the Wong-importance-weighted SLR percentile-band figure for the
poster's global-uncertainty panel. Uses the LHS-10k conditional-BRICK
baseline ensemble (10,000 LHS triplets × 451 yearly columns 1850-2300,
ESS ~ 7,000 under Wong importance weighting).

Replaces the earlier 500-cell paired ensemble; the percentiles agree to
within ~1-2 cm at every horizon, but the LHS-10k gives much smoother tails
and resolves the AIS-tipping fat tail more reliably.

Plot truncated to 2150 per project standard. Full 2300 data left in the
underlying CSV for SC-GHG NPV use.

Output:
  outputs/poster/slr_band.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

# v1.4.5 slim baseline (post-PR#93 BRICK + FaIR v1.4.5 + Wong-weighting).
SLR_CSV = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_baseline_to2300_weighted.csv"
OBS_GMSL_CSV = ROOT / "data" / "observations" / "nasa_gmsl_annual.csv"
PLOT_END = 2150

# AR6-style bias correction: rebaseline each draw at its own recent decadal
# GMSL mean, then shift to the observed satellite-altimetry value over the
# same period.  The cube stores SLR as cm rel year 2000.  Observed anchor is
# read from NOAA STAR satellite altimetry (data/observations/nasa_gmsl_annual.csv,
# units mm rel ~1993): mean over RECENT_BASELINE minus value at year 2000.
# Same framing as the substack GMST figures (AR6 projection convention).
RECENT_BASELINE              = (2015, 2024)
OBS_GMSL_RECENT_REL_2000_FBK = 6.38   # cm; fallback if obs file missing
                                       #  (computed 2026-05-18 from NOAA STAR)

# AR6 Table 9.9 GMSL projections by SSP scenario (Fox-Kemper et al. 2021).
# Values are MEDIAN [LIKELY 17-83% range] in METERS relative to 1995-2014.
# We use SSP2-4.5 and SSP3-7.0 as bracket for RFF-SP central emissions (the
# RFF-SP median CO2 emissions at 2100 sit between these two scenarios; AR6
# did not publish SSP4-6.0 through the FACTS pipeline so no Tier-2 value is
# available).
AR6_TABLE99_M_REL_1995_2014 = {
    "SSP2-4.5": {2050: 0.20, 2100: 0.56, 2150: 0.92},
    "SSP3-7.0": {2050: 0.22, 2100: 0.68, 2150: 1.19},
}
AR6_BASELINE = (1995, 2014)


def observed_gmsl_recent_rel_2000(obs_csv: Path, recent: tuple[int, int]) -> tuple[float, str]:
    """Return (cm, source_label).  Reads NOAA STAR (mm) and converts to
    cm rel year 2000.  Falls back to the documented constant if unreadable."""
    if not obs_csv.exists():
        return OBS_GMSL_RECENT_REL_2000_FBK, (
            f"NOAA STAR satellite altimetry {recent[0]}-{recent[1]} mean ≈ "
            f"+{OBS_GMSL_RECENT_REL_2000_FBK:.2f} cm rel 2000 (literature fallback)")
    obs = pd.read_csv(obs_csv)
    if not {"year", "value"}.issubset(obs.columns):
        return OBS_GMSL_RECENT_REL_2000_FBK, "literature fallback"
    m_2000 = obs.loc[obs.year == 2000, "value"]
    m_rec  = obs.loc[(obs.year >= recent[0]) & (obs.year <= recent[1]), "value"]
    if m_2000.empty or m_rec.empty:
        return OBS_GMSL_RECENT_REL_2000_FBK, "literature fallback (obs gaps)"
    val_cm = float((m_rec.mean() - m_2000.mean()) / 10.0)
    return val_cm, (f"NOAA STAR satellite altimetry, "
                    f"{recent[0]}-{recent[1]} mean rel 2000")


def weighted_quantile(values, weights, q):
    mask = np.isfinite(values) & np.isfinite(weights) & (weights >= 0)
    v = values[mask].astype(float)
    w = weights[mask].astype(float)
    if len(v) == 0 or w.sum() == 0:
        return np.nan
    s = np.argsort(v)
    v, w = v[s], w[s]
    cw = np.cumsum(w)
    return float(v[np.searchsorted(cw, q * cw[-1])])


def main():
    if not SLR_CSV.exists():
        raise SystemExit(f"Missing SLR CSV: {SLR_CSV}")
    df = pd.read_csv(SLR_CSV)
    year_cols = [c for c in df.columns if c.isdigit()]
    years = np.array([int(c) for c in year_cols])
    w = df["w_norm"].to_numpy()
    Y = df[year_cols].to_numpy()
    print(f"loaded {len(df)} draws, {len(years)} years ({years.min()}-{years.max()})")

    # AR6 bias correction: each draw rebaselined at its own RECENT_BASELINE
    # mean, then shifted to the observed satellite-altimetry value over the
    # same period (read from NOAA STAR if available, literature fallback else).
    rb_lo, rb_hi = RECENT_BASELINE
    obs_anchor, obs_src = observed_gmsl_recent_rel_2000(OBS_GMSL_CSV, RECENT_BASELINE)
    recent_mask = (years >= rb_lo) & (years <= rb_hi)
    traj_recent = Y[:, recent_mask].mean(axis=1)                # (n_draw,)
    Y           = Y - traj_recent[:, None] + obs_anchor
    print(f"AR6 bias-correction: rebaseline at {rb_lo}-{rb_hi} mean per draw, "
          f"shift to +{obs_anchor:.2f} cm rel 2000 ({obs_src})")

    mask = (years >= 2020) & (years <= PLOT_END)
    yrs_plot = years[mask]
    Y_plot = Y[:, mask]

    # Weighted quantiles per year
    qs = [0.05, 0.25, 0.50, 0.75, 0.95]
    bands = np.zeros((len(qs), len(yrs_plot)))
    for j in range(len(yrs_plot)):
        for k, q in enumerate(qs):
            bands[k, j] = weighted_quantile(Y_plot[:, j], w, q)

    weighted_mean = np.array([
        np.average(Y_plot[:, j], weights=w) for j in range(len(yrs_plot))
    ])

    # Plot
    fig, ax = plt.subplots(figsize=(9, 6))

    # 90% band
    ax.fill_between(yrs_plot, bands[0], bands[-1],
                    color="#1F4E79", alpha=0.18, label="5th–95th percentile")
    # 50% band
    ax.fill_between(yrs_plot, bands[1], bands[-2],
                    color="#1F4E79", alpha=0.35, label="25th–75th percentile")
    # Median
    ax.plot(yrs_plot, bands[2], color="#1F4E79", linewidth=2.6,
            label="Median (P50)")
    # Mean (importance-weighted, like every line on this plot; see Methods / Wong 2026)
    ax.plot(yrs_plot, weighted_mean, color="#A6361C", linewidth=2.0,
            linestyle="--", label="Mean")

    # Anchors for key years
    for y_anchor in (2050, 2100, 2150):
        if y_anchor in yrs_plot:
            j = int(np.where(yrs_plot == y_anchor)[0][0])
            m, lo, hi = bands[2, j], bands[0, j], bands[-1, j]
            ax.annotate(f"{y_anchor}:\n{m:.0f} cm  [{lo:.0f}–{hi:.0f}]",
                        xy=(y_anchor, m), xytext=(y_anchor - 8, m + 28),
                        fontsize=9, color="#1F4E79", fontweight="bold",
                        ha="left",
                        arrowprops=dict(arrowstyle="->", color="#1F4E79",
                                        lw=0.8))

    # NOAA STAR observed-anchor reference line + recent-baseline shaded span
    # were dropped 2026-05-25 per poster review; the bias-correction math
    # still uses NOAA STAR under the hood (rebaseline each draw at 2015-2024
    # then shift to obs anchor), but the on-figure dotted line and shaded
    # vertical span are removed to keep the panel focused on the projection
    # band and any AR6 SSP reference markers.

    # AR6 Table 9.9 reference markers (SSP2-4.5 and SSP3-7.0) at year 2100.
    # AR6 publishes values rel 1995-2014; our plot is rel 2000 (satellite
    # bias-corrected to 2015-2024). Convert by adding the NOAA STAR mean
    # over 1995-2014 expressed in cm rel 2000: that becomes the additive
    # offset between AR6's 1995-2014 zero and our 2000 zero.
    ar6_offset_cm = 0.0
    if OBS_GMSL_CSV.exists():
        obs = pd.read_csv(OBS_GMSL_CSV)
        m_2000 = obs.loc[obs.year == 2000, "value"]
        m_ar6  = obs.loc[(obs.year >= AR6_BASELINE[0]) & (obs.year <= AR6_BASELINE[1]),
                          "value"]
        if not m_2000.empty and not m_ar6.empty:
            ar6_offset_cm = float((m_ar6.mean() - m_2000.mean()) / 10.0)
    print(f"AR6→plot baseline shift: AR6 (rel {AR6_BASELINE[0]}–{AR6_BASELINE[1]}) is "
          f"{ar6_offset_cm:+.2f} cm rel 2000 in NOAA STAR — added to AR6 medians "
          f"before plotting.")
    for scenario, vals in AR6_TABLE99_M_REL_1995_2014.items():
        if 2100 in vals:
            y_ar6_cm = vals[2100] * 100.0 + ar6_offset_cm
            ax.plot([2100], [y_ar6_cm], marker="D", color="#888", markersize=8,
                    markeredgecolor="black", markeredgewidth=0.6, zorder=6,
                    label=f"AR6 {scenario} median 2100 ({y_ar6_cm:.0f} cm)")

    ax.set_xlim(2020, PLOT_END)
    ax.set_ylim(0, max(bands[-1, -1] * 1.1, 200))
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Global Mean Sea Level Rise (cm rel. 2000)\n"
                  "AR6-style bias-corrected", fontsize=12)
    # Internal title dropped per poster review (May 18): duplicates the
    # poster's panel-B label "B. PROBABILISTIC SLR".
    ax.grid(alpha=0.3, linewidth=0.5)
    ax.legend(loc="upper left", fontsize=10, framealpha=0.92)

    # The AR6 SSP2-4.5 reference line was previously overlaid on this plot;
    # moved to the figure caption text in the poster (per Marcus May 17).

    fig.tight_layout()
    fig.savefig(OUT / "slr_band.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "slr_band.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'slr_band.png'}")


if __name__ == "__main__":
    main()
