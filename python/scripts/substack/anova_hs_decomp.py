"""
anova_hs_decomp.py
==================

MODEL-FREE Hawkins-Sutton variance decomposition of total ΔSLR from a balanced
crossed-factorial BRICK ensemble (built by build_anova_factorial_metadata.py +
run_mimibrick_flatcube.jl). No surrogate — the balanced design lets us read the
first-order (main-effect) variance of each factor directly as the variance of
its conditional mean, which is exactly the quantity the surrogate Group-Sobol
estimates. This is the model-free cross-check of the Sobol attribution.

Factors → H-S axes:
  rff_idx       -> emissions       (structural main effect)
  fair_cfg_idx  -> climate         (structural main effect)
  post_idx      -> brick           (structural main effect)
  seed_idx      -> internal        (within-cell across-seed variance — NOT a
                                    crossed main effect, which would ~vanish by
                                    averaging and mis-load internal into interactions)

Law-of-total-variance split (anchored ΔSLR = slr_t - slr_2020), per year t:
  cell = (rff, cfg, post);  average Y over the seed replicates within each cell.
  V_internal = mean over cells of Var_seed(Y|cell)        (irreducible noise)
  V_struct   = Var over cells of mean_seed(Y|cell)        (forced-response var)
  V_total    = V_struct + V_internal                      (exact, law of total var)
  V_F        = Σ_f (n_f/N) (mean_f - grand)^2  on the seed-averaged cells, for
               F in {rff, cfg, post}                       (structural main effects)
  interactions = V_struct - (V_rff + V_cfg + V_post)       (all 2-way+ structural)
  shares = {emissions,climate,brick,internal,interactions} / V_total  (sum=1)

Output (same schema as the Sobol per-axis CSVs, drops into the existing
renderers for a side-by-side):
  outputs/substack/shapley_hs_per_axis_total_slr_anova<TAG>.csv
    columns: year, internal, brick, climate, emissions, interactions
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "substack"
YEAR_LO, YEAR_HI, ANCHOR = 2020, 2150, 2020
FACTOR_AXIS = {"rff_idx": "emissions", "fair_cfg_idx": "climate",
               "post_idx": "brick", "seed_idx": "internal"}


def v_factor(seed_avg, factor, year_cols, grand):
    """Variance of the conditional mean over levels of `factor`, computed on the
    SEED-AVERAGED cells (one row per (rff,cfg,post)). = structural main effect."""
    g = seed_avg.groupby(factor)[year_cols]
    means = g.mean().to_numpy()                 # (n_levels, n_yr)
    counts = seed_avg.groupby(factor).size().to_numpy()[:, None]
    w = counts / counts.sum()
    return (w * (means - grand) ** 2).sum(axis=0)   # (n_yr,)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--brick-csv", default=None,
                    help="default outputs/brick_v145/brick_anova<TAG>_baseline.csv")
    a = ap.parse_args()
    brick_csv = Path(a.brick_csv) if a.brick_csv else (
        ROOT / "outputs" / "brick_v145" / f"brick_anova{a.tag}_baseline.csv")

    years = np.arange(YEAR_LO, YEAR_HI + 1)
    year_cols = [f"slr_{y}" for y in years]
    keep = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"] + year_cols
    df = pd.read_csv(brick_csv, usecols=lambda c: c in keep)

    # anchor to 2020
    anc = df[f"slr_{ANCHOR}"].to_numpy()
    M = df[year_cols].to_numpy(dtype=np.float64) - anc[:, None]
    dd = df[["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]].copy()
    dd[year_cols] = M

    # ---- law-of-total-variance split over the seed axis ----
    cell_keys = ["rff_idx", "fair_cfg_idx", "post_idx"]
    gcell = dd.groupby(cell_keys)[year_cols]
    seed_avg = gcell.mean().reset_index()                       # one row per cell
    within = gcell.var(ddof=1).to_numpy()                       # per-cell seed var
    v_internal = np.nanmean(within, axis=0)                     # mean over cells
    sa = seed_avg[year_cols].to_numpy()
    grand = sa.mean(axis=0)
    v_struct = sa.var(axis=0)                                   # forced-response var
    v_total = v_struct + v_internal                            # law of total variance

    v_rff = v_factor(seed_avg, "rff_idx", year_cols, grand)
    v_cfg = v_factor(seed_avg, "fair_cfg_idx", year_cols, grand)
    v_post = v_factor(seed_avg, "post_idx", year_cols, grand)
    v_inter_struct = np.clip(v_struct - (v_rff + v_cfg + v_post), 0.0, None)

    def frac(x):
        return np.where(v_total > 0, x / v_total, 0.0)
    out = pd.DataFrame({"year": years,
                        "internal": frac(v_internal), "brick": frac(v_post),
                        "climate": frac(v_cfg), "emissions": frac(v_rff),
                        "interactions": frac(v_inter_struct)})
    # consistency check: raw total variance vs law-of-total-variance sum
    raw_vtot = M.var(axis=0)
    i2150 = int(np.where(years == 2150)[0][0])
    print(f"  LoTV check @2150: V_struct+V_int={v_total[i2150]:.4g} vs raw Var={raw_vtot[i2150]:.4g} "
          f"(ratio {v_total[i2150]/max(raw_vtot[i2150],1e-30):.3f})")
    out_csv = OUT / f"shapley_hs_per_axis_total_slr_anova{a.tag}.csv"
    out.to_csv(out_csv, index=False)
    print(f"wrote {out_csv}  ({len(df):,} cells)")
    print("  landmark shares (model-free ANOVA):")
    for y in (2050, 2100, 2150):
        r = out[out.year == y].iloc[0]
        print(f"    {y}: emissions={r.emissions:.3f} climate={r.climate:.3f} "
              f"brick={r.brick:.3f} internal={r.internal:.3f} interactions={r.interactions:.3f}")

    # side-by-side vs Sobol if present
    sob = OUT / "shapley_hs_per_axis_total_slr_hybrid_tipping.csv"
    if sob.exists():
        s = pd.read_csv(sob)
        print("\n  vs Group-Sobol (note: Sobol is importance-weighted + has a tipping wedge):")
        for y in (2100, 2150):
            sr = s[s.year == y].iloc[0]; ar = out[out.year == y].iloc[0]
            print(f"    {y} emissions: ANOVA={ar.emissions:.3f}  Sobol={sr.emissions:.3f}")


if __name__ == "__main__":
    main()
