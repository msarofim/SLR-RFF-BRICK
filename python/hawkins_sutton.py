"""
hawkins_sutton.py

Hawkins-Sutton variance decomposition for FaIR GMST + MimiBRICK GMSL across
the SLR-RFF-BRICK ensemble, plus historical observation overlay plots.

== Variance decomposition (per year t) ==

Phase A FaIR cube: gmst[rff, cfg, seed, year], shape (2000, 841, 10, 251),
years 1850-2100. Equal weights (no Wong reweighting on the climate side).

  V_emissions(t) = Var_rff [ E_{cfg,seed} gmst ]
  V_climate(t)   = E_rff   [ Var_cfg E_seed gmst ]
  V_internal(t)  = E_{rff,cfg} [ Var_seed gmst ]

For SLR (from the paired weighted CSV with one BRICK posterior per draw):
each row pairs a unique (rff,cfg,seed) with a single BRICK post. Because no
two rows share the same (rff,cfg,seed) cell, we cannot cleanly estimate
V_brick separately from V_internal -- the BRICK-parameter variance is
absorbed into the within-cell residual along with internal variability.
We therefore report a 3-way decomposition for SLR:

  V_emissions(t) = Var_w over rff      of  E_w[ slr | rff ]
  V_climate(t)   = E_w over rff of Var_w over cfg of E_w[ slr | rff, cfg ]
  V_residual(t)  = E_w[ Var_w[ slr | rff, cfg ] ]   (internal + BRICK)

All SLR variances are Wong-weighted using w_norm. See the "Caveats" comment
in the SLR figure for clarification.

== Observations overlay ==

Both historical figures rebaseline to the 1986-2005 mean. Berkeley Earth's
native 1951-1980 baseline is converted to 1986-2005 using BE's own data.
SLR observations (Dangendorf 2024, NOAA STAR altimetry) are similarly rebaselined.

== CLI ==

    python python/hawkins_sutton.py \
        --cube-stem outputs/lhs_pilot_full_N2000 \
        --brick-csv outputs/brick_paired_N2000_weighted.csv \
        [--ext-cube outputs/rff_baseline_stoch_to2300.npz] \
        [--ext-brick-csv outputs/brick_paired_rff_baseline_to2300_weighted.csv] \
        --obs-dir data/observations/ \
        --out-dir outputs/plots/ \
        --start-year 1850 --end-year 2100 \
        --decomp-start 2020 --decomp-end 2100

Outputs in --out-dir:
    hawkins_sutton_gmst.{png,pdf} + hawkins_sutton_gmst.csv
    hawkins_sutton_slr.{png,pdf}  + hawkins_sutton_slr.csv
    gmst_obs_vs_model.{png,pdf}   + gmst_obs_vs_model.csv
    slr_obs_vs_model.{png,pdf}    + slr_obs_vs_model.csv
    (and _ext.{png,pdf,csv} variants if --ext-cube / --ext-brick-csv given)
"""
import argparse
import gc
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJ_DIR = Path("/scratch/ms17839/SLR-RFF-BRICK")

# Reference baseline for both historical fit panels and for HS anchoring of
# the historical plot. The H-S figures themselves anchor at decomp-start
# (2020 = 0) by subtracting per-draw 2020 value.
REF_PERIOD = (1986, 2005)


