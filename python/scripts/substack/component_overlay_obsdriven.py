"""
component_overlay_obsdriven.py
==============================

Tony Wong follow-up figure: per-component SLR from BRICK driven by every
combination of (GMST, OHC) ∈ {obs, FaIR-mean}.

The 2×2 design isolates which input drives the FaIR-mean vs. observed
total-SLR gap:
  - AIS, GIS, GSIC are GMST-only consumers.
  - Thermal expansion (TE) is OHC-only (linear in ΔOHC; verified to 0.5%).
  - Landwater storage (LWS) depends on neither (BRICK-prior driven, no
    posterior spread).

The 2024 medians (cm, re-ref'd to year 2000) decompose the
obs_obs − fair_fair = +0.875 cm gap as ~+0.80 cm GMST contribution and
~+0.07 cm OHC contribution (with the Zanna+IGCC splice; was −0.07 with
the older Zanna+Cheng splice — see `project_igcc_ohc_finding.md`). The
obs-driven override mechanism is verified bit-identical to BRICK's
default-init path, so all differences are pure input-trajectory effects
(see `project_brick_override_is_bitidentical.md`).

Inputs (year cols 1850..2024, cm rel. year 2000, schema documented in
`handoff_2026-05-21_julia_per_component_done.md` §1.1):
  outputs/brick_obsdriven_obs_obs_to2024.csv
  outputs/brick_obsdriven_obs_fair_to2024.csv
  outputs/brick_obsdriven_fair_obs_to2024.csv
  outputs/brick_obsdriven_fair_fair_to2024.csv

Total-SLR panel also overlays:
  data/calibration/CSIRO_Recons_gmsl_yr_2015.csv  (Church & White 2011, BRICK calibration target)
  data/observations/dangendorf_2024_gmsl.csv      (Dangendorf 2024 tide-gauge reconstruction)
  data/observations/nasa_gmsl_annual.csv          (NOAA STAR satellite altimetry)

Component obs (Frederikse 2020 for AIS/GIS/GSIC) are not yet available
locally — those panels show only the four BRICK combos. Add a Frederikse
overlay once those data land.

Output:
  outputs/substack/component_overlay_obsdriven.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OBSDRIVEN_DIR = ROOT / "outputs"
# obs_obs and fair_obs swapped 2026-05-21 to the Zanna+IGCC splice — IGCC is
# the more representative obs-anchored OHC product (Cheng IAPv4.2 is the
# low-side outlier vs the IGCC multi-product compilation). See memory entry
# project_igcc_ohc_finding.md. Both "obs OHC" combos updated together so the
# OHC source is consistent across all four panels.
COMBO_CSV = {
    "obs_obs":   OBSDRIVEN_DIR / "brick_obsdriven_obs_obs_igcc_to2024.csv",
    "obs_fair":  OBSDRIVEN_DIR / "brick_obsdriven_obs_fair_to2024.csv",
    "fair_obs":  OBSDRIVEN_DIR / "brick_obsdriven_fair_obs_igcc_to2024.csv",
    "fair_fair": OBSDRIVEN_DIR / "brick_obsdriven_fair_fair_to2024.csv",
}
CW_CSV   = ROOT / "data" / "calibration"  / "CSIRO_Recons_gmsl_yr_2015.csv"
DANG_CSV = ROOT / "data" / "observations" / "dangendorf_2024_gmsl.csv"
NASA_CSV = ROOT / "data" / "observations" / "nasa_gmsl_annual.csv"
FRED_XLSX = ROOT / "data" / "observations" / "raw" / "frederikse2020_global_basin_timeseries.xlsx"
OUT_DIR  = ROOT / "outputs" / "substack"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Frederikse column mapping to BRICK component (ours -> Frederikse [mean] col stem)
FRED_COMP_MAP = {
    "ais":  "Antarctic Ice Sheet",
    "gis":  "Greenland Ice Sheet",
    "gsic": "Glaciers",
    "te":   "Steric",
    "lws":  "Terrestrial Water Storage",
    "slr":  "Observed GMSL",
}

PLOT_START = 1900
PLOT_END   = 2024

# Combo color palette + style. obs_obs/fair_fair get full bands (the
# "extremes"); obs_fair/fair_obs get median-only lines so the figure
# isn't a band fight. Match obs_overlay_slr.py conventions where possible.
COMBO_STYLE = {
    "obs_obs":   {"color": "#A6361C", "lw": 2.2, "band": True,
                  "label": "obs GMST (IGCC) + obs OHC (Zanna+IGCC)"},
    "fair_fair": {"color": "#1F4E79", "lw": 2.2, "band": True,
                  "label": "FaIR-mean GMST + FaIR-mean OHC  (10k-cell ensemble mean fed once)"},
    "obs_fair":  {"color": "#E08214", "lw": 1.6, "band": False,
                  "label": "obs GMST (IGCC) + FaIR-mean OHC", "ls": "--"},
    "fair_obs":  {"color": "#5AAE61", "lw": 1.6, "band": False,
                  "label": "FaIR-mean GMST + obs OHC (Zanna+IGCC)", "ls": "--"},
}

COMPONENTS = ["ais", "gis", "gsic", "te", "lws", "slr"]
COMPONENT_TITLE = {
    "ais":  "Antarctic ice sheet (AIS) — GMST-driven",
    "gis":  "Greenland ice sheet (GIS) — GMST-driven (nonlinear in trajectory shape)",
    "gsic": "Glaciers & small ice caps (GSIC) — GMST-driven",
    "te":   "Thermal expansion (TE) — linear in ΔOHC",
    "lws":  "Landwater storage (LWS) — projection-period only",
    "slr":  "Total GMSL (climate-only, LWS-excluded historical)",
}

LANDMARK_YEARS = (1900, 1950, 1980, 2000, 2013, 2020, 2024)


def load_combo(path: Path) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return (year array, {component: (n_post, n_year) array})."""
    df = pd.read_csv(path)
    out: dict[str, np.ndarray] = {}
    years_ref = None
    for comp in COMPONENTS:
        pat = re.compile(rf"^{comp}_(\d{{4}})$")
        cols = sorted(((int(pat.match(c).group(1)), c) for c in df.columns if pat.match(c)),
                      key=lambda t: t[0])
        years = np.array([y for y, _ in cols])
        if years_ref is None:
            years_ref = years
        elif not np.array_equal(years, years_ref):
            raise RuntimeError(f"{path.name}: component {comp} year span "
                               f"differs from reference")
        out[comp] = df[[c for _, c in cols]].to_numpy()
    return years_ref, out


