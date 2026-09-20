#!/usr/bin/env python3
"""
diag_ais_block_pca.py — principal components of the Antarctic block of a Ladrillo posterior, in PRIOR-sd
units, with the prior variance along each PC (identification) and a split R-hat across the four chains
(mixing). Marcus 2026-09-20: "Could we do something like PCA with the group of Antarctic variables on the
ridge?"  Answer: the unmixed direction is the PRIOR-DOMINATED one, not an identified ridge.

  python3 python/diag_ais_block_pca.py --tag=L26
Reads outputs/mcmc/chain_<tag>_seed{2026..2029}_n2000000.csv (2nd half, thinned 1:200), the paleo joint
prior (outputs/paleo_geo_prior_ton.csv), the paleo marginals (outputs/paleo_dais_marginals.csv), amp prior
N(1.09, 0.18), T_oc0 prior sd 0.50. Writes outputs/diag_ais_block_pca_<tag>.csv (+ provenance).
"""
import sys, os, datetime
import numpy as np, pandas as pd
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L26")
TBAR = -17.992322907746065          # LADRILLO_TBAR_ANT (ladrillo_projection.jl); only used for a --precip-reparam chain
GEO = ["ais_mu", "ais_bedheight0", "ais_slope", "ais_iceflow0", "ais_precip0_LOG", "ais_runoff_Ton", "ais_c"]
FD = ["ais_gmst_amp", "antarctic_alpha", "antarctic_nu", "antarctic_temp_threshold", "anto_alpha", "anto_beta",
      "antarctic_lambda", "antarctic_gamma", "antarctic_kappa", "ais_ocean_temperature₀"]
USE = GEO + FD
chains = []
for s in [2026, 2027, 2028, 2029]:
    f = os.path.join(REPO, f"outputs/mcmc/chain_{TAG}_seed{s}_n2000000.csv")
    hdr = open(f).readline().rstrip("\n").split(",")
    cols = [c for c in USE if c in hdr] + (["ais_precip_u"] if "ais_precip_u" in hdr else [])
    d = pd.read_csv(f, usecols=cols); d = d.iloc[len(d) // 2::200].copy()
    if "ais_precip_u" in d:
        d["ais_precip0_LOG"] = d.ais_precip_u - d.antarctic_kappa * TBAR
    chains.append(d[USE])
g = open(os.path.join(REPO, "outputs/paleo_geo_prior_ton.csv")).read().splitlines()
rows = {l.split(",")[0]: l.split(",")[1:] for l in g if l and not l.startswith("#")}
sd = np.array([float(x) for x in rows["sd"]])
corr = np.array([[float(v) for v in l.split(",")[1:]] for l in g if l.startswith("corr")])
pm = pd.read_csv(os.path.join(REPO, "outputs/paleo_dais_marginals.csv")).set_index("param")
psd = {**{c: pm.loc[c, "sd"] for c in FD if c in pm.index}, "ais_gmst_amp": 0.18, "ais_ocean_temperature₀": 0.50}
pmu = {**{c: pm.loc[c, "mean"] for c in FD if c in pm.index}, "ais_gmst_amp": 1.09, "ais_ocean_temperature₀": 0.72}
S = np.zeros((17, 17)); S[:7, :7] = np.outer(sd, sd) * corr
for i, c in enumerate(FD): S[7 + i, 7 + i] = psd[c] ** 2
mu = np.array([float(x) for x in rows["mean"]] + [pmu[c] for c in FD])
u = np.sqrt(np.diag(S))
Z = [(c.values - mu) / u for c in chains]
Cpost = np.cov(np.vstack(Z).T); Cpri = S / np.outer(u, u)
w, V = np.linalg.eigh(Cpost); o = np.argsort(w)[::-1]; w, V = w[o], V[:, o]
out = []
print(f"Antarctic block PCA, {TAG}, coordinates in prior-sd units; 4 chains x {len(Z[0])} draws")
print(f"{'PC':>3} {'post var':>9} {'prior var':>9} {'post/prior':>10} {'R-hat':>6}  loadings |>0.3|")
for k in range(17):
    v = V[:, k]; pv = v @ Cpri @ v
    sc = [z @ v for z in Z]; m = np.array([x.mean() for x in sc]); vv = np.array([x.var(ddof=1) for x in sc]); n = len(sc[0])
    W = vv.mean(); B = n * m.var(ddof=1); rhat = np.sqrt(((n - 1) / n * W + B / n) / W)
    load = ", ".join(f"{USE[i]}{v[i]:+.2f}" for i in np.argsort(-abs(v)) if abs(v[i]) > 0.3)
    print(f"{k+1:>3} {w[k]:9.3f} {pv:9.3f} {w[k]/pv:10.2f} {rhat:6.3f}  {load}")
    out.append(dict(pc=k + 1, post_var=w[k], prior_var=pv, ratio=w[k] / pv, rhat=rhat, loadings=load,
                    **{f"v_{USE[i]}": v[i] for i in range(17)}))
df = pd.DataFrame(out)
df["provenance"] = (f"diag_ais_block_pca.py | tag {TAG} | chains 2nd half thinned 1:200 | prior: paleo joint (geometry), "
                    f"paleo marginals (fast dynamics, ocean), amp N(1.09,0.18), Toc0 sd 0.5 | split R-hat over 4 chains | {datetime.date.today()}")
df.to_csv(os.path.join(REPO, f"outputs/diag_ais_block_pca_{TAG}.csv"), index=False)
print("cumulative variance first 3/5/8 PCs:", np.round(np.cumsum(w) / w.sum(), 2)[[2, 4, 7]])
