"""
group_sobol_hs.py
=================

PRODUCTION Group-Sobol Hawkins-Sutton variance decomposition, replacing the
TreeSHAP attribution that under-attributed the collinear RFF emissions axis by
~5x for SLR (8.6% vs the true ~42% at 2150). Covers all FOUR targets:

  total_gmst, pulse_gmst   — groups {emissions, climate};   internal from cube
  total_slr,  pulse_slr    — groups {emissions, climate, brick}; internal seed-aug

Why Group-Sobol (decision 2026-05-28, see memory project_slr_hs_sobol_decision):
  TreeSHAP splits the joint contribution of correlated features arbitrarily, so
  the summed per-feature SHAP variance << the true axis contribution. Sobol
  first-order indices for feature GROUPS are the mathematically correct H-S
  quantity. Saltelli pick-and-freeze with EMPIRICAL cell-based sampling keeps
  the within-group correlation structure exactly.

Surrogate (Marcus's choice 2026-05-28): tuned HistGB on the p99-CLIPPED target
  (clipping removes the AIS-tipping tail so OOF R2 rises into the >0.9 regime
  needed for sum(S_first) <= 1), with monotonic constraints on the
  cumulative-emissions features. Unweighted fit (per the shapley pipeline's
  ESS-concentration rationale), importance-weighted Saltelli sampling + R2 + V_total.

Bookkeeping (per target, per year):
  V_total      weighted variance of target across the 10k cells
  R2_oof       held-out (80/20) weighted R2 of the surrogate
  V_explained  = V_total * max(R2_oof, 0)        (honest explained variance)
  S_first_g    grouped first-order Sobol index (fraction of surrogate var)
  V_g          = S_first_g * V_explained          (absolute main effect)
  internal     SLR: model-free seed-aug (compute_v_seed_total); GMST: V_total*(1-R2)
  interactions / residual absorbs (1-sum S)*V_explained + modelling slack

Outputs:
  SLR:  outputs/substack/v5_hybrid_decomp_{total,pulse}_{clip,unclip}.csv
        (same schema downstream render/poster already read; V_emissions /
         V_climate / V_brick now Sobol-derived, V_seed still model-free)
  GMST: outputs/substack/shapley_hs_per_axis_{total,pulse}_gmst.csv  (fractions)
        + re-rendered shapley_hs_{total,pulse}_gmst.{png,pdf}

Env knobs:
  HS_QUICK=1        only landmark years [2050,2100,2150] (fast validation)
  HS_ONLY=...       comma list of targets to run (default all 4)
"""
from __future__ import annotations
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shapley_hawkins_sutton import (
    KEY_COLS, RFF_FEATURES_LIST as RFF_FEATS, CFG_FEATURES, POST_FEATURES,
    assemble_features, load_target, _smooth_traj,
    YEAR_LO, YEAR_HI, OUTLIER_PERCENTILE, SMOOTH_WINDOW_YR_PULSE,
    AXIS_LABEL, AXIS_COLOR, OUT,
)
from hybrid_hs_slr_unified import (
    load_baseline_v5, load_pulse_v5, compute_v_seed_total, clip_per_year,
    YEARS, ANCHOR, PULSE_SIZE_GTCO2,
)

# cap nested OpenMP threads so joblib process-parallelism over years doesn't
# oversubscribe cores (n_jobs workers x OMP threads each)
os.environ.setdefault("OMP_NUM_THREADS", "2")
from joblib import Parallel, delayed
from sklearn.ensemble import HistGradientBoostingRegressor

N_JOBS = 4

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
GROUPS_SLR  = {"emissions": RFF_FEATS, "climate": CFG_FEATURES, "brick": POST_FEATURES}
GROUPS_GMST = {"emissions": RFF_FEATS, "climate": CFG_FEATURES}

N_SOBOL = 8192          # base Saltelli sample; total surrogate evals = (2+G)*N
SEED    = 2026

# Tuned HistGB (high capacity; clipping makes this learnable to R2>0.9)
HGB_KW = dict(max_iter=600, max_leaf_nodes=63, learning_rate=0.03,
              min_samples_leaf=20, l2_regularization=0.5, random_state=SEED)

