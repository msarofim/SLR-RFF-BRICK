"""
compare_anova_decomp_stability.py
=================================

Compute the 4-way Hawkins-Sutton variance decomposition on the
ANOVA-stability ensemble (a different 400-RFF subset of the v145
10,000-RFF inventory) and compare to the existing ANOVA-18k variance
fractions. Tests whether the variance attribution on poster panels C/D
is robust to the specific 400 RFFs chosen.

If variance fractions agree to within ~3 pp on each axis, the existing
panels are well-anchored. A larger discrepancy would flag an under-sampling
concern.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
from hawkins_sutton import decompose_slr_4way

EXISTING = ROOT / "outputs" / "brick_v145_slim" / "brick_anova18k_baseline_to2300_weighted.csv"
NEW      = ROOT / "outputs" / "brick_anova_stab_baseline.csv"

T_ANCHOR = 2020
YEARS_REPORT = (2050, 2075, 2100, 2125, 2150, 2200, 2300)


def headline(df: pd.DataFrame, name: str) -> None:
    """Compute 4-way decomp at YEARS_REPORT; print f_emi/clim/int/brick + V_total."""
    print(f"\n=== {name}  ({len(df):,} rows, {df.rff_idx.nunique()} unique RFFs) ===")
    weights = "w_norm" if "w_norm" in df.columns else None
    decomp = decompose_slr_4way(df, list(YEARS_REPORT), t_anchor=T_ANCHOR,
                                  weights_col=weights)
    print(f"  {'year':>6}  {'V_tot':>8}  {'f_emi':>7} {'f_clim':>7} {'f_int':>7} {'f_brick':>8}  {'mean':>7}")
    for _, r in decomp.iterrows():
        print(f"  {int(r['year']):>4}  {r['V_total']:>8.2f}  "
              f"{r['f_emissions']:>7.3f} {r['f_climate']:>7.3f} "
              f"{r['f_internal']:>7.3f} {r['f_brick']:>8.3f}  {r['mean']:>7.2f}")
    return decomp


def slim_brick_csv(path: Path) -> pd.DataFrame:
    """Read a full BRICK CSV (slr_<y> + components) and yield the slim form
    needed by decompose_slr_4way: keys + 'w_norm' + bare-year SLR columns."""
    df = pd.read_csv(path)
    yrs = sorted(int(c[len("slr_"):]) for c in df.columns
                  if c.startswith("slr_") and c[len("slr_"):].isdigit())
    keys = ["rff_idx","fair_cfg_idx","seed_idx","post_idx"]
    slr_cols = [f"slr_{y}" for y in yrs]
    keep = keys + slr_cols
    if "w_norm" in df.columns:
        keep = keys + ["w_norm"] + slr_cols
    out = df[keep].rename(columns={f"slr_{y}": str(y) for y in yrs})
    return out


def main() -> None:
    print(f"Existing ANOVA-18k baseline-weighted:\n  {EXISTING}")
    existing = pd.read_csv(EXISTING)
    print(f"  rows={len(existing):,}, unique RFFs={existing.rff_idx.nunique()}, "
          f"w_norm={'w_norm' in existing.columns}")
    dec_ex = headline(existing, "EXISTING")

    print(f"\nNew 400-RFF stability cube:\n  {NEW}")
    if not NEW.exists():
        print(f"  Missing — submit & wait for Torch job, then re-run this script.")
        return
    raw_new = pd.read_csv(NEW)
    print(f"  rows={len(raw_new):,}, unique RFFs={raw_new.rff_idx.nunique()}")
    # The new BRICK CSV is unweighted (no Wong likelihood computed for this
    # 400-RFF set). For an apples-to-apples comparison we run BOTH ensembles
    # unweighted in the decomp.
    print("\n(Note: stability cube has no w_norm; running unweighted decomp on BOTH.)")
    # Recompute the existing decomp UNWEIGHTED for a fair comparison
    existing_unw = existing.drop(columns=["w_norm"]) if "w_norm" in existing.columns else existing
    dec_ex_unw = headline(existing_unw, "EXISTING (unweighted)")
    new = slim_brick_csv(NEW)
    dec_new = headline(new, "NEW STABILITY (unweighted)")

    print(f"\n=== Variance-fraction comparison (unweighted) ===")
    print(f"  {'year':>6}  | {'f_emi':>22} | {'f_clim':>22} | {'f_brick':>22}")
    print(f"  {'':>6}  | {'old   new   Δ':>22} | {'old   new   Δ':>22} | {'old   new   Δ':>22}")
    rec_ex = {int(r['year']): r for _, r in dec_ex_unw.iterrows()}
    rec_nw = {int(r['year']): r for _, r in dec_new.iterrows()}
    for y in YEARS_REPORT:
        if y not in rec_ex or y not in rec_nw:
            continue
        e, n = rec_ex[y], rec_nw[y]
        for f in ("f_emissions","f_climate","f_brick"):
            pass
        d_emi   = n['f_emissions'] - e['f_emissions']
        d_clim  = n['f_climate']   - e['f_climate']
        d_brick = n['f_brick']     - e['f_brick']
        print(f"  {y:>4}  | "
              f"{e['f_emissions']:>5.3f} {n['f_emissions']:>5.3f} {d_emi:>+5.3f} | "
              f"{e['f_climate']:>5.3f} {n['f_climate']:>5.3f} {d_clim:>+5.3f} | "
              f"{e['f_brick']:>5.3f} {n['f_brick']:>5.3f} {d_brick:>+5.3f}")

    print(f"\nSummary at 2100:")
    e100, n100 = rec_ex[2100], rec_nw[2100]
    print(f"  V_total: old={e100['V_total']:.2f} cm², new={n100['V_total']:.2f} cm²  "
          f"(ratio {n100['V_total']/e100['V_total']:.2f})")
    print(f"  Largest variance-fraction shift on any axis: "
          f"{max(abs(n100['f_emissions']-e100['f_emissions']), abs(n100['f_climate']-e100['f_climate']), abs(n100['f_brick']-e100['f_brick'])):.3f} pp")


if __name__ == "__main__":
    main()
