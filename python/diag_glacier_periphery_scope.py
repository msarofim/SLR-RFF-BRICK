#!/usr/bin/env python3
"""diag_glacier_periphery_scope.py — RGI 05 / RGI 19 in each emulator's inventory, and MAGICC's
glacier ceiling against SLEIP's 0.32 m.

THE QUESTION (Marcus, 2026-09-12). SLEIP §4.2 says most emulators "plateau at around 0.3 m ...
consistent with the estimated total global glacier volume outside the ice sheets of approximately
0.32 m SLE (Farinotti et al., 2019)". Two things to pin down from sources ON THIS MACHINE, not
recollection: (1) whether RGI 05 (Greenland periphery) and RGI 19 (Antarctic periphery) sit in
each model's GLACIER inventory, and whether they could ALSO sit in its ice-sheet component
(double count); (2) how large MAGICC's glacier melt can actually get.

SOURCES, all local:
  * Farinotti 2019 Table 3 as transcribed in emulandice `R/main.R` (`e$max_glaciers`) — per-region
    SLE, mm. This IS the 0.32 m SLEIP cites, region by region.
  * GlacierMIP2 training set `20201106_SLE_SIMULATIONS.csv` in the emulandice package — which
    glacier MODELS cover which RGI regions. `Mar-12` = Marzeion 2012, the model MAGICC's S_eq
    table is "based on" (MAGICC7.f90:18904).
  * MAGICC's own S_eq(T) table per GCM tune, `outputs/scope_magicc_glacier_drawnset.csv`, and the
    hard cap in MAGICC7.f90 (`IF T > MAXVAL(EQUITEMP) THEN EQUISLR = MAXVAL(EQUISLR)`).
  * MAGICC-SLR 600-member SSP output for the realised ceiling.

⚠ WHAT THIS CANNOT SETTLE: whether the ICE-SHEET components (SICOPOLIS, ISMIP6 GrIS/AIS, PISM)
include the peripheral glaciers inside their domain masks. That is a model-domain question and
needs Goelzer 2020 / Seroussi 2020 / Greve & Chambers 2022 / AR6 §9.5.1 — none on this machine.

  python3 python/diag_glacier_periphery_scope.py
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = os.path.expanduser("~/Documents/2026/CodeProjects/facts/modules/emulandice/shared/emulandice")
GMIP2 = os.path.join(FACTS, "inst/extdata/20201106_SLE_SIMULATIONS.csv")
MAGICC_SSP = os.path.expanduser("~/Documents/2026/CodeProjects/MAGICC/slr-refresh/data/processed/"
                                "SSPs_Nauels2025_withOCH_2026_06_16_100817.csv")
MAGICC_SEQ = os.path.join(REPO, "outputs/scope_magicc_glacier_drawnset.csv")
OUT = os.path.join(REPO, "outputs/diag_glacier_periphery_scope.csv")

# Farinotti et al. 2019 Table 3, SLE in mm, exactly as emulandice R/main.R `e$max_glaciers`
# carries it (second element of each pair). Transcribed, not derived -- the receipt is that file.
FARINOTTI_MM = {1: 43.3, 2: 2.6, 3: 64.8, 4: 20.5, 5: 33.6, 6: 9.1, 7: 17.3, 8: 0.7, 9: 32.0,
                10: 0.3, 11: 0.3, 12: 0.2, 13: 7.9, 14: 6.9, 15: 2.1, 16: 0.2, 17: 12.8,
                18: 0.2, 19: 69.4}
R_GIS_PERIPH, R_AIS_PERIPH = 5, 19
SLEIP_CEILING_M = 0.32                     # §4.2, "outside the ice sheets", Farinotti 2019
WR_CEILING_M = 0.41                        # §4.2, Wigley & Raper 2005, BRICK and FRISIA
MAGICC_MODEL_IN_GMIP2 = "Mar-12"           # Marzeion 2012, MAGICC7.f90 "BASED ON MARZEION DATA"
BASE = list(range(1995, 2015))             # SLEIP's reference period
GL_STARTYEAR = 1850                        # MAGCFG_DEFAULTALL.CFG:640 SLR_GL_STARTYEAR
SCEN_HIGH = "ssp585"
YEAR = 2300


def main():
    rows = []
    # ---- 1. what the 0.32 m is made of ------------------------------------------------
    tot = sum(FARINOTTI_MM.values()); p5, p19 = FARINOTTI_MM[R_GIS_PERIPH], FARINOTTI_MM[R_AIS_PERIPH]
    print("=== 1. FARINOTTI 2019 TABLE 3 (as in emulandice), mm SLE")
    print(f"  all 19 RGI regions        {tot:6.1f}   = {tot/1000:.3f} m  <- SLEIP's {SLEIP_CEILING_M} m")
    print(f"  RGI 05 Greenland periph   {p5:6.1f}   = {100*p5/tot:4.1f} %")
    print(f"  RGI 19 Antarctic periph   {p19:6.1f}   = {100*p19/tot:4.1f} %")
    print(f"  both peripheries          {p5+p19:6.1f}   = {100*(p5+p19)/tot:4.1f} %")
    print(f"  excluding RGI 19          {tot-p19:6.1f}")
    print(f"  excluding RGI 05 and 19   {tot-p5-p19:6.1f}")
    rows += [dict(item="farinotti_all19_mm", value=tot), dict(item="farinotti_r5_mm", value=p5),
             dict(item="farinotti_r19_mm", value=p19), dict(item="farinotti_excl19_mm", value=tot - p19)]

    # ---- 2. which GlacierMIP2 models cover the peripheries ----------------------------
    g = pd.read_csv(GMIP2, low_memory=False)
    g = g[g.ice_source == "Glaciers"]
    cov = g.groupby("model").region.nunique()
    r5m = sorted(g[g.region == f"region_{R_GIS_PERIPH}"].model.unique())
    r19m = sorted(g[g.region == f"region_{R_AIS_PERIPH}"].model.unique())
    print("\n=== 2. GLACIERMIP2 (emulandice training set): regions covered per model")
    print("  " + "  ".join(f"{m}:{n}" for m, n in cov.sort_values().items()))
    print(f"  region_5  covered by {len(r5m)}/{cov.size}: {r5m}")
    print(f"  region_19 covered by {len(r19m)}/{cov.size}: {r19m}")
    in5, in19 = MAGICC_MODEL_IN_GMIP2 in r5m, MAGICC_MODEL_IN_GMIP2 in r19m
    print(f"  ⭐ {MAGICC_MODEL_IN_GMIP2} (MAGICC's basis): region_5 {'IN' if in5 else 'OUT'}, "
          f"region_19 {'IN' if in19 else 'OUT'}  ({cov[MAGICC_MODEL_IN_GMIP2]} of 19 regions)")
    rows += [dict(item="mar12_covers_r5", value=int(in5)), dict(item="mar12_covers_r19", value=int(in19)),
             dict(item="gmip2_models_covering_r19", value=len(r19m))]

    # ---- 3. MAGICC's ceiling, from its own table and its own output --------------------
    s = pd.read_csv(MAGICC_SEQ)
    top = s.temperature_K.max()
    cap = s[s.temperature_K == top].s_eq_mm
    print(f"\n=== 3. MAGICC GLACIER CEILING")
    print(f"  S_eq at the top of its table ({top} K), hard-capped in MAGICC7.f90, rel {GL_STARTYEAR}:")
    print(f"     {cap.min():.1f} / {cap.median():.1f} / {cap.max():.1f} mm  (min / median / max over {len(cap)} tunes)")
    d = pd.read_csv(MAGICC_SSP)
    d = d.rename(columns={c: int(c[:4]) for c in d.columns if c[:4].isdigit()})
    yc = [c for c in d.columns if isinstance(c, int)]
    x = d[(d.variable == "SLR_GL") & (d.scenario == SCEN_HIGH)].set_index("ensemble_member")[yc].astype(float)
    melted = x[BASE].mean(axis=1)
    reb = x.sub(melted, axis=0)[YEAR]
    rate = ((x[YEAR] - x[YEAR - 10]) / 10)
    print(f"  already melted {GL_STARTYEAR}->{BASE[0]}-{BASE[-1]} (median member): {melted.median():.1f} mm")
    print(f"  ⇒ implied PRESENT-DAY inventory = cap - melted: "
          f"{cap.median()-melted.median():.0f} mm median ({cap.min()-melted.median():.0f}-{cap.max()-melted.median():.0f})")
    print(f"  realised {SCEN_HIGH} @{YEAR} rel {GL_STARTYEAR}: median {x[YEAR].median():.1f}, max {x[YEAR].max():.1f} mm")
    print(f"  realised {SCEN_HIGH} @{YEAR} rel {BASE[0]}-{BASE[-1]} (SLEIP frame): "
          f"median {reb.median():.1f}, p95 {reb.quantile(.95):.1f}, max {reb.max():.1f} mm")
    print(f"     members above {SLEIP_CEILING_M*1000:.0f} mm: {(reb > SLEIP_CEILING_M*1000).sum()}/{len(reb)}; "
          f"above {WR_CEILING_M*1000:.0f} mm: {(reb > WR_CEILING_M*1000).sum()}")
    print(f"     still melting at {YEAR}: median rate {rate.median():.3f} mm/yr -- NOT plateaued")
    scope_matched = tot - p19
    print(f"  ⭐ SCOPE-MATCHED comparator (Farinotti excl. RGI 19, since Mar-12 excludes it): "
          f"{scope_matched:.0f} mm")
    print(f"     MAGICC present-day inventory / scope-matched Farinotti = "
          f"{(cap.median()-melted.median())/scope_matched:.2f}x; "
          f"members above {scope_matched:.0f} mm at {YEAR}: {(reb > scope_matched).sum()}/{len(reb)}")
    rows += [dict(item="magicc_cap_median_mm", value=cap.median()), dict(item="magicc_cap_max_mm", value=cap.max()),
             dict(item="magicc_melted_by_base_mm", value=melted.median()),
             dict(item="magicc_ssp585_2300_rebased_median_mm", value=reb.median()),
             dict(item="magicc_ssp585_2300_rebased_p95_mm", value=reb.quantile(.95)),
             dict(item="magicc_n_above_320", value=int((reb > 320).sum())),
             dict(item="magicc_n_above_scope_matched", value=int((reb > scope_matched).sum()))]
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