# Monotonic constraints — only physically unambiguous cumulative-emissions feats
MONO = {
    "cum_co2_2030": 1, "cum_co2_2100": 1, "cum_co2_2300": 1,
    "peak_co2_emissions": 1, "cum_ch4_2100": 1,
    "frac_negative_post_2050": -1,
    # peak_co2_year, slope_co2_2050_2100 left unconstrained (sign ambiguous)
}

LANDMARKS = [2050, 2100, 2150]

# display-only temporal smoothing of per-year Sobol Monte-Carlo jitter for the
# GMST per-axis fraction CSV / figure (raw absolute variances are not smoothed)
SMOOTH_WIN_DISP = 11


def _smooth_disp(a, win=SMOOTH_WIN_DISP):
    a = np.asarray(a, float)
    if win <= 1 or a.size < win:
        return a
    pad = win // 2
    ap = np.pad(a, (pad, pad), mode="edge")
    return np.convolve(ap, np.ones(win) / win, mode="valid")[:a.size]


def mono_cst(feature_cols):
    return np.array([MONO.get(f, 0) for f in feature_cols], dtype=int)


# --------------------------------------------------------------------------
# Core: per-year surrogate fit + grouped Sobol indices
# --------------------------------------------------------------------------
def _sobol_year(it, Xv, y, w, gidx, mono, n_sobol, seed):
    """Per-year worker (top-level + array-only so joblib can pickle it).
    gidx: {group_name: int-index-array into Xv columns}. Returns S_first,
    S_total per group, OOF R2, weighted V_total. Surrogate fit UNWEIGHTED;
    R2 / V_total / Saltelli sampling importance-weighted. rng seeded per-year so the
    parallel run is bit-reproducible and order-independent."""
    n = Xv.shape[0]
    wsum = w.sum()
    mu_y = (y * w).sum() / wsum
    v_total = ((y - mu_y) ** 2 * w).sum() / wsum
    if v_total < 1e-30:
        z = {g: 0.0 for g in gidx}
        return dict(it=it, S_first=z, S_total=dict(z), r2_oof=0.0, v_total=float(v_total))

    rng = np.random.default_rng(seed)
    # held-out R2 (single 80/20 split)
    perm = rng.permutation(n)
    n_te = n // 5
    te, tr = perm[:n_te], perm[n_te:]
    m_tr = HistGradientBoostingRegressor(monotonic_cst=mono, **HGB_KW)
    m_tr.fit(Xv[tr], y[tr])
    yhat_te = m_tr.predict(Xv[te])
    w_te = w[te]
    mu_te = (y[te] * w_te).sum() / w_te.sum()
    ss_res = (w_te * (y[te] - yhat_te) ** 2).sum()
    ss_tot = (w_te * (y[te] - mu_te) ** 2).sum()
    r2_oof = 1.0 - ss_res / max(ss_tot, 1e-30)

    # full fit for Sobol surrogate
    m = HistGradientBoostingRegressor(monotonic_cst=mono, **HGB_KW)
    m.fit(Xv, y)

    # Saltelli pick-and-freeze, empirical importance-weighted cell sampling
    w_p = w / w.sum()
    idx_A = rng.choice(n, size=n_sobol, replace=True, p=w_p)
    idx_B = rng.choice(n, size=n_sobol, replace=True, p=w_p)
    X_A, X_B = Xv[idx_A].copy(), Xv[idx_B].copy()
    Y_A, Y_B = m.predict(X_A), m.predict(X_B)
    var_Y = np.var(np.concatenate([Y_A, Y_B]))
    S_first, S_total = {}, {}
    for g, idx in gidx.items():
        X_ABg = X_A.copy()
        X_ABg[:, idx] = X_B[:, idx]
        Y_ABg = m.predict(X_ABg)
        if var_Y < 1e-30:
            S_first[g] = 0.0; S_total[g] = 0.0
        else:
            S_first[g] = float(np.mean(Y_B * (Y_ABg - Y_A)) / var_Y)   # Saltelli 2010
            S_total[g] = float(np.mean((Y_A - Y_ABg) ** 2) / (2 * var_Y))  # Jansen 1999
    return dict(it=it, S_first=S_first, S_total=S_total,
                r2_oof=float(r2_oof), v_total=float(v_total))


