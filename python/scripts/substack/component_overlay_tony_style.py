"""
component_overlay_tony_style.py
================================

BRICK 5-component hindcast vs observations, comparing two driver paths:
  - obs_obs (IGCC):  obs GMST + obs OHC → BRICK
  - fair_fair:       FaIR GMST + FaIR OHC → BRICK (pure model)

Both runs use the post-PR#93 joint posterior. Plotting conventions follow
Wong et al. 2017 (BRICK calibration paper):
  - GMSL/GIS/GSIC/TE baselined to 1961-1990 mean; AIS on 1992-2001 mean
  - 17-83% (1σ-equivalent) band, not 5-95%
  - Obs error bars: Church & White 2011 (gmsl), Frederikse 2020 (GIS, steric),
    BRICK calibration set (GSIC, AIS-IMBIE), plus Dangendorf 2024 on the
    GMSL panel for an independent obs comparison

Inputs:
  outputs/brick_obsdriven_obs_obs_igcc_to2024.csv
  outputs/brick_obsdriven_fair_fair_to2024.csv
  ~/.julia/packages/MimiBRICK/bpCAF/data/calibration_data/all_calibration_data_combined.csv
  data/observations/raw/frederikse2020_global_basin_timeseries.xlsx
  data/observations/dangendorf_2024_gmsl.csv

Output:
  outputs/substack/component_overlay_tony_style.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
HOME = Path(os.path.expanduser("~"))
# Two BRICK obs-driven runs to overlay:
#   * obs_obs_igcc — obs GMST (IGCC) + obs OHC (IGCC) → BRICK
#   * fair_fair    — FaIR GMST + FaIR OHC → BRICK   (pure model run)
BRICK_OBS_CSV  = ROOT / "outputs/brick_obsdriven_obs_obs_igcc_to2024.csv"
BRICK_FAIR_CSV = ROOT / "outputs/brick_obsdriven_fair_fair_to2024.csv"
CALIB_CSV = HOME / ".julia/packages/MimiBRICK/bpCAF/data/calibration_data/all_calibration_data_combined.csv"
FRED_XLSX = ROOT / "data/observations/raw/frederikse2020_global_basin_timeseries.xlsx"
DANGEN_CSV = ROOT / "data/observations/dangendorf_2024_gmsl.csv"
OUT_DIR   = ROOT / "outputs/substack"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Colors for the two BRICK runs
COLOR_OBS  = "#1F4E79"   # obs_obs (blue, BRICK with observed inputs)
COLOR_FAIR = "#C04A00"   # fair_fair (orange-red, BRICK with FaIR model inputs)

HINDCAST_START, HINDCAST_END = 1850, 2020

PANEL_SPEC = [
    # (brick_prefix, panel_title,           baseline_window,    calib_col,           sigma_col,           ylabel)
    ("slr",  "Global mean sea level",       (1961, 1990),        "gmsl_obs",         "gmsl_sigma",         "Sea level (m)"),
    ("gis",  "Greenland ice sheet (GIS)",   (1961, 1990),        "merged_greenland_obs", "merged_greenland_sigma", "Sea level contribution (m)"),
    ("gsic", "Glaciers & small ice caps",   (1961, 1990),        "glaciers_obs",     "glaciers_sigma",     "Sea level contribution (m)"),
    ("ais",  "Antarctic ice sheet",         (1992, 2001),        "antarctic_imbie_obs", "antarctic_imbie_sigma", "Sea level contribution (m)"),
    ("te",   "Thermal expansion (TE)",      (1961, 1990),         None,                None,                "Sea level contribution (m)"),
    ("lws",  "Land water storage (LWS)",    (1961, 1990),         None,                None,                "Sea level contribution (m)"),
]

# Frederikse column name per BRICK component (mean / lower / upper for sigma).
# Plotted on AIS, GSIC, and LWS panels in PURPLE squares so it's visually
# distinct from the existing black-dot IMBIE-era/calib obs. Highlights the
# 20th-century AIS overshoot and GSIC undershoot — the two component biases
# that cancel to make BRICK's GMSL hindcast still match obs in spite of each
# component being mis-attributed. See `project_brick_component_biases_vs_frederikse`
# in memory for the quantitative breakdown.
FRED_COLNAMES = {
    "ais":  ("Antarctic Ice Sheet [mean]",     "Antarctic Ice Sheet [lower]",     "Antarctic Ice Sheet [upper]"),
    "gsic": ("Glaciers [mean]",                "Glaciers [lower]",                "Glaciers [upper]"),
    "lws":  ("Terrestrial Water Storage [mean]","Terrestrial Water Storage [lower]","Terrestrial Water Storage [upper]"),
}
FRED_COLOR = "#4B0082"   # same purple as Dangendorf marker for visual consistency

BAND_LOW_Q  = 0.17
BAND_HIGH_Q = 0.83


def rebaseline_brick_to_window(brick_df: pd.DataFrame, prefix: str,
                                beg_year: int, end_year: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Returns (years, median, p17, p83) in meters, rebaselined so each
    ensemble member has zero mean over [beg_year, end_year]."""
    years_in_df = sorted(int(c.split("_")[-1])
                         for c in brick_df.columns
                         if c.startswith(prefix + "_") and c[len(prefix)+1:].isdigit())
    cols = [f"{prefix}_{y}" for y in years_in_df]
    arr_cm = brick_df[cols].to_numpy()  # cm rel year 2000
    arr_m = arr_cm / 100.0
    years = np.array(years_in_df)
    mask = (years >= beg_year) & (years <= end_year)
    row_means = arr_m[:, mask].mean(axis=1, keepdims=True)
    arr_norm = arr_m - row_means
    med = np.median(arr_norm, axis=0)
    p17 = np.percentile(arr_norm, BAND_LOW_Q * 100, axis=0)
    p83 = np.percentile(arr_norm, BAND_HIGH_Q * 100, axis=0)
    return years, med, p17, p83


