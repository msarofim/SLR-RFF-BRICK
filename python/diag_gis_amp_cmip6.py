#!/usr/bin/env python
"""Greenland amplification vs GLOBAL WARMING LEVEL from CMIP6 -- the amp(dT) law.

Consumes data/cmip6_gis/tas_series_gis_*.csv (python/reduce_cmip6_tas_gis.py) and
answers the question handoff 2026-08-12c section 1 raises: Ladrillo 1.0 applies a
CONSTANT Greenland amplification (gis_amp, calibrated on the historical record,
posterior p50 1.901) all the way to 2100, and the 2100 GIS scenario spread is the
pre-registered flag that did not come down. If amplification falls with warming
level, the constant overstates future regional warming.

WHAT IS MEASURED, AND WHY TWO ESTIMATORS
    SECANT  R = mean(dT_gis) / mean(dT_glob) over the window -- the LEVEL ratio.
        This is the canonical estimator from the Antarctic work: memory
        project_pai_cmip6_time_diagnostic records that integrating a MARGINAL
        (trend-ratio) fit biased the level ratio ~0.1 LOW via a too-low
        extrapolated dT->0 intercept, and the lesson recorded was "report the
        secant directly".
    SLOPE   R = sum(x*y)/sum(x^2) over the window's annual anomalies -- the
        THROUGH-ORIGIN estimator, which is exactly what build_t_gis.amp_through_origin
        uses to produce outputs/gis_amp_prior.csv, i.e. the estimator behind the
        calibrated gis_amp prior N(1.92, 0.32).
    Both are reported because the anchoring decision (whether to keep the observed
    LEVEL and take only the CMIP6 SHAPE) is only defensible if the CMIP6 and
    observed numbers are computed the same way. Comparing our secant to their
    slope would measure the estimator, not the physics.

CONTAMINATION FILTERS (named constants, all applied to both estimators)
    YEAR_MIN     pre-1950 windows dropped -- the global denominator is small and
                 the ratio is noise-dominated. This is the SAME artifact that
                 inflates the observed "early" window to 3.60 (build_t_gis's own
                 comment: a through-origin fit over decades when the global anomaly
                 was near zero while Greenland swung +/-1 C).
    DT_MIN       windows whose mean dT_glob is below this are dropped for the same
                 small-denominator reason, independently of calendar year.

FITTING
    Pooled least squares over per-model windows is outlier-dominated (fat tails) --
    the trap recorded in the Antarctic memory. So: bin by warming level, take the
    MEDIAN across models within each bin per scenario, and bootstrap OVER MODELS
    for the interval. The deliverable curve is a PCHIP through the binned medians
    rather than a 2-parameter parametric fit (user convention: interpolate the real
    data; reserve parametric approximations for when data are absent). A linear fit
    is reported alongside ONLY as a slope-vs-zero test.

Outputs:
  outputs/diag_gis_amp_cmip6.csv          per model x scenario x window
  outputs/diag_gis_amp_cmip6_binned.csv   binned medians + bootstrap CI (the curve)
  outputs/diag_gis_amp_cmip6_summary.md   headline numbers + the flat-vs-declining verdict
  outputs/gis_amp_shape.csv               S(dT) on a fine grid -- what Julia consumes
  outputs/gis_amp_shape_meta.csv          anchor, support and provenance of that grid
  figures/diag_gis_amp_cmip6.png

Requires python/diag_gis_amp_anchor.py to have been run (it supplies the anchor
warming level dT_eff; there is no fallback).
"""
import glob
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_t_gis as BTG

