#!/usr/bin/env python3
"""
scope_gis_3basin_partition.py — can THREE basins on ONE Greenland driver
reproduce the observed Mouginot sector partition AND the calibration total at
once, and how much does the south basin's calibration move once it stops
absorbing the other basins' loss?

WHY THIS EXISTS (2026-08-18, handoff 2026-08-18e §5)
  The basin mock's MID-basin dormancy premise is false. Scored against Mouginot
  Dataset S2, NW is the single most OVER-active region in Greenland — 17.3% of
  the volume, 31.7% of the 1972-2018 loss (ratio 1.83) — while the mock holds it
  dormant. Only the high basin's premise survives (NO+NE, ratio 0.54). The
  consequence for the shipped model is the real problem: A+B is calibrated to
  TOTAL Greenland loss while driven by SOUTH-zone temperature alone, so its
  fitted parameters are compensating for mass that came from other basins.

  Same discipline as the whole arc: prove the structure offline BEFORE pricing
  the calibrator restructure. The mock proved the 2300 separation was
  representable; this asks the strictly harder question, and it can fail.

THE DESIGN BEING PROTOTYPED (Marcus, 2026-08-18)
  Basins = Mouginot SECTORS: south {SW,CW,CE,SE} / mid {NW} / high {NO,NE}.
  A SINGLE Greenland amplification on the `all` driver — so the sector geometry
  lives entirely in the LIKELIHOOD, not in the drivers. south keeps A+B
  fast/slow; mid is an ACTIVE channel with NO tap (Aschwanden's NW transition is
  a DECELERATION at 2300, the opposite sign from a tap); high is a small active
  channel PLUS the volume tap.

THE REDUCED PARAMETERISATION, AND WHY IT IS HONEST
  There is one posterior, fitted to the total on the south driver; three basins'
  full parameter sets cannot be re-fitted offline without a chain. So each basin
  keeps the shipped A+B SHAPE parameters, its equilibrium commitment is scaled
  by its own volume share (k_b = V0_b / V0), and the ONE free knob per basin is
  its rate scale s_b — bisected exactly as the ridge harness does. Three free
  parameters, three sector observations: exactly identified. That makes the
  TOTAL a genuine out-of-sample PREDICTION, which is the test.

TWO DATA FACTS THAT SHAPE THE TEST, both measured here and not assumed away
  1. The calibration target and Mouginot DISAGREE on the total: over 1972-2018
     the target says 1.689 cm, Mouginot's sector sum says 1.377 cm — a factor
     1.227. Plausibly peripheral glaciers/ice caps, which Mouginot's drainage
     sectors exclude and a GIS budget term may not — NOT verified here, so it is
     flagged, not explained. The fit therefore uses Mouginot for the SHARES ONLY
     and the target for the TOTAL; nothing re-litigates the calibration total.
  2. Mouginot's window is 1972-2018 but the calibration window is 1900-2025, and
     **the target puts 3.715 cm of 5.781 cm — 64% — BEFORE 1972**. So the
     partition is pinned over barely a third of the signal and the pre-1972 era
     is entirely out-of-sample for it. That is what makes the total a real test,
     and it is also the single biggest caveat on the whole restructure.

THE QUESTIONS, FIXED BEFORE RUNNING
  P1  fitted to the 1972-2018 partition, does the 3-basin model reproduce the
      1900-2025 TOTAL the calibration target demands? By how much does it miss?
      **P1 IS USELESS WITHOUT ITS CONTROL**, and a first draft of this script
      shipped without one and drew the wrong conclusion from it. The SINGLE
      basin -- no partition, no reduction -- must be run through the same
      two-window test, because if IT also misses, the tension belongs to the
      model/driver/target and cannot be charged to the partition.
  P2  how far does the south basin's rate scale move once it carries only its
      own sector's loss, and what does that do to its 2300 projection? This is
      the number that decides whether the restructure moves the headline.
  P3  does the 2300 scorecard still clear with a high-basin tap on top?
  FALSIFIER: if P1 misses the total badly AND the single-basin control does
  not, the shared-driver / volume-proportional-commitment reduction is too stiff
  and the restructure needs per-basin commitment parameters too. If BOTH miss,
  the finding is about the model/driver/target rather than the partition, and
  the per-sector likelihood term will PULL AGAINST the total term in the real
  calibrator — a weighting problem to anticipate, not a reduction to fix.

READS   the ridge harness (posterior, targets, bands, ab_series), the Mouginot
        Dataset S2 parse in diag_gis_basin_lit_check, gis_amp_shape_all.csv
WRITES  outputs/scope_gis_3basin_partition.csv

  source ~/climate-env/bin/activate
  python3 python/scope_gis_3basin_partition.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
import scope_gis_leq_ridge_vs_literature as ridge  # noqa: E402
import diag_gis_basin_lit_check as lit  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    GIS_V0_M, IREF, SSPS, YEARS, gmst_rebased,
)
from diag_gis_zone_driver_scope import amp_mean, shape_fun, zone_driver  # noqa: E402

# --- the design, as named constants -----------------------------------------
DRIVER_ZONE = "all"            # single Greenland amp; geometry lives in the likelihood
AMP_WINDOW = "full"            # matches the shipped south choice
BASINS = {"south": ("SW", "CW", "CE", "SE"), "mid": ("NW",), "high": ("NO", "NE")}
TAPPED = "high"                # only NO+NE gets a volume tap
GT_PER_MM_SLE = 361.8
MOUGINOT_WIN = lit.DORMANCY_WIN            # (1972, 2018)
CALIB_WIN = ridge.HIND                     # (1900, 2025)
POST, TARGETS = ridge.POST, ridge.TARGETS
LIT_2300_M, G4_DEGRADE_TOL = ridge.LIT_2300_M, ridge.G4_DEGRADE_TOL
RIDGE_CSV, REPRO_TOL = ridge.OUT, 1e-9
OUT = os.path.join(REPO, "outputs/scope_gis_3basin_partition.csv")

# the tap grid — mid has NO tap now, so this is the high basin only
TAP_ONSET_K = [4.0, 5.0, 6.0, 7.0]         # GMT K rel 1850-1900
TAP_V_M = [0.5, 1.0, 1.5, 2.0, 2.5]        # m SLE, capped by the high inventory
TAP_TAU = [50, 100, 200, 400]
TAP_RAMP_W_K = 1.0


def bisect_rate(T, pa, k, want_m, i0, i1, lo=1e-4, hi=1e3, n=80):
    """Rate scale s such that the basin's loss over [i0, i1] equals want_m."""
    for _ in range(n):
        m = np.sqrt(lo * hi)
        L = ridge.ab_series(T, pa, k, m)[0]
        if (L[i1] - L[i0]) < want_m:
            lo = m
        else:
            hi = m
    return float(np.sqrt(lo * hi))


