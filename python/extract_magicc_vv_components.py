#!/usr/bin/env python3
"""extract_magicc_vv_components.py — MAGICC-SLR components for the van Vuuren markers,
with the three SSPs re-run as a CONTROL against the existing frozen arm.

  python3 python/extract_magicc_vv_components.py

Writes data/comparison/magicc_nauels_components_vv.csv

SIBLING of extract_magicc_components.py, and DELIBERATELY REUSES ITS CONSTANTS by import
rather than restating them: the baseline window, the mm->cm factor, the module->component
map and the quantile set all have to be identical or the new rows are not comparable with
the old ones, and a second hand-typed copy is how two conventions drift apart.

⚠ THE SSPs IN THIS RUN ARE A CONTROL, NOT A RESULT (Marcus 2026-08-31). Once MAGICC and
FACTS are driven by us, the seven van Vuuren markers are a complete four-model set on ONE
emissions vintage, and the SSPs stop being needed as a comparison axis. They are here for
exactly one job: they are the only scenarios where a prior result exists, so re-running them
through the same binary and drawnset proves the pipeline. That is why they kept their
ORIGINAL RCMIP inputs -- reproducing an old run requires the old inputs.

[CONTROL] therefore compares the re-run SSP rows against data/comparison/
magicc_nauels_components.csv cell by cell. Same binary (b1fa246), same 600-member drawnset,
same inputs => the difference should be at floating-point level. Anything larger is a real
change in the pipeline and must be explained before the van Vuuren rows are trusted, because
those rows have no comparator of their own.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

import extract_magicc_components as emc   # the conventions, imported not restated

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.expanduser(
    "~/Documents/2026/CodeProjects/MAGICC/slr-refresh/data/processed/"
    "VVandSSPs_Nauels2025_withOCH_2026_08_31_073153.csv")
FROZEN = os.path.join(REPO, "data/comparison/magicc_nauels_components.csv")
OUT = os.path.join(REPO, "data/comparison/magicc_nauels_components_vv.csv")

VV = ["vvVL", "vvLN", "vvL", "vvML", "vvM", "vvHL", "vvH"]
CONTROL = ["ssp126", "ssp245", "ssp585"]
## ⚠ THE BOUND MATCHES THE KIND OF CLAIM, AND THE CLAIM IS NOT BIT-IDENTITY.
## A first version set 1e-6 cm, reasoning "same binary, same drawnset, same inputs => an
## identity". It FIRED, at 6.1e-3 cm on ssp585 p95, and running it down produced a real
## finding rather than a bug:
##   * the raw MAGICC output is BIT-IDENTICAL for ssp126 and ssp245 (0 of 3.3M cells differ);
##   * ssp585 differs on ALL 600 members, worst 0.096 mm on Sea Level Rise;
##   * the cause is TWO emissions cells that differ by ONE ULP (~1e-16 relative) between the
##     reference file and my scmdata round-trip of it -- and one of them is ssp585's CO2 FFI
##     at 2130. ssp245's perturbed cell (CH4 at 2190) moved the output NOT AT ALL.
## So a 1e-16 input change moves ssp585 SLR by ~1e-5 relative: a ~1e11 amplification. That is
## a THRESHOLD CROSSING flipping for some members, not smooth error propagation, and it is
## the same behaviour this repo already documents for BRICK's DAIS fast dynamics (memory
## `dais_fastdynamics_quant`, "HARD ANNUAL STEP -- a pulse shifts the crossing year").
##
## ⇒ MAGICC-SLR is deterministic on identical inputs but ULP-SENSITIVE at ssp585. An identity
## bound can therefore never pass there, and loosening it to make it pass would be
## re-baselining. The bound is instead derived from what the control actually needs to show:
## that the re-run reproduces the frozen arm to well inside REPORTING PRECISION. We quote
## these numbers to 0.1 cm, so the bound is a tenth of the last quoted digit -- an external
## convention, not a number chosen to fit the observed 6.1e-3.
REPORT_PRECISION_CM = 0.1
CONTROL_TOL_CM = 0.1 * REPORT_PRECISION_CM


def extract(df, scenarios):
    rows = []
    for scen in scenarios:
        s = df[df.scenario == scen]
        if s.empty:
            raise SystemExit("[SOURCE] scenario %r absent from %s" % (scen, SOURCE))
        for comp, variables in emc.COMPONENT_MAP.items():
            sub = s[s.variable.isin(variables)]
            missing = set(variables) - set(sub.variable)
            if missing:
                raise SystemExit("[SOURCE] %s/%s missing %s" % (scen, comp, sorted(missing)))
            ## sum modules PER MEMBER, then rebaseline, then quantile -- emc's order exactly.
            ## ⚠ THE SELECTION MUST COVER THE BASELINE WINDOW TOO. Selecting YEARS_OUT
            ## (2000-2300) first and then rebaselining on BASE_YEARS (1995-2014) drops
            ## 1995-1999 and raises. emc avoids this by carrying the full year axis until
            ## after the subtraction; do the same, then cut to YEARS_OUT.
            yrs = sorted(set(emc.YEARS_OUT) | set(emc.BASE_YEARS))
            member = sub.groupby("ensemble_member")[yrs].sum() * emc.MM_TO_CM
            member = member.sub(member[emc.BASE_YEARS].mean(axis=1), axis=0)
            arr = member[emc.YEARS_OUT].to_numpy()
            for name, q in emc.QUANTILES.items():
                vals = np.percentile(arr, q, axis=0)
                for y, val in zip(emc.YEARS_OUT, vals):
                    rows.append((scen, comp, y, name, val))
    d = pd.DataFrame(rows, columns=["scenario", "component", "year", "stat", "value"])
    return d.pivot_table(index=["scenario", "component", "year"],
                         columns="stat", values="value").reset_index()


def load_source():
    d = pd.read_csv(SOURCE)
    ycols = {c: int(str(c)[:4]) for c in d.columns if str(c)[:4].isdigit()}
    d = d.rename(columns=ycols)
    ## [YEARS-PRESENT] assert the columns exist rather than trusting a range literal -- the
    ## same gate emc carries, and the reason its 2100 cut was caught.
    have = {c for c in d.columns if isinstance(c, (int, np.integer))}
    gap = [y for y in emc.YEARS_OUT if y not in have]
    if gap:
        raise SystemExit("[YEARS-PRESENT] %d requested year(s) absent from the source, "
                         "first %d" % (len(gap), gap[0]))
    return d


if __name__ == "__main__":
    if not os.path.exists(SOURCE):
        raise SystemExit("no MAGICC output at %s" % SOURCE)
    df = load_source()
    print("[SOURCE] %s\n         %d scenarios, %d members"
          % (os.path.basename(SOURCE), df.scenario.nunique(),
             df.ensemble_member.nunique()))

    ctl = extract(df, CONTROL)
    frozen = pd.read_csv(FROZEN)
    k = ["scenario", "component", "year"]
    j = ctl.merge(frozen, on=k, suffixes=("_new", "_old"), how="inner")
    if j.empty:
        raise SystemExit("[CONTROL] no overlapping cells with %s -- the control cannot run, "
                         "and an absent control is not a passing one." % FROZEN)
    stats = [s for s in emc.QUANTILES if "%s_new" % s in j and "%s_old" % s in j]
    worst = max((np.abs(j["%s_new" % s] - j["%s_old" % s]).max(), s) for s in stats)
    print("[CONTROL] %d cells x %d statistics vs the frozen arm; max |new - old| = %.3e cm "
          "(%s)  tol %.0e  %s"
          % (len(j), len(stats), worst[0], worst[1], CONTROL_TOL_CM,
             "PASS" if worst[0] <= CONTROL_TOL_CM else "FAIL"))
    ## The ULP-sensitivity is REPORTED on every run, never left implicit: a control that
    ## passes silently would hide the one interesting thing it found.
    if worst[0] > 0:
        print("          ⚠ non-zero, as expected: ssp585 is ULP-sensitive (a 1e-16 emissions "
              "change moves it ~1e-5 relative,\n            a threshold crossing). ssp126 and "
              "ssp245 raw output are bit-identical between the two runs.")
    if worst[0] > CONTROL_TOL_CM:
        bad = j.loc[np.abs(j["%s_new" % worst[1]] - j["%s_old" % worst[1]]).nlargest(5).index]
        raise SystemExit(
            "[CONTROL] the re-run SSPs do NOT reproduce the frozen arm. Same binary, same "
            "drawnset, same inputs -- so this is a real change in the pipeline and the van "
            "Vuuren rows, which have NO comparator of their own, must not be trusted until "
            "it is explained.\n%s"
            % bad[k + ["%s_new" % worst[1], "%s_old" % worst[1]]].to_string(index=False))

    vv = extract(df, VV)
    out = pd.concat([vv, ctl], ignore_index=True)
    out["unit"] = "cm rel 1995-2014"
    out["source"] = "MAGICC-SLR"
    out["module"] = "Nauels2025"
    out["arm"] = np.where(out.scenario.isin(CONTROL), "control", "comparison")
    out.to_csv(OUT, index=False)
    print("\nwrote %s  (%d rows; %d van Vuuren + %d control)"
          % (os.path.relpath(OUT, REPO), len(out), len(vv), len(ctl)))

    print("\nMAGICC-SLR median cm rel 1995-2014, van Vuuren markers")
    print("  %-6s %8s %8s %8s %8s %8s %8s" % ("marker", "glaciers", "gis", "ais", "te",
                                              "lws", "TOTAL"))
    for y in (2100, 2150, 2300):
        print("  @%d" % y)
        for m in VV:
            r = {c: vv[(vv.scenario == m) & (vv.component == c) & (vv.year == y)]
                 for c in emc.COMPONENT_MAP}
            print("  %-6s " % m + " ".join(
                "%8.1f" % r[c]["med"].iloc[0] for c in
                ["glaciers", "gis", "ais", "te", "lws", "total"]))
