"""
apply_wong_weights_pulse3brick.py
=================================

Step 5(d) of the CO2/CH4 pulse->SLR / 3-BRICK-version study: compute per-cell
Wong (2025) importance weights for ONE Wong-weighted BRICK arm (pre93 or brick2).

This is the split-CSV adaptation of apply_wong_weights.py. It reuses that
module's core numerics verbatim (hetero_logl_ar1 Kalman filter, ess_fraction,
weighted_quantile, the Dangendorf/CSIRO loaders, load_posterior) and differs
ONLY in I/O:

  * The OLD script read one "paired CSV" whose trajectory columns were bare
    integer-strings ("1850".."2100"). Our Step-4 outputs SPLIT the arms, so the
    GMSL history (the l_FB input) lives in `{version}_baseline.csv` under columns
    named `slr_<year>` (1850..2300), each = 100*(gmsl[t] - gmsl[2000]) in cm,
    i.e. ALREADY re-referenced to year 2000 (verified: slr_2000 == 0).
  * Output is a SLIM per-cell weights file (key cols + l_FB,l_B,log_w,w_norm),
    not a fat augmented copy of the trajectories.

mengel is EQUAL-WEIGHTED (NO Wong) per the locked 2026-06-15 decision, so this
script is run for pre93 and brick2 only.

The likelihood, units (METERS), and 2000-baseline normalisation are IDENTICAL to
apply_wong_weights.py and to the Julia l_B scripts -- l_FB and l_B MUST be scored
against the same observed series (--obs), or (l_FB - l_B) is meaningless.

CLI
---
    --baseline    CSV  {version}_baseline.csv (slr_<year> trajectory cols)
    --version     STR  pre93 | brick2  (label only; drives default output name)
    --obs         STR  'dangendorf' (default) or 'csiro'  (MUST match the Julia l_B run)
    --obs-path    CSV  default data/observations/dangendorf_2024_gmsl.csv
    --posterior   CSV  the SAME posterior the cells' post_idx index into
                       (pre93 = the quarantined pre-#93 file; brick2 = data/MimiBRICK/...)
    --lB          CSV  outputs/brick_lB_per_post_{version}.csv (Julia, same --obs)
    --output      CSV  default outputs/wong_weights_{version}.csv
    --c           FLOAT or 'auto' (default auto-tune)
    --ess-target  FLOAT in (0,1]  ESS-fraction target for auto c (default 0.5)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse the canonical numerics from the sibling module (same dir).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_wong_weights import (  # noqa: E402
    hetero_logl_ar1,
    ess_fraction,
    weighted_quantile,
    load_dangendorf,
    load_csiro,
    load_posterior,
)

KEY_COLS = ["axis", "rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]
TRAJ_RE = re.compile(r"^slr_(\d{4})$")   # matches slr_1850..slr_2300, NOT slr_2100_cm


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--baseline", required=True,
                   help="{version}_baseline.csv with slr_<year> trajectory columns.")
    p.add_argument("--version", required=True, choices=["pre93", "brick2"],
                   help="Which Wong-weighted arm (label; drives default --output name).")
    p.add_argument("--obs", choices=["dangendorf", "csiro"], default="dangendorf",
                   help="Observed GMSL source; MUST match compute_lB_per_post_*.jl --obs.")
    p.add_argument("--obs-path", default="data/observations/dangendorf_2024_gmsl.csv")
    p.add_argument("--posterior", required=True,
                   help="Posterior the cells' post_idx index into (sd_gmsl/rho_gmsl).")
    p.add_argument("--lB", default=None,
                   help="Per-post baseline l_B (default outputs/brick_lB_per_post_{version}.csv).")
    p.add_argument("--output", default=None,
                   help="Slim per-cell weights CSV (default outputs/wong_weights_{version}.csv).")
    p.add_argument("--c", default="auto")
    p.add_argument("--ess-target", type=float, default=0.5)
    p.add_argument("--c-grid", default="0.0001,0.001,0.01,0.05,0.1,0.2,0.5,1.0,2.0,5.0")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    t_start = time.time()
    version = args.version
    lB_path = args.lB or f"outputs/brick_lB_per_post_{version}.csv"
    out_path = Path(args.output or f"outputs/wong_weights_{version}.csv")

    # ---------------------------------------------------------------
    # 1. Load baseline arm (l_FB trajectories), obs, posterior, l_B.
    # ---------------------------------------------------------------
    print(f"[{version}] load baseline: {args.baseline}", flush=True)
    base = pd.read_csv(args.baseline)
    n_rows = len(base)
    for k in KEY_COLS:
        assert k in base.columns, f"baseline CSV missing key column '{k}'"
    print(f"        n_rows = {n_rows:,}", flush=True)

    print(f"[{version}] load obs ({args.obs}): {args.obs_path}", flush=True)
    obs_all = (load_dangendorf(args.obs_path) if args.obs == "dangendorf"
               else load_csiro(args.obs_path))
    print(f"        obs years {obs_all.year.min()}-{obs_all.year.max()} ({len(obs_all)} rows)",
          flush=True)

    print(f"[{version}] load posterior: {args.posterior}", flush=True)
    posterior = load_posterior(args.posterior)
    assert {"sd_gmsl", "rho_gmsl"} <= set(posterior.columns), \
        "posterior missing sd_gmsl/rho_gmsl"
    print(f"        n_post = {len(posterior):,}", flush=True)

    print(f"[{version}] load l_B: {lB_path}", flush=True)
    lB_df = pd.read_csv(lB_path)
    assert {"post_idx", "l_B_gmsl"} <= set(lB_df.columns), \
        f"l_B file must have post_idx,l_B_gmsl; got {list(lB_df.columns)}"
    print(f"        n_lB = {len(lB_df):,}", flush=True)

    # ---------------------------------------------------------------
    # 2. Trajectory columns: slr_<year> ONLY (exclude slr_<year>_cm).
    # ---------------------------------------------------------------
    traj_year_by_col = {}
    for c in base.columns:
        mobj = TRAJ_RE.match(c)
        if mobj:
            traj_year_by_col[c] = int(mobj.group(1))
    assert traj_year_by_col, "no slr_<year> trajectory columns found in baseline CSV."
    traj_years_all = sorted(traj_year_by_col.values())
    print(f"[{version}] trajectory cols: slr_{traj_years_all[0]}..slr_{traj_years_all[-1]} "
          f"({len(traj_years_all)} years)", flush=True)

    # ---------------------------------------------------------------
    # 3. Observation arrays in METERS, referenced to year 2000.
    # ---------------------------------------------------------------
    if 2000 not in obs_all.year.values:
        raise RuntimeError(f"obs '{args.obs}' missing year 2000 — cannot re-baseline.")
    o2000 = obs_all.loc[obs_all.year == 2000].iloc[0]
    gmsl_m_2000, sigma_m_2000 = o2000.gmsl_m, o2000.sigma_m

    obs = obs_all[obs_all.year.isin(traj_years_all)].sort_values("year").reset_index(drop=True)
    obs_years = obs.year.values
    obs_delta = (obs.gmsl_m - gmsl_m_2000).values                     # m, delta-from-2000
    obs_sigma = np.sqrt(obs.sigma_m.values ** 2 + sigma_m_2000 ** 2)  # inflated 1-sigma
    print(f"[{version}] obs years used: {obs_years[0]}..{obs_years[-1]} ({len(obs_years)})",
          flush=True)

    # Column names for those overlap years, in the same order.
    col_by_year = {y: c for c, y in traj_year_by_col.items()}
    obs_cols = [col_by_year[y] for y in obs_years]

    # ---------------------------------------------------------------
    # 4. Modeled trajectories (n_rows, n_obs_years) in METERS (cm/100).
    # ---------------------------------------------------------------
    traj_m = base[obs_cols].to_numpy(dtype=np.float64) / 100.0
    if np.any(np.isnan(traj_m)):
        raise RuntimeError(f"{int(np.isnan(traj_m).sum())} NaNs in modeled trajectories; aborting.")

    # ---------------------------------------------------------------
    # 5. l_FB per row using each cell's OWN AR(1) nuisance params.
    #
    # post_idx CONVENTION: the Step-4 cells store post_idx 0-BASED (the driver
    # run_mimibrick_pulse_versioned.jl does post_idx_1b = post_i + 1 and writes
    # the 0-based post_i). load_posterior() (and the Julia l_B output) are
    # 1-BASED. So the 1-based posterior-member index = cell post_idx + 1. We do
    # all sd/rho lookups and the l_B merge on that +1 key, but KEEP the cell's
    # 0-based post_idx in the output so it pairs cleanly with the Step-6
    # marginal extractor (which keys on the cell's own 0-based post_idx).
    # ---------------------------------------------------------------
    sd_lookup = dict(zip(posterior.post_idx.values, posterior.sd_gmsl.values))
    rho_lookup = dict(zip(posterior.post_idx.values, posterior.rho_gmsl.values))
    post_idx0 = base.post_idx.values.astype(int)    # 0-based cell value
    post_idx1 = post_idx0 + 1                        # 1-based posterior-member index
    miss = sorted(set(post_idx1) - set(sd_lookup))
    if miss:
        raise RuntimeError(f"{len(miss)} (1-based) post_idx not in posterior (e.g. {miss[:5]}).")

    print(f"[{version}] computing l_FB for {n_rows:,} rows ...", flush=True)
    l_FB = np.empty(n_rows)
    t0 = time.time()
    for i in range(n_rows):
        pi = post_idx1[i]
        resid = obs_delta - traj_m[i, :]
        l_FB[i] = hetero_logl_ar1(resid, float(sd_lookup[pi]), float(rho_lookup[pi]), obs_sigma)
        if (i + 1) % 5000 == 0 or i + 1 == n_rows:
            el = time.time() - t0
            print(f"   {i+1:,}/{n_rows:,}  ({el:.1f}s, {(i+1)/el:.0f} rows/s)", flush=True)
    print(f"[{version}] l_FB: median={np.nanmedian(l_FB):.3f} "
          f"min={np.nanmin(l_FB):.3f} max={np.nanmax(l_FB):.3f} "
          f"-inf={int(np.isneginf(l_FB).sum())}", flush=True)

    # ---------------------------------------------------------------
    # 6. Merge l_B by 1-based post_idx; form diff = l_FB - l_B.
    # ---------------------------------------------------------------
    out = base[KEY_COLS].copy()
    out["l_FB"] = l_FB
    out["_post_idx_1b"] = post_idx1
    lB_m = lB_df.rename(columns={"l_B_gmsl": "l_B", "post_idx": "_post_idx_1b"})
    out = out.merge(lB_m, on="_post_idx_1b", how="left").drop(columns="_post_idx_1b")
    if out.l_B.isna().any():
        raise RuntimeError(f"{int(out.l_B.isna().sum())} rows have no l_B for their post_idx.")
    diff = (out.l_FB - out.l_B).to_numpy()
    print(f"[{version}] (l_FB - l_B): median={np.median(diff):.3f} "
          f"p5={np.percentile(diff,5):.3f} p95={np.percentile(diff,95):.3f}", flush=True)

    # ---------------------------------------------------------------
    # 7. Auto-tune c to ESS target (or fixed c), then weights.
    #
    # ess_fraction(c*diff) is monotonically DECREASING in c (1.0 at c=0 ->
    # 1/N as c->inf), so we bisect for the c that hits --ess-target EXACTLY,
    # rather than snapping to a coarse grid (the ESS curve is steep, so a grid
    # over/undershoots the 0.5 target badly). This is the Wong heuristic done
    # continuously.
    # ---------------------------------------------------------------
    if args.c == "auto":
        target = args.ess_target
        f_ess = lambda c: ess_fraction(c * diff)
        lo, hi = 0.0, 1e-6
        it = 0
        while f_ess(hi) > target and it < 200:
            hi *= 2.0
            it += 1
        if f_ess(hi) > target:
            print(f"[{version}] WARN: could not drive ESS below target; using c={hi:.5g}", flush=True)
            c_use = hi
        else:
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if f_ess(mid) > target:
                    lo = mid
                else:
                    hi = mid
                if abs(f_ess(mid) - target) < 1e-4:
                    break
            c_use = 0.5 * (lo + hi)
        print(f"[{version}] bisected c = {c_use:.6g}  (ESS/N target {target})", flush=True)
    else:
        c_use = float(args.c)
    print(f"[{version}] chosen c = {c_use:.6g}", flush=True)

    log_w = c_use * diff
    w = np.exp(log_w - np.max(log_w))
    w_norm = w / w.sum()
    ess = (w.sum() ** 2) / (w ** 2).sum()
    print(f"[{version}] final ESS = {ess:.1f} / {n_rows}  ({100*ess/n_rows:.1f}%)", flush=True)

    out["log_w"] = log_w
    out["w_norm"] = w_norm

    # ---------------------------------------------------------------
    # 8. Sanity: unweighted vs weighted TOTAL-SLR percentiles (baseline arm).
    # ---------------------------------------------------------------
    print(f"\n=== [{version}] baseline-arm TOTAL SLR: unweighted vs Wong-weighted (cm) ===",
          flush=True)
    print(f"{'metric':<14} {'p5_u':>8} {'p50_u':>8} {'p95_u':>8}   "
          f"{'p5_w':>8} {'p50_w':>8} {'p95_w':>8}", flush=True)
    for col in ["slr_2100_cm", "slr_2150_cm", "slr_2300_cm"]:
        if col not in base.columns:
            continue
        v = base[col].to_numpy()
        pu = np.percentile(v, [5, 50, 95])
        pw = weighted_quantile(v, w_norm, (0.05, 0.50, 0.95))
        print(f"{col:<14} {pu[0]:>8.2f} {pu[1]:>8.2f} {pu[2]:>8.2f}   "
              f"{pw[0]:>8.2f} {pw[1]:>8.2f} {pw[2]:>8.2f}", flush=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"\n[{version}] wrote {out_path}  ({n_rows:,} rows)", flush=True)
    print(f"[{version}] ESS_fraction={ess/n_rows:.4f}  c={c_use:.5f}  "
          f"elapsed={time.time()-t_start:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
