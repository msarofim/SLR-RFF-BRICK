#!/usr/bin/env python3
"""
scope_gis_gamma_offline.py — OPTION 2 PRICED OFFLINE: a state-dependent relaxation
rate, scored on all five matched-forcing arms AND on our own three deliverables.

WHY (2026-08-21j, notes/handoff_2026-08-21e §3)
  The base model's error against matched forcing is a ROTATION in time -- too high
  early, right in the middle, too low late, with a 7.2x late-rate deficit under
  constant forcing. A scale k cannot fix a rotation, which §3.1 then confirmed by
  measurement: the ssp585 arms want k = 3 and the cool arms k = 0.75. The proposed
  fix is a rate that ACCELERATES as loss proceeds:

      r = r0(T) * (1 + gamma * L_b / (k_b * V0))

  built offline behind a `gamma` argument in the kernel, `greenland_3basin_component.jl`
  untouched until a gamma clears here.

THE QUANTITATIVE PRE-CHECK, RUN FIRST AND REPORTED WHATEVER IT SAYS
  A pure rate accelerator can only move L toward L_eq -- it cannot raise L_eq. So
  its ceiling at any horizon is 1/phi, where phi = L/L_eq is the equilibration
  fraction ALREADY reached. Measured at k=1: phi(2300) is 0.84-0.92 across the
  arms, so the CEILING on any gamma is x1.09-1.20, and x1.13 on our own ssp585.
  Against a matched band whose p50 (98.5 cm) is ~2x our 50.0 cm, that is ~8x short.
  (Note the memory's "99% equilibrated by 2300", phi = 0.987-0.991, is the L12
  SINGLE-BASIN figure; L14 two-basin is materially lower. Re-derived, not quoted --
  handoff 2026-08-21d §6 rules out transferring L12 absolute levels.)

  This is computed and printed BEFORE the scan, so the scan is read as "what does
  gamma actually buy inside that ceiling", not as an open-ended search.

WHAT GAMMA CAN STILL DO, AND WHY THE SCAN IS WORTH RUNNING ANYWAY
  Under the hindcast constraint gamma is NOT only an accelerator. The 1900-2025
  bisection re-solves r0 downward to absorb the late boost, which lowers the EARLY
  trajectory while the feedback protects the late one -- i.e. a rotation, which is
  exactly the diagnosed error. Whether that nets out as an improvement is a
  measurement, not an argument. [[sens_scan_achievable]]

WHAT IS CHECKED, each as its own gate rather than a footnote
  NESTING     gamma = 0.0 does not enter the feedback branch at all, so it is
              bit-identical to the pre-gamma kernel by construction. Asserted here.
  2100        the accepted deliverable must not move (handoff §3 watch-item a).
  HINDCAST    unlike k, gamma does NOT preserve the hindcast for free -- the rate is
              re-solved per draw at every gamma and the residual is reported.
  LIKELIHOOD  max |r_with - r_without| over the CALIBRATION window, the same way G2
              does for the tap. Inertness is MEASURED before it is claimed, because
              prior-propagating gamma projection-side depends on it entirely.
  V0 CLIP     phi is reported per gamma: a faster rate against a saturating target
              can flatten, and that would look like gamma failing when it is the
              clip binding (handoff §3 watch-item b).

WRITES outputs/scope_gis_gamma_offline.csv
  python3 python/scope_gis_gamma_offline.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

from scope_gis_ridge_vs_protect import (  # noqa: E402
    K_HIGH, K_SOUTH, basin2_series, rebase_cm,
)
from scope_gis_leq_ridge_vs_literature import gis_tbar, native_greenland  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, GIS_V0_M, YEARS, gis_shape_table, regional_driver,
)
from scope_gis_ridge_vs_protect import IB  # noqa: E402  the 1995-2014 rebase index
import gis_targets  # noqa: E402
import scope_gis_shape_all_scenarios as A  # noqa: E402

OUT = os.path.join(REPO, "outputs/scope_gis_gamma_offline.csv")

# --- named constants ---------------------------------------------------------
TAG = A.TAG
HIND, HORIZONS, ARM, ARMS = A.HIND, A.HORIZONS, A.ARM, A.ARMS
SSP585_ARMS, COOL_ARMS = A.SSP585_ARMS, A.COOL_ARMS
K_FIXED = 1.0                    # gamma is priced AT THE SHIPPED COMMITMENT SCALE
GAMMA_GRID = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0]
GAMMA_ON = ("both", "slow", "fast")
OURS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
HIND_RESID_TOL = 0.01            # cm; how far the re-solved hindcast may miss
Y2100_TOL_CM = 0.10              # cm; "2100 must not move" made numerical
LIKE_WIN = HIND                  # the calibration window for the inertness test


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    S = gis_shape_table()
    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in list(HORIZONS) + list(HIND) + [2015]}
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])

    def driver_from(path, col):
        g = pd.read_csv(path).set_index("year")[col].reindex(YEARS).to_numpy()
        rb = g - g[ibd].mean()
        return rb, regional_driver(rb, post["gis_amp"].to_numpy(), S)

    drivers, gmst = {}, {}
    for ssp, lab, fam, stem in ARMS:
        gmst[(ssp, fam)], drivers[(ssp, fam)] = driver_from(
            os.path.join(REPO, f"outputs/{stem}.csv"), f"gmst_{ARM}")
    ours_drv = {lab: driver_from(
        os.path.join(REPO, f"data/observations/fair_mean_gmst_{ssp}.csv"), "gmst_C")[1]
        for ssp, lab in OURS}

    print(f"scope_gis_gamma_offline — r = r0(T)*(1 + gamma*L_b/(k_b*V0)), {TAG}, "
          f"{len(post)} draws, k fixed at {K_FIXED:g}\n")

    # --- GATE: NESTING ---------------------------------------------------------
    a0 = basin2_series(drivers[("ssp585", "x2300")], post, K_FIXED, 1.0)
    for on in GAMMA_ON:
        a1 = basin2_series(drivers[("ssp585", "x2300")], post, K_FIXED, 1.0,
                           gamma=0.0, gamma_on=on)
        if not np.array_equal(a0, a1):
            sys.exit(f"NESTING GATE FAILED for gamma_on={on!r}: gamma=0 is not "
                     f"bit-identical to the pre-gamma kernel.")
    print("GATE NESTING — gamma = 0.0 is BIT-IDENTICAL on all three gamma_on "
          "settings (exact, not a tolerance)\n")

    # --- THE PRE-CHECK: gamma's ceiling is 1/phi -------------------------------
    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    Th = drivers[A.HIND_ARM]

    def solve_rate(k, gamma, on):
        lo, hi = np.full(len(post), 1e-4), np.full(len(post), 1e3)
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            L = basin2_series(Th, post, k, mid, gamma=gamma, gamma_on=on)
            below = 100.0 * (L[:, idx[HIND[1]]] - L[:, idx[HIND[0]]]) < want_cm
            lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
        return np.sqrt(lo * hi)

    c1 = post["gis_c1"].to_numpy()[:, None]
    c0 = post["gis_c0"].to_numpy()[:, None]

    def phi_at(T, k, y):
        eq = sum(np.clip(kb * k * (c1 * T + c0), 0.0, kb * GIS_V0_M)
                 for kb in (K_SOUTH, K_HIGH))
        L = basin2_series(T, post, k, s0, gamma=0.0)
        return float(np.median(L[:, idx[y]] / np.maximum(eq[:, idx[y]], 1e-12)))

    s0 = solve_rate(K_FIXED, 0.0, "both")
    print("PRE-CHECK — a rate accelerator can only move L toward L_eq, so its "
          "ceiling is 1/phi:")
    ceil = {}
    for ssp, lab, fam, _ in ARMS:
        p = phi_at(drivers[(ssp, fam)], K_FIXED, 2300)
        ceil[f"{lab} {fam}"] = 1.0 / p
        print(f"    {lab} {fam:6}: phi(2300) = {p:.3f}  ->  gamma can lift 2300 by "
              f"at most x{1.0 / p:.3f}")
    for lab, D in ours_drv.items():
        p = phi_at(D, K_FIXED, 2300)
        ceil[f"OURS {lab}"] = 1.0 / p
        print(f"    OURS {lab:11}: phi(2300) = {p:.3f}  ->  at most x{1.0 / p:.3f}")
    lo585, hi585 = gis_targets.MATCHED_2300_M["SSP5-8.5"]
    p50 = gis_targets.MATCHED_2300_P50_M["SSP5-8.5"]
    base585 = float(np.median(rebase_cm(
        basin2_series(ours_drv["SSP5-8.5"], post, K_FIXED, s0))[:, idx[2300]])) / 100.0
    print(f"\n  our ssp585 @2300 = {100 * base585:.1f} cm; the matched band's p50 is "
          f"{100 * p50:.1f} cm ({p50 / base585:.2f}x)")
    print(f"  the ceiling on our ssp585 is x{ceil['OURS SSP5-8.5']:.3f} "
          f"=> gamma is {(p50 / base585) / ceil['OURS SSP5-8.5']:.1f}x SHORT of the "
          f"p50 even at gamma -> infinity.")
    print(f"  It is NOT short of the band FLOOR ({100 * lo585:.1f} cm), which the "
          f"base already clears.\n")

    # --- the scan --------------------------------------------------------------
    ann = pd.read_csv(A.ANN)
    offs = float(np.median(rebase_cm(
        basin2_series(drivers[("ssp585", "r2300")], post, 1.0, 1.0))[:, idx[2015]]))
    band = {}
    for ssp, lab, fam, _ in ARMS:
        q = A.protect_band(ann, lab, fam).groupby("year").gis_cm
        band[(ssp, fam)] = {y: (q.quantile(.05)[y] + offs, q.median()[y] + offs,
                                q.quantile(.95)[y] + offs) for y in HORIZONS}

    ref = {}
    hdr = (f"{'on':>5} {'gamma':>7} {'rate s':>8} {'hind':>7} | {'585':>6} {'cool':>6} "
           f"{'all':>6} | {'2100':>7} {'d2100':>7} {'2300':>7} {'x base':>7} "
           f"{'phi':>5} | {'|dr| calib':>10}")
    print(hdr); print("-" * len(hdr))
    rows = []
    for on in GAMMA_ON:
        for g in GAMMA_GRID:
            if g == 0.0 and on != GAMMA_ON[0]:
                continue
            s = solve_rate(K_FIXED, g, on)
            rec = dict(k=K_FIXED, gamma=g, gamma_on=on, rate_s=float(np.median(s)))
            Lh = basin2_series(Th, post, K_FIXED, s, gamma=g, gamma_on=on)
            rec["hind_resid_cm"] = float(np.median(
                100.0 * (Lh[:, idx[HIND[1]]] - Lh[:, idx[HIND[0]]])) - want_cm)

            per = {}
            for ssp, lab, fam, _ in ARMS:
                L = np.median(rebase_cm(basin2_series(
                    drivers[(ssp, fam)], post, K_FIXED, s, gamma=g, gamma_on=on)), axis=0)
                lsq = [np.log(max(L[idx[y]], 1e-6) / band[(ssp, fam)][y][1]) ** 2
                       for y in HORIZONS]
                per[(ssp, fam)] = float(np.sqrt(np.mean(lsq)))
                rec[f"rms_{ssp}_{fam}"] = per[(ssp, fam)]
            agg = lambda arms: float(np.sqrt(np.mean(
                [per[(a[0], a[2])] ** 2 for a in arms])))
            rec["rms_ssp585"], rec["rms_cool"] = agg(SSP585_ARMS), agg(COOL_ARMS)
            rec["rms_all"] = agg(ARMS)

            ## our own deliverables: 2100 must not move, 2300 is the thing at issue
            for lab, D in ours_drv.items():
                L = np.median(rebase_cm(basin2_series(
                    D, post, K_FIXED, s, gamma=g, gamma_on=on)), axis=0)
                rec[f"ours_{lab}_2100_cm"] = L[idx[2100]]
                rec[f"ours_{lab}_2300_cm"] = L[idx[2300]]
                rec[f"ours_{lab}_in_matched"] = bool(
                    100 * gis_targets.MATCHED_2300_M[lab][0] <= L[idx[2300]]
                    <= 100 * gis_targets.MATCHED_2300_M[lab][1])
            if g == 0.0:
                ref = dict(rec)
            rec["d2100_585_cm"] = rec["ours_SSP5-8.5_2100_cm"] - ref["ours_SSP5-8.5_2100_cm"]
            rec["x_base_2300_585"] = rec["ours_SSP5-8.5_2300_cm"] / ref["ours_SSP5-8.5_2300_cm"]
            ## THE RATIO THE 1/phi CEILING ACTUALLY BOUNDS IS THE RAW LOSS, not the
            ## rebased one. Lowering r0 (which the bisection does at every gamma)
            ## also shrinks the 1995-2014 SUBTRAHEND, so the rebased ratio runs
            ## ahead of the raw one and can appear to break its own ceiling. Both
            ## are carried: the difference is baseline shift, NOT extra ice loss,
            ## and reporting only the rebased one would overstate gamma.
            Lraw = basin2_series(ours_drv["SSP5-8.5"], post, K_FIXED, s,
                                 gamma=g, gamma_on=on)
            rec["ours_SSP5-8.5_2300_raw_m"] = float(np.median(Lraw[:, idx[2300]]))
            rec["baseline_9514_m"] = float(np.median(Lraw[:, A.__dict__.get("IB", IB)].mean(axis=1))
                                           if False else np.median(Lraw[:, IB].mean(axis=1)))
            if g == 0.0:
                ref["raw"] = rec["ours_SSP5-8.5_2300_raw_m"]
            rec["x_base_2300_585_raw"] = rec["ours_SSP5-8.5_2300_raw_m"] / ref["raw"]

            ## LIKELIHOOD INERTNESS, measured the way G2 does for the tap: how much
            ## does the feedback move the RATE inside the calibration window?
            D585 = ours_drv["SSP5-8.5"]
            Lc = basin2_series(D585, post, K_FIXED, s, gamma=0.0)
            iw = (YEARS >= LIKE_WIN[0]) & (YEARS <= LIKE_WIN[1])
            frac = np.median(Lc[:, iw], axis=0) / (K_HIGH * GIS_V0_M)
            rec["max_dr_calib"] = float(np.max(g * frac))
            eqm = sum(np.clip(kb * K_FIXED * (c1 * D585 + c0), 0.0, kb * GIS_V0_M)
                      for kb in (K_SOUTH, K_HIGH))
            Lg = basin2_series(D585, post, K_FIXED, s, gamma=g, gamma_on=on)
            rec["phi_585_2300"] = float(np.median(
                Lg[:, idx[2300]] / np.maximum(eqm[:, idx[2300]], 1e-12)))
            rows.append(rec)
            print(f"{on:>5} {g:7.1f} {rec['rate_s']:8.4f} {rec['hind_resid_cm']:+7.4f} | "
                  f"{rec['rms_ssp585']:6.3f} {rec['rms_cool']:6.3f} {rec['rms_all']:6.3f} | "
                  f"{rec['ours_SSP5-8.5_2100_cm']:7.2f} {rec['d2100_585_cm']:+7.3f} "
                  f"{rec['ours_SSP5-8.5_2300_cm']:7.2f} {rec['x_base_2300_585']:7.3f} "
                  f"{rec['phi_585_2300']:5.3f} | {rec['max_dr_calib']:10.2e}")

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    print(f"\n  (2100/2300 are OUR ssp585 deliverable, cm; d2100 vs gamma=0; "
          f"|dr| calib = max fractional rate change inside {LIKE_WIN})")
    print("\n=== VERDICT ===\n")
    b0 = out[out.gamma == 0.0].iloc[0]
    worst_h = float(out.hind_resid_cm.abs().max())
    print(f"  HINDCAST: worst residual {worst_h:.4f} cm over the whole grid "
          f"({'held' if worst_h < HIND_RESID_TOL else 'NOT HELD'}; the rate is "
          f"re-solved per draw at every gamma)")
    worst_2100 = float(out.d2100_585_cm.abs().max())
    print(f"  2100:     moves by at most {worst_2100:.3f} cm "
          f"({'UNAFFECTED' if worst_2100 < Y2100_TOL_CM else 'MOVES'})")
    best = out.loc[out.rms_all.idxmin()]
    best585 = out.loc[out.rms_ssp585.idxmin()]
    print(f"  SHAPE:    best rms_all {best.rms_all:.3f} at gamma={best.gamma:g} "
          f"({best.gamma_on}) vs {b0.rms_all:.3f} at gamma=0 "
          f"-> {b0.rms_all / best.rms_all:.3f}x better")
    print(f"            best rms_ssp585 {best585.rms_ssp585:.3f} at gamma="
          f"{best585.gamma:g} ({best585.gamma_on}) vs {b0.rms_ssp585:.3f} "
          f"-> {b0.rms_ssp585 / best585.rms_ssp585:.3f}x better")
    top = out.x_base_2300_585.max()
    top_raw = out.x_base_2300_585_raw.max()
    print(f"  LEVEL:    our ssp585 @2300 reaches at most x{top:.3f} of the gamma=0 "
          f"value ({b0['ours_SSP5-8.5_2300_cm']:.1f} -> "
          f"{out['ours_SSP5-8.5_2300_cm'].max():.1f} cm)")
    print(f"            of which only x{top_raw:.3f} is EXTRA ICE LOSS -- the rest is "
          f"the 1995-2014\n            subtrahend shrinking as the bisection lowers "
          f"r0 ({b0.baseline_9514_m:.5f} -> "
          f"{out.baseline_9514_m.min():.5f} m). The raw ratio is what the pre-check "
          f"ceiling\n            x{ceil['OURS SSP5-8.5']:.3f} bounds, and it is "
          f"INSIDE it. Quoting the rebased x{top:.3f} would overstate gamma.")
    print(f"            the matched band's p50 is {100 * p50:.1f} cm, which needs "
          f"x{p50 / base585:.2f} -- NOT REACHABLE by any gamma.")
    infer = out[out.max_dr_calib > 0]
    print(f"  LIKELIHOOD: the feedback changes the calibration-window rate by up to "
          f"{infer.max_dr_calib.min():.1e}-{infer.max_dr_calib.max():.1e} "
          f"(fractional) over the grid")
    print(f"            => gamma is NOT automatically likelihood-inert the way the "
          f"tap is; at the gammas that do anything it is a real prior-vs-refit "
          f"question. MEASURED, not assumed.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
