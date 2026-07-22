#!/usr/bin/env python
"""Level-vs-rate decomposition of the CMIP6 GMST->Antarctic amplification, 5 scenarios.

Motivation: in the 2-scenario collapse test, SSP2-4.5 sits ABOVE SSP5-8.5 at matched
warming (2.2-3 K) — a pure level-function amp(dT) cannot do that; a warming-RATE deficit
(slow Southern-Ocean adjustment) can. Adding ssp119/ssp126/ssp370 spans the rate axis.

Estimator: windowed 41-yr trend ratio (land-frame AIS / global), per model x scenario;
windows with |global trend| < TREND_MIN masked (the estimator degenerates as scenarios
stabilize — noted in the summary, it thins ssp119/126 late-century windows).

Joint fit on the common-model subset (models present in ALL of FIT_SCENARIOS):
    pai = A_EQ - (A_EQ - a0)*exp(-dT/Ts) - c*rate        [rate in K/decade]
c > 0 means faster warming suppresses amplification at matched level = a time component.
c is bootstrapped over models. Outputs: figure, tidy CSV, summary md.
"""
import glob, os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IN_DIR    = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/cmip6_pai"
OUT_PNG   = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_cmip6_rate.png"
OUT_CSV   = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_cmip6_rate.csv"
OUT_MD    = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_cmip6_rate_summary.md"
# SSP3-7.0 EXCLUDED (Marcus 2026-07-22): it is the aerosol outlier (weak air-quality
# controls), and SH aerosol forcing confounds the amplification-vs-rate comparison.
# Its reduced series remain in data/cmip6_pai; exclusion is analysis-level only.
SCENARIOS = ["ssp119", "ssp126", "ssp245", "ssp585"]
FIT_SCENARIOS = ["ssp126", "ssp245", "ssp585"]   # common-model joint-fit set
SCEN_LABEL = {"ssp119": "SSP1-1.9", "ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5",
              "ssp370": "SSP3-7.0", "ssp585": "SSP5-8.5"}
COLORS = {"ssp119": "#00a9cf", "ssp126": "#173c66", "ssp245": "#f69320",
          "ssp370": "#e71d25", "ssp585": "#7f0a13"}
BASELINE  = (1850, 1900)
WINDOW    = 41
TREND_MIN = 0.05          # K/decade global-trend floor (display/estimator validity)
DT_MIN    = 0.6           # K; fit window
FIT_YEAR_MIN = 2005       # fit/table windows: centre year >= this (excludes the
                          # ozone-hole/aerosol era, where Antarctic trends are negative
                          # under non-GHG forcing)
FIT_RATE_MIN = 0.10       # K/decade; fit/table floor (ratio degenerates + ozone-recovery
                          # confound as scenarios stabilize, e.g. ssp126 post-2060)
A_EQ      = 1.196         # fixed asymptote (DAIS equilibrium slope)
DT_BINS   = [1.0, 1.5, 2.0, 2.5, 3.0]; DT_HALF = 0.15
NBOOT     = 500

def trend(y):
    x = np.arange(len(y)); return np.polyfit(x, y, 1)[0]

# ---- load base + ext series ----
series = {}
for f in sorted(glob.glob(os.path.join(IN_DIR, "tas_series_*.csv"))):
    b = os.path.basename(f)
    if b.startswith("tas_series_ext_"): continue
    model = b[len("tas_series_"):-len(".csv")]
    df = pd.read_csv(f)
    ext = os.path.join(IN_DIR, f"tas_series_ext_{model}.csv")
    if os.path.exists(ext):
        df = pd.concat([df, pd.read_csv(ext)])
    hist = df[(df.scenario == "historical") & (df.year <= 2014)]
    base = hist[hist.year.between(*BASELINE)][["tas_global", "tas_ais"]].mean()
    if len(hist) < 160: continue
    out = {}
    for sc in SCENARIOS:
        s = pd.concat([hist, df[df.scenario == sc]]).sort_values("year").set_index("year")
        s = s[~s.index.duplicated()]
        s = s[s.index <= 2100]
        if len(s.loc[2015:2100]) < 80: continue
        out[sc] = pd.DataFrame({"dTg": s.tas_global - base.tas_global,
                                "dTa": s.tas_ais    - base.tas_ais})
    if out: series[model] = out
avail = {sc: sorted(m for m in series if sc in series[m]) for sc in SCENARIOS}
common = sorted(set.intersection(*[set(avail[sc]) for sc in FIT_SCENARIOS]))
print("models per scenario: " + ", ".join(f"{sc} {len(avail[sc])}" for sc in SCENARIOS))
print(f"common subset over {FIT_SCENARIOS}: {len(common)} models")

