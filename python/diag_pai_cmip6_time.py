#!/usr/bin/env python
"""Antarctic amplification vs time and warming level, as the SECANT (level) ratio that
BRICK's `a` actually represents:

    R(t) = [smooth30(T_AIS)(t) - T_AIS,PI] / [smooth30(T_glob)(t) - T_glob,PI]

i.e. cumulative warming-since-preindustrial ratio, NOT the sliding-window marginal
trend ratio (that earlier version is superseded — the secant is the BRICK-relevant
quantity and needs no marginal->level integration). Each temperature is a SMOOTH-year
running mean; PI = mean over BASELINE; pre-START_YEAR is dropped (small denominators =
noise). Land-frame AIS (land >=50% south of 60S).

Input: data/cmip6_pai/tas_series_<model>.csv (historical + ssp245 + ssp585).
Panels: (a) R(t) ssp245, (b) R(t) ssp585, (c) collapse R vs dT_glob, both scenarios.
Reference lines: proposal-A constant AMP_PROP and DAIS equilibrium AMP_EQ.

NOTE: R is a LEVEL ratio, directly comparable to BRICK `a` and to the DECK 1pctCO2
secant (diag_pai_deck.py) — it is NOT Xie et al.'s trend-ratio PAI1, so the old Xie gate
does not apply. Cross-check is against the DECK 1pct GHG-only secant instead.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pai_series import model_series_files
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
BASELINE   = (1850, 1900)      # pre-industrial reference for both T_AIS and T_glob
SMOOTH     = 30                # running-mean length, years (centered)
SMOOTH_MINP = 15              # min periods -> coverage extends to ~2100 (asymmetric ends)
START_YEAR = 1950             # drop pre-1950 (denominator too small -> noisy)
DT_BINS    = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]; DT_HALF = 0.15
AMP_PROP   = 1.08             # proposal-A constant `a` (direct-secant crossing-relevant value)
AMP_EQ     = 1.196            # DAIS equilibrium amplification (1/0.8365)
COLORS     = {"ssp245": "#0d7c8c", "ssp585": "#b25c39"}

series = {}
## Which files are per-model series is resolved ONCE, in python/pai_series.py, with a
## schema gate behind the filename filter -- the inline prefix tuple that used to live
## here went stale when the OHC reduction landed in the same directory.
for model, f in sorted(model_series_files(IN_DIR).items()):
    df = pd.read_csv(f)
    base = df[(df.scenario == "historical")
              & df.year.between(*BASELINE)][["tas_global", "tas_ais"]].mean()
    hist = df[(df.scenario == "historical") & (df.year <= 2014)]
    out = {}
    for sc in SCENARIOS:
        s = pd.concat([hist, df[df.scenario == sc]]).sort_values("year").set_index("year")
        s = s[(~s.index.duplicated()) & (s.index <= 2100)]
        dTg = (s.tas_global - base.tas_global).rolling(SMOOTH, center=True,
                                                       min_periods=SMOOTH_MINP).mean()
        dTa = (s.tas_ais    - base.tas_ais).rolling(SMOOTH, center=True,
                                                    min_periods=SMOOTH_MINP).mean()
        R = (dTa / dTg).where(dTg > 0.1)          # guard tiny/neg denominators
        out[sc] = pd.DataFrame({"dTg": dTg, "R": R}).loc[START_YEAR:]
    ok = all(out[sc].R.loc[2000:2090].notna().sum() >= 60 for sc in SCENARIOS)
    if not ok:
        print(f"DROP {model}: incomplete coverage"); continue
    series[model] = out
models = sorted(series)
print(f"{len(models)} models: {', '.join(models)}")

rows = []
for model in models:
    for sc in SCENARIOS:
        s = series[model][sc]
        for yr, r, dt in zip(s.index, s.R, s.dTg):
            rows.append(dict(model=model, scenario=sc, year=yr, dTg=dt, R=r))
sec = pd.DataFrame(rows); sec.to_csv(OUT_CSV, index=False)
med = sec.groupby(["scenario", "year"])[["R", "dTg"]].median()
q25 = sec.groupby(["scenario", "year"]).R.quantile(.25)
q75 = sec.groupby(["scenario", "year"]).R.quantile(.75)

# ---- within-scenario rise + matched-warming secant table ----
rise_lines = []
for sc in SCENARIOS:
    m = med.loc[sc].R.dropna()
    early, late = m.loc[1950:1975].mean(), m.loc[2065:2090].mean()
    rise_lines.append(f"{SCEN_LABEL[sc]}: median secant {early:.2f} (1950-75) -> "
                      f"{late:.2f} (2065-90)")
    print("RISE " + rise_lines[-1])
tbl = []
for dt in DT_BINS:
    row = {"dT": dt}
    for sc in SCENARIOS:
        s = sec[(sec.scenario == sc) & sec.R.notna() & sec.dTg.between(dt - DT_HALF, dt + DT_HALF)]
        g = s.groupby("model").R.median()
        row[sc] = g.median() if len(g) >= 8 else np.nan
        row[f"{sc}_n"] = len(g)
    tbl.append(row)
mw = pd.DataFrame(tbl)
print("\nmatched-warming SECANT ratio (median over models):")
for _, r in mw.iterrows():
    print(f"  dT={r.dT:.1f}K:  ssp245 {r.ssp245:.3f} (n={int(r.ssp245_n)})  "
          f"ssp585 {r.ssp585:.3f} (n={int(r.ssp585_n)})")

# ---- figure ----
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
for ax, sc in zip(axes[:2], SCENARIOS):
    for model in models:
        s = series[model][sc]
        ax.plot(s.index, s.R, color=COLORS[sc], alpha=.16, lw=.8)
    m = med.loc[sc]
    ax.fill_between(m.index, q25.loc[sc], q75.loc[sc], color=COLORS[sc], alpha=.20, lw=0)
    ax.plot(m.index, m.R, color=COLORS[sc], lw=2.2, label="multi-model median")
    ax.axhline(AMP_PROP, color="k", ls=":", lw=1, alpha=.6)
    ax.axhline(AMP_EQ, color="k", ls="--", lw=1, alpha=.6)
    ax.text(START_YEAR + 2, AMP_PROP, f" proposal a = {AMP_PROP:.2f}", va="bottom",
            fontsize=8, alpha=.7)
    ax.text(START_YEAR + 2, AMP_EQ, f" DAIS equilibrium {AMP_EQ}", va="bottom",
            fontsize=8, alpha=.7)
    ax.set(title=f"{SCEN_LABEL[sc]}: amplification ratio ({SMOOTH}-yr mean, rel. PI)",
           xlabel="year", ylabel="Antarctic amplification ratio",
           xlim=(START_YEAR, 2100), ylim=(0.6, 1.5))
    ax.legend(frameon=False, fontsize=8)
ax = axes[2]
for sc in SCENARIOS:
    m = med.loc[sc].dropna().sort_values("dTg")
    ax.plot(m.dTg, m.R, color=COLORS[sc], lw=2.2, label=SCEN_LABEL[sc])
ax.axhline(AMP_PROP, color="k", ls=":", lw=1, alpha=.6)
ax.axhline(AMP_EQ, color="k", ls="--", lw=1, alpha=.6)
ax.set(title="Collapse test: amplification ratio vs warming level",
       xlabel=f"ΔT_global rel {BASELINE[0]}–{BASELINE[1]} (K)",
       ylabel="Antarctic amplification ratio", ylim=(0.6, 1.5))
ax.legend(frameon=False, fontsize=9)
fig.suptitle(f"CMIP6 Antarctic amplification ratio since pre-industrial "
             f"({len(models)} models, land-frame AIS, post-{START_YEAR})", fontsize=11)
fig.tight_layout(); fig.savefig(OUT_PNG, dpi=160)
print(f"wrote {OUT_PNG}")

with open(OUT_MD, "w") as f:
    f.write(f"# Antarctic amplification, SECANT (level) ratio ({len(models)} CMIP6 models)\n\n"
            f"R = [smooth{SMOOTH}(T_AIS) - T_AIS,PI] / [smooth{SMOOTH}(T_glob) - T_glob,PI]; "
            f"PI = {BASELINE}; centered {SMOOTH}-yr mean; plotted post-{START_YEAR}; "
            f"land-frame AIS. This is a LEVEL ratio (= BRICK `a`), NOT Xie's trend ratio.\n\n"
            f"## Within-scenario rise\n"
            + "".join(f"- {l}\n" for l in rise_lines)
            + "\n## Matched-warming secant ratio (median over models)\n"
            + mw[["dT", "ssp245", "ssp585"]].to_markdown(index=False, floatfmt=".3f") + "\n\n"
            f"Models: {', '.join(models)}\n")
print(f"wrote {OUT_MD}")
