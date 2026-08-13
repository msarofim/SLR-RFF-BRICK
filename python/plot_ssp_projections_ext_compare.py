#!/usr/bin/env python3
"""
A/B comparison of SSP-2100 GMSL projections: 2018-baseline vs post-2018-extended
BRICK-Mengel posteriors (both UNWEIGHTED, FaIR v1.4.5-forced, rel 1995-2014).

Shows that extending the calibration to capture the post-2020 Antarctic pause +
glacier acceleration + steric rise LOWERS GMSL@2100 by ~1-3cm (mostly via AIS),
while leaving the high-forcing overshoot vs AR6 essentially intact (MICI-driven).

Panel (a): dot-whisker p05/p50/p95 per SSP, baseline vs extended, with AR6 medians.
Panel (b): the Δ(extended - baseline) decomposed into total vs AIS component.

Inputs:  outputs/quarantine/20260813_pre_extc_mengel_vintage/proj_ssps_mengel_summary.csv (baseline)
         outputs/quarantine/20260813_pre_extc_mengel_vintage/proj_ssps_mengel_ext_summary.csv (extended)
Output:  outputs/ssp_projections_ext_compare.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
# The pre-extC BRICK-Mengel vintage was QUARANTINED 2026-08-13 (vintage difference,
# not a bug -- see outputs/quarantine/20260813_pre_extc_mengel_vintage/README.md). This script is a CROSS-VINTAGE comparison, so it
# legitimately reads the superseded files; it reads them from the quarantine.
B = pd.read_csv(os.path.join(REPO, "outputs/quarantine/20260813_pre_extc_mengel_vintage/proj_ssps_mengel_summary.csv")).set_index("ssp_label")
E = pd.read_csv(os.path.join(REPO, "outputs/quarantine/20260813_pre_extc_mengel_vintage/proj_ssps_mengel_ext_summary.csv")).set_index("ssp_label")
OUT = os.path.join(REPO, "outputs/ssp_projections_ext_compare.png")

# AR6 median GMSL @2100 rel 1995-2014 (cm), medium-confidence (handoff table)
AR6 = {"SSP1-1.9": 38, "SSP1-2.6": 44, "SSP2-4.5": 56, "SSP3-7.0": 68, "SSP5-8.5": 77}
order = ["SSP1-1.9", "SSP1-2.6", "SSP2-4.5", "SSP4-6.0", "SSP3-7.0", "SSP5-8.5"]
x = np.arange(len(order))

fig, ax = plt.subplots(1, 2, figsize=(14, 5.4), gridspec_kw={"width_ratios": [1.6, 1]})

# (a) dot-whisker baseline vs extended
for i, s in enumerate(order):
    for src, df, off, col, lab in [("base", B, -0.13, "0.5", "2018-baseline"),
                                    ("ext", E, +0.13, "#1763b8", "post-2018-extended")]:
        r = df.loc[s]
        ax[0].plot([i+off, i+off], [r.p05, r.p95], color=col, lw=2, solid_capstyle="round")
        ax[0].plot(i+off, r.p50, "o", color=col, ms=7, label=(lab if i == 0 else None))
    if s in AR6:
        ax[0].plot(i, AR6[s], "D", color="#c0392b", ms=7, label=("AR6 median" if i == 2 else None))
ax[0].set_xticks(x); ax[0].set_xticklabels(order, rotation=20, fontsize=9)
ax[0].set_ylabel("GMSL @2100 (cm, rel 1995-2014)")
ax[0].set_title("(a) SSP-2100 GMSL: baseline vs extended (whisker = 5–95%)")
ax[0].legend(fontsize=9, loc="upper left"); ax[0].grid(alpha=0.3, axis="y")

# (b) delta decomposition
dtot = [E.loc[s, "p50"] - B.loc[s, "p50"] for s in order]
dais = [E.loc[s, "ais"] - B.loc[s, "ais"] for s in order]
ax[1].bar(x - 0.18, dtot, 0.36, color="#1763b8", label="Δ total p50")
ax[1].bar(x + 0.18, dais, 0.36, color="#0f9b6c", label="Δ AIS median")
ax[1].axhline(0, color="k", lw=0.6)
ax[1].set_xticks(x); ax[1].set_xticklabels(order, rotation=20, fontsize=9)
ax[1].set_ylabel("extended − baseline (cm)")
ax[1].set_title("(b) Extension effect @2100\n(post-2020 pause → lower AIS)")
ax[1].legend(fontsize=9); ax[1].grid(alpha=0.3, axis="y")

fig.suptitle("Effect of extending the BRICK-Mengel calibration past 2018 (GRACE-FO/GlaMBIE/NOAA) on SSP-2100 GMSL\n"
             "Extension lowers 2100 GMSL ~1–3 cm, almost entirely via AIS; high-forcing overshoot vs AR6 persists "
             "(MICI-threshold-driven, unconstrained by 7 yr)", fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.92])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
