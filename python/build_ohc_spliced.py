"""
Build a spliced observed OHC time series (Zanna 2019 PNAS + Cheng IAPv4.2)
for use as input to obs-driven BRICK runs.

Output frame: cumulative OHC since 1750 (FaIR's internal reference year),
units 10^22 J (matches BRICK's `ocean_heat_interior` parameter, matches the
unit convention in python/lhs_climate_pilot.py:418).

Pipeline:
  1850-1869:    FaIR ensemble-mean OHC trajectory (mean over the 490x841
                LHS-10k baseline cube).
  1870-SPLICE:  Zanna 2019 OHC_2000m, shifted so that Zanna(1871) equals
                the FaIR ensemble mean at 1871. This anchors the obs
                series into FaIR's 1750-zero frame.
  SPLICE+1...:  Cheng IAPv4.2 0-2000m annual mean, shifted by a single
                constant so Cheng(SPLICE+1) == Zanna_aligned(SPLICE).

A sensitivity figure shows the spliced result for SPLICE in
{1955, 1960, 1965, 1970, 1980}; the headline output uses SPLICE_YEAR.

Inputs:
  data/observations/raw/zanna2019_OHC_GF_1870_2018.nc
  data/observations/raw/IAPv4.2_OHC_estimate_update.txt
  outputs/rff_baseline_stoch_to2300.npz   (FaIR baseline cube)

Outputs:
  data/observations/ohc_spliced_zanna_cheng.csv     (canonical spliced series)
  outputs/ohc_splice_sensitivity.png                (transition-year sensitivity)

Refs:
  Zanna L. et al. 2019. PNAS 116:1126-1131. doi:10.1073/pnas.1808838115
    Zenodo deposit: doi:10.5281/zenodo.4603700
  Cheng L. et al. 2024. ESSD 16:3517-3546. doi:10.5194/essd-16-3517-2024
    Annual-update text file: IAPv4.2_OHC_estimate_update.txt
"""

from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

# --- Configuration (named constants per project convention) -----------------
REPO_ROOT = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
ZANNA_NC = REPO_ROOT / "data/observations/raw/zanna2019_OHC_GF_1870_2018.nc"
CHENG_TXT = REPO_ROOT / "data/observations/raw/IAPv4.2_OHC_estimate_update.txt"
FAIR_CUBE_NPZ = REPO_ROOT / "outputs/rff_baseline_stoch_to2300.npz"

OUT_CSV = REPO_ROOT / "data/observations/ohc_spliced_zanna_cheng.csv"
OUT_FIG = REPO_ROOT / "outputs/ohc_splice_sensitivity.png"

ZANNA_DEPTH_VAR = "OHC_2000m"           # match Cheng 0-2000m for headline
ZANNA_ERR_VAR = "error_OHC_2000"

ANCHOR_YEAR = 1871                       # earliest Zanna year with non-zero OHC
SPLICE_YEAR = 1960                       # canonical splice transition
SENSITIVITY_SPLICE_YEARS = [1955, 1960, 1965, 1970, 1980]

# Cheng has much higher interannual noise than Zanna in 1955-1965 (Green's
# function reconstruction smooths, EnOI-DE/CMIP5 product does not). A
# single-year offset locks one noisy Cheng point to one smooth Zanna point.
# Use a centered N-year mean so the offset reflects the *level* difference
# rather than one year's variability. ±2 -> 5-year window centered on splice.
SPLICE_OFFSET_HALFWINDOW = 2

START_YEAR_OUT = 1850                    # match FaIR cube; pre-1870 from FaIR mean
END_YEAR_OUT_DEFAULT = None              # use whatever the obs data supports

ZANNA_UNIT_TO_BRICK = 0.1                # Zanna ZJ (=1e21 J) -> 1e22 J
CHENG_UNIT_TO_BRICK = 1.0                # Cheng already in 1e22 J


# --- Loaders -----------------------------------------------------------------
def load_zanna(nc_path: Path) -> pd.DataFrame:
    """Return Zanna OHC_2000m (and error) as a DataFrame in units of 10^22 J,
    indexed by integer year. Zanna's native zero is 1870."""
    ds = xr.open_dataset(nc_path)
    year = ds["time"].values.astype(int)
    ohc_zj = ds[ZANNA_DEPTH_VAR].values
    err_zj = ds[ZANNA_ERR_VAR].values
    df = pd.DataFrame({
        "year": year,
        "zanna_ohc_1e22J": ohc_zj * ZANNA_UNIT_TO_BRICK,
        "zanna_err_1e22J": err_zj * ZANNA_UNIT_TO_BRICK,
    }).set_index("year")
    return df


