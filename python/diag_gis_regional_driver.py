#!/usr/bin/env python3
"""
diag_gis_regional_driver.py — does the GIS component need the Option-D
(regional-driver) fix that D0 validated for glaciers?

GIS scales with the GMST input alone (mimibrick-quirks #10), and the B1
extA108 hindcast shows GIS undershooting mid-century (1950-1993 bias -0.68 cm,
band coverage 0.00). Greenland sits at the center of the ETCW. Test: does the
observed GIS melt-rate history (Frederikse GIS target) follow Greenland-region
observed temperature (r05 of t_glac_regions_hadcrut5.csv) better than GMST?

Method: 11-yr running means of (a) the GIS target's annual flow (cm/yr) and
(b) candidate drivers r05 / HadCRUT5-global, 1900-2018; Pearson r on the
smoothed series + the ETCW-window excess. Diagnostic only — no refit.

Outputs: figures/diag_gis_regional_driver.png, console numbers.
"""
import os
import subprocess

import numpy as np
import pandas as pd

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
TREG = os.path.join(REPO, "data/observations/t_glac_regions_hadcrut5.csv")
TGLAC = os.path.join(REPO, "data/observations/t_glac_hadcrut5.csv")
OUT_FIG = os.path.join(REPO, "figures/diag_gis_regional_driver.png")

SMOOTH = 11
WIN = (1900, 2018)            # Frederikse-era GIS target
ETCW_WIN = (1920, 1945)       # Greenland ETCW is usually dated ~1920-1945
COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

tg = pd.read_csv(TARGETS).set_index("year")
reg = pd.read_csv(TREG).set_index("year")
glob = pd.read_csv(TGLAC).set_index("year")["gmst_hadcrut5_C"]

gis = tg["gis"].dropna()
flow = gis.diff()                                  # cm/yr melt rate
sm = lambda s: s.rolling(SMOOTH, center=True).mean()

idx = np.arange(WIN[0], WIN[1] + 1)
f = sm(flow).reindex(idx)
r05 = sm(reg["r05"]).reindex(idx)
gl = sm(glob).reindex(idx)

ok = f.notna() & r05.notna() & gl.notna()
r_r05 = np.corrcoef(f[ok], r05[ok])[0, 1]
r_gl = np.corrcoef(f[ok], gl[ok])[0, 1]

sel = (reg.index >= ETCW_WIN[0]) & (reg.index <= ETCW_WIN[1])
selg = (glob.index >= ETCW_WIN[0]) & (glob.index <= ETCW_WIN[1])
etcw_r05 = reg.loc[sel, "r05"].mean()
etcw_gl = glob[selg].mean()

# mid-century cooling: Greenland 1940-1990 trend vs global
t4090 = np.arange(1940, 1991)
tr = np.polyfit(t4090, reg["r05"].reindex(t4090), 1)[0] * 100
trg = np.polyfit(t4090, glob.reindex(t4090), 1)[0] * 100

print(f"diag_gis_regional_driver | commit={COMMIT} | smooth={SMOOTH}yr window={WIN}")
print(f"  corr(GIS melt rate, T) 11-yr smoothed: r05 Greenland {r_r05:+.3f}  vs global {r_gl:+.3f}")
print(f"  ETCW {ETCW_WIN}: r05 {etcw_r05:+.2f} C vs global {etcw_gl:+.2f} C rel 1850-1900 "
      f"({etcw_r05/etcw_gl:.1f}x)")
print(f"  1940-1990 trend: r05 {tr:+.2f} C/century vs global {trg:+.2f} C/century")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True, constrained_layout=True)
ax1.plot(reg.index, sm(reg["r05"]), color="tab:red", label="r05 Greenland periphery (11-yr)")
ax1.plot(glob.index, sm(glob), color="0.3", label="HadCRUT5 global (11-yr)")
ax1.axvspan(*ETCW_WIN, color="tab:blue", alpha=0.10, label=f"ETCW {ETCW_WIN[0]}-{ETCW_WIN[1]}")
ax1.axhline(0, color="k", lw=0.6)
ax1.set(ylabel="anomaly rel 1850-1900 (C)",
        title="Greenland-region vs global temperature — the driver the GIS component never sees")
ax1.legend(fontsize=8)

ax2.plot(idx, f, color="tab:green", label=f"GIS target melt rate (11-yr, cm/yr)")
ax2b = ax2.twinx()
ax2b.plot(idx, r05, color="tab:red", lw=1, alpha=0.7)
ax2b.plot(idx, gl, color="0.3", lw=1, alpha=0.7)
ax2b.set_ylabel("T anomaly (C)")
ax2.axvspan(*ETCW_WIN, color="tab:blue", alpha=0.10)
ax2.set(xlabel="year", ylabel="cm/yr",
        title=f"GIS melt rate vs drivers: corr r05 {r_r05:+.2f} / global {r_gl:+.2f}")
ax2.legend(fontsize=8, loc="upper left")
ax2.set_xlim(1895, 2020)
fig.suptitle(f"GIS regional-driver diagnostic (Option-D analog) | commit {COMMIT}", fontsize=10)
fig.savefig(OUT_FIG, dpi=150)
print(f"  wrote {os.path.relpath(OUT_FIG, REPO)}")
