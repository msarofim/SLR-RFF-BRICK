#!/usr/bin/env python3
"""DOES THE GLACIER-BLOCK AMPLIFICATION HOLD INTO THE FUTURE? CMIP6 ssp245, per block.

THE QUESTION (Marcus 2026-09-13). The R19 (Antarctic periphery) amplification prior N(0.72, 0.15)
is centred on the HadCRUT5/GISTEMP historical fit (0.61/0.58; Berkeley 0.85), and CMIP6's
historical median is 0.87. If the Southern Ocean's low ratio is a DELAY (Armour et al. 2016), the
ratio should rise toward 1 over the 21st century, and a fixed historical amp under-warms R19 in
projection. This measures the ssp245 amplification per model on the FUTURE window alone and on
the full run, for all three blocks, against the historical value the offset diagnostic
(diag_glac_amp_cmip6_offset.py) already reports. Same secant estimator (through-origin on anomalies), same models
(data/cmip6_glac, reduce_cmip6_tas_glac.py), historical + ssp245 concatenated.

WRITES outputs/diag_glac_amp_cmip6_future.csv (stamped)
  python3 python/diag_glac_amp_cmip6_future.py
"""
import glob
import os
import subprocess
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
CMIP_DIR = "data/cmip6_glac"
OUT = "outputs/diag_glac_amp_cmip6_future.csv"
BLOCKS = ["R19", "SLOWP", "FAST"]
BASELINE = (1995, 2014)          # the projection frame; the splice matches the obs driver's last 11 yr
WINDOWS = {"historical 1901-2024": (1901, 2024),
           "future 2025-2100": (2025, 2100),
           "late 2070-2100": (2070, 2100),
           "full 1901-2100": (1901, 2100)}
# (mu, sigma) per block; MIRRORS julia/calibrate_mcmc_ext.jl AMP_PRIOR (its first two entries,
# verified 2026-09-14). Stamped into the CSV as prior_mu/prior_sd -- keep the two in step by hand.
PRIOR = {"R19": (0.72, 0.15), "SLOWP": (2.50, 0.45), "FAST": (1.45, 0.15)}


def secant(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    return float((x[ok] * y[ok]).sum() / (x[ok] ** 2).sum()) if ok.sum() >= 20 else np.nan


def main():
    cm = {}
    for f in sorted(glob.glob(os.path.join(CMIP_DIR, "tas_series_glac_*.csv"))):
        d = pd.read_csv(f)
        d = d[d.scenario.isin(("historical", "ssp245"))].drop_duplicates("year").set_index("year")
        if d.index.min() > 1850 or d.index.max() < 2099:
            continue
        cm[os.path.basename(f)[len("tas_series_glac_"):-4]] = d
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    prov = (f"diag_glac_amp_cmip6_future.py | seed n/a (no RNG) | {len(cm)} CMIP6 models, historical+ssp245, "
            f"data/cmip6_glac | secant through origin on anomalies rel {BASELINE[0]}-{BASELINE[1]} | commit {commit}")
    rows = []
    for b in BLOCKS:
        for wn, (y0, y1) in WINDOWS.items():
            a = []
            for name, d in cm.items():
                g = d.tas_global - d.tas_global.loc[BASELINE[0]:BASELINE[1]].mean()
                z = d[f"tas_{b}"] - d[f"tas_{b}"].loc[BASELINE[0]:BASELINE[1]].mean()
                m = (d.index >= y0) & (d.index <= y1)
                a.append(secant(g.to_numpy(float)[m], z.to_numpy(float)[m]))
            a = np.array(a)
            rows.append(dict(block=b, window=wn, cmip6_median=np.nanmedian(a),
                             cmip6_p05=np.nanpercentile(a, 5), cmip6_p95=np.nanpercentile(a, 95),
                             n_models=int(np.isfinite(a).sum()), prior_mu=PRIOR[b][0], prior_sd=PRIOR[b][1],
                             provenance=prov))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"diag_glac_amp_cmip6_future — {len(cm)} models, anomalies rel {BASELINE[0]}-{BASELINE[1]}\n")
    for b in BLOCKS:
        print(f"=== {b}  (prior N({PRIOR[b][0]}, {PRIOR[b][1]})) ===")
        for _, r in out[out.block == b].iterrows():
            print(f"  {r.window:22} median {r.cmip6_median:5.2f}   p05-p95 {r.cmip6_p05:4.2f}-{r.cmip6_p95:4.2f}   n={r.n_models}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
