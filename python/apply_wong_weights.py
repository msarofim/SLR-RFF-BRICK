"""
apply_wong_weights.py
=====================

Apply Wong (2025) importance weights to a MimiBRICK paired ensemble.

Wong's "Vehicle SLR" paper (Eqs 1-3) re-weights paired FaIR-BRICK draws by
the ratio of (i) the historical-fit log-likelihood of the FaIR-BRICK
trajectory and (ii) the historical-fit log-likelihood of the same BRICK
posterior member run with BRICK's default (non-FaIR) forcing:

    log(w_i)    = c · ( l(theta_i, FB) - l(theta_i, B) )       # Wong Eq 1
    W_i         = exp( log(w_i) - max(log(w_i)) )              # max-shift for stability
    W_i_norm    = W_i / sum(W_i)                               # normalise

l_FB is computed here from each row's saved GMSL trajectory in the paired
CSV. l_B is computed once per BRICK posterior member by the companion
Julia script `julia/compute_lB_per_post.jl`, which we read in and merge.

Per Wong's paper, we use ONLY the GMSL channel of BRICK's heteroscedastic
AR(1) likelihood (see MimiBRICK source
`src/calibration/create_log_posteriors/create_log_posterior_brick.jl` and
`src/calibration/calibration_helper_functions.jl::hetero_logl_ar1`):

    cov_matrix = sigma^2 / (1 - rho^2) * rho^|t_i - t_j|  +  diag(eps_t^2)
    log L      = log-pdf of MvNormal(0, cov_matrix) at the residuals

where sigma=sd_gmsl and rho=rho_gmsl are the posterior member's own AR(1)
nuisance parameters and eps_t is the per-year observed-GMSL 1-sigma (from
Dangendorf et al. 2024 by default; CSIRO Recons supported as a legacy
fallback via --obs csiro).

UNITS DECISION
--------------
BRICK's native GMSL unit is METERS, and sd_gmsl in the posterior CSV is in
meters (typical magnitude ~0.003 m). To keep the likelihood semantics
identical to BRICK's calibrator and identical between l_FB (here) and l_B
(Julia script), we evaluate the AR(1) likelihood entirely in METERS.
The paired CSV's year columns store `100 * (gmsl[t] - gmsl[2000])` in cm,
so we divide by 100 to get a m-delta-from-2000. CSIRO observations are
loaded as mm and divided by 1000 to m, then re-referenced to year 2000.

BASELINE NORMALISATION
----------------------
The paired CSV normalises modeled gmsl to year 2000. We re-reference the
observed series to year 2000 as well. This differs from BRICK's
calibration default (1961-1990 mean), but residuals against a common
baseline are what matter for the AR(1) likelihood, and the Julia l_B
script applies the SAME 2000-baseline normalisation, so l_FB and l_B are
on identical footing.

IMPORTANT: l_FB and l_B MUST be computed against the SAME observed series,
or their difference (l_FB - l_B) is meaningless. If you change --obs here,
re-run `julia/compute_lB_per_post.jl --obs <same>` first, otherwise the
weights are nonsense.

CLI
---
    --paired       CSV  outputs/brick_paired_*.csv  (trajectories included)
    --obs          STR  'dangendorf' (default) or 'csiro'
    --obs-path     CSV  obs CSV.  Default: data/observations/dangendorf_2024_gmsl.csv
                        (dangendorf) or data/calibration/CSIRO_Recons_gmsl_yr_2015.csv (csiro)
    --posterior    CSV  parameters_subsample_brick.csv
    --lB           CSV  outputs/brick_lB_per_post.csv  (from Julia script — same --obs!)
    --output       CSV  augmented paired CSV with l_FB, l_B, log_w, w_norm
    --c            FLOAT or "auto" (default auto-tune)
    --ess-target   FLOAT in (0,1]  effective sample size target as fraction of N (default 0.5)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve
from scipy.stats import multivariate_normal


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--paired",     default="outputs/brick_paired_N2000.csv",
                   help="Paired ensemble CSV with year-by-year trajectories.")
    p.add_argument("--obs", choices=["dangendorf", "csiro"], default="dangendorf",
                   help="Observed GMSL source (default: dangendorf 2024). "
                        "Whatever you pick here MUST match what was used by "
                        "compute_lB_per_post.jl to produce --lB, otherwise "
                        "the weights are meaningless.")
    p.add_argument("--obs-path", default=None,
                   help="Path to obs CSV.  Defaults: "
                        "data/observations/dangendorf_2024_gmsl.csv (dangendorf) "
                        "or data/calibration/CSIRO_Recons_gmsl_yr_2015.csv (csiro).")
    p.add_argument("--posterior",  default="data/MimiBRICK/parameters_subsample_brick.csv",
                   help="BRICK posterior subsample CSV with sd_gmsl/rho_gmsl columns.")
    p.add_argument("--lB",         default="outputs/brick_lB_per_post.csv",
                   help="Per-posterior baseline log-likelihoods (from compute_lB_per_post.jl).")
    p.add_argument("--output",     default="outputs/brick_paired_N2000_weighted.csv",
                   help="Augmented paired CSV with weight columns appended.")
    p.add_argument("--c",          default="auto",
                   help="Wong scaling constant 'c'. 'auto' sweeps a small grid and "
                        "picks the c whose ESS fraction is closest to --ess-target.")
    p.add_argument("--ess-target", type=float, default=0.5,
                   help="Target ESS fraction for auto c-tuning (default 0.5).")
    p.add_argument("--c-grid",     default="0.0001,0.001,0.01,0.05,0.1,0.2,0.5,1.0,2.0,5.0",
                   help="Comma-separated c grid for auto-tuning. The right c "
                        "depends on the magnitude of (l_FB - l_B) diffs; if all "
                        "ESS=100%, try a larger grid. For GMSL-only likelihood "
                        "with our paired ensemble, c~0.1-1.0 typically targets ESS=0.5.")
    return p.parse_args()


# -----------------------------------------------------------------------------
# Loaders
# -----------------------------------------------------------------------------
def load_csiro(path: str) -> pd.DataFrame:
    """
    Load CSIRO Recons GMSL: 9 header lines (each starting with '#'), then a
    header row `Time, GMSL (mm), GMSL 1-sigma uncertainty (mm)` followed by
    rows from ~1880.5 onward.

    Returns DataFrame with integer-year index and columns gmsl_m, sigma_m
    (both in meters).
    """
    df = pd.read_csv(path, skiprows=9)
    # Defensive: the column names may carry trailing spaces in some releases
    df.columns = [c.strip() for c in df.columns]
    # Time stamps are half-years (e.g. 1880.5); BRICK floors to int.
    df["year"] = np.floor(df["Time"].values).astype(int)
    df["gmsl_m"]  = df["GMSL (mm)"].astype(float) / 1000.0
    df["sigma_m"] = df["GMSL 1-sigma uncertainty (mm)"].astype(float) / 1000.0
    return df[["year", "gmsl_m", "sigma_m"]].reset_index(drop=True)


def load_dangendorf(path: str) -> pd.DataFrame:
    """
    Load Dangendorf et al. 2024 GMSL reconstruction (ESSD 16, 3471).

    Expected schema (from python/download_obs.py): columns
        year (int), value (mm), sigma (mm), value_lower (mm), value_upper (mm)
    `sigma` is approximated from the 90% interval via (upper-lower)/3.29.

    Returns DataFrame with integer-year column and gmsl_m, sigma_m (meters).
    """
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    if not {"year", "value", "sigma"}.issubset(df.columns):
        raise RuntimeError(
            f"Dangendorf CSV missing expected columns; got {list(df.columns)}.  "
            f"Re-run python/download_obs.py to produce a fresh dangendorf_2024_gmsl.csv.")
    df["year"] = df["year"].astype(int)
    df["gmsl_m"]  = df["value"].astype(float) / 1000.0
    df["sigma_m"] = df["sigma"].astype(float) / 1000.0
    return df[["year", "gmsl_m", "sigma_m"]].reset_index(drop=True)


def load_posterior(path: str) -> pd.DataFrame:
    """Load BRICK posterior. Adds a 1-based post_idx column to match the
    Julia-side convention used in the paired CSV."""
    post = pd.read_csv(path)
    # post_idx is the 1-based row index (Julia 1-indexing matches what
    # run_mimibrick_paired_seeded.jl saved out).
    post = post.reset_index(drop=True)
    post["post_idx"] = np.arange(1, len(post) + 1)
    return post


# -----------------------------------------------------------------------------
# AR(1) likelihood (BRICK's hetero_logl_ar1 ported to numpy)
# -----------------------------------------------------------------------------
def hetero_logl_ar1(residuals: np.ndarray,
                    sigma: float,
                    rho: float,
                    obs_sigma: np.ndarray) -> float:
    """
    Heteroscedastic AR(1) Gaussian log-likelihood via Kalman filter.

    Mathematically equivalent (to floating-point precision) to:
        cov_matrix = sigma^2 / (1 - rho^2) * rho^|t_i - t_j|  +  diag(obs_sigma_t^2)
        return logpdf(MvNormal(cov_matrix), residuals)

    Implementation uses the equivalent state-space representation:
        state:       r_t = rho * r_{t-1} + epsilon_t,  epsilon ~ N(0, sigma^2)
        observation: y_t = r_t + eta_t,                eta ~ N(0, obs_sigma_t^2)
    The marginal Gaussian over (y_1..y_n) has exactly the cov_matrix above,
    so the Kalman filter's prediction-error decomposition gives the same
    log-likelihood, but in O(n) rather than O(n^3) operations.

    Parameters and return identical to the prior MvNormal version. ~5000x
    faster on n=134 observation years.
    """
    n = len(residuals)
    if n == 0:
        return 0.0
    if abs(rho) >= 1.0:
        return -np.inf  # non-stationary, posterior member rejected
    proc_var = sigma * sigma
    # State distribution at t=1 is stationary marginal of AR(1).
    state_mean = 0.0
    state_var  = proc_var / (1.0 - rho * rho)
    loglik = 0.0
    log2pi = np.log(2.0 * np.pi)
    for t in range(n):
        # Predicted observation given y_1..y_{t-1}:
        obs_var_t = obs_sigma[t]
        pred_var  = state_var + obs_var_t * obs_var_t
        innov     = residuals[t] - state_mean
        # Numerical guard.
        if pred_var <= 0 or not np.isfinite(pred_var):
            return -np.inf
        loglik   += -0.5 * (log2pi + np.log(pred_var) + innov * innov / pred_var)
        # Filter update given y_t (Kalman gain).
        K = state_var / pred_var
        state_mean = state_mean + K * innov
        state_var  = (1.0 - K) * state_var
        # Propagate to t+1.
        state_mean = rho * state_mean
        state_var  = rho * rho * state_var + proc_var
    return float(loglik)


# -----------------------------------------------------------------------------
# Effective sample size
# -----------------------------------------------------------------------------
def ess_fraction(log_w: np.ndarray) -> float:
    """Compute ESS / N for unnormalised log-weights."""
    lw = log_w - np.max(log_w)
    w = np.exp(lw)
    s1 = w.sum()
    s2 = (w ** 2).sum()
    if s1 == 0 or s2 == 0:
        return 0.0
    return float((s1 ** 2) / s2 / len(log_w))


# -----------------------------------------------------------------------------
# Weighted percentiles (numpy doesn't ship one)
# -----------------------------------------------------------------------------
def weighted_quantile(values: np.ndarray, weights: np.ndarray,
                      qs=(0.05, 0.50, 0.95)) -> np.ndarray:
    """Linear-interpolated weighted quantiles."""
    order = np.argsort(values)
    v = values[order]
    w = weights[order]
    cdf = np.cumsum(w) / w.sum()
    return np.interp(qs, cdf, v)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> int:
    args = parse_args()
    t_start = time.time()

    # ---------------------------------------------------------------
    # 1. Load all four inputs.
    # ---------------------------------------------------------------
    print(f"[load] paired ensemble: {args.paired}", flush=True)
    paired = pd.read_csv(args.paired)
    n_rows = len(paired)
    print(f"       n_rows = {n_rows:,}", flush=True)

    if args.obs_path is None:
        obs_path = ("data/observations/dangendorf_2024_gmsl.csv"
                    if args.obs == "dangendorf"
                    else "data/calibration/CSIRO_Recons_gmsl_yr_2015.csv")
    else:
        obs_path = args.obs_path
    print(f"[load] obs ({args.obs}): {obs_path}", flush=True)
    csiro = (load_dangendorf(obs_path) if args.obs == "dangendorf"
             else load_csiro(obs_path))
    print(f"       obs years {csiro.year.min()}-{csiro.year.max()}  ({len(csiro)} rows)", flush=True)

    print(f"[load] BRICK posterior: {args.posterior}", flush=True)
    posterior = load_posterior(args.posterior)
    print(f"       n_post = {len(posterior):,}", flush=True)

    print(f"[load] baseline l_B:    {args.lB}", flush=True)
    lB_df = pd.read_csv(args.lB)
    assert {"post_idx", "l_B_gmsl"} <= set(lB_df.columns), \
        f"l_B file must have columns post_idx, l_B_gmsl; got {list(lB_df.columns)}"
    print(f"       n_lB = {len(lB_df):,}", flush=True)

    # ---------------------------------------------------------------
    # 2. Identify year columns in the paired CSV (strings "1850".."2100").
    #    These store 100 * (gmsl[t] - gmsl[2000]) in cm.
    # ---------------------------------------------------------------
    year_cols = [c for c in paired.columns if c.isdigit()]
    year_cols_int = sorted(int(c) for c in year_cols)
    assert len(year_cols) > 0, "No integer-string year columns found in paired CSV."
    print(f"[setup] trajectory year columns: {year_cols_int[0]}..{year_cols_int[-1]} "
          f"({len(year_cols_int)} years)", flush=True)

    # ---------------------------------------------------------------
    # 3. Pre-compute observation arrays in METERS, referenced to year 2000.
    #
    #    obs_delta_m[t]  = csiro_m[t] - csiro_m[2000]
    #    obs_sigma_m[t]  = sqrt( sigma_m[t]^2 + sigma_m[2000]^2 )
    #
    #    Restricted to years that are both in CSIRO and in our trajectory grid.
    # ---------------------------------------------------------------
    if 2000 not in csiro.year.values:
        raise RuntimeError(f"obs source '{args.obs}' missing year 2000 — cannot re-baseline.")
    csiro_2000   = csiro.loc[csiro.year == 2000].iloc[0]
    gmsl_m_2000  = csiro_2000.gmsl_m
    sigma_m_2000 = csiro_2000.sigma_m

    # Use only years that appear in BOTH obs and the trajectory columns.
    obs = csiro[csiro.year.isin(year_cols_int)].copy()
    obs = obs.sort_values("year").reset_index(drop=True)
    obs["obs_delta_m"] = obs.gmsl_m - gmsl_m_2000
    # Independent-error propagation for two reference points (BRICK does
    # not double-count the 2000 anchor either, but using both sigmas is
    # the conservative, statistically clean choice when re-baselining).
    obs["obs_sigma_m"] = np.sqrt(obs.sigma_m ** 2 + sigma_m_2000 ** 2)
    obs_years = obs.year.values
    obs_delta = obs.obs_delta_m.values
    obs_sigma = obs.obs_sigma_m.values
    print(f"[setup] obs years used: {obs_years[0]}..{obs_years[-1]} "
          f"({len(obs_years)} years)", flush=True)

    # String column names for indexing the paired CSV's year columns.
    obs_year_strs = [str(y) for y in obs_years]
    # Verify all needed columns exist.
    missing = [c for c in obs_year_strs if c not in paired.columns]
    if missing:
        raise RuntimeError(f"Paired CSV missing trajectory columns: {missing[:5]} ...")

    # ---------------------------------------------------------------
    # 4. Build a per-post lookup of (sd_gmsl, rho_gmsl) keyed by 1-based
    #    post_idx, so each row's likelihood uses its OWN AR(1) parameters.
    # ---------------------------------------------------------------
    sd_lookup  = dict(zip(posterior.post_idx.values, posterior.sd_gmsl.values))
    rho_lookup = dict(zip(posterior.post_idx.values, posterior.rho_gmsl.values))

    # ---------------------------------------------------------------
    # 5. Extract trajectories as a (n_rows, n_obs_years) array IN METERS.
    #    Paired-CSV cells are cm; divide by 100.
    # ---------------------------------------------------------------
    print("[compute] assembling modeled trajectories (cm -> m) ...", flush=True)
    traj_cm = paired[obs_year_strs].to_numpy(dtype=np.float64)
    traj_m  = traj_cm / 100.0   # delta-from-2000 in METERS
    assert traj_m.shape == (n_rows, len(obs_years)), \
        f"trajectory shape mismatch: {traj_m.shape} vs ({n_rows},{len(obs_years)})"
    if np.any(np.isnan(traj_m)):
        n_nan = int(np.isnan(traj_m).sum())
        raise RuntimeError(f"Found {n_nan} NaNs in modeled trajectories; aborting.")

    # ---------------------------------------------------------------
    # 6. Compute l_FB per row.
    # ---------------------------------------------------------------
    print(f"[compute] l_FB for {n_rows:,} rows ...", flush=True)
    l_FB = np.full(n_rows, np.nan)
    post_indices = paired.post_idx.values
    t0 = time.time()
    for i in range(n_rows):
        pi = int(post_indices[i])
        sigma = float(sd_lookup[pi])
        rho   = float(rho_lookup[pi])
        # Residual = obs - model, both in m, both delta-from-2000.
        resid = obs_delta - traj_m[i, :]
        l_FB[i] = hetero_logl_ar1(resid, sigma, rho, obs_sigma)
        if (i + 1) % 5000 == 0 or i + 1 == n_rows:
            el = time.time() - t0
            print(f"   {i+1:,}/{n_rows:,}  ({el:.1f}s, {(i+1)/el:.1f} rows/s)", flush=True)

    # Sanity: no all-NaN or all-inf.
    n_neginf = int(np.isneginf(l_FB).sum())
    n_nan    = int(np.isnan(l_FB).sum())
    print(f"[compute] l_FB done: median={np.nanmedian(l_FB):.3f}  "
          f"min={np.nanmin(l_FB):.3f}  max={np.nanmax(l_FB):.3f}  "
          f"-inf={n_neginf}  nan={n_nan}", flush=True)

    # ---------------------------------------------------------------
    # 7. Merge l_B by post_idx.
    # ---------------------------------------------------------------
    paired_aug = paired.copy()
    paired_aug["l_FB"] = l_FB
    paired_aug = paired_aug.merge(lB_df, on="post_idx", how="left")
    n_missing_lB = paired_aug.l_B_gmsl.isna().sum()
    if n_missing_lB > 0:
        raise RuntimeError(f"{n_missing_lB} rows have no matching l_B for their post_idx; "
                           f"check that compute_lB_per_post.jl covered all posterior members.")
    paired_aug = paired_aug.rename(columns={"l_B_gmsl": "l_B"})

    # ---------------------------------------------------------------
    # 8. Compute weights with c sweep (or fixed c).
    #
    #    log_w_i = c * (l_FB - l_B)
    #    For ESS, the constant doesn't matter (subtraction of max),
    #    but the SHAPE of the weight distribution does — larger c
    #    sharpens the weights and lowers ESS. Wong tunes c heuristically
    #    to keep ESS near 50% of N.
    # ---------------------------------------------------------------
    diff = (paired_aug.l_FB - paired_aug.l_B).to_numpy()
    print(f"[weights] log-lik diff (l_FB - l_B): "
          f"median={np.median(diff):.3f}  p5={np.percentile(diff,5):.3f}  "
          f"p95={np.percentile(diff,95):.3f}", flush=True)

    if args.c == "auto":
        c_grid = [float(x) for x in args.c_grid.split(",")]
        print(f"[weights] auto-tuning c over grid {c_grid} for ESS/N ~ {args.ess_target}", flush=True)
        best_c = None
        best_dist = np.inf
        for c in c_grid:
            ef = ess_fraction(c * diff)
            print(f"   c={c:.5f}   ESS/N = {ef:.3f}", flush=True)
            d = abs(ef - args.ess_target)
            if d < best_dist:
                best_dist = d
                best_c = c
        c_use = best_c
        print(f"[weights] chosen c = {c_use:.5f}  (ESS/N closest to target)", flush=True)
    else:
        c_use = float(args.c)
        print(f"[weights] using fixed c = {c_use:.5f}", flush=True)

    log_w = c_use * diff
    # Max-shift then normalise (Wong Eq 2-3).
    log_w_shift = log_w - np.max(log_w)
    w = np.exp(log_w_shift)
    w_norm = w / w.sum()
    ess = (w.sum() ** 2) / (w ** 2).sum()
    print(f"[weights] final ESS = {ess:.1f} / {n_rows}  ({100*ess/n_rows:.1f} %)", flush=True)

    paired_aug["log_w"]  = log_w
    paired_aug["w_norm"] = w_norm

    # ---------------------------------------------------------------
    # 9. Side-by-side unweighted vs weighted percentiles for headline cols.
    # ---------------------------------------------------------------
    headline_cols = [
        "slr_2050_cm", "slr_2100_cm",
        "ais_2100_cm", "gsic_2100_cm", "gis_2100_cm", "te_2100_cm",
    ]
    print("\n=== Unweighted vs weighted percentiles (cm) ===", flush=True)
    print(f"{'metric':<14}  {'p5_u':>8} {'p50_u':>8} {'p95_u':>8}    "
          f"{'p5_w':>8} {'p50_w':>8} {'p95_w':>8}", flush=True)
    qs = (0.05, 0.50, 0.95)
    for col in headline_cols:
        if col not in paired_aug.columns:
            continue
        v = paired_aug[col].to_numpy()
        pu = np.percentile(v, [5, 50, 95])
        pw = weighted_quantile(v, w_norm, qs)
        print(f"{col:<14}  {pu[0]:>8.2f} {pu[1]:>8.2f} {pu[2]:>8.2f}    "
              f"{pw[0]:>8.2f} {pw[1]:>8.2f} {pw[2]:>8.2f}", flush=True)

    # ---------------------------------------------------------------
    # 10. Write augmented CSV.
    # ---------------------------------------------------------------
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    paired_aug.to_csv(out_path, index=False)
    print(f"\n[save] {out_path}  ({n_rows:,} rows)", flush=True)
    print(f"[done] total elapsed {time.time() - t_start:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
