"""
shapley_hawkins_sutton.py
=========================

Unified Shapley-based Hawkins-Sutton variance decomposition pipeline that
produces FOUR H-S figures from the v1.4.5 LHS-10k ensemble:

  1. Total ΔGMST(t) — variance of cell-to-cell GMST relative to 2020
  2. Total ΔSLR(t)  — variance of cell-to-cell SLR  relative to 2020
  3. Pulse ΔGMST(t) — variance of per-cell paired (pulse − base) ΔGMST
  4. Pulse ΔSLR(t)  — variance of per-cell paired (pulse − base) ΔSLR

The LHS-10k cube is single-seeded by design (seed_idx = 0 for all
10,000 cells), so it contains zero V_internal contribution: cell-to-
cell variance at any year is purely cfg + RFF driven. V_internal
therefore CANNOT be recovered from a residual-of-surrogate-fit on
LHS-10k; the residual is surrogate modeling error, not seed noise.
The fix: take V_internal from the matching v1.4.5 ANOVA-18k cube
(3 seeds × ~6 cfgs × ~1000 RFFs, bias-corrected per Searle 2006), and
stack it on top of the LHS-10k Shapley axes on the combined variance
scale (LHS V_cfg+V_RFF + ANOVA V_seed).
  outputs/substack/updated_hawkins_sutton_data.csv  (V_internal for GMST)
  outputs/plots/hawkins_sutton_slr_4way.csv         (V_internal for SLR)

For the PULSE figures the matched-seed paired difference cancels
stochastic seed noise by construction (and LHS-10k single-seed makes
it exactly zero), so V_internal is dropped from those decompositions
entirely.

Outliers (AIS pulse-induced tipping cells) are clipped at p99 for the
pulse-SLR target only — they don't appear in the linear-regime
pulse-marginal that this Shapley decomp characterizes. See the
docstring of the previous `shapley_hawkins_sutton_pulse.py` for the
methodological motivation.

Methodology — PER-YEAR Shapley surrogate:
  • Separate HistGradientBoosting surrogate fitted per year on the
    10,000-cell static-feature panel (no `year` feature). Replaces the
    earlier time-as-feature stacked-panel approach because the stacked
    surrogate produced artifacts at low-signal years.
  • SHAP TreeExplainer per year, aggregated to source-axis-level
    Shapley effects.
  • Importance weights from Wong (2026) are applied in the SHAP-
    variance aggregation, not in the surrogate fit (ESS=3815/10000
    is concentrated enough that weighted fitting would exclude ~60%
    of cells and break held-out generalization).

Outputs (in outputs/substack/):
  shapley_hs_total_gmst.{png,pdf}
  shapley_hs_total_slr.{png,pdf}
  shapley_hs_pulse_gmst.{png,pdf}
  shapley_hs_pulse_slr.{png,pdf}
  shapley_hs_per_feature_<target>.csv   per-year per-feature SHAP variance
  shapley_hs_per_axis_<target>.csv      per-year per-axis aggregation
"""
from __future__ import annotations
import sys
from pathlib import Path
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)
FAI  = Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI"

SLIM_BASE_CSV    = ROOT / "outputs/brick_v145_slim/brick_lhs10k_baseline_to2300_weighted.csv"
FULL_BASE_CSV    = ROOT / "outputs/brick_v145/brick_lhs10k_baseline.csv"
FULL_PULSE_CSV   = ROOT / "outputs/brick_v145/brick_lhs10k_pulse_co2_pos_001gt.csv"
CUBE_BASE        = FAI / "fair_outputs/cubes_v145/cube_v145_lhs10k_baseline.npz"
CUBE_PULSE       = FAI / "fair_outputs/cubes_v145/cube_v145_lhs10k_pulse_co2_pos_001gt.npz"
RFF_FEATURES     = ROOT / "outputs/rff_summary_features.csv"
CFG_PARAMS_CSV   = FAI / "calibration_v145/calibrated_constrained_parameters_1.4.5.csv"
POST_PARAMS_CSV  = ROOT / "data/MimiBRICK/parameters_subsample_brick.csv"

# Existing V_internal source CSVs (bias-corrected per 2026-05-26 fix)
TOTAL_GMST_VINT_CSV = ROOT / "outputs/substack/updated_hawkins_sutton_data.csv"  # var_internal col
TOTAL_SLR_VINT_CSV  = ROOT / "outputs/plots/hawkins_sutton_slr_4way.csv"          # V_internal col