def tap_unit(G, t_on, tau):
    seq = np.clip((G - t_on) / TAP_RAMP_W_K, 0.0, 1.0)
    S = np.zeros_like(G)
    r = 1.0 / tau
    for i in range(1, len(G)):
        S[i] = S[i - 1] + (seq[i - 1] - S[i - 1]) * r
    return S


def main():
    post = pd.read_csv(POST)
    pa = ridge.native_greenland(post.median(numeric_only=True), ridge.gis_tbar())
    S_all = shape_fun(DRIVER_ZONE)
    amp = amp_mean(DRIVER_ZONE, AMP_WINDOW)

    drivers, gmt = {}, {}
    for ssp, lab in SSPS:
        _, rb = gmst_rebased(ssp)
        gmt[lab] = rb
        drivers[lab], _ = zone_driver(rb, DRIVER_ZONE, amp, S_all)
    T_hind = drivers[dict(SSPS)[ridge.HIND_DRIVER]]

    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in (CALIB_WIN[0], CALIB_WIN[1], MOUGINOT_WIN[0], MOUGINOT_WIN[1],
                     2100, 2300)}
    tgt = pd.read_csv(TARGETS).set_index("year")["gis"]
    tot_calib_cm = float(tgt.loc[CALIB_WIN[1]] - tgt.loc[CALIB_WIN[0]])
    tot_mou_cm = float(tgt.loc[MOUGINOT_WIN[1]] - tgt.loc[MOUGINOT_WIN[0]])

    # ---- the partition, from the parse the lit-check owns and gates ---------
    per = lit.sd02_per_region()
    tot_gt = sum(per[r]["cum_gt"] for r in lit.MOUGINOT_SLE_CM)
    share = {b: sum(per[s]["cum_gt"] for s in secs) / tot_gt
             for b, secs in BASINS.items()}
    v0 = {b: sum(lit.MOUGINOT_SLE_CM[s] for s in secs) / 100.0
          for b, secs in BASINS.items()}
    vshare = {b: v0[b] / sum(v0.values()) for b in BASINS}

    print("THREE BASINS ON ONE GREENLAND DRIVER — can they hold the partition "
          "AND the total?")
    print(f"  driver zone {DRIVER_ZONE!r}, single amp {amp:.4f} ({AMP_WINDOW}); "
          f"sectors = the likelihood's geometry")
    print(f"  calibration total {CALIB_WIN[0]}-{CALIB_WIN[1]} = "
          f"{tot_calib_cm:.3f} cm; Mouginot window {MOUGINOT_WIN[0]}-"
          f"{MOUGINOT_WIN[1]} = {tot_mou_cm:.3f} cm")
    mou_cm = -sum(per[r]["cum_gt"] for r in lit.MOUGINOT_SLE_CM) / (GT_PER_MM_SLE * 10)
    print(f"  Mouginot's own sector sum over that window = {mou_cm:.3f} cm "
          f"⇒ target/Mouginot = {tot_mou_cm / mou_cm:.3f}")
    print("    ⇒ SHARES from Mouginot, TOTAL from the target. The gap is "
          "flagged, not explained\n      (peripheral glaciers are the obvious "
          "candidate; not verified here).")
    frac_pre = float(tgt.loc[MOUGINOT_WIN[0]] - tgt.loc[CALIB_WIN[0]]) / tot_calib_cm
    print(f"  ⚠ {100 * frac_pre:.0f}% of the calibration signal predates "
          f"{MOUGINOT_WIN[0]} — the partition is pinned\n    over barely a "
          f"third of the window, so the total below is genuinely out-of-sample.\n")

    print(f"  {'basin':6s} {'sectors':18s} {'V0 m':>6s} {'%vol':>6s} "
          f"{'%loss':>6s} {'loss/vol':>9s}")
    for b, secs in BASINS.items():
        print(f"  {b:6s} {'+'.join(secs):18s} {v0[b]:6.2f} "
              f"{100 * vshare[b]:5.1f}% {100 * share[b]:5.1f}% "
              f"{share[b] / vshare[b]:9.2f}")
    print()

    # ---- P2 reference: the shipped single-basin fit, gated vs the ridge -----
    s_shipped = bisect_rate(T_hind, pa, 1.0, tot_calib_cm / 100.0,
                            idx[CALIB_WIN[0]], idx[CALIB_WIN[1]])
    rec = pd.read_csv(RIDGE_CSV).set_index("k")
    print(f"=== P2 reference — the SHIPPED single basin, refitted on the "
          f"{DRIVER_ZONE!r} driver ===\n")
    print(f"  rate scale s = {s_shipped:.4f}  (the south-driver value recorded "
          f"in the ridge k=1 row: {float(rec.loc[1.0, 'rate_scale']):.4f})")
    print("  NOTE these are not expected to match — the driver changed from "
          "'south' to 'all'.\n  That difference is itself part of what the "
          "restructure costs.\n")

    # ---- fit each basin to its own sector loss ------------------------------
    rows, loss = [], {}
    for b in BASINS:
        want = share[b] * tot_mou_cm / 100.0
        s_b = bisect_rate(T_hind, pa, vshare[b], want,
                          idx[MOUGINOT_WIN[0]], idx[MOUGINOT_WIN[1]])
        L = ridge.ab_series(T_hind, pa, vshare[b], s_b)[0]
        loss[b] = dict(s=s_b, L=L,
                       fit_cm=100.0 * (L[idx[MOUGINOT_WIN[1]]] - L[idx[MOUGINOT_WIN[0]]]),
                       want_cm=100.0 * want,
                       calib_cm=100.0 * (L[idx[CALIB_WIN[1]]] - L[idx[CALIB_WIN[0]]]))
        rows.append(dict(quantity="basin_fit", basin=b, v0_m=v0[b],
                         vol_share=vshare[b], loss_share=share[b],
                         rate_scale=s_b, fit_cm=loss[b]["fit_cm"],
                         want_cm=loss[b]["want_cm"],
                         calib_window_cm=loss[b]["calib_cm"]))

    print(f"=== the fit — each basin to its OWN sector loss, "
          f"{MOUGINOT_WIN[0]}-{MOUGINOT_WIN[1]} ===\n")
    print(f"  {'basin':6s} {'k=vol share':>11s} {'rate s':>9s} "
          f"{'want cm':>8s} {'got cm':>8s}")
    for b in BASINS:
        print(f"  {b:6s} {vshare[b]:11.4f} {loss[b]['s']:9.4f} "
              f"{loss[b]['want_cm']:8.3f} {loss[b]['fit_cm']:8.3f}")
    resid = max(abs(loss[b]["fit_cm"] - loss[b]["want_cm"]) for b in BASINS)
    print(f"\n  max |fit - want| = {resid:.2e} cm  "
          f"({'exactly identified, as designed' if resid < 1e-6 else 'BISECTION FAILED'})")

    # ---- P1 CONTROL: the same two-window test with NO partition ------------
    s_ctl = bisect_rate(T_hind, pa, 1.0, tot_mou_cm / 100.0,
                        idx[MOUGINOT_WIN[0]], idx[MOUGINOT_WIN[1]])
    L_ctl = ridge.ab_series(T_hind, pa, 1.0, s_ctl)[0]
    ctl_pred = 100.0 * (L_ctl[idx[CALIB_WIN[1]]] - L_ctl[idx[CALIB_WIN[0]]])
    L_fwd = ridge.ab_series(T_hind, pa, 1.0, s_shipped)[0]
    fwd_pred = 100.0 * (L_fwd[idx[MOUGINOT_WIN[1]]] - L_fwd[idx[MOUGINOT_WIN[0]]])
    rows.append(dict(quantity="p1_control_single_basin", basin="ALL",
                     fit_cm=ctl_pred, want_cm=tot_calib_cm))

    # ---- P1: the total, out-of-sample --------------------------------------
    pred = sum(loss[b]["calib_cm"] for b in BASINS)
    print(f"\n=== P1 — the {CALIB_WIN[0]}-{CALIB_WIN[1]} TOTAL, predicted not "
          f"fitted ===\n")
    for b in BASINS:
        print(f"  {b:6s} contributes {loss[b]['calib_cm']:7.3f} cm")
    print(f"  {'SUM':6s}             {pred:7.3f} cm   target "
          f"{tot_calib_cm:7.3f} cm")
    print(f"  miss = {pred - tot_calib_cm:+.3f} cm "
          f"({100 * (pred / tot_calib_cm - 1):+.1f}%)")
    rows.append(dict(quantity="total_prediction", basin="ALL",
                     fit_cm=pred, want_cm=tot_calib_cm,
                     calib_window_cm=pred - tot_calib_cm))
    ctl_miss = ctl_pred / tot_calib_cm - 1.0
    miss = pred / tot_calib_cm - 1.0
    print(f"\n  CONTROL — the SINGLE basin, no partition, same two-window test:")
    print(f"    fitted {MOUGINOT_WIN[0]}-{MOUGINOT_WIN[1]}, predicts "
          f"{ctl_pred:.3f} cm for {CALIB_WIN[0]}-{CALIB_WIN[1]} "
          f"({100 * ctl_miss:+.1f}%)")
    print(f"    fitted {CALIB_WIN[0]}-{CALIB_WIN[1]}, predicts {fwd_pred:.3f} cm "
          f"for {MOUGINOT_WIN[0]}-{MOUGINOT_WIN[1]} "
          f"(target {tot_mou_cm:.3f}, {100 * (fwd_pred / tot_mou_cm - 1):+.1f}%)")
    if abs(ctl_miss) > 0.10:
        print(f"\n  VERDICT P1: the two-window tension is PRE-EXISTING — the "
              f"single basin misses by\n    {100 * ctl_miss:+.1f}% with NO "
              f"partition at all, against the 3-basin {100 * miss:+.1f}%. The "
              f"partition is NOT\n    the cause; it slightly "
              f"{'REDUCES' if abs(miss) < abs(ctl_miss) else 'WORSENS'} the "
              f"tension. This is a finding about the\n    model / driver / "
              f"target across these two windows, not about the basin split.")
        print(f"\n    ⇒ CONSEQUENCE FOR THE RESTRUCTURE: a per-sector "
              f"likelihood term can only constrain\n      "
              f"{MOUGINOT_WIN[0]}-{MOUGINOT_WIN[1]}, while the total term "
              f"constrains {CALIB_WIN[0]}-{CALIB_WIN[1]}. They PULL AGAINST\n"
              f"      each other by ~{100 * abs(ctl_miss):.0f}%. The calibrator "
              f"must weight them deliberately; left\n      implicit this shows "
              f"up as a biased compromise or as poor mixing.")
    else:
        print(f"\n  VERDICT P1: {'PASS' if abs(miss) <= 0.15 else 'MISS'} — the "
              f"control is clean ({100 * ctl_miss:+.1f}%), so the "
              f"{100 * miss:+.1f}% belongs to the reduction")

    # ---- P2: what moved for the south basin --------------------------------
    print(f"\n=== P2 — what the south basin's calibration does when it stops "
          f"absorbing the others ===\n")
    print("  Comparing LIKE WITH LIKE: the 3-basin SUM is the whole ice sheet, "
          "so it is the\n  single basin's counterpart. (A first draft compared "
          "the SOUTH BASIN ALONE against\n  the single basin and made the "
          "restructure look like a halving — it is 45.6% of the\n  volume, so "
          "of course it is smaller. Rate scales are likewise NOT comparable "
          "across\n  different k: the ridge showed k and s trade off exactly.)\n")
    for lab in ("SSP2-4.5", "SSP5-8.5"):
        Lg = ridge.ab_series(drivers[lab], pa, 1.0, s_shipped)[0]
        g23 = 100.0 * (Lg[idx[2300]] - Lg[IREF].mean())
        tot = np.zeros(len(YEARS))
        for b in BASINS:
            tot = tot + ridge.ab_series(drivers[lab], pa, vshare[b], loss[b]["s"])[0]
        t23 = 100.0 * (tot[idx[2300]] - tot[IREF].mean())
        sou = ridge.ab_series(drivers[lab], pa, vshare["south"],
                              loss["south"]["s"])[0]
        s23 = 100.0 * (sou[idx[2300]] - sou[IREF].mean())
        print(f"  {lab} @2300: single basin {g23:7.2f} cm   3-basin SUM "
              f"{t23:7.2f} cm   ({t23 / g23:.3f}x)")
        print(f"  {'':9s}          of which south {s23:7.2f} cm "
              f"({100 * s23 / t23:.0f}% of the sum, vs {100 * vshare['south']:.0f}% "
              f"of the volume)")
        rows.append(dict(quantity="p2_2300", basin=lab, fit_cm=t23, want_cm=g23,
                         calib_window_cm=s23))

    # ---- P3: the 2300 scorecard with a high-basin tap ----------------------
    base23, base21 = {}, {}
    for _, lab in SSPS:
        tot = np.zeros(len(YEARS))
        for b in BASINS:
            tot = tot + ridge.ab_series(drivers[lab], pa, vshare[b], loss[b]["s"])[0]
        base23[lab] = float(tot[idx[2300]] - tot[IREF].mean())
        base21[lab] = float(tot[idx[2100]] - tot[IREF].mean())
    print(f"\n=== P3 — the 3-basin base, before any tap (m SLE rel 1995-2014) "
          f"===\n")
    for _, lab in SSPS:
        lo_, hi_ = LIT_2300_M[lab]
        print(f"  {lab:9s} 2300 {base23[lab]:6.3f}   band {lo_:.3f}-{hi_:.3f}"
              f"   {'IN' if lo_ <= base23[lab] <= hi_ else 'out'}")
    g4_base = 100.0 * (base21["SSP5-8.5"] - base21["SSP1-2.6"])

    head_high = v0["high"] - float(np.clip(
        vshare["high"] * (pa["gis_c1"] * drivers["SSP5-8.5"][idx[2300]]
                          + pa["gis_c0"]), 0, v0["high"]))
    npass = 0
    for t_on in TAP_ONSET_K:
        for V in TAP_V_M:
            if V > head_high:
                continue
            for tau in TAP_TAU:
                r = dict(quantity="p3_cell", basin=TAPPED, tap_onset_K=t_on,
                         tap_V_m=V, tap_tau=tau)
                ok = True
                for _, lab in SSPS:
                    u = tap_unit(gmt[lab], t_on, tau)
                    m23 = base23[lab] + V * u[idx[2300]]
                    r[f"m2300_{lab}"] = m23
                    r[f"dorm2100_{lab}"] = V * u[idx[2100]]
                    ok &= LIT_2300_M[lab][0] <= m23 <= LIT_2300_M[lab][1]
                g4 = g4_base + 100.0 * (r["dorm2100_SSP5-8.5"]
                                        - r["dorm2100_SSP1-2.6"])
                r["g4_rel_to_base"] = g4 / g4_base
                ok &= abs(g4 / g4_base - 1.0) <= G4_DEGRADE_TOL
                r["all_pass"] = ok
                npass += int(ok)
                rows.append(r)
    ncell = sum(1 for t in TAP_ONSET_K for V in TAP_V_M
                for _ in TAP_TAU if V <= head_high)
    print(f"\n  high-basin inventory headroom {head_high:.2f} m; tap grid "
          f"{ncell} cells")
    print(f"  cells clearing all three 2300 bands + G4 within "
          f"{100 * G4_DEGRADE_TOL:.0f}%: {npass}/{ncell}")
    print(f"  VERDICT P3: {'PASS' if npass else 'NO cell clears — report, do not tune'}")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
