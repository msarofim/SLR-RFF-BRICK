"""
ch4_pulse_summary_brick_averaged.py
====================================

Rebuild the CH4 pulse SLR summary using BRICK-averaged per-cell marginals.

For each v5 cell (rff, cfg, seed), we now have 10 BRICK realizations of the
paired marginal SLR(CH4 pulse) − SLR(baseline) (1 paired + 9 augmented).
Averaging across the 10 BRICK posts per cell collapses BRICK-induced
per-cell scatter by √10 ≈ 3.2× before percentile aggregation across cells.
The resulting median + 5–95% band should be visibly smoother than the
single-BRICK-post-per-cell version in
`outputs/substack/ch4_pulse_slr_summary_lhs10k_0p01tg.csv`.

Outputs:
  outputs/substack/ch4_pulse_slr_summary_lhs10ks_0p01tg_brickavg.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT  = ROOT / "outputs" / "substack"
BRICK_DIR = ROOT / "outputs" / "brick_v145_lhs10ks"
SLIM_BASE = ROOT / "outputs/brick_v145_slim/brick_lhs10ks_baseline_to2300_weighted.csv"

ANCHOR = 2020
PULSE_SIZE_TG_CH4 = 0.01

YEARS = np.arange(1850, 2301)


def main():
    key_cols = ["rff_idx","fair_cfg_idx","seed_idx","post_idx"]
    print("[load] v5 baseline paired (10k cells, 1 post each) + importance weights")
    base_main = pd.read_csv(SLIM_BASE)
    # Bare-year cols in slim → rename to slr_<y> for consistency
    base_main = base_main.rename(columns={str(y): f"slr_{y}" for y in YEARS if str(y) in base_main.columns})

    print("[load] CH4 pulse paired (10k cells)")
    pulse_main = pd.read_csv(BRICK_DIR / "brick_lhs10ks_pulse_ch4_pos_001tg.csv",
                              usecols=key_cols + [f"slr_{y}" for y in YEARS])

    print("[load] baseline postaug (90k cells)")
    base_aug = pd.read_csv(BRICK_DIR / "brick_lhs10ks_baseline_postaugment.csv",
                            usecols=key_cols + [f"slr_{y}" for y in YEARS])
    print("[load] CH4 pulse postaug (90k cells)")
    pulse_aug = pd.read_csv(BRICK_DIR / "brick_lhs10ks_pulse_ch4_pos_001tg_postaugment.csv",
                             usecols=key_cols + [f"slr_{y}" for y in YEARS])

    # Pair the two augmentations row-for-row (same metadata used)
    assert (base_aug[key_cols].values == pulse_aug[key_cols].values).all(), \
        "augmentation rows mis-aligned between baseline and CH4 pulse"

    # Per-row marginal in the postaug (already paired by same post_idx)
    yr_cols = [f"slr_{y}" for y in YEARS]
    base_aug_anom = base_aug[yr_cols].to_numpy() - base_aug[f"slr_{ANCHOR}"].to_numpy()[:, None]
    pulse_aug_anom = pulse_aug[yr_cols].to_numpy() - pulse_aug[f"slr_{ANCHOR}"].to_numpy()[:, None]
    marg_aug = (pulse_aug_anom - base_aug_anom) / PULSE_SIZE_TG_CH4   # per Tg CH4

    # Same for the main paired arm (10k cells)
    base_main_sorted = base_main.sort_values(["rff_idx","fair_cfg_idx","seed_idx"]).reset_index(drop=True)
    pulse_main_sorted = pulse_main.sort_values(["rff_idx","fair_cfg_idx","seed_idx"]).reset_index(drop=True)
    assert (base_main_sorted[["rff_idx","fair_cfg_idx","seed_idx"]].values ==
             pulse_main_sorted[["rff_idx","fair_cfg_idx","seed_idx"]].values).all()
    base_main_anom = base_main_sorted[yr_cols].to_numpy() - base_main_sorted[f"slr_{ANCHOR}"].to_numpy()[:, None]
    pulse_main_anom = pulse_main_sorted[yr_cols].to_numpy() - pulse_main_sorted[f"slr_{ANCHOR}"].to_numpy()[:, None]
    marg_main = (pulse_main_anom - base_main_anom) / PULSE_SIZE_TG_CH4

    # Stack and group by cell (rff, cfg, seed) → average over the 10 BRICK posts
    keys_main = base_main_sorted[["rff_idx","fair_cfg_idx","seed_idx"]].copy()
    keys_aug = base_aug[["rff_idx","fair_cfg_idx","seed_idx"]].copy()
    all_keys = pd.concat([keys_main, keys_aug], ignore_index=True)
    all_marg = np.vstack([marg_main, marg_aug])
    print(f"[stack] {len(all_keys):,} (cell × post) rows total")

    # Per-cell mean marginal across the 10 posts (variance-reducing aggregation)
    cell_groups = all_keys.groupby(["rff_idx","fair_cfg_idx","seed_idx"])
    print(f"[stack] {len(cell_groups):,} unique cells, reps/cell min/max: "
          f"{cell_groups.size().min()}/{cell_groups.size().max()}")
    grp_keys = list(cell_groups.groups.keys())
    cell_mean = np.zeros((len(grp_keys), len(YEARS)))
    for k, (key, g) in enumerate(cell_groups):
        cell_mean[k] = all_marg[g.index].mean(axis=0)

    # Cell-level importance weight (from v5 slim)
    w_lut = base_main_sorted.set_index(["rff_idx","fair_cfg_idx","seed_idx"])["w_norm"].to_dict()
    cell_w = np.array([w_lut[k] for k in grp_keys])

    # Weighted percentiles across cells per year (per Tg CH4 units)
    def wq(values, q, w):
        order = np.argsort(values)
        v = values[order]; wo = w[order]
        cum = np.cumsum(wo) / wo.sum()
        return np.interp(q, cum, v)

    rows = []
    for iy, y in enumerate(YEARS):
        col = cell_mean[:, iy]
        mu = (col * cell_w).sum() / cell_w.sum()
        p5, p50, p95 = [wq(col, q, cell_w) for q in (0.05, 0.5, 0.95)]
        rows.append(dict(year=int(y), mean=mu, p5=p5, p50=p50, p95=p95))
    out_df = pd.DataFrame(rows)

    out_csv = OUT / "ch4_pulse_slr_summary_lhs10ks_0p01tg_brickavg.csv"
    out_df.to_csv(out_csv, index=False)
    print(f"\nwrote {out_csv}")

    # Quick noise comparison vs the original single-BRICK-post summary
    old = pd.read_csv(OUT / "ch4_pulse_slr_summary_lhs10k_0p01tg.csv")
    print(f"\n{'year':>4s} | {'old p50':>10s} {'new p50':>10s} | {'old p5-p95':>11s} {'new p5-p95':>11s}")
    for y in [2050, 2075, 2100, 2125, 2150]:
        on = old[old.year == y].iloc[0]
        nn = out_df[out_df.year == y].iloc[0]
        print(f"{y:>4d} | {on.p50:10.4e} {nn.p50:10.4e} | "
              f"{(on.p95-on.p5):11.4e} {(nn.p95-nn.p5):11.4e}")
    # Year-to-year wobble in the median (simple measure of noisiness)
    old_diff = old[(old.year >= 2050) & (old.year <= 2150)].p50.diff().abs().mean()
    new_diff = out_df[(out_df.year >= 2050) & (out_df.year <= 2150)].p50.diff().abs().mean()
    print(f"\nmean |Δp50| year-to-year 2050-2150: "
          f"old={old_diff:.3e}  new={new_diff:.3e}  ratio old/new={old_diff/new_diff:.2f}×")


if __name__ == "__main__":
    main()
