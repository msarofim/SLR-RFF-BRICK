#!/usr/bin/env python3
"""
extract_magicc_components.py — MAGICC-SLR (Nauels 2025) component bands, once,
into a tracked file this repo can compare against without the MAGICC tree.

Source: the 600-member AR6 drawnset run of MAGICC v7.5.3 with the Nauels-2025
sea-level module (slr-refresh notebooks 200 -> 302 -> 400), which lives in the
members-only MAGICC working copy. MAGICC *output* is publishable (the binary,
source and drawnset are not), so the extracted bands are tracked here and the
comparison script never needs the private tree.

MAGICC's seven SLR modules are mapped onto BRICK's five components:
    te        = SLR_EXPANSION
    glaciers  = SLR_GL
    gis       = SLR_GIS_SMB + SLR_GIS_SID
    ais       = SLR_AIS_SMB + SLR_AIS_SID
    lws       = SLR_LANDWATER
    total     = Sea Level Rise            (reported, not summed)

Conventions matched to the Ladrillo projections: cm, re-referenced to the
1995-2014 mean, per-member sums BEFORE quantiles (so component bands are
internally consistent with the total).

  python3 python/extract_magicc_components.py
Writes data/comparison/magicc_nauels_components.csv          (projection: 2000-2300, rel 1995-2014)
       data/comparison/magicc_nauels_components_hist.csv     (HINDCAST: 1900-2026, rel 1995-2005,
                                                              ssp245, + the SMB/SID splits)
       data/comparison/magicc_nauels_gis_split.csv           (projection: gis_smb / gis_sid /
                                                              ais_smb / ais_sid, all SSPs)

⚠ THE HINDCAST FILE IS SEPARATE, ON PURPOSE (2026-09-11). The projection file is frozen in the
benchmark (`benchmark/reference/_fixed/magicc_nauels_components.csv`, sha in its manifest), so
it must stay BYTE-IDENTICAL on re-extraction; the history and the ice-sheet split are additive
files with their own baseline. The source run spans 1750-2305 -- the pre-2000 years were
always there, exactly as the post-2100 ones were before 2026-08-25 (same lesson, same file).
⚠ MAGICC's ICE SHEETS START IN 1991 (GIS) AND 2003 (AIS): the series are identically zero
before their `slr_*_startyear`, so [HIST-START] records the first year each component moves
and the hindcast file carries NaN before it rather than a false flat line. Glaciers and
expansion are hindcast from 1851. See diag_magicc_gis_structure.py.
⚠ The history is SCENARIO-INVARIANT before 2015 (max member-wise spread across the six SSPs
< 0.01 mm, [HIST-SCEN] below), so the hindcast file takes ssp245 -- the scenario whose
harmonized FaIR twin (ssp245harm) drives Ladrillo's and BRICK 2.0's hindcasts.
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.expanduser(
    "~/Documents/2026/CodeProjects/MAGICC/slr-refresh/data/processed/"
    "SSPs_Nauels2025_withOCH_2026_06_16_100817.csv")
OUT = os.path.join(REPO, "data/comparison/magicc_nauels_components.csv")
OUT_HIST = os.path.join(REPO, "data/comparison/magicc_nauels_components_hist.csv")
OUT_SPLIT = os.path.join(REPO, "data/comparison/magicc_nauels_gis_split.csv")
HIST_YEARS = list(range(1900, 2027))          # plot_hindcast_components X0..X1
HIST_BASE = list(range(1995, 2006))           # the CALIBRATION window (BASE0..BASE1 there)
HIST_SSP = "ssp245"
## [HIST-SCEN] bound: a fraction of the hindcast SIGNAL (the total's own 1750-2015 median
## range), not a typed millimetre -- `tolerance_scaled_to_spread`. Solver noise across the six
## SSP runs is ~1e-2 mm against ~1e2 mm of signal; 1e-3 of the signal sits an order of
## magnitude above the noise and three below anything a figure could show.
HIST_SCEN_REL = 1e-3
SPLIT_MAP = {"gis_smb": ["SLR_GIS_SMB"], "gis_sid": ["SLR_GIS_SID"],
             "ais_smb": ["SLR_AIS_SMB"], "ais_sid": ["SLR_AIS_SID"]}

BASE_YEARS = list(range(1995, 2015))
MM_TO_CM = 0.1
## ⚠ CORRECTED 2026-08-25. This used to read `range(2000, 2101)` with the comment "this
## MAGICC run ends at 2100". THE RUN DOES NOT END AT 2100 — the source file carries annual
## columns through 2305-01-01, because `slr-refresh/notebooks/302_run-magicc-scenarios-SSPs.py`
## sets `endyear_run = 2300 + 5` and its own summary table filters to `year=[2100, 2300]`.
## The 2100 cut was OURS, and it is why every comparison this repo has ever made at 2150 had
## only FACTS to compare against ("NO UPPER COMPARATOR AT THIS HORIZON" in bench_ladrillo,
## and step 1's caveat that the separation ruling "is a 2100 statement"). No MAGICC re-run is
## needed to fix it; only this line was wrong.
## [YEARS-PRESENT] below asserts the columns actually exist rather than trusting this range.
YEARS_OUT = list(range(2000, 2301))
SSPS = ["ssp119", "ssp126", "ssp245", "ssp370", "ssp585"]
COMPONENT_MAP = {
    "te":       ["SLR_EXPANSION"],
    "glaciers": ["SLR_GL"],
    "gis":      ["SLR_GIS_SMB", "SLR_GIS_SID"],
    "ais":      ["SLR_AIS_SMB", "SLR_AIS_SID"],
    "lws":      ["SLR_LANDWATER"],
    "total":    ["Sea Level Rise"],
}
QUANTILES = {"p05": 5, "p17": 17, "med": 50, "p83": 83, "p95": 95}


def load_source():
    """scmdata wide format: metadata columns + one column per timestamp."""
    df = pd.read_csv(SOURCE)
    year_cols = [c for c in df.columns if c[:4].isdigit()]
    years = [int(c[:4]) for c in year_cols]
    df = df.rename(columns=dict(zip(year_cols, years)))
    keep = ["scenario", "variable", "ensemble_member", "unit"] + years
    return df[keep], years


def main():
    df, years = load_source()
    # [YEARS-PRESENT] the whole point of the 2026-08-25 correction is that the requested
    # horizon must be CHECKED against the file, not assumed from a comment.
    missing = [y for y in YEARS_OUT if y not in years]
    if missing:
        raise SystemExit(f"source lacks {len(missing)} requested years "
                         f"({missing[0]}-{missing[-1]}); it spans {min(years)}-{max(years)}")
    print(f"[YEARS-PRESENT] source spans {min(years)}-{max(years)}; "
          f"extracting {YEARS_OUT[0]}-{YEARS_OUT[-1]}")
    needed = {v for vs in COMPONENT_MAP.values() for v in vs}
    units = df[df.variable.isin(needed)].unit.unique()
    assert set(units) == {"mm"}, f"expected mm-valued SLR series, got {units}"

    rows = []
    for ssp in SSPS:
        sub = df[df.scenario == ssp]
        if sub.empty:
            print(f"  {ssp}: absent from the MAGICC run — skipped")
            continue
        for comp, variables in COMPONENT_MAP.items():
            # sum the MAGICC modules PER MEMBER, then rebaseline, then quantile
            parts = []
            for v in variables:
                p = sub[sub.variable == v].set_index("ensemble_member")[years].sort_index()
                assert not p.empty, f"{ssp}: MAGICC variable {v} missing"
                parts.append(p)
            member = sum(parts[1:], parts[0]) * MM_TO_CM
            member = member.sub(member[BASE_YEARS].mean(axis=1), axis=0)
            arr = member[YEARS_OUT].to_numpy()
            for name, q in QUANTILES.items():
                for y, val in zip(YEARS_OUT, np.percentile(arr, q, axis=0)):
                    rows.append(dict(scenario=ssp, component=comp, year=y,
                                     stat=name, value=val, n=arr.shape[0]))
        print(f"  {ssp}: {arr.shape[0]} members")

    ## --- the projection-side ice-sheet SPLIT (additive file; same baseline as OUT) ---
    srows = []
    for ssp in SSPS:
        sub = df[df.scenario == ssp]
        if sub.empty:
            continue
        for comp, variables in SPLIT_MAP.items():
            p = sub[sub.variable == variables[0]].set_index("ensemble_member")[years].sort_index()
            member = p * MM_TO_CM
            member = member.sub(member[BASE_YEARS].mean(axis=1), axis=0)
            arr = member[YEARS_OUT].to_numpy()
            for name, q in QUANTILES.items():
                for y, val in zip(YEARS_OUT, np.percentile(arr, q, axis=0)):
                    srows.append(dict(scenario=ssp, component=comp, year=y,
                                      stat=name, value=val, n=arr.shape[0]))
    split = pd.DataFrame(srows).pivot_table(
        index=["scenario", "component", "year", "n"], columns="stat", values="value"
    ).reset_index()[["scenario", "component", "year", "med", "p05", "p17", "p83", "p95", "n"]]
    split["unit"] = "cm rel 1995-2014"
    split.to_csv(OUT_SPLIT, index=False)
    print(f"wrote {os.path.relpath(OUT_SPLIT, REPO)}  ({len(split)} rows)")

    ## --- the HINDCAST file: 1900-2026, rel 1995-2005, ssp245, components + splits ---
    missing = [y for y in HIST_YEARS if y not in years]
    assert not missing, f"source lacks hindcast years {missing[0]}-{missing[-1]}"
    ## [HIST-SCEN] the pre-2015 history must not depend on the SSP, or "ssp245" is a choice.
    allv = df[df.variable.isin(needed)]
    ref = allv[allv.scenario == HIST_SSP].set_index(["variable", "ensemble_member"]).sort_index()
    pre = [y for y in years if y <= 2015]
    tot = ref.loc["Sea Level Rise"][pre].median()
    tol = HIST_SCEN_REL * float(tot.max() - tot.min())
    worst = 0.0
    for ssp in SSPS:
        o = allv[allv.scenario == ssp].set_index(["variable", "ensemble_member"]).sort_index()
        if o.empty:
            continue
        worst = max(worst, float(np.nanmax(np.abs(o[pre].to_numpy() - ref[pre].to_numpy()))))
    print(f"[HIST-SCEN] max member-wise |ssp - {HIST_SSP}| over 1750-2015 = {worst:.2e} mm "
          f"(bound {tol:.2e} mm = {HIST_SCEN_REL:g} x the total's {tot.max() - tot.min():.0f} mm "
          f"1750-2015 range)  {'PASS' if worst <= tol else 'FAIL'}")
    if worst > tol:
        raise SystemExit("[HIST-SCEN] the MAGICC history is scenario-dependent before 2015; "
                         "the hindcast file cannot be labelled scenario-free.")
    sub = df[df.scenario == HIST_SSP]
    hrows, starts = [], {}
    for comp, variables in {**COMPONENT_MAP, **SPLIT_MAP}.items():
        parts = [sub[sub.variable == v].set_index("ensemble_member")[years].sort_index()
                 for v in variables]
        member = sum(parts[1:], parts[0]) * MM_TO_CM
        ## [HIST-START] first year the ensemble MEDIAN departs from its 1750 value: an
        ## ice-sheet module that has not started yet is identically zero, which re-baselined
        ## becomes a flat NEGATIVE line -- a false hindcast. Those years are written as NaN.
        med = member[years].median()
        moved = med[(med - med.iloc[0]).abs() > 1e-9]
        start = int(moved.index[0]) if len(moved) else None
        starts[comp] = start
        member = member.sub(member[HIST_BASE].mean(axis=1), axis=0)
        arr = member[HIST_YEARS].to_numpy()
        qs = {name: np.percentile(arr, q, axis=0) for name, q in QUANTILES.items()}
        for i, y in enumerate(HIST_YEARS):
            live = start is not None and y >= start
            hrows.append(dict(scenario=HIST_SSP, component=comp, year=y,
                              **{name: (qs[name][i] if live else np.nan) for name in QUANTILES},
                              n=arr.shape[0], start_year=start))
    print("[HIST-START] first year each component's median moves: "
          + ", ".join(f"{c} {s}" for c, s in starts.items()))
    ## Built row-wise, not with pivot_table: a NaN-valued pivot with the start year in the
    ## index cross-multiplies the NaN rows over every start_year (4x the rows, all empty).
    hist = pd.DataFrame(hrows)[["scenario", "component", "year", "med", "p05", "p17", "p83",
                                "p95", "n", "start_year"]]
    hist["unit"] = "cm rel 1995-2005"
    hist.to_csv(OUT_HIST, index=False)
    print(f"wrote {os.path.relpath(OUT_HIST, REPO)}  ({len(hist)} rows, "
          f"{hist.component.nunique()} components, {HIST_YEARS[0]}-{HIST_YEARS[-1]})")

    out = pd.DataFrame(rows).pivot_table(
        index=["scenario", "component", "year", "n"], columns="stat", values="value"
    ).reset_index()[["scenario", "component", "year", "med", "p05", "p17", "p83", "p95", "n"]]
    out["unit"] = "cm rel 1995-2014"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {os.path.relpath(OUT, REPO)}  ({len(out)} rows, "
          f"{out.scenario.nunique()} scenarios x {out.component.nunique()} components)")
    for y in (2100, 2150, 2300):
        print(f"\n--- {y} ---")
        print(out[out.year == y].to_string(index=False))


if __name__ == "__main__":
    main()
