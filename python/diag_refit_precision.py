#!/usr/bin/env python3
"""diag_refit_precision.py -- how far apart do near-identical refits land? (2026-09-20, for the paper's
STATED precision of the Antarctic projection medians; handoff_2026-09-20b §3.)

For each tag: (1) the Antarctic block's per-chain and pooled 2nd-half medians, in units of the REFERENCE
tag's pooled posterior sd, so a move can be read against the posterior width; (2) the full-window hindcast
RMSE of the posterior-predictive median against the bare targets, per component (the one-axis gate);
(3) the fixed-climate SSP component medians and 5-95 % at 2100 / 2300 (AIS and total), from
ssps_components_2300_<tag>_<tap>.csv. Then the pairwise spread across the tags that share an objective,
which IS the between-refit precision. Nothing here is a verdict: the table is what the paper quotes.

  python3 python/diag_refit_precision.py --tags=L26,L27,L27r,L27b --ref=L26
Writes outputs/diag_refit_precision_<tags>.csv (long) and prints the tables.
"""
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import stamp

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs")
MCMC = os.path.join(OUT, "mcmc")
TAGS = next((a[7:] for a in sys.argv[1:] if a.startswith("--tags=")), "L26,L27").split(",")
REF = next((a[6:] for a in sys.argv[1:] if a.startswith("--ref=")), TAGS[0])
TAP = "tap4p69K_V5p64m_tau800_n2_ws"
## The Antarctic block as sampled from L26 on (the 09-20 per-chain diagnostic's set; lambda/T_crit/gamma
## are absent from L27-family chains and are skipped where missing).
AIS_COLS = ["ais_ocean_temperature₀", "antarctic_alpha", "antarctic_nu", "anto_alpha", "anto_beta",
            "ais_mu", "ais_bedheight0", "ais_slope", "ais_iceflow0", "ais_precip_u", "ais_runoff_Ton", "ais_c",
            "ais_gmst_amp", "antarctic_lambda", "antarctic_temp_threshold", "antarctic_gamma"]
COMP = {"glaciers": ("glaciers_p50", "glaciers_obs"), "ais": ("ais_p50", "ais_obs"), "gis": ("gis_p50", "gis_obs"),
        "te": ("te_p50", "te_obs"), "total": ("total_p50", "total_obs")}
SSP_CELLS = [("SSP2-4.5", "ais", 2100), ("SSP2-4.5", "ais", 2300), ("SSP5-8.5", "ais", 2100), ("SSP5-8.5", "ais", 2300),
             ("SSP1-2.6", "ais", 2300), ("SSP2-4.5", "total", 2100), ("SSP2-4.5", "total", 2300)]

rows = []

## 1. the Antarctic block, per chain -----------------------------------------------------------------
def chain_files(tag):
    return sorted(glob.glob(os.path.join(MCMC, f"chain_{tag}_seed*_n2000000.csv")))

def chain_cols(path):
    return list(pd.read_csv(path, nrows=0).columns)