# ---- windowed PAI ----
half = WINDOW // 2
rows = []
for model in series:
    for sc, s in series[model].items():
        yrs = s.index.values
        for c0 in range(yrs[0] + half, yrs[-1] - half + 1):
            w = s.loc[c0 - half: c0 + half]
            tg, ta = trend(w.dTg.values), trend(w.dTa.values)
            rows.append(dict(model=model, scenario=sc, year=c0, dT=w.dTg.mean(),
                             rate=tg * 10,
                             pai=(ta / tg) if abs(tg) >= TREND_MIN / 10 else np.nan))
pai = pd.DataFrame(rows); pai.to_csv(OUT_CSV, index=False)

# ---- matched-warming table (common subset; ssp119 with own pool, flagged) ----
tbl = []
for lev in DT_BINS:
    for sc in SCENARIOS:
        pool = common if sc in FIT_SCENARIOS else avail[sc]
        sub = pai[(pai.scenario == sc) & pai.model.isin(pool)
                  & pai.pai.notna() & pai.dT.between(lev - DT_HALF, lev + DT_HALF)
                  & (pai.year >= FIT_YEAR_MIN) & (pai.rate >= FIT_RATE_MIN)]
        if len(sub) < 10: continue
        tbl.append(dict(level=lev, scenario=sc, pai=sub.pai.median(),
                        year=int(sub.year.median()), rate=sub.rate.median(), n=len(sub)))
mw = pd.DataFrame(tbl)
print("\nmatched-warming medians (level: scenario pai@year, rate K/dec):")
for lev in DT_BINS:
    s = mw[mw.level == lev]
    if s.empty: continue
    print(f"  dT={lev:.1f}K: " + "  ".join(
        f"{r.scenario} {r.pai:.2f}@{r.year}(r={r.rate:.2f})" for r in s.itertuples()))

# ---- joint level+rate fit on scenario-MEDIAN curves (common subset) ----
# The per-model windowed ratio has fat-tailed noise (small-trend windows), so least
# squares on pooled raw points is outlier-dominated; fit the per-(scenario, year)
# median curves instead (same estimator as the 2-scenario diagnostic), and bootstrap
# the MODELS underlying the medians for the CI on c.
fitd = pai[pai.scenario.isin(FIT_SCENARIOS) & pai.model.isin(common)
           & pai.pai.notna() & (pai.dT >= DT_MIN)
           & (pai.year >= FIT_YEAR_MIN) & (pai.rate >= FIT_RATE_MIN)].copy()
def f_lr(X, a0, Ts, c):
    dT, rate = X
    return A_EQ - (A_EQ - a0) * np.exp(-dT / Ts) - c * rate
def f_l(dT, a0, Ts):
    return A_EQ - (A_EQ - a0) * np.exp(-dT / Ts)

def median_curves(df):
    m = df.groupby(["scenario", "year"])[["pai", "dT", "rate"]].median().dropna()
    return m[m.dT >= DT_MIN]

B_L  = ([-1.0, 0.1], [A_EQ, 10.0])          # a0, Ts bounds (Ts unbounded degenerates)
B_LR = ([-1.0, 0.1, -2.0], [A_EQ, 10.0, 2.0])
mc = median_curves(fitd)
p_l, _  = curve_fit(f_l, mc.dT.values, mc.pai.values, p0=[0.7, 1.0],
                    bounds=B_L, maxfev=20000)
p_lr, _ = curve_fit(f_lr, (mc.dT.values, mc.rate.values), mc.pai.values,
                    p0=[0.7, 1.0, 0.3], bounds=B_LR, maxfev=20000)
r_l  = np.sqrt(np.mean((f_l(mc.dT.values, *p_l) - mc.pai.values) ** 2))
r_lr = np.sqrt(np.mean((f_lr((mc.dT.values, mc.rate.values), *p_lr)
                        - mc.pai.values) ** 2))
boot = []
rng = np.random.default_rng(2026)
marr = np.array(common)
for _ in range(NBOOT):
    pick = rng.choice(marr, size=len(marr), replace=True)
    bs = pd.concat([fitd[fitd.model == m] for m in pick])
    try:
        bm = median_curves(bs)
        pb, _ = curve_fit(f_lr, (bm.dT.values, bm.rate.values), bm.pai.values,
                          p0=p_lr, bounds=B_LR, maxfev=20000)
        boot.append(pb[2])
    except Exception:
        pass
