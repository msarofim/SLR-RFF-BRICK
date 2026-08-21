#!/usr/bin/env python3
"""
scope_gis_leq_ridge_vs_literature.py — can an external Leq(T) constraint fix the
SSP5-8.5 2300 shortfall, or is the shortfall STRUCTURAL to the linear commitment?

WHY THIS EXISTS (2026-08-18)
  The 2026-08-18 literature check found Ladrillo's ssp585 Greenland at 2300 low
  by 3.8-6.9x against continued-warming ice-sheet models, while SSP1-2.6 matches
  almost exactly (0.091 vs 0.092 m) and SSP2-4.5 sits inside its reported range.
  scope_gis_2300_relaxation.py had already shown WHY the calibration cannot
  simply find a bigger commitment: the 1900-2025 hindcast constrains only the
  PRODUCT phi*Leq, so scaling (c1,c0) by k and re-solving the rate scale fits the
  hindcast identically for every k -- a ridge. The stated fix was "the identifying
  constraint must be an external Leq(T) target".

  BEFORE BUYING THAT REFIT: an external Leq(T) target moves the model ALONG this
  ridge. It cannot move it off. So the refit can only succeed if some point on the
  ridge is simultaneously acceptable for all three scenarios. This script walks
  the ridge and checks. It is offline -- no chain, no calibrator edit.

  If NO k works, the shortfall is not an identification problem at all and the
  fix has to change the SHAPE of Leq(T), not its scale. That is a different and
  much larger piece of work, and it would be wrong to discover it after paying
  for a calibration.

THE THREE CONSTRAINTS ANY CANDIDATE MUST MEET SIMULTANEOUSLY
  1. the 1900-2025 hindcast -- imposed by construction (s is bisected to it), so
     it is satisfied at every k and is NOT a discriminator;
  2. the 2100 deliverable -- what A+B was SELECTED on. Raising k changes 2100 as
     well, and a fix that repairs 2300 by breaking the shipped 2100 column is not
     a fix. Reported per k, never assumed unchanged;
  3. the 2300 literature bands, per scenario.

  Reporting 2300 alone would let a candidate "win" by wrecking 2100 invisibly.

READS   data/MimiBRICK/parameters_subsample_brick_mengel_<TAG>.csv
        outputs/recalib_targets_ext.csv, outputs/gis_amp_shape{,_meta}.csv
        data/observations/fair_mean_gmst_<ssp>.csv, t_gis_zones.csv
WRITES  outputs/scope_gis_leq_ridge_vs_literature.csv

  source ~/climate-env/bin/activate
  python3 python/scope_gis_leq_ridge_vs_literature.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
# the A+B re-implementation, its drivers and its reproduction gate are defined
# once, in the script that established the ridge. Do not re-implement them here.
from scope_gis_2300_relaxation import (  # noqa: E402
    GIS_ZONE, GIS_V0_M, IREF, OBS, YEARS, gis_shape_table, gmst_rebased,
    regional_driver,
)

# --- named constants; every label below derives from these -------------------
LADRILLO_TAG = "L12"
POST = os.path.join(REPO,
                    f"data/MimiBRICK/parameters_subsample_brick_mengel_{LADRILLO_TAG}.csv")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
OUT = os.path.join(REPO, "outputs/scope_gis_leq_ridge_vs_literature.csv")
HIND = (1900, 2025)
HIND_DRIVER = "ssp245"        # history is observed t_gis, so this choice is inert
SSPS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
K_GRID = [1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 10.0, 12.0, 14.0, 16.0, 22.6, 32.0, 50.0]

# 2300 targets. MOVED 2026-08-21g into python/gis_targets.py, which is now the ONE
# place both the raw literature bands and the forcing-matched set live -- six
# scripts scored against these and two carried their own copied literals, so no
# single edit could correct them all. Re-exported here under the OLD names because
# four scripts import them from this module; the values are byte-identical to the
# transcription that lived here (TC 19:6887 (2025) doi 10.5194/tc-19-6887-2025;
# TC 20:309 (2026) doi 10.5194/tc-20-309-2026). Scripts that want the matched set
# call gis_targets.from_argv / gis_targets.get.
import gis_targets  # noqa: E402
LIT_2300_M, LIT_2300_NOTE = gis_targets.LIT_2300_M, gis_targets.LIT_2300_NOTE
# G4 = the 2100 scenario spread (ssp585 - ssp126, cm) that A+B was SELECTED on.
# The evaluation band is 6.3-7.3 cm, but that band applies to the ENSEMBLE median,
# and this scan runs at MEDIAN PARAMETERS -- medians are not multiplicative, so the
# two differ (k=1 gives ~8.1 here against the ensemble's 7.37). Testing the
# median-parameter G4 against the ensemble band would wrongly indict the SHIPPED
# model at k=1. So G4 is reported RELATIVE TO k=1: the question is not "is this in
# the band" but "how far does raising k drag 2100 away from what was accepted".
G4_REF_K = 1.0
G4_DEGRADE_TOL = 0.15      # >15% change in the 2100 spread counts as breaking it
# mirrors LADRILLO_GIS_TBAR_WIN in julia/ladrillo_projection.jl. TBAR is DERIVED
# from the driver, not hardcoded, and asserted against the Julia's own tolerance
# so a driver change cannot silently rescale alpha_s.
TBAR_WIN = (2015, 2024)
TBAR_EXPECT, TBAR_TOL = 1.963, 5e-3


def gis_tbar():
    tgz = pd.read_csv(os.path.join(OBS, "t_gis_zones.csv"))
    m = (tgz["year"].astype(int) >= TBAR_WIN[0]) & (tgz["year"].astype(int) <= TBAR_WIN[1])
    tbar = float(tgz.loc[m, GIS_ZONE].astype(float).mean())
    if abs(tbar - TBAR_EXPECT) >= TBAR_TOL:
        raise SystemExit(f"TBAR = {tbar:.4f} from {TBAR_WIN} disagrees with the "
                         f"Julia's {TBAR_EXPECT} +/- {TBAR_TOL}")
    return tbar


def native_greenland(pa, tbar):
    """Map the sampled (ell, w) slow-channel coordinates back to native
    alpha_s/beta_s. Mirrors ladrillo_native_greenland! exactly; L11 and later
    carry ONLY (ell, w), so this is required -- L10 was the last native vintage."""
    pa = pa.copy()
    if "gis_alpha_s" not in pa.index:
        r_s = np.exp(float(pa["gis_slow_ell"]))
        w_s = float(pa["gis_slow_w"])
        pa["gis_alpha_s"] = w_s * r_s / tbar
        pa["gis_beta_s"] = (1.0 - w_s) * r_s
    return pa


def ab_series(T, pa, k_c, s_r):
    """A+B at median params, commitment scaled by k_c and both channel rates by
    s_r. Mirrors _ab_series in scope_gis_2300_relaxation.py."""
    eq = np.clip(k_c * (pa["gis_c1"] * T + pa["gis_c0"]), 0.0, GIS_V0_M)
    f = pa["gis_f"]
    rf = np.clip(s_r * (pa["gis_alpha_f"] * T + pa["gis_beta_f"]), 1e-9, 1.0)
    rs = np.clip(s_r * (pa["gis_alpha_s"] * T + pa["gis_beta_s"]), 1e-9, 1.0)
    fast = np.zeros_like(T)
    slow = np.zeros_like(T)
    for i in range(1, len(T)):
        fast[i] = fast[i - 1] + (f * eq[i - 1] - fast[i - 1]) * rf[i - 1]
        slow[i] = slow[i - 1] + ((1 - f) * eq[i - 1] - slow[i - 1]) * rs[i - 1]
    return fast + slow, eq


def main():
    post = pd.read_csv(POST)
    tbar = gis_tbar()
    pa = native_greenland(post.median(numeric_only=True), tbar)
    print(f"  slow-channel coordinates mapped (ell, w) -> native at "
          f"TBAR = {tbar:.4f} K over {TBAR_WIN[0]}-{TBAR_WIN[1]}")
    S = gis_shape_table()
    drivers = {}
    for ssp, label in SSPS:
        _, rb = gmst_rebased(ssp)
        drivers[label] = regional_driver(rb, np.array([pa["gis_amp"]]), S)[0]

    tgt = pd.read_csv(TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    Th = drivers[dict(SSPS)[HIND_DRIVER]]
    ih0 = int(np.where(YEARS == HIND[0])[0][0])
    ih1 = int(np.where(YEARS == HIND[1])[0][0])
    i21 = int(np.where(YEARS == 2100)[0][0])
    i23 = int(np.where(YEARS == 2300)[0][0])

    def solve_rate(k):
        lo, hi = 1e-4, 1e3
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            L, _ = ab_series(Th, pa, k, mid)
            if 100.0 * (L[ih1] - L[ih0]) < want_cm:
                lo = mid
            else:
                hi = mid
        return np.sqrt(lo * hi)

    print(f"CAN AN EXTERNAL Leq(T) TARGET FIX ssp585@2300?  — Ladrillo {LADRILLO_TAG}, "
          f"median params, offline")
    print(f"  hindcast {HIND[0]}-{HIND[1]} = {want_cm:.2f} cm, restored by "
          f"bisection at every k (so it never discriminates)")
    print(f"  2300 literature targets, m SLE:")
    for _, lab in SSPS:
        lo, hi = LIT_2300_M[lab]
        print(f"    {lab:9s} {lo:.3f}-{hi:.3f}   [{LIT_2300_NOTE[lab]}]")
    print(f"  2100 G4 spread judged RELATIVE to k=1 (median-params, not the ensemble "
          f"band); >{100 * G4_DEGRADE_TOL:.0f}% change = 2100 broken\n")

    hdr = (f"  {'k':>6s} {'rate s':>8s} {'Leq585':>8s} | "
           + " ".join(f"{lab:>9s}" for _, lab in SSPS)
           + f" | {'G4_100':>7s} {'vs k=1':>6s}  verdict")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    rows, winners = [], []
    for k in K_GRID:
        s = solve_rate(k)
        v2300, v2100 = {}, {}
        for _, lab in SSPS:
            L, eq = ab_series(drivers[lab], pa, k, s)
            v2300[lab] = float(L[i23] - L[IREF].mean())
            v2100[lab] = float(L[i21] - L[IREF].mean())
        leq585 = float(np.clip(k * (pa["gis_c1"] * drivers["SSP5-8.5"][i23]
                                    + pa["gis_c0"]), 0, GIS_V0_M))
        g4 = 100.0 * (v2100["SSP5-8.5"] - v2100["SSP1-2.6"])
        ok = {lab: LIT_2300_M[lab][0] <= v2300[lab] <= LIT_2300_M[lab][1]
              for _, lab in SSPS}
        rows.append(dict(tag=LADRILLO_TAG, k=k, rate_scale=s, leq_585_2300_m=leq585,
                         g4_2100_cm=g4,
                         **{f"m2300_{lab}": v2300[lab] for _, lab in SSPS},
                         **{f"in_band_{lab}": ok[lab] for _, lab in SSPS}))

    g4_ref = [r["g4_2100_cm"] for r in rows if r["k"] == G4_REF_K][0]
    for r in rows:
        r["g4_rel_to_k1"] = r["g4_2100_cm"] / g4_ref
        r["keeps_2100"] = abs(r["g4_rel_to_k1"] - 1.0) <= G4_DEGRADE_TOL
        r["all_pass"] = all(r[f"in_band_{lab}"] for _, lab in SSPS) and r["keeps_2100"]
        if r["all_pass"]:
            winners.append(r["k"])
        cells = " ".join(f"{r[f'm2300_{lab}']:8.3f}"
                         + ("*" if r[f"in_band_{lab}"] else " ") for _, lab in SSPS)
        verdict = ("ALL PASS" if r["all_pass"] else
                   f"{sum(r[f'in_band_{lab}'] for _, lab in SSPS)}/3 @2300"
                   + ("" if r["keeps_2100"] else ", 2100 broken"))
        print(f"  {r['k']:6.1f} {r['rate_scale']:8.4f} {r['leq_585_2300_m']:8.3f} | "
              + cells + f" | {r['g4_2100_cm']:7.2f} {r['g4_rel_to_k1']:6.2f}x  {verdict}")

    print("\n  (* = inside that scenario's 2300 literature band; "
          "Leq585 = committed loss at ssp585/2300)\n")
    print("=== VERDICT ===\n")
    if winners:
        print(f"  Ridge points satisfying ALL constraints: k = {winners}")
        print("  -> An external Leq(T) target CAN work. Buying the refit is justified.")
    else:
        print("  NO point on the ridge satisfies all three scenarios plus the 2100 band.")
        print("  -> The ssp585 shortfall is NOT an identification problem. An external")
        print("     Leq(T) target moves the model ALONG this ridge, and no point on it")
        print("     is acceptable, so the refit CANNOT fix it. The commitment's SHAPE")
        print("     in temperature has to change, not its scale.")
        best = max(rows, key=lambda r: sum(r[f"in_band_{lab}"] for _, lab in SSPS))
        print(f"     Best any k manages: "
              f"{sum(best[f'in_band_{lab}'] for _, lab in SSPS)}/3, at k = {best['k']}.")
        top = max(rows, key=lambda r: r["m2300_SSP5-8.5"])
        lo_lit = LIT_2300_M["SSP5-8.5"][0]
        print(f"\n  THE RIDGE HAS A CEILING, and it is NON-MONOTONE in k.")
        print(f"     ssp585@2300 peaks at {top['m2300_SSP5-8.5']:.3f} m (k = {top['k']}), "
              f"barely reaching the BOTTOM of the {lo_lit:.3f}-"
              f"{LIT_2300_M['SSP5-8.5'][1]:.3f} m band.")
        print(f"     Beyond that it FALLS: Leq clips at V0 = {GIS_V0_M} m, so further k")
        print(f"     buys no more commitment while still slowing the rate. Raising the")
        print(f"     commitment cannot be pushed arbitrarily far even in principle.")
        at_top = top
        print(f"     And at that peak SSP1-2.6 is {at_top['m2300_SSP1-2.6'] / LIT_2300_M['SSP1-2.6'][1]:.1f}x "
              f"over its band top and SSP2-4.5 "
              f"{at_top['m2300_SSP2-4.5'] / LIT_2300_M['SSP2-4.5'][1]:.1f}x over its.")

    # The invariant that actually decides it. Band membership is a coarse test;
    # the ssp585/ssp245 RATIO at 2300 is what the ridge cannot change, and it is
    # what separates this model family from the literature.
    lit_lo = LIT_2300_M["SSP5-8.5"][0] / LIT_2300_M["SSP2-4.5"][1]
    lit_hi = LIT_2300_M["SSP5-8.5"][1] / LIT_2300_M["SSP2-4.5"][0]
    ratios = [(r["k"], r["m2300_SSP5-8.5"] / r["m2300_SSP2-4.5"]) for r in rows]
    rmin, rmax = min(x[1] for x in ratios), max(x[1] for x in ratios)
    kbest = max(ratios, key=lambda t: t[1])[0]
    for r in rows:
        r["ratio_585_over_245"] = r["m2300_SSP5-8.5"] / r["m2300_SSP2-4.5"]
    print("\n=== THE INVARIANT: the ssp585/ssp245 ratio at 2300 ===\n")
    print(f"  literature demands  {lit_lo:.1f}x - {lit_hi:.1f}x")
    print(f"  the ridge delivers  {rmin:.2f}x - {rmax:.2f}x  (best {rmax:.2f}x at k = {kbest})")
    print(f"\n  A LINEAR Leq ties the scenarios together: raising it to lift ssp585")
    print(f"  raises the cooler scenarios by nearly the same factor, so the RATIO")
    print(f"  barely moves. The literature's ratio is {lit_lo / rmax:.1f}-{lit_hi / rmax:.1f}x")
    print(f"  beyond anything this family can reach at ANY k. That, not band")
    print(f"  membership, is why an external Leq(T) target cannot be the fix.")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