REPO = BTG.REPO
IN_DIR = os.path.join(REPO, "data/cmip6_gis")
OUT_CSV = os.path.join(REPO, "outputs/diag_gis_amp_cmip6.csv")
OUT_BINNED = os.path.join(REPO, "outputs/diag_gis_amp_cmip6_binned.csv")
OUT_MD = os.path.join(REPO, "outputs/diag_gis_amp_cmip6_summary.md")
OUT_FIG = os.path.join(REPO, "figures/diag_gis_amp_cmip6.png")
# The deliverable of this script: the shape factor S(dT) the Julia projection
# kernel consumes, on a fine grid, plus its provenance row.
OUT_SHAPE = os.path.join(REPO, "outputs/gis_amp_shape.csv")
OUT_SHAPE_META = os.path.join(REPO, "outputs/gis_amp_shape_meta.csv")
# Where the anchor comes from: python/diag_gis_amp_anchor.py, which measures the
# x^2-weighted warming level dT_eff = sum(x^3)/sum(x^2) of the SAME through-origin
# fit that produced the observed amplification. There is no fallback constant --
# anchoring at a guessed warming level is the error this file used to make.
ANCHOR_CSV = os.path.join(REPO, "outputs/gis_amp_anchor.csv")
ANCHOR_SCRIPT = "python/diag_gis_amp_anchor.py"
# Sensitivity arm of the flat-hold sub-choice; the Julia kernel selects it with
# LADRILLO_GIS_SHAPE=<stem>, so the stem names both <stem>.csv and <stem>_meta.csv.
SHAPE_ALT_STEM = "gis_amp_shape_fullcurve"

# ---- named constants: every label below derives from these --------------------
ZONE = "south"                     # headline zone; matches build_t_gis.HEADLINE_ZONE
ZONE_COL = f"tas_gis_{ZONE}"
BASE = BTG.BASE                    # (1850, 1900) anomaly baseline, multi-year rule
SMOOTH_WIN = 30                    # running-window length, years (Antarctic precedent)
YEAR_MIN = 1950                    # pre-1950 windows dropped (small denominator)
DT_MIN = 0.5                       # K; drop windows below this warming level
SCENARIOS = ["ssp126", "ssp245", "ssp585"]
HIST = "historical"
BIN_EDGES = np.arange(0.5, 6.01, 0.5)   # warming-level bins, K
N_BOOT = 2000
BOOT_SEED = 2026
OBS_AMP_FULL = 1.9221976385152952  # outputs/gis_amp_prior.csv south/full -- the value in use
OBS_AMP_MODERN = 1.7918384323792236  # south/modern
# Shape support. Below SHAPE_DT_MIN and above SHAPE_DT_MAX the shape is HELD FLAT
# rather than extrapolated. SHAPE_DT_MAX = 2.75 is the last bin below the 3.25 K
# bump; that bump survives the balanced panel (so it is not model dropout) and is
# most likely SCENARIO composition -- a model only reaches 3.25 K under ssp585, so
# high bins are ssp585-weighted while low bins are ssp126/245-weighted, and the
# balanced panel balances models but not scenarios. Holding flat is conservative:
# it stops the amplification falling further on evidence we do not trust, and it
# keeps the law monotone. SHAPE_DT_MIN is the first bin; below it the driver is
# observations anyway (the splice only starts after the last observed year).
SHAPE_DT_MIN = 0.75
SHAPE_DT_MAX = 2.75
SHAPE_GRID_STEP = 0.01             # K; the emitted grid the Julia kernel interpolates
SHAPE_GRID_MAX = 8.0               # K; covers ssp585 GMST to 2300

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()


def load_model(path):
    """Return {scenario: DataFrame(year, dt_glob, dt_zone)} anomalies rel BASE."""
    df = pd.read_csv(path)
    if ZONE_COL not in df.columns:
        return None
    df = df.groupby(["scenario", "year"], as_index=False).mean(numeric_only=True)
    hist = df[df.scenario == HIST]
    if hist.empty:
        return None
    seg = hist[(hist.year >= BASE[0]) & (hist.year <= BASE[1])]
    if len(seg) < 20:
        return None
    g0, z0 = seg["tas_global"].mean(), seg[ZONE_COL].mean()

    out = {}
    for sc in SCENARIOS:
        fut = df[df.scenario == sc]
        if fut.empty:
            continue
        joined = (pd.concat([hist, fut])
                    .drop_duplicates(subset="year", keep="last")
                    .sort_values("year"))
        out[sc] = pd.DataFrame({
            "year": joined["year"].values,
            "dt_glob": joined["tas_global"].values - g0,
            "dt_zone": joined[ZONE_COL].values - z0,
        })
    return out


