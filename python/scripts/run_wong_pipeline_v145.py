"""
run_wong_pipeline_v145.py
=========================

Wong importance-weighting pipeline for the v1.4.5 flat-cube BRICK outputs.
Bridges the new `run_mimibrick_flatcube.jl` per-arm CSV schema (slr_<y>,
te_<y>, ais_<y>, gis_<y>, gsic_<y>, lws_<y>; 0-based post_idx) to the
legacy `apply_wong_weights.py` semantics (bare-year columns; 1-based
post_idx). Designed to run on Torch beside the 26 GB of raw BRICK CSVs so
only small summary envelopes get pulled down.

Steps:
  1. Load baseline BRICK CSV (e.g. brick_lhs10k_baseline.csv).
  2. Compute l_FB per row from its slr_<y> trajectory vs Dangendorf 2024 obs,
     using the post-PR#93 BRICK posterior's sd_gmsl/rho_gmsl AR(1) nuisance
     parameters per row.
  3. Merge l_B (post-PR#93 brick_lB_per_post_dangendorf_postpr93.csv) on
     post_idx (converting metadata's 0-based -> 1-based to match Julia/
     posterior convention).
  4. Auto-tune c on a fixed grid for ESS/N ~ 0.5 (Wong's default target).
  5. Write baseline_weighted.csv with l_FB, l_B, log_w, w_norm columns
     appended.
  6. Write baseline envelope CSV (p5/p50/p95 + weighted versions, per year,
     per component) — small (~451 rows x ~30 cols).
  7. For each pulse arm, paired-merge on (rff_idx, fair_cfg_idx, seed_idx,
     post_idx) to inherit w_norm. Compute marginal delta_slr_<y> = pulse -
     baseline per matched row. Write pulse_envelopes.csv +
     marginal_envelopes.csv.

Per the climate-modeling skill's checkpointing convention, we write the
baseline weighted CSV first, then process pulse arms in a loop with each
arm's envelope CSV emitted atomically. A re-run with --skip-existing will
not redo arms whose summaries are already present.

Usage:
  python python/scripts/run_wong_pipeline_v145.py \
      --brick-dir outputs/brick_v145 \
      --posterior data/MimiBRICK/parameters_subsample_brick.csv \
      --lB outputs/brick_lB_per_post_dangendorf_postpr93.csv \
      --obs data/observations/dangendorf_2024_gmsl.csv \
      --out-dir outputs/brick_v145_summaries
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Re-use helper functions from the legacy apply_wong_weights.py to keep
# Wong's likelihood semantics identical across the two pipelines.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from apply_wong_weights import (  # noqa: E402
    load_dangendorf,
    load_posterior,
    hetero_logl_ar1,
    ess_fraction,
    weighted_quantile,
)
from column_helpers import KEY_COLS, detect_year_columns  # noqa: E402


# ---------------------------------------------------------------------------
# Tunables (kept as module-level constants so they appear in CHANGELOG diffs
# if changed — matches the "Labels derive from named constants" discipline).
# ---------------------------------------------------------------------------
ESS_TARGET = 0.5
C_GRID = (0.0001, 0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0)
COMPONENTS = ("slr", "te", "ais", "gis", "gsic", "lws")
ENVELOPE_QUANTILES = (0.05, 0.17, 0.50, 0.83, 0.95)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--brick-dir", required=True, help="dir with brick_<arm>.csv files")
    p.add_argument("--families", default="lhs10k,anova18k",
                   help="comma-separated families to process (default: lhs10k,anova18k)")
    p.add_argument("--posterior", required=True, help="BRICK posterior CSV")
    p.add_argument("--lB",        required=True, help="brick_lB_per_post_*.csv (post-PR#93)")
    p.add_argument("--obs",       required=True, help="Dangendorf obs CSV (year, value, sigma)")
    p.add_argument("--out-dir",   required=True, help="dir for weighted CSVs + envelope summaries")
    p.add_argument("--skip-existing", action="store_true",
                   help="Skip an arm if its envelope CSV is already present.")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Wong-weights step for the baseline arm
# ---------------------------------------------------------------------------
def compute_wong_weights(
    baseline: pd.DataFrame, posterior: pd.DataFrame, lB_df: pd.DataFrame,
    obs_dang: pd.DataFrame,
) -> tuple[pd.DataFrame, float, float]:
    """Compute l_FB, log_w, w_norm per row of `baseline`. Mutates a copy.
    Returns (baseline_aug, c_use, ess_fraction)."""
    print(f"[wong] baseline rows: {len(baseline):,}", flush=True)

    # ----- year columns (slr_<y>) ---------------------------------------
    years = detect_year_columns(baseline, "slr_")
    assert years, "no slr_<year> columns found in baseline CSV"
    print(f"[wong] year columns: {years[0]}..{years[-1]} ({len(years)})", flush=True)

    # ----- obs anchor at 2000 -------------------------------------------
    if 2000 not in obs_dang.year.values:
        raise RuntimeError("obs CSV missing year 2000 (re-baselining anchor)")
    obs2000 = obs_dang.loc[obs_dang.year == 2000].iloc[0]
    gmsl2000 = obs2000.gmsl_m
    sig2000  = obs2000.sigma_m
    obs_use = obs_dang[obs_dang.year.isin(years)].sort_values("year").reset_index(drop=True)
    obs_delta = obs_use.gmsl_m.to_numpy() - gmsl2000
    obs_sigma = np.sqrt(obs_use.sigma_m.to_numpy() ** 2 + sig2000 ** 2)
    obs_years = obs_use.year.to_numpy()
    print(f"[wong] obs years: {obs_years[0]}..{obs_years[-1]} ({len(obs_years)})", flush=True)

    # ----- trajectory matrix (cm -> m, delta from 2000) -----------------
    obs_cols = [f"slr_{y}" for y in obs_years]
    missing = [c for c in obs_cols if c not in baseline.columns]
    if missing:
        raise RuntimeError(f"baseline missing trajectory cols: {missing[:5]} ...")
    traj_m = baseline[obs_cols].to_numpy(dtype=np.float64) / 100.0
    if np.isnan(traj_m).any():
        raise RuntimeError(f"NaNs in baseline trajectory ({int(np.isnan(traj_m).sum())} cells)")

    # ----- per-row AR(1) nuisance params (1-based post_idx lookup) ------
    sd_lu  = dict(zip(posterior.post_idx.values, posterior.sd_gmsl.values))
    rho_lu = dict(zip(posterior.post_idx.values, posterior.rho_gmsl.values))
    # Convert metadata's 0-based post_idx -> 1-based for posterior lookup.
    pi_1b = (baseline.post_idx.to_numpy().astype(int) + 1)

    n = len(baseline)
    l_FB = np.full(n, np.nan)
    t0 = time.time()
    for i in range(n):
        sigma = float(sd_lu[pi_1b[i]])
        rho   = float(rho_lu[pi_1b[i]])
        resid = obs_delta - traj_m[i, :]
        l_FB[i] = hetero_logl_ar1(resid, sigma, rho, obs_sigma)
        if (i + 1) % 5000 == 0 or i + 1 == n:
            el = time.time() - t0
            print(f"  l_FB {i+1:,}/{n:,}  ({el:.1f} s, {(i+1)/el:.1f} rows/s)", flush=True)

    # ----- merge l_B (also 1-based) -------------------------------------
    lB_df = lB_df.rename(columns={"l_B_gmsl": "l_B"})
    base_aug = baseline.copy()
    base_aug["post_idx_1b"] = pi_1b
    base_aug["l_FB"] = l_FB
    base_aug = base_aug.merge(lB_df.rename(columns={"post_idx": "post_idx_1b"}),
                               on="post_idx_1b", how="left")
    if base_aug.l_B.isna().any():
        raise RuntimeError(f"{int(base_aug.l_B.isna().sum())} rows missing l_B after merge")

    # ----- auto-tune c on grid for ESS/N ~ ESS_TARGET --------------------
    diff = (base_aug.l_FB - base_aug.l_B).to_numpy()
    print(f"[wong] l_FB - l_B: median={np.median(diff):.3f} "
          f"p5={np.percentile(diff,5):.3f} p95={np.percentile(diff,95):.3f}", flush=True)
    best_c, best_d = None, np.inf
    for c in C_GRID:
        ef = ess_fraction(c * diff)
        print(f"  c={c:.5f}  ESS/N = {ef:.3f}", flush=True)
        d = abs(ef - ESS_TARGET)
        if d < best_d:
            best_d, best_c = d, c
    log_w = best_c * diff
    log_w_shift = log_w - np.max(log_w)
    w = np.exp(log_w_shift)
    w_norm = w / w.sum()
    ess = (w.sum() ** 2) / (w ** 2).sum()
    base_aug["log_w"]  = log_w
    base_aug["w_norm"] = w_norm
    print(f"[wong] chosen c = {best_c:.5f}  ESS = {ess:.1f}/{n}  ({100*ess/n:.1f}%)", flush=True)
    return base_aug, float(best_c), float(ess / n)


# ---------------------------------------------------------------------------
# Envelope summary helpers
# ---------------------------------------------------------------------------
def summarize_envelopes(df: pd.DataFrame, weight_col: str | None,
                         components: tuple[str, ...] = COMPONENTS,
                         year_grid: list[int] | None = None) -> pd.DataFrame:
    """Per-year p5/p17/p50/p83/p95 (weighted if weight_col, unweighted always)."""
    if year_grid is None:
        year_grid = detect_year_columns(df, prefix=f"{components[0]}_")
    rows = []
    w = df[weight_col].to_numpy() if weight_col is not None else None
    for y in year_grid:
        row = {"year": int(y)}
        for comp in components:
            col = f"{comp}_{y}"
            if col not in df.columns:
                continue
            v = df[col].to_numpy()
            qs_unw = np.percentile(v, [q*100 for q in ENVELOPE_QUANTILES])
            for q, qv in zip(ENVELOPE_QUANTILES, qs_unw):
                row[f"{comp}_p{int(round(q*100)):02d}_unw"] = float(qv)
            if w is not None:
                qs_w = weighted_quantile(v, w, ENVELOPE_QUANTILES)
                for q, qv in zip(ENVELOPE_QUANTILES, qs_w):
                    row[f"{comp}_p{int(round(q*100)):02d}"] = float(qv)
        rows.append(row)
    return pd.DataFrame(rows)


def marginal_envelopes(base_aug: pd.DataFrame, pulse: pd.DataFrame,
                        year_grid: list[int]) -> pd.DataFrame:
    """Paired marginal ΔSLR(y) = pulse - baseline per (rff, cfg, seed, post)
    tuple; per-year envelope across the tuples. Weighted via baseline's
    w_norm (the conceptually right move per Wong's paper)."""
    join_keys = list(KEY_COLS)
    # Restrict baseline to just the columns we need.
    base_cols = join_keys + ["w_norm"] + [f"slr_{y}" for y in year_grid]
    pulse_cols = join_keys + [f"slr_{y}" for y in year_grid]
    j = pulse[pulse_cols].merge(base_aug[base_cols], on=join_keys, how="inner",
                                 suffixes=("_p", "_b"))
    n_dropped = len(pulse) - len(j)
    if n_dropped > 0:
        # Silent paired-merge drops are a known foot-gun: a pulse cell that
        # has no baseline twin is unweightable and silently distorts the
        # marginal envelope. Hard-fail at >1% so the operator knows.
        frac = n_dropped / max(len(pulse), 1)
        msg = (f"[marg] {n_dropped} / {len(pulse)} pulse rows "
               f"({100*frac:.2f}%) had no matching baseline tuple")
        if frac > 0.01:
            raise RuntimeError(msg + " — aborting (>1% pairing loss).")
        print(f"  WARNING: {msg}", flush=True)
    rows = []
    w = j["w_norm"].to_numpy()
    for y in year_grid:
        d = j[f"slr_{y}_p"].to_numpy() - j[f"slr_{y}_b"].to_numpy()
        row = {"year": int(y)}
        qs_unw = np.percentile(d, [q*100 for q in ENVELOPE_QUANTILES])
        for q, qv in zip(ENVELOPE_QUANTILES, qs_unw):
            row[f"delta_slr_p{int(round(q*100)):02d}_unw_cm"] = float(qv)
        qs_w = weighted_quantile(d, w, ENVELOPE_QUANTILES)
        for q, qv in zip(ENVELOPE_QUANTILES, qs_w):
            row[f"delta_slr_p{int(round(q*100)):02d}_cm"] = float(qv)
        row["delta_slr_mean_cm"]   = float(np.average(d, weights=w))
        row["delta_slr_mean_unw_cm"] = float(d.mean())
        row["n_tuples"] = int(len(d))
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Per-family driver
# ---------------------------------------------------------------------------
def process_family(family: str, brick_dir: Path, out_dir: Path,
                    posterior: pd.DataFrame, lB_df: pd.DataFrame,
                    obs_dang: pd.DataFrame, skip_existing: bool) -> None:
    print(f"\n===== family: {family} =====", flush=True)
    baseline_csv = brick_dir / f"brick_{family}_baseline.csv"
    if not baseline_csv.exists():
        print(f"  no baseline CSV at {baseline_csv} — skipping family", flush=True)
        return
    print(f"[load] {baseline_csv}", flush=True)
    baseline = pd.read_csv(baseline_csv)

    # ----- Wong weights from baseline ------------------------------------
    baseline_aug, c_use, ess_frac = compute_wong_weights(
        baseline, posterior, lB_df, obs_dang)
    weighted_csv = out_dir / f"brick_{family}_baseline_weighted.csv"
    baseline_aug.to_csv(weighted_csv, index=False)
    print(f"[save] {weighted_csv}  ({len(baseline_aug):,} rows)", flush=True)

    year_grid = detect_year_columns(baseline_aug, "slr_")

    # ----- baseline envelopes (small) ------------------------------------
    env = summarize_envelopes(baseline_aug, "w_norm", year_grid=year_grid)
    env_csv = out_dir / f"brick_{family}_baseline_envelopes.csv"
    env.to_csv(env_csv, index=False)
    print(f"[save] {env_csv}  ({len(env)} years × {env.shape[1]} cols)", flush=True)

    # ----- per-pulse arms ------------------------------------------------
    pulse_csvs = sorted(brick_dir.glob(f"brick_{family}_pulse_*.csv"))
    for pcsv in pulse_csvs:
        arm = pcsv.stem.replace(f"brick_{family}_", "")
        env_out = out_dir / f"brick_{family}_{arm}_envelopes.csv"
        marg_out = out_dir / f"brick_{family}_{arm}_marginal_envelopes.csv"
        if skip_existing and env_out.exists() and marg_out.exists():
            print(f"  [skip] {arm}", flush=True)
            continue
        print(f"\n[arm] {arm}", flush=True)
        pulse = pd.read_csv(pcsv)
        # Inherit weights from the baseline arm (per paired-tuple).
        join_keys = list(KEY_COLS)
        pulse_aug = pulse.merge(baseline_aug[join_keys + ["w_norm"]], on=join_keys, how="left")
        if pulse_aug.w_norm.isna().any():
            # Same silent-drop concern as in marginal_envelopes — hard-fail
            # above 1% so the operator doesn't ship an arm with degraded
            # importance-weight coverage.
            n_miss = int(pulse_aug.w_norm.isna().sum())
            frac = n_miss / max(len(pulse_aug), 1)
            msg = f"{n_miss} / {len(pulse_aug)} pulse rows ({100*frac:.2f}%) had no baseline weight match"
            if frac > 0.01:
                raise RuntimeError(msg + " — aborting (>1%).")
            print(f"  WARNING: {msg}", flush=True)
        env_p = summarize_envelopes(pulse_aug, "w_norm", year_grid=year_grid)
        env_p.to_csv(env_out, index=False)
        print(f"[save] {env_out}", flush=True)

        marg = marginal_envelopes(baseline_aug, pulse, year_grid)
        marg.to_csv(marg_out, index=False)
        print(f"[save] {marg_out}", flush=True)


def main():
    args = parse_args()
    brick_dir = Path(args.brick_dir)
    out_dir   = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    print("[load] posterior  ", args.posterior, flush=True)
    posterior = load_posterior(args.posterior)
    print(f"        n_post = {len(posterior):,}", flush=True)
    print("[load] l_B (per-post post-PR#93)  ", args.lB, flush=True)
    lB_df = pd.read_csv(args.lB)
    print(f"        n_lB = {len(lB_df):,}", flush=True)
    print("[load] obs (Dangendorf 2024)  ", args.obs, flush=True)
    obs_dang = load_dangendorf(args.obs)
    print(f"        obs years: {obs_dang.year.min()}..{obs_dang.year.max()} "
          f"({len(obs_dang)})", flush=True)

    for family in [f.strip() for f in args.families.split(",")]:
        process_family(family, brick_dir, out_dir,
                        posterior, lB_df, obs_dang, args.skip_existing)


if __name__ == "__main__":
    main()