def percentile_bands(traj: np.ndarray, plot_mask: np.ndarray) -> dict[str, np.ndarray]:
    """Equal-weighted 5/50/95 percentile bands + mean across rows."""
    sub = traj[:, plot_mask]
    return {
        "p5":   np.percentile(sub, 5, axis=0),
        "p50":  np.percentile(sub, 50, axis=0),
        "p95":  np.percentile(sub, 95, axis=0),
        "mean": sub.mean(axis=0),
    }


def rebase_obs_to_2000_cm(path: Path) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path).sort_values("year").reset_index(drop=True)
    if 2000 not in df.year.values:
        raise RuntimeError(f"{path.name}: year 2000 not present")
    v2000 = float(df.loc[df.year == 2000, "value"].iloc[0])
    return df.year.to_numpy(), (df["value"].to_numpy() - v2000) / 10.0


def load_church_white(path: Path) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path, skiprows=9)
    gmsl_col = [c for c in df.columns if "GMSL" in c and "uncertainty" not in c][0]
    years = np.floor(df["Time"].to_numpy()).astype(int)
    mm = df[gmsl_col].to_numpy(dtype=float)
    if 2000 not in years:
        raise RuntimeError(f"{path.name}: year 2000 not present")
    return years, (mm - float(mm[years == 2000][0])) / 10.0


def load_frederikse(path: Path) -> dict[str, dict[str, np.ndarray]]:
    """Frederikse 2020 Global sheet -> {component_name: {year, mean, lower, upper}}
    All values cm, re-baselined to year 2000.
    Native units in xlsx are mm (Observed GMSL at 1900 ~-173 mm rel mid-record)."""
    df = pd.read_excel(path, sheet_name="Global")
    df = df.rename(columns={"Unnamed: 0": "year"}).set_index("year")
    out = {}
    for comp, stem in FRED_COMP_MAP.items():
        mean_col, lo_col, up_col = f"{stem} [mean]", f"{stem} [lower]", f"{stem} [upper]"
        if mean_col not in df.columns:
            continue
        mean_mm = df[mean_col].to_numpy(dtype=float)
        lo_mm   = df[lo_col].to_numpy(dtype=float)
        up_mm   = df[up_col].to_numpy(dtype=float)
        years = df.index.to_numpy()
        i2000 = int(np.where(years == 2000)[0][0])
        out[comp] = dict(
            year  = years,
            mean  = (mean_mm - mean_mm[i2000]) / 10.0,
            lower = (lo_mm - mean_mm[i2000]) / 10.0,
            upper = (up_mm - mean_mm[i2000]) / 10.0,
        )
    return out