def _gidx_for(feature_cols, groups):
    col_of = {f: i for i, f in enumerate(feature_cols)}
    return {g: np.array([col_of[f] for f in flist], int) for g, flist in groups.items()}


SEED_BASE = {"total_gmst": 1_000_000, "pulse_gmst": 2_000_000,
             "total_slr": 3_000_000, "pulse_slr": 4_000_000}


def _seed_for(target_tag, it):
    return SEED_BASE.get(target_tag, 9_000_000) + it


# --------------------------------------------------------------------------
# SLR pipeline (total / pulse) -> v5_hybrid_decomp CSVs
# --------------------------------------------------------------------------
def _build_slr_target(target_name):
    v5_base, slr_base = load_baseline_v5()
    i_a = int(np.where(YEARS == ANCHOR)[0][0])
    if target_name == "total":
        target = slr_base - slr_base[:, [i_a]]
        v5_pulse = None
    else:
        v5_pulse, slr_pulse = load_pulse_v5()
        assert (v5_base[KEY_COLS].to_numpy() == v5_pulse[KEY_COLS].to_numpy()).all()
        target = ((slr_pulse - slr_pulse[:, [i_a]]) -
                  (slr_base - slr_base[:, [i_a]])) / PULSE_SIZE_GTCO2
    return v5_base, slr_base, target


def _wvar_per_year(M, w):
    """Weighted variance of each year-column of M (cells × years)."""
    wsum = w.sum()
    mu = (M * w[:, None]).sum(axis=0) / wsum
    return (((M - mu) ** 2) * w[:, None]).sum(axis=0) / wsum


def run_slr(target_name, years_idx):
    """target_name 'total' or 'pulse'. Writes clip CSV (full Sobol, parallel
    over years) + unclip CSV (V_total only — the render uses just unc.V_total
    for the tipping wedge, so Sobol on the unclipped target is never read)."""
    print(f"\n=== SLR {target_name.upper()} (Group-Sobol) ===", flush=True)
    v5_base, slr_base, target_unclip = _build_slr_target(target_name)
    w = v5_base["w_norm"].to_numpy(dtype=np.float64)

    feat = assemble_features()
    assert (feat[KEY_COLS].to_numpy() == v5_base[KEY_COLS].to_numpy()).all(), \
        "feature/target row mismatch"
    feature_cols = RFF_FEATS + CFG_FEATURES + POST_FEATURES
    Xv = feat[feature_cols].to_numpy(dtype=np.float64)
    gidx = _gidx_for(feature_cols, GROUPS_SLR)
    mono = mono_cst(feature_cols)
    tgt_tag = f"{target_name}_slr"

    if target_name == "total":
        v_seed_full = compute_v_seed_total(v5_base, slr_base)
    else:
        v_seed_full = np.zeros(len(YEARS))

    # ---- unclip CSV: V_total only (wedges unused downstream) ----
    v_tot_unclip = _wvar_per_year(target_unclip, w)
    unc = pd.DataFrame({"year": [int(YEARS[it]) for it in years_idx],
                        "V_total": [v_tot_unclip[it] for it in years_idx]})
    for c in ["V_emissions", "V_climate", "V_brick", "V_seed", "V_residual"]:
        unc[c] = 0.0
    unc.to_csv(OUT / f"v5_hybrid_decomp_{target_name}_unclip.csv", index=False)

    # ---- clip CSV: full Group-Sobol, parallel over years ----
    target = clip_per_year(target_unclip, q=99.0)
    t0 = time.time()
    results = Parallel(n_jobs=N_JOBS, verbose=5)(
        delayed(_sobol_year)(it, Xv, target[:, it].astype(np.float64), w,
                             gidx, mono, N_SOBOL, _seed_for(tgt_tag, it))
        for it in years_idx)
    rows = []
    for res in sorted(results, key=lambda r: r["it"]):
        it = res["it"]
        v_tot = res["v_total"]
        v_expl = v_tot * max(res["r2_oof"], 0.0)
        s_emi, s_clim, s_brick = (res["S_first"]["emissions"],
                                  res["S_first"]["climate"], res["S_first"]["brick"])
        # NORMALIZED framing: residual = surrogate-captured group interactions
        # only (aggregate ST - S1); model-unresolved (V_tot-V_expl beyond seed)
        # is DROPPED. Render normalizes by sum of wedges (V_expl+V_seed+V_tipping).
        v_resid = max(1.0 - (s_emi + s_clim + s_brick), 0.0) * v_expl
        rows.append(dict(year=int(YEARS[it]), V_total=v_tot,
                         V_emissions=s_emi * v_expl, V_climate=s_clim * v_expl,
                         V_brick=s_brick * v_expl, V_seed=v_seed_full[it],
                         V_residual=v_resid, R2_oof=res["r2_oof"],
                         S_emi=s_emi, S_clim=s_clim, S_brick=s_brick,
                         ST_emi=res["S_total"]["emissions"],
                         ST_clim=res["S_total"]["climate"],
                         ST_brick=res["S_total"]["brick"]))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"v5_hybrid_decomp_{target_name}_clip.csv", index=False)
    print(f"  wrote clip+unclip ({time.time()-t0:.0f}s; R2@2150="
          f"{df[df.year==2150].R2_oof.values}, "
          f"emi S={df[df.year==2150].S_emi.values})", flush=True)


