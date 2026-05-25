"""
component_overlay_tony_style_extended.py
========================================

Extends ``component_overlay_tony_style.py`` to overlay THREE BRICK
configurations on each panel using Tony Wong's plotting conventions
(1961-1990 baseline for everything except AIS, which uses 1992-2001;
17-83% bands rather than 5-95%; errorbar style for observations):

  - obs_obs   (IGCC 4-dataset mean GMST + Zanna+IGCC OHC splice)  → maroon
  - fair_fair (FaIR ensemble-mean GMST + OHC)                      → navy
  - SNEASY-BRICK (canned SNEASY MAP RCP45 GMST + OHC, equivalent
    to Tony-mode `test_sneasy_posterior.jl` — verified bit-identical
    in `project_brick_override_is_bitidentical.md`)                → dark green

GMSL panel adds Dangendorf 2024 and Church & White 2011 obs alongside the
calibration-target gmsl_obs (Tony's notebook only shows the calibration
target). Component panels keep Tony's calibration-data overlays + Frederikse
GIS replacement.

This is the diagnostic figure for the "FaIR-BRICK TE undershoot" question.
Three BRICK lines + obs let the reader see at a glance:

  - How much of the FaIR vs Tony-mode TE gap is endpoint-noise on raw SNEASY
    (visible as the offset between the SNEASY-BRICK and fair_fair medians at
    1900 and 2018, given the 1961-1990 baseline).
  - Where in the trajectory the BRICK lines diverge from each other and from
    obs (the GIS trajectory-shape effect on Greenland, the OHC trajectory
    effect on TE).

Inputs:
  outputs/brick_obsdriven_obs_obs_igcc_to2024.csv     (IGCC GMST + Zanna+IGCC OHC)
  outputs/brick_obsdriven_fair_fair_to2024.csv        (FaIR-mean GMST + FaIR-mean OHC)
  outputs/brick_obsdriven_sneasyMAP_override_to2024.csv (SNEASY MAP GMST + OHC; Tony-mode)
  ~/.julia/packages/MimiBRICK/bpCAF/data/calibration_data/all_calibration_data_combined.csv
  data/observations/raw/frederikse2020_global_basin_timeseries.xlsx
  data/calibration/CSIRO_Recons_gmsl_yr_2015.csv
  data/observations/dangendorf_2024_gmsl.csv

Output:
  outputs/substack/component_overlay_tony_style_extended.{png,pdf}
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

# Three BRICK runs to overlay. Order matters for legend order.
BRICK_RUNS = [
    ("sneasy_brick",
     "SNEASY-BRICK (SNEASY MAP GMST + OHC; ≡ Tony-mode)",
     "#1B7837",                                            # dark green
     ROOT / "outputs/brick_obsdriven_sneasyMAP_override_to2024.csv"),
    ("fair_fair",
     "FaIR-BRICK (FaIR-mean GMST + FaIR-mean OHC)",
     "#1F4E79",                                            # navy
     ROOT / "outputs/brick_obsdriven_fair_fair_to2024.csv"),
    ("obs_obs",
     "obs-BRICK (IGCC GMST + Zanna+IGCC OHC)",
     "#A6361C",                                            # maroon
     ROOT / "outputs/brick_obsdriven_obs_obs_igcc_to2024.csv"),
]

CALIB_CSV = HOME / ".julia/packages/MimiBRICK/bpCAF/data/calibration_data/all_calibration_data_combined.csv"
FRED_XLSX = ROOT / "data/observations/raw/frederikse2020_global_basin_timeseries.xlsx"
CW_CSV    = ROOT / "data/calibration/CSIRO_Recons_gmsl_yr_2015.csv"
DANG_CSV  = ROOT / "data/observations/dangendorf_2024_gmsl.csv"
OUT_DIR   = ROOT / "outputs/substack"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HINDCAST_START, HINDCAST_END = 1850, 2024

# Tony's baselines and panel labels. Order = top-down on the figure.
PANEL_SPEC = [
    # (brick_prefix, panel_title,                  baseline_window,  calib_obs_col,          calib_sigma_col,           ylabel)
    ("slr",  "Global mean sea level",              (1961, 1990),     "gmsl_obs",             "gmsl_sigma",              "Sea level (m)"),
    ("gis",  "Greenland ice sheet (GIS)",          (1961, 1990),     "merged_greenland_obs", "merged_greenland_sigma",  "Sea level contribution (m)"),
    ("gsic", "Glaciers & small ice caps",          (1961, 1990),     "glaciers_obs",         "glaciers_sigma",          "Sea level contribution (m)"),
    ("ais",  "Antarctic ice sheet",                (1992, 2001),     "antarctic_imbie_obs",  "antarctic_imbie_sigma",   "Sea level contribution (m)"),
    ("te",   "Thermal expansion (TE)",             (1961, 1990),     None,                   None,                      "Sea level contribution (m)"),
]

BAND_LOW_Q  = 0.17
BAND_HIGH_Q = 0.83


def rebaseline_brick_to_window(brick_df: pd.DataFrame, prefix: str,
                               beg_year: int, end_year: int
                               ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Rebaseline each ensemble row so its mean over [beg, end] = 0.

    Returns (years, median, p17, p83) in METERS.
    """
    years_in_df = sorted(int(c.split("_")[-1])
                         for c in brick_df.columns
                         if c.startswith(prefix + "_") and c[len(prefix) + 1:].isdigit())
    cols = [f"{prefix}_{y}" for y in years_in_df]
    arr_m = brick_df[cols].to_numpy() / 100.0   # cm rel year 2000 → m
    years = np.array(years_in_df)
    mask = (years >= beg_year) & (years <= end_year)
    if not mask.any():
        raise RuntimeError(f"baseline window {beg_year}-{end_year} outside {prefix} year span "
                           f"{years_in_df[0]}-{years_in_df[-1]}")
    row_means = arr_m[:, mask].mean(axis=1, keepdims=True)
    arr_norm = arr_m - row_means
    med = np.median(arr_norm, axis=0)
    p17 = np.percentile(arr_norm, BAND_LOW_Q * 100, axis=0)
    p83 = np.percentile(arr_norm, BAND_HIGH_Q * 100, axis=0)
    return years, med, p17, p83


