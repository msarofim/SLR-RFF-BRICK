#!/usr/bin/env python
"""PAI-vs-time diagnostic: does the GMST->Antarctic amplification rise with time /
temperature WITHIN a scenario (ssp245, ssp585)?

Input: data/cmip6_pai/tas_series_<model>.csv from reduce_cmip6_tas_pai.py
       (annual tas_global, tas_ais in K; historical + ssp245 + ssp585).

Estimator (primary, Xie-consistent): sliding-window PAI1 = OLS trend(T_ais) /
OLS trend(T_global) over WINDOW-year windows (windowed version of Xie et al. 2022's
full-period trend ratio). Trend ratios isolate the forced, time-linear component;
windows where the global trend is below TREND_MIN K/decade are masked (ratio unstable).

Panels:
  (a) PAI1(t) per model + multi-model median, ssp245;
  (b) same, ssp585;
  (c) collapse test — median PAI1 vs window-mean dT_global (rel BASELINE), both scenarios:
      curves collapsing onto one line => temperature-controlled; separating => time/
      composition-controlled.
Reference lines: BRICK-FM A6 transient prior 0.95 and DAIS equilibrium 1.196.

VALIDATION GATE: full-window 2015-2100 MMEM PAI1 must land near Xie et al. 2022
Table 1 (ssp245 0.95, ssp585 1.03) — printed with pass/fail vs XIE_TOL.
"""
import glob, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IN_DIR     = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/cmip6_pai"
OUT_PNG    = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_cmip6_time.png"
OUT_CSV    = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_cmip6_time.csv"
OUT_MD     = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_cmip6_time_summary.md"
SCENARIOS  = ["ssp245", "ssp585"]
SCEN_LABEL = {"ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
BASELINE   = (1850, 1900)      # anomaly reference (Xie's historical baseline)
WINDOW     = 41                # sliding-window length, years (odd; centered)
TREND_MIN  = 0.05              # K/decade global-trend floor for a valid ratio
XIE_FULL   = (2015, 2100)      # Xie et al. 2022 PAI1 trend window
XIE_VALS   = {"ssp245": 0.95, "ssp585": 1.03}   # Xie Table 1, annual PAI1 over AIS
XIE_TOL    = 0.10              # |MMEM - Xie| gate (their model set differs from ours)
AMP_TRANS  = 0.95              # BRICK-FM A6 transient prior mean
AMP_EQ     = 1.196             # DAIS equilibrium amplification (1/0.8365)

def trend(y):
    x = np.arange(len(y))
    return np.polyfit(x, y, 1)[0]

series = {}
for f in sorted(glob.glob(os.path.join(IN_DIR, "tas_series_*.csv"))):
    model = os.path.basename(f)[len("tas_series_"):-len(".csv")]
    df = pd.read_csv(f)
    base = df[(df.scenario == "historical")
              & df.year.between(*BASELINE)][["tas_global", "tas_ais"]].mean()
    hist = df[(df.scenario == "historical") & (df.year <= 2014)]  # some stores run past 2014
    out = {}
    for sc in SCENARIOS:
        s = pd.concat([hist, df[df.scenario == sc]]).sort_values("year").set_index("year")
        s = s[s.index <= 2100]   # a few models carry post-2100 extensions; keep the common window
        out[sc] = pd.DataFrame({"dTg": s.tas_global - base.tas_global,
                                "dTa": s.tas_ais    - base.tas_ais})
    # coverage filter: need essentially-complete 1850-2100 in BOTH scenarios
    ok = all(len(out[sc].loc[1850:2014]) >= 160 and len(out[sc].loc[2015:2100]) >= 85
             for sc in SCENARIOS)
    if not ok:
        print(f"DROP {model}: incomplete coverage "
              + str({sc: (int(out[sc].index.min()), int(out[sc].index.max()),
                          len(out[sc])) for sc in SCENARIOS}))
        continue
    series[model] = out
models = sorted(series)
print(f"{len(models)} models: {', '.join(models)}")

# ---- sliding-window PAI1 per model ----
half = WINDOW // 2
rows = []
for model in models:
    for sc in SCENARIOS:
        s = series[model][sc]
        yrs = s.index.values
        for c in range(yrs[0] + half, yrs[-1] - half + 1):
            w = s.loc[c - half: c + half]
            tg, ta = trend(w.dTg.values), trend(w.dTa.values)
            rows.append(dict(model=model, scenario=sc, year=c,
                             dTg_win=w.dTg.mean(), trend_g=tg * 10,
                             pai=(ta / tg) if abs(tg) >= TREND_MIN / 10 else np.nan))
pai = pd.DataFrame(rows)
pai.to_csv(OUT_CSV, index=False)

med = pai.groupby(["scenario", "year"])[["pai", "dTg_win"]].median()
q25 = pai.groupby(["scenario", "year"])["pai"].quantile(.25)
q75 = pai.groupby(["scenario", "year"])["pai"].quantile(.75)

# ---- validation gate: full-window MMEM PAI1 vs Xie ----
gate_lines = []
for sc in SCENARIOS:
    vals = []
    for model in models:
        s = series[model][sc].loc[XIE_FULL[0]: XIE_FULL[1]]
        vals.append(trend(s.dTa.values) / trend(s.dTg.values))
    # Xie uses the trend of the multi-model ensemble MEAN series; approximate with
    # mean-of-model-ratios AND ratio-of-mean-series, report both. Per-year mean skips
    # models missing that year (coverage differs by +-1 yr at the edges).
    sgm = pd.DataFrame({m: series[m][sc].loc[XIE_FULL[0]:XIE_FULL[1]].dTg
                        for m in models}).mean(axis=1).dropna()
    sam = pd.DataFrame({m: series[m][sc].loc[XIE_FULL[0]:XIE_FULL[1]].dTa
                        for m in models}).mean(axis=1).dropna()
    mmem = trend(sam.values) / trend(sgm.values)
    ok = abs(mmem - XIE_VALS[sc]) <= XIE_TOL
    gate_lines.append(f"{SCEN_LABEL[sc]}: MMEM-series PAI1 {mmem:.3f} "
                      f"(mean-of-ratios {np.mean(vals):.3f}, model range "
                      f"{np.min(vals):.2f}-{np.max(vals):.2f}) vs Xie {XIE_VALS[sc]:.2f} "
                      f"-> {'PASS' if ok else 'FAIL'} (tol {XIE_TOL})")
    print("GATE " + gate_lines[-1])

# ---- within-scenario time trend of the median PAI ----
trend_lines = []
for sc in SCENARIOS:
    m = med.loc[sc].dropna()
    m21 = m[(m.index >= 2015 + half) & (m.index <= 2100 - half)]
    b = np.polyfit(m21.index, m21.pai, 1)[0] * 10
    first, last = m21.pai.iloc[:10].mean(), m21.pai.iloc[-10:].mean()
    trend_lines.append(f"{SCEN_LABEL[sc]}: median PAI1 {first:.2f} (early windows) -> "
                       f"{last:.2f} (late windows); within-scenario slope {b:+.3f}/decade")
    print("TREND " + trend_lines[-1])

# ---- figure ----
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
colors = {"ssp245": "#0d7c8c", "ssp585": "#b25c39"}
for ax, sc in zip(axes[:2], SCENARIOS):
    for model in models:
        p = pai[(pai.model == model) & (pai.scenario == sc)]
        ax.plot(p.year, p.pai, color=colors[sc], alpha=.18, lw=.8)
    m = med.loc[sc]
    ax.fill_between(m.index, q25.loc[sc], q75.loc[sc], color=colors[sc], alpha=.20, lw=0)
    ax.plot(m.index, m.pai, color=colors[sc], lw=2.2, label="multi-model median")
    ax.axhline(AMP_TRANS, color="k", ls=":", lw=1, alpha=.6)
    ax.axhline(AMP_EQ, color="k", ls="--", lw=1, alpha=.6)
    ax.text(1902, AMP_TRANS, f" A6 transient {AMP_TRANS}", va="bottom", fontsize=8, alpha=.7)
    ax.text(1902, AMP_EQ, f" DAIS equilibrium {AMP_EQ}", va="bottom", fontsize=8, alpha=.7)
    ax.set(title=f"{SCEN_LABEL[sc]}: windowed PAI1 ({WINDOW}-yr trend ratio)",
           xlabel="window centre year", ylabel="PAI1 = trend(T_AIS)/trend(T_glob)",
           ylim=(-0.5, 2.5))
    ax.legend(frameon=False, fontsize=8)
ax = axes[2]
for sc in SCENARIOS:
    m = med.loc[sc].dropna()
    ax.plot(m.dTg_win, m.pai, color=colors[sc], lw=2.2, label=SCEN_LABEL[sc])
ax.axhline(AMP_TRANS, color="k", ls=":", lw=1, alpha=.6)
ax.axhline(AMP_EQ, color="k", ls="--", lw=1, alpha=.6)
ax.set(title="Collapse test: median PAI1 vs global warming level",
       xlabel=f"window-mean ΔT_global rel {BASELINE[0]}–{BASELINE[1]} (K)",
       ylabel="median PAI1")
ax.legend(frameon=False, fontsize=9)
fig.suptitle(f"CMIP6 Antarctic amplification vs time and warming level "
             f"({len(models)} models, AIS = land ≥50% south of 60°S)", fontsize=11)
fig.tight_layout()
fig.savefig(OUT_PNG, dpi=160)
print(f"wrote {OUT_PNG}")

with open(OUT_MD, "w") as f:
    f.write(f"# PAI-vs-time diagnostic ({len(models)} CMIP6 models)\n\n"
            f"Windowed PAI1 = {WINDOW}-yr trend(T_AIS)/trend(T_glob); AIS = land "
            f"(sftlf>=50%) south of 60S; anomalies rel {BASELINE}; global-trend floor "
            f"{TREND_MIN} K/decade.\n\n## Validation gate (Xie et al. 2022 Table 1)\n"
            + "".join(f"- {l}\n" for l in gate_lines)
            + "\n## Within-scenario time dependence\n"
            + "".join(f"- {l}\n" for l in trend_lines)
            + f"\nModels: {', '.join(models)}\n")
print(f"wrote {OUT_MD}")
