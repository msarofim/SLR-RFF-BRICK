"""
fair_vs_obs_gmst_ohc.py

Two-panel validation figure: FaIR ensemble-mean GMST and OHC vs the leading
observational products.

  Top panel — GMST (°C, rel 1850-1900):
    - FaIR ensemble-mean
    - IGCC 2024 4-dataset annual mean (HadCRUT5, NOAA, Berkeley, Kadow)
    - Berkeley Earth annual ± sigma

  Bottom panel — OHC (10^22 J, rel 1871-1900):
    - FaIR ensemble-mean
    - Zanna 2019 + IGCC 2024 splice  (Zanna 1870-1980, IGCC/Palmer-vS 1981-2024)
      Zanna is the only OHC product extending back to 1900; IGCC is what FaIR
      calibrates to in the modern period; together they span 1900-2024 with
      a single physically-consistent dataset.

The OHC baseline is 1871-1900 (Zanna real-obs era) instead of 1850-1900
to avoid the 1850-1869 portion of the obs splice file, which is filled
from a FaIR-ensemble-mean anchor and would artificially align FaIR with
obs there.

IGCC source note: we use `igcc2024_gmst_4dataset_mean.csv` (the observed
annual mean across HadCRUT5/NOAA/Berkeley/Kadow), NOT
`igcc2024_gmst_with_uncertainty.csv` (the smoothed anthropogenic-warming
trend with forcing/feedback decomposition).  The annual mean is the
right comparator for year-by-year FaIR vs obs validation.

Output:
    outputs/substack/fair_vs_obs_gmst_ohc.{png,pdf}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT  = Path(__file__).resolve().parents[3]
DATA  = ROOT / "data" / "observations"
OUT   = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

FAIR_GMST = DATA / "fair_mean_gmst_v145.csv"        # v1.4.5 (Smith 2024 + RFF-SP)
FAIR_OHC  = DATA / "fair_mean_ohc_v145.csv"
IGCC_GMST = DATA / "igcc2024_gmst_4dataset_mean.csv"
BE_GMST   = DATA / "berkeley_earth_annual.csv"
OHC_IGCC  = DATA / "ohc_spliced_zanna_igcc.csv"
# Gouretski 2007 OHC — BRICK's calibration target. Lives in the MimiBRICK package.
OHC_GOURETSKI = Path(
    "/Users/MarcusMarcus/.julia/packages/MimiBRICK/bpCAF/data/"
    "calibration_data/ocean_heat_gouretski_3000m.csv"
)

PLOT_START, PLOT_END = 1850, 2024
GMST_BASE = (1850, 1900)         # IPCC standard; all GMST products cover it
OHC_BASE  = (1981, 1996)         # common to FaIR, Gouretski (1953-1996), and IGCC (1981-2024)
IGCC_OHC_START = 1981            # drop the Zanna portion of the splice (pre-1955 reconstruction
                                 # noise; the dramatic 1900-1915 dip is order-of-magnitude larger
                                 # than what modern volcanic-OHC literature supports)

# Colors
COLOR_FAIR      = "#C04A00"
COLOR_IGCC      = "#1F4E79"
COLOR_BE        = "#5C8A8A"
COLOR_GOURETSKI = "#7E3F00"


def rebaseline(years: np.ndarray, vals: np.ndarray, beg: int, end: int) -> np.ndarray:
    mask = (years >= beg) & (years <= end)
    if not mask.any():
        raise ValueError(f"No data in baseline window [{beg}, {end}]")
    return vals - float(vals[mask].mean())


def load_fair_gmst() -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(FAIR_GMST)
    return df.year.to_numpy(), df.gmst_C.to_numpy()


def load_fair_ohc() -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(FAIR_OHC)
    return df.year.to_numpy(), df.ohc_1e22J.to_numpy()


def load_igcc_gmst():
    """IGCC 4-dataset annual mean (observed; not the anthropogenic trend).
    The CSV has time = year + 0.5 with timebound_lower = the actual year.
    Returns (years, gmst). IGCC is already rel 1850-1900."""
    df = pd.read_csv(IGCC_GMST)
    yrs = df.timebound_lower.to_numpy().astype(int)   # actual calendar year
    val = df.GMST.to_numpy()
    return yrs, val


def load_berkeley():
    df = pd.read_csv(BE_GMST)
    return df.year.to_numpy(), df.value.to_numpy(), df.sigma.to_numpy()


def load_ohc_obs(path: Path) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path, comment="#")
    return df.year.to_numpy(), df.ohc_1e22J.to_numpy()


def load_gouretski_ohc() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Gouretski 2007 OHC (1953-1996; what BRICK was calibrated against).
    File: 3 prefatory lines (citation, blank, units row) then header
    `year,heat_anomaly,std_dev` then data."""
    df = pd.read_csv(OHC_GOURETSKI, skiprows=3)
    return (df.year.to_numpy().astype(int),
            df.heat_anomaly.to_numpy(),
            df.std_dev.to_numpy())


