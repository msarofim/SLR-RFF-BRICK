#!/usr/bin/env python3
"""What would the Rignot SMB anchor's AREA SCALING change? Importance-reweighting receipt (GMD Table 3 note 17).

The calibrator scores the model's 1979-2008 mean Antarctic SMB against Rignot et al. (2019) 2098 ± 133 Gt/yr scaled
by 10.92/12.295 = 0.888 (julia/calibrate_mcmc_ext.jl SMB_TARGET_GT). 10.92e6 km2 is DAIS's idealised pi*R0^2 disc;
12.295e6 km2 is the Bedmap2 grounded-ice area (Fretwell et al. 2013, Table 7, "area excluding ice shelves").
Rignot et al.'s OWN basin total is 12,353e3 km2 and includes the peripheral islands (163.0e3 km2; SMB 77.0 ± 4.5);
the regional rows sum to 12,352 and 2098.

Two alternatives, each scored against the shipped posterior by importance weights w = N_new(s)/N_old(s) on each
draw's own 1979-2008 SMB s. The SMB term is the only likelihood term that changes, so the weights are exact:
  rignot_total     2098 ± 133 over 12.353 (islands included, as Rignot's 2098 is)
  excl_islands     2021 ± 128.5 over 12.189 (islands removed from both; Rignot's ±133 is the LINEAR sum of the
                   regional errors, 27+38+63+4.5 = 132.5, so the islands' 4.5 is removed linearly)
Reports the shift of the posterior mean SMB, in Gt/yr and in posterior sd, and the ESS. No RNG.

  python3 python/diag_smb_area_reweight.py [--tag=L27]   # writes outputs/diag_smb_area_reweight_<tag>.csv
"""
import argparse, hashlib, os, subprocess
import numpy as np
import pandas as pd
from scipy.stats import norm

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAIS_AREA = 10.92          # 1e6 km2, pi*R0^2 with R0 = 1.864e6 m
SHIPPED = dict(arm="shipped_bedmap2", smb=2098.0, sig=133.0, area=12.295)
ARMS = [dict(arm="rignot_total", smb=2098.0, sig=133.0, area=12.353),
        dict(arm="excl_islands", smb=2098.0 - 77.0, sig=133.0 - 4.5, area=12.353 - 0.163)]

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="L27")
a = ap.parse_args()
src = os.path.join(REPO, f"outputs/diag_ais_flux_split_vs_imbie_draws_{a.tag}.csv")
OUT = os.path.join(REPO, f"outputs/diag_smb_area_reweight_{a.tag}.csv")
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
md5 = hashlib.md5(open(src, "rb").read()).hexdigest()[:8]

s = pd.read_csv(src)["smb_1979_2008"].to_numpy()
tgt = lambda c: (c["smb"] * DAIS_AREA / c["area"], c["sig"] * DAIS_AREA / c["area"])
mu0, sd0 = tgt(SHIPPED)
rows = [dict(arm=SHIPPED["arm"], factor=DAIS_AREA / SHIPPED["area"], target_gt=mu0, sigma_gt=sd0,
             post_mean_gt=s.mean(), shift_gt=0.0, shift_post_sd=0.0, ess=float(len(s)))]
for c in ARMS:
    mu, sd = tgt(c)
    lw = norm.logpdf(s, mu, sd) - norm.logpdf(s, mu0, sd0)
    w = np.exp(lw - lw.max()); w /= w.sum()
    m = float((w * s).sum())
    rows.append(dict(arm=c["arm"], factor=DAIS_AREA / c["area"], target_gt=mu, sigma_gt=sd, post_mean_gt=m,
                     shift_gt=m - s.mean(), shift_post_sd=(m - s.mean()) / s.std(), ess=float(1 / (w ** 2).sum())))
df = pd.DataFrame(rows)
df["provenance"] = (f"diag_smb_area_reweight.py | tag {a.tag} | per-draw SMB from {os.path.basename(src)} md5 {md5} "
                    f"n={len(s)} | Gt/yr, 1979-2008 mean | importance weights on the SMB term only | no RNG | commit {commit}")
df.to_csv(OUT, index=False)
print(df.drop(columns="provenance").round(4).to_string(index=False))
print(f"wrote {os.path.relpath(OUT, REPO)}")
