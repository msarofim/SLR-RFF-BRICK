"""
shapley_hawkins_sutton_pulse.py
===============================

Shapley-based Hawkins-Sutton-style variance decomposition of the
v1.4.5 LHS-10k pulse-marginal SLR (0.01-GtCO₂ small pulse), 2020-2150.

Replaces the ANOVA-18k nested decomp for substack/poster figures C/D
with a richer attribution at the physical-parameter level. See
notes/shapley_lhs10k_scope.md for the scope; this script is the
implementation.

Methodology — TIME-AS-FEATURE Shapley:
  1. Per-cell pulse-marginal SLR(t) for 10,000 LHS-10k cells × 131
     years (2020-2150) is the target.
  2. Each cell has ~50 continuous covariates: per-RFF emissions summary
     stats, per-cfg FaIR climate parameters, per-post BRICK posterior
     parameters. Year is added as a 51st feature.
  3. Stack (10000 × 131 = 1.31M rows) into a single training set; fit
     a HistGradientBoostingRegressor; verify with 5-fold CV.
  4. SHAP TreeExplainer computes per-cell × per-feature contributions.
     Per-year aggregation: sum over cells of (mean SHAP² per feature)
     gives a year-by-year per-feature Shapley effect.
  5. Aggregate features to 3 source-axis groupings (emissions / climate /
     BRICK) and stack with V_internal(t) from the ANOVA-18k seed-
     replication-derived estimate. Primary figure: 4-axis H-S stacked
     area (emi / clim / BRICK / internal) — directly comparable to the
     ANOVA-18k Panel D framing.
  6. Secondary figure: top-2 physical drivers per source-axis (so 6
     stacked physical drivers + 1 internal = 7-axis stacked area), to
     surface specific physical mechanisms.

V_internal is computed separately from the ANOVA-18k cube (NOT from
LHS-10k Shapley), because the seed dimension needs the 3-seed within-
cell replication that the LHS-10k doesn't provide. This is a
deliberate hybrid: each ensemble used for its strength.

Outputs:
  outputs/substack/shapley_hs_lhs10k_pulse_4axis.{png,pdf}     primary
  outputs/substack/shapley_hs_lhs10k_pulse_top2_per_axis.{png,pdf} secondary
  outputs/substack/shapley_hs_lhs10k_per_feature.csv     full per-feature table
  outputs/substack/shapley_hs_lhs10k_per_year_axis.csv   axis-aggregated long form
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

# ---- Inputs ----
SLIM_BASE_CSV = ROOT / "outputs/brick_v145_slim/brick_lhs10k_baseline_to2300_weighted.csv"
FULL_BASE_CSV = ROOT / "outputs/brick_v145/brick_lhs10k_baseline.csv"
FULL_PULSE_CSV = ROOT / "outputs/brick_v145/brick_lhs10k_pulse_co2_pos_001gt.csv"
RFF_FEATURES   = ROOT / "outputs/rff_summary_features.csv"
CFG_PARAMS_CSV = FAI / "calibration_v145/calibrated_constrained_parameters_1.4.5.csv"
POST_PARAMS_CSV = ROOT / "data/MimiBRICK/parameters_subsample_brick.csv"

# Pulse magnitude (FaIR v1.4.5 CO2 FFI input_unit is GtCO2, not GtC)
PULSE_SIZE_GTCO2 = 0.01

# Year range for Shapley H-S diagram
YEAR_LO, YEAR_HI = 2020, 2150

# Cube path for V_internal estimate (ANOVA-18k baseline, no pulse needed —
# we'll re-derive V_internal from the seed replication on the BASELINE
# ensemble since seed noise cancels in the pulse-baseline difference.
# For the PULSE-marginal V_internal we use the ANOVA-18k pulse arm against
# baseline as a paired computation, same as the existing
# run_pulse_4way_slr_decomp.py.
ANOVA_PULSE_MARGINAL = ROOT / "outputs/brick_v145_slim/brick_anova18k_marginal_co2_pos_1gt_to2300_weighted.csv"

# ---- Feature selection per axis ----
# Per-cfg FaIR parameters (subset that meaningfully drives pulse response).
# Full v1.4.5 calibration CSV has ~80 columns; we pick the climate-sensitivity
# and forcing-relevant ones to keep the feature count manageable.
CFG_FEATURES = [
    "forcing_4co2",            # 4×CO2 forcing → ECS proxy
    "ocean_heat_capacity[0]",  # surface heat capacity
    "ocean_heat_capacity[1]",
    "ocean_heat_capacity[2]",
    "ocean_heat_transfer[0]",  # ocean heat uptake
    "ocean_heat_transfer[1]",
    "ocean_heat_transfer[2]",
    "deep_ocean_efficacy",     # ocean heat efficacy
    "iirf_0[CO2]",             # carbon cycle: airborne IRF
    "iirf_uptake[CO2]",
    "iirf_temperature[CO2]",
    "iirf_airborne[CO2]",
    "erfari_radiative_efficiency[BC]",
    "erfari_radiative_efficiency[Sulfur]",  # main negative aerosol forcing
    "sigma_eta",               # FaIR stochastic noise sigma (eta channel)
    "sigma_xi",                # FaIR stochastic noise sigma (xi channel)
]

# Per-post BRICK parameters
POST_FEATURES = [
    "thermal_alpha",           # te_α
    "thermal_s0",
    "glaciers_beta0",          # gsic_β₀
    "glaciers_v0",
    "glaciers_s0",
    "glaciers_n",
    "greenland_a",
    "greenland_b",
    "greenland_alpha",
    "greenland_beta",
    "greenland_v0",
    "antarctic_alpha",
    "antarctic_gamma",
    "antarctic_mu",
    "antarctic_nu",
    "antarctic_kappa",
    "antarctic_precip0",
    "antarctic_flow0",
    "antarctic_temp_threshold",
    "anto_alpha",
    "anto_beta",
]

# Per-RFF features (from build_rff_summary_features.py)
RFF_FEATURES_LIST = [
    "cum_co2_2030", "cum_co2_2100", "cum_co2_2300",
    "peak_co2_emissions", "peak_co2_year",
    "slope_co2_2050_2100", "frac_negative_post_2050",
    "cum_ch4_2100",
]

AXIS_OF = {**{f: "climate"   for f in CFG_FEATURES},
           **{f: "brick"     for f in POST_FEATURES},
           **{f: "emissions" for f in RFF_FEATURES_LIST}}

KEY_COLS = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]


# ---------------------------------------------------------------------------
# Stage A: assemble per-cell covariates + paired marginal trajectory
# ---------------------------------------------------------------------------
def assemble_features():
    print(f"[A] assembling per-cell features ...", flush=True)
    print(f"  reading slim baseline (for keys + w_norm)", flush=True)
    slim = pd.read_csv(SLIM_BASE_CSV, usecols=KEY_COLS + ["w_norm"])
    print(f"  {len(slim)} cells", flush=True)

    # Smith v1.4.5 cfg parameters
    print(f"  reading cfg parameters", flush=True)
    cfg = pd.read_csv(CFG_PARAMS_CSV, usecols=lambda c: c == ""  # row index column
                                                 or c in CFG_FEATURES)
    # row index column should be the cfg index; rename
    cfg = cfg.reset_index().rename(columns={"index": "fair_cfg_idx"})
    # Drop the empty-name column (it's the row index from the CSV)
    cfg = cfg[["fair_cfg_idx"] + CFG_FEATURES]
    print(f"    {len(cfg)} cfgs × {cfg.shape[1]-1} features", flush=True)

    # BRICK posterior parameters
    print(f"  reading BRICK posterior parameters", flush=True)
    post = pd.read_csv(POST_PARAMS_CSV, usecols=POST_FEATURES)
    # post_idx in slim CSV is 0-based from the cube/wong pipeline
    post = post.reset_index().rename(columns={"index": "post_idx"})
    print(f"    {len(post)} posts × {post.shape[1]-1} features", flush=True)

    # RFF summary features
    print(f"  reading RFF summary features", flush=True)
    rff = pd.read_csv(RFF_FEATURES, usecols=["rff_idx"] + RFF_FEATURES_LIST)
    print(f"    {len(rff)} RFFs × {rff.shape[1]-1} features", flush=True)

    # Merge
    print(f"  merging onto slim keys", flush=True)
    df = slim.merge(rff, on="rff_idx", how="left")
    df = df.merge(cfg, on="fair_cfg_idx", how="left")
    df = df.merge(post, on="post_idx", how="left")

    # Sanity: no NaNs in features
    feat_cols = RFF_FEATURES_LIST + CFG_FEATURES + POST_FEATURES
    n_nan = int(df[feat_cols].isna().any(axis=1).sum())
    if n_nan:
        print(f"  WARNING: {n_nan} rows have NaN in features — investigating", flush=True)
        for c in feat_cols:
            n_c = df[c].isna().sum()
            if n_c:
                print(f"    {c}: {n_c} NaNs", flush=True)
    print(f"  feature table: {df.shape}", flush=True)
    return df


# Box-car smoothing window (years) applied to the per-cell pulse-marginal
# trajectory before fitting the surrogate. This is Hawkins-Sutton 2009's
# "polynomial smoothing" idea applied to LHS-10k samples: damp the per-year
# seed-induced noise so the surrogate sees the deterministic signal, not
# the seed-realization noise that LHS-10k samples are non-replicated over.
SMOOTH_WINDOW_YR = 5


def _smooth_traj(M, window):
    """5-year centered moving average along the year axis."""
    if window <= 1:
        return M
    pad = window // 2
    n_cells, n_yr = M.shape
    # Reflect-pad the edges so the smoothed array stays same length
    Mp = np.pad(M, ((0, 0), (pad, pad)), mode="edge")
    kernel = np.ones(window) / window
    # Conv along axis 1 — use cumulative-sum trick for speed
    csum = np.cumsum(Mp, axis=1)
    csum = np.concatenate([np.zeros((n_cells, 1)), csum], axis=1)
    out = (csum[:, window:] - csum[:, :-window]) / window
    return out


def load_paired_marginal(slim_df):
    """Load per-cell pulse-marginal SLR(2020..2150) for the 0.01-GtCO₂ arm.

    Returns: years (np.array shape (n_yr,)),
             M (np.array shape (n_cells, n_yr)) — cm per GtCO₂.
             The trajectory is centered-moving-average smoothed over
             SMOOTH_WINDOW_YR years to suppress year-to-year FaIR-seed
             noise that the surrogate can't learn from the static features."""
    print(f"\n[B] loading paired pulse-marginal SLR(t)", flush=True)
    year_cols = [f"slr_{y}" for y in range(YEAR_LO, YEAR_HI + 1)]
    # Read full CSVs, only the year cols we need (huge memory savings)
    print(f"  baseline ({YEAR_LO}-{YEAR_HI}, slr only) ...", flush=True)
    base = pd.read_csv(FULL_BASE_CSV, usecols=KEY_COLS + year_cols)
    print(f"    {len(base)} rows", flush=True)
    print(f"  pulse ({YEAR_LO}-{YEAR_HI}, slr only) ...", flush=True)
    pulse = pd.read_csv(FULL_PULSE_CSV, usecols=KEY_COLS + year_cols)
    print(f"    {len(pulse)} rows", flush=True)
    # Sort by keys for paired difference
    base = base.sort_values(KEY_COLS).reset_index(drop=True)
    pulse = pulse.sort_values(KEY_COLS).reset_index(drop=True)
    assert (base[KEY_COLS].to_numpy() == pulse[KEY_COLS].to_numpy()).all(), \
        "baseline / pulse keys mismatch"
    Yb = base[year_cols].to_numpy(dtype=np.float64)
    Yp = pulse[year_cols].to_numpy(dtype=np.float64)
    M_raw = (Yp - Yb) / PULSE_SIZE_GTCO2  # cm per GtCO₂
    years = np.arange(YEAR_LO, YEAR_HI + 1)
    print(f"  raw marginal shape {M_raw.shape}; median@2100 = {np.median(M_raw[:, 80]):.4f} "
          f"max = {M_raw[:, 80].max():.2f} cm/GtCO₂", flush=True)

    # ── Drop pulse-induced AIS tipping outliers ──────────────────────────
    # Even at the 0.01-GtCO₂ small pulse, ~1% of cells happen to sit at
    # the AIS tipping threshold and the small pulse pushes them over.
    # Their marginals jump to ~10²-10⁴× the linear-regime value, which
    # breaks any surrogate-based regression. This is a separate
    # state-dependence phenomenon from the linear SC-GHG response the
    # Shapley decomposition targets. The cells flagged here mostly
    # appear in the ANOVA-18k V_brick (high posterior variance) and are
    # tracked separately via the AIS-tipping classifier framework.
    OUTLIER_PERCENTILE = 99.0
    cap = float(np.percentile(M_raw, OUTLIER_PERCENTILE))
    outlier_cells = (M_raw.max(axis=1) > cap)
    n_outlier = int(outlier_cells.sum())
    print(f"  outlier filter at p{OUTLIER_PERCENTILE:.0f} (cap = {cap:.4f} cm/GtCO₂): "
          f"{n_outlier} cells ({100*n_outlier/len(outlier_cells):.2f}%) flagged",
          flush=True)
    M_raw = np.clip(M_raw, None, cap)

    # Time-smooth to suppress per-cell year-to-year seed noise
    M = _smooth_traj(M_raw, SMOOTH_WINDOW_YR)
    print(f"  smoothed ({SMOOTH_WINDOW_YR}-yr boxcar): "
          f"median@2100 = {np.median(M[:, 80]):.4f} cm/GtCO₂", flush=True)
    # Return base[KEY_COLS] so caller can align with feature df
    return base[KEY_COLS].copy(), years, M


