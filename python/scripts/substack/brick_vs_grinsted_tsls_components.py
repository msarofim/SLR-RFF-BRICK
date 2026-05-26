"""
brick_vs_grinsted_tsls_components.py
====================================

Compare our FaIR-v1.4.5 + BRICK (post-PR#93) pipeline's Transient Sea
Level Sensitivity (TSLS) — by component, by period — against the
Grinsted et al. 2022 (Earth's Future 10, e2022EF002696) reference
values for CMIP6 models and historical observations.

TSLS is defined (Grinsted & Christensen 2021, Ocean Science 17:181-186,
the paper that introduced the concept):

    dS/dt = TSLS · T + S_0          (eq. 2)

where T is GMST anomaly (here, relative to 1995-2014 to match Grinsted),
S is component SLR, and S_0 is the rate at zero anomaly (the intercept;
its sign gives the "balance temperature" — the temperature at which
that component would be in steady-state).

Two TSLS objects are computed for each component × period:

  1. BASELINE TSLS — cross-cell weighted linear regression of period-mean
     rate vs period-mean GMST across the LHS-10k ensemble. The slope is
     the TSLS for that component × period. This is the direct Grinsted
     methodological analog (his eq. 2; he regresses across CMIP6 models
     with model-temperature-match weights, we regress across LHS-10k
     cells with Wong importance weights).

  2. PULSE-MARGINAL TSLS — per-cell ratio of (period-mean Δrate) /
     (period-mean ΔT_pulse), where Δ = pulse - baseline arm. In linear
     response the intercept S_0 cancels in the difference, so the
     per-cell ratio IS the TSLS (no regression needed). We use the
     0.01-GtCO2 pulse arm to stay in the linear regime per
     project_pulse_size_findings.md (the 1-GtCO2 arm contaminates with
     pulse-induced AIS tipping).

Comparing baseline vs pulse-marginal TSLS in our own ensemble tests
linearity: equality means BRICK's pulse-marginal trajectory is just
TSLS-convolution of the baseline temperature impulse response, which is
exactly the linearization Grinsted assumes. Inequality flags
nonlinearity (e.g., AIS already tipping in baseline so the pulse rides
on top of a saturated component).

Comparing both to Grinsted 2022's published numbers tells us whether
our v1.4.5 BRICK + post-PR#93 calibration is consistent with
literature CMIP6 / observational estimates.

Inputs:
  outputs/brick_v145/brick_lhs10k_baseline.csv                (per-component, per-year)
  outputs/brick_v145/brick_lhs10k_pulse_co2_pos_001gt.csv     (paired pulse arm)
  outputs/brick_v145_slim/brick_lhs10k_baseline_to2300_weighted.csv  (just w_norm)
  ~/Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10k_baseline.npz
  ~/Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10k_pulse_co2_pos_001gt.npz

Outputs:
  outputs/substack/brick_vs_grinsted_tsls_components.{csv,png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

FAI  = Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI"
CUBE_BASE  = FAI / "fair_outputs/cubes_v145/cube_v145_lhs10k_baseline.npz"
CUBE_PULSE = FAI / "fair_outputs/cubes_v145/cube_v145_lhs10k_pulse_co2_pos_001gt.npz"
BRICK_BASE_CSV  = ROOT / "outputs/brick_v145/brick_lhs10k_baseline.csv"
BRICK_PULSE_CSV = ROOT / "outputs/brick_v145/brick_lhs10k_pulse_co2_pos_001gt.csv"
SLIM_WEIGHTS    = ROOT / "outputs/brick_v145_slim/brick_lhs10k_baseline_to2300_weighted.csv"

# ---- Methodological choices (explicit per CLAUDE.md) ----
PERIODS  = [(2016, 2050), (2051, 2100)]
GMST_BASELINE = (1995, 2014)      # Grinsted 2022 anomaly reference window
PULSE_SIZE_GTCO2 = 0.01           # FaIR v1.4.5 CO2 FFI input unit
N_BOOTSTRAP = 200                 # bootstrap regression CIs

# Map BRICK component prefix → (Grinsted label, plotting color)
COMPONENTS = [
    ("te",   "Steric",  "#1F77B4"),
    ("gis",  "GIS",     "#2CA02C"),
    ("ais",  "AIS",     "#D62728"),
    ("gsic", "GSIC",    "#FF7F0E"),
    ("gmsl", "GMSL",    "#7F7F7F"),   # synthetic = te+gis+ais+gsic (LWS excluded)
]

# Grinsted 2022 reference values (mm/yr/K). Numbers below are from the
# paper's abstract and main text (sections 4.1, 4.5, 4.6, 4.7) — bar
# values from Figure 10 that aren't quoted in the body text are marked
# np.nan and rendered as "—" in the plot.
GRINSTED = {
    # period: { component: { "model": (mu, sigma), "obs": (mu, sigma) } }
    (2016, 2050): {
        "te":   {"model": (2.1, 0.8),  "obs": (1.4, 0.5)},   # 2015-2050 model (sec 4.1)
        "gis":  {"model": (np.nan, np.nan), "obs": (0.4, 0.2)},
        "ais":  {"model": (np.nan, np.nan), "obs": (0.4, 0.2)},  # historical incl satellite
        "gsic": {"model": (2.8, 0.4),  "obs": (np.nan, np.nan)},  # GIC pre-2050
        "gmsl": {"model": (5.3, 1.0),  "obs": (3.3, 0.4)},
    },
    (2051, 2100): {
        "te":   {"model": (1.5, 0.2),  "obs": (1.4, 0.5)},
        "gis":  {"model": (0.8, 0.2),  "obs": (0.4, 0.2)},
        "ais":  {"model": (0.0, 0.3),  "obs": (0.4, 0.2)},
        "gsic": {"model": (0.7, 0.1),  "obs": (np.nan, np.nan)},
        "gmsl": {"model": (3.0, 0.4),  "obs": (3.3, 0.4)},
    },
}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def _load_cube_gmst(path: Path):
    """Return cells_meta (n,3), years (n_yr,), gmst (n_cells, n_yr)."""
    c = np.load(path, allow_pickle=True)
    return (np.asarray(c["cells_meta"], dtype=np.int64),
            np.asarray(c["years"], dtype=np.int64),
            np.asarray(c["gmst_traj"], dtype=np.float64))


def _component_year_block(df: pd.DataFrame, prefix: str, year_min: int, year_max: int) -> np.ndarray:
    """Return (n_cells, n_yr) matrix of component trajectories cm."""
    cols = [f"{prefix}_{y}" for y in range(year_min, year_max + 1)]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise RuntimeError(f"{prefix}: BRICK CSV missing {len(missing)} cols (e.g. {missing[:3]})")
    return df[cols].to_numpy(dtype=np.float64)


def _gmsl_no_lws(df: pd.DataFrame, year_min: int, year_max: int) -> np.ndarray:
    """Reconstruct GMSL ex-LWS as te + gis + ais + gsic per cell per year."""
    out = np.zeros((len(df), year_max - year_min + 1), dtype=np.float64)
    for pref in ("te", "gis", "ais", "gsic"):
        out += _component_year_block(df, pref, year_min, year_max)
    return out


def _period_rate(traj: np.ndarray, years: np.ndarray, lo: int, hi: int) -> np.ndarray:
    """Return per-cell (S(hi) - S(lo)) / (hi - lo), units = cm/yr → mm/yr * 10."""
    i_lo = int(np.where(years == lo)[0][0])
    i_hi = int(np.where(years == hi)[0][0])
    return (traj[:, i_hi] - traj[:, i_lo]) / (hi - lo) * 10.0   # cm/yr → mm/yr


def _period_mean(traj: np.ndarray, years: np.ndarray, lo: int, hi: int) -> np.ndarray:
    """Per-cell time-mean over inclusive [lo, hi]."""
    mask = (years >= lo) & (years <= hi)
    return traj[:, mask].mean(axis=1)


def _weighted_regression(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    """Weighted linear regression y ~ a + b*x. Returns (slope, intercept)."""
    w = w / w.sum()
    xbar = float(np.sum(w * x))
    ybar = float(np.sum(w * y))
    num = float(np.sum(w * (x - xbar) * (y - ybar)))
    den = float(np.sum(w * (x - xbar) ** 2))
    slope = num / den if den > 0 else np.nan
    intercept = ybar - slope * xbar
    return slope, intercept


def _bootstrap_slope_ci(x, y, w, n_boot=N_BOOTSTRAP, q=(0.05, 0.50, 0.95)) -> tuple[float, float, float]:
    n = len(x)
    rng = np.random.default_rng(2026)
    slopes = np.empty(n_boot)
    p = w / w.sum()
    for b in range(n_boot):
        idx = rng.choice(n, size=n, replace=True, p=p)
        slopes[b], _ = _weighted_regression(x[idx], y[idx], w[idx])
    p5, p50, p95 = np.quantile(slopes, q)
    return float(p5), float(p50), float(p95)


def _weighted_quantile(v, w, q):
    o = np.argsort(v); v, w = v[o], w[o]
    cw = np.cumsum(w); cw /= cw[-1]
    return float(v[np.searchsorted(cw, q)])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("[load] BRICK baseline:", BRICK_BASE_CSV)
    base = pd.read_csv(BRICK_BASE_CSV)
    print("[load] BRICK pulse:   ", BRICK_PULSE_CSV)
    pulse = pd.read_csv(BRICK_PULSE_CSV)
    print(f"  baseline rows {len(base):,}; pulse rows {len(pulse):,}")
    key_cols = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]
    base = base.sort_values(key_cols).reset_index(drop=True)
    pulse = pulse.sort_values(key_cols).reset_index(drop=True)
    if not (base[key_cols].to_numpy() == pulse[key_cols].to_numpy()).all():
        sys.exit("baseline / pulse key columns don't align after sort — cannot pair")

    print("[load] FaIR GMST cubes")
    bm, by, base_gmst = _load_cube_gmst(CUBE_BASE)
    pm, py, pulse_gmst = _load_cube_gmst(CUBE_PULSE)
    assert (bm == pm).all() and (by == py).all(), "cube key/year mismatch"
    cube_idx = {(int(r), int(c), int(s)): i for i, (r, c, s) in enumerate(bm)}
    cube_rows = np.array([cube_idx[(int(r), int(c), int(s))]
                          for r, c, s in base[["rff_idx","fair_cfg_idx","seed_idx"]].to_numpy()])
    base_gmst = base_gmst[cube_rows]
    pulse_gmst = pulse_gmst[cube_rows]
    print(f"  cube cells {len(bm):,}; aligned to BRICK CSV order")

    # ---- GMST anomaly relative to 1995-2014 ----
    anom_lo, anom_hi = GMST_BASELINE
    mask_anom = (by >= anom_lo) & (by <= anom_hi)
    base_anom_T  = _period_mean(base_gmst,  by, anom_lo, anom_hi)[:, None]
    pulse_anom_T = _period_mean(pulse_gmst, by, anom_lo, anom_hi)[:, None]
    base_gmst_anom  = base_gmst  - base_anom_T
    pulse_gmst_anom = pulse_gmst - pulse_anom_T   # each cell's own anomaly reference

    # ---- Wong w_norm from slim CSV (paired) ----
    print("[load] Wong w_norm from slim CSV")
    slim = pd.read_csv(SLIM_WEIGHTS, usecols=key_cols + ["w_norm"]).sort_values(key_cols).reset_index(drop=True)
    if not (slim[key_cols].to_numpy() == base[key_cols].to_numpy()).all():
        sys.exit("slim CSV doesn't align with BRICK CSV on keys")
    w = slim["w_norm"].to_numpy(dtype=np.float64)
    w = w / w.sum()

    # ---- iterate components × periods ----
    rows = []
    for prefix, label, _ in COMPONENTS:
        if prefix == "gmsl":
            traj_base  = _gmsl_no_lws(base,  by[0], by[-1])
            traj_pulse = _gmsl_no_lws(pulse, by[0], by[-1])
            cube_years = np.arange(by[0], by[-1] + 1)
        else:
            traj_base  = _component_year_block(base,  prefix, by[0], by[-1])
            traj_pulse = _component_year_block(pulse, prefix, by[0], by[-1])
            cube_years = np.arange(by[0], by[-1] + 1)

        for (lo, hi) in PERIODS:
            # Baseline TSLS: cross-cell regression of period-mean rate vs period-mean GMST anomaly
            T_base = _period_mean(base_gmst_anom, by, lo, hi)
            R_base = _period_rate(traj_base, cube_years, lo, hi)        # mm/yr
            slope_base, intercept_base = _weighted_regression(T_base, R_base, w)
            p5, p50, p95 = _bootstrap_slope_ci(T_base, R_base, w)

            # Pulse-marginal TSLS: per-cell (Δrate / ΔT) and importance-weighted median
            T_pulse = _period_mean(pulse_gmst_anom, by, lo, hi)
            R_pulse = _period_rate(traj_pulse, cube_years, lo, hi)
            dT = T_pulse - T_base
            dR = R_pulse - R_base
            mask = np.isfinite(dT) & np.isfinite(dR) & (np.abs(dT) > 1e-6)
            tsls_pulse_cells = dR[mask] / dT[mask]
            w_m = w[mask] / w[mask].sum()
            pulse_p5  = _weighted_quantile(tsls_pulse_cells, w_m, 0.05)
            pulse_p50 = _weighted_quantile(tsls_pulse_cells, w_m, 0.50)
            pulse_p95 = _weighted_quantile(tsls_pulse_cells, w_m, 0.95)

            g_model = GRINSTED.get((lo, hi), {}).get(prefix, {}).get("model", (np.nan, np.nan))
            g_obs   = GRINSTED.get((lo, hi), {}).get(prefix, {}).get("obs",   (np.nan, np.nan))

            rows.append({
                "component":          label,
                "period":             f"{lo}-{hi}",
                "brick_baseline_tsls":   slope_base,
                "brick_baseline_p5":     p5,
                "brick_baseline_p95":    p95,
                "brick_baseline_intercept_balance_K": -intercept_base / slope_base if slope_base else np.nan,
                "brick_pulse_tsls":      pulse_p50,
                "brick_pulse_p5":        pulse_p5,
                "brick_pulse_p95":       pulse_p95,
                "grinsted_model_mu":     g_model[0],
                "grinsted_model_sigma":  g_model[1],
                "grinsted_obs_mu":       g_obs[0],
                "grinsted_obs_sigma":    g_obs[1],
                "n_cells":               int(mask.sum()),
            })
    df = pd.DataFrame(rows)
    csv_out = OUT / "brick_vs_grinsted_tsls_components.csv"
    df.to_csv(csv_out, index=False)
    print(f"[save] {csv_out}")
    print("\n=== TSLS (mm/yr/K), BRICK v1.4.5 vs Grinsted 2022 ===")
    with pd.option_context("display.width", 200, "display.max_columns", 20,
                            "display.float_format", "{:.2f}".format):
        cols_show = ["component", "period",
                     "brick_baseline_tsls", "brick_pulse_tsls",
                     "grinsted_model_mu", "grinsted_obs_mu"]
        print(df[cols_show].to_string(index=False))

    # ---- plot: 2 panels, one per period; grouped bars ----
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)
    for ax, (lo, hi) in zip(axes, PERIODS):
        sub = df[df.period == f"{lo}-{hi}"].set_index("component")
        labels = [lbl for _, lbl, _ in COMPONENTS]
        x = np.arange(len(labels))
        width = 0.21
        for off, (col, mu_col, lo_col, hi_col, color) in enumerate([
            ("BRICK base.",  "brick_baseline_tsls", "brick_baseline_p5",  "brick_baseline_p95", "#1F4E79"),
            ("BRICK pulse",  "brick_pulse_tsls",    "brick_pulse_p5",     "brick_pulse_p95",    "#A6361C"),
        ]):
            y    = sub[mu_col].reindex(labels).to_numpy()
            ylo  = sub[lo_col].reindex(labels).to_numpy()
            yhi  = sub[hi_col].reindex(labels).to_numpy()
            # Clamp bootstrap CIs to be one-sided non-negative — for small
            # ensembles the bootstrap can land outside the weighted-regression
            # point estimate; we use max(0, ·) so matplotlib can render.
            err_lo = np.clip(y - ylo, 0, None)
            err_hi = np.clip(yhi - y, 0, None)
            ax.bar(x + (off - 1.5) * width, y, width, color=color, label=col,
                    yerr=[err_lo, err_hi], capsize=3, error_kw=dict(lw=0.8))
        # Grinsted model + obs
        gm = sub["grinsted_model_mu"].reindex(labels).to_numpy()
        gs = sub["grinsted_model_sigma"].reindex(labels).to_numpy()
        om = sub["grinsted_obs_mu"].reindex(labels).to_numpy()
        os_ = sub["grinsted_obs_sigma"].reindex(labels).to_numpy()
        ax.bar(x + 0.5 * width, gm, width, color="#888", label="Grinsted CMIP6",
                yerr=np.nan_to_num(gs), capsize=3, error_kw=dict(lw=0.8))
        ax.bar(x + 1.5 * width, om, width, color="#CCC", label="Grinsted obs",
                yerr=np.nan_to_num(os_), capsize=3, error_kw=dict(lw=0.8))
        ax.axhline(0, color="grey", lw=0.5)
        ax.set_xticks(x); ax.set_xticklabels(labels, rotation=0, fontsize=10)
        ax.set_title(f"{lo}-{hi}", fontsize=12, fontweight="bold", color="#1F4E79")
        ax.set_ylabel("TSLS  (mm/yr/K)", fontsize=10)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(loc="upper right", fontsize=8.5, framealpha=0.92)

    fig.suptitle("Transient Sea Level Sensitivity by component:\n"
                 "v1.4.5 BRICK (baseline & 0.01 GtCO₂ pulse-marginal) vs. Grinsted et al. 2022",
                 fontsize=12.5, fontweight="bold", color="#1F4E79", y=1.005)
    fig.text(0.5, -0.02,
              "Grinsted reference: Grinsted, Bamber, Bingham, Buzzard, Nias, Ng, Weeks (2022), "
              "Earth's Future 10, e2022EF002696, extending Grinsted & Christensen (2021), "
              "Ocean Science 17:181-186.  BRICK = MimiBRICK v1.0.1 post-PR#93; FaIR-calibrate v1.4.5; "
              "10,000-draw LHS ensemble.  Error bars: BRICK = bootstrap 5/95% on weighted regression; "
              "Grinsted = paper's stated ±1σ.",
              ha="center", va="top", fontsize=8, color="#444", wrap=True)
    fig.tight_layout()
    png_out = OUT / "brick_vs_grinsted_tsls_components.png"
    pdf_out = OUT / "brick_vs_grinsted_tsls_components.pdf"
    fig.savefig(png_out, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_out, bbox_inches="tight")
    plt.close(fig)
    print(f"[save] {png_out}")


if __name__ == "__main__":
    main()
