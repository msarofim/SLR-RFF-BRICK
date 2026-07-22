#!/usr/bin/env python
"""Level-vs-time decomposition of GMST->Antarctic amplification from CMIP6 DECK runs.

1pctCO2 sweeps warming LEVEL at a fast sustained rate; abrupt-4xCO2 holds forcing fixed
and sweeps TIME. Both are GHG-only (aerosols/ozone at piControl) — no composition
confound. Anomalies rel. each model's piControl mean (drift not removed — second-order
for ratios of multi-K anomalies).

Quantities per model (land-frame AIS as everywhere in this diagnostic):
  - LEVEL ratio R = dT_ais/dT_glob, SMOOTH-yr running mean, used for dT >= DT_MIN_LEVEL
    (annual ratio unstable at small denominators). This is the BRICK-relevant secant `a`.
  - 1pctCO2 windowed WINDOW-yr trend ratio (marginal amp on the ramp).
  - abrupt-4xCO2 Gregory-style slopes: OLS T_ais~T_glob years 1-20 (fast mode) and
    21-150 (slow mode); asymptotic R = mean over years 100-150 (and 250-300 if present).

HEADLINE: median level ratio at matched dT bins, 1pctCO2 vs abrupt-4xCO2, with the
paired difference D = R_abrupt - R_1pct bootstrapped over models. D > 0 at matched
warming = amplification grows with time-at-level = a real time component.
"""
import glob, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IN_DIR   = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/cmip6_pai"
OUT_PNG  = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_deck.png"
OUT_CSV  = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_deck.csv"
OUT_MD   = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_deck_summary.md"
SMOOTH        = 11         # yr running mean for level ratios
DT_MIN_LEVEL  = 1.0        # K; level ratio used above this warming only
WINDOW        = 41         # yr; 1pct windowed trend ratio
A_EQ          = 1.196      # DAIS equilibrium slope reference
DT_BINS       = [2.5, 3.0, 3.5, 4.0, 4.5]; DT_HALF = 0.25
GREG_FAST     = (1, 20); GREG_SLOW = (21, 150); GREG_LATE = (151, 300)
ASY1, ASY2    = (100, 150), (250, 300)
NBOOT         = 1000
COL = {"1pctCO2": "#b25c39", "abrupt-4xCO2": "#0d7c8c"}

def trend(y):
    x = np.arange(len(y)); return np.polyfit(x, y, 1)[0]

def ols_slope(x, y):
    x = np.asarray(x); y = np.asarray(y)
    return np.cov(x, y)[0, 1] / np.var(x)

data = {}
for f in sorted(glob.glob(os.path.join(IN_DIR, "tas_series_deck_*.csv"))):
    model = os.path.basename(f)[len("tas_series_deck_"):-len(".csv")]
    df = pd.read_csv(f)
    pic = df[df.scenario == "piControl"][["tas_global", "tas_ais"]].mean()
    d = {}
    for exp in ("1pctCO2", "abrupt-4xCO2"):
        s = df[df.scenario == exp].set_index("year").sort_index()
        if len(s) < 100: continue
        d[exp] = pd.DataFrame({"dTg": s.tas_global - pic.tas_global,
                               "dTa": s.tas_ais    - pic.tas_ais})
    if len(d) == 2: data[model] = d
models = sorted(data)
print(f"{len(models)} models: {', '.join(models)}")