# --------------------------------------------------------------------------
# GMST pipeline (total / pulse) -> per-axis fraction CSV + standalone figure
# --------------------------------------------------------------------------
GMST_TARGETS = {
    "total_gmst": dict(loader="fair_cube_baseline", anchor=2020, smoothing=1,
                       internal="residual",
                       title="Total ΔGMST  (relative to 2020)",
                       ylabel="Fraction of ΔGMST variance",
                       axes_order=["internal", "climate", "emissions", "interactions"]),
    "pulse_gmst": dict(loader="fair_pulse_marginal", anchor=None,
                       smoothing=SMOOTH_WINDOW_YR_PULSE, internal="zero",
                       title="Pulse-marginal ΔGMST  (per GtCO₂, 2030 pulse)",
                       ylabel="Fraction of ΔGMST_pulse variance",
                       axes_order=["climate", "emissions", "interactions"]),
}


def run_gmst(key, years_idx):
    cfg = GMST_TARGETS[key]
    print(f"\n=== {key} (Group-Sobol) ===", flush=True)
    feat = assemble_features()
    years, M = load_target(cfg["loader"], feat, cfg["anchor"])
    if cfg["smoothing"] > 1:
        M = _smooth_traj(M, cfg["smoothing"])
        print(f"  smoothed ({cfg['smoothing']}-yr boxcar)", flush=True)
    w = feat["w_norm"].to_numpy(dtype=np.float64)
    feature_cols = RFF_FEATS + CFG_FEATURES
    Xv = feat[feature_cols].to_numpy(dtype=np.float64)
    gidx = _gidx_for(feature_cols, GROUPS_GMST)
    mono = mono_cst(feature_cols)

    t0 = time.time()
    results = Parallel(n_jobs=N_JOBS, verbose=5)(
        delayed(_sobol_year)(it, Xv, M[:, it].astype(np.float64), w,
                             gidx, mono, N_SOBOL, _seed_for(key, it))
        for it in years_idx)
    rows = []
    for res in sorted(results, key=lambda r: r["it"]):
        it = res["it"]
        v_tot = res["v_total"]
        v_expl = v_tot * max(res["r2_oof"], 0.0)
        s_emi, s_clim = res["S_first"]["emissions"], res["S_first"]["climate"]
        v_inter = max(1.0 - (s_emi + s_clim), 0.0) * v_expl   # emi×clim interaction
        v_int  = (v_tot - v_expl) if cfg["internal"] == "residual" else 0.0
        rows.append(dict(year=int(years[it]), V_total=v_tot,
                         emissions=s_emi * v_expl, climate=s_clim * v_expl,
                         internal=v_int, interactions=v_inter,
                         R2_oof=res["r2_oof"], S_emi=s_emi, S_clim=s_clim))
    print(f"  {key}: {len(rows)} yrs in {time.time()-t0:.0f}s", flush=True)

    df = pd.DataFrame(rows)
    # normalize to the rendered axes (matches existing GMST render convention:
    # the small group-interaction (1-S_emi-S_clim)*V_expl is dropped, exactly
    # as the SHAP version dropped cross-covariance)
    ax = cfg["axes_order"]
    denom = df[ax].sum(axis=1).replace(0, 1.0)
    frac = df[ax].divide(denom, axis=0)
    # display smoothing (per-year Sobol jitter), then renormalize to sum 1
    for a in ax:
        frac[a] = _smooth_disp(frac[a].to_numpy())
    s = frac[ax].sum(axis=1).replace(0, 1.0)
    frac[ax] = frac[ax].divide(s, axis=0)
    frac["year"] = df["year"].to_numpy()
    out_axis = frac[["year"] + ax]
    out_axis.to_csv(OUT / f"shapley_hs_per_axis_{key}.csv", index=False)
    print(f"  wrote {OUT}/shapley_hs_per_axis_{key}.csv", flush=True)

    _render_gmst(key, cfg, out_axis)
    print("  fractions at landmarks:", flush=True)
    for yy in LANDMARKS:
        if yy in out_axis.year.values:
            i = int(np.where(out_axis.year.values == yy)[0][0])
            print("    " + str(yy) + ": " +
                  " ".join(f"{a}={out_axis[a].iloc[i]:.3f}" for a in ax), flush=True)


