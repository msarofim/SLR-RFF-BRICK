#!/usr/bin/env python3
"""
ladrillo_model_comparison.py — Ladrillo against FACTS, MAGICC-SLR, and BRICK 2.0.

Puts the four projection sources on one basis (cm, re-referenced to 1995-2014,
per SSP and component) and reports medians with 17-83% bands at 2100 and 2150,
plus the scenario-spread diagnostic (SSP1-2.6 -> SSP5-8.5 median difference per
component), which is what exposes a glacier module that saturates.

Sources
  Ladrillo    outputs/ssps_components_2300_<TAG>.csv  (--tag=, default L10)
              L10 = Ladrillo 1.0; L11 = the D1+D2 change set accepted 2026-08-15.
              2000 draws, FaIR-mean forcing per SSP, Greenland A+B with the
              amp(GMST) law.
  BRICK 2.0   outputs/ssps_components_2300_oldbrick.csv  (REPOINTED 2026-08-27)
              Stock MimiBRICK v2.0.0 on its own post-PR#93 posterior, ALL SIX
              COMPONENTS to 2300 with p17/p83. Was ssps_gsic_2300.csv = glaciers
              only at 5-95%; see load_brick20 for why that was wrong and why
              repointing does not affect benchmark scoring.
  MAGICC-SLR  data/comparison/magicc_nauels_components.csv
              MAGICC v7.5.3 + Nauels 2025 SLR, 600-member AR6 drawnset,
              extracted by python/extract_magicc_components.py. ⚠ RUNS TO 2305 --
              this line said 'Ends at 2100' until 2026-08-29; 2300 was added on
              2026-08-25 (see MAGICC_CSV note below) and the docstring was not updated.
  FACTS       outputs/facts_components_shared_n200.csv
              global.shared.{ssp126,ssp245,ssp585}.n200, per module, on the SHARED
              injected climate (FaIR 2.2.4 calib 1.6.0 + CMIP7, the same 841-config
              cubes / 2014 splice / 1995-2014 reference as Ladrillo and BRICK 2.0),
              rel. baseyear 2005 (~ the 1995-2014 mean; the standing
              MAGICC-comparison convention treats the two as comparable).
              ⚠ SAME MACHINERY AS THE VAN VUUREN ARM since 2026-08-31 -- one builder,
              one config generator, one extractor, one climate convention across both
              scenario sets. It previously read FACTS-INTERNAL FaIR 1.6.4, which made
              the FACTS column straddle two conventions between the two sets.

BAND CAVEAT ⚠ CORRECTED 2026-08-31. This docstring said "Ladrillo and BRICK 2.0 run
on MEAN climate forcing, so their bands are POSTERIOR-PARAMETER spread only ...
MEDIANS are comparable; band WIDTHS are not." That has been FALSE since 2026-08-30:
both joint arms propagate their posteriors across the SAME 841 FaIR configs, so all
four bands carry climate uncertainty and the widths ARE comparable. Whether a given
ROW's band qualifies is decided per row by its own `band_basis` via
ladrillo_figs.band_is_comparable -- never by a source-name list, which is exactly the
constant that went stale here and suppressed three of four bands on the figure.

  python3 python/ladrillo_model_comparison.py [--tag=L11]
Writes outputs/ladrillo_model_comparison_<TAG>{,_spread}.csv
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gis_targets  # noqa: E402
from draws_io import draws_exists, read_draws  # noqa: E402

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The posterior TAG drives the input file, the OUTPUT filenames, and the module
# column of every row emitted, so a run on L11 cannot overwrite or be mistaken
# for L10. Both tags are suffixed symmetrically -- there is no bare-name default
# that silently means one vintage.
LADRILLO_TAG = next((a[len("--tag="):] for a in sys.argv[1:]
                     if a.startswith("--tag=")), "L10")
## WHICH ARM. The tap is part of the module (2026-08-23), so the TAPPED deliverable is
## what this comparison reports unless --no-tap is passed. Resolved through
## gis_targets.ssps_csv, which rebuilds the cell-encoded filename from the same Julia
## GIS_TAP_CELL the projection driver's own TAG derives from -- this script used to
## build the path by f-string and could therefore only ever see the untapped file,
## which is why no comparison had ever been produced for the shipped model.
## The ARM IS IN THE OUTPUT NAME: an untapped comparison must not be mistakable for a
## tapped one on disk, the same rule the projections themselves follow.
TAPPED = "--no-tap" not in sys.argv[1:]
LADRILLO_CSV = gis_targets.ssps_csv(LADRILLO_TAG, tapped=TAPPED)
ARM_TAG = "" if TAPPED else "_notap"
OUT = os.path.join(REPO, f"outputs/ladrillo_model_comparison_{LADRILLO_TAG}{ARM_TAG}.csv")
BRICK20_GSIC_CSV = os.path.join(REPO, "outputs/ssps_gsic_2300.csv")   # superseded, see load_brick20
BRICK20_COMPONENTS_CSV = os.path.join(REPO, "outputs/ssps_components_2300_oldbrick.csv")
MAGICC_CSV = os.path.join(REPO, "data/comparison/magicc_nauels_components.csv")
## ⚠ THE FACTS ARM MOVED ONTO THE SHARED MACHINERY, 2026-08-31 (Marcus: "everything using the
## same machinery where possible"). It used to read outputs/facts_components_n200.csv, from
## experiments/global.coupling.<ssp>.n200 -- FACTS driven by its OWN INTERNAL FaIR 1.6.4. The
## van Vuuren arm was necessarily built the other way (injected external climate), so the FACTS
## COLUMN straddled two climate-driver conventions across the two scenario sets.
##
## It now reads the same file the van Vuuren figure does, produced by the same builder, the same
## config generator and the same extractor:
##   facts/build_shared_climate_nc.py -> build_shared_configs.py -> extract_facts_shared_components.py
## so the FACTS column is on ONE convention everywhere: FaIR 2.2.4 calib 1.6.0 + CMIP7, the same
## 841-config cubes, the same 2014 splice and 1995-2014 reference as Ladrillo and BRICK 2.0.
##
## ⚠ THIS MOVES THE COMPARATOR, and the frozen arm under benchmark/reference/_fixed/ exists
## precisely to make that visible rather than silent. Expect the [LIT] gate to report the FACTS
## rows as moved until the arm is deliberately RE-FROZEN with a note saying why. Do not re-freeze
## to silence it; re-freeze because the driver changed on purpose.
##
## The three SSPs keep emuAIS / emuGrIS / emuglaciers and wf1e/wf2e/wf3e: emulandice is
## per-SSP-TRAINED, so it is valid here and only excluded on the van Vuuren markers. Dropping
## those comparators would have been a real loss disguised as a plumbing change.
FACTS_CSV = os.path.join(REPO, "outputs/facts_components_shared_n200.csv")

## 2300 added 2026-08-25: MAGICC-SLR was always run to 2305, and only our own extractor
## cut it at 2100 (`extract_magicc_components.py` [YEARS-PRESENT]). FACTS still stops at
## 2150, so 2300 carries ONE comparator -- which the benchmark flags rather than hides.
HORIZONS = [2100, 2150, 2300]
SCENARIOS = ["ssp126", "ssp245", "ssp585"]      # the three all four sources share
LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
COMPONENTS = ["glaciers", "gis", "ais", "te", "lws", "total"]
SPREAD_LO, SPREAD_HI = "ssp126", "ssp585"
COLS = ["source", "module", "scenario", "component", "year", "med", "p05", "p17", "p83", "p95",
        "band_basis"]

## ---------------------------------------------------------------------------
## BAND PROVENANCE (2026-08-29). Every width statement downstream depends on WHICH
## band each row carries, so it is now a COLUMN, not a footnote.
##
## Ladrillo is reported on the JOINT arm (posterior parameters x 841 FaIR configs)
## wherever that arm is VALID, because MAGICC and FACTS carry climate uncertainty and
## only the joint band is like-for-like against them (`like_for_like_forcing`).
##
## ⚠ WHERE IT IS NOT VALID, AND WHY THE GATE IS NOT STATISTICAL.
## scope_slr_fair_uncertainty.jl has NO tap support (grepped: no "tap" in the file) --
## it projects the UNTAPPED Greenland, while this comparison reports the TAPPED
## deliverable. So the joint draws are the wrong ARM wherever the tap fires, and
## substituting them there would silently drop 41 cm of GIS at ssp585/2300.
##
## The gate therefore reads the CAUSE, not a proxy: the exact per-cell tap effect,
## differenced from the two SHIPPED files we already have. A first version compared the
## joint driver's own FIXED arm against this table and accepted a cell when the gap sat
## inside the median's sampling error -- that gate had NO POWER on total/ssp585/2150,
## where a real 1.31 cm tap offset is smaller than the total's own Monte-Carlo noise
## (`no_power_null`). An exact difference has no noise floor and needs no tolerance.
TAP_EPS      = 0.0        # cm; a cell is joint-eligible only if the tap effect is EXACTLY zero
BASIS_JOINT  = "joint (posterior params x FaIR forcing)"
BASIS_TAPPED = "FIXED (tapped arm; no joint band exists)"
BASIS_FIXED  = "fixed (posterior params, mean forcing)"
BASIS_CLIM   = "climate + parameter"
JOINT_GLOB   = "outputs/scope_slr_fairunc_draws_{ssp}_spliced_{tag}.csv"
## The TAPPED joint arm, produced by scope_slr_fair_uncertainty.jl --tap (added
## 2026-08-30). When present it is PREFERRED, because it is the same Greenland arm this
## comparison reports -- and then the tap gate has nothing left to hold.
JOINT_TAP_GLOB = ("outputs/scope_slr_fairunc_draws_{ssp}_spliced_{tag}"
                  "_tap4p69K_V5p64m_tau800.csv")
## BRICK 2.0's OWN joint band (scope_slr_fairunc_oldbrick.jl, 2026-08-30). Built on the
## SAME cubes, the same 2014 splice pivot, the same 1995-2014 re-reference and the same
## PAIR_SEED as the Ladrillo joint arm -- otherwise the two would not be comparable and
## the point of building it would be lost. ⚠ An earlier draft of the model document said
## BRICK 2.0 "can never be made joint"; `set_forcing!` takes an arbitrary (gmst, ohc)
## pair, so that was simply wrong.
BRICK_JOINT_GLOB = "outputs/scope_slr_fairunc_draws_{ssp}_spliced_oldbrick.csv"
BASIS_JOINT_B20  = "joint (BRICK 2.0 posterior x FaIR forcing)"


def _rows(df, source, module_col=None, module=None, basis=""):
    out = df.copy()
    out["source"] = source
    out["module"] = out[module_col] if module_col else module
    for q in ("p05", "p17", "p83", "p95"):
        if q not in out:
            out[q] = float("nan")
    if "band_basis" not in out:
        out["band_basis"] = basis
    return out[COLS]


def _tap_effect():
    """EXACT per-cell |tapped - untapped| median, from the two shipped files. No noise,
    so no tolerance is needed and none is invented. Returns {(scenario, component, year): cm}."""
    import gis_targets as _gt
    k = ["year", "ssp", "component"]
    unt = pd.read_csv(_gt.ssps_csv(LADRILLO_TAG, False)).set_index(k)
    tap = pd.read_csv(_gt.ssps_csv(LADRILLO_TAG, True)).set_index(k)
    j = tap[["med"]].join(unt[["med"]], rsuffix="_u").reset_index()
    j["scenario"] = j.ssp.map({v: k2 for k2, v in LABEL.items()})
    return {(r.scenario, r.component, int(r.year)): abs(r.med - r.med_u)
            for r in j.itertuples()}


def _joint_bands():
    """Per-cell joint-arm quantiles from the paired (posterior x FaIR config) draws.

    Returns (bands, tapped) where `tapped` is True only if EVERY scenario supplied a
    tapped file. A partial set would mix arms across scenarios, which is worse than
    using none of it, so it is treated as untapped."""
    out, tap_seen, n_ssp = {}, 0, 0
    for ssp in SCENARIOS:
        ft = os.path.join(REPO, JOINT_TAP_GLOB.format(ssp=ssp, tag=LADRILLO_TAG))
        fu = os.path.join(REPO, JOINT_GLOB.format(ssp=ssp, tag=LADRILLO_TAG))
        if draws_exists(ft):
            f, tap_seen = ft, tap_seen + 1
        elif draws_exists(fu):
            f = fu
        else:
            continue
        n_ssp += 1
        d = read_draws(f)
        d = d[d.arm == "joint"]
        for (comp, hz), g in d.groupby(["component", "horizon"]):
            v = g.value_cm.values
            q = np.percentile(v, [5, 17, 50, 83, 95])
            out[(ssp, comp, int(hz))] = dict(p05=q[0], p17=q[1], med=q[2],
                                             p83=q[3], p95=q[4], n=len(v))
    tapped = (tap_seen == len(SCENARIOS))
    if 0 < tap_seen < len(SCENARIOS):
        print(f"[BAND] ⚠ tapped joint files found for only {tap_seen}/{len(SCENARIOS)} "
              f"scenarios -- treating the whole set as UNTAPPED rather than mixing arms.")
    return out, tapped


def load_ladrillo():
    """Ladrillo on the JOINT arm wherever that arm is valid, FIXED (tapped) where it is
    not. The gate is the exact tap effect -- see the BAND PROVENANCE note above."""
    df = pd.read_csv(LADRILLO_CSV)
    df["scenario"] = df.ssp.map({v: k for k, v in LABEL.items()})
    df = _rows(df, "Ladrillo", module=LADRILLO_TAG, basis=BASIS_TAPPED)
    tap, (jb, jb_tapped) = _tap_effect(), _joint_bands()
    if jb_tapped:
        # the joint arm IS the tapped arm now, so the tap can no longer disqualify a cell
        tap = {k: 0.0 for k in tap}
    n_j = n_t = n_missing = 0
    for i, r in df.iterrows():
        key = (r.scenario, r.component, int(r.year))
        te = tap.get(key)
        if te is None or te > TAP_EPS:            # tap fires (or unknown) -> keep FIXED
            n_t += 1; continue
        b = jb.get(key)
        if b is None:
            n_missing += 1; continue              # no joint draw for this cell -> keep FIXED
        for q in ("med", "p05", "p17", "p83", "p95"):
            df.at[i, q] = b[q]
        df.at[i, "band_basis"] = BASIS_JOINT
        n_j += 1
    held = sorted(k for k, v in tap.items() if v > TAP_EPS and k[0] in SCENARIOS
                  and k[1] in COMPONENTS and k[2] in HORIZONS)
    rep = df[df.scenario.isin(SCENARIOS) & df.component.isin(COMPONENTS)
             & df.year.isin(HORIZONS)]
    print(f"[BAND] joint arm is {'TAPPED (matches this comparison)' if jb_tapped else 'UNTAPPED'}")
    print(f"[BAND] Ladrillo REPORTED cells: {(rep.band_basis == BASIS_JOINT).sum()} on the "
          f"JOINT arm, {(rep.band_basis != BASIS_JOINT).sum()} held on FIXED, of {len(rep)}. "
          f"(Non-horizon years are never reported and are left on FIXED.)")
    if held:
        print("[BAND] HELD ON FIXED because the joint driver has no tap support "
              "(scope_slr_fair_uncertainty.jl); substituting there would drop the tap:")
        for k in held:
            print(f"          {k[1]:>8s} {k[0]} {k[2]}   tap effect {tap[k]:7.3f} cm")
    return df


def load_brick20():
    """Stock BRICK 2.0, ALL SIX COMPONENTS to 2300, with p17/p83.

    REPOINTED 2026-08-27 (Marcus). This used to read outputs/ssps_gsic_2300.csv — GLACIERS
    ONLY, and lo/hi = 5-95% because that file carries no p17/p83. Every AIS / Greenland / TE /
    LWS / total cell of the comparison was therefore BLANK for the reference model, and its one
    populated column reported a 90% interval alongside everyone else's 66%.

    julia/project_ssps_components_oldbrick.jl was written specifically to fix this ("every AIS /
    Greenland / TE / total cell of the comparison therefore had a BLANK where the reference model
    should be") and emits all six components to 2300 WITH p17/p83, on the same posterior, the
    same FaIR mean forcing, and the same 1995-2014 re-reference as Ladrillo. bench_ladrillo.py
    has read it since it was written; this script was never repointed. No re-run was needed.

    ⚠ BENCHMARK IMPACT: NONE. The frozen benchmark/reference/_fixed/literature_rows.csv carries
    only FACTS and MAGICC-SLR rows — no BRICK 2.0 — and bench_ladrillo.py takes BRICK 2.0 from
    `brick20_projection`, which is ALREADY this file. Scoring is untouched.
    ⚠ The manifest records a sha256 for this script's OUTPUT under `literature`; that hash will
    now differ. That is the manifest doing its job — making a changed input VISIBLE rather than
    silently re-scoring — not a failure. Re-freeze when convenient."""
    df = pd.read_csv(BRICK20_COMPONENTS_CSV)
    df["scenario"] = df.ssp.map({v: k for k, v in LABEL.items()})
    df = df.dropna(subset=["scenario"])
    df = _rows(df, "BRICK 2.0", basis=BASIS_FIXED, module="BRICK2.0")
    # substitute the joint arm wherever it exists. BRICK 2.0 has NO Greenland tap, so
    # unlike Ladrillo there is no arm to gate on -- the joint driver's own [CONTROL]
    # (its fixed arm vs the shipped panel, on the SAME thinning) is the check.
    jb = {}
    for ssp in SCENARIOS:
        f = os.path.join(REPO, BRICK_JOINT_GLOB.format(ssp=ssp))
        if not draws_exists(f):
            continue
        d = read_draws(f)
        d = d[d.arm == "joint"]
        for (comp, hz), g in d.groupby(["component", "horizon"]):
            q = np.percentile(g.value_cm.values, [5, 17, 50, 83, 95])
            jb[(ssp, comp, int(hz))] = dict(p05=q[0], p17=q[1], med=q[2], p83=q[3], p95=q[4])
    n_j = 0
    for i, r in df.iterrows():
        b = jb.get((r.scenario, r.component, int(r.year)))
        if b is None:
            continue
        for q in ("med", "p05", "p17", "p83", "p95"):
            df.at[i, q] = b[q]
        df.at[i, "band_basis"] = BASIS_JOINT_B20
        n_j += 1
    rep = df[df.scenario.isin(SCENARIOS) & df.component.isin(COMPONENTS)
             & df.year.isin(HORIZONS)]
    print(f"[BAND] BRICK 2.0 REPORTED cells: {(rep.band_basis == BASIS_JOINT_B20).sum()} on "
          f"its OWN JOINT arm, {(rep.band_basis != BASIS_JOINT_B20).sum()} on FIXED, "
          f"of {len(rep)}.")
    return df


def load_magicc():
    return _rows(pd.read_csv(MAGICC_CSV), "MAGICC-SLR", module="Nauels2025",
                 basis=BASIS_CLIM)


def load_facts():
    return _rows(pd.read_csv(FACTS_CSV), "FACTS", module_col="module",
                 basis=BASIS_CLIM)


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
    print("BAND BASIS is now a COLUMN, per row. Ladrillo is on the JOINT arm (posterior "
          "params x FaIR\n  forcing) wherever the Greenland tap does not fire, which makes it "
          "LIKE-FOR-LIKE against MAGICC\n  and FACTS. BRICK 2.0 is posterior-parameter spread "
          "on MEAN forcing and can never be joint, so\n  its WIDTHS are not comparable to any "
          "other source here -- compare its MEDIANS only.\n  ⚠ ssp585 gis/total/ais at "
          "2150 and 2300 are HELD ON FIXED: the joint driver has no tap\n  support, so no "
          "joint band exists for the tapped arm. Those rows say so in band_basis.")

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
