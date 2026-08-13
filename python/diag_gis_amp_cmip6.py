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
  figures/diag_gis_amp_cmip6.png
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
PRESENT_DT = 1.25                  # K; present-day warming level for shape-anchoring

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
    if len(pooled_sec) >= 3:
        pch = PchipInterpolator(pooled_sec["dt_bin"].values,
                                pooled_sec["median"].values, extrapolate=True)
        r_present = float(pch(PRESENT_DT))
        lines += ["## anchored shape (for ladrillo_gis_driver)", "",
                  f"Shape factor S(dT) = R_secant(dT) / R_secant({PRESENT_DT} K), "
                  f"R_secant({PRESENT_DT}) = {r_present:.3f}", "",
                  "| dT (K) | S(dT) | amp = S * obs_full |", "|---|---|---|"]
        for dt in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0):
            if dt < pooled_sec["dt_bin"].min() or dt > pooled_sec["dt_bin"].max():
                continue
            s = float(pch(dt)) / r_present
            lines.append(f"| {dt:.1f} | {s:.3f} | {s*OBS_AMP_FULL:.3f} |")
        lines.append("")

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
