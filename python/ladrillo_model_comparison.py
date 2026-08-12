#!/usr/bin/env python3
"""
ladrillo_model_comparison.py — Ladrillo against FACTS, MAGICC-SLR, and BRICK 2.0.

Puts the four projection sources on one basis (cm, re-referenced to 1995-2014,
per SSP and component) and reports medians with 17-83% bands at 2100 and 2150,
plus the scenario-spread diagnostic (SSP1-2.6 -> SSP5-8.5 median difference per
component), which is what exposes a glacier module that saturates.

Sources
  Ladrillo    outputs/ssps_components_2300_extC.csv
              extC posterior, 2000 draws, FaIR-mean forcing per SSP.
  BRICK 2.0   outputs/ssps_gsic_2300.csv
              pre-Mengel MimiBRICK v2.0.0 with the Wigley-Raper glacier module
              on the post-PR#93 posterior. GLACIERS ONLY - the one legacy arm.
  MAGICC-SLR  data/comparison/magicc_nauels_components.csv
              MAGICC v7.5.3 + Nauels 2025 SLR, 600-member AR6 drawnset,
              extracted by python/extract_magicc_components.py. Ends at 2100.
  FACTS       outputs/facts_components_n200.csv
              global.coupling.{ssp126,ssp245,ssp585}.n200, per module,
              rel. baseyear 2005 (~ the 1995-2014 mean; the standing
              MAGICC-comparison convention treats the two as comparable).

BAND CAVEAT, stated in every table: Ladrillo and BRICK 2.0 run on MEAN climate
forcing, so their bands are POSTERIOR-PARAMETER spread only. MAGICC and FACTS
bands carry climate uncertainty as well. MEDIANS are comparable; band WIDTHS
are not.

  python3 python/ladrillo_model_comparison.py
Writes outputs/ladrillo_model_comparison.csv
"""
import os

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs/ladrillo_model_comparison.csv")

LADRILLO_CSV = os.path.join(REPO, "outputs/ssps_components_2300_extC.csv")
BRICK20_GSIC_CSV = os.path.join(REPO, "outputs/ssps_gsic_2300.csv")
MAGICC_CSV = os.path.join(REPO, "data/comparison/magicc_nauels_components.csv")
FACTS_CSV = os.path.join(REPO, "outputs/facts_components_n200.csv")

HORIZONS = [2100, 2150]
SCENARIOS = ["ssp126", "ssp245", "ssp585"]      # the three all four sources share
LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
COMPONENTS = ["glaciers", "gis", "ais", "te", "lws", "total"]
SPREAD_LO, SPREAD_HI = "ssp126", "ssp585"
COLS = ["source", "module", "scenario", "component", "year", "med", "p05", "p17", "p83", "p95"]


def _rows(df, source, module_col=None, module=None):
    out = df.copy()
    out["source"] = source
    out["module"] = out[module_col] if module_col else module
    for q in ("p05", "p17", "p83", "p95"):
        if q not in out:
            out[q] = float("nan")
    return out[COLS]


def load_ladrillo():
    df = pd.read_csv(LADRILLO_CSV)
    df["scenario"] = df.ssp.map({v: k for k, v in LABEL.items()})
    return _rows(df, "Ladrillo", module="extC")


def load_brick20():
    """Pre-Mengel BRICK 2.0, glaciers only (Wigley-Raper), lo/hi are 5-95%."""
    df = pd.read_csv(BRICK20_GSIC_CSV)
    df["scenario"] = df.ssp.map({v: k for k, v in LABEL.items()})
    df = df.dropna(subset=["scenario"]).rename(
        columns={"gsic_med": "med", "gsic_lo": "p05", "gsic_hi": "p95"})
    df["component"] = "glaciers"
    return _rows(df, "BRICK 2.0", module="WR-GSIC")


def load_magicc():
    return _rows(pd.read_csv(MAGICC_CSV), "MAGICC-SLR", module="Nauels2025")


def load_facts():
    return _rows(pd.read_csv(FACTS_CSV), "FACTS", module_col="module")


def band(r):
    if pd.isna(r.p17) or pd.isna(r.p83):
        return f"{r.med:6.1f} [{r.p05:6.1f},{r.p95:6.1f}]*"
    return f"{r.med:6.1f} [{r.p17:6.1f},{r.p83:6.1f}]"


def main():
    df = pd.concat([load_ladrillo(), load_brick20(), load_magicc(), load_facts()],
                   ignore_index=True)
    df = df[df.scenario.isin(SCENARIOS) & df.component.isin(COMPONENTS)]
    df = df[df.year.isin(HORIZONS + [2100])]
    df.sort_values(["component", "source", "module", "scenario", "year"]).to_csv(OUT, index=False)

    print("Ladrillo vs FACTS / MAGICC-SLR / BRICK 2.0 — cm, rel. 1995-2014 "
          "(FACTS rel. baseyear 2005)")
    print("median [17-83%]; * = 5-95% (that source reports no 17-83 band)")
    print("BAND CAVEAT: BRICK bands are posterior-parameter spread on MEAN forcing; "
          "MAGICC/FACTS bands also carry climate uncertainty. Compare MEDIANS.")

    for y in HORIZONS:
        print(f"\n{'='*96}\n@{y}\n{'='*96}")
        for comp in COMPONENTS:
            sub = df[(df.component == comp) & (df.year == y)]
            if sub.empty:
                continue
            print(f"--- {comp} ---")
            for (source, module), g in sub.groupby(["source", "module"], sort=False):
                line = f"  {source:11s} {module:12s}"
                for ssp in SCENARIOS:
                    r = g[g.scenario == ssp]
                    line += f"  {LABEL[ssp]}: " + (band(r.iloc[0]) if len(r)
                                                   else f"{'-':>21s}")
                print(line)

    print(f"\n{'='*96}\nSCENARIO SPREAD  {LABEL[SPREAD_LO]} -> {LABEL[SPREAD_HI]} "
          f"(cm, median difference at 2100)\n{'='*96}")
    print("  A glacier module with no finite temperature-dependent equilibrium, or one")
    print("  whose reservoirs are exhausted, shows little spread across scenarios.")
    spread_rows = []
    for comp in COMPONENTS:
        sub = df[(df.component == comp) & (df.year == 2100)]
        for (source, module), g in sub.groupby(["source", "module"], sort=False):
            lo = g[g.scenario == SPREAD_LO]
            hi = g[g.scenario == SPREAD_HI]
            if len(lo) and len(hi):
                d = hi.iloc[0].med - lo.iloc[0].med
                print(f"  {comp:9s} {source:11s} {module:12s} {d:+7.1f}")
                spread_rows.append(dict(component=comp, source=source, module=module,
                                        year=2100, spread_126_585=d))
    pd.DataFrame(spread_rows).to_csv(
        OUT.replace(".csv", "_spread.csv"), index=False)

    print(f"\nwrote {os.path.relpath(OUT, REPO)} and "
          f"{os.path.relpath(OUT.replace('.csv', '_spread.csv'), REPO)}")


if __name__ == "__main__":
    main()
