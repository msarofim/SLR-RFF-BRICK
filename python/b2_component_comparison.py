#!/usr/bin/env python3
"""
B2 — BRICK-AM (extA108) vs FACTS per-component comparison table.

Merges outputs/ssps_components_2300_extA108.csv (BRICK-AM, rel 1995-2014)
with outputs/facts_components_n200.csv (FACTS n200, rel baseyear 2005;
directly comparable per the MAGICC-comparison convention) and reports,
per scenario x component x horizon: BRICK median [17-83%] vs each FACTS
module's median [17-83%], plus the SSP1-2.6 -> SSP5-8.5 scenario SPREAD
per component (the saturation diagnostic that caught the glacier bug).

FACTS horizons: wf-f modules reach 2150, emulandice (wf-e) stops at 2100,
nothing reaches 2300 (AR6 Ch9 literature numbers cover that horizon).

Usage: python3 b2_component_comparison.py
Writes: outputs/b2_component_comparison.csv + console tables.
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
BRICK_CSV = os.path.join(REPO, "outputs/ssps_components_2300_extA108.csv")
FACTS_CSV = os.path.join(REPO, "outputs/facts_components_n200.csv")
OUT = os.path.join(REPO, "outputs/b2_component_comparison.csv")
HORIZONS = [2100, 2150]
SPREAD_LO, SPREAD_HI = "ssp126", "ssp585"
SSP_LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
# BRICK component name -> FACTS component name
CMAP = {"glaciers": "glaciers", "gis": "gis", "ais": "ais", "te": "te",
        "lws": "lws", "total": "total"}

brick = pd.read_csv(BRICK_CSV)
facts = pd.read_csv(FACTS_CSV)

rows = []
for ssp, label in SSP_LABEL.items():
    for comp_b, comp_f in CMAP.items():
        for y in HORIZONS:
            b = brick[(brick.ssp == label) & (brick.component == comp_b) & (brick.year == y)]
            if len(b):
                r = b.iloc[0]
                rows.append(dict(scenario=ssp, component=comp_b, model="BRICK-AM",
                                 module="extA108", year=y, med=r.med, p17=r.p17, p83=r.p83))
            f = facts[(facts.scenario == ssp) & (facts.component == comp_f) & (facts.year == y)]
            for _, r in f.iterrows():
                rows.append(dict(scenario=ssp, component=comp_b, model="FACTS",
                                 module=r.module, year=y, med=r.med, p17=r.p17, p83=r.p83))
df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)

have = sorted(set(df.scenario))
for y in HORIZONS:
    print(f"\n================ @{y} (cm; BRICK rel 1995-2014, FACTS rel 2005) ================")
    for comp in CMAP:
        sub = df[(df.component == comp) & (df.year == y)]
        if not len(sub):
            continue
        print(f"--- {comp} ---")
        mods = sub[["model", "module"]].drop_duplicates().values
        for model, module in mods:
            line = f"  {model:9s} {module:12s}"
            for ssp in have:
                r = sub[(sub.scenario == ssp) & (sub.model == model) & (sub.module == module)]
                line += (f"  {SSP_LABEL[ssp]}: {r.iloc[0].med:6.1f} [{r.iloc[0].p17:6.1f},{r.iloc[0].p83:6.1f}]"
                         if len(r) else f"  {SSP_LABEL[ssp]}: {'—':>22s}")
            print(line)

if SPREAD_LO in have and SPREAD_HI in have:
    print(f"\n================ scenario spread {SSP_LABEL[SPREAD_LO]} -> {SSP_LABEL[SPREAD_HI]} (cm, medians) ================")
    for y in HORIZONS:
        print(f"--- @{y} ---")
        for comp in CMAP:
            sub = df[(df.component == comp) & (df.year == y)]
            for model, module in sub[["model", "module"]].drop_duplicates().values:
                lo = sub[(sub.scenario == SPREAD_LO) & (sub.module == module)]
                hi = sub[(sub.scenario == SPREAD_HI) & (sub.module == module)]
                if len(lo) and len(hi):
                    print(f"  {comp:9s} {model:9s} {module:12s} {hi.iloc[0].med - lo.iloc[0].med:7.1f}")
else:
    print(f"\n(scenario spread needs {SPREAD_LO} and {SPREAD_HI}; have {have})")
print(f"\nwrote {os.path.relpath(OUT, REPO)}")
