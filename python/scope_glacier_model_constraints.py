#!/usr/bin/env python3
"""
scope_glacier_model_constraints.py — can the Zekollari et al. 2024 glacier-model
archives constrain Ladrillo's three glacier reservoirs, and do those models match
the historical observations first?

SOURCES (fetched 2026-08-14, both openly licensed)
  Zekollari, H., Huss, M., Schuster, L., Maussion, F., Rounce, D. R., Aguayo, R.,
  Champollion, N., Compagno, L., Hugonnet, R., Marzeion, B., Mojtabavi, S.,
  Farinotti, D. (2024) "21st century global glacier evolution under CMIP6
  scenarios and the role of glacier-specific observations", The Cryosphere 18,
  5045-5066, doi 10.5194/tc-18-5045-2024.
    GloGEM : zenodo.10908278 (CC BY 4.0) — Volume/Area per RGI region, 2015-2100,
             12 CMIP6 GCMs, SSP1-1.9/1-2.6/2-4.5/3-7.0/5-8.5.
    OGGM   : zenodo.8286065 (oggm-standard-projections-csv-files v1.0) —
             volume per RGI region, 2000-2100 (19 GCMs) and 2000-2300 (6 GCMs,
             ssp126/ssp534-over/ssp585 only).

WHY THIS IS WORTH DOING, in Marcus's priority order (2026-08-14):
  1. HISTORICAL FIRST. Both archives start before the projection era, so the same
     files that give a projection constraint also say whether these models
     reproduce the observed 2000-2020 mass loss — per region, against GlaMBIE.
     A model family that misses the observed record has no business constraining
     our projection, and R19 is exactly where that has to be checked.
  2. PHYSICS THROUGH GLACIER MODELS. The GlacierMIP3 rungs already in the
     likelihood are COMMITTED loss at a warming level. These archives are
     REALISED loss by a date, which additionally constrains the response
     timescale (kappa, nu) rather than S_eq alone — a different axis.
  3. A 2300 COMPARATOR AT ALL. FACTS stops at 2150 and MAGICC-SLR at 2100, so
     Ladrillo's 2300 column currently has no external check. OGGM's 2300 branch
     is the first one available.

WHAT IS DELIBERATELY NOT DONE HERE. No likelihood term is written. This scopes
what the data can support, per block, and reports where it cannot.

FETCHING THE ARCHIVES (they are NOT committed — 584 kB + 47 MB; only the
aggregated per-block CSV this script writes is):

  mkdir -p /tmp/zen && cd /tmp/zen
  curl -sL -o glogem.zip "https://zenodo.org/records/10908278/files/GloGEM_CMIP6_global_glacier_projections.zip?download=1"
  curl -sL -o oggm.zip   "https://zenodo.org/records/8286065/files/OGGM/oggm-standard-projections-csv-files-v1.0.zip?download=1"
  unzip -q glogem.zip -d glogem && unzip -q oggm.zip -d oggm

  source ~/climate-env/bin/activate
  python3 python/scope_glacier_model_constraints.py --root /tmp/zen
Writes outputs/scope_glacier_model_constraints.csv
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs/scope_glacier_model_constraints.csv")

# Ladrillo's three reservoirs (calibrate_mcmc_ext.jl L141). RGI 05 (Greenland
# periphery) belongs to no block — it is the ice sheet's, not the glaciers'.
BLOCKS = {
    "R19":   ["19"],
    "SLOWP": ["03", "09", "07", "06"],
    "FAST":  ["01", "04", "17", "13", "14", "02", "15", "08", "10", "11", "16",
              "18", "12"],
}
SSPS = ["ssp126", "ssp245", "ssp585"]
HIST_WIN = (2000, 2020)      # the GlaMBIE-comparable window (OGGM only; GloGEM starts 2015)
PROJ_REF = 2015              # Zekollari's own reference year for "% of 2015 mass"
HORIZONS = [2100, 2300]


def glogem_volume(root, region, ssp):
    f = os.path.join(root, "glogem", "Volume", f"RGI{region}", f"{ssp}.csv")
    if not os.path.isfile(f):
        return None
    d = pd.read_csv(f).set_index("year")
    return d


def oggm_volume(root, region, ssp, branch):
    """branch: '2100' (19 GCMs, to 2100) or '2300' (6 GCMs, to 2300)."""
    base = glob.glob(os.path.join(
        root, "oggm", "*", "1.6.1", "common_running_2100_2300", "volume",
        "CMIP6", branch, f"RGI{region}", f"{ssp}.csv"))
    if not base:
        return None
    d = pd.read_csv(base[0]).set_index("time")
    d.index = d.index.astype(int)
    return d


def block_volume(loader, members, ssp, **kw):
    """Sum member regions on their COMMON GCM columns and common years. Summing
    only shared columns matters: a GCM present for one region and absent for
    another would otherwise silently contribute an incomplete block."""
    parts = []
    for r in members:
        d = loader(r, ssp, **kw)
        if d is None:
            return None, []
        parts.append(d)
    gcms = set(parts[0].columns)
    for p in parts[1:]:
        gcms &= set(p.columns)
    gcms = sorted(gcms)
    if not gcms:
        return None, []
    yrs = parts[0].index
    for p in parts[1:]:
        yrs = yrs.intersection(p.index)
    tot = sum(p.loc[yrs, gcms] for p in parts)
    return tot, gcms


def loss_pct(vol, y0, y1):
    """% of y0 volume lost by y1, per GCM."""
    if vol is None or y0 not in vol.index or y1 not in vol.index:
        return None
    return 100.0 * (vol.loc[y0] - vol.loc[y1]) / vol.loc[y0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True,
                    help="directory holding the unzipped 'glogem' and 'oggm' archives")
    args = ap.parse_args()
    G = lambda r, s: glogem_volume(args.root, r, s)
    O = lambda r, s, branch="2100": oggm_volume(args.root, r, s, branch)

    rows = []
    print("Zekollari et al. 2024 glacier archives, aggregated to Ladrillo's blocks")
    print("  GloGEM zenodo.10908278 (2015-2100) | OGGM zenodo.8286065 "
          "(2000-2100, and 2000-2300 on a 6-GCM subset)\n")

    # ---- 1. HISTORICAL FIRST -------------------------------------------------
    print(f"  1. HISTORICAL {HIST_WIN[0]}-{HIST_WIN[1]} — % of {HIST_WIN[0]} volume lost")
    print("     (OGGM only; GloGEM's archive starts at 2015. Compare with GlaMBIE")
    print("      per-block cumulative over the same window before trusting anything else.)")
    print(f"  {'block':7s} {'ssp':8s} {'n GCM':>6s} {'median':>9s} {'5-95%':>16s}")
    for b, mem in BLOCKS.items():
        for ssp in SSPS:
            vol, gcms = block_volume(O, mem, ssp, branch="2100")
            l = loss_pct(vol, HIST_WIN[0], HIST_WIN[1])
            if l is None:
                continue
            q = np.percentile(l, [5, 50, 95])
            print(f"  {b:7s} {ssp:8s} {len(gcms):6d} {q[1]:9.2f} "
                  f"[{q[0]:6.2f},{q[2]:6.2f}]")
            rows.append(dict(model="OGGM", block=b, ssp=ssp, window=f"{HIST_WIN[0]}-{HIST_WIN[1]}",
                             n_gcm=len(gcms), median=q[1], p05=q[0], p95=q[2]))

    # ---- 2. PROJECTIONS, 2100 -----------------------------------------------
    print(f"\n  2. PROJECTION {PROJ_REF}-2100 — % of {PROJ_REF} volume lost")
    print(f"  {'block':7s} {'ssp':8s} {'model':7s} {'n GCM':>6s} {'median':>9s} {'5-95%':>16s}")
    for b, mem in BLOCKS.items():
        for ssp in SSPS:
            for name, vol, gcms in (
                ("GloGEM",) + block_volume(G, mem, ssp),
                ("OGGM",) + block_volume(O, mem, ssp, branch="2100"),
            ):
                l = loss_pct(vol, PROJ_REF, 2100)
                if l is None:
                    continue
                q = np.percentile(l, [5, 50, 95])
                print(f"  {b:7s} {ssp:8s} {name:7s} {len(gcms):6d} {q[1]:9.2f} "
                      f"[{q[0]:6.2f},{q[2]:6.2f}]")
                rows.append(dict(model=name, block=b, ssp=ssp,
                                 window=f"{PROJ_REF}-2100", n_gcm=len(gcms),
                                 median=q[1], p05=q[0], p95=q[2]))

    # ---- 3. THE 2300 BRANCH --------------------------------------------------
    print(f"\n  3. PROJECTION {PROJ_REF}-2300 — OGGM only, 6-GCM subset, "
          "ssp126/ssp585 only")
    print("     This is the ONLY external 2300 glacier comparator available: FACTS")
    print("     stops at 2150, MAGICC-SLR at 2100.")
    print(f"  {'block':7s} {'ssp':8s} {'n GCM':>6s} {'median':>9s} {'5-95%':>16s}")
    for b, mem in BLOCKS.items():
        for ssp in ("ssp126", "ssp585"):
            vol, gcms = block_volume(O, mem, ssp, branch="2300")
            l = loss_pct(vol, PROJ_REF, 2300)
            if l is None:
                continue
            q = np.percentile(l, [5, 50, 95])
            print(f"  {b:7s} {ssp:8s} {len(gcms):6d} {q[1]:9.2f} "
                  f"[{q[0]:6.2f},{q[2]:6.2f}]")
            rows.append(dict(model="OGGM", block=b, ssp=ssp,
                             window=f"{PROJ_REF}-2300", n_gcm=len(gcms),
                             median=q[1], p05=q[0], p95=q[2]))

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    # ---- inter-model spread, which is the thing any term must span -----------
    print("\n  INTER-MODEL SPREAD at 2100 — GloGEM vs OGGM, percentage points")
    print("  (the paper flags region 19 as its largest disagreement, from frontal")
    print("   ablation: GloGEM treats it simply, this OGGM setup not explicitly)")
    p = df[df.window == f"{PROJ_REF}-2100"].pivot_table(
        index=["block", "ssp"], columns="model", values="median")
    p["OGGM - GloGEM"] = p["OGGM"] - p["GloGEM"]
    print(p.round(2).to_string())

    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