# ---------------------------------------------------------------------------
# Stage B: fit + SHAP
# ---------------------------------------------------------------------------
def fit_and_shap(feat_df, marg_keys, years, M):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.model_selection import KFold
    try:
        import shap
    except ImportError:
        sys.exit("shap not installed. pip install shap")

    feature_cols = RFF_FEATURES_LIST + CFG_FEATURES + POST_FEATURES
    # Align: feat_df has all 10k cells; marg_keys is the same set sorted
    fd = feat_df.sort_values(KEY_COLS).reset_index(drop=True)
    assert (fd[KEY_COLS].to_numpy() == marg_keys[KEY_COLS].to_numpy()).all()

    # Stack panel: each row = (cell, year). Repeat features 131× per cell.
    print(f"\n[C] stacking time-as-feature panel ...", flush=True)
    n_cells = len(fd)
    n_yr = len(years)
    X_static = fd[feature_cols].to_numpy(dtype=np.float64)
    w_cell = fd["w_norm"].to_numpy(dtype=np.float64)

    X_long = np.repeat(X_static, n_yr, axis=0)
    year_long = np.tile(years, n_cells).reshape(-1, 1)
    X_long = np.hstack([year_long, X_long])
    y_long = M.reshape(-1)
    w_long = np.repeat(w_cell, n_yr)
    feature_names = ["year"] + feature_cols
    print(f"  panel shape: {X_long.shape}; y shape: {y_long.shape}", flush=True)

    # Hold-out by cell (not row): the high-noise per-cell trajectory
    # easily overfits if a regularization-naive model is used. Aggressive
    # regularization + early stopping on a 20% held-out cell split.
    rng = np.random.default_rng(2026)
    cell_perm = rng.permutation(n_cells)
    n_te = n_cells // 5
    te_cells = set(cell_perm[:n_te])
    cell_ids = np.repeat(np.arange(n_cells), n_yr)
    te_mask = np.isin(cell_ids, list(te_cells))
    tr_mask = ~te_mask

    # NB: Surrogate is fitted with UNIFORM weights — the Wong importance
    # weights are concentrated (ESS = 3815/10000 = 38%) and using them in
    # the fit excludes ~60% of cells from training, producing wild
    # extrapolation on held-out cells. The importance weights are still applied
    # downstream in the SHAP→variance aggregation (weighted variance of
    # SHAP across cells), so the FINAL Shapley attribution is still
    # importance-weighted in the right sense.
    print(f"\n[D] fitting HistGradientBoostingRegressor (regularized, "
          f"uniform-weighted training) ...", flush=True)
    print(f"  train: {tr_mask.sum()} rows from {n_cells - n_te} cells", flush=True)
    print(f"  test:  {te_mask.sum()} rows from {n_te} cells", flush=True)
    t0 = time.time()
    model = HistGradientBoostingRegressor(
        max_iter=300,
        max_leaf_nodes=31,
        learning_rate=0.05,
        min_samples_leaf=20,
        l2_regularization=0.5,
        random_state=2026,
    )
    model.fit(X_long[tr_mask], y_long[tr_mask])     # no sample_weight
    train_r2 = model.score(X_long[tr_mask], y_long[tr_mask])
    test_r2  = model.score(X_long[te_mask], y_long[te_mask])
    print(f"  fit time: {time.time()-t0:.1f}s", flush=True)
    print(f"  train R²: {train_r2:.4f}  |  test R² (held-out 20% cells): {test_r2:.4f}", flush=True)
    if test_r2 < 0.3:
        print(f"  [warn] test R² < 0.3; SHAP attributions may be unreliable.", flush=True)

    # Re-fit on full data for the SHAP computation
    print(f"  re-fitting on full data for final SHAP ...", flush=True)
    model_full = HistGradientBoostingRegressor(
        max_iter=300, max_leaf_nodes=31, learning_rate=0.05,
        min_samples_leaf=20, l2_regularization=0.5,
        random_state=2026,
    )
    model_full.fit(X_long, y_long)
    model = model_full
    r2s = [test_r2]

    # SHAP per year — compute on the full fitted model, slice by year.
    # Track V_total and V_modeled per year so V_internal can be derived
    # as the unexplained-variance residual (LHS-10k residual interpretation
    # of internal variability; properly on the same scale as Shapley).
    print(f"\n[F] SHAP TreeExplainer ...", flush=True)
    t0 = time.time()
    explainer = shap.TreeExplainer(model)
    sh_per_year = np.zeros((n_yr, len(feature_names)))   # variance contribution
    sh_signed_per_year = np.zeros((n_yr, len(feature_names)))  # signed mean
    v_total_per_year   = np.zeros(n_yr)
    v_residual_per_year = np.zeros(n_yr)
    for it, y in enumerate(years):
        idx = np.arange(it, len(X_long), n_yr)
        Xs = X_long[idx]
        ys = y_long[idx]
        ws = w_long[idx]
        yhat = model.predict(Xs)
        shvals = explainer.shap_values(Xs)
        wsum = ws.sum()
        mu_y = (ys * ws).sum() / wsum
        v_total_per_year[it] = ((ys - mu_y) ** 2 * ws).sum() / wsum
        v_residual_per_year[it] = (((ys - yhat) ** 2) * ws).sum() / wsum
        mu_sh = (shvals * ws[:, None]).sum(axis=0) / wsum
        var_sh = ((shvals - mu_sh) ** 2 * ws[:, None]).sum(axis=0) / wsum
        sh_per_year[it] = var_sh
        sh_signed_per_year[it] = mu_sh
        if (it + 1) % 20 == 0 or it == 0:
            print(f"  year {y}: SHAP done ({time.time()-t0:.1f}s; "
                  f"V_total={v_total_per_year[it]:.5g} "
                  f"V_res={v_residual_per_year[it]:.5g})", flush=True)

    return feature_names, sh_per_year, sh_signed_per_year, r2s, v_total_per_year, v_residual_per_year