rows = []
greg = []
for model in models:
    for exp, s in data[model].items():
        sm = s.rolling(SMOOTH, center=True).mean().dropna()
        lev = sm[sm.dTg >= DT_MIN_LEVEL]
        for yr, r in zip(lev.index, lev.dTa / lev.dTg):
            rows.append(dict(model=model, exp=exp, kind="level", year=yr,
                             dT=lev.dTg.loc[yr], val=r))
    s1 = data[model]["1pctCO2"]
    half = WINDOW // 2
    for c0 in range(int(s1.index.min()) + half, int(s1.index.max()) - half + 1):
        w = s1.loc[c0 - half: c0 + half]
        tg = trend(w.dTg.values)
        if tg * 10 >= 0.05:
            rows.append(dict(model=model, exp="1pctCO2", kind="marginal", year=c0,
                             dT=w.dTg.mean(), val=trend(w.dTa.values) / tg))
    sa = data[model]["abrupt-4xCO2"]
    g = dict(model=model)
    for name, (y0, y1) in (("fast", GREG_FAST), ("slow", GREG_SLOW), ("late", GREG_LATE)):
        w = sa.loc[y0:y1]
        g[name] = ols_slope(w.dTg, w.dTa) if len(w) >= 20 else np.nan
    for name, (y0, y1) in (("asy150", ASY1), ("asy300", ASY2)):
        w = sa.loc[y0:y1]
        g[name] = (w.dTa / w.dTg).mean() if len(w) >= 30 else np.nan
    greg.append(g)
lev = pd.DataFrame(rows); lev.to_csv(OUT_CSV, index=False)
greg = pd.DataFrame(greg).set_index("model")

# ---- matched-warming level ratios + paired bootstrap ----
def bin_median(df, exp, lo, hi):
    s = df[(df.exp == exp) & (df.kind == "level") & df.dT.between(lo, hi)]
    return s.groupby("model")[["val", "year"]].median()

print("\nmatched-warming LEVEL ratios (median over models; years since branch):")
summary = []
rng = np.random.default_rng(2026)
for b in DT_BINS:
    p1 = bin_median(lev, "1pctCO2", b - DT_HALF, b + DT_HALF)
    pa = bin_median(lev, "abrupt-4xCO2", b - DT_HALF, b + DT_HALF)
    both = p1.join(pa, lsuffix="_1pct", rsuffix="_ab").dropna()
    if len(both) < 5: continue
    D = both.val_ab - both.val_1pct
    bs = [np.median(rng.choice(D.values, size=len(D), replace=True))
          for _ in range(NBOOT)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    summary.append(dict(dT=b, n=len(both),
                        r_1pct=both.val_1pct.median(), yr_1pct=int(both.year_1pct.median()),
                        r_abrupt=both.val_ab.median(), yr_abrupt=int(both.year_ab.median()),
                        D=D.median(), D_lo=lo, D_hi=hi))
    print(f"  dT={b:.1f}K (n={len(both)}): 1pct {both.val_1pct.median():.3f}@yr{int(both.year_1pct.median())}"
          f"  abrupt {both.val_ab.median():.3f}@yr{int(both.year_ab.median())}"
          f"  D={D.median():+.3f} [{lo:+.3f},{hi:+.3f}]")
summ = pd.DataFrame(summary)

print("\nabrupt-4xCO2 Gregory slopes / asymptotes (median [IQR] over models):")
for c in ("fast", "slow", "late", "asy150", "asy300"):
    v = greg[c].dropna()
    if len(v):
        print(f"  {c:7s} n={len(v):2d}  {v.median():.3f} [{v.quantile(.25):.3f}, {v.quantile(.75):.3f}]")
v1 = lev[(lev.exp == "1pctCO2") & (lev.kind == "marginal")]
for yb in ((60, 80), (120, 140)):
    s = v1[v1.year.between(*yb)].groupby("model").val.median()
    print(f"  1pct marginal yrs {yb}: n={len(s)}  {s.median():.3f} [{s.quantile(.25):.3f}, {s.quantile(.75):.3f}]")

# ---- figure ----
fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))
ax = axes[0]
for model in models:
    s = data[model]["abrupt-4xCO2"]
    sm = s.rolling(SMOOTH, center=True).mean().dropna()
    ax.plot(sm.index, sm.dTa / sm.dTg, color=COL["abrupt-4xCO2"], alpha=.15, lw=.8)
med_rt = {}
sall = pd.concat([data[m]["abrupt-4xCO2"].rolling(SMOOTH, center=True).mean().dropna()
                  .assign(model=m, R=lambda d: d.dTa / d.dTg) for m in models])