def load_dangendorf_gmsl(beg: int = 1961, end: int = 1990
                          ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Dangendorf 2024 GMSL (mm) rebaselined to [beg, end] mean, returning
    (years, value_m, sigma_m). The CSV's value column is in mm rel
    Dangendorf's own baseline; we re-center to match Tony's 1961-1990
    convention and convert mm → m."""
    df = pd.read_csv(DANGEN_CSV)
    years = df.year.to_numpy()
    val = df.value.to_numpy() / 1000.0   # mm → m
    sig = df.sigma.to_numpy() / 1000.0   # mm → m
    mask = (years >= beg) & (years <= end)
    if mask.any():
        val = val - val[mask].mean()
    return years, val, sig


def load_frederikse_gis_replacement(beg: int = 1961, end: int = 1990) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Mirror Tony's GIS-replacement: Frederikse Greenland Ice Sheet [mean],
    normalized to 1961-1990; sigma = (upper-lower)/4 (treating upper-lower
    as ~95% CI)."""
    df = pd.read_excel(FRED_XLSX, sheet_name="Global").rename(columns={"Unnamed: 0": "year"}).set_index("year")
    years = df.index.to_numpy()
    gis_m   = df["Greenland Ice Sheet [mean]"]  / 1000.0  # mm -> m
    gis_lo  = df["Greenland Ice Sheet [lower]"] / 1000.0
    gis_up  = df["Greenland Ice Sheet [upper]"] / 1000.0
    norm = gis_m.loc[beg:end].mean()
    gis_m   = gis_m   - norm
    gis_lo  = gis_lo  - norm
    gis_up  = gis_up  - norm
    gis_sigma = (gis_up - gis_lo) / 4.0
    return years, gis_m.to_numpy(), gis_sigma.to_numpy()


def load_frederikse_overlay(mean_col: str, lo_col: str, up_col: str,
                             beg: int, end: int
                             ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generic Frederikse 2020 overlay loader: returns (years, value_m, sigma_m)
    rebaselined so mean of [beg, end] = 0; sigma = (upper-lower)/4 (~95% CI)."""
    df = pd.read_excel(FRED_XLSX, sheet_name="Global").rename(columns={"Unnamed: 0": "year"}).set_index("year")
    years = df.index.to_numpy()
    mean_m = df[mean_col] / 1000.0
    lo_m   = df[lo_col]   / 1000.0
    up_m   = df[up_col]   / 1000.0
    norm = mean_m.loc[beg:end].mean()
    mean_m = mean_m - norm
    lo_m   = lo_m   - norm
    up_m   = up_m   - norm
    sigma = (up_m - lo_m) / 4.0
    return years, mean_m.to_numpy(), sigma.to_numpy()


def main() -> None:
    print(f"Loading BRICK obs_obs CSV:  {BRICK_OBS_CSV.name}")
    brick_obs = pd.read_csv(BRICK_OBS_CSV)
    print(f"  rows: {len(brick_obs)}")

    print(f"Loading BRICK fair_fair CSV: {BRICK_FAIR_CSV.name}")
    brick_fair = pd.read_csv(BRICK_FAIR_CSV)
    print(f"  rows: {len(brick_fair)}")

    print(f"Loading calibration data: {CALIB_CSV.name}")
    calib = pd.read_csv(CALIB_CSV, na_values="NA")
    print(f"  rows: {len(calib)}, years {calib.year.min()}-{calib.year.max()}")

    print("Loading Dangendorf 2024 GMSL ...")
    dan_yrs, dan_val, dan_sig = load_dangendorf_gmsl(1961, 1990)
    print(f"  Dangendorf years: {dan_yrs.min()}-{dan_yrs.max()} (rebaselined to 1961-1990)")

    print("Loading Frederikse GIS replacement (per Tony's notebook)...")
    fred_yrs, fred_gis, fred_gis_sigma = load_frederikse_gis_replacement(1961, 1990)
    # Replace the merged_greenland columns in calib with Frederikse
    calib = calib.drop(columns=["merged_greenland_obs", "merged_greenland_sigma"])
    fred_df = pd.DataFrame({
        "year": fred_yrs,
        "merged_greenland_obs": fred_gis,
        "merged_greenland_sigma": fred_gis_sigma,
    })
    calib = calib.merge(fred_df, on="year", how="left")

    # Build figure. Drop constrained_layout in favor of manual tight_layout
    # with explicit rect padding for the 2-line suptitle.
    n_panels = len(PANEL_SPEC)
    fig, axes = plt.subplots(nrows=n_panels, ncols=1, figsize=(9.5, 2.4*n_panels + 0.6),
                              sharex=True)
    if n_panels == 1:
        axes = [axes]

    for ax, (prefix, title, (beg, end), obs_col, sig_col, ylabel) in zip(axes, PANEL_SPEC):
        # Plot BOTH BRICK runs (obs_obs in blue + fair_fair in orange)
        for brick_df, color, run_label in [
            (brick_obs,  COLOR_OBS,  "obs_obs (IGCC)"),
            (brick_fair, COLOR_FAIR, "fair_fair (FaIR→BRICK)"),
        ]:
            years, med, p17, p83 = rebaseline_brick_to_window(brick_df, prefix, beg, end)
            m = (years >= HINDCAST_START) & (years <= HINDCAST_END)
            ax.fill_between(years[m], p17[m], p83[m],
                            color=color, alpha=0.22, linewidth=0,
                            label=f"BRICK 17-83% — {run_label}")
            ax.plot(years[m], med[m], color=color, lw=2.0,
                    label=f"BRICK median — {run_label}")

        # Obs overlay (if any)
        if obs_col is not None and obs_col in calib.columns:
            obs_df = calib.dropna(subset=[obs_col])
            obs_df = obs_df[(obs_df.year >= HINDCAST_START) & (obs_df.year <= HINDCAST_END)]
            sig = obs_df[sig_col] if (sig_col is not None and sig_col in calib.columns) else None
            obs_label = ("Church & White 2011" if prefix == "slr"
                         else f"obs ({obs_col})")
            ax.errorbar(obs_df.year, obs_df[obs_col],
                        yerr=sig, fmt="k.", markersize=2.5,
                        elinewidth=0.5, capsize=0, alpha=0.7,
                        label=obs_label)
            # On the GMSL panel only, also overlay Dangendorf 2024
            if prefix == "slr":
                dan_m = (dan_yrs >= HINDCAST_START) & (dan_yrs <= HINDCAST_END)
                ax.errorbar(dan_yrs[dan_m], dan_val[dan_m],
                            yerr=dan_sig[dan_m],
                            fmt="s", color="#4B0082", markersize=2.5,
                            markerfacecolor="#4B0082", markeredgecolor="#4B0082",
                            elinewidth=0.5, capsize=0, alpha=0.7,
                            label="Dangendorf 2024")
        elif prefix == "te":
            # No TE obs in calibration data (only trends per Tony's note).
            # Overlay Frederikse Steric for visual context.
            fred_yrs_te, fred_te, fred_te_sigma = load_frederikse_overlay(
                "Steric [mean]", "Steric [lower]", "Steric [upper]", beg, end)
            sm = (fred_yrs_te >= HINDCAST_START) & (fred_yrs_te <= HINDCAST_END)
            ax.errorbar(fred_yrs_te[sm], fred_te[sm],
                        yerr=fred_te_sigma[sm],
                        fmt="k.", markersize=2.5, elinewidth=0.5, capsize=0,
                        alpha=0.7, label="Frederikse 2020 Steric (no obs in calib data)")

        # Frederikse 2020 overlay (purple squares) on AIS, GSIC, and LWS — these
        # are the panels where pre-1990 obs are either absent (calib data
        # antarctic_imbie_obs starts 1992) or BRICK is zero-by-design (LWS).
        # Plotting Frederikse 1900-2018 here makes the component-level biases
        # visible: AIS over-melts, GSIC under-melts, and BRICK has no LWS
        # contribution in the hindcast.
        if prefix in FRED_COLNAMES:
            mean_col, lo_col, up_col = FRED_COLNAMES[prefix]
            fred_yrs, fred_val, fred_sig = load_frederikse_overlay(
                mean_col, lo_col, up_col, beg, end)
            fm = (fred_yrs >= HINDCAST_START) & (fred_yrs <= HINDCAST_END)
            label = ("Frederikse 2020 (Terr. Water Storage)"
                     if prefix == "lws"
                     else "Frederikse 2020")
            ax.errorbar(fred_yrs[fm], fred_val[fm], yerr=fred_sig[fm],
                        fmt="s", color=FRED_COLOR, markersize=2.5,
                        markerfacecolor=FRED_COLOR, markeredgecolor=FRED_COLOR,
                        elinewidth=0.5, capsize=0, alpha=0.7,
                        label=label)

        ax.set_title(f"{title}  (rebaselined to {beg}-{end})", fontsize=10,
                     fontweight="bold", color="#1A1A1A")
        ax.set_ylabel(ylabel, fontsize=9)
        ax.axhline(0, color="grey", linewidth=0.5)
        ax.grid(alpha=0.3, linewidth=0.4)
        ax.legend(loc="upper left", fontsize=7.5, framealpha=0.92, ncol=2)

    axes[-1].set_xlim(HINDCAST_START, HINDCAST_END)
    axes[-1].set_xlabel("Year", fontsize=10)

    # Reserve top space for the title; caption sits at the bottom.
    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.suptitle(
        "BRICK hindcast: sea-level components",
        fontsize=14, fontweight="bold", color="#1A1A1A", y=0.98)
    # Caption (assumptions / methods) at the bottom of the figure
    fig.text(
        0.5, 0.01,
        "Post-PR#93 joint posterior; obs-driven runs with IGCC GMST + IGCC OHC, "
        "and FaIR-driven runs with FaIR GMST + FaIR OHC.  "
        "Bands are 17-83 % across the importance-weighted posterior; lines are medians.  "
        "Baselines: 1961-1990 mean (GMSL, GIS, GSIC, TE) and 1992-2001 mean (AIS), per "
        "Wong et al. 2017.",
        ha="center", va="bottom", fontsize=9.0, color="#444444",
        style="italic", wrap=True)

    out_png = OUT_DIR / "component_overlay_tony_style.png"
    out_pdf = OUT_DIR / "component_overlay_tony_style.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")
    print(f"wrote {out_pdf}")

    # Diagnostic table at landmark years (for each BRICK run). Now includes
    # LWS so the BRICK-zero-by-design convention is visible in the printed
    # diagnostics, not just the figure panel.
    for run_name, brick_df in [("obs_obs (IGCC)", brick_obs),
                               ("fair_fair", brick_fair)]:
        print(f"\nBRICK {run_name} (m, rebaselined to Tony conventions):")
        print(f'{"year":>6}  {"AIS(1992-01)":>14}  {"GIS(61-90)":>14}  '
              f'{"GSIC(61-90)":>14}  {"TE(61-90)":>14}  '
              f'{"LWS(61-90)":>14}  {"Total(61-90)":>14}')
        for y in (1850, 1900, 1950, 1990, 2000, 2018, 2020):
            row = [str(y)]
            for prefix, _, (beg, end), _, _, _ in PANEL_SPEC:
                years, med, _, _ = rebaseline_brick_to_window(brick_df, prefix, beg, end)
                if y in years:
                    i = list(years).index(y)
                    row.append(f"{med[i]:>+14.4f}")
                else:
                    row.append("-".rjust(14))
            # PANEL_SPEC order is slr, gis, gsic, ais, te, lws
            slr_v, gis_v, gsic_v, ais_v, te_v, lws_v = (
                row[1], row[2], row[3], row[4], row[5], row[6])
            print(f"{y:>6d}  {ais_v}  {gis_v}  {gsic_v}  {te_v}  {lws_v}  {slr_v}")


if __name__ == "__main__":
    main()