PULSE_SIZE_GTCO2 = 0.01
YEAR_LO, YEAR_HI = 2020, 2150
SMOOTH_WINDOW_YR_PULSE = 5
OUTLIER_PERCENTILE = 99.0

CFG_FEATURES = [
    # Climate sensitivity / ocean heat uptake
    "forcing_4co2",
    "ocean_heat_capacity[0]", "ocean_heat_capacity[1]", "ocean_heat_capacity[2]",
    "ocean_heat_transfer[0]", "ocean_heat_transfer[1]", "ocean_heat_transfer[2]",
    "deep_ocean_efficacy",
    # Carbon cycle
    "iirf_0[CO2]", "iirf_uptake[CO2]", "iirf_temperature[CO2]", "iirf_airborne[CO2]",
    # Aerosol-radiation interactions (ERFari)
    "erfari_radiative_efficiency[BC]",
    "erfari_radiative_efficiency[OC]",
    "erfari_radiative_efficiency[Sulfur]",
    "erfari_radiative_efficiency[NOx]",
    "erfari_radiative_efficiency[VOC]",
    "erfari_radiative_efficiency[NH3]",
    # Aerosol-cloud interactions (ERFaci)
    "aci_shape[Sulfur]", "aci_shape[BC]", "aci_shape[OC]", "aci_scale",
    # CH4 / N2O forcing scaling
    "forcing_scale[CH4]", "forcing_scale[N2O]",
    # FaIR stochastic noise amplitudes
    "sigma_eta", "sigma_xi",
]
POST_FEATURES = [
    "thermal_alpha", "thermal_s0",
    "glaciers_beta0", "glaciers_v0", "glaciers_s0", "glaciers_n",
    "greenland_a", "greenland_b", "greenland_alpha", "greenland_beta", "greenland_v0",
    "antarctic_alpha", "antarctic_gamma", "antarctic_mu", "antarctic_nu",
    "antarctic_kappa", "antarctic_precip0", "antarctic_flow0",
    "antarctic_temp_threshold", "anto_alpha", "anto_beta",
]
RFF_FEATURES_LIST = [
    "cum_co2_2030", "cum_co2_2100", "cum_co2_2300",
    "peak_co2_emissions", "peak_co2_year",
    "slope_co2_2050_2100", "frac_negative_post_2050",
    "cum_ch4_2100",
]
KEY_COLS = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]

AXIS_OF = {**{f: "climate" for f in CFG_FEATURES},
           **{f: "brick" for f in POST_FEATURES},
           **{f: "emissions" for f in RFF_FEATURES_LIST}}

AXIS_LABEL = {
    "emissions": "Emissions (RFF-SP)",
    "climate":   "Climate response (FaIR cfg)",
    "brick":     "BRICK posterior",
    "internal":  "Internal variability (FaIR seed)",
}
AXIS_COLOR = {
    "emissions": "#d95f02",
    "climate":   "#7570b3",
    "internal":  "#1b9e77",
    "brick":     "#e7298a",
}


# ============================================================================
# Target configurations
# ============================================================================
TARGETS = [
    {
        "key":            "total_gmst",
        "title":          "Total ΔGMST  (relative to 2020)",
        "ylabel":         "Fraction of ΔGMST variance",
        "loader":         "fair_cube_baseline",
        "anchor_year":    2020,
        "use_brick_features":  False,
        "clip_outliers":  False,
        "smoothing":      1,
        "axes_order":     ["emissions", "climate", "internal"],
        "v_internal_csv": TOTAL_GMST_VINT_CSV,
        "v_internal_col": "var_internal",
    },
    {
        "key":            "total_slr",
        "title":          "Total ΔSLR  (relative to 2020)",
        "ylabel":         "Fraction of ΔSLR variance",
        "loader":         "brick_baseline_slr",
        "anchor_year":    2020,
        "use_brick_features":  True,
        "clip_outliers":  False,
        "smoothing":      1,
        "axes_order":     ["emissions", "climate", "brick", "internal"],
        "v_internal_csv": TOTAL_SLR_VINT_CSV,
        "v_internal_col": "V_internal",
    },
    {
        "key":            "pulse_gmst",
        "title":          "Pulse-marginal ΔGMST  (per GtCO₂, 2030 pulse)",
        "ylabel":         "Fraction of ΔGMST_pulse variance",
        "loader":         "fair_pulse_marginal",
        "anchor_year":    None,
        "use_brick_features":  False,
        "clip_outliers":  False,
        "smoothing":      SMOOTH_WINDOW_YR_PULSE,
        "axes_order":     ["emissions", "climate"],
        "v_internal_csv": None,           # matched-seed paired marginal cancels seed noise;
        "v_internal_col": None,           # LHS-10k single-seed makes it exactly 0 here
    },
    {
        "key":            "pulse_slr",
        "title":          "Pulse-marginal ΔSLR  (per GtCO₂, 2030 pulse, linear regime)",
        "ylabel":         "Fraction of ΔSLR_pulse variance",
        "loader":         "brick_pulse_marginal",
        "anchor_year":    None,
        "use_brick_features":  True,
        "clip_outliers":  True,
        "smoothing":      SMOOTH_WINDOW_YR_PULSE,
        "axes_order":     ["emissions", "climate", "brick"],
        "v_internal_csv": None,
        "v_internal_col": None,
    },
]


