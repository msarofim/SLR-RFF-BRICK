#!/usr/bin/env python3
"""
B2 figure — BRICK-AM (extA108) vs FACTS n200 vs AR6 Ch9 Table 9.9, per component.

Six panels (glaciers, GIS, AIS, TE, LWS, total) at YEAR_PANEL; per scenario:
  * BRICK-AM median + 17-83% (parameter-only band, mean forcing),
  * each FACTS module median + 17-83% (includes FACTS's climate-ensemble spread),
  * AR6 WG1 Table 9.9 median + likely range (medium confidence), rel 1995-2014.
Baselines: BRICK rel 1995-2014, FACTS rel baseyear 2005, AR6 rel 1995-2014 — comparable.

Usage: python3 plot_b2_component_comparison.py [year]   (default 2100; 2150 has no AR6
component rows and no emulandice modules)
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
BRICK_CSV = os.path.join(REPO, "outputs/ssps_components_2300_extA108.csv")
FACTS_CSV = os.path.join(REPO, "outputs/facts_components_n200.csv")
YEAR_PANEL = int(sys.argv[1]) if len(sys.argv) > 1 else 2100
OUT_FIG = os.path.join(REPO, f"figures/b2_component_comparison_{YEAR_PANEL}.png")

SSPS = ["ssp126", "ssp245", "ssp585"]
SSP_LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
COMPS = [("glaciers", "Glaciers"), ("gis", "Greenland"), ("ais", "Antarctica"),
         ("te", "Thermal expansion"), ("lws", "Land water storage"), ("total", "TOTAL GMSL")]

# AR6 WG1 Ch9 Table 9.9 (Fox-Kemper 2021, p.1302): median (17-83%), m rel 1995-2014, @2100.
# 2150: totals only. Verified from the chapter PDF 2026-08-05.
AR6_2100 = {
    "te":       {"ssp126": (14, 11, 18), "ssp245": (20, 16, 24), "ssp585": (30, 24, 36)},
    "gis":      {"ssp126": (6, 1, 10),   "ssp245": (8, 4, 13),   "ssp585": (13, 9, 18)},
    "ais":      {"ssp126": (11, 3, 27),  "ssp245": (11, 3, 29),  "ssp585": (12, 3, 34)},
    "glaciers": {"ssp126": (9, 7, 11),   "ssp245": (12, 10, 15), "ssp585": (18, 15, 21)},
    "lws":      {"ssp126": (3, 1, 4),    "ssp245": (3, 1, 4),    "ssp585": (3, 1, 4)},
    "total":    {"ssp126": (44, 32, 62), "ssp245": (56, 44, 76), "ssp585": (77, 63, 101)},
}
AR6_2150 = {"total": {"ssp126": (68, 46, 99), "ssp245": (92, 66, 133), "ssp585": (132, 98, 188)}}
AR6 = AR6_2100 if YEAR_PANEL == 2100 else (AR6_2150 if YEAR_PANEL == 2150 else {})

brick = pd.read_csv(BRICK_CSV)
facts = pd.read_csv(FACTS_CSV)

fig, axes = plt.subplots(2, 3, figsize=(13, 8), constrained_layout=True)
for ax, (comp, title) in zip(axes.flat, COMPS):
    for i, ssp in enumerate(SSPS):
        # BRICK-AM
        b = brick[(brick.ssp == SSP_LABEL[ssp]) & (brick.component == comp) & (brick.year == YEAR_PANEL)]
        if len(b):
            r = b.iloc[0]
            ax.errorbar(i - 0.25, r.med, yerr=[[r.med - r.p17], [r.p83 - r.med]],
                        fmt="s", color="tab:red", ms=7, capsize=4, lw=2,
                        label="BRICK-AM extA108" if (i == 0 and comp == "glaciers") else None)
        # FACTS modules
        f = facts[(facts.scenario == ssp) & (facts.component == comp) & (facts.year == YEAR_PANEL)]
        for k, (_, r) in enumerate(f.iterrows()):
            ax.errorbar(i + 0.02 + 0.07 * k, r.med, yerr=[[r.med - r.p17], [r.p83 - r.med]],
                        fmt="o", color="tab:blue", ms=4, capsize=2, alpha=0.7, lw=1,
                        label="FACTS n200 modules" if (i == 0 and k == 0 and comp == "glaciers") else None)
        # AR6
        if comp in AR6 and ssp in AR6[comp]:
            m, lo, hi = AR6[comp][ssp]
            ax.errorbar(i + 0.32, m, yerr=[[m - lo], [hi - m]],
                        fmt="D", color="k", ms=6, capsize=4, lw=1.5,
                        label="AR6 Table 9.9" if (i == 0 and comp == "glaciers") else None)
    ax.set_xticks(range(len(SSPS)), [SSP_LABEL[s] for s in SSPS])
    ax.set_title(title)
    ax.set_ylabel("cm rel ~2005" if ax in axes[:, 0] else "")
    ax.grid(axis="y", alpha=0.3)
axes.flat[0].legend(fontsize=8, loc="upper left")
fig.suptitle(f"BRICK-AM (extA108, parameter-only bands) vs FACTS n200 (incl. climate spread) "
             f"vs AR6 Ch9 — components @{YEAR_PANEL}\n"
             f"BRICK rel 1995-2014 mean forcing; FACTS rel baseyear 2005 internal FaIR-1.6.4; "
             f"AR6 rel 1995-2014 (medium confidence)", fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"wrote {os.path.relpath(OUT_FIG, REPO)}")
