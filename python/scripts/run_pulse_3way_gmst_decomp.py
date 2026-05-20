"""
run_pulse_3way_gmst_decomp.py
=============================

Compute the 2-way Hawkins-Sutton decomposition of the marginal GMST response
to a 1 GtCO₂ pulse at 2030 — the GMST companion to run_pulse_4way_slr_decomp.

2-way decomposition over the FULL FaIR cube (rff × cfg):

  V_emi(t)  = Var over rff       of  E_cfg[ ΔGMST ]
  V_clim(t) = E over rff of Var_cfg[ ΔGMST ]

(No BRICK component — GMST is upstream of BRICK. No seed dimension in the
current cubes, so V_internal is structurally absent.)

We decompose over the full FaIR cube with equal weight per (rff, cfg) draw —
NOT the BRICK paired subset. The 500-cell BRICK subset under-samples the
841 FaIR configs (only ~10 RFFs have >1 cfg sampled), which would zero out
V_clim by construction. The full cube reflects honest emissions × climate
uncertainty propagation, independent of the BRICK-side importance weighting.

Inputs (on Torch):
  outputs/rff_baseline_stoch_to2300.npz   (gmst_traj_rff, years, unique_rffs)
  outputs/rff_pulse_stoch_to2300.npz      (same shape, +1 GtCO2 at 2030)

Output:
  outputs/plots/hawkins_sutton_gmst_3way_pulse.csv

Usage on Torch (login node, ~30-90 s wall):
  cd /scratch/ms17839/SLR-RFF-BRICK
  source /share/apps/anaconda3/2025.06/etc/profile.d/conda.sh
  conda activate /scratch/ms17839/SLR-RFF-BRICK/envs/fair
  python python/scripts/run_pulse_3way_gmst_decomp.py
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd


_TORCH = Path("/scratch/ms17839/SLR-RFF-BRICK")
ROOT = _TORCH if _TORCH.exists() else Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
PLOTS = OUT / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

BASELINE_CUBE  = OUT / "rff_baseline_stoch_to2300.npz"
PULSE_CUBE     = OUT / "rff_pulse_stoch_to2300.npz"

T_ANCHOR        = 2020
DECOMP_YEAR_LO  = 2020
DECOMP_YEAR_HI  = 2300


def main():
    for p in (BASELINE_CUBE, PULSE_CUBE):
        if not p.exists():
            sys.exit(f"Missing input: {p}")

    print(f"Loading FaIR cubes from {OUT}")
    nb  = np.load(BASELINE_CUBE)
    npz = np.load(PULSE_CUBE)
    years = nb["years"]
    Gb = nb["gmst_traj_rff"]
    Gp = npz["gmst_traj_rff"]
    print(f"  baseline shape: {Gb.shape}  dtype={Gb.dtype}")
    print(f"  pulse    shape: {Gp.shape}  dtype={Gp.dtype}")
    assert Gb.shape == Gp.shape, "baseline / pulse shape mismatch"
    n_yr = Gb.shape[-1]

    # ---- Build full-cube marginal -------------------------------------------
    # Cubes are (n_rff, n_cfg, n_yr) in the current run (no seed dim).
    if Gb.ndim != 3:
        sys.exit(f"Expected 3-D cube (rff, cfg, yr); got ndim={Gb.ndim}")
    D = Gp.astype(np.float64) - Gb.astype(np.float64)
    n_rff, n_cfg, _ = D.shape
    i_anchor = int(np.where(years == T_ANCHOR)[0][0])
    D = D - D[:, :, i_anchor:i_anchor + 1]
    print(f"  marginal cube: {D.shape}; anchored at {T_ANCHOR}")
    print(f"  decomposing over {n_rff} rff × {n_cfg} cfg = "
          f"{n_rff * n_cfg:,} draws per year")

    # ---- Decompose year-by-year --------------------------------------------
    # Equal weight per (rff, cfg) draw: vectorize across the rff axis as the
    # outer "emissions" factor and cfg axis as the inner "climate" factor.
    out_rows = []
    yrs = np.asarray(years, dtype=int)
    print("Decomposing per year...")
    t0 = time.time()
    for j in range(n_yr):
        y = int(yrs[j])
        if not (DECOMP_YEAR_LO <= y <= DECOMP_YEAR_HI):
            continue
        slab = D[:, :, j]                       # (n_rff, n_cfg)
        m_rff   = slab.mean(axis=1)             # E_cfg[ΔGMST | rff]
        grand   = m_rff.mean()
        V_emi   = float(m_rff.var(ddof=0))                          # Var_rff(m_rff)
        V_clim  = float(slab.var(axis=1, ddof=0).mean())            # E_rff[Var_cfg]

        V_total = V_emi + V_clim
        eps = max(V_total, 1e-30)

        # Empirical (equal-weight) percentiles across all rff×cfg draws.
        flat = slab.ravel()
        p5  = float(np.quantile(flat, 0.05))
        p50 = float(np.quantile(flat, 0.50))
        p95 = float(np.quantile(flat, 0.95))

        out_rows.append({
            "year": y,
            "V_total":     V_total,
            "V_emissions": V_emi,
            "V_climate":   V_clim,
            "V_internal":  0.0,
            "f_emissions": V_emi / eps,
            "f_climate":   V_clim / eps,
            "f_internal":  0.0,
            "mean":        float(grand),
            "p5": p5, "p50": p50, "p95": p95,
        })

        if y % 25 == 0:
            print(f"  {y}: V_tot={V_total:.4g}  "
                  f"f_emi={V_emi/eps:.2f}  f_clim={V_clim/eps:.2f}  "
                  f"mean={grand:+.5f}  ({time.time()-t0:.1f}s)", flush=True)

    out = pd.DataFrame(out_rows)
    out_csv = PLOTS / "hawkins_sutton_gmst_3way_pulse.csv"
    out.to_csv(out_csv, index=False)
    print(f"\nwrote {out_csv}  ({len(out)} years)")

    # Headline preview
    print("\nKey ΔGMST values (degC per 1 GtCO2 pulse, anchored at "
          f"{T_ANCHOR}):")
    for y in (2030, 2050, 2075, 2100, 2125, 2150, 2200, 2300):
        m = out[out["year"] == y]
        if not len(m):
            continue
        r = m.iloc[0]
        print(f"  {y}: mean={r['mean']:+.5f}  p5={r.p5:+.5f}  p50={r.p50:+.5f}  "
              f"p95={r.p95:+.5f}  "
              f"f_emi={r.f_emissions:.2f}  f_clim={r.f_climate:.2f}")


if __name__ == "__main__":
    main()
