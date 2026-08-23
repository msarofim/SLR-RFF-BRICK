#!/usr/bin/env python3
"""
scope_gis_onset_rescan.py -- RE-SCAN THE RESERVOIR ONSET OVER THE LADDER RANGE.

WHY. The shipped onset is 4.69 K GMST. Memory `gis_tap_priced_l13` records where
that came from: "Bracket floor 4.69 K = exactly the 'don't move 2100' constraint."
It was chosen to protect 2100 -- and 16 ISMIP6 ice-sheet models say our 2100 is
already 1.30x FAST, so the protection was protecting a defect. Every equilibrium
ladder (Yelmo-REMBO 1.68-1.76 K, PISM-dEBM 2.18-2.60 K, CLIMBER-X 1.44-2.24 K)
puts the Greenland threshold at 1.7-2.6 K, i.e. 2.0-2.8x BELOW the shipped onset.
`handoff_2026-08-23_commitment_evidence.md` sec 5 calls this the highest-value
single change available, and sec 4 item 2 is this scan.

`diag_gis_npv_tau_sensitivity.py` then added a SECOND, independent reason: at the
shipped onset the reservoir's PER-TONNE contribution in SSP2-4.5 is exactly
0.00000 cm/mK, while at onset 2.0 K it is 0.00956 -- 4.2x the SSP5-8.5 marginal,
because ssp245 sits INSIDE the ramp. An RFF-SP-weighted SC-GHG lives in that
scenario space, so the shipped onset does not shrink the commitment term per
tonne, it DELETES it.

THE SCORING SET (Marcus 2026-08-23, and note what is NOT in it)
  history   HARD GATE, exactly-zero (G-INERT), and the scan's onset FLOOR is
            DERIVED from it rather than typed. The first run of this file scanned
            from a hardcoded 1.5 K and the gate fired at 1.204e-04: the floor is
            not our own drivers' 1.398 K but 1.588 K, set by CNRM-CM6-1's own
            hot recent history once the GCM cells joined the scoring set.
  2100      vs the ISMIP6 16-model MEDIAN, on the 5 CMIP6 cells.
  2300      vs SICOPOLIS (Greve) on the same 5 cells, PLUS the ssp585 matched band.
  3001      vs SICOPOLIS on the same 5 cells.
  ssp245@2300 is a DIAGNOSTIC, NOT A GATE -- dropped as a gate by Marcus
            2026-08-23. Its 2-GCM matched band is 3-9x too narrow by this repo's
            own sample-size analysis, and no leave-one-out is even defined on a
            2-GCM arm. It is printed for every cell so its leverage stays visible.

THE TENSION THIS SCAN EXISTS TO MEASURE, stated in advance so the result cannot be
read as a surprise: the reservoir is ADDITIVE and our 2100 is ALREADY 1.30x high.
Any onset below a scenario's 2100 GMST therefore makes 2100 WORSE. The handoff
expected 2100 "to move, and that is a feature" -- but it can only move UP. So the
question this scan actually answers is: how much 2100 degradation does a given
2300/3001 repair cost, and is there an onset where the trade is worth making?

WRITES outputs/scope_gis_onset_rescan.csv
  python3 python/scope_gis_onset_rescan.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

import scope_gis_shape_all_scenarios as A  # noqa: E402
import gis_targets  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, GIS_V0_M  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import DRIVER_BASE, gis_shape_table  # noqa: E402
from scope_gis_reservoir_offline import reservoir_unit, CM_PER_M  # noqa: E402
import scope_gis_reservoir_offline as _RES  # noqa: E402
## The extended-axis machinery, IMPORTED from the file that built and gated it, so
## this scan cannot drift from the object that produced the Greve comparison.
from diag_gis_greve_year3000 import (  # noqa: E402
    EXPS, YEARS_EXT, Y_LAST, DRAW_STRIDE, K_FIXED, HOLD_WIN,
    ext_driver, gcm_gmst_ext, gate, read_greve,
)

OUT = os.path.join(REPO, "outputs/scope_gis_onset_rescan.csv")
CMP_REF = os.path.join(REPO, "outputs/diag_gis_greve_year3000_cmp.csv")
ISM_REF = os.path.join(REPO, "outputs/diag_gis_ismip6_2100_ism_spread_arms.csv")

# --- named constants ----------------------------------------------------------
TAG = A.TAG
LINEAGE = "L14 canonical (two-basin), extended axis 1850-3001, thinned posterior"
ONSET_SHIPPED_K = 4.69
## The ladder range, from the three equilibrium sources: Yelmo-REMBO 1.68-1.76 K,
## PISM-dEBM 2.18-2.60 K, CLIMBER-X 1.44-2.24 K.
##
## THE FLOOR IS NOT TYPED, IT IS MEASURED (`onset_floor()`), and the first run of
## this file is why. An onset at or below the maximum GMST any scored driver
## reaches inside the calibration window makes the reservoir fire during the
## hindcast -- which turns prior-propagation into a REFIT. The obvious floor is our
## own drivers' 1.398 K. It is the WRONG floor here: adding the Greve/ISMIP6 GCM
## cells to the scoring set brings in GCMs that are HOT over the recent historical
## period (CNRM-CM6-1 reaches 1.588 K by 2023), and they set the floor instead.
## Scanning from a hardcoded 1.5 K broke G-INERT at 1.204e-04.
ONSET_MAX_K, ONSET_STEP_K = 3.0, 0.25
ONSET_FLOOR_ROUND_K = 0.05     # the measured floor is rounded UP to this grid
## V free up to the whole sheet; tau free over the millennial range the commitment
## evidence points at (psi = 100*V/tau is DERIVED, never typed).
V_SCAN_M = [1.0, 2.0, 3.0, 4.5, 6.0, GIS_V0_M]
TAU_SCAN_YR = [800.0, 1600.0, 2200.0, 2700.0, 3200.0]
HORIZONS = (2100, 2300, Y_LAST)
OURS = ["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"]
SSP_KEY = {"SSP1-2.6": "ssp126", "SSP2-4.5": "ssp245", "SSP5-8.5": "ssp585"}
CALIB_WIN = A.HIND
BASE_GATE_TOL_PCT = 0.5      # our 2100 must reproduce the Greve script's ours_2100
PSI_EVIDENCE = (0.179, 0.341)   # Greve@3001 per-cell requirement, median 0.242


def onset_floor(gmst, iw):
    """The lowest onset that is EXACTLY calibration-inert: the maximum GMST any
    scored driver reaches inside the calibration window. Derived, never typed --
    it moved once already when the GCM cells joined the scoring set."""
    per = {k: float(np.max(g[iw])) for k, g in gmst.items()}
    raw = max(per.values())
    return per, raw, float(np.ceil(raw / ONSET_FLOOR_ROUND_K) * ONSET_FLOOR_ROUND_K)


def build_base():
    """The base model on the extended axis, EXACTLY as diag_gis_greve_year3000
    section 3 builds it (thinned posterior, hindcast bisection, 2015 offset). Gated
    against that script's own output below, so 'exactly' is measured."""
    post = pd.read_csv(A.POST)
    S = gis_shape_table()
    gate(post, S)                       # ext_driver == regional_driver on the overlap
    thin = post.iloc[::DRAW_STRIDE].reset_index(drop=True)
    tbar = gis_tbar()
    r_s = np.exp(thin["gis_slow_ell"].to_numpy())
    thin["gis_alpha_s"] = thin["gis_slow_w"].to_numpy() * r_s / tbar
    thin["gis_beta_s"] = (1.0 - thin["gis_slow_w"].to_numpy()) * r_s

    ie = {y: int(np.where(YEARS_EXT == y)[0][0]) for y in HORIZONS + (2015,)}
    ih = {y: int(np.where(YEARS_EXT == y)[0][0]) for y in CALIB_WIN}
    ibd = (YEARS_EXT >= DRIVER_BASE[0]) & (YEARS_EXT <= DRIVER_BASE[1])

    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want = float(tgt.loc[CALIB_WIN[1]] - tgt.loc[CALIB_WIN[0]])
    gh = pd.read_csv(os.path.join(REPO, f"outputs/{A.ARMS[0][3]}.csv")).set_index(
        "year")[f"gmst_{A.ARM}"].reindex(YEARS_EXT).ffill().bfill().to_numpy()
    hd = ext_driver(gh - gh[ibd].mean(), thin, S)
    lo, hi = np.full(len(thin), 1e-4), np.full(len(thin), 1e3)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = basin2_series(hd, thin, K_FIXED, mid)
        b = 100.0 * (L[:, ih[CALIB_WIN[1]]] - L[:, ih[CALIB_WIN[0]]]) < want
        lo, hi = np.where(b, mid, lo), np.where(b, hi, mid)
    s_r = np.sqrt(lo * hi)
    offs = float(np.median(basin2_series(hd, thin, 1.0, 1.0)[:, ie[2015]])) * CM_PER_M

    def series(gmst_rb):
        drv = ext_driver(gmst_rb, thin, S)
        return np.median(basin2_series(drv, thin, K_FIXED, s_r), axis=0) * CM_PER_M - offs

    gmst, base = {}, {}
    for e, (lab, model, ssp) in EXPS.items():
        if not model:
            continue
        gmst[e] = gcm_gmst_ext(model, ssp)
        base[e] = series(gmst[e])
    ## Our own SSPs: the fair_mean files stop at 2301 and are HELD beyond it. Only
    ## horizons <= 2300 are ever read from them, so the hold is never scored.
    for lab in OURS:
        g = pd.read_csv(os.path.join(
            REPO, f"data/observations/fair_mean_gmst_{SSP_KEY[lab]}.csv")).set_index(
            "year")["gmst_C"].reindex(YEARS_EXT).ffill().bfill().to_numpy()
        gmst[lab] = g - g[ibd].mean()
        base[lab] = series(gmst[lab])
    return gmst, base, ie, thin


