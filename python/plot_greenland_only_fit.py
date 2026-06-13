#!/usr/bin/env python3
"""
plot_greenland_only_fit.py — CANDIDATE-1 diagnostic (handoff_2026-06-13 §4.1).

Visualizes the GIS-only best fit of the SIMPLE/Bakker Greenland module (widened
bounds, GIS alone, no competition from other components) against the extended
GIS target. Two panels:
  (top)    cumulative GIS (cm SLE, de-meaned 1995-2005): obs+band vs best-fit model
  (bottom) decadal melt RATE (cm/decade): obs vs model, with GMST overlaid

The structural question is whether SIMPLE can delay the melt resumption to the
observed ~2000 while keeping the ~1920s-40s early-century melt. The reference
lines mark the ~1970 GMST warming resumption and the ~2000 observed GIS melt
resumption — the ~30 yr gap the module must reproduce.
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CSV  = REPO / "outputs/greenland_only_fit_ext.csv"
PNG  = REPO / "outputs/greenland_only_fit_ext.png"

# ---- labels from named constants (filter/window/baseline must match the data) ----
BASELINE   = "1995–2005"
WARM_RESUME = 1970   # GMST warming resumption
MELT_RESUME = 2000   # observed GIS melt resumption
TITLE = ("Candidate-1 test: SIMPLE/Bakker Greenland, GIS-only best fit "
         "(widened bounds)\nCan one linear-equilibrium + single-τ relaxation "
         f"delay melt resumption to ~{MELT_RESUME}?")

d = pd.read_csv(CSV)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), sharex=True,
                               gridspec_kw=dict(height_ratios=[1.1, 1.0]))

# ---- panel 1: cumulative GIS ----
ax1.fill_between(d.year, d.gis_lo, d.gis_hi, color="0.8",
                 label="obs 90% band (Frederikse 1900–2018 + GRACE-FO →2025)")
ax1.plot(d.year, d.gis_obs, color="k", lw=2, label="observed GIS")
ax1.plot(d.year, d.gis_model, color="C3", lw=2, ls="--", label="SIMPLE best fit (GIS-only)")
ax1.axvline(MELT_RESUME, color="C0", ls=":", lw=1.2)
ax1.set_ylabel(f"GIS sea-level contribution\n(cm SLE, rel {BASELINE})")
ax1.set_title(TITLE, fontsize=10)
ax1.legend(fontsize=8, loc="upper left")
ax1.grid(alpha=0.3)

# ---- panel 2: decadal melt rate + GMST overlay ----
ax2.plot(d.year, d.obs_rate_cm_dec, color="k", lw=2, label="observed melt rate")
ax2.plot(d.year, d.model_rate_cm_dec, color="C3", lw=2, ls="--", label="SIMPLE best fit melt rate")
ax2.axvline(WARM_RESUME, color="C1", ls=":", lw=1.2)
ax2.axvline(MELT_RESUME, color="C0", ls=":", lw=1.2)
ax2.text(WARM_RESUME, ax2.get_ylim()[1], f" GMST warming\n resumes ~{WARM_RESUME}",
         color="C1", fontsize=7.5, va="top", ha="left")
ax2.text(MELT_RESUME, ax2.get_ylim()[1], f" obs melt\n resumes ~{MELT_RESUME}",
         color="C0", fontsize=7.5, va="top", ha="left")
ax2.set_ylabel("GIS melt rate\n(cm SLE / decade)")
ax2.set_xlabel("year")
ax2.grid(alpha=0.3)
axT = ax2.twinx()
axT.plot(d.year, d.gmst, color="C2", lw=1.2, alpha=0.7, label="FaIR-mean GMST")
axT.set_ylabel("GMST (°C)", color="C2")
axT.tick_params(axis="y", labelcolor="C2")
l1, lab1 = ax2.get_legend_handles_labels(); l2, lab2 = axT.get_legend_handles_labels()
ax2.legend(l1 + l2, lab1 + lab2, fontsize=8, loc="upper left")

ax2.set_xlim(1900, d.year.max())
fig.tight_layout()
fig.savefig(PNG, dpi=150, bbox_inches="tight")
print(f"wrote {PNG}")
