"""
build_v145_gmst_pulse_products.py
=================================

Build v1.4.5 replacements for the four legacy v1.4.1-era GMST pulse
products that pulse_responses_clean.py and pulse_hawkins_sutton.py read:

  1. co2_pulse_gmst_summary_v145.csv  — LHS-10k importance-weighted pulse-marginal
     GMST envelope (year, mean, p5, p50, p95) for 1-GtCO₂ CO₂ pulse at 2030.
  2. ch4_pulse_gmst_summary_v145.csv  — same for 1-Tg CH₄ pulse at 2030.
  3. hawkins_sutton_gmst_3way_pulse_v145.csv — 3-way variance decomposition
     of CO₂ pulse-marginal GMST over ANOVA-18k's (rff × cfg × seed) factorial.

Sources (all v1.4.5 calibration):
  LHS-10k baseline + CO₂ pulse cubes  (per-cell GMST trajectories)
  LHS-10k baseline + CH₄ pulse cubes
  ANOVA-18k baseline + CO₂ pulse cubes  (factorial structure for variance decomp)
  Wong importance weights from BRICK side at the same (rff, cfg, seed, post) cell

Per the climate-modeling skill's "GtC vs GtCO₂" check: FaIR v1.4.5 CO2 FFI
input unit is GtCO₂.  CH4 input unit is Tg CH4/yr.  Pulse sizes 0.01 GtCO₂
and 0.01 Tg CH4 respectively for the small-pulse arms used here.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

# ---- Paths ----
ROOT = Path(__file__).resolve().parents[2]
FAI  = Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI"
CUBES = FAI / "fair_outputs/cubes_v145"
META  = FAI / "fair_outputs/metadata_v145"

LHS_BASE_CUBE      = CUBES / "cube_v145_lhs10k_baseline.npz"
LHS_CO2_PULSE_CUBE = CUBES / "cube_v145_lhs10k_pulse_co2_pos_001gt.npz"
LHS_CH4_PULSE_CUBE = CUBES / "cube_v145_lhs10k_pulse_ch4_pos_001tg.npz"

ANOVA_BASE_CUBE      = CUBES / "cube_v145_anova18k_baseline.npz"
ANOVA_CO2_PULSE_CUBE = CUBES / "cube_v145_anova18k_pulse_co2_pos_1gt.npz"

LHS_METADATA   = META / "lhs10k_metadata_v145.csv"
ANOVA_METADATA = META / "anova18k_metadata_v145.csv"

# importance-weighted slim baseline carries `w_norm` per cell.
LHS_WONG_WEIGHTED = ROOT / "outputs/brick_v145_slim/brick_lhs10k_baseline_to2300_weighted.csv"

OUT = ROOT / "outputs"
OUT_SUBSTACK = OUT / "substack"
OUT_PLOTS    = OUT / "plots"
OUT_SUBSTACK.mkdir(parents=True, exist_ok=True)
OUT_PLOTS.mkdir(parents=True, exist_ok=True)

PULSE_SIZE_GTCO2 = 0.01    # CO₂ FFI pulse, FaIR v1.4.5 GtCO₂ input unit
PULSE_SIZE_TG_CH4 = 0.01   # CH4 pulse, FaIR v1.4.5 Tg CH4/yr input unit


# ---- Helpers ----
def _load_cube(path: Path):
    """Return (cells_meta, years, gmst_traj). cells_meta has shape (n_cells, 3)
    with columns (rff_idx, fair_cfg_idx, seed_idx)."""
    c = np.load(path, allow_pickle=True)
    return (np.asarray(c["cells_meta"], dtype=np.int64),
            np.asarray(c["years"], dtype=np.int64),
            np.asarray(c["gmst_traj"], dtype=np.float64))


def _weighted_quantile(v, w, q):
    o = np.argsort(v); v, w = v[o], w[o]
    cw = np.cumsum(w); cw /= cw[-1]
    return float(v[np.searchsorted(cw, q)])


# ---- LHS-10k pulse-marginal GMST envelopes ----
def build_lhs10k_envelope(pulse_cube: Path, pulse_size_unit: float, out_csv: Path,
                            unit_label: str) -> None:
    """Build the year-by-year importance-weighted pulse-marginal envelope.

    out_csv schema:  year, mean, p5, p50, p95   (°C per `unit_label`, e.g.
    per GtCO₂ or per Tg CH4)."""
    base_meta, yrs_b, base_gmst   = _load_cube(LHS_BASE_CUBE)
    pulse_meta, yrs_p, pulse_gmst = _load_cube(pulse_cube)
    assert (base_meta == pulse_meta).all(), "cells_meta mismatch between baseline and pulse"
    assert (yrs_b == yrs_p).all(), "years mismatch"

    # Marginal per cell per year, scaled to per-unit pulse magnitude.
    M = (pulse_gmst - base_gmst) / pulse_size_unit   # shape (n_cells, n_year)

    # Pull importance weights (joined on rff, cfg, seed, post). The cubes are flat
    # over (rff, cfg, seed); the slim weighted CSV has a w_norm per
    # (rff, cfg, seed, post) row. There's exactly one post per cell in
    # LHS-10k metadata, so we can map cells_meta -> w_norm directly.
    bw = pd.read_csv(LHS_WONG_WEIGHTED, usecols=["rff_idx","fair_cfg_idx","seed_idx","post_idx","w_norm"])
    key_to_w = {(r,c,s): w for r,c,s,_,w in
                  zip(bw.rff_idx, bw.fair_cfg_idx, bw.seed_idx, bw.post_idx, bw.w_norm)}
    w = np.array([key_to_w.get((int(r),int(c),int(s)), 0.0)
                   for r,c,s in base_meta])
    if (w == 0.0).any():
        n_zero = int((w == 0.0).sum())
        raise RuntimeError(f"{n_zero} cube cells had no matching w_norm in the slim weighted CSV")
    w /= w.sum()

    rows = []
    for j, y in enumerate(yrs_b):
        v = M[:, j]
        rows.append({
            "year": int(y),
            "mean": float(np.average(v, weights=w)),
            "p5":   _weighted_quantile(v, w, 0.05),
            "p50":  _weighted_quantile(v, w, 0.50),
            "p95":  _weighted_quantile(v, w, 0.95),
        })
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}  ({len(df)} years, unit: °C per {unit_label})")
    for y in (2050, 2100, 2150):
        r = df[df.year == y]
        if len(r):
            r0 = r.iloc[0]
            print(f"    {y}: mean={r0['mean']:.4e}  p5={r0.p5:.4e}  p50={r0.p50:.4e}  p95={r0.p95:.4e}  °C/{unit_label}")


# ---- ANOVA-18k 3-way variance decomp on GMST pulse-marginal ----
def build_anova_3way_decomp(pulse_cube: Path, pulse_size_unit: float, out_csv: Path,
                              unit_label: str, anchor_year: int = 2020) -> None:
    """3-way Hawkins-Sutton variance decomp of the GMST pulse-marginal
    over the ANOVA-18k factorial (rff × cfg × seed).  Output schema matches
    the legacy hawkins_sutton_gmst_3way_pulse.csv.
    """
    base_meta, yrs_b, base_gmst = _load_cube(ANOVA_BASE_CUBE)
    pulse_meta, yrs_p, pulse_gmst = _load_cube(pulse_cube)
    assert (base_meta == pulse_meta).all(), "ANOVA cells_meta mismatch"
    assert (yrs_b == yrs_p).all()

    M = (pulse_gmst - base_gmst) / pulse_size_unit   # (n_cells, n_year)
    i_anchor = int(np.where(yrs_b == anchor_year)[0][0])
    M = M - M[:, [i_anchor]]   # re-anchor to anchor_year = 0

    # Long-form: rff_idx, fair_cfg_idx, seed_idx, year, v
    rff  = base_meta[:, 0]
    cfg  = base_meta[:, 1]
    seed = base_meta[:, 2]

    # ANOVA-18k replication counts (400 RFFs × 15 cfgs × 3 seeds). The
    # nested-ANOVA decomp uses unbiased within-cell variance (ddof=1) AND
    # subtracts the propagated within-cell sampling-noise term from each
    # outer level — without this finite-replication correction, V_climate
    # is upward-biased by V_internal/n_seed (see 2026-05-26 fix).
    N_SEED, N_CFG = 3, 15

    rows = []
    for j, y in enumerate(yrs_b):
        v = M[:, j]
        df_y = pd.DataFrame({"rff": rff, "cfg": cfg, "seed": seed, "v": v})

        # Variance decomp: take expectations over inner axes, then variance
        # over outer axis. ddof=1 for unbiased estimator at every level.
        # E_seed of v given (rff, cfg)
        e_seed_rc = df_y.groupby(["rff","cfg"], sort=False).v.mean().reset_index()
        # Var_cfg of E_seed given rff  (raw)
        v_cfg_r = e_seed_rc.groupby("rff", sort=False).v.var(ddof=1)
        # E_cfg E_seed of v given rff
        e_cfg_seed_r = e_seed_rc.groupby("rff", sort=False).v.mean()
        # Var_seed of v given (rff, cfg)  →  V_internal (lowest level)
        v_seed_rc = df_y.groupby(["rff","cfg"], sort=False).v.var(ddof=1)

        V_internal = float(v_seed_rc.mean())
        # V_climate = E_r[Var_cfg(rc_means)] − V_internal/n_seed
        V_climate   = max(0.0, float(v_cfg_r.mean()) - V_internal / N_SEED)
        # V_emissions = Var_r(rff_means) − V_climate/n_cfg − V_internal/(n_cfg × n_seed)
        v_rff_raw = float(e_cfg_seed_r.var(ddof=1))
        V_emissions = max(0.0, v_rff_raw
                                - V_climate  /  N_CFG
                                - V_internal / (N_CFG * N_SEED))
        V_total     = V_emissions + V_climate + V_internal

        # Empirical percentiles of v across the full ensemble (informational)
        p5  = float(np.percentile(v, 5))
        p50 = float(np.percentile(v, 50))
        p95 = float(np.percentile(v, 95))
        mean = float(v.mean())
        rows.append({
            "year": int(y),
            "V_total": V_total,
            "V_emissions": V_emissions,
            "V_climate":   V_climate,
            "V_internal":  V_internal,
            "f_emissions": V_emissions / V_total if V_total > 0 else 0.0,
            "f_climate":   V_climate   / V_total if V_total > 0 else 0.0,
            "f_internal":  V_internal  / V_total if V_total > 0 else 0.0,
            "mean": mean, "p5": p5, "p50": p50, "p95": p95,
        })
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}  ({len(df)} years, anchor {anchor_year}, unit: °C per {unit_label})")
    for y in (2050, 2100, 2150):
        r = df[df.year == y]
        if len(r):
            r0 = r.iloc[0]
            print(f"    {y}: V_tot={r0.V_total:.3e}  f_emi={r0.f_emissions:.2f}  f_clim={r0.f_climate:.2f}  "
                  f"f_int={r0.f_internal:.2f}  mean={r0['mean']:.4e}")


def main():
    print("=== LHS-10k CO₂ pulse-marginal GMST envelope (per GtCO₂) ===")
    build_lhs10k_envelope(LHS_CO2_PULSE_CUBE, PULSE_SIZE_GTCO2,
                          OUT_SUBSTACK / "co2_pulse_gmst_summary_v145.csv", "GtCO₂")

    print("\n=== LHS-10k CH₄ pulse-marginal GMST envelope (per Tg CH₄) ===")
    build_lhs10k_envelope(LHS_CH4_PULSE_CUBE, PULSE_SIZE_TG_CH4,
                          OUT_SUBSTACK / "ch4_pulse_gmst_summary_v145.csv", "Tg CH4")

    print("\n=== ANOVA-18k CO₂ pulse-marginal 3-way GMST variance decomp ===")
    # 1-GtCO₂ pulse for ANOVA-18k (larger arm is well-anchored for variance)
    build_anova_3way_decomp(ANOVA_CO2_PULSE_CUBE, 1.0,
                              OUT_PLOTS / "hawkins_sutton_gmst_3way_pulse_v145.csv",
                              "GtCO₂", anchor_year=2020)


if __name__ == "__main__":
    main()