def main():
    print(f"scope_gis_onset_rescan -- {LINEAGE}, {TAG}")
    gmst, base, ie, thin = build_base()

    # --- GATE 1: the base reproduces the script that produced the Greve numbers --
    ref = pd.read_csv(CMP_REF).set_index("exp")
    worst = max(abs(base[e][ie[2100]] / ref.loc[e, "ours_2100"] - 1) * 100
                for e in ref.index)
    if worst > BASE_GATE_TOL_PCT:
        sys.exit(f"BASE GATE: our 2100 differs from diag_gis_greve_year3000_cmp.csv "
                 f"by {worst:.3f}% (tol {BASE_GATE_TOL_PCT}%)")
    print(f"  BASE GATE  our 2100 reproduces diag_gis_greve_year3000_cmp.csv to "
          f"{worst:.4f}% on {len(ref)} cells\n")

    # --- the targets ----------------------------------------------------------
    sico = {e: {2300: float(ref.loc[e, "sico_2300"]),
                Y_LAST: float(ref.loc[e, f"sico_{Y_LAST}"])} for e in ref.index}
    ism = pd.read_csv(ISM_REF)
    ismed = {}
    for e in ref.index:
        _, model, ssp = EXPS[e]
        m = ism[(ism.gcm == model) & (ism.ssp == ssp)]
        if not len(m):
            sys.exit(f"no ISMIP6 median for {e} ({model} {ssp})")
        ismed[e] = float(m.iloc[0]["ism_median"])
    band585 = tuple(100.0 * x for x in gis_targets.MATCHED_2300_M["SSP5-8.5"])

    print(f"=== TARGETS ({len(ref)} CMIP6 cells; SICOPOLIS held {HOLD_WIN}) ===")
    print(f"  {'exp':8}{'forcing':22}{'ISM med 2100':>13}{'ours 2100':>11}"
          f"{'SICO 2300':>11}{'ours 2300':>11}{f'SICO {Y_LAST}':>11}{'ours':>10}")
    for e in ref.index:
        print(f"  {e:8}{EXPS[e][0]:22}{ismed[e]:13.1f}{base[e][ie[2100]]:11.1f}"
              f"{sico[e][2300]:11.1f}{base[e][ie[2300]]:11.1f}"
              f"{sico[e][Y_LAST]:11.1f}{base[e][ie[Y_LAST]]:10.1f}")
    r0 = {y: np.array([base[e][ie[y]] /
                       (ismed[e] if y == 2100 else sico[e][y]) for e in ref.index])
          for y in HORIZONS}
    print(f"\n  BASE, no reservoir -- ours/target by horizon:")
    for y in HORIZONS:
        print(f"    {y:<6} {r0[y].min():.2f}-{r0[y].max():.2f}x   "
              f"(median {np.median(r0[y]):.2f})")
    print(f"  ssp585@2300 {base['SSP5-8.5'][ie[2300]]:.1f} cm "
          f"(matched band {band585[0]:.0f}-{band585[1]:.0f});  "
          f"ssp245@2300 {base['SSP2-4.5'][ie[2300]]:.1f};  "
          f"ssp126@2300 {base['SSP1-2.6'][ie[2300]]:.1f}\n")

    # --- the ONSET FLOOR, measured before the grid is built -------------------
    iw = (YEARS_EXT >= CALIB_WIN[0]) & (YEARS_EXT <= CALIB_WIN[1])
    per, raw, floor = onset_floor(gmst, iw)
    print(f"=== THE ONSET FLOOR IS MEASURED, NOT ASSUMED -- max GMST inside the "
          f"calibration window {CALIB_WIN} ===")
    for k in sorted(per, key=per.get, reverse=True):
        lab = EXPS[k][0] if k in EXPS else k
        mark = "  <- SETS THE FLOOR" if per[k] == raw else ""
        print(f"  {lab:24}{per[k]:8.4f} K{mark}")
    ours_max = max(per[l] for l in OURS)
    print(f"\n  floor = {raw:.4f} K, rounded up to {floor:.2f} K.")
    print(f"  OUR OWN drivers top out at {ours_max:.3f} K -- so the floor is set by "
          f"the GCM cells,\n  which joined the scoring set only when the "
          f"Greve/ISMIP6 targets did. A scan built on\n  the 1.398 K figure would "
          f"silently refit the hindcast.")
    print(f"  CONSEQUENCE FOR THE LADDER: Yelmo-REMBO's threshold (1.68-1.76 K) sits "
          f"only\n  {1.68 - raw:.3f} K above the floor and is testable; anything "
          f"BELOW {floor:.2f} K is NOT reachable by\n  prior-propagation at all and "
          f"would be a refit question.\n")
    ONSET_SCAN_K = list(np.round(np.arange(floor, ONSET_MAX_K + 1e-9,
                                           ONSET_STEP_K), 4))

    # --- the scan -------------------------------------------------------------
    rows, ginert_worst = [], 0.0
    for on in ONSET_SCAN_K + [ONSET_SHIPPED_K]:
        for V in V_SCAN_M:
            for tau in TAU_SCAN_YR:
                unit = {k: reservoir_unit(g, on, tau) for k, g in gmst.items()}
                ginert_worst = max(ginert_worst,
                                   max(float(np.max(np.abs(u[iw])))
                                       for u in unit.values()))
                addc = {k: CM_PER_M * V * u for k, u in unit.items()}
                rec = dict(onset_K=on, V_m=V, tau_yr=tau,
                           psi_cm_per_yr=CM_PER_M * V / tau,
                           shipped_onset=bool(on == ONSET_SHIPPED_K),
                           psi_in_greve=bool(PSI_EVIDENCE[0]
                                             <= CM_PER_M * V / tau
                                             <= PSI_EVIDENCE[1]))
                for y in HORIZONS:
                    lr = np.array([np.log((base[e][ie[y]] + addc[e][ie[y]])
                                          / (ismed[e] if y == 2100 else sico[e][y]))
                                   for e in ref.index])
                    rec[f"score_{y}"] = float(np.sqrt(np.mean(lr ** 2)))
                    rec[f"ratio_{y}_med"] = float(np.exp(np.median(lr)))
                rec["score_all"] = float(np.sqrt(np.mean(
                    [rec[f"score_{y}"] ** 2 for y in HORIZONS])))
                for lab in OURS:
                    rec[f"{SSP_KEY[lab]}_2300_cm"] = base[lab][ie[2300]] + \
                        addc[lab][ie[2300]]
                    rec[f"{SSP_KEY[lab]}_2100_cm"] = base[lab][ie[2100]] + \
                        addc[lab][ie[2100]]
                rec["ssp585_in_band"] = bool(band585[0] <= rec["ssp585_2300_cm"]
                                             <= band585[1])
                rec["within_inventory"] = bool(V <= GIS_V0_M)
                rows.append(rec)
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    # --- GATE 2: G-INERT ------------------------------------------------------
    print(f"=== G-INERT GATE -- max |reservoir ramp| over the calibration window "
          f"{CALIB_WIN}, over ALL {len(out)} cells x every driver ===")
    print(f"  {ginert_worst:.3e}")
    if ginert_worst != 0.0:
        sys.exit(f"G-INERT FAILED at {ginert_worst:.3e}: an onset this low is NOT "
                 f"calibration-inert, so this is a REFIT question, not a "
                 f"prior-propagation one. The measured floor is "
                 f"{floor:.2f} K.")
    print(f"  EXACTLY zero => every onset down to the measured floor "
          f"{floor:.2f} K is still prior-propagatable.\n")

    # --- the result -----------------------------------------------------------
    base_all = float(np.sqrt(np.mean([np.mean(np.log(r0[y]) ** 2)
                                      for y in HORIZONS])))
    print(f"=== THE SCAN -- {len(ONSET_SCAN_K)} onsets x {len(V_SCAN_M)} V x "
          f"{len(TAU_SCAN_YR)} tau (+ the shipped onset as a reference row) ===")
    print(f"  BASELINE (no reservoir) score_all = {base_all:.3f}\n")
    print(f"  BEST CELL AT EACH ONSET (by score_all, within inventory):")
    print(f"  {'onset':>7}{'V_m':>7}{'tau':>7}{'psi':>7}{'  all':>8}{'  2100':>8}"
          f"{'  2300':>8}{f'  {Y_LAST}':>8}{'  585@2300':>11}{'band':>6}"
          f"{'  245@2300':>11}")
    for on in ONSET_SCAN_K + [ONSET_SHIPPED_K]:
        s = out[(out.onset_K == on) & out.within_inventory]
        b = s.loc[s.score_all.idxmin()]
        tagon = " <- SHIPPED" if b.shipped_onset else ""
        print(f"  {b.onset_K:>7.2f}{b.V_m:>7.2f}{b.tau_yr:>7.0f}"
              f"{b.psi_cm_per_yr:>7.3f}{b.score_all:>8.3f}{b.score_2100:>8.3f}"
              f"{b.score_2300:>8.3f}{b[f'score_{Y_LAST}']:>8.3f}"
              f"{b.ssp585_2300_cm:>11.1f}{'  in' if b.ssp585_in_band else ' OUT':>6}"
              f"{b.ssp245_2300_cm:>11.1f}{tagon}")

    print(f"\n  THE TRADE, made explicit -- 2100 can only get WORSE (the reservoir is "
          f"ADDITIVE\n  and our 2100 is already high), so read these two columns "
          f"together:")
    print(f"  {'onset':>7}{'best 2300+3001 score':>22}{'2100 score':>13}"
          f"{'2100 ratio (ours/ISM med)':>28}")
    for on in ONSET_SCAN_K + [ONSET_SHIPPED_K]:
        s = out[(out.onset_K == on) & out.within_inventory].copy()
        s["late"] = np.sqrt((s.score_2300 ** 2 + s[f"score_{Y_LAST}"] ** 2) / 2)
        b = s.loc[s.late.idxmin()]
        print(f"  {on:>7.2f}{b.late:>22.3f}{b.score_2100:>13.3f}"
              f"{b.ratio_2100_med:>28.2f}x")
    base2100 = float(np.sqrt(np.mean(np.log(r0[2100]) ** 2)))
    print(f"  (baseline 2100 score {base2100:.3f}, ratio "
          f"{np.median(r0[2100]):.2f}x -- the 1.30x ISMIP6 fast bias)")

    # --- THE PREMISE OF THE SHIPPED ONSET, TESTED -----------------------------
    print(f"\n=== DOES THE SHIPPED {ONSET_SHIPPED_K} K ONSET STILL DO THE JOB IT WAS "
          f"CHOSEN FOR? ===")
    print(f"  It exists because memory `gis_tap_priced_l13` records it as \"exactly "
          f"the 'don't move\n  2100' constraint\". That was evaluated on OUR fair_mean "
          f"ssp585 driver. Crossing years:")
    for k, g in gmst.items():
        lab = EXPS[k][0] if k in EXPS else k
        c = np.where(g >= ONSET_SHIPPED_K)[0]
        yr = str(int(YEARS_EXT[c[0]])) if len(c) else "never"
        mark = "   <- the driver the onset was tuned against" if lab == "SSP5-8.5" else ""
        print(f"    {lab:24}{yr:>8}{mark}")
    print(f"\n  Our own ssp585 crosses at exactly 2100 -- by construction. The FOUR "
          f"ssp585 GCM cells\n  that carry the ISMIP6 and Greve evidence cross 13-31 "
          f"years EARLIER, so the reservoir\n  is already running before 2100 on every "
          f"one of them.")
    shp = out[(out.onset_K == ONSET_SHIPPED_K) & (out.V_m == 1.0)
              & (out.tau_yr == 800.0)]
    if len(shp):
        b = shp.iloc[0]
        print(f"\n  MEASURED on the actual shipped cell (V=1.0 m, tau=800 yr): the "
              f"2100 median ratio\n  moves {np.median(r0[2100]):.2f}x -> "
              f"{b.ratio_2100_med:.2f}x. **The shipped onset does NOT hold 2100 fixed "
              f"on the\n  cells the 2100 evidence lives on.** It holds it fixed on one "
              f"driver: the one it was\n  tuned against. The 'protect 2100' argument "
              f"for keeping 4.69 K is therefore already\n  spent, independently of the "
              f"ladder evidence.")
        f8 = out[(out.V_m == 1.0) & (out.tau_yr == 800.0)].sort_values("score_all")
        bb = f8.iloc[0]
        print(f"\n  AND AT THE SHIPPED V AND tau, LOWERING THE ONSET IS UNAMBIGUOUSLY "
              f"BETTER:\n  score_all {b.score_all:.3f} at {ONSET_SHIPPED_K} K vs "
              f"{bb.score_all:.3f} at {bb.onset_K:g} K -- and {ONSET_SHIPPED_K} K is "
              f"the WORST of the\n  {len(f8)} onsets at that cell. The earlier "
              f"per-onset table let V and tau float, which\n  masked this.")

    print(f"\n  CELLS WHOSE psi SITS IN THE GREVE RANGE {PSI_EVIDENCE} AND WHOSE "
          f"ssp585@2300 IS IN BAND:")
    q = out[out.psi_in_greve & out.ssp585_in_band & out.within_inventory]
    if q.empty:
        print("    NONE.")
    else:
        q = q.sort_values("score_all")
        print(f"    {len(q)} cells; best 8 by score_all:")
        print(f"    {'onset':>7}{'V_m':>7}{'tau':>7}{'psi':>7}{'  all':>8}"
              f"{'  2100':>8}{'  2300':>8}{f'  {Y_LAST}':>8}{'  245@2300':>11}")
        for _, b in q.head(8).iterrows():
            print(f"    {b.onset_K:>7.2f}{b.V_m:>7.2f}{b.tau_yr:>7.0f}"
                  f"{b.psi_cm_per_yr:>7.3f}{b.score_all:>8.3f}{b.score_2100:>8.3f}"
                  f"{b.score_2300:>8.3f}{b[f'score_{Y_LAST}']:>8.3f}"
                  f"{b.ssp245_2300_cm:>11.1f}")
    print(f"\n  ssp245@2300 IS A DIAGNOSTIC, NOT A GATE (Marcus 2026-08-23). Its "
          f"shipped matched\n  band top is "
          f"{100 * gis_targets.MATCHED_2300_M['SSP2-4.5'][1]:.1f} cm and the base "
          f"sits at {base['SSP2-4.5'][ie[2300]]:.1f}; the values above are printed "
          f"so its\n  leverage stays visible without being imposed.")
    print(f"\nWROTE {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