clo, chi = np.percentile(boot, [2.5, 97.5])
print(f"\nlevel-only fit:  a0={p_l[0]:.3f} Ts={p_l[1]:.2f}  RMSE {r_l:.3f}")
print(f"level+rate fit:  a0={p_lr[0]:.3f} Ts={p_lr[1]:.2f} c={p_lr[2]:.3f} "
      f"[{clo:.3f},{chi:.3f}] K^-1·decade  RMSE {r_lr:.3f}")
print(f"interpretation: rate term at 0.5 K/dec (ssp585 mid-century) = "
      f"{-0.5*p_lr[2]:+.2f}; at 0.15 K/dec (ssp126 mid-century) = {-0.15*p_lr[2]:+.2f}")

# ---- figure ----
fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))
for sc in SCENARIOS:
    pool = common if sc in FIT_SCENARIOS else avail[sc]
    sub = pai[(pai.scenario == sc) & pai.model.isin(pool)]
    med = sub.groupby("year")[["pai", "dT"]].median().dropna()
    axes[0].plot(med.index, med.pai, color=COLORS[sc], lw=1.8,
                 label=f"{SCEN_LABEL[sc]} (n={len(pool)})")
    axes[1].plot(med.dT, med.pai, color=COLORS[sc], lw=1.8, label=SCEN_LABEL[sc])
axes[0].set(title=f"Windowed amplification vs time ({WINDOW}-yr trend ratio, land frame)",
            xlabel="window centre year", ylabel="trend(T_AIS)/trend(T_glob)",
            xlim=(1980, 2085), ylim=(0.6, 1.5))
axes[1].set(title="vs global warming level", xlabel="window-mean ΔT_glob (K)",
            ylabel="trend ratio", xlim=(0, 4.3), ylim=(0.6, 1.5))
for ax in axes[:2]:
    ax.axhline(A_EQ, color="k", ls="--", lw=1, alpha=.5)
    ax.legend(frameon=False, fontsize=7.5)
res = fitd.assign(resid=fitd.pai - f_l(fitd.dT.values, *p_l))
rm = res.groupby(["scenario", "year"])[["resid", "rate"]].median().reset_index()
for sc in FIT_SCENARIOS:
    s = rm[rm.scenario == sc]
    axes[2].scatter(s.rate, s.resid, s=14, color=COLORS[sc], alpha=.7,
                    label=SCEN_LABEL[sc])
xx = np.linspace(0, rm.rate.max() * 1.05, 50)
axes[2].plot(xx, np.mean(rm.resid + p_lr[2] * rm.rate) - p_lr[2] * xx, "k-", lw=1.5,
             label=f"slope −c = −{p_lr[2]:.2f}")
axes[2].axhline(0, color="k", lw=.6, alpha=.4)
axes[2].set(title="Rate test: residual from level-only fit",
            xlabel="window global trend (K/decade)", ylabel="PAI residual")
axes[2].legend(frameon=False, fontsize=7.5)
fig.suptitle(f"CMIP6 Antarctic amplification: warming level + warming rate "
             f"(common subset {len(common)} models for fits; SSP3-7.0 excluded — "
             f"aerosol outlier)", fontsize=11)
fig.tight_layout(); fig.savefig(OUT_PNG, dpi=160)
print(f"wrote {OUT_PNG}")

with open(OUT_MD, "w") as f:
    f.write(f"# Level+rate decomposition ({len(common)}-model common subset for fits; "
            f"SSP3-7.0 excluded as the aerosol outlier)\n\n"
            f"pai = {A_EQ} - ({A_EQ} - a0)exp(-dT/Ts) - c*rate; windows {WINDOW} yr; "
            f"fit/table inclusion: centre year >= {FIT_YEAR_MIN} (excludes the "
            f"ozone-hole/aerosol era, negative Antarctic trends under non-GHG forcing), "
            f"global trend >= {FIT_RATE_MIN} K/dec (ratio degenerates + ozone-recovery "
            f"confound in stabilized windows), dT >= {DT_MIN} K.\n\n"
            f"- level-only: a0={p_l[0]:.3f}, Ts={p_l[1]:.2f}, RMSE {r_l:.3f}\n"
            f"- level+rate: a0={p_lr[0]:.3f}, Ts={p_lr[1]:.2f}, "
            f"**c={p_lr[2]:.3f} [{clo:.3f}, {chi:.3f}] per (K/decade)**, RMSE {r_lr:.3f}\n\n"
            f"Models/scenario: "
            + ", ".join(f"{sc} {len(avail[sc])}" for sc in SCENARIOS) + "\n\n"
            + mw.to_markdown(index=False) + "\n")
print(f"wrote {OUT_MD}")
