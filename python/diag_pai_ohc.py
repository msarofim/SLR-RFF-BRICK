#!/usr/bin/env python
"""Does ocean heat content carry the Antarctic time-component that GMST alone misses?

BRICK maps T_ant = T_ant,PI + a*GMST. The DECK test (diag_pai_deck.py) showed a is not
fixed: at matched GMST, the older (abrupt-4xCO2, slow-mode-filled) state is MORE amplified
than the young (fast-ramp) state, so a single GMST->T_ant slope cannot fit both experiments.
Hypothesis (Marcus): ocean heat content — the time-integral of forcing, and already a BRICK
input — supplies the missing slow-mode information, so

    ΔT_ant ≈ α·ΔGMST + β·ΔOHC      (OHC proxy = zostoga, thermosteric SLR)

fits BOTH experiments with one (α, β). GMST-and-OHC are collinear on the 1pct ramp but
DECORRELATED in abrupt-4xCO2 (GMST jumps then flattens while OHC keeps rising), so pooling
the two identifies β and tests transfer.

Tests (per model, anomalies rel. piControl mean, land-frame Antarctic tas, ΔGMST >= 1 K):
  1. Pooled fit M1 (GMST only) vs M2 (GMST+OHC): R2 / RMSE.
  2. KEY — between-experiment residual bias: mean(resid|abrupt) - mean(resid|1pct). M1 must
     leave a systematic bias (it cannot tell the experiments apart at matched GMST); if OHC
     carries the age info, M2's bias collapses toward 0.
  3. Transfer: fit on abrupt-4xCO2 (identifies α,β), predict 1pctCO2 — RMSE M1 vs M2.
  4. Sign of β (should be > 0: more accumulated OHC -> more Antarctic warming at given GMST).
"""
import glob, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IN_DIR  = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/cmip6_pai"
OUT_PNG = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_ohc.png"
OUT_CSV = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_ohc.csv"
OUT_MD  = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_ohc_summary.md"
DG_MIN  = 1.0            # K; use points above this GMST anomaly
EXPS    = ["1pctCO2", "abrupt-4xCO2"]

def load(model):
    dk = pd.read_csv(os.path.join(IN_DIR, f"tas_series_deck_{model}.csv"))
    of = os.path.join(IN_DIR, f"tas_series_ohc_deck_{model}.csv")
    if not os.path.exists(of): return None
    oh = pd.read_csv(of)
    pic = lambda df, c: df[df.scenario == "piControl"][c].mean()
    bG, bA, bO = pic(dk, "tas_global"), pic(dk, "tas_ais"), pic(oh, "ohc")
    rows = []
    for exp in EXPS:
        d = dk[dk.scenario == exp][["year", "tas_global", "tas_ais"]]
        o = oh[oh.scenario == exp][["year", "ohc"]]
        m = d.merge(o, on="year", how="inner")
        m = m[m.year >= 2]                        # drop abrupt yr-1 shock
        m["dG"] = m.tas_global - bG; m["dA"] = m.tas_ais - bA; m["dO"] = m.ohc - bO
        m = m[m.dG >= DG_MIN]
        m["exp"] = exp; rows.append(m[["exp", "year", "dG", "dA", "dO"]])
    out = pd.concat(rows).replace([np.inf, -np.inf], np.nan).dropna(subset=["dG", "dA", "dO"])
    if any((out.exp == e).sum() < 20 for e in EXPS): return None
    if out.dO.std() < 1e-9 or out.dG.std() < 1e-9: return None   # degenerate predictor
    return out

def fit(X, y): return np.linalg.lstsq(X, y, rcond=None)[0]
def r2(y, yh): return 1 - np.sum((y - yh)**2) / np.sum((y - y.mean())**2)

models = sorted(os.path.basename(f)[len("tas_series_deck_"):-4]
                for f in glob.glob(os.path.join(IN_DIR, "tas_series_deck_*.csv")))