med = {}   # (tag, seed) -> Series of medians ; ("pooled", tag) -> medians ; ("sd", tag) -> sd
draws_by_tag = {}
for tag in TAGS:
    fs = chain_files(tag)
    if not fs:
        print(f"[{tag}] no chains found — skipped"); continue
    cols = [c for c in AIS_COLS if c in chain_cols(fs[0])]
    parts = []
    for f in fs:
        seed = re.search(r"_seed(\d+)_", f).group(1)
        d = pd.read_csv(f, usecols=cols)
        d = d.iloc[len(d) // 2:]
        med[(tag, seed)] = d.median()
        parts.append(d.iloc[::50])                       # thinned pooled draws for sd / pooled median
        print(f"[{tag}] seed{seed}: {len(d)} 2nd-half draws, {len(cols)} AIS columns")
    pooled = pd.concat(parts)
    med[("pooled", tag)] = pooled.median(); med[("sd", tag)] = pooled.std()
    draws_by_tag[tag] = pooled

ref_sd = med[("sd", REF)]; ref_med = med[("pooled", REF)]
print(f"\n=== ANTARCTIC BLOCK: 2nd-half medians in {REF}-sd units (pooled median of {REF} = 0) ===")
tags_ok = [t for t in TAGS if ("pooled", t) in med]
hdr = "%-26s" % "parameter" + "".join("%12s" % t for t in tags_ok) + "   per-chain range (max over tags)"
print(hdr)
for p in AIS_COLS:
    if p not in ref_sd.index or not np.isfinite(ref_sd[p]) or ref_sd[p] == 0:
        continue
    line = "%-26s" % p; rng = []
    for t in tags_ok:
        v = (med[("pooled", t)].get(p, np.nan) - ref_med[p]) / ref_sd[p]
        line += "%12s" % ("%+.2f" % v if np.isfinite(v) else "—")
        per = [(med[(t, s)][p] - ref_med[p]) / ref_sd[p] for (tt, s) in med if tt == t and p in med[(t, s)].index]
        if per:
            rng.append(max(per) - min(per))
        rows.append(dict(block="ais_geometry", tag=t, quantity=p, value=v, unit=f"{REF}-sd",
                         per_chain=";".join("%.2f" % x for x in per)))
    print(line + "   %.2f" % max(rng) if rng else line)

## 2. hindcast RMSE (full window, postpred median vs bare targets) ------------------------------------
print("\n=== HINDCAST RMSE, full window, cm (postpred p50 vs target) ===")
print("%-8s" % "comp" + "".join("%10s" % t for t in tags_ok))
for comp, (pc, oc) in COMP.items():
    line = "%-8s" % comp
    for t in tags_ok:
        f = os.path.join(OUT, f"postpred_{t}_components_timeseries.csv")
        if not os.path.exists(f):
            line += "%10s" % "—"; continue
        d = pd.read_csv(f).set_index("year")
        r = (d[pc] - d[oc]).loc[1900:2026].dropna()
        v = float(np.sqrt((r ** 2).mean()))
        line += "%10.3f" % v
        rows.append(dict(block="hindcast_rmse", tag=t, quantity=comp, value=v, unit="cm", per_chain=""))
    print(line)

## 3. fixed-climate projections --------------------------------------------------------------------
print("\n=== FIXED-CLIMATE SSP COMPONENTS (tap), median [5-95], cm rel. 1995-2014 ===")
print("%-22s" % "cell" + "".join("%24s" % t for t in tags_ok))
for ssp, comp, yr in SSP_CELLS:
    line = "%-22s" % f"{ssp} {comp} {yr}"
    for t in tags_ok:
        f = os.path.join(OUT, f"ssps_components_2300_{t}_{TAP}.csv")
        if not os.path.exists(f):
            line += "%24s" % "—"; continue
        d = pd.read_csv(f)
        c = d[(d.ssp == ssp) & (d.component == comp) & (d.year == yr)]
        if c.empty:
            line += "%24s" % "—"; continue
        m, lo, hi = float(c.med.iloc[0]), float(c.p05.iloc[0]), float(c.p95.iloc[0])
        line += "%24s" % ("%.1f [%.0f, %.0f]" % (m, lo, hi))
        rows.append(dict(block="ssp_fixed", tag=t, quantity=f"{ssp}|{comp}|{yr}|med", value=m, unit="cm", per_chain=""))
        rows.append(dict(block="ssp_fixed", tag=t, quantity=f"{ssp}|{comp}|{yr}|p95", value=hi, unit="cm", per_chain=""))
    print(line)

## 4. between-refit spread on the same objective ---------------------------------------------------
same = [t for t in tags_ok if t in ("L27", "L27r")]
if len(same) == 2:
    print("\n=== BETWEEN-REFIT SPREAD, L27 vs L27r (same objective, new seeds/starts/covariance) ===")
    R = pd.DataFrame(rows)
    for blk in ("ssp_fixed", "hindcast_rmse"):
        a = R[(R.block == blk) & (R.tag == "L27")].set_index("quantity").value
        b = R[(R.block == blk) & (R.tag == "L27r")].set_index("quantity").value
        for q in a.index:
            if q in b.index:
                print("  %-28s L27 %8.2f  L27r %8.2f  diff %+7.2f" % (q, a[q], b[q], b[q] - a[q]))
    g = R[(R.block == "ais_geometry")]
    a = g[g.tag == "L27"].set_index("quantity").value; b = g[g.tag == "L27r"].set_index("quantity").value
    dd = (b - a).dropna()
    print("  AIS geometry |L27r − L27| in %s-sd: max %.2f (%s), median %.2f" % (REF, dd.abs().max(), dd.abs().idxmax(), dd.abs().median()))

out = os.path.join(OUT, "diag_refit_precision_%s.csv" % "_".join(tags_ok))
stamp(pd.DataFrame(rows), __file__, tag="+".join(tags_ok),
      inputs={t: f"chain_{t}_seed*_n2000000.csv; postpred_{t}; ssps_components_2300_{t}_{TAP}" for t in tags_ok},
      extra=f"AIS medians in {REF}-sd units (pooled 2nd-half); RMSE full window vs bare targets; fixed-climate tap cells").to_csv(out, index=False)
print(f"\nwrote {os.path.relpath(out, REPO)}")