# ============================================================================
# Helpers
# ============================================================================
def _smooth_traj(M, window):
    if window <= 1:
        return M
    n_cells, n_yr = M.shape
    pad = window // 2
    Mp = np.pad(M, ((0, 0), (pad, pad)), mode="edge")
    csum = np.cumsum(Mp, axis=1)
    csum = np.concatenate([np.zeros((n_cells, 1)), csum], axis=1)
    return (csum[:, window:] - csum[:, :-window]) / window


def assemble_features():
    """Load slim baseline + Wong weights + cfg + post + RFF features.
    Returns (df, key sort applied)."""
    slim = pd.read_csv(SLIM_BASE_CSV, usecols=KEY_COLS + ["w_norm"])
    rff = pd.read_csv(RFF_FEATURES, usecols=["rff_idx"] + RFF_FEATURES_LIST)
    cfg = pd.read_csv(CFG_PARAMS_CSV, usecols=lambda c: c == "" or c in CFG_FEATURES)
    cfg = cfg.reset_index().rename(columns={"index": "fair_cfg_idx"})
    cfg = cfg[["fair_cfg_idx"] + CFG_FEATURES]
    post = pd.read_csv(POST_PARAMS_CSV, usecols=POST_FEATURES)
    post = post.reset_index().rename(columns={"index": "post_idx"})
    df = slim.merge(rff, on="rff_idx").merge(cfg, on="fair_cfg_idx").merge(post, on="post_idx")
    df = df.sort_values(KEY_COLS).reset_index(drop=True)
    return df