# ---------------------------------------------------------------------------
# Weighted-statistics helpers
# ---------------------------------------------------------------------------
def weighted_mean(x, w, axis=None):
    """Weighted mean along `axis`. Assumes w sums to 1 or arbitrary positive."""
    w = np.asarray(w, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    wsum = w.sum(axis=axis, keepdims=(axis is not None))
    return (w * x).sum(axis=axis, keepdims=(axis is not None)) / wsum


def weighted_var(x, w, axis=None, ddof=0):
    """Weighted variance: E_w[x^2] - (E_w[x])^2, ddof for plug-in (0)."""
    w = np.asarray(w, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    wsum = w.sum(axis=axis, keepdims=(axis is not None))
    m = (w * x).sum(axis=axis, keepdims=(axis is not None)) / wsum
    var = (w * (x - m) ** 2).sum(axis=axis, keepdims=(axis is not None)) / wsum
    if axis is None:
        return float(var)
    return np.squeeze(var, axis=axis)


def weighted_quantile(x, w, qs):
    """Weighted quantiles via the linear-interp method on sorted values."""
    x = np.asarray(x, dtype=np.float64)
    w = np.asarray(w, dtype=np.float64)
    finite = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x = x[finite]; w = w[finite]
    if len(x) == 0:
        return np.array([np.nan] * len(qs))
    order = np.argsort(x)
    xs = x[order]; ws = w[order]
    cdf = np.cumsum(ws) - 0.5 * ws
    cdf /= ws.sum()
    return np.interp(qs, cdf, xs)


# ---------------------------------------------------------------------------
# GMST variance decomposition from the (rff,cfg,seed,year) cube
# ---------------------------------------------------------------------------
def decompose_gmst(gmst_cube, years, t_anchor):
    """
    gmst_cube : np.memmap or ndarray, shape (n_rff, n_cfg, n_seed, n_yr), float
    years     : 1-D int array of length n_yr
    t_anchor  : int -- anchor year. Each trajectory is rebased so that
                gmst[..., t_anchor] == 0.

    Returns
    -------
    out : pd.DataFrame with columns
        year, V_total, V_emissions, V_climate, V_internal,
        f_emissions, f_climate, f_internal, mean
    Variance is in degC^2; mean in degC (anomaly vs anchor year).
    """
    n_rff, n_cfg, n_seed, n_yr = gmst_cube.shape
    i_anchor = int(np.where(years == t_anchor)[0][0])

    # We process one year at a time to keep memory bounded -- the full cube
    # is ~17 GB float32 and we don't want a float64 copy.
    V_emissions = np.zeros(n_yr)
    V_climate   = np.zeros(n_yr)
    V_internal  = np.zeros(n_yr)
    mean_t      = np.zeros(n_yr)

    # The anchor slice (n_rff, n_cfg, n_seed), float32 -> float64 once
    anchor = gmst_cube[:, :, :, i_anchor].astype(np.float64, copy=True)

    print(f"[gmst-decomp] {n_rff} rff x {n_cfg} cfg x {n_seed} seed; "
          f"years {years.min()}-{years.max()}; anchor = {t_anchor}",
          flush=True)
    t0 = time.time()
    for it in range(n_yr):
        slab = gmst_cube[:, :, :, it].astype(np.float64) - anchor
        # E_seed: average over seed dim -> (n_rff, n_cfg)
        mean_seed = slab.mean(axis=2)
        # E_{cfg,seed} = mean of mean_seed over cfg -> (n_rff,)
        mean_cfg_seed = mean_seed.mean(axis=1)
        # E_{rff,cfg,seed} scalar
        grand_mean = mean_cfg_seed.mean()

        # V_emissions = Var_rff(mean_cfg_seed)
        V_emissions[it] = mean_cfg_seed.var(ddof=0)
        # V_climate = E_rff[ Var_cfg(mean_seed) ]
        V_climate[it]   = mean_seed.var(axis=1, ddof=0).mean()
        # V_internal = E_{rff,cfg}[ Var_seed(slab) ]
        V_internal[it]  = slab.var(axis=2, ddof=0).mean()

        mean_t[it] = grand_mean

        if (it % 25) == 0:
            print(f"  year={int(years[it])}  V_emi={V_emissions[it]:.4g}  "
                  f"V_clim={V_climate[it]:.4g}  V_int={V_internal[it]:.4g}  "
                  f"({time.time()-t0:.1f}s)", flush=True)

    V_total = V_emissions + V_climate + V_internal
    # Guard against division by zero at anchor year (V_total ~= 0)
    eps = np.maximum(V_total, 1e-15)
    out = pd.DataFrame({
        "year": years.astype(int),
        "V_total":     V_total,
        "V_emissions": V_emissions,
        "V_climate":   V_climate,
        "V_internal":  V_internal,
        "f_emissions": V_emissions / eps,
        "f_climate":   V_climate   / eps,
        "f_internal":  V_internal  / eps,
        "mean":        mean_t,
    })
    return out


# ---------------------------------------------------------------------------
# 4-way SLR variance decomposition (emissions / climate / internal / BRICK)
# Designed for a BALANCED factorial dataset like the ANOVA metadata, where
# every (rff, cfg, seed) cell has the same number of post samples, every
# (rff, cfg) has the same n_seed, etc.
# ---------------------------------------------------------------------------
def _wmean(v, w):
    """Weighted mean. w_sum must be > 0."""
    return (v * w).sum() / w.sum()


def _wvar(v, w):
    """Weighted variance (population, biased / ddof=0). Uses weighted mean."""
    mu = _wmean(v, w)
    return ((v - mu) ** 2 * w).sum() / w.sum()


def decompose_slr_4way(brick_df, years, t_anchor, weights_col=None):
    """
    Nested random-effects 4-way decomposition of SLR variance:

        V_brick     = E_{rcs}[ Var_post( slr | rff, cfg, seed ) ]
        V_internal  = E_{rc}[  Var_seed( E_post[ slr | rff, cfg, seed ] ) ]
        V_climate   = E_{r}[   Var_cfg(  E_{seed,post}[ slr | rff, cfg ] ) ]
        V_emissions = Var_rff(  E_{cfg,seed,post}[ slr | rff ] )
        V_total     = sum of the four

    For a balanced factorial design (e.g. 100 rffs × 15 cfgs × 3 seeds × 3
    posts) this is the standard nested-ANOVA decomp.

    brick_df : long-format DataFrame with rff_idx, fair_cfg_idx, seed_idx,
               post_idx columns and one column per year (str-int names).
               One row per (rff, cfg, seed, post) tuple.
    weights_col : optional column name with Wong importance weights (or any
               per-row weights). If None, each row gets equal weight (1).
               Weighted nested ANOVA: at each level, the within-cell variance
               is weighted by the row weights, and the cell weight in the
               outer expectation is the sum of within-cell weights.
    """
    rows_out = []
    anchor_col = str(int(t_anchor))
    if anchor_col not in brick_df.columns:
        raise ValueError(f"anchor year {t_anchor} not in BRICK CSV year columns")
    anchor_vec = brick_df[anchor_col].to_numpy()

    if weights_col is None:
        w_all = np.ones(len(brick_df), dtype=np.float64)
    else:
        w_all = brick_df[weights_col].to_numpy(dtype=np.float64)
        if not np.all(w_all >= 0):
            raise ValueError(f"weights in {weights_col} contain negatives")
        if w_all.sum() <= 0:
            raise ValueError(f"weights in {weights_col} sum to 0")

    keys_full = ["rff_idx", "fair_cfg_idx", "seed_idx"]
    keys_rc   = ["rff_idx", "fair_cfg_idx"]

    # Pre-build group-by once (same indexing for every year)
    base = brick_df[keys_full].copy()
    base["w"] = w_all

    for y in years:
        ycol = str(int(y))
        v = brick_df[ycol].to_numpy() - anchor_vec
        tmp = base.copy()
        tmp["v"] = v

        # Level 1: weighted mean and var across posts WITHIN (rff, cfg, seed)
        rcs_list = []
        for keys, g in tmp.groupby(keys_full, sort=False):
            vg = g["v"].to_numpy()
            wg = g["w"].to_numpy()
            ws = wg.sum()
            if ws <= 0:
                continue
            mu  = (vg * wg).sum() / ws
            var = ((vg - mu) ** 2 * wg).sum() / ws
            rcs_list.append((keys[0], keys[1], keys[2], mu, var, ws))
        rcs_df = pd.DataFrame(rcs_list,
                              columns=["rff_idx","fair_cfg_idx","seed_idx","mu","var","w"])
        V_brick = float((rcs_df["var"] * rcs_df["w"]).sum() / rcs_df["w"].sum())

        # Level 2: weighted mean+var across seeds within (rff, cfg)
        rc_list = []
        for keys, g in rcs_df.groupby(keys_rc, sort=False):
            mug = g["mu"].to_numpy()
            wg  = g["w"].to_numpy()
            ws  = wg.sum()
            if ws <= 0:
                continue
            mu  = (mug * wg).sum() / ws
            var = ((mug - mu) ** 2 * wg).sum() / ws
            rc_list.append((keys[0], keys[1], mu, var, ws))
        rc_df = pd.DataFrame(rc_list,
                             columns=["rff_idx","fair_cfg_idx","mu","var","w"])
        V_internal = float((rc_df["var"] * rc_df["w"]).sum() / rc_df["w"].sum())

        # Level 3: weighted mean+var across cfgs within rff
        r_list = []
        for keys, g in rc_df.groupby("rff_idx", sort=False):
            mug = g["mu"].to_numpy()
            wg  = g["w"].to_numpy()
            ws  = wg.sum()
            if ws <= 0:
                continue
            mu  = (mug * wg).sum() / ws
            var = ((mug - mu) ** 2 * wg).sum() / ws
            r_list.append((keys, mu, var, ws))
        r_df = pd.DataFrame(r_list,
                            columns=["rff_idx","mu","var","w"])
        V_climate = float((r_df["var"] * r_df["w"]).sum() / r_df["w"].sum())

        # Level 4: weighted var across rffs
        mug = r_df["mu"].to_numpy()
        wg  = r_df["w"].to_numpy()
        ws  = wg.sum()
        Y_grand = float((mug * wg).sum() / ws)
        V_emissions = float(((mug - Y_grand) ** 2 * wg).sum() / ws)

        V_total = V_emissions + V_climate + V_internal + V_brick
        rows_out.append({
            "year": int(y),
            "V_total":      V_total,
            "V_emissions":  V_emissions,
            "V_climate":    V_climate,
            "V_internal":   V_internal,
            "V_brick":      V_brick,
            "mean":         Y_grand,
        })

    df_out = pd.DataFrame(rows_out)
    eps = np.maximum(df_out["V_total"], 1e-15)
    for c in ("emissions", "climate", "internal", "brick"):
        df_out[f"f_{c}"] = df_out[f"V_{c}"] / eps
    return df_out


def ofat_variance(ofat_df, years, t_anchor):
    """
    OFAT cross-check: for each axis in ofat_df (vary_rff, vary_cfg, vary_seed,
    vary_post), compute the local sample variance of slr at each year.

    Returns DataFrame with columns: axis, year, V_local, mean, N.
    The 'V_local' for axis X estimates the variance contribution from
    perturbing X around the OFAT centroid — comparable to V_X(t) from
    decompose_slr_4way at the SAME centroid (modulo interactions).
    """
    anchor_col = str(int(t_anchor))
    anchor_vec = ofat_df[anchor_col].to_numpy()
    rows = []
    for axis in sorted(ofat_df["axis"].unique()):
        if axis in ("centroid", ""):
            continue
        sub = ofat_df[ofat_df["axis"] == axis]
        anchor_sub = anchor_vec[sub.index]
        for y in years:
            ycol = str(int(y))
            v = sub[ycol].to_numpy() - anchor_sub
            rows.append({
                "axis":    axis,
                "year":    int(y),
                "V_local": float(np.var(v, ddof=0)),
                "mean":    float(np.mean(v)),
                "N":       int(len(v)),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# SLR variance decomposition from the paired weighted CSV
# ---------------------------------------------------------------------------
def decompose_slr(brick_df, years, t_anchor, weights_col="w_norm"):
    """
    brick_df : DataFrame with columns rff_idx, fair_cfg_idx, seed_idx,
               post_idx, w_norm, and one column per year (string-int names).
    years    : list/array of int years to use for the decomposition.

    Returns DataFrame indexed by year with V_emissions, V_climate, V_residual,
    f_*, and weighted mean.
    """
    # Verify column presence
    required = ["rff_idx", "fair_cfg_idx", "seed_idx", weights_col]
    for c in required:
        if c not in brick_df.columns:
            raise KeyError(f"brick CSV missing column {c!r}")
    yr_cols = [str(int(y)) for y in years]
    missing = [c for c in yr_cols if c not in brick_df.columns]
    if missing:
        raise KeyError(f"brick CSV missing year columns: {missing[:5]}...")

    if str(int(t_anchor)) not in brick_df.columns:
        raise ValueError(f"brick CSV has no anchor year column {t_anchor}")
    print(f"[slr-decomp] {len(brick_df):,} paired rows; anchor = {t_anchor}",
          flush=True)

    w_all = brick_df[weights_col].to_numpy(dtype=np.float64)
    # normalise just in case
    w_all = w_all / w_all.sum()

    # Pre-extract the year matrix as float64 (n_rows, n_yr)
    Y = brick_df[yr_cols].to_numpy(dtype=np.float64)
    anchor_vec = brick_df[str(int(t_anchor))].to_numpy(dtype=np.float64)
    Y_anom = Y - anchor_vec[:, None]   # cm rel to anchor year per row

    # Group indices for rff and (rff,cfg)
    rff_codes, rff_uniques = pd.factorize(brick_df["rff_idx"])
    cfg_codes = brick_df["fair_cfg_idx"].to_numpy()
    # 2D group: combine rff and cfg into a single label. Newer pandas
    # (>=2.x) requires a Series/Index/ndarray for factorize -- a list of
    # tuples is rejected with TypeError. Combine to a single int64 key.
    rff_key = brick_df["rff_idx"].to_numpy(dtype=np.int64)
    cfg_key = brick_df["fair_cfg_idx"].to_numpy(dtype=np.int64)
    # Pack as (rff * MAX_CFG + cfg). MAX_CFG = 10000 is safely above the
    # 841 configs in v1.4.1 and well within int64.
    MAX_CFG = 10_000
    rff_cfg_combined = rff_key * MAX_CFG + cfg_key
    rff_cfg_codes, _ = pd.factorize(rff_cfg_combined)

    n_rows, n_yr = Y_anom.shape
    print(f"  unique rff = {len(rff_uniques)}, "
          f"unique (rff,cfg) cells = {rff_cfg_codes.max()+1}", flush=True)

    # ---- Pre-compute per-rff weighted means E_w[slr | rff] for all years ----
    # Vectorised: build a (n_groups, n_yr) array by accumulating w_i * Y_i
    n_rff_groups = len(rff_uniques)
    # weight per row * Y; sum within group / sum of weights within group
    Wt = np.zeros(n_rff_groups, dtype=np.float64)
    WX_rff = np.zeros((n_rff_groups, n_yr), dtype=np.float64)
    for i in range(n_rows):
        g = rff_codes[i]
        Wt[g] += w_all[i]
        WX_rff[g] += w_all[i] * Y_anom[i]
    M_rff = WX_rff / Wt[:, None]   # E_w[slr | rff] for each rff group, per yr
    Wt_rff = Wt.copy()             # weight mass per rff group

    # ---- E_w[slr | rff, cfg] for each (rff,cfg) cell ----
    n_cells = int(rff_cfg_codes.max() + 1)
    Wt_cell = np.zeros(n_cells, dtype=np.float64)
    WX_cell = np.zeros((n_cells, n_yr), dtype=np.float64)
    WX2_cell = np.zeros((n_cells, n_yr), dtype=np.float64)
    cell_to_rff = np.full(n_cells, -1, dtype=np.int64)
    for i in range(n_rows):
        c = rff_cfg_codes[i]
        Wt_cell[c] += w_all[i]
        WX_cell[c] += w_all[i] * Y_anom[i]
        WX2_cell[c] += w_all[i] * (Y_anom[i] ** 2)
        cell_to_rff[c] = rff_codes[i]
    M_cell = WX_cell / Wt_cell[:, None]   # E_w[slr | rff,cfg]
    # Within-cell variance E_w[x^2] - (E_w[x])^2
    Vresid_cell = WX2_cell / Wt_cell[:, None] - M_cell ** 2
    Vresid_cell = np.clip(Vresid_cell, 0.0, None)

    # ---- Weighted grand mean over rff (using Wt_rff as weights) ----
    grand_w = Wt_rff / Wt_rff.sum()
    grand_mean = (M_rff * grand_w[:, None]).sum(axis=0)   # (n_yr,)

    # V_emissions = Var_w over rff of M_rff
    V_emissions = (
        ((M_rff - grand_mean[None, :]) ** 2) * grand_w[:, None]
    ).sum(axis=0)

    # For V_climate, treat each rff group: weighted variance of M_cell across
    # the cfg cells *within that rff*, weighted by per-cell mass, then average
    # over rff groups weighted by Wt_rff.
    # We compute the contribution per cell and aggregate.
    # First, mean of M_cell within rff = M_rff (already have it).
    M_rff_of_cell = M_rff[cell_to_rff]      # (n_cells, n_yr)
    sqdev = (M_cell - M_rff_of_cell) ** 2   # cell-to-rff-mean squared deviation
    # weight per cell as fraction of its rff group
    cell_w_within_rff = Wt_cell / Wt_rff[cell_to_rff]
    contrib_climate_per_cell = sqdev * cell_w_within_rff[:, None]
    # sum within rff -> per-rff variance, then average over rff (mass-weighted)
    Vclim_per_rff = np.zeros((n_rff_groups, n_yr), dtype=np.float64)
    for c in range(n_cells):
        Vclim_per_rff[cell_to_rff[c]] += contrib_climate_per_cell[c]
    V_climate = (Vclim_per_rff * grand_w[:, None]).sum(axis=0)

    # V_residual: E over (rff,cfg) cells of within-cell variance
    cell_w_global = Wt_cell / Wt_cell.sum()
    V_residual = (Vresid_cell * cell_w_global[:, None]).sum(axis=0)

    V_total = V_emissions + V_climate + V_residual
    eps = np.maximum(V_total, 1e-15)

    out = pd.DataFrame({
        "year": np.asarray(years, dtype=int),
        "V_total":     V_total,
        "V_emissions": V_emissions,
        "V_climate":   V_climate,
        "V_residual":  V_residual,
        "f_emissions": V_emissions / eps,
        "f_climate":   V_climate   / eps,
        "f_residual":  V_residual  / eps,
        "mean":        grand_mean,
    })
    return out


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------
def plot_hs_stack(decomp_df, components, colors, labels, title,
                  out_png, out_pdf, y_total_label, inset_units="degC"):
    """
    Generic Hawkins-Sutton stacked-fraction plot.

    decomp_df  : DataFrame with year, V_total, V_<c>, f_<c> for c in components
    components : list of suffixes (e.g. ['emissions','climate','internal'])
    """
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    yrs = decomp_df["year"].to_numpy()
    fracs = [decomp_df[f"f_{c}"].to_numpy() for c in components]
    ax.stackplot(yrs, *fracs, labels=labels, colors=colors, alpha=0.85,
                 edgecolor="white", linewidth=0.4)
    ax.set_xlim(yrs.min(), yrs.max())
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year")
    ax.set_ylabel("Fraction of total variance")
    ax.set_title(title)
    # Reverse legend so order matches visual top→bottom stack order
    # (last component is plotted on top → should appear first in legend).
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="lower right", framealpha=0.9, fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)

    # Inset: ensemble mean + empirical 5-95% band on absolute scale.
    # If the caller provides empirical 'p5'/'p95' columns in decomp_df we use
    # those directly (correct for asymmetric/long-tailed distributions like
    # pulse-marginal SLR which is bounded near 0 with a fat upper tail). If
    # absent we fall back to the Gaussian ±1.96·√V_total approximation, which
    # is fine for symmetric quantities like total GMST but produces nonsense
    # negative lower bounds for skewed positive-tail distributions.
    ax2 = ax.inset_axes([0.08, 0.62, 0.32, 0.32])
    m = decomp_df["mean"].to_numpy()
    if "p5" in decomp_df.columns and "p95" in decomp_df.columns:
        lo = decomp_df["p5"].to_numpy()
        hi = decomp_df["p95"].to_numpy()
        band_label = f"mean / 5–95% ({inset_units})"
    else:
        sd = np.sqrt(np.maximum(decomp_df["V_total"].to_numpy(), 0))
        lo = m - 1.96 * sd
        hi = m + 1.96 * sd
        band_label = f"mean ± 1.96σ ({inset_units})"
    ax2.fill_between(yrs, lo, hi, color="#666666", alpha=0.25, linewidth=0)
    ax2.plot(yrs, m, color="#222222", linewidth=1.3)
    ax2.set_title(band_label, fontsize=8)
    ax2.tick_params(labelsize=7)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(yrs.min(), yrs.max())

    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"  wrote {out_png}\n  wrote {out_pdf}")


def percentile_band_from_cube(gmst_cube, years, qs=(0.05, 0.5, 0.95)):
    """Return (n_yr, len(qs)) array of quantiles taken across all rff*cfg*seed
    for each year. Computed in a memory-bounded way."""
    n_rff, n_cfg, n_seed, n_yr = gmst_cube.shape
    out = np.zeros((n_yr, len(qs)), dtype=np.float64)
    for it in range(n_yr):
        slab = gmst_cube[:, :, :, it].astype(np.float64).ravel()
        out[it] = np.quantile(slab, qs)
    return out


def percentile_band_weighted_csv(brick_df, year_cols, w, qs=(0.05, 0.5, 0.95)):
    """Weighted quantiles for each year column."""
    out = np.zeros((len(year_cols), len(qs)), dtype=np.float64)
    Y = brick_df[year_cols].to_numpy(dtype=np.float64)
    for i in range(Y.shape[1]):
        out[i] = weighted_quantile(Y[:, i], w, qs)
    return out


def rebaseline_to_period(years, values, start, end):
    """Subtract the mean of values over years in [start, end] (inclusive)."""
    mask = (years >= start) & (years <= end)
    if mask.sum() == 0:
        return values
    return values - np.mean(values[mask])


def plot_obs_overlay(years_model, q_model, obs_dfs, title, ylabel,
                     out_png, out_pdf, zoom_period=None,
                     obs_styles=None):
    """
    Two-panel figure: full historical + optional zoom.

    years_model : (n_yr,) int
    q_model     : (n_yr, 3)  -- p5/p50/p95
    obs_dfs     : dict {label: DataFrame[year,value]} already rebaselined
    """
    if zoom_period is None:
        fig, ax = plt.subplots(1, 1, figsize=(8.0, 4.5))
        axes = [ax]
    else:
        fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.5),
                                  gridspec_kw=dict(width_ratios=[2.2, 1.0]))

    panels = [None, zoom_period]
    for ax, panel_period in zip(axes, panels):
        ax.fill_between(years_model, q_model[:, 0], q_model[:, 2],
                        color="#9999dd", alpha=0.45,
                        label="Model 5-95%")
        ax.plot(years_model, q_model[:, 1], color="#222266", lw=1.5,
                label="Model median")
        for label, df in obs_dfs.items():
            sty = (obs_styles or {}).get(label, dict(color="k", lw=1.0,
                                                     marker="o", ms=2.5))
            ax.plot(df["year"], df["value"], label=label, **sty)
        if panel_period is not None:
            ax.set_xlim(*panel_period)
            # tight y to data in zoom window
            yvals = []
            yvals.append(q_model[(years_model >= panel_period[0])
                                  & (years_model <= panel_period[1]), 0])
            yvals.append(q_model[(years_model >= panel_period[0])
                                  & (years_model <= panel_period[1]), 2])
            for df in obs_dfs.values():
                m = (df["year"] >= panel_period[0]) & (df["year"] <= panel_period[1])
                yvals.append(df["value"].to_numpy()[m])
            yvals = np.concatenate([y for y in yvals if len(y) > 0])
            if len(yvals) > 0:
                lo, hi = np.nanmin(yvals), np.nanmax(yvals)
                pad = 0.1 * (hi - lo + 1e-9)
                ax.set_ylim(lo - pad, hi + pad)
        else:
            ax.set_xlim(years_model.min(), years_model.max())
        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        if panel_period is None:
            ax.legend(loc="upper left", fontsize=9, framealpha=0.9)

    if zoom_period is not None:
        axes[1].set_title(f"Zoom {zoom_period[0]}-{zoom_period[1]}", fontsize=10)
    axes[0].set_title(title)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"  wrote {out_png}\n  wrote {out_pdf}")