def load_cheng_annual(txt_path: Path) -> pd.DataFrame:
    """Read IAPv4.2 monthly text file, return calendar-year mean 0-2000m OHC."""
    cols = [
        "year", "month",
        "ohc0_700", "smooth_ohc0_700", "err_ohc0_700",
        "ohc700_2000", "smooth_ohc700_2000", "err_ohc700_2000",
        "ohc0_2000", "smooth_ohc0_2000", "err_ohc0_2000",
        "ohc2000_6000", "smooth_ohc2000_6000", "err_ohc2000_6000",
    ]
    df = pd.read_csv(txt_path, sep=r"\s+", comment="%", header=None,
                     names=cols, na_values="NaN")
    # The IAP txt has a "[year] [month] ..." label row that doesn't start
    # with %; coerce numerics and drop it.
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["year", "month", "ohc0_2000"])
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    annual = df.groupby("year").agg(
        cheng_ohc_1e22J=("ohc0_2000", "mean"),
        cheng_err_1e22J=("err_ohc0_2000", "mean"),
        n_months=("ohc0_2000", "count"),
    )
    # keep only fully-observed years (12 months); drops partial trailing year
    annual = annual[annual["n_months"] == 12].drop(columns="n_months")
    annual["cheng_ohc_1e22J"] *= CHENG_UNIT_TO_BRICK
    annual["cheng_err_1e22J"] *= CHENG_UNIT_TO_BRICK
    return annual


def load_fair_mean_ohc(cube_path: Path) -> pd.Series:
    """Return FaIR ensemble-mean OHC trajectory (mean over RFF x cfg), indexed by year."""
    with np.load(cube_path, mmap_mode="r") as z:
        years = z["years"][:]
        ohc = z["ohc_traj_rff"]
        # Mean over RFFs and cfgs (axes 0 and 1)
        # ohc is float32 (490, 841, 451) ~= 412 GB if loaded; use chunked mean
        # but 490*841*451*4 bytes = 0.74 GB so just load it
        mean_ohc = ohc.mean(axis=(0, 1))  # (451,) float32
    return pd.Series(mean_ohc.astype(np.float64), index=years, name="fair_mean_ohc_1e22J")


# --- Splice ------------------------------------------------------------------
def splice_series(zanna: pd.DataFrame, cheng: pd.DataFrame,
                  fair_mean: pd.Series, splice_year: int,
                  start_year: int) -> pd.DataFrame:
    """Return a unified annual cumulative-OHC series in the FaIR (1750-zero) frame.

    Splice rules:
      [start_year, 1869]   -> FaIR mean trajectory
      [1870, splice_year]  -> Zanna shifted so Zanna(ANCHOR_YEAR) == FaIR_mean(ANCHOR_YEAR)
      (splice_year, end]   -> Cheng annual shifted so Cheng(splice_year+1)
                              equals the spliced value at splice_year+1 implied
                              by extending Zanna_shifted continuously.

    The Cheng offset is a single constant chosen so that Cheng(splice_year)
    matches Zanna_shifted(splice_year).
    """
    if ANCHOR_YEAR not in zanna.index:
        raise ValueError(f"Zanna missing anchor year {ANCHOR_YEAR}")
    if ANCHOR_YEAR not in fair_mean.index:
        raise ValueError(f"FaIR cube missing anchor year {ANCHOR_YEAR}")
    zanna_shift = fair_mean.loc[ANCHOR_YEAR] - zanna.loc[ANCHOR_YEAR, "zanna_ohc_1e22J"]
    zanna_aligned = zanna["zanna_ohc_1e22J"] + zanna_shift

    if splice_year not in zanna_aligned.index:
        raise ValueError(f"Zanna does not cover splice year {splice_year}")
    if splice_year not in cheng.index:
        raise ValueError(f"Cheng does not cover splice year {splice_year}")
    w = SPLICE_OFFSET_HALFWINDOW
    win = np.arange(splice_year - w, splice_year + w + 1)
    win_zanna = [y for y in win if y in zanna_aligned.index]
    win_cheng = [y for y in win if y in cheng.index]
    if len(win_zanna) < 2 * w + 1 or len(win_cheng) < 2 * w + 1:
        raise ValueError(f"Splice window {win[0]}-{win[-1]} not fully covered "
                         f"by both products (Zanna: {len(win_zanna)}, "
                         f"Cheng: {len(win_cheng)})")
    zanna_win_mean = zanna_aligned.loc[win_zanna].mean()
    cheng_win_mean = cheng.loc[win_cheng, "cheng_ohc_1e22J"].mean()
    cheng_offset = zanna_win_mean - cheng_win_mean
    cheng_aligned = cheng["cheng_ohc_1e22J"] + cheng_offset

    end_year = int(cheng_aligned.index.max())
    out_index = np.arange(start_year, end_year + 1)
    out = pd.DataFrame(index=out_index)
    out.index.name = "year"

    # Pre-Zanna: FaIR mean
    pre_zanna = (out.index >= start_year) & (out.index < 1870)
    out.loc[pre_zanna, "ohc_1e22J"] = fair_mean.reindex(out.index[pre_zanna]).values
    out.loc[pre_zanna, "source"] = "fair_mean"

    # 1870 .. splice_year: Zanna_aligned
    zanna_range = (out.index >= 1870) & (out.index <= splice_year)
    out.loc[zanna_range, "ohc_1e22J"] = zanna_aligned.reindex(out.index[zanna_range]).values
    out.loc[zanna_range, "source"] = "zanna_aligned"

    # splice_year+1 .. end: Cheng_aligned
    cheng_range = out.index > splice_year
    out.loc[cheng_range, "ohc_1e22J"] = cheng_aligned.reindex(out.index[cheng_range]).values
    out.loc[cheng_range, "source"] = "cheng_aligned"

    # Attach metadata
    attrs = {
        "zanna_shift_1e22J": float(zanna_shift),
        "cheng_offset_1e22J": float(cheng_offset),
        "anchor_year": ANCHOR_YEAR,
        "splice_year": splice_year,
        "splice_offset_halfwindow": SPLICE_OFFSET_HALFWINDOW,
        "splice_window_years": f"{int(win[0])}-{int(win[-1])}",
        "fair_mean_at_anchor": float(fair_mean.loc[ANCHOR_YEAR]),
        "zanna_at_anchor": float(zanna.loc[ANCHOR_YEAR, "zanna_ohc_1e22J"]),
        "zanna_aligned_mean_in_window": float(zanna_win_mean),
        "cheng_raw_mean_in_window": float(cheng_win_mean),
    }
    out.attrs = attrs
    return out