def load_target(loader: str, keys_ref: pd.DataFrame, anchor_year: int | None):
    """Returns (years, M) where M shape (n_cells, n_yr). keys_ref provides
    the canonical row ordering."""
    print(f"  [load_target] loader={loader}, anchor_year={anchor_year}", flush=True)
    year_cols_brick = [f"slr_{y}" for y in range(YEAR_LO, YEAR_HI + 1)]
    years = np.arange(YEAR_LO, YEAR_HI + 1)
    keys_sorted = keys_ref[KEY_COLS].sort_values(KEY_COLS).reset_index(drop=True)

    if loader == "fair_cube_baseline":
        c = np.load(CUBE_BASE, allow_pickle=True)
        cm = np.asarray(c["cells_meta"], dtype=np.int64)
        yrs_c = np.asarray(c["years"], dtype=np.int64)
        gmst = np.asarray(c["gmst_traj"], dtype=np.float64)
        i_lo = int(np.where(yrs_c == YEAR_LO)[0][0])
        i_hi = int(np.where(yrs_c == YEAR_HI)[0][0])
        cube_M = gmst[:, i_lo:i_hi+1]
        # Map cube cells_meta (rff, cfg, seed) to keys_sorted via (rff,cfg,seed)
        cube_keys = pd.DataFrame(cm[:, :3], columns=["rff_idx", "fair_cfg_idx", "seed_idx"])
        cube_keys["_cube_row"] = np.arange(len(cube_keys))
        merged = keys_sorted.merge(cube_keys, on=["rff_idx", "fair_cfg_idx", "seed_idx"], how="left")
        if merged["_cube_row"].isna().any():
            sys.exit("fair_cube_baseline: cell mismatch with slim CSV")
        M = cube_M[merged["_cube_row"].to_numpy(dtype=int)]
        if anchor_year is not None:
            i_a = int(np.where(years == anchor_year)[0][0])
            M = M - M[:, [i_a]]
        return years, M

    if loader == "fair_pulse_marginal":
        cb = np.load(CUBE_BASE, allow_pickle=True)
        cp = np.load(CUBE_PULSE, allow_pickle=True)
        assert (cb["cells_meta"] == cp["cells_meta"]).all()
        yrs_c = np.asarray(cb["years"], dtype=np.int64)
        i_lo = int(np.where(yrs_c == YEAR_LO)[0][0])
        i_hi = int(np.where(yrs_c == YEAR_HI)[0][0])
        marg = (np.asarray(cp["gmst_traj"], dtype=np.float64) -
                np.asarray(cb["gmst_traj"], dtype=np.float64))[:, i_lo:i_hi+1] / PULSE_SIZE_GTCO2
        cube_keys = pd.DataFrame(cb["cells_meta"][:, :3], columns=["rff_idx","fair_cfg_idx","seed_idx"])
        cube_keys["_cube_row"] = np.arange(len(cube_keys))
        merged = keys_sorted.merge(cube_keys, on=["rff_idx","fair_cfg_idx","seed_idx"], how="left")
        M = marg[merged["_cube_row"].to_numpy(dtype=int)]
        return years, M

    if loader == "brick_baseline_slr":
        base = pd.read_csv(FULL_BASE_CSV, usecols=KEY_COLS + year_cols_brick)
        base = base.sort_values(KEY_COLS).reset_index(drop=True)
        assert (base[KEY_COLS].to_numpy() == keys_sorted.to_numpy()).all()
        M = base[year_cols_brick].to_numpy(dtype=np.float64)
        if anchor_year is not None:
            i_a = int(np.where(years == anchor_year)[0][0])
            M = M - M[:, [i_a]]
        return years, M

    if loader == "brick_pulse_marginal":
        base = pd.read_csv(FULL_BASE_CSV, usecols=KEY_COLS + year_cols_brick)
        pulse = pd.read_csv(FULL_PULSE_CSV, usecols=KEY_COLS + year_cols_brick)
        base = base.sort_values(KEY_COLS).reset_index(drop=True)
        pulse = pulse.sort_values(KEY_COLS).reset_index(drop=True)
        assert (base[KEY_COLS].to_numpy() == pulse[KEY_COLS].to_numpy()).all()
        M = (pulse[year_cols_brick].to_numpy(dtype=np.float64) -
             base[year_cols_brick].to_numpy(dtype=np.float64)) / PULSE_SIZE_GTCO2
        return years, M

    raise ValueError(f"unknown loader {loader}")


