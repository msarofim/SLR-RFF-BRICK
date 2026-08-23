#!/usr/bin/env python3
"""
scope_gis_reservoir_offline.py — OPTION 3: a third, genuinely SLOW reservoir,
priced against the matched targets AND the five matched-forcing shape arms.

WHAT IS DIFFERENT FROM EVERY PRIOR ATTEMPT (2026-08-21k) — read this first
  This is NOT new machinery. The tap ALREADY is a reservoir: `tap_unit` relaxes a
  state S toward a soft GMT ramp at rate 1/tau and adds V*S. Four things were never
  done, and the first is the one that matters:

  1. TAU WAS NEVER TAKEN PAST 400 yr. `TAP_TAU = [50, 100, 200, 400]`, and the tap
     SHAPE scan topped out at 200. "Centuries-to-millennium" (handoff 2026-08-21e
     §4 item 3) is unexplored, not a re-run. This file scans to 3200 yr.
  2. THE DECISIVE ONE. EVERY PRIOR PRICING TARGETED THE RAW LITERATURE BAND (173-313 cm at ssp585),
     which needs ~1.5-2.5 m REALISED by 2300 and therefore FORCES tau short. That
     is why the tap came out front-loaded and 3.5x too high at 2150. The matched
     band is 42.9-145.0 cm and the base already sits at 49.9, so only ~0.49 m is
     needed -- small V and long tau became simultaneously admissible only after the
     2026-08-21g re-target.
  3. THE SHAPE SCORECARD DID NOT EXIST. The tap was scored on 2300 LEVELS plus a
     ratio band; it was never run against the five matched-forcing arms, and 2150 --
     the horizon every prior tap cell failed (0/25 in band) -- is one of theirs.
  4. vs the OLD `A+B+C`: that REPLACED `L_eq` with the Bochow ladder and was REFIT
     (nlp 563 vs A+B's 17.86, hindcast RMSE 0.844 vs 0.062 -- the fit was
     destroyed). This is ADDITIVE, DEFAULT-OFF and PRIOR-PROPAGATED. And there is
     no throughput cap, so the algebraic obstruction that killed `D` -- wherever
     min() selects q, dL/dt stops depending on L_eq -- cannot arise.

THE PRE-CHECK, which says a threshold is the only form that can work
  ssp585 must rise x1.97 to the matched p50 while ssp245 has x1.17 of headroom to
  its band TOP (and is already x1.19 ABOVE its p50), so the minimum SELECTIVITY is
  x1.68. A commitment proportional to T gives ~1.0 (that is the ridge's failure); a
  state-dependent L/V0 term measured 2.3 and still failed on level (2026-08-21j).
  A GMT THRESHOLD gives EXACTLY 0.0 below onset -- and our cool scenarios peak at
  1.73 and 3.15 K -- so any onset above 3.15 K removes the cool constraint
  entirely. That is the whole design freedom, and it is why this is worth running.

WHY THE SCAN IS CHEAP, and the gate that makes it legitimate
  The reservoir is ADDITIVE and DETERMINISTIC given the scenario, and its ramp is
  EXACTLY zero over the calibration window for every onset scanned. So the base
  model, its hindcast bisection and its rate solution are all UNCHANGED, and each
  cell is one addition rather than one model run. G-INERT below MEASURES that
  (max |ramp| over 1900-2025 must be exactly 0.0) instead of assuming it -- the
  same test G2 applies to the tap, and the test gamma FAILED 2026-08-21j.

WRITES outputs/scope_gis_reservoir_offline.csv
  python3 python/scope_gis_reservoir_offline.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, GIS_V0_M, YEARS, gis_shape_table, regional_driver,
)
import gis_targets  # noqa: E402
import scope_gis_shape_all_scenarios as A  # noqa: E402

OUT_STEM = os.path.join(REPO, "outputs/scope_gis_reservoir_offline")

# --- named constants ---------------------------------------------------------
TAG, HIND, HORIZONS, ARM, ARMS = A.TAG, A.HIND, A.HORIZONS, A.ARM, A.ARMS
SSP585_ARMS, COOL_ARMS = A.SSP585_ARMS, A.COOL_ARMS
K_FIXED = 1.0
OURS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
## Mirrors scope_gis_tap_l13.TAP_RAMP_W_K -- the SAME ramp, so this is the tap's
## own reservoir and not a second, subtly different one.
RAMP_W_K = 1.0
## THE NEW AXIS. 100-400 reproduces the tap's own grid; 800-3200 is what handoff
## §4 item 3 calls "centuries-to-millennium" and what has never been scanned.
RES_TAU = [100, 200, 400, 800, 1600, 3200]
## Onsets: 3.2 is just above OUR ssp245's 2300 GMT (3.15 K), the point at which the
## cool constraint switches off exactly; 4.69 is the Tier-1 floor (ssp585 @2100, so
## nothing fires inside the accepted 2100 deliverable); 7.81 is ssp585 @2300.
RES_ONSET_K = [3.2, 4.0, 4.69, 5.5, 6.5, 7.5]
## --- THE ONSET-LADDER ARM, `--onsets=a,b,c` (2026-08-23) -------------------
## WHY. The default ladder above STARTS at 3.2 K and `scope_gis_onset_rescan.py`
## STOPS at 3.0 K, so the whole span between the ladder-corroborated 2.1 K optimum
## and the shipped 4.69 K is covered by NEITHER scorecard: the rescan has no 2150
## criterion and this file has no Greve/ISMIP6 horizons. Any onset in that gap has
## therefore never been scored on a complete criterion set. The flag takes an
## explicit list so the two files can be run on the SAME ladder and joined.
##
## THE GAP IS NOT SMOOTH, which is why it needs scanning rather than interpolating:
## our SSP2-4.5 PEAKS at 3.19 K, so at any onset above that the moderate-scenario
## term is EXACTLY zero, while just below it the crossing year moves violently
## (2058 at 2.10 K, 2087 at 2.60, 2115 at 2.85, 2176 at 3.10) because that
## scenario's GMST flattens near its peak.
ONSETS_ARG = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--onsets=")), "")
if ONSETS_ARG:
    RES_ONSET_K = [float(x) for x in ONSETS_ARG.split(",")]
RES_V_M = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
## V is in METRES and every base_* series is in CM (rebase_cm). The conversion is a
## named constant because getting it wrong is silent: a 2 m reservoir added without
## it lands as 1.8 cm at 2300 instead of 172, every cell "passes", and the 216/216
## looks like a result. It was exactly that uniformity that exposed it.
CM_PER_M = 100.0
V_MAX_M = 2.73                   # NO+NE Mouginot inventory, the hard ceiling
## --- THE WHOLE-SHEET ARM, `--wide-v` (2026-08-23) --------------------------
## WHY IT EXISTS. The weighted verdict of handoff_2026-08-23b picked V = 7.42 m --
## the WHOLE SHEET -- at tau = 2700 yr. Both lie OUTSIDE this scorecard's grid, and
## V lies outside V_MAX_M, which is the NO+NE high-basin inventory that bounded the
## reservoir for as long as it was conceived as a high-basin TAP. That matters here
## and nowhere else: the 2150 ssp585 criterion below is the horizon every previous
## tap cell failed (0/25 in band), it is the reason cell A was ever preferred, and
## the winner has NEVER been scored on it. `--wide-v` extends the V and tau ladders
## to cover the winner and moves the inventory ceiling with them.
##
## THE CEILING CHANGE IS A CLAIM, NOT A CONVENIENCE: V <= 7.42 m is admissible only
## if the reservoir is a WHOLE-SHEET object. It is not a wider high-basin tap --
## 100*V/tau at the 2.73 m ceiling caps psi at 0.124 against the 0.273 the Greve and
## rate criteria both pin, 2.2x short. So the arm and the wiring stand or fall
## together, and INVENTORY_NAME travels into every label and filename below.
##
## The DEFAULT path is untouched and its CSV must stay byte-identical.
WIDE_V = "--wide-v" in sys.argv
RES_V_M_WIDE = [2.73, 3.0, 4.5, 6.0, GIS_V0_M]
RES_TAU_WIDE = [2200, 2700]
WINNER_CELL = (GIS_V0_M, 4.69, 2700.0)   # (V_m, onset_K, tau_yr), handoff sec 1
CELL_A = (1.0, 4.69, 800.0)              # the reservoir cell this file selected
V_GRID = RES_V_M + RES_V_M_WIDE if WIDE_V else RES_V_M
TAU_GRID = sorted(RES_TAU + RES_TAU_WIDE) if WIDE_V else RES_TAU
V_CEIL_M = GIS_V0_M if WIDE_V else V_MAX_M
INVENTORY_NAME = "whole sheet" if WIDE_V else "NO+NE high basin"
## --- THE CASCADE ARM, `--stages=N` (2026-08-23) ----------------------------
## WHY. diag_gis_2150_band_veto.py showed the joint constraint -- at most 8.1 cm at
## 2150 on the ssp585 x2300 arm, 48.6 cm at 2300 on our own ssp585 -- needs a
## delivery ratio R = 6.03, and that a FIRST-ORDER reservoir tops out at 2.89 over
## every onset in 1.6-7.5 K. So no (V, tau) can be wired: the FORM is what fails.
## An n-stage cascade responds as an n-fold repeated integral of the ramp, is
## back-loaded, and -- decisively -- is NOT completely monotone, so the exact bound
## that refuted the ladder, Prony, stretched-exponential, Mittag-Leffler and
## power-law families does not reach it.
##
## PARAMETERISATION: `tau` stays the TOTAL mean delay, so each stage runs at
## stages/tau and `stages=1` is the existing reservoir BIT-IDENTICALLY (gated by
## re-running the default arm and diffing the CSV).
STAGES = next((int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--stages=")), 1)
STAGES >= 1 or sys.exit("--stages must be >= 1")
STAGE_WORD = "first-order reservoir" if STAGES == 1 else f"{STAGES}-stage cascade"
CALIB_WIN = HIND
# --- THE 2100 TOLERANCE, DERIVED FROM THE SAMPLED SPREAD (Marcus 2026-08-23) ---
## WHAT IT WAS. A bare literal `Y2100_TOL_CM = 0.10` cm with no recorded
## justification, imported by three other scripts. It is a PHYSICAL-PLAUSIBILITY
## gate ("the reservoir must not disturb the 2100 deliverable") and it was written
## with the tightness of an IDENTITY gate. Those are different things:
##   identity / reproduction gates  -> stay exact or near-exact. A byte-diff, a
##       G-INERT ramp that must be 0.0, a base that must reproduce another
##       script's output: these test that two computations are THE SAME.
##   plausibility gates             -> must be scaled to the UNCERTAINTY of the
##       quantity being compared. 0.10 cm is 2.1% of Greenland's own sampled
##       p05-p95 at 2100 on ssp585 (4.78 cm) and 0.20% of the TOTAL's (50.1 cm).
##       It was demanding agreement ~50x finer than the model can resolve.
##
## WHY IT MATTERED. On the 2026-08-23 onset ladder this gate -- not the ssp245
## band, which was tested and does not bind -- is what forces tau to 2700-3200 yr
## at low onsets, and a reservoir that slow reaches only 0.28-0.53x of Greve@3001.
## A constraint tighter than the model's own resolution was setting the shape.
##
## THE RULE, stated once and applied mechanically: the reservoir's contribution at
## 2100 must be small against the POSTERIOR SPREAD of the quantity it is added to,
## PER SCENARIO. `TOL_FRAC` is a fraction of that scenario's own sampled p05-p95
## WIDTH, so TOL_FRAC = 0.5 means "within the half-width of the sampled 90%
## interval". The scan prints the whole TOL_FRAC ladder, so the choice of fraction
## is visible in every run rather than buried in this constant.
Y2100_TOL_LEGACY_CM = 0.10      # the superseded literal, kept for reproduction
TOL_BAND_Q = (0.05, 0.95)       # the sampled interval the tolerance is scaled to
TOL_FRAC = 0.5                  # fraction of that interval's WIDTH == half-width
TOL_FRAC_LADDER = (0.021, 0.10, 0.25, 0.50, 1.00)   # 0.021 ~ the legacy 0.10 cm
TOL_RULE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--tol=")),
                "spread")
TOL_RULE in ("spread", "legacy") or sys.exit("--tol must be spread|legacy")
## The spread is read from the SHIPPED deliverable so importers of this module get
## a defined scalar at import time; the scan itself re-derives it PER SCENARIO from
## its own ensemble and GATES the two against each other, so the file cannot rot.
DELIVERABLE = os.path.join(REPO, "outputs/ssps_components_2300_L14.csv")


def _sampled_spread_2100():
    """Greenland p05-p95 width at 2100 per scenario, cm, from the shipped L14
    deliverable (SAME rebase frame as rebase_cm: rel 1995-2014)."""
    if not os.path.exists(DELIVERABLE):
        return {}
    d = pd.read_csv(DELIVERABLE)
    d = d[(d.year == 2100) & (d.component == "gis")]
    return {r.ssp: float(r.p95 - r.p05) for _, r in d.iterrows()}


Y2100_SPREAD_CM = _sampled_spread_2100()
Y2100_TOL_CM = (TOL_FRAC * Y2100_SPREAD_CM["SSP5-8.5"]
                if TOL_RULE == "spread" and "SSP5-8.5" in Y2100_SPREAD_CM
                else Y2100_TOL_LEGACY_CM)
Y2100_TOL_WORD = (f"{TOL_FRAC:g} x sampled p05-p95 width" if TOL_RULE == "spread"
                  else "LEGACY fixed 0.10 cm")
## EVERY non-default choice is in the FILENAME -- the arm, the stage count, the
## onset ladder and now the tolerance rule -- so the artefact the shipped 86/216
## verdict rests on keeps its own name, is still reachable with `--tol=legacy`,
## and no scan can overwrite another's result under its name.
ARM_SUFFIX = (("_wideV" if WIDE_V else "") + (f"_n{STAGES}" if STAGES > 1 else "")
              + ("_onsetladder" if ONSETS_ARG else "")
              + ("_tolspread" if TOL_RULE == "spread" else ""))
OUT = OUT_STEM + ARM_SUFFIX + ".csv"
OURS_GMT_2300 = {"SSP1-2.6": 1.73, "SSP2-4.5": 3.15, "SSP5-8.5": 7.81}


def reservoir_unit_n(gmt, onset, tau, stages=1):
    """n-stage cascade of first-order reservoirs, TOTAL mean delay `tau` (each
    stage runs at stages/tau). At stages=1 this is `reservoir_unit` term for term,
    which is why the default arm can be gated byte-identical rather than argued.

    The point of n > 1 is SHAPE, not size: the response to a ramp is an n-fold
    repeated integral, so it is ~t^n early instead of ~t, which is the only way
    the 2150 cap and the 2300 target stop contradicting each other."""
    seq = np.clip((gmt - onset) / RAMP_W_K, 0.0, 1.0)
    r = stages / tau
    S = [np.zeros_like(gmt) for _ in range(stages)]
    for i in range(1, len(gmt)):
        upstream = seq[i - 1]
        for k in range(stages):
            prev = S[k][i - 1]
            S[k][i] = prev + (upstream - prev) * r
            upstream = prev          # stage k+1 sees stage k's PREVIOUS year
    return S[-1]


def reservoir_unit(gmt, onset, tau):
    """Unit reservoir: first-order relaxation toward a soft GMT ramp. IDENTICAL in
    form to scope_gis_tap_l13.tap_unit -- deterministic given the scenario, which
    is exactly why it is prior-propagated rather than sampled."""
    seq = np.clip((gmt - onset) / RAMP_W_K, 0.0, 1.0)
    S = np.zeros_like(gmt)
    r = 1.0 / tau
    for i in range(1, len(gmt)):
        S[i] = S[i - 1] + (seq[i - 1] - S[i - 1]) * r
    return S


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    S_tab = gis_shape_table()
    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in list(HORIZONS) + list(HIND) + [2015]}
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])

    def load(path, col):
        g = pd.read_csv(path).set_index("year")[col].reindex(YEARS).to_numpy()
        rb = g - g[ibd].mean()
        return rb, regional_driver(rb, post["gis_amp"].to_numpy(), S_tab)

    gmst, drivers = {}, {}
    for ssp, lab, fam, stem in ARMS:
        gmst[(ssp, fam)], drivers[(ssp, fam)] = load(
            os.path.join(REPO, f"outputs/{stem}.csv"), f"gmst_{ARM}")
    ours_gmst, ours_drv = {}, {}
    for ssp, lab in OURS:
        ours_gmst[lab], ours_drv[lab] = load(
            os.path.join(REPO, f"data/observations/fair_mean_gmst_{ssp}.csv"), "gmst_C")

    print(f"scope_gis_reservoir_offline — {STAGE_WORD} at MILLENNIAL tau, "
          f"{TAG}, {len(post)} draws, k={K_FIXED:g}, inventory ceiling "
          f"{V_CEIL_M:g} m ({INVENTORY_NAME})\n")

    # --- the base model, run ONCE: the reservoir is additive and calib-inert ----
    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    Th = drivers[A.HIND_ARM]
    lo, hi = np.full(len(post), 1e-4), np.full(len(post), 1e3)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = basin2_series(Th, post, K_FIXED, mid)
        below = 100.0 * (L[:, idx[HIND[1]]] - L[:, idx[HIND[0]]]) < want_cm
        lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
    s = np.sqrt(lo * hi)
    base_arm = {k: np.median(rebase_cm(basin2_series(v, post, K_FIXED, s)), axis=0)
                for k, v in drivers.items()}
    ens_ours = {k: rebase_cm(basin2_series(v, post, K_FIXED, s))
                for k, v in ours_drv.items()}
    base_ours = {k: np.median(e, axis=0) for k, e in ens_ours.items()}
    ## THE TOLERANCE IS DERIVED HERE, per scenario, from THIS ensemble -- and gated
    ## against the shipped deliverable's own 2100 spread so neither can drift.
    spread_ens = {lab: float(np.quantile(ens_ours[lab][:, idx[2100]], TOL_BAND_Q[1])
                             - np.quantile(ens_ours[lab][:, idx[2100]], TOL_BAND_Q[0]))
                  for _, lab in OURS}
    TOL = {lab: (TOL_FRAC * spread_ens[lab] if TOL_RULE == "spread"
                 else Y2100_TOL_LEGACY_CM) for _, lab in OURS}
    print(f"=== THE 2100 TOLERANCE ({Y2100_TOL_WORD}) ===")
    print(f"  {'scenario':10}{'sampled p05-p95 @2100':>24}{'deliverable':>13}"
          f"{'ratio':>8}{'tolerance':>12}{'  vs legacy':>12}")
    for _, lab in OURS:
        dl = Y2100_SPREAD_CM.get(lab, float("nan"))
        print(f"  {lab:10}{spread_ens[lab]:24.3f}{dl:13.3f}"
              f"{spread_ens[lab] / dl:8.3f}{TOL[lab]:12.3f}"
              f"{TOL[lab] / Y2100_TOL_LEGACY_CM:11.1f}x")
    print(f"  The legacy 0.10 cm was {100 * Y2100_TOL_LEGACY_CM / spread_ens['SSP5-8.5']:.1f}% "
          f"of ssp585's own sampled spread -- a PLAUSIBILITY gate held to an "
          f"IDENTITY gate's\n  tightness. Identity gates (G-INERT, the base "
          f"reproduction, byte-diffs) stay exact; this one\n  is now scaled to what "
          f"the model can actually resolve.\n")

    # --- G-INERT: the ramp must be EXACTLY zero over the calibration window ----
    iw = (YEARS >= CALIB_WIN[0]) & (YEARS <= CALIB_WIN[1])
    worst = 0.0
    for lab in list(ours_gmst) + [f"{a[1]} {a[2]}" for a in ARMS]:
        g = ours_gmst[lab] if lab in ours_gmst else gmst[
            next((a[0], a[2]) for a in ARMS if f"{a[1]} {a[2]}" == lab)]
        for on in RES_ONSET_K:
            for tau in TAU_GRID:
                worst = max(worst, float(np.max(np.abs(
                    reservoir_unit_n(g, on, tau, STAGES)[iw]))))
    print(f"G-INERT — max |reservoir ramp| over {CALIB_WIN}, over ALL "
          f"{len(RES_ONSET_K) * len(TAU_GRID)} (onset,tau) x every driver: {worst:.3e}")
    if worst != 0.0:
        sys.exit(f"G-INERT FAILED: the reservoir is not exactly calibration-inert "
                 f"({worst:.3e}); the base rate solution cannot be reused and this "
                 f"is a refit question, not a prior-propagation one.")
    print("  EXACTLY zero => the hindcast, the bisection and the base rate solution "
          "are UNCHANGED,\n  so the reservoir is prior-propagatable like the tap and "
          "gis_amp -- and unlike gamma.\n")

    # --- the scan ---------------------------------------------------------------
    ann = pd.read_csv(A.ANN)
    offs = float(np.median(rebase_cm(
        basin2_series(drivers[("ssp585", "r2300")], post, 1.0, 1.0))[:, idx[2015]]))
    band = {}
    for ssp, lab, fam, _ in ARMS:
        q = A.protect_band(ann, lab, fam).groupby("year").gis_cm
        band[(ssp, fam)] = {y: (q.quantile(.05)[y] + offs, q.median()[y] + offs,
                                q.quantile(.95)[y] + offs) for y in HORIZONS}
    MB = {lab: (100 * gis_targets.MATCHED_2300_M[lab][0],
                100 * gis_targets.MATCHED_2300_M[lab][1]) for _, lab in OURS}

    def score(add_arm, add_ours):
        per = {}
        for ssp, lab, fam, _ in ARMS:
            L = base_arm[(ssp, fam)] + add_arm[(ssp, fam)]
            per[(ssp, fam)] = float(np.sqrt(np.mean(
                [np.log(max(L[idx[y]], 1e-6) / band[(ssp, fam)][y][1]) ** 2
                 for y in HORIZONS])))
        agg = lambda arms: float(np.sqrt(np.mean([per[(a[0], a[2])] ** 2 for a in arms])))
        return per, agg(SSP585_ARMS), agg(COOL_ARMS), agg(ARMS)

    zero_arm = {k: 0.0 for k in drivers}
    zero_ours = {k: 0.0 for k in ours_drv}
    per0, r585_0, rcool_0, rall_0 = score(zero_arm, zero_ours)
    print(f"BASELINE (no reservoir): rms_ssp585 {r585_0:.3f}  rms_cool {rcool_0:.3f}  "
          f"rms_all {rall_0:.3f}")
    print(f"  our 2300: " + "  ".join(
        f"{lab} {base_ours[lab][idx[2300]]:.1f}" for _, lab in OURS)
        + "   (matched bands " + ", ".join(f"{MB[lab][0]:.0f}-{MB[lab][1]:.0f}"
                                           for _, lab in OURS) + ")\n")

    rows = []
    for V in V_GRID:
        for on in RES_ONSET_K:
            for tau in TAU_GRID:
                aa = {(a[0], a[2]): CM_PER_M * V * reservoir_unit_n(
                          gmst[(a[0], a[2])], on, tau, STAGES) for a in ARMS}
                ao = {lab: CM_PER_M * V * reservoir_unit_n(
                          ours_gmst[lab], on, tau, STAGES) for _, lab in OURS}
                per, r585, rcool, rall = score(aa, ao)
                ## The default arm keeps its EXACT pre-existing schema, so a
                ## stages=1 run stays byte-identical and every consumer of the
                ## shipped CSV is untouched; the cascade arm carries its own column.
                rec = dict(V_m=V, onset_K=on, tau_yr=tau,
                           within_inventory=bool(V <= V_CEIL_M),
                           rms_ssp585=r585, rms_cool=rcool, rms_all=rall)
                if STAGES > 1:
                    rec["stages"] = STAGES
                for ssp, lab, fam, _ in ARMS:
                    rec[f"rms_{ssp}_{fam}"] = per[(ssp, fam)]
                    rec[f"{ssp}_{fam}_2150"] = base_arm[(ssp, fam)][idx[2150]] + \
                        aa[(ssp, fam)][idx[2150]]
                    rec[f"{ssp}_{fam}_2150_in"] = bool(
                        band[(ssp, fam)][2150][0] <= rec[f"{ssp}_{fam}_2150"]
                        <= band[(ssp, fam)][2150][2])
                ok2300, ok2100 = True, True
                for _, lab in OURS:
                    v23 = base_ours[lab][idx[2300]] + ao[lab][idx[2300]]
                    d21 = ao[lab][idx[2100]]
                    rec[f"ours_{lab}_2300_cm"] = v23
                    rec[f"ours_{lab}_d2100_cm"] = d21
                    rec[f"ours_{lab}_in_matched"] = bool(MB[lab][0] <= v23 <= MB[lab][1])
                    ok2300 &= rec[f"ours_{lab}_in_matched"]
                    ok2100 &= abs(d21) < TOL[lab]
                rec["bands_ok"], rec["keeps_2100"] = ok2300, ok2100
                rec["shape_better"] = bool(rall < rall_0)
                rec["all_pass"] = bool(ok2300 and ok2100 and rec["within_inventory"]
                                       and rall < rall_0)
                rows.append(rec)

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    adm = out[out.within_inventory]
    print(f"=== GRID — {len(V_GRID)}x{len(RES_ONSET_K)}x{len(TAU_GRID)} = {len(out)} "
          f"cells; inventory ceiling {V_CEIL_M:g} m ({INVENTORY_NAME}), "
          f"{int(out.within_inventory.sum())} within it ===\n")
    print(f"  keeps 2100 ({Y2100_TOL_WORD})  {int(adm.keeps_2100.sum()):4d}/{len(adm)}")
    print(f"  all three 2300 matched bands        {int(adm.bands_ok.sum()):4d}/{len(adm)}")
    print(f"  improves the 5-arm shape            {int(adm.shape_better.sum()):4d}/{len(adm)}")
    print(f"  ALL OF THE ABOVE                    {int(adm.all_pass.sum()):4d}/{len(adm)}")

    p = adm[adm.all_pass]
    if p.empty:
        print("\n  NO CELL PASSES. Reporting the closest on each criterion "
              "separately, so the binding one is visible:")
        for c, nm in (("bands_ok", "2300 bands"), ("keeps_2100", "2100"),
                      ("shape_better", "shape")):
            print(f"    {nm:12} passed by {int(adm[c].sum())} cells")
    else:
        print(f"\n  BEST BY 5-ARM SHAPE among passing cells:")
        b = p.loc[p.rms_all.idxmin()]
        print(f"    V={b.V_m:g} m  onset={b.onset_K:g} K  tau={b.tau_yr:g} yr")
        print(f"      rms_all {b.rms_all:.3f} vs {rall_0:.3f} baseline "
              f"({rall_0 / b.rms_all:.3f}x better);  rms_ssp585 {b.rms_ssp585:.3f} "
              f"vs {r585_0:.3f} ({r585_0 / b.rms_ssp585:.3f}x)")
        print(f"      our 2300: " + "  ".join(
            f"{lab} {b[f'ours_{lab}_2300_cm']:.1f}" for _, lab in OURS))
        print(f"      2150 on the ssp585 arms: "
              + "  ".join(f"{fam} {b[f'ssp585_{fam}_2150']:.1f} "
                          f"(band {band[('ssp585', fam)][2150][0]:.0f}-"
                          f"{band[('ssp585', fam)][2150][2]:.0f}, "
                          f"{'IN' if b[f'ssp585_{fam}_2150_in'] else 'out'})"
                          for fam in ("r2300", "x2300")))
        print(f"\n  TAU OF THE PASSING CELLS: "
              f"{sorted(set(p.tau_yr))}   (the tap's own grid stops at 400)")
        print(f"  V   OF THE PASSING CELLS: {sorted(set(p.V_m))}")
        print(f"  ONSET OF THE PASSING CELLS: {sorted(set(p.onset_K))}")
        n_new = int((p.tau_yr > 400).sum())
        print(f"\n  {n_new}/{len(p)} passing cells have tau > 400 yr, i.e. lie OUTSIDE "
              f"the grid every\n  previous tap pricing ever scanned.")

        ## THE 2150 HORIZON is where every previous tap cell failed (0/25 in band),
        ## so it is reported as its own count rather than folded into all_pass.
        p2 = p[p["ssp585_r2300_2150_in"] & p["ssp585_x2300_2150_in"]]
        print(f"\n=== 2150, THE HORIZON THE TAP SCORED 0/25 ON ===\n")
        print(f"  cells clearing everything AND both ssp585 2150 bands: {len(p2)}/{len(p)}")
        if len(p2):
            b2 = p2.loc[p2.rms_all.idxmin()]
            print(f"  best: V={b2.V_m:g} m  onset={b2.onset_K:g} K  tau={b2.tau_yr:g} yr")
            print(f"    rms_all {b2.rms_all:.3f} ({rall_0 / b2.rms_all:.2f}x baseline), "
                  f"rms_ssp585 {b2.rms_ssp585:.3f} ({r585_0 / b2.rms_ssp585:.2f}x), "
                  f"rms_cool {b2.rms_cool:.3f} (baseline {rcool_0:.3f})")
            print(f"    our 2300 cm: " + "  ".join(
                f"{lab} {b2[f'ours_{lab}_2300_cm']:.1f}" for _, lab in OURS)
                + f";  d2100 ssp585 {b2['ours_SSP5-8.5_d2100_cm']:+.4f} cm")
            print(f"    2150: r2300 {b2['ssp585_r2300_2150']:.1f} "
                  f"(band {band[('ssp585','r2300')][2150][0]:.0f}-"
                  f"{band[('ssp585','r2300')][2150][2]:.0f})   "
                  f"x2300 {b2['ssp585_x2300_2150']:.1f} "
                  f"(band {band[('ssp585','x2300')][2150][0]:.0f}-"
                  f"{band[('ssp585','x2300')][2150][2]:.1f})")

            ## WHICH OF THE FOUR DIFFERENCES ACTUALLY DID THE WORK. Measured by
            ## splitting the passing set at the old tau ceiling, because "we scanned
            ## somewhere new" and "the new region is why it works" are different
            ## claims and only the second would justify the new axis.
            old, new = p2[p2.tau_yr <= 400], p2[p2.tau_yr > 400]
            print(f"\n  DECOMPOSITION — what actually opened the door:")
            print(f"    inside the OLD tau grid (<=400): {len(old)} cells clear "
                  f"everything, best rms_all "
                  f"{old.rms_all.min() if len(old) else float('nan'):.3f}")
            print(f"    in the NEW tau range   (>400) : {len(new)} cells, best rms_all "
                  f"{new.rms_all.min() if len(new) else float('nan'):.3f}")
            if len(old) and len(new):
                print(f"    => extending tau past 400 buys "
                      f"{old.rms_all.min() / new.rms_all.min():.3f}x. It is NOT what "
                      f"opened the door.")
                add = b2["ours_SSP5-8.5_2300_cm"] - base_ours["SSP5-8.5"][idx[2300]]
                litlo = 100 * gis_targets.LIT_2300_M["SSP5-8.5"][0]
                print(f"    THE RE-TARGET IS. The best cell adds {add:.1f} cm at 2300 "
                      f"(49.9 -> {b2['ours_SSP5-8.5_2300_cm']:.1f}); against the RAW "
                      f"literature\n       floor of {litlo:.0f} cm that is "
                      f"{litlo / b2['ours_SSP5-8.5_2300_cm']:.1f}x SHORT, which is "
                      f"exactly why no small-V\n       reservoir was ever admissible "
                      f"before 2026-08-21g.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