def main():
    # ── Load all sources ────────────────────────────────────────────────────
    print("Loading FaIR mean GMST + OHC ...")
    fair_g_yrs, fair_g_raw = load_fair_gmst()
    fair_o_yrs, fair_o_raw = load_fair_ohc()

    print("Loading IGCC GMST (4-dataset annual mean) ...")
    igcc_yrs, igcc_val = load_igcc_gmst()

    print("Loading Berkeley Earth GMST ...")
    be_yrs, be_val, be_sig = load_berkeley()

    print("Loading IGCC OHC (modern portion only; pre-1955 Zanna dropped) ...")
    _yrs, _vals = load_ohc_obs(OHC_IGCC)
    keep = _yrs >= IGCC_OHC_START
    igcc_o_yrs, igcc_o_raw = _yrs[keep], _vals[keep]
    print(f"  IGCC OHC: {igcc_o_yrs[0]}–{igcc_o_yrs[-1]}, {len(igcc_o_yrs)} years")

    print("Loading Gouretski 2007 OHC (BRICK calibration target) ...")
    g_yrs, g_val, g_sig = load_gouretski_ohc()

    # ── Rebaseline everything to common windows ─────────────────────────────
    # GMST → 1850-1900 (IGCC's native anchor; FaIR and Berkeley re-anchored)
    fair_g = rebaseline(fair_g_yrs, fair_g_raw, *GMST_BASE)
    be_anom = rebaseline(be_yrs, be_val, *GMST_BASE)
    # IGCC 4-dataset mean is already rel 1850-1900 (re-anchor anyway to be sure)
    igcc_anom = rebaseline(igcc_yrs, igcc_val, *GMST_BASE)

    # OHC → 1961-1990 (common to all three OHC products: FaIR, Zanna+IGCC,
    # Gouretski). Standard Wong et al. 2017 climate baseline.
    fair_o = rebaseline(fair_o_yrs, fair_o_raw, *OHC_BASE)
    igcc_o = rebaseline(igcc_o_yrs, igcc_o_raw, *OHC_BASE)
    g_o    = rebaseline(g_yrs, g_val, *OHC_BASE)

    # ── Plot ────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True)

    # Top panel: GMST
    ax = axes[0]
    # IGCC 4-dataset mean (annual)
    m = (igcc_yrs >= PLOT_START) & (igcc_yrs <= PLOT_END)
    ax.plot(igcc_yrs[m], igcc_anom[m], color=COLOR_IGCC, lw=2.0,
            label="IGCC 2024 (4-dataset annual mean)")
    # Berkeley Earth
    m = (be_yrs >= PLOT_START) & (be_yrs <= PLOT_END)
    ax.errorbar(be_yrs[m], be_anom[m], yerr=be_sig[m],
                fmt="o", color=COLOR_BE, markersize=2.0, elinewidth=0.4,
                capsize=0, alpha=0.55, label="Berkeley Earth annual ± σ")
    # FaIR mean
    m = (fair_g_yrs >= PLOT_START) & (fair_g_yrs <= PLOT_END)
    ax.plot(fair_g_yrs[m], fair_g[m], color=COLOR_FAIR, lw=2.4,
            label="FaIR v1.4.5 ensemble-mean")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_title("Global mean surface temperature  (rebaselined to 1850-1900)",
                 fontsize=11.5, fontweight="bold", color="#1A1A1A")
    ax.set_ylabel("GMST anomaly (°C)", fontsize=10)
    ax.grid(alpha=0.30, linewidth=0.5)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.92)

    # Bottom panel: OHC — IGCC + Gouretski + FaIR (Zanna pre-1955 dropped)
    ax = axes[1]
    # IGCC modern OHC (1981-2024) — FaIR's calibration target
    m = (igcc_o_yrs >= PLOT_START) & (igcc_o_yrs <= PLOT_END)
    ax.plot(igcc_o_yrs[m], igcc_o[m], color=COLOR_IGCC, lw=2.0,
            label="IGCC 2024 / Palmer-vS  (FaIR calibration target, 1981-2024)")
    # Gouretski 2007 (1953-1996) — BRICK's calibration target
    m = (g_yrs >= PLOT_START) & (g_yrs <= PLOT_END)
    ax.errorbar(g_yrs[m], g_o[m], yerr=g_sig[m],
                fmt="s", color=COLOR_GOURETSKI, markersize=3.0,
                markerfacecolor=COLOR_GOURETSKI, markeredgecolor=COLOR_GOURETSKI,
                elinewidth=0.5, capsize=0, alpha=0.75,
                label="Gouretski 2007 ± σ  (BRICK calibration target, 1953-1996)")
    # FaIR mean
    m = (fair_o_yrs >= PLOT_START) & (fair_o_yrs <= PLOT_END)
    ax.plot(fair_o_yrs[m], fair_o[m], color=COLOR_FAIR, lw=2.4,
            label="FaIR v1.4.5 ensemble-mean")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_title(f"Ocean heat content  (rebaselined to {OHC_BASE[0]}-{OHC_BASE[1]} mean)",
                 fontsize=11.5, fontweight="bold", color="#1A1A1A")
    ax.set_ylabel("OHC anomaly (10$^{22}$ J)", fontsize=10)
    ax.set_xlabel("Year", fontsize=10)
    ax.grid(alpha=0.30, linewidth=0.5)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.92)
    ax.set_xlim(PLOT_START, PLOT_END)

    # Title block — simple title + caption beneath
    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.suptitle("FaIR ensemble-mean vs observations: GMST and OHC",
                 fontsize=14, fontweight="bold", color="#1A1A1A", y=0.98)
    fig.text(
        0.5, 0.01,
        "FaIR: v1.4.5 841-config posterior with Smith 2024 historical emissions + RFF-SP central draw, "
        "ensemble-mean across 10,000 LHS cells.  "
        "GMST obs: IGCC 2024 (annual mean across HadCRUT5 / NOAA / Berkeley / Kadow) and Berkeley Earth annual.  "
        "OHC obs: IGCC 2024 / Palmer-vS (1981-2024; FaIR's modern calibration target) and Gouretski 2007 "
        "(1953-1996; BRICK's calibration target).  "
        "Baselines: GMST 1850-1900 (IPCC standard); OHC 1981-1996 (common to all three OHC products).",
        ha="center", va="bottom", fontsize=8.0, color="#444444",
        style="italic", wrap=True)

    out_png = OUT / "fair_vs_obs_gmst_ohc.png"
    out_pdf = OUT / "fair_vs_obs_gmst_ohc.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")
    print(f"wrote {out_pdf}")

    # Diagnostic: 2024 endpoint values
    def at_year(yrs, vals, target):
        ix = np.where(yrs == target)[0]
        return float(vals[ix[0]]) if len(ix) else float("nan")

    print(f"\n=== 2024 endpoints ===")
    print(f"  GMST (°C rel 1850-1900):")
    print(f"    FaIR v1.4.5:    {at_year(fair_g_yrs, fair_g, 2024):+.3f}")
    print(f"    IGCC 4ds mean:  {at_year(igcc_yrs, igcc_anom, 2024):+.3f}")
    print(f"    Berkeley:       {at_year(be_yrs, be_anom, 2024):+.3f}")
    print(f"  OHC (10^22 J rel {OHC_BASE[0]}-{OHC_BASE[1]}):")
    print(f"    FaIR v1.4.5:    {at_year(fair_o_yrs, fair_o, 2024):+.2f}")
    print(f"    IGCC 2024:      {at_year(igcc_o_yrs, igcc_o, 2024):+.2f}")
    print(f"    Gouretski @1996: {at_year(g_yrs, g_o, 1996):+.2f}  "
          f"(for comparison vs IGCC @1996: "
          f"{at_year(igcc_o_yrs, igcc_o, 1996):+.2f}, "
          f"FaIR v1.4.5 @1996: {at_year(fair_o_yrs, fair_o, 1996):+.2f})")


if __name__ == "__main__":
    main()