def fit_and_shap(feat_df, years, M, target):
    """Per-year-surrogate Shapley pipeline.

    Replaces the earlier time-as-feature stacked-panel approach because
    the stacked surrogate produced an artifact: at low-signal years
    (e.g., 2021, where ΔGMST from 2020 anchor is dominated by 1-year FaIR
    seed noise) the cross-year-trained model still predicted cell-
    specific values using cfg features, depressing the residual and
    therefore depressing V_internal. The canonical Hawkins-Sutton
    expectation of V_internal ≈ 100% at near-term is recovered by
    fitting a SEPARATE surrogate per year. At year 2021 the per-year
    surrogate has R² ≈ 0 (it can't predict seed noise from static
    features), so the residual ≈ V_total → V_internal fraction near 100%.

    For each year t in `years`:
      1. Fit HistGradientBoostingRegressor on the 10,000 cells with target
         M[:, t] and static features X_static (no year feature).
      2. Compute SHAP TreeExplainer values across cells.
      3. Compute V_total, V_residual, per-feature variance of SHAP.

    Per-year fit is fast (~1-2 sec on 10,000 cells); 131 years × 4 targets
    fits cleanly into ~20-30 min total.
    """
    from sklearn.ensemble import HistGradientBoostingRegressor
    import shap

    use_brick = target["use_brick_features"]
    feature_cols = (RFF_FEATURES_LIST + CFG_FEATURES + (POST_FEATURES if use_brick else []))
    feature_names = list(feature_cols)
    n_cells, n_yr = M.shape

    # Optional outlier clipping
    if target["clip_outliers"]:
        cap = float(np.percentile(M, OUTLIER_PERCENTILE))
        n_out = int((M.max(axis=1) > cap).sum())
        print(f"  outlier clip p{OUTLIER_PERCENTILE:.0f} = {cap:.4g}: "
              f"{n_out} cells ({100*n_out/n_cells:.2f}%) flagged", flush=True)
        M = np.clip(M, None, cap)

    # Optional smoothing
    if target["smoothing"] > 1:
        M = _smooth_traj(M, target["smoothing"])
        print(f"  smoothed ({target['smoothing']}-yr boxcar)", flush=True)

    X_static = feat_df[feature_cols].to_numpy(dtype=np.float64)
    w_cell = feat_df["w_norm"].to_numpy(dtype=np.float64)
    print(f"  per-year fits: {n_yr} years × ({n_cells} cells × {len(feature_cols)} features)", flush=True)

    # Per-year results
    sh_per_year = np.zeros((n_yr, len(feature_names)))
    v_total = np.zeros(n_yr)
    v_residual = np.zeros(n_yr)
    r2_per_year = np.zeros(n_yr)

    # Train/test split for diagnostic (single fixed split across years for
    # consistency; per-year R² reported as average across all years).
    rng = np.random.default_rng(2026)
    perm = rng.permutation(n_cells)
    n_te = n_cells // 5
    te_idx = perm[:n_te]
    tr_idx = perm[n_te:]

    t0 = time.time()
    for it, y in enumerate(years):
        y_target = M[:, it]
        # Per-year fit. Smaller trees + more conservative regularization
        # than the stacked-panel version since each year has only 10000
        # samples (vs 1.31M for the stacked panel).
        m = HistGradientBoostingRegressor(
            max_iter=200, max_leaf_nodes=15, learning_rate=0.05,
            min_samples_leaf=30, l2_regularization=1.0, random_state=2026,
        )
        m.fit(X_static[tr_idx], y_target[tr_idx])
        r2_per_year[it] = m.score(X_static[te_idx], y_target[te_idx])

        # Refit on full data for SHAP
        m_full = HistGradientBoostingRegressor(
            max_iter=200, max_leaf_nodes=15, learning_rate=0.05,
            min_samples_leaf=30, l2_regularization=1.0, random_state=2026,
        )
        m_full.fit(X_static, y_target)

        yhat = m_full.predict(X_static)
        explainer = shap.TreeExplainer(m_full)
        shvals = explainer.shap_values(X_static)

        wsum = w_cell.sum()
        mu_y = (y_target * w_cell).sum() / wsum
        v_total[it] = ((y_target - mu_y) ** 2 * w_cell).sum() / wsum
        v_residual[it] = (((y_target - yhat) ** 2) * w_cell).sum() / wsum
        mu_sh = (shvals * w_cell[:, None]).sum(axis=0) / wsum
        sh_per_year[it] = ((shvals - mu_sh) ** 2 * w_cell[:, None]).sum(axis=0) / wsum

        if (it+1) % 20 == 0 or it == 0 or it == n_yr-1:
            print(f"    year {y}: fit + SHAP done ({time.time()-t0:.1f}s elapsed; "
                  f"R²={r2_per_year[it]:.3f}  V_total={v_total[it]:.4g}  "
                  f"V_res/V_total={v_residual[it]/max(v_total[it],1e-30):.3f})", flush=True)

    mean_r2 = float(np.mean(r2_per_year[(r2_per_year > -1e6)]))   # exclude crazy outliers
    print(f"  per-year R²: mean = {mean_r2:.3f}  "
          f"(at 2021: {r2_per_year[2021-years[0]]:.3f}, "
          f"at 2100: {r2_per_year[2100-years[0]]:.3f}, "
          f"at 2150: {r2_per_year[2150-years[0]]:.3f})", flush=True)
    return feature_names, sh_per_year, v_total, v_residual, mean_r2, mean_r2


def load_v_internal_for_total(target, years):
    if target["v_internal_csv"] is None:
        return None
    df = pd.read_csv(target["v_internal_csv"])
    if "year" not in df.columns or target["v_internal_col"] not in df.columns:
        sys.exit(f"V_internal CSV {target['v_internal_csv']} missing year or {target['v_internal_col']}")
    return df.set_index("year")[target["v_internal_col"]].reindex(years).fillna(0.0).to_numpy()


