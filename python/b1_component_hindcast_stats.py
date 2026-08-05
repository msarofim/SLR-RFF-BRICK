#!/usr/bin/env python3
"""
B1 — historical component-hindcast statistics for BRICK-AM (extA108).

Reads the existing posterior bands (outputs/component_hindcast_bands.csv,
diag_component_hindcast.jl on extA108, rebaselined 1995-2005) and the
calibration targets (outputs/recalib_targets_ext.csv: AIS/GIS Frederikse+
GRACE-FO, GSIC Frederikse+GlaMBIE, steric Frederikse+NOAA NCEI, total
Dangendorf+STAR), and reports per component:
  * mean bias (model p50 − obs) per window,
  * trend bias (OLS slope of p50 − OLS slope of obs) per window,
  * coverage: fraction of years where obs lies inside the model p5–p95 band.

Windows follow the handoff B1 spec: 1900–1950, 1950–1993, 1993–end.
Output: outputs/b1_component_hindcast_stats.csv + console table.
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
BANDS = os.path.join(REPO, "outputs/component_hindcast_bands.csv")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
OUT = os.path.join(REPO, "outputs/b1_component_hindcast_stats.csv")
MODEL = "BRICK-AM"
WINDOWS = [(1900, 1950), (1950, 1993), (1993, 2026)]
# bands component name -> targets column (model total is ice+steric only; obs dang total
# includes LWS, so add the targets' own LWS series to the model total for the comparison)
COMP_MAP = {"ais": "ais", "gis": "gis", "gsic": "gsic", "te": "steric", "total": "dang"}

bands = pd.read_csv(BANDS)
tg = pd.read_csv(TARGETS).set_index("year")

rows = []
for comp, tcol in COMP_MAP.items():
    b = bands[(bands.model == MODEL) & (bands.component == comp)].set_index("year")
    obs = tg[tcol].dropna()
    yrs = obs.index.intersection(b.index)
    obs = obs.loc[yrs]
    p50, p5, p95 = b.loc[yrs, "p50"].copy(), b.loc[yrs, "p5"].copy(), b.loc[yrs, "p95"].copy()
    if comp == "total":  # model bands are ice+steric; obs total includes LWS
        lws = tg.loc[yrs, "lws"]
        p50, p5, p95 = p50 + lws, p5 + lws, p95 + lws
    cover_all = ((obs >= p5) & (obs <= p95)).mean()
    for (w0, w1) in WINDOWS:
        wy = yrs[(yrs >= w0) & (yrs <= w1)]
        if len(wy) < 5:
            continue
        o, m = obs.loc[wy], p50.loc[wy]
        slope = lambda s: np.polyfit(wy, s, 1)[0] * 10  # cm/decade
        rows.append(dict(component=comp, window=f"{w0}-{w1}", n=len(wy),
                         bias_cm=(m - o).mean(),
                         trend_bias_cm_per_dec=slope(m) - slope(o),
                         obs_trend_cm_per_dec=slope(o),
                         coverage_p5p95=((o >= p5.loc[wy]) & (o <= p95.loc[wy])).mean(),
                         coverage_full=cover_all))

df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)
print(f"B1 hindcast stats | bands={os.path.basename(BANDS)} ({MODEL}) | targets={os.path.basename(TARGETS)}")
print(f"\n{'comp':6s} {'window':10s} {'bias':>7s} {'trendbias':>10s} {'obstrend':>9s} {'cov(win)':>9s} {'cov(all)':>9s}")
print(f"{'':6s} {'':10s} {'(cm)':>7s} {'(cm/dec)':>10s} {'(cm/dec)':>9s} {'':>9s} {'':>9s}")
for _, r in df.iterrows():
    print(f"{r.component:6s} {r.window:10s} {r.bias_cm:7.2f} {r.trend_bias_cm_per_dec:10.3f} "
          f"{r.obs_trend_cm_per_dec:9.3f} {r.coverage_p5p95:9.2f} {r.coverage_full:9.2f}")
print(f"\nwrote {os.path.relpath(OUT, REPO)}")