def windows(ts):
    """Rolling SMOOTH_WIN windows -> secant and through-origin slope per window."""
    rows = []
    yr = ts["year"].values
    x, y = ts["dt_glob"].values, ts["dt_zone"].values
    for i in range(len(yr) - SMOOTH_WIN + 1):
        s = slice(i, i + SMOOTH_WIN)
        xc, yc = x[s], y[s]
        xm = xc.mean()
        centre = yr[s].mean()
        if centre < YEAR_MIN or xm < DT_MIN:
            continue
        rows.append({
            "year": centre,
            "dt_glob": xm,
            "secant": yc.mean() / xm,
            "slope": float((xc * yc).sum() / (xc ** 2).sum()),
        })
    return pd.DataFrame(rows)


def binned_curve(df, est):
    """Median across MODELS per (scenario, warming bin), bootstrapped over models."""
    rng = np.random.default_rng(BOOT_SEED)
    df = df.copy()
    df["bin"] = pd.cut(df["dt_glob"], BIN_EDGES,
                       labels=(BIN_EDGES[:-1] + BIN_EDGES[1:]) / 2)
    rows = []
    for (sc, b), g in df.groupby(["scenario", "bin"], observed=True):
        # one value per model first, so models with more windows do not dominate
        per_model = g.groupby("model")[est].median()
        if len(per_model) < 5:
            continue
        vals = per_model.values
        boot = np.array([np.median(rng.choice(vals, len(vals), replace=True))
                         for _ in range(N_BOOT)])
        rows.append({"scenario": sc, "estimator": est, "dt_bin": float(b),
                     "n_models": len(vals), "median": float(np.median(vals)),
                     "lo95": float(np.percentile(boot, 2.5)),
                     "hi95": float(np.percentile(boot, 97.5))})
    return pd.DataFrame(rows)


def anchor_dt():
    """The warming level at which S must equal 1: the x^2-weighted effective
    level of the observed through-origin fit, averaged over the same three
    products the amp prior averages. Errors rather than guessing."""
    if not os.path.exists(ANCHOR_CSV):
        sys.exit(f"missing {ANCHOR_CSV}; run {ANCHOR_SCRIPT} first")
    a = pd.read_csv(ANCHOR_CSV)
    a = a[(a.zone == ZONE) & (a.window == BTG.AMP_WINDOW_HEADLINE)]
    if a.empty:
        sys.exit(f"{ANCHOR_CSV} has no rows for zone={ZONE} "
                 f"window={BTG.AMP_WINDOW_HEADLINE}")
    return float(a.dt_eff.mean())


def shape_table(pooled, dt_anchor, dt_max=SHAPE_DT_MAX):
    """PCHIP through the pooled binned medians over [SHAPE_DT_MIN, dt_max], held
    flat outside, normalised to 1 at `dt_anchor`. Returns (grid DataFrame, R at
    the anchor)."""
    sub = pooled[(pooled.dt_bin >= SHAPE_DT_MIN) & (pooled.dt_bin <= dt_max)]
    pch = PchipInterpolator(sub["dt_bin"].values, sub["median"].values,
                            extrapolate=False)
    clip = lambda d: np.clip(d, SHAPE_DT_MIN, dt_max)
    r_anchor = float(pch(clip(dt_anchor)))
    dt = np.round(np.arange(0.0, SHAPE_GRID_MAX + SHAPE_GRID_STEP / 2,
                            SHAPE_GRID_STEP), 4)
    # The anchor is inserted as its own node so that S(dT_eff) == 1 EXACTLY under
    # the consumer's linear interpolation of this grid, not to 1e-7. The Julia
    # kernel asserts that identity at load; without the node it fires.
    dt = np.unique(np.concatenate([dt, [dt_anchor]]))
    r = pch(clip(dt))
    return pd.DataFrame({"dt": dt, "R_secant": r, "S": r / r_anchor}), r_anchor


