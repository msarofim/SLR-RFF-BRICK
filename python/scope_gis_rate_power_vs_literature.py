#!/usr/bin/env python3
"""
scope_gis_rate_power_vs_literature.py — can a CONVEX rate law on the FAST (SMB)
channel break the ssp585/ssp245 ratio ceiling that Leq scaling provably cannot?

WHY THIS EXISTS (2026-08-18, handoff §5)
  scope_gis_leq_ridge_vs_literature.py established that no point on the phi*Leq
  ridge fixes ssp585@2300: the ssp585/ssp245 ratio at 2300 is capped at ~3.4x
  against a literature demand of ~8-32x, because a linear Leq ties the scenarios
  together. At k=1 both scenarios are ~99% equilibrated, so realised = Leq and
  the ratio IS the Leq ratio. To break it you need DIFFERENTIAL EQUILIBRATION —
  the cooler scenario far from a (raised) commitment while the hotter one closes
  on it — and the only term in A+B that can produce that is a rate that is small
  at low T and large at high T.

THE LAW (asymmetric BY DESIGN — the physics differs between the channels)
    r_f(T) = alpha_f * Tbar * (max(T,0)/Tbar)^p + beta_f     FAST/SMB: convex
    r_s(T) = alpha_s * T + beta_s                            SLOW/dynamic: UNCHANGED
  Fast-channel convexity is well-motivated (PDD threshold convexity, bare-ice
  albedo expansion, firn saturation/ice slabs — MacFerrin 2019 doi
  10.1038/s41586-019-1550-3). Dynamic discharge is NOT convex — it self-limits
  (Aschwanden 2019 doi 10.1126/sciadv.aav9396; Shannon 2013 PNAS) — so the slow
  channel stays linear. Applying one superlinear law to both would be LESS
  physical than the incumbent.
  ANCHOR: at T = Tbar the fast rate equals alpha_f*Tbar + beta_f for EVERY p, so
  p rotates the law about the calibration point instead of rescaling it — the
  same discipline that makes the amp law identifiable. Tbar is DERIVED from the
  driver (ridge.gis_tbar asserts it against the Julia's constant), never
  hardcoded. max(T,0) is required, not cosmetic: the regional driver goes
  negative early in the record and a negative base with non-integer p is NaN.
  Consequence: at p=1 the family nests the incumbent EXCEPT in negative-driver
  years, where max(T,0) floors the fast rate at beta_f. The gap is MEASURED
  below (p=1 column vs the ridge CSV), not assumed away.

PRE-REGISTERED PREDICTIONS (handoff §5.5 — written before the first run)
  P1  ratio_585_over_245 rises MONOTONICALLY in p at every k
      (mechanism = differential equilibration)
  P2  some p in [1.5, 3] reaches the literature ratio band at some k
  P3  the hindcast stays satisfiable at every (k,p) — bisection converges,
      because the anchor pins the law near the hindcast temperatures
  P4  2100 G4 stays within 15% of the (k=1,p=1) value over the P2-passing cells

THE FALSIFIER (the likely one — D2's failure mode)
  If raising p mostly slows the HINDCAST-era rate and forces s up so far that
  everything rescales together, the ratio will not move — the fix would be doing
  nothing while appearing to fit. Watch for s moving by orders of magnitude with
  the ratio flat, and for railing. Either FIRING is a result, not a bug.

READS   the ridge scan's whole harness (posterior, targets, drivers, bands) plus
        outputs/scope_gis_leq_ridge_vs_literature.csv (reproduction gate)
WRITES  outputs/scope_gis_rate_power_vs_literature_<targetset>.csv

  source ~/climate-env/bin/activate
  python3 python/scope_gis_rate_power_vs_literature.py [--targets=matched|lit]
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
# the harness is defined ONCE, in the scripts that established the ridge. The
# posterior path, literature bands, Tbar derivation, (ell,w)->native mapping and
# the incumbent A+B series all come from there — do not re-implement.
import scope_gis_leq_ridge_vs_literature as ridge  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    GIS_V0_M, IREF, YEARS, gis_shape_table, gmst_rebased, regional_driver,
)

# --- named constants; every label below derives from these -------------------
LADRILLO_TAG = ridge.LADRILLO_TAG
POST, TARGETS = ridge.POST, ridge.TARGETS
HIND, HIND_DRIVER, SSPS = ridge.HIND, ridge.HIND_DRIVER, ridge.SSPS
## 2026-08-21g: scored against a NAMED target set. `--targets=lit` reproduces the
## published verdict (this family was killed at 4.71x against a 7.9-31.9x band);
## `--targets=matched` scores the forcing-matched bands, whose ratio floor is
## 2.00x. The set is in the printout AND the output filename.
import gis_targets  # noqa: E402
LIT_2300_M, TARGET_SET = gis_targets.from_argv(sys.argv)
TARGET_WORD = gis_targets.SET_WORD[TARGET_SET]
LIT_2300_NOTE = {lab: gis_targets.note(lab, TARGET_SET) for lab in LIT_2300_M}
RIDGE_CSV = ridge.OUT
OUT = gis_targets.out_path(
    os.path.join(REPO, "outputs/scope_gis_rate_power_vs_literature.csv"), TARGET_SET)

K_GRID = ridge.K_GRID                       # identical k axis to the ridge scan
P_GRID = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0]
G4_REF_CELL = (1.0, 1.0)                    # G4 judged RELATIVE to (k=1, p=1)
G4_DEGRADE_TOL = ridge.G4_DEGRADE_TOL       # >15% change in 2100 spread = broken

# pre-registered thresholds — set BEFORE the first run, do not tune afterwards
P2_P_BAND = (1.5, 3.0)                      # P2's "some p in 1.5-3"
HIND_RESID_TOL_CM = 0.02                    # P3: bisection converged
S_BOUNDS = (1e-4, 1e3)                      # same bisection box as the ridge
S_RAIL_FACTOR = 2.0                         # s within 2x of a bound = railed
FALSIFIER_S_INFLATION = 10.0                # s(k,pmax)/s(k,1) beyond this ...
FALSIFIER_RATIO_GAIN = 1.5                  # ... with ratio gain below this = fired
REPRO_KS = (1.0, 14.0, 50.0)                # gate cells re-run with the incumbent law
REPRO_TOL = 1e-9                            # same code path -> must match to fp noise
NEST_P = 1.0                                # the column measured against the ridge CSV


def ab_series_power(T, pa, k_c, s_r, p, tbar):
    """A+B at median params: commitment scaled by k_c, both channel rates by
    s_r, and the FAST channel's rate made convex in T with exponent p, anchored
    at tbar. The slow channel is byte-identical to the incumbent. Returns
    (loss, eq, rf, fast, slow)."""
    eq = np.clip(k_c * (pa["gis_c1"] * T + pa["gis_c0"]), 0.0, GIS_V0_M)
    f = pa["gis_f"]
    tpos = np.maximum(T, 0.0)               # negative base ** non-integer p = NaN
    rf = np.clip(s_r * (pa["gis_alpha_f"] * tbar * (tpos / tbar) ** p
                        + pa["gis_beta_f"]), 1e-9, 1.0)
    rs = np.clip(s_r * (pa["gis_alpha_s"] * T + pa["gis_beta_s"]), 1e-9, 1.0)
    fast = np.zeros_like(T)
    slow = np.zeros_like(T)
    for i in range(1, len(T)):
        fast[i] = fast[i - 1] + (f * eq[i - 1] - fast[i - 1]) * rf[i - 1]
        slow[i] = slow[i - 1] + ((1 - f) * eq[i - 1] - slow[i - 1]) * rs[i - 1]
    return fast + slow, eq, rf, fast, slow


def main():
    post = pd.read_csv(POST)
    tbar = ridge.gis_tbar()
    pa = ridge.native_greenland(post.median(numeric_only=True), tbar)
    # the anchor identity the whole scan rests on: at T = tbar the fast rate is
    # p-invariant, so p rotates the law about the calibration point
    r_anchor = pa["gis_alpha_f"] * tbar + pa["gis_beta_f"]
    for p in P_GRID:
        got = pa["gis_alpha_f"] * tbar * (tbar / tbar) ** p + pa["gis_beta_f"]
        assert abs(got - r_anchor) < 1e-12, "anchor broken — p rescales, not rotates"

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
    iproj = YEARS > HIND[1]

    def bisect_rate(loss_at):               # loss_at(s) -> loss series on Th
        lo, hi = S_BOUNDS
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            L = loss_at(mid)
            if 100.0 * (L[ih1] - L[ih0]) < want_cm:
                lo = mid
            else:
                hi = mid
        return float(np.sqrt(lo * hi))

    print(f"CAN A CONVEX FAST-CHANNEL RATE BREAK THE RATIO CEILING?  — Ladrillo "
          f"{LADRILLO_TAG}, median params, offline")
    print(f"  r_f(T) = alpha_f*Tbar*(max(T,0)/Tbar)^p + beta_f, anchored at "
          f"Tbar = {tbar:.4f} K; slow channel UNCHANGED")
    print(f"  hindcast {HIND[0]}-{HIND[1]} = {want_cm:.2f} cm, restored by "
          f"bisection at every (k,p)")

    # ---- reproduction gate: the incumbent law through THIS plumbing must ----
    # ---- reproduce the ridge CSV exactly (same code path, deterministic) ----
    rec = pd.read_csv(RIDGE_CSV).set_index("k")
    gate_fail = []
    for k in REPRO_KS:
        s = bisect_rate(lambda sv: ridge.ab_series(Th, pa, k, sv)[0])
        if abs(s - float(rec.loc[k, "rate_scale"])) > REPRO_TOL:
            gate_fail.append((k, "rate_scale", s, float(rec.loc[k, "rate_scale"])))
        for _, lab in SSPS:
            L, _ = ridge.ab_series(drivers[lab], pa, k, s)
            got = float(L[i23] - L[IREF].mean())
            want = float(rec.loc[k, f"m2300_{lab}"])
            if abs(got - want) > REPRO_TOL:
                gate_fail.append((k, f"m2300_{lab}", got, want))
    if gate_fail:
        print("\nREPRODUCTION GATE FAILED — this plumbing does not reproduce the "
              "ridge scan; refusing to scan:")
        for k, what, got, want in gate_fail:
            print(f"    k={k}: {what} offline {got:.6g} recorded {want:.6g}")
        raise SystemExit(1)
    print(f"  reproduction gate PASSED — incumbent law at k={REPRO_KS} matches "
          f"the ridge CSV to {REPRO_TOL:g}\n")

    # ---- the 2-D scan -------------------------------------------------------
    rows = []
    for k in K_GRID:
        for p in P_GRID:
            s = bisect_rate(lambda sv: ab_series_power(Th, pa, k, sv, p, tbar)[0])
            Lh = ab_series_power(Th, pa, k, s, p, tbar)[0]
            hind_resid = 100.0 * (Lh[ih1] - Lh[ih0]) - want_cm
            r = dict(tag=LADRILLO_TAG, k=k, p=p, rate_scale=s,
                     hind_resid_cm=hind_resid)
            for _, lab in SSPS:
                loss, eq, rf, fast, slow = ab_series_power(
                    drivers[lab], pa, k, s, p, tbar)
                r[f"m2300_{lab}"] = float(loss[i23] - loss[IREF].mean())
                r[f"m2100_{lab}"] = float(loss[i21] - loss[IREF].mean())
                r[f"in_band_{lab}"] = (LIT_2300_M[lab][0] <= r[f"m2300_{lab}"]
                                       <= LIT_2300_M[lab][1])
                r[f"phi_2300_{lab}"] = float(loss[i23] / eq[i23])
                r[f"phi_fast_2300_{lab}"] = float(fast[i23] / (pa["gis_f"] * eq[i23]))
                if lab == "SSP5-8.5":
                    r["leq_585_2300_m"] = float(eq[i23])
                    r["rf_clip_years_585"] = int((rf[iproj] >= 1.0 - 1e-12).sum())
            r["g4_2100_cm"] = 100.0 * (r["m2100_SSP5-8.5"] - r["m2100_SSP1-2.6"])
            r["ratio_585_over_245"] = r["m2300_SSP5-8.5"] / r["m2300_SSP2-4.5"]
            r["s_railed"] = (s <= S_BOUNDS[0] * S_RAIL_FACTOR
                             or s >= S_BOUNDS[1] / S_RAIL_FACTOR)
            rows.append(r)

    cell = {(r["k"], r["p"]): r for r in rows}
    g4_ref = cell[G4_REF_CELL]["g4_2100_cm"]
    for r in rows:
        r["g4_rel_to_ref"] = r["g4_2100_cm"] / g4_ref
        r["keeps_2100"] = abs(r["g4_rel_to_ref"] - 1.0) <= G4_DEGRADE_TOL
        r["s_rel_to_p1"] = r["rate_scale"] / cell[(r["k"], 1.0)]["rate_scale"]
        r["all_pass"] = (all(r[f"in_band_{lab}"] for _, lab in SSPS)
                         and r["keeps_2100"])

    # ---- nesting gap: the p=1 column vs the ridge CSV (max(T,0) is the only
    # ---- difference, and only in negative-driver years) ---------------------
    nest = []
    for k in K_GRID:
        r = cell[(k, NEST_P)]
        nest.append(max(abs(r[f"m2300_{lab}"] - float(rec.loc[k, f"m2300_{lab}"]))
                        for _, lab in SSPS))
    print(f"  nesting gap at p={NEST_P:g} (max |m2300 - ridge| over k, from "
          f"max(T,0) in negative-driver years): {max(nest):.2e} m\n")

    # ---- the headline grid: the ssp585/ssp245 ratio at 2300 -----------------
    lit_lo, lit_hi = gis_targets.ratio_band(LIT_2300_M)
    print("  " + gis_targets.banner(TARGET_SET).replace("\n", "\n  ") + "\n")
    print(f"=== ssp585/ssp245 RATIO AT 2300 — {TARGET_WORD} demands "
          f"{lit_lo:.2f}x-{lit_hi:.2f}x; the 1-D ridge capped at 3.36x ===\n")
    hdr = "  k \\ p " + "".join(f"{p:>8g}" for p in P_GRID)
    print(hdr)
    for k in K_GRID:
        line = f"  {k:6.1f} "
        for p in P_GRID:
            v = cell[(k, p)]["ratio_585_over_245"]
            mark = "*" if lit_lo <= v <= lit_hi else " "
            line += f"{v:7.2f}{mark}"
        print(line)
    print(f"\n  (* = ratio inside the {TARGET_WORD} band {lit_lo:.2f}-{lit_hi:.2f}x)\n")

    print("=== ssp585 @2300, m SLE — band "
          f"{LIT_2300_M['SSP5-8.5'][0]:.3f}-{LIT_2300_M['SSP5-8.5'][1]:.3f} "
          f"[{LIT_2300_NOTE['SSP5-8.5']}] ===\n")
    print(hdr)
    for k in K_GRID:
        line = f"  {k:6.1f} "
        for p in P_GRID:
            r = cell[(k, p)]
            mark = "*" if r["in_band_SSP5-8.5"] else " "
            line += f"{r['m2300_SSP5-8.5']:7.3f}{mark}"
        print(line)

    print("\n=== bands passed at 2300 (of 3) + 2100 kept -> 'P' = ALL PASS ===\n")
    print(hdr)
    for k in K_GRID:
        line = f"  {k:6.1f} "
        for p in P_GRID:
            r = cell[(k, p)]
            n = sum(r[f"in_band_{lab}"] for _, lab in SSPS)
            tag = "P" if r["all_pass"] else ("k" if r["keeps_2100"] else "x")
            line += f"{n:>6d}{tag} "
        print(line)
    print("\n  (k = 2100 kept within "
          f"{100 * G4_DEGRADE_TOL:.0f}% of (k,p)=({G4_REF_CELL[0]:g},"
          f"{G4_REF_CELL[1]:g}); x = 2100 broken)\n")

    # ---- pre-registered predictions ----------------------------------------
    print("=== PRE-REGISTERED PREDICTIONS (handoff 2026-08-18b §5.5) ===\n")

    p1_viol = []
    for k in K_GRID:
        rr = [cell[(k, p)]["ratio_585_over_245"] for p in P_GRID]
        if any(b < a - 1e-9 for a, b in zip(rr, rr[1:])):
            p1_viol.append(k)
    print(f"  P1 ratio monotone in p at every k: "
          f"{'PASS' if not p1_viol else f'FAIL at k={p1_viol}'}")

    p2_cells = [r for r in rows
                if P2_P_BAND[0] <= r["p"] <= P2_P_BAND[1]
                and lit_lo <= r["ratio_585_over_245"] <= lit_hi]
    best = max(rows, key=lambda r: r["ratio_585_over_245"])
    print(f"  P2 some p in {P2_P_BAND} reaches the ratio band: "
          f"{'PASS' if p2_cells else 'FAIL'}  "
          f"(best ratio anywhere {best['ratio_585_over_245']:.2f}x at "
          f"k={best['k']:g}, p={best['p']:g})")

    p3_bad = [r for r in rows
              if abs(r["hind_resid_cm"]) > HIND_RESID_TOL_CM or r["s_railed"]]
    print(f"  P3 hindcast satisfiable at every (k,p): "
          f"{'PASS' if not p3_bad else f'FAIL at {[(r['k'], r['p']) for r in p3_bad]}'}")

    if p2_cells:
        p4_bad = [r for r in p2_cells if not r["keeps_2100"]]
        print(f"  P4 2100 G4 within {100 * G4_DEGRADE_TOL:.0f}% over P2 cells: "
              f"{'PASS' if not p4_bad else f'FAIL at {[(r['k'], r['p']) for r in p4_bad]}'}")
    else:
        print("  P4 vacuous — no P2 cells to test")

    # ---- the falsifier ------------------------------------------------------
    print("\n=== THE FALSIFIER — does p just rescale s (D2's 'fit by deleting "
          "the machinery') ? ===\n")
    print(f"  {'k':>6s} {'s(p=1)':>9s} {'s(pmax)':>9s} {'s infl':>7s} "
          f"{'ratio(1)':>9s} {'ratio(pmax)':>11s} {'gain':>6s}  verdict")
    fired = []
    pmax = P_GRID[-1]
    for k in K_GRID:
        s1, sp = cell[(k, 1.0)]["rate_scale"], cell[(k, pmax)]["rate_scale"]
        r1 = cell[(k, 1.0)]["ratio_585_over_245"]
        rp = cell[(k, pmax)]["ratio_585_over_245"]
        infl, gain = sp / s1, rp / r1
        f_fired = infl > FALSIFIER_S_INFLATION and gain < FALSIFIER_RATIO_GAIN
        if f_fired:
            fired.append(k)
        print(f"  {k:6.1f} {s1:9.4f} {sp:9.4f} {infl:7.2f} {r1:9.2f} {rp:11.2f} "
              f"{gain:6.2f}  {'FIRED' if f_fired else 'no'}")
    print(f"\n  falsifier ({'s x>' + format(FALSIFIER_S_INFLATION, 'g')} with "
          f"ratio gain <{FALSIFIER_RATIO_GAIN:g}): "
          f"{'FIRED at k=' + str(fired) if fired else 'not fired at any k'}")

    # ---- mechanism check at the best cell: differential equilibration -------
    print(f"\n=== MECHANISM at the best-ratio cell (k={best['k']:g}, "
          f"p={best['p']:g}) — phi at 2300 ===\n")
    for _, lab in SSPS:
        print(f"  {lab:9s} phi_total {best[f'phi_2300_{lab}']:.3f}   "
              f"phi_fast {best[f'phi_fast_2300_{lab}']:.3f}")
    print(f"  (shipped k=1,p=1 was ~0.99 everywhere: equilibrated. The mechanism "
          f"needs ssp245 LOW, ssp585 HIGH.)")
    print(f"  fast-rate clip years, ssp585 projection, best cell: "
          f"{best['rf_clip_years_585']} of {int(iproj.sum())}")

    # ---- verdict ------------------------------------------------------------
    winners = [r for r in rows if r["all_pass"]]
    print("\n=== VERDICT ===\n")
    if winners:
        print("  Cells satisfying ALL 2300 bands AND keeping 2100:")
        for r in winners:
            print(f"    k={r['k']:g} p={r['p']:g}: "
                  + " ".join(f"{lab} {r[f'm2300_{lab}']:.3f}" for _, lab in SSPS)
                  + f", ratio {r['ratio_585_over_245']:.2f}x, "
                  f"G4 {r['g4_rel_to_ref']:.2f}x of ref")
        print("\n  -> the convex fast-channel rate CAN clear everything offline;")
        print("     pricing a real refit (chain, both arms) is now justified.")
    else:
        nb = max(rows, key=lambda r: (sum(r[f"in_band_{lab}"] for _, lab in SSPS),
                                      r["keeps_2100"]))
        print("  NO cell clears all three 2300 bands while keeping 2100.")
        print(f"  Best cell: k={nb['k']:g} p={nb['p']:g} — "
              f"{sum(nb[f'in_band_{lab}'] for _, lab in SSPS)}/3 bands, "
              f"2100 {'kept' if nb['keeps_2100'] else 'broken'}, "
              f"ratio {nb['ratio_585_over_245']:.2f}x")
        print("  -> per handoff §5.6: (b) a threshold form carrying both Leq and")
        print("     rate, or (c) ship 2300/ssp585 with the shortfall as a stated")
        print("     caveat. (c) is a legitimate outcome; 2100 is unaffected.")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