def _render_gmst(key, cfg, frac_df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    label = {**AXIS_LABEL, "interactions": "Interactions (emissions × climate)"}
    color = {**AXIS_COLOR, "interactions": "#999999"}
    ax_cols = cfg["axes_order"]
    years = frac_df.year.to_numpy()
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.stackplot(years, *[frac_df[a].to_numpy() for a in ax_cols],
                 labels=[label[a] for a in ax_cols],
                 colors=[color[a] for a in ax_cols],
                 alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.set_xlim(years.min(), years.max())
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel(cfg["ylabel"], fontsize=11)
    method = ("Group-Sobol (LHS-10k_s cfg+RFF); V_internal = 0 (matched-seed pulse marginal)"
              if cfg["internal"] == "zero" else
              "Group-Sobol (LHS-10k_s cfg+RFF); V_internal = surrogate OOF residual (seed-LHS cube)")
    ax.set_title(f"{cfg['title']}\n{method}", fontsize=12, fontweight="bold", color="#1F4E79")
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="center right", fontsize=9.5, framealpha=0.92)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / f"shapley_hs_{key}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"shapley_hs_{key}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {OUT}/shapley_hs_{key}.{{png,pdf}}", flush=True)


# --------------------------------------------------------------------------
def main():
    quick = os.environ.get("HS_QUICK", "").strip() == "1"
    only = set(s.strip() for s in os.environ.get("HS_ONLY", "").split(",") if s.strip())
    years_idx = ([int(np.where(YEARS == y)[0][0]) for y in LANDMARKS] if quick
                 else list(range(len(YEARS))))
    print(f"[config] quick={quick}  n_years={len(years_idx)}  N_SOBOL={N_SOBOL}", flush=True)

    def want(k): return (not only) or (k in only)

    if want("total_gmst"): run_gmst("total_gmst", years_idx)
    if want("pulse_gmst"): run_gmst("pulse_gmst", years_idx)
    if want("total_slr"):  run_slr("total", years_idx)
    if want("pulse_slr"):  run_slr("pulse", years_idx)
    print("\nDONE.", flush=True)


if __name__ == "__main__":
    main()