def plot_component(ax, comp: str, combo_bands: dict, plot_yrs: np.ndarray,
                   obs_overlays: dict | None,
                   frederikse: dict | None = None) -> None:
    title = COMPONENT_TITLE[comp]
    ax.set_title(title, fontsize=11, fontweight="bold", color="#1F4E79")

    for combo, bands in combo_bands.items():
        sty = COMBO_STYLE[combo]
        if sty["band"]:
            ax.fill_between(plot_yrs, bands["p5"], bands["p95"],
                            color=sty["color"], alpha=0.16,
                            label=f'{sty["label"]} (5–95%)')
            ax.plot(plot_yrs, bands["p50"], color=sty["color"],
                    lw=sty["lw"], label=f'{sty["label"]} (median)')
        else:
            ax.plot(plot_yrs, bands["p50"], color=sty["color"],
                    lw=sty["lw"], ls=sty.get("ls", "-"),
                    label=f'{sty["label"]} (median)')

    if frederikse is not None:
        fy = frederikse["year"]
        m = (fy >= PLOT_START) & (fy <= PLOT_END)
        ax.fill_between(fy[m], frederikse["lower"][m], frederikse["upper"][m],
                        color="#1B7837", alpha=0.18, label="Frederikse 2020 (5–95%)")
        ax.plot(fy[m], frederikse["mean"][m], color="#1B7837", lw=2.0,
                label="Frederikse 2020 (mean)")

    if obs_overlays:
        for obs_label, (oy, ov, oc, olw) in obs_overlays.items():
            ax.plot(oy, ov, color=oc, lw=olw, label=obs_label)

    ax.axhline(0, color="grey", linewidth=0.5)
    ax.axvline(2000, color="grey", linewidth=0.4, linestyle=":")
    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("cm (rel. year 2000)", fontsize=9)
    ax.grid(alpha=0.3, linewidth=0.4)