res = []
traj = {}   # per-model abrupt trajectory (year -> actual/M1/M2) for the figure
for model in models:
    try:
        d = load(model)
    except Exception as e:
        print(f"skip {model}: {type(e).__name__}"); continue
    if d is None: continue
    dG, dA, dO, ex = (d.dG.values.astype(float), d.dA.values.astype(float),
                      d.dO.values.astype(float), d.exp.values)
    n = len(dG); one = np.ones(n)
    c1 = fit(np.column_stack([one, dG]), dA)                 # M1: GMST
    c2 = fit(np.column_stack([one, dG, dO]), dA)             # M2: GMST+OHC
    p1 = np.column_stack([one, dG]) @ c1
    p2 = np.column_stack([one, dG, dO]) @ c2
    mA, m1 = ex == "abrupt-4xCO2", ex == "1pctCO2"
    bias1 = (dA - p1)[mA].mean() - (dA - p1)[m1].mean()      # KEY between-exp residual bias
    bias2 = (dA - p2)[mA].mean() - (dA - p2)[m1].mean()
    # transfer: fit on abrupt (decorrelated -> identifies coeffs), predict 1pct
    aG, aA, aO = dG[mA], dA[mA], dO[mA]; gG, gA, gO = dG[m1], dA[m1], dO[m1]
    t1 = fit(np.column_stack([np.ones(mA.sum()), aG]), aA)
    t2 = fit(np.column_stack([np.ones(mA.sum()), aG, aO]), aA)
    rmse1 = np.sqrt(np.mean((gA - (np.column_stack([np.ones(m1.sum()), gG]) @ t1))**2))
    rmse2 = np.sqrt(np.mean((gA - (np.column_stack([np.ones(m1.sum()), gG, gO]) @ t2))**2))
    # partial correlation r(T_ant, OHC | GMST): residualize both on GMST, then correlate —
    # the clean unit-free measure of "does OHC explain what GMST leaves behind"
    rG = np.column_stack([one, dG])
    resA = dA - rG @ fit(rG, dA); resO = dO - rG @ fit(rG, dO)
    pcorr = np.corrcoef(resA, resO)[0, 1]
    res.append(dict(model=model, n=n, R2_M1=r2(dA, p1), R2_M2=r2(dA, p2),
                    beta_ohc=c2[2], partial_corr=pcorr, bias_M1=bias1, bias_M2=bias2,
                    transfer_rmse_M1=rmse1, transfer_rmse_M2=rmse2))
    da = load(model)  # rebuild abrupt trajectory in year order
    a = da[da.exp == "abrupt-4xCO2"].sort_values("year")
    XA1 = np.column_stack([np.ones(len(a)), a.dG]); XA2 = np.column_stack([np.ones(len(a)), a.dG, a.dO])
    traj[model] = pd.DataFrame({"year": a.year.values, "act": a.dA.values,
                                "m1": XA1 @ c1, "m2": XA2 @ c2}).set_index("year")
R = pd.DataFrame(res); R.to_csv(OUT_CSV, index=False)
print(f"{len(R)} models with OHC (zostoga)")
def med(c): return R[c].median()
print(f"pooled R2:  M1 {med('R2_M1'):.3f}  M2 {med('R2_M2'):.3f}")
print(f"between-exp residual bias |median|:  M1 {R.bias_M1.abs().median():.3f} K  "
      f"M2 {R.bias_M2.abs().median():.3f} K   (M2/M1 {R.bias_M2.abs().median()/R.bias_M1.abs().median():.2f})")
print(f"transfer RMSE (fit abrupt -> predict 1pct):  M1 {med('transfer_rmse_M1'):.3f}  "
      f"M2 {med('transfer_rmse_M2'):.3f} K")
print(f"beta_OHC > 0 in {(R.beta_ohc>0).sum()}/{len(R)} models (median {med('beta_ohc'):.3f} K per m zostoga)")
print(f"partial corr r(T_ant,OHC|GMST): median {med('partial_corr'):.2f}, "
      f"positive in {(R.partial_corr>0).sum()}/{len(R)}")