def render_figure(target, feature_names, sh_var, v_internal_anova, years, v_total, v_residual):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    feat_axis = {f: ("year" if f == "year" else AXIS_OF.get(f, "other")) for f in feature_names}
    rows = []
    for it, y in enumerate(years):
        for j, f in enumerate(feature_names):
            rows.append({"year": int(y), "feature": f, "axis": feat_axis[f],
                          "V_shap": float(sh_var[it, j])})
    long_df = pd.DataFrame(rows)
    long_df.to_csv(OUT / f"shapley_hs_per_feature_{target['key']}.csv", index=False)

    axis_df = (long_df[long_df.axis.isin(["emissions", "climate", "brick"])]
                .groupby(["year", "axis"], as_index=False)["V_shap"].sum())
    pivot = axis_df.pivot(index="year", columns="axis", values="V_shap").reindex(years).fillna(0.0)

    # V_internal handling. The LHS-10k cube is single-seeded
    # (seed_idx = 0 for all 10,000 cells), so the LHS-10k residual is
    # surrogate modeling error, NOT internal variability. Correct V_int
    # source for TOTAL targets is the v1.4.5 ANOVA-18k cube (3 seed
    # replicates per cfg×RFF; bias-corrected per Searle 2006), loaded
    # via `v_internal_anova` from the matching ANOVA-18k CSV. PULSE
    # targets get V_internal = 0 because matched-seed paired marginals
    # cancel seed noise by construction; the LHS-10k surrogate residual
    # there is purely modeling gap and should not be drawn as V_int.
    axes_order = target["axes_order"]
    ax_cols = list(axes_order)
    for a in ax_cols:
        if a not in pivot.columns and a != "internal":
            pivot[a] = 0.0
    if "internal" in ax_cols:
        if v_internal_anova is not None:
            pivot["internal"] = v_internal_anova
        else:
            pivot["internal"] = 0.0
    # Normalize to sum of all axes (Shapley + V_internal_ANOVA)
    total = pivot[ax_cols].sum(axis=1).replace(0, 1.0)
    frac = pivot[ax_cols].divide(total, axis=0)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.stackplot(years, *[frac[a].to_numpy() for a in ax_cols],
                 labels=[AXIS_LABEL[a] for a in ax_cols],
                 colors=[AXIS_COLOR[a] for a in ax_cols],
                 alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.set_xlim(YEAR_LO, YEAR_HI)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel(target["ylabel"], fontsize=11)
    is_pulse_target = "pulse" in target["key"]
    method = ("Shapley TreeExplainer (LHS-10k cfg+RFF); V_internal = 0 (matched-seed pulse marginal)"
              if is_pulse_target else
              "Shapley TreeExplainer (LHS-10k cfg+RFF); V_internal from v1.4.5 ANOVA-18k seed replicates")
    ax.set_title(f"{target['title']}\n{method}",
                 fontsize=12, fontweight="bold", color="#1F4E79")
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="center right", fontsize=9.5, framealpha=0.92)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    k = target["key"]
    fig.savefig(OUT / f"shapley_hs_{k}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"shapley_hs_{k}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {OUT / f'shapley_hs_{k}.png'}", flush=True)

    # Persist axis-aggregated time series
    out_axis = frac.copy()
    out_axis["year"] = years
    out_axis.to_csv(OUT / f"shapley_hs_per_axis_{target['key']}.csv", index=False)

    # Headline numbers
    print(f"  Fractions at landmark years:")
    for y in (2050, 2100, 2150):
        i = int(np.where(years == y)[0][0])
        parts = [f"{a}={frac[a].iloc[i]:.2f}" for a in ax_cols]
        print(f"    {y}: " + " ".join(parts), flush=True)


def main():
    print("[features] assembling per-cell covariates", flush=True)
    feat = assemble_features()
    print(f"  {len(feat)} cells × {feat.shape[1]} cols", flush=True)

    for target in TARGETS:
        print(f"\n=== {target['key']} : {target['title']} ===", flush=True)
        years, M = load_target(target["loader"], feat, target["anchor_year"])
        print(f"  target M shape {M.shape}", flush=True)
        feature_names, sh_var, v_total, v_residual, train_r2, test_r2 = fit_and_shap(feat, years, M, target)
        v_int_anova = load_v_internal_for_total(target, years)
        render_figure(target, feature_names, sh_var, v_int_anova, years, v_total, v_residual)


if __name__ == "__main__":
    main()
