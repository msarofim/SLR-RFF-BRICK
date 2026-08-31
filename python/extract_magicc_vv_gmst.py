#!/usr/bin/env python3
"""extract_magicc_vv_gmst.py — MAGICC's OWN GMST for the van Vuuren markers.

  python3 python/extract_magicc_vv_gmst.py [--force]

Writes data/comparison/magicc_gmst_vv.csv (year, scenario, med/p05/p17/p83/p95, K rel
1850-1900) from the same 477 MB source run that
`extract_magicc_vv_components.py` reads for the SLR components.

WHY THIS EXISTS. MAGICC-SLR computes its own climate from emissions -- that is what makes
its agreement with the FaIR-driven arms non-circular -- but it also means that comparing
MAGICC's glacier path against a Ladrillo equilibrium evaluated at FaIR's temperature is
NOT like-for-like (`like_for_like_forcing`: forcing trajectory first). Any claim of the
form "MAGICC implies a lower S_eq than ours" needs MAGICC's own T, or the difference could
be nothing but the two models' climate.

CONVENTIONS ARE IMPORTED, NOT RESTATED, from extract_magicc_components (the sibling
extractor): the source path, the year axis, and the quantile set. Only the baseline
differs, and deliberately: the SLR extractors rebase on 1995-2014 because that is the
projection baseline every Ladrillo SLR product uses, while a TEMPERATURE has to be on
1850-1900 to be comparable with Ladrillo's glacier-frame drivers and with the
GlacierMIP3 rungs, which are stated as global K rel 1850-1900.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

import extract_magicc_components as emc
import extract_magicc_vv_components as evc

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data/comparison/magicc_gmst_vv.csv")
VAR = "Surface Air Temperature Change"
TBASE = list(range(1850, 1901))          # K rel 1850-1900 -- the rung frame
SCENARIOS = evc.VV + evc.CONTROL


def main():
    force = "--force" in sys.argv[1:]
    if os.path.exists(OUT) and not force:
        print("cached: %s (pass --force to rebuild)" % os.path.relpath(OUT, REPO))
        return
    print("reading %s ..." % os.path.basename(evc.SOURCE))
    d = pd.read_csv(evc.SOURCE)
    ycols = {c: int(str(c)[:4]) for c in d.columns if str(c)[:4].isdigit()}
    d = d.rename(columns=ycols)
    d = d[d.variable == VAR]
    if d.empty:
        raise SystemExit("[SOURCE] no rows for variable %r" % VAR)
    ## [BASELINE-PRESENT] the 1850-1900 columns must exist before we rebase on them --
    ## the sibling extractor's YEARS-PRESENT gate, moved to the window this script needs.
    have = {c for c in d.columns if isinstance(c, (int, np.integer))}
    gap = [y for y in TBASE + emc.YEARS_OUT if y not in have]
    if gap:
        raise SystemExit("[BASELINE-PRESENT] %d year(s) absent, first %d" % (len(gap), gap[0]))

    rows = []
    for scen in SCENARIOS:
        s = d[d.scenario == scen]
        if s.empty:
            raise SystemExit("[SOURCE] scenario %r absent" % scen)
        yrs = sorted(set(emc.YEARS_OUT) | set(TBASE))
        member = s.groupby("ensemble_member")[yrs].mean()
        member = member.sub(member[TBASE].mean(axis=1), axis=0)
        arr = member[emc.YEARS_OUT].to_numpy()
        for name, q in emc.QUANTILES.items():
            for y, val in zip(emc.YEARS_OUT, np.percentile(arr, q, axis=0)):
                rows.append((scen, y, name, val))
        print("  %-8s n=%d  T@2100=%.2f  T@2300=%.2f K"
              % (scen, len(member), np.median(member[2100]), np.median(member[2300])))
    out = (pd.DataFrame(rows, columns=["scenario", "year", "stat", "value"])
           .pivot_table(index=["scenario", "year"], columns="stat",
                        values="value").reset_index())
    out["unit"] = "K rel 1850-1900"
    out["source"] = "MAGICC-SLR"
    out.to_csv(OUT, index=False)
    print("\nwrote %s (%d rows)" % (os.path.relpath(OUT, REPO), len(out)))


if __name__ == "__main__":
    main()