def load_frederikse_replacement(prefix: str, beg: int, end: int
                                ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per Tony's notebook step: load Frederikse 2020 [mean, lower, upper] for
    the component name and return (year, value_m, sigma_m) rebaselined to
    [beg, end] mean = 0. sigma = (upper - lower) / 4 (treating bracket as ~95% CI).
    """
    stem_map = {
        "gis": "Greenland Ice Sheet",
        "te":  "Steric",
        "ais": "Antarctic Ice Sheet",
    }
    if prefix not in stem_map:
        raise KeyError(f"no Frederikse mapping for {prefix}")
    df = pd.read_excel(FRED_XLSX, sheet_name="Global").rename(columns={"Unnamed: 0": "year"}).set_index("year")
    stem = stem_map[prefix]
    m  = df[f"{stem} [mean]"]  / 1000.0
    lo = df[f"{stem} [lower]"] / 1000.0
    up = df[f"{stem} [upper]"] / 1000.0
    norm = m.loc[beg:end].mean()
    m  = m  - norm
    lo = lo - norm
    up = up - norm
    sigma = (up - lo) / 4.0
    return df.index.to_numpy(), m.to_numpy(), sigma.to_numpy()


def load_external_gmsl_obs(beg: int, end: int) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Dangendorf 2024 and Church & White 2011 GMSL, rebaselined to [beg, end] mean = 0.

    Returns dict {label: (years, values_m)}. (No sigma — these aren't carried as
    matched-σ in the source CSVs at annual resolution.)
    """
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    # Dangendorf 2024
    if DANG_CSV.exists():
        dd = pd.read_csv(DANG_CSV).sort_values("year").reset_index(drop=True)
        # value_col is `value` per existing component_overlay_obsdriven loader
        dy = dd["year"].to_numpy()
        # Source CSV is in mm
        dv_mm = dd["value"].to_numpy()
        # Rebaseline to [beg, end]
        mask = (dy >= beg) & (dy <= end)
        if mask.any():
            dv_mm = dv_mm - dv_mm[mask].mean()
        out["Dangendorf 2024"] = (dy, dv_mm / 1000.0)

    # Church & White 2011 (BRICK calibration target = "gmsl_obs" already; this
    # is the published reconstruction with its own header). Skip parsing if
    # not present.
    if CW_CSV.exists():
        cw = pd.read_csv(CW_CSV, skiprows=9)
        gmsl_col = [c for c in cw.columns if "GMSL" in c and "uncertainty" not in c][0]
        cw_y = np.floor(cw["Time"].to_numpy()).astype(int)
        cw_mm = cw[gmsl_col].to_numpy(dtype=float)
        mask = (cw_y >= beg) & (cw_y <= end)
        if mask.any():
            cw_mm = cw_mm - cw_mm[mask].mean()
        out["Church & White 2011"] = (cw_y, cw_mm / 1000.0)

    return out


def main() -> None:
    # Load three BRICK runs
    brick_runs: dict[str, pd.DataFrame] = {}
    for tag, _label, _color, path in BRICK_RUNS:
        print(f"Loading {tag}: {path.name}")
        brick_runs[tag] = pd.read_csv(path)
        print(f"  rows: {len(brick_runs[tag])}")

    # Load calibration obs (gmsl, glaciers, antarctic_imbie)
    print(f"Loading calibration data: {CALIB_CSV.name}")
    calib = pd.read_csv(CALIB_CSV, na_values="NA")
    print(f"  rows: {len(calib)}, years {calib.year.min()}-{calib.year.max()}")

    # Replace merged_greenland with Frederikse per Tony's recipe
    fred_yrs, fred_gis, fred_gis_sigma = load_frederikse_replacement("gis", 1961, 1990)
    calib = calib.drop(columns=["merged_greenland_obs", "merged_greenland_sigma"])
    fred_df = pd.DataFrame({
        "year": fred_yrs,
        "merged_greenland_obs": fred_gis,
        "merged_greenland_sigma": fred_gis_sigma,
    })
    calib = calib.merge(fred_df, on="year", how="left")

    # External GMSL obs (Dangendorf + C&W). Use 1961-1990 baseline to match the
    # GMSL panel convention.
    extra_gmsl_obs = load_external_gmsl_obs(1961, 1990)
    print(f"  extra GMSL obs loaded: {list(extra_gmsl_obs.keys())}")

    n_panels = len(PANEL_SPEC)
    fig, axes = plt.subplots(nrows=n_panels, ncols=1,
                             figsize=(10.5, 2.5 * n_panels + 0.6),
                             sharex=True)
    fig.subplots_adjust(top=0.94, bottom=0.05, left=0.09, right=0.97, hspace=0.45)
    if n_panels == 1:
        axes = [axes]

    for ax, (prefix, title, (beg, end), obs_col, sig_col, ylabel) in zip(axes, PANEL_SPEC):
        # Three BRICK lines, each as 17-83% band + median
        for tag, label, color, _path in BRICK_RUNS:
            years, med, p17, p83 = rebaseline_brick_to_window(brick_runs[tag], prefix, beg, end)
            mask_yr = (years >= HINDCAST_START) & (years <= HINDCAST_END)
            ax.fill_between(years[mask_yr], p17[mask_yr], p83[mask_yr],
                            color=color, alpha=0.18)
            ax.plot(years[mask_yr], med[mask_yr], color=color, lw=1.8, label=label)

        # Calibration-data obs overlay (errorbar)
        if obs_col is not None and obs_col in calib.columns:
            obs_df = calib.dropna(subset=[obs_col])
            obs_df = obs_df[(obs_df.year >= HINDCAST_START) & (obs_df.year <= HINDCAST_END)]
            sig = obs_df[sig_col] if (sig_col and sig_col in calib.columns) else None
            ax.errorbar(obs_df.year, obs_df[obs_col],
                        yerr=sig, fmt="k.", markersize=2.5,
                        elinewidth=0.5, capsize=0, alpha=0.7,
                        label=f"obs ({obs_col})")
        elif prefix == "te":
            # Frederikse Steric for TE (no calib obs)
            sy, sv, sg = load_frederikse_replacement("te", beg, end)
            sm = (sy >= HINDCAST_START) & (sy <= HINDCAST_END)
            ax.errorbar(sy[sm], sv[sm], yerr=sg[sm],
                        fmt="k.", markersize=2.5, elinewidth=0.5, capsize=0,
                        alpha=0.7, label="Frederikse 2020 Steric")

        # Extra GMSL obs (Dangendorf + C&W) only on the SLR panel
        if prefix == "slr":
            for obs_label, (oy, ov) in extra_gmsl_obs.items():
                m = (oy >= HINDCAST_START) & (oy <= HINDCAST_END)
                ax.plot(oy[m], ov[m], lw=1.3, alpha=0.85,
                        label=obs_label,
                        color="#7A1A8B" if "Dangendorf" in obs_label else "#3F8E3F")

        ax.set_title(f"{title}  (rebaselined to {beg}-{end} mean)", fontsize=10,
                     fontweight="bold", color="#1F4E79")
        ax.set_ylabel(ylabel, fontsize=9)
        ax.axhline(0, color="grey", linewidth=0.5)
        ax.axvspan(beg, end, color="grey", alpha=0.06, lw=0)
        ax.grid(alpha=0.3, linewidth=0.4)
        ax.legend(loc="upper left", fontsize=7.5, framealpha=0.9, ncol=2)

    axes[-1].set_xlim(HINDCAST_START, HINDCAST_END)
    axes[-1].set_xlabel("Year", fontsize=10)

    fig.suptitle("BRICK hindcast vs obs — three input scenarios, Tony's plotting conventions",
                 fontsize=12, fontweight="bold", color="#1F4E79", y=0.99)

    # Source attribution under the suptitle (use coordinate inside [top, 1])
    fig.text(0.5, 0.965,
             "BRICK 17-83% band; obs as black errorbars except GMSL panel "
             "(Dangendorf 2024 in purple, Church & White 2011 in green).  "
             "Baseline windows shaded grey.",
             ha="center", va="top", fontsize=8.5, style="italic", color="#444444")

    out_png = OUT_DIR / "component_overlay_tony_style_extended.png"
    out_pdf = OUT_DIR / "component_overlay_tony_style_extended.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")
    print(f"wrote {out_pdf}")

    # Diagnostic table at landmark years for each BRICK run
    print("\nMedian SLR contribution at landmark years (m, rebaselined per Tony):")
    for tag, label, _color, _path in BRICK_RUNS:
        print(f"\n  {tag}  ({label})")
        print(f'    {"year":>6}  {"AIS(92-01)":>11}  {"GIS(61-90)":>11}  '
              f'{"GSIC(61-90)":>12}  {"TE(61-90)":>10}  {"SLR(61-90)":>11}')
        for y in (1900, 1950, 1990, 2018, 2020):
            row = [str(y)]
            for prefix, _, (beg, end), _, _, _ in PANEL_SPEC:
                years, med, _, _ = rebaseline_brick_to_window(brick_runs[tag], prefix, beg, end)
                if y in years:
                    i = list(years).index(y)
                    row.append(f"{med[i]:>+10.4f}")
                else:
                    row.append("-".rjust(10))
            # Reorder slr,gis,gsic,ais,te → ais,gis,gsic,te,slr
            slr_v, gis_v, gsic_v, ais_v, te_v = row[1], row[2], row[3], row[4], row[5]
            print(f"    {y:>6d}  {ais_v}  {gis_v}  {gsic_v}  {te_v}  {slr_v}")


if __name__ == "__main__":
    main()
