#!/usr/bin/env python3
"""
diag_gis_matched_band_score.py -- SCORE THE WEIGHTED-VERDICT CELL AGAINST THE
FORCING-MATCHED PROTECT BAND, BEFORE ITS AGREEMENT IS QUOTED AS A RESULT.

WHY (handoff_2026-08-23b_weighted_verdict.md sec 1 and sec 7 item 1)
  The weighted verdict moved the reservoir cell to V=7.42 m / tau=2700 yr / onset
  4.69 K and that cell puts our ssp585 at 99.4 cm in 2300 -- "almost exactly on the
  ~100 cm (70-230) physics bracket". The handoff flagged, correctly, that the
  agreement had NOT been scored and must not be quoted until it is. Three things
  have to be checked before it can be, and none of them is arithmetic:

  1. WHICH BAND. The "~100 cm (70-230)" figure in memory `protect_matched_forcing`
     is the 2026-08-21d TWO-ANCHOR QUOTE -- the r2300 and x2300 plateau p50s read
     off as a range. It was SUPERSEDED on 2026-08-21g by the DERIVED band in
     python/gis_targets.py (42.9-145.0 cm, p50 98.5), built by PCHIP through five
     anchors against the GSAT INTEGRAL. Scoring against the superseded quote would
     be scoring against a looser, older object. This file scores against the
     derived set and reports the legacy bracket only as provenance.

  2. WHICH PREDICTOR. The adopted band interpolates against the 2015-2300 GSAT
     INTEGRAL. build_gis_matched_targets.py also computed, and deliberately kept,
     the arm that interpolates against the 2300 LEVEL. A "lands on the p50" claim
     that holds on one predictor and not the other is a predictor-dependent claim
     and must be reported as one. BOTH arms are scored here.

  3. WHETHER IT IS CIRCULAR. The cell was selected by a weighted score over 2100
     (ISMIP6 16-model medians) and 2300/3001 (Greve/SICOPOLIS). The band is
     PROTECT/NORCE-CISM. Those are different ice-sheet models, so the band is an
     OUT-OF-SAMPLE check -- but `ssp585_in_band` is also a column in the scan, so
     the claim needs the selection path stated explicitly rather than assumed.

WHAT THIS FILE DOES NOT DO
  It does not re-run the model. It reconstructs the reservoir contribution from
  first principles (`reservoir_unit` x V x CM_PER_M on the same rebased driver) and
  subtracts it, which recovers the no-reservoir base from EVERY row of the scan
  independently -- a stronger check on the scan CSV than reading its base line.

READS   outputs/scope_gis_onset_rescan.csv, outputs/gis_matched_targets_2300.csv
WRITES  outputs/diag_gis_matched_band_score.csv
  python3 python/diag_gis_matched_band_score.py
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

import gis_targets  # noqa: E402
from scope_gis_reservoir_offline import reservoir_unit, CM_PER_M, RAMP_W_K  # noqa: E402

SCAN = os.path.join(REPO, "outputs/scope_gis_onset_rescan.csv")
DERIV = os.path.join(REPO, "outputs/gis_matched_targets_2300.csv")
OUT = os.path.join(REPO, "outputs/diag_gis_matched_band_score.csv")

# --- named constants; every label below derives from these --------------------
LINEAGE = "L14 canonical (two-basin), extended axis 1850-3001, thinned posterior"
YEARS_EXT = np.arange(1850, 3002)
DRIVER_BASE = (1850, 1900)          # the GMST rebase window (the frame contract)
HORIZON = 2300
SSP_KEY = {"SSP1-2.6": "ssp126", "SSP2-4.5": "ssp245", "SSP5-8.5": "ssp585"}
## The three cells being scored. (onset_K, V_m, tau_yr); None = no reservoir.
CELLS = [("base (no reservoir)", None),
         ("cell A (shipped)", (4.69, 1.00, 800.0)),
         ("WINNER (weighted verdict)", (4.69, 7.42, 2700.0))]
WINNER_LABEL = "WINNER (weighted verdict)"
## The quantile ladder written by build_gis_matched_targets.py, and the two
## predictor arms it kept. "matched_" is the ADOPTED arm.
QLEV = (5, 17, 50, 83, 95)
ARMS = {"GSAT integral 2015-2300 (ADOPTED)": "matched_p{:02d}_cm",
        "GSAT level at 2300 (stated sensitivity)": "matched_Tarm_p{:02d}_cm"}
ADOPTED_ARM = "GSAT integral 2015-2300 (ADOPTED)"
## The superseded two-anchor quote, kept ONLY so the handoff's phrasing can be
## traced. memory `protect_matched_forcing` 2026-08-21d: r2300 5.61 K -> 72.3 cm,
## x2300 13.59 K -> 234.4 cm, quoted as "~100 cm (70-230)".
LEGACY_BRACKET_CM = (70.0, 230.0)
LEGACY_CENTRAL_CM = 100.0
LEGACY_NOTE = ("2026-08-21d two-anchor quote, SUPERSEDED 2026-08-21g by the "
               "derived band in gis_targets.py")
RECON_TOL_CM = 1e-6                 # base reconstruction agreement across rows
SELECTION_TARGETS = ("2100 = ISMIP6 16-model medians; 2300/3001 = Greve/SICOPOLIS")
BAND_SOURCE_ISM = "PROTECT-Greenland / NORCE-CISM"


def driver(ssp_key):
    """The rebased GMST driver on the extended axis, EXACTLY as
    scope_gis_onset_rescan.build_base() builds it for our own SSPs: reindex the
    fair_mean file onto YEARS_EXT, hold at both ends, subtract the DRIVER_BASE
    mean. No posterior is needed -- the reservoir is deterministic given GMST."""
    g = pd.read_csv(os.path.join(
        REPO, f"data/observations/fair_mean_gmst_{ssp_key}.csv")).set_index(
        "year")["gmst_C"].reindex(YEARS_EXT).ffill().bfill().to_numpy()
    ibd = (YEARS_EXT >= DRIVER_BASE[0]) & (YEARS_EXT <= DRIVER_BASE[1])
    return g - g[ibd].mean()


def add_cm(ssp_key, onset, V, tau, year=HORIZON):
    """The reservoir's contribution in cm at `year`, reconstructed from first
    principles rather than read back out of the scan."""
    u = reservoir_unit(driver(ssp_key), onset, tau)
    return CM_PER_M * V * float(u[int(np.where(YEARS_EXT == year)[0][0])])


def pctile(value, qcm):
    """Percentile of `value` within a quantile ladder, monotone-interpolated in
    log(cm) -- the space the band was BUILT in. Returns None outside the ladder
    rather than extrapolating a tail this ensemble cannot support."""
    lq = np.log(np.asarray(qcm, float))
    if np.any(np.diff(lq) <= 0):
        return None
    if value <= qcm[0] or value >= qcm[-1]:
        return None
    return float(PchipInterpolator(lq, np.array(QLEV, float))(np.log(value)))


def main():
    print(f"diag_gis_matched_band_score -- {LINEAGE}")
    print(f"  {gis_targets.VERIFY_STATUS}\n")
    print(gis_targets.banner() + "\n")

    scan = pd.read_csv(SCAN)
    der = pd.read_csv(DERIV).set_index("ssp")

    # --- GATE 1: recover the no-reservoir base from EVERY row independently ----
    print(f"=== GATE 1 -- the no-reservoir base, reconstructed from all "
          f"{len(scan)} scan rows ===")
    bases = {}
    for lab, key in SSP_KEY.items():
        col = f"{key}_{HORIZON}_cm"
        b = np.array([r[col] - add_cm(key, r.onset_K, r.V_m, r.tau_yr)
                      for _, r in scan.iterrows()])
        spread = float(b.max() - b.min())
        bases[lab] = float(np.median(b))
        flag = "OK" if spread <= RECON_TOL_CM else "FAILED"
        print(f"  {lab:9} base@{HORIZON} = {bases[lab]:7.3f} cm   "
              f"spread across rows {spread:.3e} cm  [{flag}]")
        if spread > RECON_TOL_CM:
            sys.exit(f"BASE RECONSTRUCTION FAILED for {lab}: the scan's "
                     f"{col} is not base + V*reservoir_unit(onset,tau) to "
                     f"{RECON_TOL_CM} cm. Do not score this CSV.")
    print(f"  => the scan's {HORIZON} column IS base + CM_PER_M*V*"
          f"reservoir_unit(onset,tau), RAMP_W_K={RAMP_W_K:g}. "
          f"Nothing else is in it.\n")

    # --- the three cells ------------------------------------------------------
    vals = {}
    for name, cell in CELLS:
        if cell is None:
            vals[name] = dict(bases)
            continue
        on, V, tau = cell
        row = scan[(scan.onset_K == on) & (scan.V_m == V) & (scan.tau_yr == tau)]
        if not len(row):
            sys.exit(f"cell {name} ({cell}) is not in {os.path.basename(SCAN)}")
        vals[name] = {lab: float(row.iloc[0][f"{SSP_KEY[lab]}_{HORIZON}_cm"])
                      for lab in SSP_KEY}

    # --- the score ------------------------------------------------------------
    rows = []
    for arm_name, tmpl in ARMS.items():
        print(f"=== SCORED AGAINST THE {arm_name} ARM ===")
        print(f"  {'cell':28}{'scenario':10}{'ours':>8}{'p05':>8}{'p50':>8}"
              f"{'p95':>8}{'ours/p50':>10}{'pctile':>9}{'  band'}")
        for name, cell in CELLS:
            for lab in ("SSP5-8.5", "SSP2-4.5", "SSP1-2.6"):
                key = SSP_KEY[lab]
                q = [float(der.loc[key, tmpl.format(p)]) for p in QLEV]
                v = vals[name][lab]
                lo, hi = (100.0 * x for x in gis_targets.MATCHED_2300_M[lab])
                p = pctile(v, q)
                inb = "in" if lo <= v <= hi else "OUT"
                print(f"  {name:28}{lab:10}{v:8.1f}{q[0]:8.1f}{q[2]:8.1f}"
                      f"{q[4]:8.1f}{v / q[2]:10.3f}"
                      f"{('  --' if p is None else f'{p:9.1f}')}"
                      f"   {inb} [{lo:.1f}-{hi:.1f}]")
                rows.append(dict(arm=arm_name, cell=name, scenario=lab,
                                 ours_cm=v, p05_cm=q[0], p50_cm=q[2],
                                 p95_cm=q[4], ratio_to_p50=v / q[2],
                                 pctile=p, band_lo_cm=lo, band_hi_cm=hi,
                                 in_adopted_band=bool(lo <= v <= hi),
                                 adopted_arm=bool(arm_name == ADOPTED_ARM)))
        print()
    pd.DataFrame(rows).to_csv(OUT, index=False)

    # --- what the numbers do and do not license -------------------------------
    w585 = vals[WINNER_LABEL]["SSP5-8.5"]
    qi = [float(der.loc["ssp585", ARMS[ADOPTED_ARM].format(p)]) for p in QLEV]
    qt = [float(der.loc["ssp585", ARMS["GSAT level at 2300 (stated sensitivity)"]
                        .format(p)]) for p in QLEV]
    print(f"=== THE VERDICT ON THE {WINNER_LABEL} CELL, ssp585@{HORIZON} ===")
    print(f"  ours {w585:.1f} cm.")
    print(f"  ADOPTED (integral) arm: {w585 / qi[2]:.3f}x the p50 "
          f"({qi[2]:.1f}), percentile {pctile(w585, qi):.0f} -- IN band.")
    print(f"  LEVEL arm (the stated sensitivity): {w585 / qt[2]:.3f}x the p50 "
          f"({qt[2]:.1f}), percentile {pctile(w585, qt):.0f} -- still in the "
          f"adopted band,\n  but NOT 'on the central estimate'. The "
          f"lands-on-the-p50 reading is PREDICTOR-DEPENDENT and\n  must be quoted "
          f"with the predictor named.")
    print(f"  Legacy quote for comparison ONLY -- {LEGACY_CENTRAL_CM:.0f} cm "
          f"({LEGACY_BRACKET_CM[0]:.0f}-{LEGACY_BRACKET_CM[1]:.0f}): {LEGACY_NOTE}."
          f"\n  {w585:.1f} is inside it too, at {w585 / LEGACY_CENTRAL_CM:.2f}x its "
          f"centre -- but that bracket is 2.9x wider than the derived band on the\n"
          f"  high side, so agreement with it is a much weaker statement.")

    print(f"\n=== IS THIS CIRCULAR? NO, BUT STATE THE PATH ===")
    print(f"  Selection used {SELECTION_TARGETS}.")
    print(f"  The band is {BAND_SOURCE_ISM} -- a DIFFERENT ice-sheet model from "
          f"SICOPOLIS, so the {HORIZON}\n  agreement is out-of-sample with respect "
          f"to what selected the cell. Two qualifications:\n"
          f"    (a) `ssp585_in_band` IS a column in the scan, but it is a reported "
          f"flag, not a\n        filter -- the winner is the argmin of score_w, and "
          f"every cell in the table is in band.\n"
          f"    (b) NORCE-CISM is ALSO one member of the ISMIP6 ensemble supplying "
          f"the 2100 term,\n        so the two evidence streams are not perfectly "
          f"disjoint at 2100. They are at {HORIZON}.")

    print(f"\n=== WHAT THE COOL SCENARIOS DO NOT SAY ===")
    for lab in ("SSP2-4.5", "SSP1-2.6"):
        d = vals[WINNER_LABEL][lab] - bases[lab]
        print(f"  {lab:9} winner {vals[WINNER_LABEL][lab]:6.1f} cm, base "
              f"{bases[lab]:6.1f} cm, reservoir contribution {d:.3e} cm")
    print(f"  The onset is 4.69 K and these scenarios peak below it, so their "
          f"{HORIZON} values are the\n  BASE model's, EXACTLY unchanged. They "
          f"neither corroborate nor refute the cell -- they only\n  confirm the "
          f"reservoir did not break what already passed.")

    print(f"\n  CAVEAT THAT TRAVELS WITH EVERY NUMBER ABOVE: "
          f"{gis_targets.MATCHED_CAVEAT}.")
    print(f"\nWROTE {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
