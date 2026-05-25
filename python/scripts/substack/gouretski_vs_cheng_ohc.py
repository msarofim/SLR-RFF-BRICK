"""
gouretski_vs_cheng_ohc.py
=========================

Headline diagnostic figure: the OHC calibration target that BRICK was tuned
against (Gouretski & Koltermann 2007, 0-3000m, 1953-1996) vs. modern Cheng
IAPv4.2 0-2000m reanalysis over the same window. SNEASY's RCP45 MAP
trajectory (BRICK's coupled climate-module output) overlaid for reference.

Headline numbers (1953-1996):
  Gouretski:     ΔOHC = +26.67 × 10²² J   (BRICK calibration target)
  Cheng IAPv4.2: ΔOHC = +13.50 × 10²² J   (modern ARGO-era reanalysis)
  SNEASY MAP:    ΔOHC = +33.04 × 10²² J   (BRICK's internal climate model)
  Ratio: Gouretski / Cheng ≈ 2.0×

This is the actual mismatch driving the SLR-RFF-BRICK pipeline's TE
undershoot when fed modern obs OHC: te_α was calibrated for Gouretski-scale
ΔOHC; modern Cheng is half that.

Inputs:
  ~/.julia/packages/MimiBRICK/bpCAF/data/calibration_data/ocean_heat_gouretski_3000m.csv
  data/observations/raw/IAPv4.2_OHC_estimate_update.txt
  ~/.julia/packages/MimiBRICK/bpCAF/data/model_data/sneasy_oceanheat_RCP45_1850_2300.csv

Output:
  outputs/substack/gouretski_vs_cheng_ohc.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
HOME = Path(os.path.expanduser("~"))
GOURETSKI_CSV = HOME / ".julia/packages/MimiBRICK/bpCAF/data/calibration_data/ocean_heat_gouretski_3000m.csv"
CHENG_TXT     = ROOT / "data/observations/raw/IAPv4.2_OHC_estimate_update.txt"
IGCC_CSV      = (ROOT / "data/observations/raw/igcc2024/"
                        "ClimateIndicator-data-2cd2409/data/earth_energy_imbalance/"
                        "earth_energy_imbalance.csv")
ZANNA_NC      = ROOT / "data/observations/raw/zanna2019_OHC_GF_1870_2018.nc"
FAIR_CSV      = ROOT / "data/observations/fair_mean_ohc.csv"
SNEASY_CSV    = HOME / ".julia/packages/MimiBRICK/bpCAF/data/model_data/sneasy_oceanheat_RCP45_1850_2300.csv"
OUT_DIR       = ROOT / "outputs/substack"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REF_YEAR_FOR_BASELINE = 1971  # all six products have 1971 → common anchor
BASELINE_HALFWIDTH = 5        # use [1966..1976] mean as baseline (11-yr window).
                              # Never single-year for noisy products like raw
                              # SNEASY MAP (±20 ZJ year-to-year noise) — a
                              # single-year baseline produces fictional offsets
                              # when overlaying smoothed curves derived from the
                              # same noisy series. See memory entry
                              # `feedback_multiyear_baseline.md`.
WINDOW_START, WINDOW_END = 1870, 2024  # Zanna's start through IGCC's end


def baseline_to_window(series_or_array, year_index, ref_year, halfwidth):
    """Return the mean of series[ref_year - halfwidth .. ref_year + halfwidth].

    Works for pandas Series (with index = year), Gouretski DataFrame, or a
    pair (year_array, value_array).
    """
    if isinstance(series_or_array, pd.Series):
        mask = (series_or_array.index >= ref_year - halfwidth) & \
               (series_or_array.index <= ref_year + halfwidth)
        return float(series_or_array.loc[mask].mean())
    # numpy path: year_index aligned with values
    mask = (year_index >= ref_year - halfwidth) & (year_index <= ref_year + halfwidth)
    return float(np.nanmean(series_or_array[mask]))


def load_gouretski(path: Path) -> pd.DataFrame:
    """1953-1996, units 10²² J, columns: year, heat_anomaly, std_dev."""
    df = pd.read_csv(path, skiprows=3)
    return df.set_index("year")


def load_cheng_annual(path: Path) -> pd.Series:
    """0-2000m, units 10²² J. Calendar-year mean of monthly."""
    cols = ["year","month","ohc0_700","smooth_ohc0_700","err_ohc0_700",
            "ohc700_2000","smooth_ohc700_2000","err_ohc700_2000",
            "ohc0_2000","smooth_ohc0_2000","err_ohc0_2000",
            "ohc2000_6000","smooth_ohc2000_6000","err_ohc2000_6000"]
    df = pd.read_csv(path, sep=r"\s+", comment="%", header=None,
                     names=cols, na_values="NaN")
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["year","month","ohc0_2000"])
    df["year"] = df["year"].astype(int)
    return df.groupby("year")["ohc0_2000"].mean()


def load_sneasy(path: Path) -> pd.Series:
    """SNEASY MAP OHC trajectory, units 10²² J."""
    return pd.read_csv(path).set_index("Year")["MAP Ocean Heat"]


def load_igcc(path: Path) -> tuple[pd.Series, pd.Series]:
    """IGCC 0-2000m OHC + propagated 1σ error, units 10²² J. Native ZJ × 0.1."""
    df = pd.read_csv(path)
    df["year"] = df["time"].astype(int)
    df = df.set_index("year")
    ohc = (df["ocean_0-700m"] + df["ocean_700-2000m"]) * 0.1
    err = np.sqrt(df["ocean_0-700m_error"]**2 + df["ocean_700-2000m_error"]**2) * 0.1
    return ohc, err


def load_zanna(path: Path) -> tuple[pd.Series, pd.Series]:
    """Zanna 2019 OHC_2000m + 1σ error, units 10²² J. Native ZJ × 0.1."""
    import xarray as xr
    ds = xr.open_dataset(path)
    year = ds["time"].values.astype(int)
    ohc = pd.Series(ds["OHC_2000m"].values * 0.1, index=year)
    err = pd.Series(ds["error_OHC_2000"].values * 0.1, index=year)
    return ohc, err


def load_fair(path: Path) -> pd.Series:
    """FaIR ensemble mean OHC, units 10²² J."""
    df = pd.read_csv(path)
    return df.set_index("year")["ohc_1e22J"]


def main() -> None:
    gouretski = load_gouretski(GOURETSKI_CSV)
    cheng     = load_cheng_annual(CHENG_TXT)
    sneasy    = load_sneasy(SNEASY_CSV)
    igcc_ohc, igcc_err = load_igcc(IGCC_CSV)
    zanna_ohc, zanna_err = load_zanna(ZANNA_NC)
    fair = load_fair(FAIR_CSV)

    # Baseline every curve to the mean over [REF_YEAR ± BASELINE_HALFWIDTH]
    # (11-year window centered on 1971). Single-year baselines on noisy data
    # cause smoothed overlays to read fictionally offset — see
    # `feedback_multiyear_baseline.md`.
    R, H = REF_YEAR_FOR_BASELINE, BASELINE_HALFWIDTH

    g_ref = float(gouretski.loc[(gouretski.index >= R - H) & (gouretski.index <= R + H),
                                "heat_anomaly"].mean())
    c_ref = baseline_to_window(cheng,     None, R, H)
    s_ref = baseline_to_window(sneasy,    None, R, H)
    i_ref = baseline_to_window(igcc_ohc,  None, R, H)
    z_ref = baseline_to_window(zanna_ohc, None, R, H)
    f_ref = baseline_to_window(fair,      None, R, H)

    g_y = gouretski.index.to_numpy()
    g_mean = gouretski["heat_anomaly"].to_numpy() - g_ref
    g_std  = gouretski["std_dev"].to_numpy()

    c_y = cheng.index.to_numpy()
    c_mean = cheng.to_numpy() - c_ref

    s_y = sneasy.index.to_numpy()
    s_mean = sneasy.to_numpy() - s_ref

    i_y = igcc_ohc.index.to_numpy()
    i_mean = igcc_ohc.to_numpy() - i_ref
    i_std  = igcc_err.to_numpy()

    z_y = zanna_ohc.index.to_numpy()
    z_mean = zanna_ohc.to_numpy() - z_ref
    z_std  = zanna_err.to_numpy()

    f_y = fair.index.to_numpy()
    f_mean = fair.to_numpy() - f_ref

    # Window mask
    g_mask = (g_y >= WINDOW_START) & (g_y <= WINDOW_END)
    c_mask = (c_y >= WINDOW_START) & (c_y <= WINDOW_END)
    s_mask = (s_y >= WINDOW_START) & (s_y <= WINDOW_END)
    i_mask = (i_y >= WINDOW_START) & (i_y <= WINDOW_END)
    z_mask = (z_y >= WINDOW_START) & (z_y <= WINDOW_END)
    f_mask = (f_y >= WINDOW_START) & (f_y <= WINDOW_END)

    # ΔOHC over 1971-2018 (Zanna's modern end) for all products that cover it
    def delta_at(s, beg, end):
        try:
            return float(s.loc[end] - s.loc[beg])
        except KeyError:
            return float("nan")
    z_delta_1971_2018 = delta_at(zanna_ohc, 1971, 2018)
    g_delta_1971_1996 = delta_at(gouretski["heat_anomaly"], 1971, 1996)
    c_delta_1971_2018 = delta_at(cheng, 1971, 2018)
    i_delta_1971_2018 = delta_at(igcc_ohc, 1971, 2018)
    f_delta_1971_2018 = delta_at(fair, 1971, 2018)
    s_delta_1971_2018 = delta_at(sneasy, 1971, 2018)
    # ΔOHC over 1900-2018 — the load-bearing window for BRICK ΔTE
    # (BRICK posterior te_α 0.057 implies ΔTE(1900-2018) = 0.0036·ΔOHC; verified
    # to 0.5% across Tony-mode, FaIR-mean, Zanna+Cheng, and Zanna+IGCC inputs).
    f_delta_1900_2018 = delta_at(fair, 1900, 2018)
    i_delta_1900_2018 = delta_at(igcc_ohc, 1900, 2018)
    z_delta_1900_2018 = delta_at(zanna_ohc, 1900, 2018)
    s_delta_1900_2018 = delta_at(sneasy, 1900, 2018)
    # Original Gouretski-window ΔOHC for the inset comparison
    g_delta_5396 = delta_at(gouretski["heat_anomaly"], 1953, 1996)
    c_delta_5396 = delta_at(cheng, 1953, 1996)
    s_delta_5396 = delta_at(sneasy, 1953, 1996)

    # --- plot ----
    fig, ax = plt.subplots(figsize=(12, 6.5))

    # Zanna long-term obs reconstruction (1870-2018) + ±1σ band
    ax.fill_between(z_y[z_mask], (z_mean - z_std)[z_mask], (z_mean + z_std)[z_mask],
                    color="#1B7837", alpha=0.12)
    ax.plot(z_y[z_mask], z_mean[z_mask], color="#1B7837", lw=2.2,
            label="Zanna 2019 (0-2000m) — long-term obs reconstruction")

    # Gouretski (BRICK calibration target) + ±1σ band — 1953-1996 only
    ax.fill_between(g_y[g_mask], (g_mean - g_std)[g_mask], (g_mean + g_std)[g_mask],
                    color="#A6361C", alpha=0.15)
    ax.plot(g_y[g_mask], g_mean[g_mask], color="#A6361C", lw=2.4, marker="o",
            markersize=4, label="Gouretski 2007 (0-3000m) — BRICK calibration target")

    # Cheng IAPv4.2 (light, since it's the current pipeline default we're replacing)
    ax.plot(c_y[c_mask], c_mean[c_mask], color="#5AAE61", lw=1.6,
            linestyle=":", label="Cheng IAPv4.2 (0-2000m) — modern reanalysis")

    # IGCC ±1σ band — Palmer/von Schuckmann multi-product
    ax.fill_between(i_y[i_mask], (i_mean - i_std)[i_mask], (i_mean + i_std)[i_mask],
                    color="#7A1A8B", alpha=0.18)
    ax.plot(i_y[i_mask], i_mean[i_mask], color="#7A1A8B", lw=2.2, marker="^",
            markersize=3, label="IGCC 2024 (0-2000m) — multi-product compilation")

    # FaIR ensemble mean (our cube)
    ax.plot(f_y[f_mask], f_mean[f_mask], color="#E08214", lw=2.0,
            label="FaIR ensemble mean (our LHS-10k cube)")

    # SNEASY MAP (BRICK's internal climate) — raw at low alpha to keep the
    # ±20 ZJ year-to-year noise visible, plus an 11-year centered running mean
    # so the trend is comparable to FaIR/IGCC at-a-glance.
    sneasy_smooth = pd.Series(sneasy.values, index=s_y).rolling(
        window=11, center=True, min_periods=6
    ).mean().values - s_ref
    ax.plot(s_y[s_mask], s_mean[s_mask], color="#1F4E79", lw=0.7,
            linestyle="-", alpha=0.30,
            label="SNEASY MAP RCP45 (raw, annual)")
    ax.plot(s_y[s_mask], sneasy_smooth[s_mask], color="#1F4E79", lw=2.0,
            linestyle="--", alpha=0.95,
            label="SNEASY MAP RCP45 (11-yr running mean) — BRICK's internal climate")

    ax.axhline(0, color="grey", linewidth=0.6)
    ax.axvspan(REF_YEAR_FOR_BASELINE - BASELINE_HALFWIDTH,
               REF_YEAR_FOR_BASELINE + BASELINE_HALFWIDTH,
               color="grey", alpha=0.08, lw=0)
    ax.axvline(REF_YEAR_FOR_BASELINE, color="grey", linewidth=0.4, linestyle=":")
    ax.set_xlim(WINDOW_START - 1, WINDOW_END + 1)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel(f"OHC anomaly (10²² J), rel. "
                  f"{REF_YEAR_FOR_BASELINE - BASELINE_HALFWIDTH}-"
                  f"{REF_YEAR_FOR_BASELINE + BASELINE_HALFWIDTH} mean",
                  fontsize=11)
    ax.set_title("Ocean heat content: BRICK calibration target, modern products, "
                 "and model trajectories",
                 fontsize=12, fontweight="bold", color="#1F4E79")
    ax.grid(alpha=0.3, linewidth=0.5)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)

    # Headline ΔOHC numbers in an inset box
    table = (
        f"ΔOHC 1900-2018 (10²² J)  ← drives BRICK ΔTE:\n"
        f"  SNEASY MAP:        +{s_delta_1900_2018:5.2f}  (Tony-mode input)\n"
        f"  FaIR (our cube):   +{f_delta_1900_2018:5.2f}\n"
        f"  IGCC 2024:         +{i_delta_1900_2018:5.2f}\n"
        f"  Zanna 2019:        +{z_delta_1900_2018:5.2f}\n"
        "\n"
        f"ΔOHC 1971-2018 (10²² J):\n"
        f"  Zanna 2019:        +{z_delta_1971_2018:5.2f}\n"
        f"  Cheng IAPv4.2:     +{c_delta_1971_2018:5.2f}\n"
        f"  IGCC 2024:         +{i_delta_1971_2018:5.2f}\n"
        f"  FaIR (our cube):   +{f_delta_1971_2018:5.2f}\n"
        f"  SNEASY MAP:        +{s_delta_1971_2018:5.2f}\n"
        "\n"
        f"All curves rebaselined to 1966-1976 mean\n"
        f"(11-yr window; avoids single-year baseline\n"
        f"artifacts on noisy raw SNEASY).\n"
        f"SNEASY runs hot pre-1971 vs all obs-anchored\n"
        f"products; that's where the BRICK ΔTE gap\n"
        f"(Tony-mode 2.7 cm vs obs 1.6-1.9 cm) lives."
    )
    ax.text(0.985, 0.02, table, transform=ax.transAxes,
            fontsize=8.5, verticalalignment="bottom",
            horizontalalignment="right", family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor="grey", alpha=0.92))

    fig.tight_layout()
    out_png = OUT_DIR / "gouretski_vs_cheng_ohc.png"
    out_pdf = OUT_DIR / "gouretski_vs_cheng_ohc.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")
    print(f"wrote {out_pdf}")

    # Diagnostic print
    print(f"\nΔOHC 1971-2018 (10²² J):")
    print(f"  Zanna 2019:    +{z_delta_1971_2018:.2f}")
    print(f"  Cheng IAPv4.2: +{c_delta_1971_2018:.2f}")
    print(f"  IGCC 2024:     +{i_delta_1971_2018:.2f}")
    print(f"  FaIR (cube):   +{f_delta_1971_2018:.2f}")
    print(f"  SNEASY MAP:    +{s_delta_1971_2018:.2f}")
    print(f"\nΔOHC 1953-1996 (Gouretski window):")
    print(f"  Gouretski:     +{g_delta_5396:.2f}")
    print(f"  Cheng IAPv4.2: +{c_delta_5396:.2f}")
    print(f"  SNEASY MAP:    +{s_delta_5396:.2f}")


if __name__ == "__main__":
    main()
