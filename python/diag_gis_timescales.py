#!/usr/bin/env python3
"""Greenland relaxation timescales at present-day temperature, per posterior draw (receipt for the GMD draft).

GMD draft, Greenland 'Two channels' paragraph: "about a 110-year relaxation timescale at present-day
temperatures in the active basin" (SMB) and "about a 290-year" (discharge). Those were computed on 09-29
and recorded only in CHANGELOG; this script makes them reproducible.

Definitions (julia/calibrate_mcmc_ext.jl, Greenland block):
  fast (SMB) channel       rate_f(T) = alpha_f*T + beta_f          tau_f = 1 / rate_f(Tbar)
  slow (discharge) channel ell = log rate_s(Tbar)                  tau_s = exp(-ell)
The active (south) basin is the reference basin, pinned at scale s = 1 (GISB_REF), so no basin scale
enters. Tbar = mean of the south-zone regional temperature over GIS_TBAR_WIN, derived from the same
driver file the calibrator reads and asserted against its 1.963 K anchor. No RNG.

  python3 python/diag_gis_timescales.py [--tag=L27]     # writes outputs/diag_gis_timescales_<tag>.csv
"""
import argparse, hashlib, os, subprocess
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIS_ZONE = "south"
GIS_TBAR_WIN = (2015, 2024)
GIS_TBAR_ANCHOR = 1.963          # calibrate_mcmc_ext.jl GIS_TBAR_REPARAM_ANCHOR
QUANTILES = (0.05, 0.50, 0.95)

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="L27")
a = ap.parse_args()

post_path = os.path.join(REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{a.tag}.csv")
tgz_path = os.path.join(REPO, "data/observations/t_gis_zones.csv")
OUT = os.path.join(REPO, f"outputs/diag_gis_timescales_{a.tag}.csv")
md5 = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()[:8]
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

tgz = pd.read_csv(tgz_path)
win = tgz[(tgz.year >= GIS_TBAR_WIN[0]) & (tgz.year <= GIS_TBAR_WIN[1])]
tbar = float(win[GIS_ZONE].mean())
assert abs(tbar - GIS_TBAR_ANCHOR) < 5e-3, f"Tbar {tbar:.4f} K disagrees with the {GIS_TBAR_ANCHOR} K anchor"

p = pd.read_csv(post_path)
rate_f = p["gis_alpha_f"] * tbar + p["gis_beta_f"]
assert (rate_f > 0).all(), "non-positive fast rate at Tbar"
tau = {"fast_smb": 1.0 / rate_f, "slow_discharge": np.exp(-p["gis_slow_ell"])}

prov = (f"diag_gis_timescales.py | tag {a.tag} | posterior {os.path.basename(post_path)} md5 {md5(post_path)} "
        f"n={len(p)} | Tbar {tbar:.4f} K = {GIS_ZONE} zone mean {GIS_TBAR_WIN[0]}-{GIS_TBAR_WIN[1]} from "
        f"t_gis_zones.csv md5 {md5(tgz_path)} | active basin (s=1) | per-draw quantiles | no RNG | commit {commit}")
rows = []
for ch, t in tau.items():
    q = np.quantile(t, QUANTILES)
    rows.append(dict(channel=ch, tbar_K=round(tbar, 4), units="yr",
                     **{f"p{int(100*x):02d}": v for x, v in zip(QUANTILES, q)}, provenance=prov))
    print(f"{ch:15s} tau = {q[1]:6.1f} yr  ({int(100*QUANTILES[0])}-{int(100*QUANTILES[2])}%: {q[0]:.1f}-{q[2]:.1f})")
pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"wrote {os.path.relpath(OUT, REPO)}")
