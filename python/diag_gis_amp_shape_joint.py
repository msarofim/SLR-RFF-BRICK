#!/usr/bin/env python3
"""Greenland amplification SHAPE on the JOINT arm: shipped (warming-dependent) vs shape-constant.

GMD draft, Greenland 'Amplification' paragraph (Marcus 2026-09-30: put it on the joint arm, like the
above-threshold channel paragraph). Reads the per-draw files of the shipped joint arm and of the run
with LADRILLO_GIS_SHAPE=gis_amp_shape_const (julia/scope_slr_fair_uncertainty.jl --tag=L27 --ssp=<s>
--tap; the shape is in the filename and provenance since 2026-09-30). Draw->config pairing is a fixed
stride, so the difference is taken DRAW BY DRAW; the paired median is the number to quote, the
difference of medians is written beside it.

  python3 python/diag_gis_amp_shape_joint.py            # writes outputs/diag_gis_amp_shape_joint_L27.csv
"""
import os, subprocess
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEM = "L27_tap4p69K_V5p64m_tau800"
SSPS = ("ssp126", "ssp245", "ssp585")
OUT = os.path.join(REPO, "outputs/diag_gis_amp_shape_joint_L27.csv")
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

rows = []
for s in SSPS:
    f0 = os.path.join(REPO, f"outputs/scope_slr_fairunc_draws_{s}_spliced_{STEM}.csv")
    f1 = os.path.join(REPO, f"outputs/scope_slr_fairunc_draws_{s}_spliced_{STEM}_gis_amp_shape_const.csv")
    a, b = pd.read_csv(f0), pd.read_csv(f1)
    m = a.merge(b, on=["draw", "config", "component", "horizon", "arm"], suffixes=("_ship", "_const"))
    assert len(m) == len(a) == len(b), "draw sets differ -- not a paired comparison"
    for arm in ("joint", "fixed"):
        for comp in ("gis", "total"):
            for h in (2100, 2300):
                x = m[(m.arm == arm) & (m.component == comp) & (m.horizon == h)]
                dlt = x.value_cm_const - x.value_cm_ship
                rows.append(dict(ssp=s, arm=arm, component=comp, horizon=h, n=len(x),
                                 ship_median_cm=x.value_cm_ship.median(), const_median_cm=x.value_cm_const.median(),
                                 diff_of_medians_cm=x.value_cm_const.median() - x.value_cm_ship.median(),
                                 paired_median_cm=dlt.median(), paired_p05_cm=dlt.quantile(.05),
                                 paired_p95_cm=dlt.quantile(.95)))
out = pd.DataFrame(rows)
out["provenance"] = (f"diag_gis_amp_shape_joint.py | commit {commit} | Ladrillo L27 tapped ({STEM}) | spliced forcing | "
                     f"shape-constant (LADRILLO_GIS_SHAPE=gis_amp_shape_const) minus shipped, per draw | cm rel. 1995-2014 "
                     f"| seed n/a here (pairing seed of the driver, 2026)")
out.to_csv(OUT, index=False)
print(out[(out.component == "gis") & (out.horizon == 2300)][["ssp", "arm", "paired_median_cm", "paired_p05_cm",
                                                             "paired_p95_cm", "diff_of_medians_cm"]].round(2).to_string(index=False))
print("wrote", os.path.relpath(OUT, REPO))