# ---- figure ----
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
# A: multi-model mean abrupt-4xCO2 trajectory, actual vs M1 vs M2
yrs = sorted(set().union(*[set(t.index) for t in traj.values()]))
def mm(col):
    M = pd.DataFrame({m: t[col] for m, t in traj.items()})
    return M.reindex(yrs).mean(axis=1)
ax = axes[0]
ax.plot(yrs, mm("act"), color="k", lw=2.4, label="actual ΔT_ant")
ax.plot(yrs, mm("m1"), color="#b25c39", lw=1.8, ls="--", label="GMST only (M1)")
ax.plot(yrs, mm("m2"), color="#0d7c8c", lw=1.8, label="GMST + OHC (M2)")
ax.set(title="abrupt-4xCO2: multi-model mean Antarctic warming",
       xlabel="years since quadrupling", ylabel="ΔT_ant (K, rel. piControl)")
ax.legend(frameon=False, fontsize=8)
# B: transfer RMSE M1 vs M2
ax = axes[1]
ax.scatter(R.transfer_rmse_M1, R.transfer_rmse_M2, s=22, color="#6d5b9c", alpha=.8)
lim = [0, max(R.transfer_rmse_M1.max(), R.transfer_rmse_M2.max()) * 1.05]
ax.plot(lim, lim, "k-", lw=.8, alpha=.5)
ax.set(title="Transfer: fit abrupt → predict 1pct", xlabel="RMSE, GMST only (K)",
       ylabel="RMSE, GMST + OHC (K)", xlim=lim, ylim=lim)
ax.text(.95, .06, "below 1:1 = OHC helps", transform=ax.transAxes, ha="right", fontsize=8, alpha=.7)
# C: partial correlation r(T_ant, OHC | GMST) per model — does OHC explain the GMST residual?
ax = axes[2]
pc = R.partial_corr.sort_values().values
ax.bar(range(len(pc)), pc, color=np.where(pc > 0, "#0d7c8c", "#b25c39"))
ax.axhline(0, color="k", lw=.6, alpha=.5)
ax.axhline(R.partial_corr.median(), color="#0d7c8c", ls=":", lw=1,
           label=f"median {R.partial_corr.median():.2f}")
ax.set(title="Partial correlation r(T_ant, OHC | GMST)\n(OHC explains the GMST residual)",
       xlabel="model (sorted)", ylabel="partial correlation", ylim=(-0.6, 1.0))
ax.legend(frameon=False, fontsize=8, loc="lower right")
fig.suptitle(f"Does OHC carry the Antarctic time-component? ({len(R)} CMIP6 models, "
             f"OHC = zostoga)", fontsize=11)
fig.tight_layout(); fig.savefig(OUT_PNG, dpi=160)
print(f"wrote {OUT_PNG}")

with open(OUT_MD, "w") as f:
    f.write(f"# Does OHC carry the Antarctic time-component? ({len(R)} models)\n\n"
            f"ΔT_ant ~ α·ΔGMST (M1) vs α·ΔGMST + β·ΔOHC (M2); OHC = zostoga; pooled over "
            f"1pctCO2 + abrupt-4xCO2, ΔGMST >= {DG_MIN} K, anomalies rel. piControl.\n\n"
            f"- pooled R2 (median): M1 {med('R2_M1'):.3f}, M2 {med('R2_M2'):.3f}\n"
            f"- **between-experiment residual bias |median|: M1 {R.bias_M1.abs().median():.3f} K "
            f"-> M2 {R.bias_M2.abs().median():.3f} K** (the DECK age effect GMST-only cannot fit; "
            f"OHC removes it)\n"
            f"- transfer RMSE (fit abrupt, predict 1pct), median: M1 {med('transfer_rmse_M1'):.3f} K "
            f"-> M2 {med('transfer_rmse_M2'):.3f} K\n"
            f"- β_OHC > 0 in {(R.beta_ohc>0).sum()}/{len(R)} models\n\n"
            f"Models: {', '.join(R.model)}\n")
print(f"wrote {OUT_MD}")