# --- Plot --------------------------------------------------------------------
def plot_sensitivity(zanna: pd.DataFrame, cheng: pd.DataFrame,
                     fair_mean: pd.Series, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11, 9), sharex=True)
    ax_full, ax_zoom = axes

    # Top: full spliced series for each candidate splice year
    colors = plt.cm.viridis(np.linspace(0.15, 0.85, len(SENSITIVITY_SPLICE_YEARS)))
    for c, sy in zip(colors, SENSITIVITY_SPLICE_YEARS):
        s = splice_series(zanna, cheng, fair_mean, sy, START_YEAR_OUT)
        ax_full.plot(s.index, s["ohc_1e22J"], color=c, lw=1.3,
                     label=f"splice at {sy}")
        ax_zoom.plot(s.index, s["ohc_1e22J"], color=c, lw=1.3,
                     label=f"splice at {sy}")

    # Underlay raw obs (aligned only via Zanna anchor) for reference
    zanna_shift = fair_mean.loc[ANCHOR_YEAR] - zanna.loc[ANCHOR_YEAR, "zanna_ohc_1e22J"]
    zanna_aligned = zanna["zanna_ohc_1e22J"] + zanna_shift
    ax_full.plot(zanna_aligned.index, zanna_aligned.values, "k:",
                 lw=1.0, alpha=0.6, label="Zanna (aligned, raw)")
    ax_zoom.plot(zanna_aligned.index, zanna_aligned.values, "k:",
                 lw=1.0, alpha=0.6, label="Zanna (aligned, raw)")

    # FaIR mean as a faint reference for the obs comparison
    ax_full.plot(fair_mean.index, fair_mean.values, color="0.5", lw=0.9,
                 alpha=0.7, label="FaIR cube mean (LHS-10k baseline)")
    ax_zoom.plot(fair_mean.index, fair_mean.values, color="0.5", lw=0.9,
                 alpha=0.7, label="FaIR cube mean")

    ax_full.set_ylabel("OHC since FaIR 1750-zero  ($10^{22}$ J)")
    ax_full.set_title("Spliced OHC: Zanna 2019 (0-2000m) + Cheng IAPv4.2 (0-2000m), "
                      f"anchored to FaIR mean at {ANCHOR_YEAR}")
    ax_full.legend(loc="upper left", fontsize=8, ncol=2)
    ax_full.grid(alpha=0.3)

    ax_zoom.set_xlim(1950, 1990)
    z_min = min(splice_series(zanna, cheng, fair_mean, sy, START_YEAR_OUT)
                .loc[1950:1990, "ohc_1e22J"].min()
                for sy in SENSITIVITY_SPLICE_YEARS)
    z_max = max(splice_series(zanna, cheng, fair_mean, sy, START_YEAR_OUT)
                .loc[1950:1990, "ohc_1e22J"].max()
                for sy in SENSITIVITY_SPLICE_YEARS)
    pad = 0.05 * (z_max - z_min)
    ax_zoom.set_ylim(z_min - pad, z_max + pad)
    ax_zoom.set_xlabel("Year")
    ax_zoom.set_ylabel("OHC ($10^{22}$ J)")
    ax_zoom.set_title("Sensitivity to splice-transition year (1950-1990 zoom)")
    ax_zoom.grid(alpha=0.3)
    ax_zoom.legend(loc="upper left", fontsize=8, ncol=2)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f"wrote {out_path}")


