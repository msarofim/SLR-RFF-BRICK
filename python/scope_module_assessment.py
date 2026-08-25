#!/usr/bin/env python3
"""
scope_module_assessment.py — STEPS 2, 3 and 4 of Marcus's five-step module
                             assessment, on the same four criteria as step 1.

Marcus 2026-08-25:
    "Step 1: how good is our AIS module relative to old BRICK and to the literature,
     recognizing that there are irreducible uncertainties. Step 2: Do the same test
     for glaciers. Step 3: Do the same test for Greenland, but with more flexibility
     because it isn't as important for global sea level. Step 4: Do the same test for
     the sum of all the components. Step 5: If the model passes steps 1-4, then redo
     the calibration test with the new model."

Criteria (Marcus 2026-08-14): (1) formulation at least as credible as BRICK 2.0's,
(2) hindcast at least as good, (3) projection spread at least as good (FACTS/MAGICC
match, or more physical), (4) the same under the joint calibration = step 5.

WHY THIS IS ONE PARAMETERISED SCRIPT AND NOT THREE COPIES OF THE STEP-1 TEMPLATE.
Every criterion-(2)/(3) number is now computed once, for every module, by
`python/bench_ladrillo.py`, and read from `outputs/bench_ladrillo_<TAG>.csv`. Three
copies of the metric code would drift, and the point of the benchmark is that step 2
and a re-run six months from now use the SAME metric. What is genuinely per-module is
criterion (1) -- the FORMULATION argument -- and that is a dossier of facts with
file:line provenance, below, not a computation.

⚠ CRITERION (1) IS A REAL QUESTION FOR GLACIERS AND GREENLAND, unlike AIS. The AIS
slot is never `replace!`d, so step 1 could pass criterion (1) by identity. The glacier
and Greenland slots ARE replaced (`brick_mengel.jl`), so those are genuinely different
formulations and the argument has to be made.

    source ~/climate-env/bin/activate
    python python/scope_module_assessment.py --module=glaciers   # step 2
    python python/scope_module_assessment.py --module=gis        # step 3
    python python/scope_module_assessment.py --module=total      # step 4
    python python/scope_module_assessment.py --all
Reads   outputs/bench_ladrillo_<TAG>.csv  (run bench_ladrillo.py first)
Writes  outputs/scope_module_assessment_<module>_<TAG>.csv
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
BENCH = os.path.join(REPO, "outputs", f"bench_ladrillo_{TAG}.csv")

STEP = {"ais": 1, "glaciers": 2, "gis": 3, "te": None, "lws": None, "total": 4}
LABEL = {"ais": "AIS", "glaciers": "glaciers", "gis": "Greenland",
         "te": "thermal expansion", "lws": "land water storage", "total": "THE SUM"}

# ---------------------------------------------------------------------------
# CRITERION (1): the FORMULATION dossier. Facts with provenance, not opinions.
# Each entry: (verdict, [lines]). Anything asserted here must name the file, the
# component, or the memory it comes from -- the standing "confidence words need
# receipts" rule applies to a formulation argument exactly as to a number.
# ---------------------------------------------------------------------------
FORMULATION = {
    "glaciers": ("A DIFFERENT AND MORE CONSTRAINED FORMULATION -- argued, not assumed", [
        "The glacier slot IS `replace!`d (brick_mengel.jl:57,117,173,238,267), so unlike AIS",
        "this is NOT BRICK 2.0's component. What is being compared:",
        "",
        "  BRICK 2.0   Wigley-Raper GSIC. dV/dt proportional to (T - teq), ONE reservoir, and",
        "              NO finite temperature-dependent equilibrium: for any sustained T > teq the",
        "              equilibrium is TOTAL loss (project_ssps_gsic_2300.jl header). `gsic_teq` is",
        "              not even sampled in its published posterior.",
        "  Ladrillo    glaciers_nu3: THREE reservoirs (R19 / SLOWP / FAST), each with a FINITE",
        "              temperature-dependent equilibrium S_eq,b = a_b(1 - exp(-b_b(T_b - T_off_b)))",
        "              and a Nauels-nu transient dS_b = min(kappa_b exc^nu_b, 1)(S_eq,b - S_b).",
        "              (glaciers_nu3_component.jl:1-20)",
        "",
        "THREE THINGS THE NEW FORM BUYS, each of which the old form cannot represent at all:",
        "  * A FINITE EQUILIBRIUM. Wigley-Raper commits every glacier to total loss above teq;",
        "    the observed and modelled world has glaciers that stabilise at a warmer level.",
        "  * REGIONAL EXHAUSTION. R19 (Antarctic periphery) holds most of the volume and melts",
        "    slowest; a single reservoir must trade the fast regions' rate against the slow",
        "    regions' volume, and cannot have both.",
        "  * A DRIVER THAT IS NOT GMST. Each block is driven by its own glacier-area temperature,",
        "    amp-spliced, and the parameter names deliberately do NOT match Mimi's shared",
        "    :model_global_surface_temperature so nothing auto-connects raw GMST.",
        "",
        "AND ITS PROVENANCE IS EXTERNAL, which is the part that makes it a credibility gain and",
        "not just a flexibility gain: the block structure and the equilibrium ladder come from",
        "GlacierMIP3 committed-loss rungs at 1.2/1.5/2.0/3.0 K (ladrillo_data.py:36-43,112),",
        "i.e. from glacier models, not from fitting our own sea-level history harder.",
        "",
        "⚠ COST OF THE NEW FORM: 15 sampled parameters against Wigley-Raper's 4. A three-reservoir",
        "  model fitted to ONE global cumulative series is under-determined by that series alone;",
        "  the GlacierMIP3 rungs are what identify it, so the formulation's credibility is exactly",
        "  as good as those rungs are.",
    ]),
    "gis": ("A DIFFERENT FORMULATION, JUSTIFIED BY A HINDCAST FEATURE THE OLD ONE CANNOT FIT", [
        "The Greenland slot IS `replace!`d. BRICK 2.0 runs SIMPLE (Bakker 2016); Ladrillo runs",
        "greenland_ab -> the two-stage cascade adopted 2026-08-23 (greenland_ab_component.jl:1-30).",
        "",
        "  A. REGIONAL DRIVER, not GMST: southern-Greenland (59-70N) land-masked temperature.",
        "     This is what closes the 1942-1982 window -- Greenland COOLED at -1.8 C/century from",
        "     1940 to 1990 while the globe warmed. A GMST-driven Greenland cannot reproduce that",
        "     window at all; it is a structural miss, not a calibration one.",
        "  B. TWO CHANNELS, fast surface-mass-balance and slow dynamic discharge, with the split",
        "     PINNED by the Mouginot 2019 SMB/discharge partition (73.5% surface) -- an external",
        "     observation, because the sea-level history cannot separate the channels itself.",
        "  The stock V/V0 damping is DROPPED: measured at 0.0 cm on the 2100 scenario spread",
        "  (only ~1% of the sheet is gone by 2100) and it has the wrong sign physically.",
        "",
        "⚠ MARCUS'S 'MORE FLEXIBILITY' HAS A NUMBER. Greenland is 6.0% of the ssp585@2300 joint",
        "  band and 8.8% of the ADDRESSABLE uncertainty; AIS is 82.7%. Step 3 should not consume",
        "  step-1-sized effort, and a Greenland defect worth <1 cm at 2100 is not worth reopening",
        "  a CLOSED module for (closed 2026-08-24).",
        "",
        "⚠ CARRIED FORWARD, NOT RE-LITIGATED: the 2100 projection runs 1.31-1.32x fast against",
        "  ISMIP6, that bias is the AMP LAW, and it is HINDCAST-INERT -- so it does not show up in",
        "  criterion (2) below and must not be read as absent because criterion (2) passes.",
    ]),
    "total": ("NOT A FIFTH MODULE -- and NOT the conjunction of the other four verdicts", [
        "The total is the sum of five components plus their covariance. [SUM] in",
        "julia/scope_slr_fair_uncertainty.jl checks the decomposition closes PER DRAW (~2e-13 cm),",
        "so there is no bookkeeping question. The question is a different one:",
        "",
        "⚠ THE COVARIANCE RESIDUAL IS +18% TO +34%. A p05-p95 spread is NOT additive, so the",
        "  components' spreads do not sum to the total's, and a total-level PASS can hide two",
        "  compensating component errors while a total-level FAIL can be produced by components",
        "  that individually pass. The total is therefore scored ON ITS OWN below, and its verdict",
        "  is NOT inherited from steps 1-3 in either direction.",
        "",
        "⚠ AND IT IS THE ONLY LEVEL WITH A DIRECT OBSERVATIONAL TARGET OF ITS OWN: the Dangendorf",
        "  2024 GMSL reconstruction, whose 1-sigma (1.54 cm) is 3-9x wider than any component's.",
        "  A total that matches Dangendorf is a much weaker statement than four components that",
        "  each match their own target.",
    ]),
    "te": ("BRICK 2.0's COMPONENT, UNMODIFIED -- like AIS, criterion (1) holds by identity", [
        "The thermal-expansion slot is never `replace!`d. Both arms run the same MimiBRICK",
        "component on the same FaIR OHC. Anything that differs is calibration or forcing.",
    ]),
}

# The share of the ssp585@2300 JOINT band, and of the ADDRESSABLE (non-forcing) part,
# that each module carries. This is what "how much does this module matter" means, and
# it is what Marcus's step-3 'more flexibility' instruction is quantified by.
# Source: handoff_2026-08-25_fair_uncertainty.md addendum D (`addressable_not_band_growth`).
ADDRESSABLE_585_2300 = {"ais": 0.827, "gis": 0.088, "te": 0.050, "glaciers": 0.035}
ADDRESSABLE_126_2100 = {"glaciers": 0.401, "te": 0.226, "ais": 0.219, "gis": 0.154}


def assess(mod, b, rows):
    lab = LABEL[mod]
    step = STEP[mod]
    hdr = f"STEP {step} — " if step else "SUPPORTING — "
    print("\n" + "=" * 104)
    print(f"{hdr}{lab.upper()} MODULE ASSESSMENT ({TAG}) vs BRICK 2.0 and the literature")
    print("=" * 104)
    m = b[b.component == mod]

    def emit(block, key, value, note, verdict=""):
        rows.append(dict(module=mod, block=block, key=key, value=value,
                         note=note, verdict=verdict))

    # ------------------------------------------------------------ criterion 1
    verdict1, lines = FORMULATION.get(mod, ("(no dossier)", []))
    print(f"\n[1] FORMULATION — is it at least as credible as BRICK 2.0's?   => {verdict1}")
    for ln in lines:
        print("    " + ln)
    emit("formulation", "verdict", np.nan, verdict1, verdict1.split(" --")[0])

    # ------------------------------------------------------------ criterion 2
    print("\n[2] HINDCAST — the full observational period, scaled to this component's own "
          "target 1-sigma")
    h = m[(m.block == "H") & (m.metric.str.startswith("hindcast"))]
    if h.empty:
        print("    (no hindcast rows -- this component has no observational target)")
    else:
        print(f"    {'window':12s} {'arm':12s} {'RMSE cm':>9s} {'RMSE sd':>9s}  note")
        for _, r in h.iterrows():
            print(f"    {r.metric.split('/')[1]:12s} {r.arm:12s} {r.value:9.4f} "
                  f"{r.value_sigma:9.2f}  {r.note}")
            emit("hindcast", f"{r.metric}/{r.arm}", r.value, r.note, r.verdict)
        rr = m[(m.block == "H") & (m.metric.str.startswith("rmse_ratio"))]
        print("\n    RMSE ratio, candidate / comparator (<1 = candidate closer to the obs):")
        for _, r in rr.iterrows():
            print(f"      {r.metric.split('/')[1]:12s} {r.arm:26s} {r.value:6.2f}x  {r.verdict}")
            emit("hindcast_ratio", f"{r.metric}/{r.arm}", r.value, r.note, r.verdict)
        # THE SCALED READING IS THE ONE THAT DECIDES. A raw RMSE ratio of 1.01x and a
        # raw ratio of 11.7 sigma are the same number in different units of what the
        # observations can actually resolve.
        both = h[h.arm.isin([TAG, "BRICK 2.0"])]
        worst_us = both[both.arm == TAG].value_sigma.abs().max()
        worst_them = both[both.arm == "BRICK 2.0"].value_sigma.abs().max()
        print(f"\n    worst window, in target sigma: {TAG} {worst_us:.2f} sd, "
              f"BRICK 2.0 {worst_them:.2f} sd")
        print("    ⚠ IN-SAMPLE for Ladrillo, OUT-OF-SAMPLE for BRICK 2.0 -- this RANKS IN ONE")
        print("      DIRECTION ONLY. It can REJECT an arm that misses by many sigma; a small")
        print("      fitted bias is not evidence of skill.")
        emit("hindcast", "worst_sigma_ours", worst_us, "max |RMSE| in target sigma across windows")
        emit("hindcast", "worst_sigma_brick20", worst_them, "max |RMSE| in target sigma")

    # ---------------------------------------------------- criterion 2b: slope
    r_ = m[m.block == "R"]
    if not r_.empty:
        print("\n[2b] RATE AND ACCELERATION — the level can be right while the slope is wrong")
        for _, r in r_.iterrows():
            print(f"    {r.metric:26s} {r.arm:14s} {r.value:11.5g} {r.unit:8s} "
                  f"{'' if not np.isfinite(r.value_sigma) else f'z={r.value_sigma:+6.2f}'}  "
                  f"{r.verdict}")
            emit("rate", f"{r.metric}/{r.arm}", r.value, r.note, r.verdict)

    # ------------------------------------------------------------ criterion 3
    print("\n[3] PROJECTION — level and spread vs FACTS / MAGICC-SLR / BRICK 2.0, "
          "on the JOINT band")
    p = m[(m.block == "P") & (m.metric.str.endswith("_vs_lit"))]
    if p.empty:
        print("    (no literature comparator for this component)")
    else:
        for _, r in p.iterrows():
            print(f"    {r.scenario} @{int(r.horizon)}  {r.metric:14s} {r.value:6.3f} "
                  f"{r.unit:14s} {r.verdict:20s} {r.note}")
            emit("projection", f"{r.scenario}_{int(r.horizon)}_{r.metric}", r.value,
                 r.note, r.verdict)
    s = m[(m.block == "S") & (m.arm == TAG)]
    if not s.empty:
        print("\n    SCENARIO SEPARATION (ssp585/ssp126 median). Marcus 2026-08-25: lying "
              "BETWEEN\n    FACTS and MAGICC is acceptable, so the verdict is bracket "
              "membership.")
        for _, r in s.iterrows():
            print(f"    @{int(r.horizon)}  {r.value:6.2f}x   {r.verdict:12s} {r.note}")
            emit("separation", f"{int(r.horizon)}", r.value, r.note, r.verdict)

    # ------------------------------------------------------------ criterion 4
    print("\n[4] HOW MUCH THIS MODULE MATTERS, and how much of its width evidence could move")
    a585 = ADDRESSABLE_585_2300.get(mod)
    a126 = ADDRESSABLE_126_2100.get(mod)
    if a585 is not None:
        print(f"    share of ADDRESSABLE uncertainty: ssp585@2300 {a585:.1%}, "
              f"ssp126@2100 {a126:.1%}")
        emit("priority", "addressable_ssp585_2300", a585, "share of the non-forcing spread")
        emit("priority", "addressable_ssp126_2100", a126, "share of the non-forcing spread")
    if mod == "ais":
        print("    78% of the ssp585 2300 band is antarctic_lambda's PALEO PRIOR -- most of the")
        print("    width is not an inference, and narrowing it would be a WORSE model.")
    if mod == "glaciers":
        print("    ⚠ THE TRANSIENT GLOBAL-SLE LITERATURE TARGET DOES NOT EXIST IN THIS REPO.")
        print("      What we score against is FACTS ar5glaciers/emuglaciers + MAGICC-SLR, three")
        print("      comparators. GlacierMIP3 is in the repo but as a COMMITTED-loss ladder at")
        print("      warming levels (ladrillo_data.py), which is already IN the likelihood and so")
        print("      is not an independent check; and the GloGEM/OGGM archives are scoped in")
        print("      python/scope_glacier_model_constraints.py as per-BLOCK mass-loss percentages,")
        print("      NOT global cm. Assembling a global-cm GloGEM/OGGM target is the one piece of")
        print("      real work step 2 identifies and does not do.")
    if mod == "gis":
        print("    ⚠ HINDCAST-INERT DEFECT CARRIED FORWARD: the 2100 projection is 1.31-1.32x")
        print("      fast against ISMIP6 and the bias is the AMP LAW. Criterion (2) cannot see")
        print("      it. Do not read a criterion-(2) PASS as its absence.")
    if mod == "total":
        print("    ⚠ The covariance residual is +18% to +34%: this verdict is NOT the conjunction")
        print("      of steps 1-3, in either direction.")
    return rows


def main():
    if not os.path.exists(BENCH):
        raise SystemExit(f"missing {os.path.relpath(BENCH, REPO)} -- run "
                         f"`python python/bench_ladrillo.py --tag={TAG}` first")
    b = pd.read_csv(BENCH)
    args = sys.argv[1:]
    mods = ([a[len("--module="):] for a in args if a.startswith("--module=")] or
            (["glaciers", "gis", "total"] if "--all" in args else []))
    if not mods:
        raise SystemExit(__doc__)
    for mod in mods:
        rows = assess(mod, b, [])
        out = os.path.join(REPO, "outputs", f"scope_module_assessment_{mod}_{TAG}.csv")
        pd.DataFrame(rows).to_csv(out, index=False)
        print(f"\nwrote {os.path.relpath(out, REPO)}")


if __name__ == "__main__":
    main()
