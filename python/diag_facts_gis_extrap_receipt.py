#!/usr/bin/env python3
"""FACTS FittedISMIP Greenland past 2100: default rate extrapolation vs the fit evaluated through 2300 (GMD receipt).

GMD draft, model-comparison paragraph: "By default FACTS ... continues each sample at its 2080-2100 mean rate,
which gives a High-to-Low Greenland median of 47 cm at 2300. Evaluating the fit through 2300 instead gives
112 cm even though the climate cools." Those were measured on 09-12c from a scratch FACTS run that was not
kept; this script reads two committed-to-disk FACTS experiments and writes the receipt.

  default   facts/experiments/global.shared.vvHL2300.n200          (crateyear_end = 2100, FACTS default)
  fit2300   facts/experiments/global.shared.vvHL2300.n200.crate0   (copy, GrIS1f crateyear_end: 0, 2026-10-01)

Both arms share the climate input and FittedISMIP's default seed (1234), so the samples are paired; the script
asserts that they are identical through 2100, as they must be if the only difference is the post-2100 rule.
FACTS reports Greenland relative to its baseyear (2005), as in the draft's 47 / 112 cm.
GMST fall = per-sample peak minus 2300 of the shared FaIR GSAT driver, median over samples.

  python3 python/diag_facts_gis_extrap_receipt.py      # writes outputs/diag_facts_gis_extrap_receipt_vvHL2300.csv
"""
import hashlib, os, subprocess
import numpy as np
import xarray as xr
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = os.path.join(os.path.dirname(REPO), "facts")
SCEN = "vvHL2300"
ARMS = {"default": f"global.shared.{SCEN}.n200", "fit2300": f"global.shared.{SCEN}.n200.crate0"}
HORIZONS = (2100, 2300)
QUANTILES = (0.05, 0.50, 0.95)
OUT = os.path.join(REPO, f"outputs/diag_facts_gis_extrap_receipt_{SCEN}.csv")
md5 = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()[:8]
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

sl, paths = {}, {}
for arm, exp in ARMS.items():
    paths[arm] = os.path.join(FACTS, "experiments", exp, "output", f"{exp}.GrIS1f.FittedISMIP.GrIS_GIS_globalsl.nc")
    d = xr.open_dataset(paths[arm])
    assert d.attrs.get("scenario") == SCEN and int(d.attrs.get("baseyear")) == 2005, d.attrs
    v = d["sea_level_change"]
    assert v.attrs.get("units") == "mm", v.attrs
    sl[arm] = v.isel(locations=0) / 10.0                      # mm -> cm, dims (samples, years)
pre = sl["default"].years <= 2100
assert np.array_equal(sl["default"].sel(years=pre).values, sl["fit2300"].sel(years=pre).values), \
    "arms differ before 2100 -- not a paired post-2100 comparison"

gsat_path = os.path.join(FACTS, "experiments", ARMS["default"], "input", f"shared_{SCEN}_gsat.nc")
g = xr.open_dataset(gsat_path)["surface_temperature"].isel(locations=0).sel(years=slice(2000, 2300))
gmst_fall = float(np.median(g.max("years") - g.sel(years=2300)))

prov = (f"diag_facts_gis_extrap_receipt.py | FACTS FittedISMIP GrIS (GrIS1f), n=200, seed 1234 (module default) | "
        f"default {os.path.basename(paths['default'])} md5 {md5(paths['default'])} | fit2300 "
        f"{os.path.basename(paths['fit2300'])} md5 {md5(paths['fit2300'])} | climate {os.path.basename(gsat_path)} "
        f"md5 {md5(gsat_path)} (FaIR 2.2.4 calib 1.6.0) | cm relative to FACTS baseyear 2005 | commit {commit}")
rows = []
for arm in ARMS:
    for h in HORIZONS:
        q = np.quantile(sl[arm].sel(years=h).values, QUANTILES)
        rows.append(dict(scenario=SCEN, arm=arm, horizon=h, units="cm",
                         **{f"p{int(100*x):02d}": round(float(v), 2) for x, v in zip(QUANTILES, q)},
                         gmst_fall_peak_to_2300_K=round(gmst_fall, 2), provenance=prov))
        print(f"{arm:8s} {h}: median {q[1]:6.1f} cm  (5-95%: {q[0]:.1f}-{q[2]:.1f})")
print(f"GMST fall, peak -> 2300 (median over samples): {gmst_fall:.2f} K")
pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"wrote {os.path.relpath(OUT, REPO)}")