def load_obs_csv(path):
    """Return DataFrame[year,value,sigma] or None if missing/empty."""
    p = Path(path)
    if not p.exists():
        print(f"  [obs] not found: {p}")
        return None
    try:
        df = pd.read_csv(p)
    except Exception as e:
        print(f"  [obs] failed to read {p}: {e}")
        return None
    if "year" not in df.columns or "value" not in df.columns:
        print(f"  [obs] {p} missing year/value columns; got {list(df.columns)}")
        return None
    if len(df) == 0:
        print(f"  [obs] {p} is empty")
        return None
    df = df.dropna(subset=["year", "value"]).copy()
    df["year"] = df["year"].astype(int)
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cube-stem", required=True,
                    help="Stem for FaIR cube .npy files (looks for "
                         "<stem>_gmst.npy and <stem>_years.npy)")
    ap.add_argument("--brick-csv", required=True,
                    help="Weighted paired BRICK CSV (with w_norm column)")
    ap.add_argument("--ext-cube", default=None,
                    help="Optional extended-horizon FaIR cube .npz "
                         "(keys years, gmst_traj_rff) e.g. rff_baseline_stoch_to2300")
    ap.add_argument("--ext-brick-csv", default=None,
                    help="Optional extended-horizon weighted BRICK CSV")
    ap.add_argument("--obs-dir",
                    default=str(PROJ_DIR / "data" / "observations"))
    ap.add_argument("--out-dir",
                    default=str(PROJ_DIR / "outputs" / "plots"))
    ap.add_argument("--start-year", type=int, default=1850,
                    help="Lower x-axis for historical-fit panels")
    ap.add_argument("--end-year", type=int, default=2100,
                    help="Upper x-axis for historical-fit panels")
    ap.add_argument("--decomp-start", type=int, default=2020,
                    help="Anchor year for H-S decomposition (anomalies = 0 here)")
    ap.add_argument("--decomp-end", type=int, default=2100,
                    help="Upper x-axis for H-S figures")
    ap.add_argument("--cfg-stride", type=int, default=1,
                    help="Subsample FaIR configs (use every k-th cfg) to "
                         "speed up the GMST decomposition; default 1")
    args = ap.parse_args()

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    obs_dir = Path(args.obs_dir)
    print(f"=== hawkins_sutton.py ===")
    print(f"  cube_stem    = {args.cube_stem}")
    print(f"  brick_csv    = {args.brick_csv}")
    print(f"  ext_cube     = {args.ext_cube}")
    print(f"  ext_brick    = {args.ext_brick_csv}")
    print(f"  obs_dir      = {obs_dir}")
    print(f"  out_dir      = {out_dir}")
    print(f"  decomp anchor= {args.decomp_start}, span -> {args.decomp_end}")

    # ----- Load Phase A FaIR cube (memmap) -----------------------------------
    cube_stem = Path(args.cube_stem)
    if not cube_stem.is_absolute():
        cube_stem = PROJ_DIR / cube_stem
    gmst_path  = cube_stem.with_name(cube_stem.name + "_gmst.npy")
    years_path = cube_stem.with_name(cube_stem.name + "_years.npy")
    if not gmst_path.exists() or not years_path.exists():
        print(f"!! Cannot find {gmst_path} or {years_path}; aborting")
        sys.exit(1)
    print(f"  loading {gmst_path} (mmap)")
    gmst_cube = np.load(gmst_path, mmap_mode="r")
    years = np.load(years_path)
    print(f"  cube shape = {gmst_cube.shape}, dtype = {gmst_cube.dtype}, "
          f"years {years.min()}-{years.max()}")
    assert gmst_cube.ndim == 4, "expected 4-D cube (rff,cfg,seed,year)"

    if args.cfg_stride > 1:
        print(f"  subsampling configs by stride {args.cfg_stride}")
        gmst_cube = gmst_cube[:, ::args.cfg_stride, :, :]

    # ----- Figure 1: H-S GMST -------------------------------------------------
    print("\n[fig 1] Hawkins-Sutton decomposition of GMST")
    decomp_yrs_mask = (years >= args.decomp_start) & (years <= args.decomp_end)
    decomp_years = years[decomp_yrs_mask]
    gmst_decomp = decompose_gmst(gmst_cube, years, t_anchor=args.decomp_start)
    gmst_decomp_window = gmst_decomp[
        gmst_decomp["year"].between(args.decomp_start, args.decomp_end)
    ].reset_index(drop=True)

    csv1 = out_dir / "hawkins_sutton_gmst.csv"
    gmst_decomp_window.to_csv(csv1, index=False)
    print(f"  wrote {csv1}")

    plot_hs_stack(
        gmst_decomp_window,
        components=["emissions", "climate", "internal"],
        colors=["#d95f02", "#7570b3", "#1b9e77"],
        labels=["Emissions (RFF-SP)", "Climate response (FaIR configs)",
                "Internal variability (seeds)"],
        title=("Hawkins-Sutton variance decomposition: GMST\n"
               f"(anomaly rel. to {args.decomp_start}; "
               f"{gmst_cube.shape[0]} rff x {gmst_cube.shape[1]} configs "
               f"x {gmst_cube.shape[2]} seeds)"),
        out_png=out_dir / "hawkins_sutton_gmst.png",
        out_pdf=out_dir / "hawkins_sutton_gmst.pdf",
        y_total_label="Var(GMST) [degC^2]",
        inset_units="degC",
    )

    # ----- Figure 3: GMST historical fit vs Berkeley Earth -------------------
    print("\n[fig 3] GMST historical fit vs observations")
    # Compute percentile band from cube, rebaselined to REF_PERIOD per draw.
    # Cheaper approach: compute quantile over (rff,cfg,seed) of anomaly[year]
    # where anomaly is computed using the cube's REF_PERIOD mean across years.
    # Since the cube starts at 1850 and REF_PERIOD is 1986-2005, we can
    # compute per-trajectory mean across those years and subtract.
    i0 = int(np.where(years == REF_PERIOD[0])[0][0])
    i1 = int(np.where(years == REF_PERIOD[1])[0][0])
    print(f"  re-baselining cube to mean over years "
          f"{REF_PERIOD[0]}-{REF_PERIOD[1]} (cube indices {i0}-{i1})")
    # mean across REF_PERIOD years for each (rff,cfg,seed): shape (n_rff,n_cfg,n_seed)
    ref_mean = gmst_cube[:, :, :, i0:i1+1].astype(np.float64).mean(axis=3)

    n_yr = gmst_cube.shape[-1]
    q_model = np.zeros((n_yr, 3), dtype=np.float64)
    for it in range(n_yr):
        slab = gmst_cube[:, :, :, it].astype(np.float64) - ref_mean
        q_model[it] = np.quantile(slab.ravel(), [0.05, 0.5, 0.95])
    # restrict to plot window
    plot_mask = (years >= args.start_year) & (years <= args.end_year)
    yrs_plot = years[plot_mask]
    q_plot   = q_model[plot_mask]

    # Berkeley Earth obs: native baseline 1951-1980; rebase to 1986-2005 using BE itself
    be_df = load_obs_csv(obs_dir / "berkeley_earth_annual.csv")
    obs_for_fig3 = {}
    if be_df is not None:
        # compute BE offset: mean over 1986-2005 in BE (already rel to 1951-1980)
        m_be = ((be_df["year"] >= REF_PERIOD[0])
                & (be_df["year"] <= REF_PERIOD[1]))
        if m_be.sum() > 0:
            offset = be_df.loc[m_be, "value"].mean()
            be_rb = be_df.copy()
            be_rb["value"] = be_rb["value"] - offset
            obs_for_fig3["Berkeley Earth"] = be_rb
            print(f"  BE offset (1951-80 -> 1986-2005) = {offset:+.3f} degC")
        else:
            print("  BE doesn't cover 1986-2005; cannot rebaseline cleanly; "
                  "using raw")
            obs_for_fig3["Berkeley Earth (1951-80 base)"] = be_df

    plot_obs_overlay(
        yrs_plot, q_plot, obs_for_fig3,
        title=(f"GMST: FaIR ensemble vs Berkeley Earth   "
               f"(anomaly rel. to {REF_PERIOD[0]}-{REF_PERIOD[1]} mean)"),
        ylabel="GMST anomaly [degC]",
        out_png=out_dir / "gmst_obs_vs_model.png",
        out_pdf=out_dir / "gmst_obs_vs_model.pdf",
        zoom_period=(2020, min(2025, args.end_year)),
        obs_styles={"Berkeley Earth": dict(color="k", lw=1.0, marker="o", ms=3.0),
                    "Berkeley Earth (1951-80 base)":
                        dict(color="k", lw=1.0, marker="o", ms=3.0, alpha=0.5)},
    )
    # CSV export of the model band + obs
    obs_export = pd.DataFrame({"year": yrs_plot,
                               "model_p05": q_plot[:, 0],
                               "model_p50": q_plot[:, 1],
                               "model_p95": q_plot[:, 2]})
    if be_df is not None and "Berkeley Earth" in obs_for_fig3:
        be_rb = obs_for_fig3["Berkeley Earth"]
        obs_export = obs_export.merge(
            be_rb[["year", "value"]].rename(columns={"value": "berkeley_earth"}),
            on="year", how="left")
    obs_export.to_csv(out_dir / "gmst_obs_vs_model.csv", index=False)
    print(f"  wrote {out_dir / 'gmst_obs_vs_model.csv'}")

    # Free the big GMST array
    del gmst_cube, ref_mean
    gc.collect()

    # ----- Load Phase A BRICK paired CSV --------------------------------------
    brick_path = Path(args.brick_csv)
    if not brick_path.is_absolute():
        brick_path = PROJ_DIR / brick_path
    print(f"\n  loading {brick_path}")
    brick_df = pd.read_csv(brick_path)
    yr_str_cols = sorted([c for c in brick_df.columns if c.isdigit()],
                         key=int)
    brick_years = np.array([int(c) for c in yr_str_cols], dtype=int)
    print(f"  brick CSV: {len(brick_df):,} rows, year columns "
          f"{brick_years.min()}-{brick_years.max()}")

    # ----- Figure 2: H-S SLR --------------------------------------------------
    print("\n[fig 2] Hawkins-Sutton decomposition of SLR")
    slr_decomp_years = brick_years[
        (brick_years >= args.decomp_start) & (brick_years <= args.decomp_end)
    ]
    slr_decomp = decompose_slr(brick_df, slr_decomp_years,
                                t_anchor=args.decomp_start,
                                weights_col="w_norm")
    csv2 = out_dir / "hawkins_sutton_slr.csv"
    slr_decomp.to_csv(csv2, index=False)
    print(f"  wrote {csv2}")
    plot_hs_stack(
        slr_decomp,
        components=["emissions", "climate", "residual"],
        colors=["#d95f02", "#7570b3", "#1b9e77"],
        labels=["Emissions (RFF-SP)", "Climate response (FaIR configs)",
                "Residual (internal + BRICK posterior)"],
        title=("Hawkins-Sutton variance decomposition: GMSL\n"
               f"(weighted; anomaly rel. to {args.decomp_start}; "
               "BRICK posterior absorbed into residual term)"),
        out_png=out_dir / "hawkins_sutton_slr.png",
        out_pdf=out_dir / "hawkins_sutton_slr.pdf",
        y_total_label="Var(GMSL) [cm^2]",
        inset_units="cm",
    )

    # ----- Figure 4: SLR historical fit ---------------------------------------
    print("\n[fig 4] SLR historical fit vs observations")
    # Rebaseline each draw to its own REF_PERIOD mean
    ref_yrs_avail = [str(y) for y in range(REF_PERIOD[0], REF_PERIOD[1]+1)
                     if str(y) in brick_df.columns]
    if len(ref_yrs_avail) < 5:
        print(f"  warn: only {len(ref_yrs_avail)} of "
              f"{REF_PERIOD[1]-REF_PERIOD[0]+1} REF_PERIOD years present "
              f"in brick CSV; using what's available")
    if not ref_yrs_avail:
        print("  cannot rebase; using raw trajectories")
        ref_mean = np.zeros(len(brick_df))
    else:
        ref_mean = brick_df[ref_yrs_avail].to_numpy(dtype=np.float64).mean(axis=1)

    plot_years = [int(c) for c in yr_str_cols
                  if args.start_year <= int(c) <= args.end_year]
    plot_year_cols = [str(y) for y in plot_years]
    plot_years = np.array(plot_years, dtype=int)
    Y_plot = (brick_df[plot_year_cols].to_numpy(dtype=np.float64)
              - ref_mean[:, None])
    w = brick_df["w_norm"].to_numpy(dtype=np.float64)
    w = w / w.sum()
    q_slr = np.zeros((len(plot_years), 3), dtype=np.float64)
    for i in range(len(plot_years)):
        q_slr[i] = weighted_quantile(Y_plot[:, i], w, (0.05, 0.5, 0.95))

    # Obs: Dangendorf 2024 reconstruction (mm, 1900-2018) + NOAA STAR
    # satellite altimetry (mm rel 1993).  Dangendorf supersedes the previously
    # used CSIRO Recons (1880-2013) as the canonical long-record GMSL source.
    obs_for_fig4 = {}
    dangendorf_df = load_obs_csv(obs_dir / "dangendorf_2024_gmsl.csv")
    if dangendorf_df is not None:
        d = dangendorf_df.copy()
        d["value"] = d["value"] / 10.0   # mm -> cm
        m = (d["year"] >= REF_PERIOD[0]) & (d["year"] <= REF_PERIOD[1])
        if m.sum() > 0:
            d["value"] = d["value"] - d.loc[m, "value"].mean()
        obs_for_fig4["Dangendorf 2024"] = d
        print(f"  Dangendorf 2024: {len(d)} rows in cm")

    nasa_df = load_obs_csv(obs_dir / "nasa_gmsl_annual.csv")
    if nasa_df is not None:
        n = nasa_df.copy()
        n["value"] = n["value"] / 10.0   # mm -> cm
        # NOAA STAR only covers 1993-present so it can't span REF_PERIOD
        # (1986-2005) entirely. Use whatever overlap exists, else align to
        # Dangendorf via the early-overlap offset.
        m = (n["year"] >= REF_PERIOD[0]) & (n["year"] <= REF_PERIOD[1])
        if m.sum() > 0:
            n["value"] = n["value"] - n.loc[m, "value"].mean()
            print(f"  NOAA STAR altimetry: rebased on {m.sum()} years in 1986-2005")
        elif dangendorf_df is not None:
            dan_cm = obs_for_fig4["Dangendorf 2024"]
            overlap = dan_cm.merge(n, on="year", suffixes=("_dan", "_nasa"))
            if len(overlap) > 0:
                offset = (overlap["value_dan"] - overlap["value_nasa"]).mean()
                n["value"] = n["value"] + offset
                print(f"  NOAA STAR altimetry: aligned to Dangendorf via offset "
                      f"{offset:+.2f} cm")
        obs_for_fig4["NOAA STAR altimetry"] = n

    plot_obs_overlay(
        plot_years, q_slr, obs_for_fig4,
        title=(f"GMSL: BRICK ensemble (weighted) vs observations   "
               f"(anomaly rel. to {REF_PERIOD[0]}-{REF_PERIOD[1]} mean)"),
        ylabel="GMSL anomaly [cm]",
        out_png=out_dir / "slr_obs_vs_model.png",
        out_pdf=out_dir / "slr_obs_vs_model.pdf",
        zoom_period=(2010, min(2025, args.end_year)),
        obs_styles={"Dangendorf 2024":     dict(color="black", lw=1.0,
                                                marker="o", ms=2.5),
                    "NOAA STAR altimetry": dict(color="red", lw=1.0,
                                                marker="s", ms=2.5)},
    )

    slr_export = pd.DataFrame({"year": plot_years,
                               "model_p05": q_slr[:, 0],
                               "model_p50": q_slr[:, 1],
                               "model_p95": q_slr[:, 2]})
    for label, df in obs_for_fig4.items():
        slr_export = slr_export.merge(
            df[["year", "value"]].rename(columns={"value": label.replace(" ", "_")}),
            on="year", how="left")
    slr_export.to_csv(out_dir / "slr_obs_vs_model.csv", index=False)
    print(f"  wrote {out_dir / 'slr_obs_vs_model.csv'}")

    # ------------------------------------------------------------------
    # Optional: extended-horizon (Phase C) variants
    # ------------------------------------------------------------------
    if args.ext_cube and Path(args.ext_cube).exists():
        print(f"\n[fig 1-ext] H-S GMST extended via {args.ext_cube}")
        try:
            nz = np.load(args.ext_cube)
            ext_years = nz["years"].astype(int)
            ext_cube = nz["gmst_traj_rff"]
            print(f"  ext cube shape = {ext_cube.shape}, "
                  f"years {ext_years.min()}-{ext_years.max()}")
            if ext_cube.ndim == 3:
                # (n_rff, n_cfg, n_yr): inject a seed dim so decompose_gmst
                # treats V_internal as zero (n_seed=1 -> Var_seed = 0)
                ext_cube = ext_cube[:, :, None, :]
            ext_anchor = max(args.decomp_start, int(ext_years.min()))
            ext_decomp = decompose_gmst(ext_cube, ext_years,
                                         t_anchor=ext_anchor)

            # Phase C uses a single seed by design, so V_internal is
            # structurally 0 from decompose_gmst(). But the single-seed
            # design means Phase C's V_climate is CONTAMINATED with
            # internal noise: with n_seed=1, V_climate = E_rff[Var_cfg(X)]
            # = E_rff[Var_cfg(mu + ε)] = V_climate_true + V_internal.
            #
            # We correct by (1) subtracting time-resolved Phase A V_internal
            # from V_climate to recover V_climate_true, then (2) re-adding
            # V_internal as its own component. V_total is unchanged but the
            # decomposition is now algebraically consistent.
            phaseA_csv = out_dir / "hawkins_sutton_gmst.csv"
            if phaseA_csv.exists():
                pa = pd.read_csv(phaseA_csv)[["year", "V_internal"]]
                stationary_v_int = float(pa[pa["year"] >= 2050]["V_internal"].mean())
                pa_lookup = pa.set_index("year")["V_internal"].to_dict()
                v_int_series = ext_decomp["year"].map(
                    lambda y: pa_lookup.get(int(y), stationary_v_int)
                ).astype(float)
                print(f"  Borrowing Phase A V_internal (time-resolved); "
                      f"min={v_int_series.min():.4f}, max={v_int_series.max():.4f}.")
                # Step 1: V_climate_true = V_climate_C - V_internal (clip ≥0)
                v_clim_corrected = np.maximum(
                    ext_decomp["V_climate"].to_numpy() - v_int_series.to_numpy(),
                    0.0,
                )
                ext_decomp["V_climate"]  = v_clim_corrected
                ext_decomp["V_internal"] = v_int_series.to_numpy()
                ext_decomp["V_total"] = (ext_decomp["V_emissions"] +
                                          ext_decomp["V_climate"] +
                                          ext_decomp["V_internal"])
                eps = np.maximum(ext_decomp["V_total"], 1e-15)
                for c in ("emissions", "climate", "internal"):
                    ext_decomp[f"f_{c}"] = ext_decomp[f"V_{c}"] / eps
            else:
                print(f"  [warn] {phaseA_csv} not found; V_internal stays 0")

            mask = (ext_decomp["year"] >= args.decomp_start) & (
                    ext_decomp["year"] <= int(ext_years.max()))
            ext_window = ext_decomp[mask].reset_index(drop=True)
            ext_window.to_csv(out_dir / "hawkins_sutton_gmst_ext.csv",
                              index=False)
            plot_hs_stack(
                ext_window,
                components=["emissions", "climate", "internal"],
                colors=["#d95f02", "#7570b3", "#1b9e77"],
                labels=["Emissions", "Climate configs",
                        "Internal (Phase A borrowed)"],
                title=("Hawkins-Sutton GMST (extended to {})\n"
                       "anomaly rel. to {}".format(int(ext_years.max()),
                                                    ext_anchor)),
                out_png=out_dir / "hawkins_sutton_gmst_ext.png",
                out_pdf=out_dir / "hawkins_sutton_gmst_ext.pdf",
                y_total_label="Var(GMST) [degC^2]",
            )
        except Exception as e:
            print(f"  !! ext GMST failed: {e}")

    if args.ext_brick_csv and Path(args.ext_brick_csv).exists():
        print(f"\n[fig 2-ext] H-S SLR extended via {args.ext_brick_csv}")
        try:
            extb = pd.read_csv(args.ext_brick_csv)
            extb_year_cols = sorted([c for c in extb.columns if c.isdigit()],
                                    key=int)
            extb_years = np.array([int(c) for c in extb_year_cols], dtype=int)
            ext_anchor_slr = max(args.decomp_start, int(extb_years.min()))
            decomp_years_ext = extb_years[extb_years >= ext_anchor_slr]
            ext_slr = decompose_slr(extb, decomp_years_ext,
                                     t_anchor=ext_anchor_slr,
                                     weights_col="w_norm")
            ext_slr.to_csv(out_dir / "hawkins_sutton_slr_ext.csv", index=False)
            plot_hs_stack(
                ext_slr,
                components=["emissions", "climate", "residual"],
                colors=["#d95f02", "#7570b3", "#1b9e77"],
                labels=["Emissions", "Climate configs",
                        "Residual (internal + BRICK post)"],
                title=("Hawkins-Sutton GMSL (extended to {})\n"
                       "anomaly rel. to {}, weighted".format(
                           int(extb_years.max()), ext_anchor_slr)),
                out_png=out_dir / "hawkins_sutton_slr_ext.png",
                out_pdf=out_dir / "hawkins_sutton_slr_ext.pdf",
                y_total_label="Var(GMSL) [cm^2]",
                inset_units="cm",
            )
        except Exception as e:
            print(f"  !! ext SLR failed: {e}")

    print("\n=== done ===")


if __name__ == "__main__":
    main()