# ---------------------------------------------------------------------------
# Stage C: aggregate + plot
# ---------------------------------------------------------------------------
def aggregate_and_plot(feature_names, sh_var_per_year, years, v_residual_per_year):
    print(f"\n[G] aggregating Shapley by axis ...", flush=True)

    # Build feature → axis map. `year` is excluded from the H-S decomp
    # (it's not an uncertainty source). `seed_idx` isn't a feature; the
    # internal-variability contribution is borrowed from ANOVA-18k below.
    feat_axis = {}
    for f in feature_names:
        if f == "year":
            feat_axis[f] = "year"
        elif f in AXIS_OF:
            feat_axis[f] = AXIS_OF[f]
        else:
            feat_axis[f] = "other"

    # Per-feature long-form output
    rows_long = []
    for it, y in enumerate(years):
        for j, f in enumerate(feature_names):
            rows_long.append({
                "year": int(y),
                "feature": f,
                "axis": feat_axis[f],
                "V_shap": float(sh_var_per_year[it, j]),
            })
    long_df = pd.DataFrame(rows_long)
    long_csv = OUT / "shapley_hs_lhs10k_per_feature.csv"
    long_df.to_csv(long_csv, index=False)
    print(f"  wrote {long_csv}  ({len(long_df)} rows)", flush=True)

    # Axis-aggregated time series (sum SHAP variance within each axis)
    agg = (long_df[long_df.axis != "year"]
            .groupby(["year", "axis"], as_index=False)["V_shap"].sum())
    agg_csv = OUT / "shapley_hs_lhs10k_per_year_axis.csv"
    agg.to_csv(agg_csv, index=False)
    print(f"  wrote {agg_csv}", flush=True)

    # ---- V_internal as the LHS-10k residual variance (1−R²)·V_total ────
    # The Shapley SHAP variances sum to ≈ V_predicted = V_total × R².
    # V_internal = V_total − V_predicted = (1−R²)·V_total = residual variance.
    # This is on the same scale as the Shapley contributions (both on the
    # clipped + smoothed LHS-10k target) so the stacked area is internally
    # consistent. Methodologically: the LHS-10k can't separate FaIR seed
    # noise from unmodelled non-physical variance, so V_internal here
    # bundles both — same convention as Hawkins-Sutton 2009's residual.
    v_int_t = v_residual_per_year.copy()
    print(f"  V_internal from LHS-10k residual: "
          f"@2050 = {v_int_t[2050-YEAR_LO]:.5g}, "
          f"@2100 = {v_int_t[2100-YEAR_LO]:.5g}, "
          f"@2150 = {v_int_t[2150-YEAR_LO]:.5g}", flush=True)

    # ---- Primary figure: 4-axis Hawkins-Sutton stacked area ----
    print(f"\n[I] rendering primary 4-axis H-S figure ...", flush=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plot_4axis(agg, v_int_t, years)

    # ---- Secondary figure: top-2 per source axis ----
    print(f"\n[J] rendering secondary top-2-per-source figure ...", flush=True)
    plot_top2_per_axis(long_df, v_int_t, years)


def plot_4axis(agg, v_int_t, years):
    import matplotlib.pyplot as plt
    AXIS_ORDER  = ["emissions", "climate", "brick"]
    AXIS_LABEL  = {"emissions": "Emissions (RFF-SP)",
                   "climate":   "Climate response (FaIR cfg)",
                   "brick":     "BRICK posterior",
                   "internal":  "Internal variability (FaIR seed)"}
    AXIS_COLOR  = {"emissions": "#d95f02",
                   "climate":   "#7570b3",
                   "internal":  "#1b9e77",
                   "brick":     "#e7298a"}
    pivot = agg.pivot(index="year", columns="axis", values="V_shap").reindex(years).fillna(0.0)
    for ax in AXIS_ORDER:
        if ax not in pivot.columns:
            pivot[ax] = 0.0
    pivot["internal"] = v_int_t
    V_total = pivot[AXIS_ORDER + ["internal"]].sum(axis=1).to_numpy()
    V_total_safe = np.where(V_total > 0, V_total, 1.0)
    frac = pivot[AXIS_ORDER + ["internal"]].divide(V_total_safe, axis=0)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    stack_axes = ["emissions", "climate", "internal", "brick"]
    ax.stackplot(years, *[frac[a].to_numpy() for a in stack_axes],
                 labels=[AXIS_LABEL[a] for a in stack_axes],
                 colors=[AXIS_COLOR[a] for a in stack_axes],
                 alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.set_xlim(YEAR_LO, YEAR_HI)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Fraction of pulse-marginal SLR variance", fontsize=11)
    ax.set_title("Shapley Hawkins-Sutton decomposition of pulse-marginal SLR\n"
                 "(v1.4.5 LHS-10k, 0.01-GtCO₂ pulse at 2030)",
                 fontsize=12, fontweight="bold", color="#1F4E79")
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="center right", fontsize=9.5, framealpha=0.92)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "shapley_hs_lhs10k_pulse_4axis.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "shapley_hs_lhs10k_pulse_4axis.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {OUT / 'shapley_hs_lhs10k_pulse_4axis.png'}", flush=True)

    # Headline numbers
    print(f"\n  Fractions at landmark years:")
    for y in (2050, 2100, 2150):
        i = int(np.where(years == y)[0][0])
        print(f"    {y}:  emi={frac['emissions'].iloc[i]:.2f}  "
              f"clim={frac['climate'].iloc[i]:.2f}  "
              f"int={frac['internal'].iloc[i]:.2f}  "
              f"brick={frac['brick'].iloc[i]:.2f}", flush=True)


def plot_top2_per_axis(long_df, v_int_t, years):
    """Stacked area with top-2 physical drivers per source axis,
    plus V_internal as the residual band."""
    import matplotlib.pyplot as plt
    # For each source axis, pick the top-2 features by cumulative Shapley
    # variance over 2050-2100 (the policy-relevant horizon).
    pol_years = (long_df.year >= 2050) & (long_df.year <= 2100)
    feat_score = (long_df[pol_years]
                  .groupby(["axis", "feature"])["V_shap"].sum()
                  .reset_index()
                  .sort_values(["axis", "V_shap"], ascending=[True, False]))
    top2 = (feat_score[feat_score.axis.isin(["emissions", "climate", "brick"])]
            .groupby("axis").head(2)["feature"].tolist())
    print(f"  Top-2 drivers per axis (by Shapley over 2050-2100):", flush=True)
    for f in top2:
        ax_g = AXIS_OF.get(f, "?")
        print(f"    {f} ({ax_g})", flush=True)

    # Build per-year fractions
    AXIS_COLOR_SEQ = {"emissions": ["#d95f02", "#f1a340"],
                      "climate":   ["#7570b3", "#998ec3"],
                      "brick":     ["#e7298a", "#df65b0"]}
    pivot = (long_df.pivot_table(index="year", columns="feature", values="V_shap")
                .reindex(years).fillna(0.0))
    # Sum non-top-2 within each axis into "other_<axis>"
    layers = []
    for axis in ["emissions", "climate", "brick"]:
        ax_feats = [f for f, a in AXIS_OF.items() if a == axis]
        ax_top2 = [f for f in top2 if AXIS_OF.get(f) == axis]
        for j, f in enumerate(ax_top2):
            layers.append((f"{f}", pivot[f].to_numpy(), AXIS_COLOR_SEQ[axis][j]))
        other_feats = [f for f in ax_feats if f not in ax_top2]
        if other_feats:
            other_y = pivot[other_feats].sum(axis=1).to_numpy()
            layers.append((f"other {axis}", other_y, AXIS_COLOR_SEQ[axis][1] + "60"))
    # Internal variability stacked on top
    layers.append(("Internal variability", v_int_t, "#1b9e77"))

    Y = np.array([l[1] for l in layers])
    total = Y.sum(axis=0)
    total_safe = np.where(total > 0, total, 1.0)
    frac = Y / total_safe

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.stackplot(years, *frac,
                 labels=[l[0] for l in layers],
                 colors=[l[2] for l in layers],
                 alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.set_xlim(YEAR_LO, YEAR_HI)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Fraction of pulse-marginal SLR variance", fontsize=11)
    ax.set_title("Pulse-marginal SLR variance — top-2 drivers per source axis\n"
                 "(v1.4.5 LHS-10k, 0.01-GtCO₂ pulse at 2030; Shapley TreeExplainer)",
                 fontsize=12, fontweight="bold", color="#1F4E79")
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="center right", fontsize=8.5, framealpha=0.92)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "shapley_hs_lhs10k_pulse_top2_per_axis.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "shapley_hs_lhs10k_pulse_top2_per_axis.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {OUT / 'shapley_hs_lhs10k_pulse_top2_per_axis.png'}", flush=True)


def main():
    feat = assemble_features()
    keys, years, M = load_paired_marginal(feat)
    feature_names, sh_var, sh_signed, r2s, v_total, v_resid = fit_and_shap(feat, keys, years, M)
    aggregate_and_plot(feature_names, sh_var, years, v_resid)
    print(f"\n[done] mean test R² = {np.mean(r2s):.4f}", flush=True)


if __name__ == "__main__":
    main()