# --- Main --------------------------------------------------------------------
def main() -> None:
    print(f"Loading Zanna 2019 from {ZANNA_NC.name}")
    zanna = load_zanna(ZANNA_NC)
    print(f"  rows: {len(zanna)}, years: {int(zanna.index.min())}-{int(zanna.index.max())}")

    print(f"Loading Cheng IAPv4.2 from {CHENG_TXT.name}")
    cheng = load_cheng_annual(CHENG_TXT)
    print(f"  rows: {len(cheng)}, years: {int(cheng.index.min())}-{int(cheng.index.max())}")

    print(f"Loading FaIR baseline cube from {FAIR_CUBE_NPZ.name}")
    fair_mean = load_fair_mean_ohc(FAIR_CUBE_NPZ)
    print(f"  rows: {len(fair_mean)}, years: {int(fair_mean.index.min())}-{int(fair_mean.index.max())}")

    # Canonical splice
    print(f"\nBuilding canonical splice (year={SPLICE_YEAR})")
    canonical = splice_series(zanna, cheng, fair_mean, SPLICE_YEAR, START_YEAR_OUT)
    for k, v in canonical.attrs.items():
        print(f"  {k}: {v}")

    # Continuity diagnostic: compare splice-point jump to surrounding Cheng
    # year-to-year variability. Note that Cheng has higher interannual noise
    # than Zanna so single-year jumps of ~1 1e22 J are normal in the obs.
    pre = canonical.loc[SPLICE_YEAR, "ohc_1e22J"]
    post = canonical.loc[SPLICE_YEAR + 1, "ohc_1e22J"]
    cheng_yoy = cheng["cheng_ohc_1e22J"].diff().loc[SPLICE_YEAR - 5:SPLICE_YEAR + 5]
    print(f"  splice point: OHC({SPLICE_YEAR})={pre:.3f}, OHC({SPLICE_YEAR+1})={post:.3f}, "
          f"Δ={post-pre:+.3f}")
    print(f"  Cheng year-to-year ΔOHC in window {SPLICE_YEAR - 5}-{SPLICE_YEAR + 5}: "
          f"mean={cheng_yoy.mean():+.3f}, std={cheng_yoy.std():.3f} 1e22 J/yr")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    canonical_out = canonical.reset_index()
    # Provenance header
    header = (
        f"# Spliced observed OHC (cumulative since FaIR 1750-zero), units 1e22 J\n"
        f"# Zanna 2019 PNAS (1870-{SPLICE_YEAR}, OHC_2000m, anchored to FaIR mean at {ANCHOR_YEAR}); "
        f"Cheng IAPv4.2 ({SPLICE_YEAR+1}-{int(cheng.index.max())}, 0-2000m annual mean, "
        f"constant-offset splice at {SPLICE_YEAR})\n"
        f"# 1850-1869 filled from FaIR ensemble-mean (LHS-10k baseline cube)\n"
        f"# zanna_shift_1e22J={canonical.attrs['zanna_shift_1e22J']:.6f}, "
        f"cheng_offset_1e22J={canonical.attrs['cheng_offset_1e22J']:.6f}\n"
    )
    with open(OUT_CSV, "w") as f:
        f.write(header)
        canonical_out.to_csv(f, index=False, float_format="%.6f")
    print(f"\nwrote {OUT_CSV}  ({len(canonical)} rows, "
          f"{int(canonical.index.min())}-{int(canonical.index.max())})")

    # Sensitivity figure
    print(f"\nGenerating sensitivity figure across {SENSITIVITY_SPLICE_YEARS}")
    plot_sensitivity(zanna, cheng, fair_mean, OUT_FIG)


if __name__ == "__main__":
    main()