def main():
    files = sorted(glob.glob(os.path.join(IN_DIR, "tas_series_gis_*.csv")))
    if not files:
        sys.exit(f"no inputs in {IN_DIR}; run python/reduce_cmip6_tas_gis.py first")
    print(f"{len(files)} model files", flush=True)

    recs, skipped = [], []
    for f in files:
        model = os.path.basename(f)[len("tas_series_gis_"):-len(".csv")]
        try:
            per_sc = load_model(f)
        except Exception as e:
            skipped.append(f"{model}: {type(e).__name__}: {e}")
            continue
        if not per_sc:
            skipped.append(f"{model}: no usable scenario/baseline")
            continue
        for sc, ts in per_sc.items():
            w = windows(ts)
            if w.empty:
                continue
            w["model"], w["scenario"] = model, sc
            recs.append(w)
    if not recs:
        sys.exit("no usable windows")
    allw = pd.concat(recs, ignore_index=True)
    allw.to_csv(OUT_CSV, index=False)
    n_models = allw.model.nunique()
    print(f"{n_models} models, {len(allw)} windows -> {OUT_CSV}", flush=True)
    for s in skipped:
        print(f"  SKIP {s}", flush=True)

    binned = pd.concat([binned_curve(allw, e) for e in ("secant", "slope")],
                       ignore_index=True)
    binned.to_csv(OUT_BINNED, index=False)

    # ---- pooled (all-scenario) curve per estimator: the deliverable shape -------
    lines = [f"# CMIP6 Greenland amplification vs warming level (zone = {ZONE})",
             "",
             f"- commit `{COMMIT}`; {n_models} CMIP6 models; scenarios {SCENARIOS}",
             f"- window {SMOOTH_WIN} yr, anomalies rel {BASE[0]}-{BASE[1]}, "
             f"windows dropped if centre < {YEAR_MIN} or mean dT_glob < {DT_MIN} K",
             f"- bootstrap over models, {N_BOOT} resamples, seed {BOOT_SEED}",
             f"- observed prior for comparison: south/full **{OBS_AMP_FULL:.3f}** "
             f"(the value Ladrillo 1.0 uses), south/modern {OBS_AMP_MODERN:.3f}",
             ""]

    verdicts = {}
    for est in ("secant", "slope"):
        sub = allw.copy()
        sub["bin"] = pd.cut(sub["dt_glob"], BIN_EDGES,
                            labels=(BIN_EDGES[:-1] + BIN_EDGES[1:]) / 2)
        pooled = (sub.groupby(["bin", "model"], observed=True)[est].median()
                     .groupby("bin", observed=True)
                     .agg(["median", "count"]).reset_index())
        pooled = pooled[pooled["count"] >= 5]
        pooled["dt_bin"] = pooled["bin"].astype(float)

        # slope-vs-zero test on the BINNED medians (not pooled windows: fat tails)
        rng = np.random.default_rng(BOOT_SEED)
        models = allw.model.unique()
        slopes = []
        for _ in range(N_BOOT):
            pick = rng.choice(models, len(models), replace=True)
            bs = sub[sub.model.isin(pick)]
            p = (bs.groupby(["bin", "model"], observed=True)[est].median()
                   .groupby("bin", observed=True).median().reset_index())
            p["dt_bin"] = p["bin"].astype(float)
            p = p.dropna()
            if len(p) >= 3:
                slopes.append(np.polyfit(p["dt_bin"], p[est], 1)[0])
        slopes = np.array(slopes)
        lo, hi = np.percentile(slopes, [2.5, 97.5])
        excl = (lo > 0) or (hi < 0)
        verdicts[est] = (pooled, float(np.median(slopes)), lo, hi, excl)

        lines += [f"## {est}", "",
                  "| dT bin (K) | n models | median amp |", "|---|---|---|"]
        for _, r in pooled.iterrows():
            lines.append(f"| {r['dt_bin']:.2f} | {int(r['count'])} | {r['median']:.3f} |")
        lines += ["",
                  f"- linear slope over warming level: **{np.median(slopes):+.4f} "
                  f"per K** [95% {lo:+.4f}, {hi:+.4f}]",
                  f"- **{'DECLINING/RISING (CI excludes zero)' if excl else 'FLAT (CI includes zero)'}**",
                  ""]

    # ---- the anchored shape, for the projection-side law ------------------------
    pooled_sec = verdicts["secant"][0]
    dt_anchor = anchor_dt()
    grid, r_anchor = shape_table(pooled_sec, dt_anchor)
    # full precision, no float_format: the anchor node must round-trip exactly
    grid.to_csv(OUT_SHAPE, index=False)
    pd.DataFrame([dict(anchor_dt=dt_anchor, r_anchor=r_anchor,
                       obs_amp_full=OBS_AMP_FULL, estimator="secant",
                       dt_min=SHAPE_DT_MIN, dt_max=SHAPE_DT_MAX,
                       grid_step=SHAPE_GRID_STEP, grid_max=SHAPE_GRID_MAX,
                       n_models=n_models, zone=ZONE, commit=COMMIT)]
                ).to_csv(OUT_SHAPE_META, index=False)

    # Sensitivity arm for the flat-hold sub-choice: the same construction with the
    # support running to the LAST populated bin instead of SHAPE_DT_MAX, i.e. the
    # 3.25 K bump and everything above it taken at face value. Emitted so the arm
    # can be RUN (LADRILLO_GIS_SHAPE=gis_amp_shape_fullcurve) rather than argued.
    alt_max = float(pooled_sec.dt_bin.max())
    alt_grid, alt_r = shape_table(pooled_sec, dt_anchor, dt_max=alt_max)
    alt_stem = os.path.join(REPO, f"outputs/{SHAPE_ALT_STEM}")
    alt_grid.to_csv(f"{alt_stem}.csv", index=False)
    pd.DataFrame([dict(anchor_dt=dt_anchor, r_anchor=alt_r,
                       obs_amp_full=OBS_AMP_FULL, estimator="secant",
                       dt_min=SHAPE_DT_MIN, dt_max=alt_max,
                       grid_step=SHAPE_GRID_STEP, grid_max=SHAPE_GRID_MAX,
                       n_models=n_models, zone=ZONE, commit=COMMIT)]
                ).to_csv(f"{alt_stem}_meta.csv", index=False)

    sfun = lambda d: float(np.interp(d, grid.dt.values, grid.S.values))
    sfun_alt = lambda d: float(np.interp(d, alt_grid.dt.values, alt_grid.S.values))
    lines += ["## anchored shape (for ladrillo_gis_driver)", "",
              f"Shape factor S(dT) = R_secant(dT) / R_secant(dT_eff), anchored at the "
              f"x^2-weighted effective warming level of the observed through-origin "
              f"fit: **dT_eff = {dt_anchor:.3f} K** ({ANCHOR_SCRIPT}), "
              f"R_secant(dT_eff) = {r_anchor:.3f}.",
              f"PCHIP through the pooled binned medians over "
              f"{SHAPE_DT_MIN}-{SHAPE_DT_MAX} K, HELD FLAT outside that range "
              f"(the {SHAPE_DT_MAX + 0.5:.2f} K bump is scenario composition, not "
              f"physics we trust).", "",
              "| dT (K) | S(dT) | amp = S * obs_full |", "|---|---|---|"]
    for dt in (0.5, 1.0, dt_anchor, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0):
        s = sfun(dt)
        mark = "  <- anchor" if abs(dt - dt_anchor) < 1e-9 else ""
        lines.append(f"| {dt:.2f} | {s:.3f} | {s*OBS_AMP_FULL:.3f} |{mark}")
    lines.append("")

    # Cross-check on the anchor, reported not acted on: an independent route is to
    # match ESTIMATORS instead of warming levels -- take the CMIP6 ensemble's own
    # full-window through-origin amplification (same estimator and window as the
    # observed 1.922) as the denominator. If the two routes disagree materially the
    # anchor is doing work it should not be.
    lines += [f"- **flat-hold sensitivity arm** `{SHAPE_ALT_STEM}`: same construction "
              f"with the support run to the last populated bin ({alt_max:.2f} K) "
              f"instead of {SHAPE_DT_MAX} K. S at 3.0/4.0/5.0 K: "
              f"{sfun_alt(3.0):.3f}/{sfun_alt(4.0):.3f}/{sfun_alt(5.0):.3f} vs the "
              f"held {sfun(3.0):.3f}/{sfun(4.0):.3f}/{sfun(5.0):.3f}.", ""]

    win_csv = os.path.join(REPO, "outputs/diag_gis_amp_cmip6_windows.csv")
    if os.path.exists(win_csv):
        r_win = float(pd.read_csv(win_csv)[BTG.AMP_WINDOW_HEADLINE].median())
        lines += [f"- **anchor cross-check:** estimator-matched denominator "
                  f"(CMIP6 median full-window through-origin) = {r_win:.3f} vs the "
                  f"dT_eff route's {r_anchor:.3f}, a "
                  f"{100*abs(r_win-r_anchor)/r_anchor:.1f}% difference; "
                  f"S({SHAPE_DT_MAX}) would be "
                  f"{sfun(SHAPE_DT_MAX)*r_anchor/r_win:.3f} instead of "
                  f"{sfun(SHAPE_DT_MAX):.3f}.", ""]

    with open(OUT_MD, "w") as fh:
        fh.write("\n".join(lines) + "\n")

    # ---- figure -----------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    colors = {"ssp126": "#1b7837", "ssp245": "#2166ac", "ssp585": "#b2182b"}
    for ax, est in zip(axes, ("secant", "slope")):
        for sc in SCENARIOS:
            b = binned[(binned.estimator == est) & (binned.scenario == sc)]
            if b.empty:
                continue
            ax.plot(b.dt_bin, b["median"], "o-", color=colors[sc], label=sc, lw=1.8)
            ax.fill_between(b.dt_bin, b.lo95, b.hi95, color=colors[sc], alpha=0.15)
        pooled = verdicts[est][0]
        ax.plot(pooled["dt_bin"], pooled["median"], "k--", lw=2.2,
                label="all-scenario median")
        ax.axhline(OBS_AMP_FULL, color="0.35", ls=":", lw=1.8,
                   label=f"observed full-window {OBS_AMP_FULL:.2f} (in use)")
        ax.axhline(OBS_AMP_MODERN, color="0.6", ls="-.", lw=1.5,
                   label=f"observed modern {OBS_AMP_MODERN:.2f}")
        sl, lo, hi = verdicts[est][1], verdicts[est][2], verdicts[est][3]
        ax.set_title(f"{est}: slope {sl:+.3f} /K [{lo:+.3f}, {hi:+.3f}]")
        ax.set_xlabel("global warming level, K rel %d-%d" % BASE)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel(f"Greenland ({ZONE}) amplification")
    axes[0].legend(fontsize=7, loc="best")
    fig.suptitle(f"CMIP6 Greenland amplification vs warming level -- "
                 f"{n_models} models, {SMOOTH_WIN}-yr windows (commit {COMMIT})")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=150)
    print(f"wrote {OUT_MD}\nwrote {OUT_BINNED}\nwrote {OUT_FIG}", flush=True)


if __name__ == "__main__":
    main()
