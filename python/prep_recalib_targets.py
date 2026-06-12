#!/usr/bin/env python3
"""
Prep historical recalibration targets for the quick central BRICK recalibration.

Targets (all re-referenced to a common 1995-2005 window mean, converted mm -> cm):
  - Frederikse 2020 component series: Antarctic Ice Sheet, Glaciers (GSIC),
    Steric (TE), Terrestrial Water Storage (the LWS budget term).
  - Dangendorf 2024 total GMSL.

Why a common multi-year window (1995-2005, 11 yr) and not year-2000 alone: noisy
series must never be baselined to a single year (project convention). Frederikse
is internally rel-2000 and Dangendorf is on a centred-20th-c baseline; re-referencing
both (and later the BRICK output) to the SAME window mean makes them comparable.

Output: outputs/recalib_targets.csv with, per year 1900-2018:
  year, ais/gsic/steric/lws/dang  (mean, cm rel window) + _lo/_hi 90% band cols
  + dang_sig (cm).
Per-target objective sigma is taken at 1900 (the wide, informative anchor; the
Frederikse band collapses near 2000) and written to outputs/recalib_target_sigmas.csv.
"""
import os
import numpy as np
import pandas as pd

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
FRED = os.path.join(REPO, "data/observations/raw/frederikse2020_global_basin_timeseries.xlsx")
DANG = os.path.join(REPO, "data/observations/dangendorf_2024_gmsl.csv")
OUT_CSV = os.path.join(REPO, "outputs/recalib_targets.csv")
OUT_SIG = os.path.join(REPO, "outputs/recalib_target_sigmas.csv")

BASE_Y0, BASE_Y1 = 1995, 2005     # common re-reference window (11 yr)
FIT_Y0, FIT_Y1   = 1900, 2018     # fitting window
ANCHOR = 1900                     # year at which per-target objective sigma is set

# Frederikse column -> output target name
FRED_MAP = {
    "Antarctic Ice Sheet": "ais",
    "Glaciers":            "gsic",
    "Greenland Ice Sheet": "gis",
    "Steric":              "steric",
    "Terrestrial Water Storage": "lws",
}

def reref(series_by_year, base_window):
    """Subtract the mean over base_window (a (y0,y1) tuple). series indexed by year."""
    m = series_by_year.loc[base_window[0]:base_window[1]].mean()
    return series_by_year - m

g = pd.read_excel(FRED, "Global").rename(columns={"Unnamed: 0": "year"}).set_index("year")
years = np.arange(FIT_Y0, FIT_Y1 + 1)
out = pd.DataFrame({"year": years}).set_index("year")
sigmas = {}

for fred_name, tgt in FRED_MAP.items():
    for stat, suf in [("mean", ""), ("lower", "_lo"), ("upper", "_hi")]:
        col = f"{fred_name} [{stat}]"
        s = reref(g[col] / 10.0, (BASE_Y0, BASE_Y1))   # mm -> cm, rel window
        out[tgt + suf] = s.reindex(years).values
    # objective sigma at the 1900 anchor, from the 90% band (lower..upper ~ 1.645σ)
    sig = (out.loc[ANCHOR, tgt + "_hi"] - out.loc[ANCHOR, tgt + "_lo"]) / (2 * 1.645)
    sigmas[tgt] = abs(sig)

# Dangendorf total
d = pd.read_csv(DANG).set_index("year")
out["dang"]     = reref(d["value"] / 10.0, (BASE_Y0, BASE_Y1)).reindex(years).values
out["dang_sig"] = (d["sigma"] / 10.0).reindex(years).values
sigmas["dang"]  = float(out.loc[ANCHOR, "dang_sig"])

os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
out.reset_index().to_csv(OUT_CSV, index=False)
pd.DataFrame([sigmas]).to_csv(OUT_SIG, index=False)

print(f"Wrote {OUT_CSV}  ({len(out)} yrs, {FIT_Y0}-{FIT_Y1}; baseline {BASE_Y0}-{BASE_Y1})")
print("Targets @1900 (cm rel window) and objective sigma:")
for t in ["ais", "gsic", "steric", "lws", "dang"]:
    print(f"  {t:7s}  @1900 = {out.loc[ANCHOR, t]:+7.2f}   sigma = {sigmas[t]:.3f}")
print(f"\nWrote {OUT_SIG}")