def main() -> None:
    print("Loading 4 obs-driven CSVs (~720 MB total)...")
    combos = {}
    years_ref = None
    for combo, path in COMBO_CSV.items():
        years, comp_arrs = load_combo(path)
        if years_ref is None:
            years_ref = years
        combos[combo] = comp_arrs
        print(f"  {combo}: {comp_arrs['slr'].shape[0]} posterior members, "
              f"years {years_ref[0]}-{years_ref[-1]}")

    plot_mask = (years_ref >= PLOT_START) & (years_ref <= PLOT_END)
    plot_yrs = years_ref[plot_mask]

    # Compute percentile bands per (combo, component)
    bands_by_combo = {comp: {} for comp in COMPONENTS}
    for combo, comp_arrs in combos.items():
        for comp in COMPONENTS:
            bands_by_combo[comp][combo] = percentile_bands(comp_arrs[comp], plot_mask)

    # Load obs overlays (Total panel only) and Frederikse per-component data
    cw_y, cw_v = load_church_white(CW_CSV)
    dy, dv = rebase_obs_to_2000_cm(DANG_CSV)
    ny, nv = rebase_obs_to_2000_cm(NASA_CSV)
    total_obs = {
        "Church & White 2011 (calibration target)": (cw_y, cw_v, "#3F8E3F", 1.4),
        "Dangendorf et al. 2024":                   (dy,   dv, "#000000",  1.4),
        "NOAA STAR altimetry":                      (ny,   nv, "#7A1A8B",  1.4),
    }
    print("Loading Frederikse 2020 components...")
    frederikse = load_frederikse(FRED_XLSX)
    print(f"  components loaded: {list(frederikse.keys())}")

    # Build the "BRICK + historical LWS correction" trace for the Total panel:
    # add Frederikse TWS [mean] (re-based 2000) onto the BRICK obs_obs median.
    fy_lws = frederikse["lws"]["year"]
    fv_lws = frederikse["lws"]["mean"]
    # Align Frederikse TWS to plot_yrs (Frederikse covers 1900-2018; pad
    # with NaN outside)
    tws_aligned = np.full_like(plot_yrs, np.nan, dtype=float)
    for i, y in enumerate(plot_yrs):
        hit = np.where(fy_lws == y)[0]
        if len(hit):
            tws_aligned[i] = fv_lws[hit[0]]
    brick_total_obs_obs = bands_by_combo["slr"]["obs_obs"]["p50"]
    brick_total_corrected = brick_total_obs_obs + tws_aligned

    # 2×3 grid: AIS, GIS, GSIC on top; TE, LWS, Total on bottom
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.5), sharex=True)
    panel_order = [["ais", "gis", "gsic"], ["te", "lws", "slr"]]

    for r in range(2):
        for c in range(3):
            comp = panel_order[r][c]
            obs_overlays = total_obs if comp == "slr" else None
            fred_comp = frederikse.get(comp) if comp != "slr" else None
            plot_component(axes[r, c], comp, bands_by_combo[comp],
                           plot_yrs, obs_overlays, frederikse=fred_comp)

    # Add the LWS-corrected BRICK total to the Total panel
    slr_ax = axes[1, 2]
    valid = ~np.isnan(brick_total_corrected)
    slr_ax.plot(plot_yrs[valid], brick_total_corrected[valid],
                color="#A6361C", lw=1.8, ls="--",
                label="BRICK obs_obs + Frederikse TWS (apples-to-apples)")
    # Frederikse Observed GMSL on the total panel too
    fy_obs = frederikse["slr"]["year"]; fv_obs = frederikse["slr"]["mean"]
    mfobs = (fy_obs >= PLOT_START) & (fy_obs <= PLOT_END)
    slr_ax.fill_between(fy_obs[mfobs], frederikse["slr"]["lower"][mfobs],
                        frederikse["slr"]["upper"][mfobs],
                        color="#1B7837", alpha=0.18,
                        label="Frederikse Observed GMSL (5–95%)")
    slr_ax.plot(fy_obs[mfobs], fv_obs[mfobs], color="#1B7837", lw=2.0,
                label="Frederikse Observed GMSL (mean)")

    # Single shared legend: pull from TE panel (has all 4 BRICK combos +
    # Frederikse) and append the Total-panel-only "BRICK + TWS" line.
    handles, labels = axes[1, 0].get_legend_handles_labels()
    extra_h, extra_l = axes[1, 2].get_legend_handles_labels()
    for h, l in zip(extra_h, extra_l):
        if l not in labels:
            handles.append(h); labels.append(l)
    seen = set(); H = []; L = []
    for h, l in zip(handles, labels):
        if l not in seen:
            seen.add(l); H.append(h); L.append(l)
    fig.legend(H, L, loc="lower center", ncol=3, fontsize=8.5,
               bbox_to_anchor=(0.5, -0.10), framealpha=0.92)

    fig.suptitle("BRICK per-component SLR by (GMST, OHC) source — "
                 "FaIR-mean vs. observed inputs",
                 fontsize=12, fontweight="bold", color="#1F4E79", y=1.0)

    # Explicit data-source attribution, so the reader can audit which obs and
    # FaIR products feed each line. Italic gray under the bold title.
    fig.text(0.5, 0.962,
             "Data sources — "
             "obs GMST: IGCC 2024 4-dataset mean  ·  "
             "obs OHC: Zanna 2019 + IGCC 2024 splice (1850-1960 Zanna, 1960+ IGCC)  ·  "
             "FaIR GMST / OHC: ensemble mean of 10k LHS FaIR v2.2.4 cube (RCP4.5-anchor)",
             ha="center", va="top", fontsize=9, style="italic", color="#444444")

    # Attribution annotation in the LWS panel (which is otherwise sparse).
    # Y-axis spans BOTH the BRICK obs_obs LWS range AND the Frederikse TWS
    # range, since they tell different stories (BRICK = 0 by design pre-2019;
    # Frederikse goes ~-1 to ~+3 cm).
    lws_ax = axes[1, 1]
    lws_p50 = bands_by_combo["lws"]["obs_obs"]["p50"][-1]
    fred_lws = frederikse["lws"]
    fy = fred_lws["year"]; mf = (fy >= PLOT_START) & (fy <= PLOT_END)
    y_min = min(bands_by_combo["lws"]["obs_obs"]["p5"].min(),
                fred_lws["lower"][mf].min())
    y_max = max(bands_by_combo["lws"]["obs_obs"]["p95"].max(),
                fred_lws["upper"][mf].max())
    pad = 0.1 * (y_max - y_min)
    lws_ax.set_ylim(y_min - pad, y_max + pad)
    lws_text = (
        "LWS = 0 by design before MimiBRICK's first_projection_year (~2019),\n"
        "because BRICK was calibrated against Church & White 2011 with LWS\n"
        "removed. The projection-period scenario is identical across all 4\n"
        "combos (no posterior spread; cancels in paired marginals).\n"
        f"Year-2024 median: {lws_p50:+.3f} cm rel. 2000."
    )
    lws_ax.text(0.04, 0.96, lws_text, transform=lws_ax.transAxes,
                fontsize=8.5, verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                          edgecolor="grey", alpha=0.9))

    # Embed a compact 2024 attribution table in the Total panel
    table_lines = ["Year-2024 medians (cm rel. 2000):"]
    for combo in ("obs_obs", "obs_fair", "fair_obs", "fair_fair"):
        v = bands_by_combo["slr"][combo]["p50"][-1]
        table_lines.append(f"  {combo:>10s}: {v:+.2f}")
    gap = (bands_by_combo["slr"]["obs_obs"]["p50"][-1]
           - bands_by_combo["slr"]["fair_fair"]["p50"][-1])
    gmst_only = (bands_by_combo["slr"]["obs_fair"]["p50"][-1]
                 - bands_by_combo["slr"]["fair_fair"]["p50"][-1])
    ohc_only = (bands_by_combo["slr"]["fair_obs"]["p50"][-1]
                - bands_by_combo["slr"]["fair_fair"]["p50"][-1])
    table_lines.append("")
    table_lines.append(f"  obs_obs − fair_fair gap: {gap:+.2f}")
    table_lines.append(f"    GMST contribution:     {gmst_only:+.2f}")
    table_lines.append(f"    OHC contribution:      {ohc_only:+.2f}")
    # Frederikse 2018 reference
    i2018 = int(np.where(fy_obs == 2018)[0][0])
    table_lines.append("")
    table_lines.append(f"  Frederikse Obs 2018:   {fv_obs[i2018]:+.2f}")
    table_lines.append(f"  BRICK obs_obs 2018:    "
                       f"{brick_total_obs_obs[plot_yrs == 2018][0]:+.2f}")
    table_lines.append(f"  + LWS correction:      "
                       f"{brick_total_corrected[plot_yrs == 2018][0]:+.2f}")
    table_lines.append("")
    table_lines.append("Diagnostic (1900-2018):")
    table_lines.append("  ΔOHC (ZJ):")
    table_lines.append("    SNEASY MAP:  +75.4")
    table_lines.append("    FaIR mean:   +51.5")
    table_lines.append("    Zanna+IGCC:  +48.9")
    table_lines.append("    Zanna+Cheng: +45.4")
    table_lines.append("  ΔTE is linear in ΔOHC")
    table_lines.append("  to <0.5% (verified).")
    slr_ax.text(0.02, 0.98, "\n".join(table_lines), transform=slr_ax.transAxes,
                fontsize=7.0, verticalalignment="top", family="monospace",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="grey", alpha=0.92))

    fig.tight_layout(rect=[0, 0.03, 1, 0.97])
    out_png = OUT_DIR / "component_overlay_obsdriven.png"
    out_pdf = OUT_DIR / "component_overlay_obsdriven.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")
    print(f"wrote {out_pdf}")

    # Diagnostic print: 2024 medians per (combo, component)
    print("\nYear-2024 medians (cm rel. year 2000):")
    print(f"{'combo':>10s}  " + "  ".join(f"{c:>10s}" for c in COMPONENTS))
    for combo in COMBO_CSV:
        row = [combo]
        for comp in COMPONENTS:
            v = bands_by_combo[comp][combo]["p50"][-1]
            row.append(f"{v:+10.3f}")
        print(f"{row[0]:>10s}  " + "  ".join(row[1:]))


if __name__ == "__main__":
    main()