nyr = sall.groupby(sall.index).R.count()
mm = sall.groupby(sall.index).R.median()[nyr >= 10]   # median only where >=10 models report
ax.plot(mm.index, mm.values, color=COL["abrupt-4xCO2"], lw=2.2, label="multi-model median")
ax.axhline(A_EQ, color="k", ls="--", lw=1, alpha=.6)
ax.text(3, A_EQ, f" DAIS equilibrium {A_EQ}", va="bottom", fontsize=8, alpha=.7)
ax.set(title="abrupt-4xCO2: level ratio vs time at ~fixed forcing",
       xlabel="years since quadrupling", ylabel="ΔT_AIS / ΔT_glob",
       xlim=(0, 300), ylim=(0.6, 1.6))
ax.legend(frameon=False, fontsize=8)

ax = axes[1]
for exp in ("1pctCO2", "abrupt-4xCO2"):
    sub = lev[(lev.exp == exp) & (lev.kind == "level")]
    dbins = np.arange(DT_MIN_LEVEL, sub.dT.max(), 0.25)
    med, q1, q3, xs = [], [], [], []
    for lo in dbins:
        s = sub[sub.dT.between(lo, lo + 0.25)].groupby("model").val.median()
        if len(s) >= 8:
            xs.append(lo + 0.125); med.append(s.median())
            q1.append(s.quantile(.25)); q3.append(s.quantile(.75))
    ax.fill_between(xs, q1, q3, color=COL[exp], alpha=.18, lw=0)
    ax.plot(xs, med, color=COL[exp], lw=2.2, label=exp)
ax.axhline(A_EQ, color="k", ls="--", lw=1, alpha=.6)
ax.set(title="Level ratio at matched warming (the time test)",
       xlabel="ΔT_glob (K)", ylabel="ΔT_AIS / ΔT_glob", ylim=(0.6, 1.6))
ax.legend(frameon=False, fontsize=8)

ax = axes[2]
gd = greg.dropna(subset=["fast", "slow"])
ax.scatter(gd.fast, gd.slow, s=22, color="#6d5b9c", alpha=.8)
lim = (0.4, 1.9)
ax.plot(lim, lim, "k-", lw=.8, alpha=.5)
ax.axhline(A_EQ, color="k", ls="--", lw=1, alpha=.5)
ax.axvline(A_EQ, color="k", ls=":", lw=1, alpha=.5)
ax.set(title=f"Gregory slopes: fast yrs {GREG_FAST[0]}–{GREG_FAST[1]} vs "
             f"slow yrs {GREG_SLOW[0]}–{GREG_SLOW[1]}",
       xlabel="fast-mode slope dT_AIS/dT_glob", ylabel="slow-mode slope",
       xlim=lim, ylim=lim)
fig.suptitle(f"CMIP6 DECK level-vs-time test ({len(models)} models, GHG-only forcing, "
             f"land-frame AIS)", fontsize=11)
fig.tight_layout(); fig.savefig(OUT_PNG, dpi=160)
print(f"wrote {OUT_PNG}")

with open(OUT_MD, "w") as f:
    f.write(f"# DECK level-vs-time test ({len(models)} models)\n\n"
            f"Level ratio = {SMOOTH}-yr-smoothed dT_AIS/dT_glob (dT >= {DT_MIN_LEVEL} K), "
            f"anomalies rel. piControl mean (no drift removal). D = R_abrupt - R_1pct at "
            f"matched dT, paired by model, bootstrap CI over models.\n\n"
            + summ.to_markdown(index=False, floatfmt=".3f") + "\n\n"
            f"Gregory (abrupt): fast yrs {GREG_FAST}, slow {GREG_SLOW}, late {GREG_LATE}; "
            f"asymptote R means over {ASY1}/{ASY2}.\n\n"
            + greg.describe().loc[["50%", "25%", "75%", "count"]].to_markdown(floatfmt=".3f")
            + f"\n\nModels: {', '.join(models)}\n")
print(f"wrote {OUT_MD}")
