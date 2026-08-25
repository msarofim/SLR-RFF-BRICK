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
Writes data/comparison/magicc_nauels_components.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.expanduser(
    "~/Documents/2026/CodeProjects/MAGICC/slr-refresh/data/processed/"
    "SSPs_Nauels2025_withOCH_2026_06_16_100817.csv")
OUT = os.path.join(REPO, "data/comparison/magicc_nauels_components.csv")

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
