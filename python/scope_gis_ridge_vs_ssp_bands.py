#!/usr/bin/env python3
"""
scope_gis_ridge_vs_ssp_bands.py — pre-flight items 1-3 of the next calibration
(handoff 2026-08-21c §4): does the PROTECT-preferred ridge point k = 2-3 survive
the COOL scenarios, the G4 2100 spread, and the AR6 2100 Greenland band?

WHY THIS EXISTS (2026-08-21d)
  scope_gis_ridge_vs_protect.py scored the commitment/rate ridge against 200 yr
  of PROTECT trajectory SHAPE and found an interior optimum at k = 2-3
  (tau_slow 175-290 yr against the shipped 55), with the shipped k = 1 1.7x
  worse. That is one constraint. It is not the only one the shipped model has to
  meet, and the earlier endpoint scan (scope_gis_leq_ridge_vs_literature.py)
  measured the others -- BUT AT L12, ON THE SINGLE-BASIN A+B MODEL, AT MEDIAN
  PARAMETERS. Handoff 2026-08-21c §6 is explicit about what may and may not be
  carried across from that vintage: "their RATIO and relative-to-k=1 conclusions
  should survive; ANY ABSOLUTE LEVEL FROM THEM SHOULD BE RE-DERIVED, NOT QUOTED."

  Band membership IS an absolute-level claim. So it is re-derived here, on the
  SHIPPED L14 two-basin model, per draw, ensemble median, behind a reproduction
  gate against the shipped projection CSV.

WHAT MOVED FROM THE L12 SCAN, AND WHY IT MATTERS
  1. L12 -> L14: two basins with FIXED volume shares and a sampled high-basin
     rate scale that is LOG10 in the posterior. A linear read of gis_s_high
     freezes the high basin; that was one of the three bugs the PROTECT gate
     caught, and this script inherits the fixed kernel rather than retyping it.
  2. median parameters -> PER-DRAW ensemble median. This is not cosmetic for G4:
     the L12 scan had to score the 2100 spread RELATIVE to k = 1, because at
     median parameters it read 8.07 cm against an ENSEMBLE evaluation band of
     6.3-7.3 and would have wrongly indicted the shipped model. Running per draw
     removes that excuse, so G4 is reported BOTH ways here -- absolute against
     the band it was pre-registered on, and relative to k = 1.
  3. The K_GRID is DENSIFIED over 1.0-5.0, which is where the PROTECT optimum
     lives. The L12 grid did cover k = 2 and k = 3 (contrary to handoff §4 item 1,
     which says k = 2-3 "was never scored" -- it was; what was never done is
     scoring it at L14 per draw). The densification is so the pass/fail BOUNDARY
     in k is located, not just bracketed.

THE THREE PRE-FLIGHT QUESTIONS, EACH A KILL TEST FOR k = 2-3
  Q1  the cool scenarios: ssp126 and ssp245 at 2300 against their literature
      bands. Raising the commitment raises EVERY scenario, so a k that repairs
      ssp585 can push the cool arms out the top. (§4 item 1)
  Q2  the G4 2100 scenario spread, the pre-registered Greenland evaluation gate.
      (§4 item 2)
  Q3  AR6 2100: ssp585 Greenland must stay inside ~9-18 cm. (§4 item 3)

  The hindcast is NOT a fourth question here: it is imposed by per-draw
  bisection at every k, exactly as in the PROTECT scan, so it never
  discriminates. Whether a REFIT can actually reach it at k = 2-3 without
  railing gis_slow_ell is §4 item 4 and needs the calibrator, not this script.

REPRODUCTION GATE, per the standing discipline: at (k = 1, s = 1) this offline
emulator must reproduce the SHIPPED untapped L14 projection at every horizon on
every SSP to GATE_TOL before any k is reported. The posterior is thinned the way
the projection driver thins it (_ladrillo_thin, stride cld(n, NTHIN)) so the two
medians are taken over the SAME draws.

READS   data/MimiBRICK/parameters_subsample_brick_mengel_<TAG>.csv
        outputs/ssps_components_2300_<TAG>.csv   (the untapped shipped arm)
        outputs/recalib_targets_ext.csv
WRITES  outputs/scope_gis_ridge_vs_ssp_bands.csv

  source ~/climate-env/bin/activate
  python3 python/scope_gis_ridge_vs_ssp_bands.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
## The L14 two-basin kernel and the 1995-2014 rebase are DEFINED ONCE, in the
## script whose reproduction gate established them (and caught three bugs doing
## it). Imported, never retyped.
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import (  # noqa: E402
    G4_DEGRADE_TOL, G4_REF_K, LIT_2300_M, LIT_2300_NOTE, gis_tbar, native_greenland,
)
from scope_gis_2300_relaxation import (  # noqa: E402
    YEARS, gis_shape_table, gmst_rebased, regional_driver,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = "L14"
POST = os.path.join(REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{TAG}.csv")
SHIPPED = os.path.join(REPO, f"outputs/ssps_components_2300_{TAG}.csv")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
OUT = os.path.join(REPO, "outputs/scope_gis_ridge_vs_ssp_bands.csv")
SSPS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
HIND = (1900, 2025)
HIND_DRIVER = "SSP2-4.5"        # near-inert, but NOT exactly; MEASURED in cm below
HORIZONS = (2100, 2150, 2300)
## Densified over 1.0-5.0 (where the PROTECT optimum lives) and carried out to
## 50 so the ridge's V0-CLIP CEILING is re-derived at L14 rather than quoted
## from the L12 scan, whose absolute levels handoff 2026-08-21c §6 rules out.
K_GRID = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0, 8.0, 12.0, 14.0, 16.0,
          22.6, 32.0, 50.0]
NTHIN = 2000                    # _ladrillo_thin in julia/ladrillo_projection.jl
GATE_TOL = 0.5                  # cm; offline emulator vs the shipped projection
## t_gis_zones ends in 2024, so ONE year of the 1900-2025 hindcast window (2025)
## is already spliced and therefore scenario-dependent -- the drivers differ by
## 0.043 K there. The L12 scan called HIND_DRIVER "inert" on the assumption that
## history is entirely observed; it is not, quite. What matters is not that K
## difference but its CONSEQUENCE for the bisected rate, so the check below
## re-solves under every scenario's history and scores the spread in cm.
HIND_DRIVER_TOL_CM = 0.10       # cm; max spread in any reported horizon
## G4 = the pre-registered Greenland evaluation gate: the 2100 ssp585 - ssp126
## spread, cm. Band verbatim from GATE_SPREAD_RANGE_CM in
## julia/diag_gis_spread_2100_ladrillo.jl:55. It is an ENSEMBLE-median band, and
## this script runs per draw, so unlike the L12 median-parameter scan it can be
## applied directly. G4_DEGRADE_TOL (15% off k = 1) is kept alongside it.
GATE_SPREAD_RANGE_CM = (6.3, 7.3)
## AR6 Ch9 Greenland, ssp585 at 2100, cm rel 1995-2014. The repo's standing 2100
## sanity gate since notes/scoping_2026-08-16_thread5_greenland_2300.md ("2100
## sanity: SSP5-8.5 GIS stays inside AR6's ~9-18 cm").
AR6_GIS_2100_SSP585_CM = (9.0, 18.0)
## Reference warming level for the reported slow-channel tau, chosen to equal the
## tau@5.6K column of scope_gis_ridge_vs_protect.py so the two tables line up.
TAU_REF_K = 5.6


def thin(df, n):
    """Mirror julia/ladrillo_projection.jl _ladrillo_thin: evenly thin to <= n."""
    if len(df) <= n:
        return df.reset_index(drop=True)
    step = -(-len(df) // n)                       # cld(nrow, n)
    return df.iloc[::step].head(n).reset_index(drop=True)


def main():
    post = thin(pd.read_csv(POST), NTHIN)
    tbar = gis_tbar()
    ## (ell, w) -> native (alpha_s, beta_s), per draw. L11 and later carry only
    ## the reparameterised pair.
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    pa = native_greenland(post.median(numeric_only=True), tbar)
    S = gis_shape_table()
    idx = {y: int(np.where(YEARS == y)[0][0]) for y in list(HORIZONS) + list(HIND)}

    amp = post["gis_amp"].to_numpy()
    drivers = {lab: regional_driver(gmst_rebased(ssp)[1], amp, S) for ssp, lab in SSPS}

    labs = [lab for _, lab in SSPS]
    hs = slice(idx[HIND[0]], idx[HIND[1]] + 1)
    dmax = max(float(np.abs(drivers[a][:, hs] - drivers[b][:, hs]).max())
               for a in labs for b in labs)
    print(f"Ladrillo {TAG}, {len(post)} draws (thinned to match the projection driver)")
    print(f"  histories differ by {dmax:.3f} K over {HIND[0]}-{HIND[1]} "
          f"(t_gis_zones ends 2024, so 2025 is spliced); consequence scored below\n")

    # --- REPRODUCTION GATE --------------------------------------------------
    ship = pd.read_csv(SHIPPED)
    ship = ship[ship.component == "gis"]
    print(f"reproduction gate at (k=1, s=1) vs {os.path.basename(SHIPPED)}, "
          f"tol {GATE_TOL} cm")
    worst, base = 0.0, {}
    for _, lab in SSPS:
        L = np.median(rebase_cm(basin2_series(drivers[lab], post, 1.0, 1.0)), axis=0)
        base[lab] = L
        s = ship[ship.ssp == lab].set_index("year").med
        for y in HORIZONS:
            d = L[idx[y]] - float(s.loc[y])
            worst = max(worst, abs(d))
            print(f"    {lab} {y}: offline {L[idx[y]]:7.2f}  shipped {float(s.loc[y]):7.2f} "
                  f" diff {d:+.2f}")
    if worst >= GATE_TOL:
        raise SystemExit(f"GATE FAILED: worst |offline - shipped| = {worst:.2f} cm "
                         f">= {GATE_TOL}. The offline emulator is not the shipped "
                         f"model; no k is reportable.")
    print(f"  GATE PASSED, worst {worst:.2f} cm\n")

    # --- the ridge ----------------------------------------------------------
    tgt = pd.read_csv(TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    def solve_rate(k, Th):
        """Per-draw bisection: every draw's rate scale is re-solved so THAT DRAW
        still hits its 1900-2025 hindcast increment under history `Th`. Solving
        only at median parameters would let the ensemble drift off the target it
        is pinned to."""
        lo = np.full(len(post), 1e-4)
        hi = np.full(len(post), 1e3)
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            L = basin2_series(Th, post, k, mid)
            below = 100.0 * (L[:, idx[HIND[1]]] - L[:, idx[HIND[0]]]) < want_cm
            lo = np.where(below, mid, lo)
            hi = np.where(below, hi, mid)
        return np.sqrt(lo * hi)

    def med_cm(lab, k, s):
        return np.median(rebase_cm(basin2_series(drivers[lab], post, k, s)), axis=0)

    ## HIND_DRIVER's consequence, measured at both ends of the K grid: re-solve the
    ## rate under each scenario's history and score the spread it induces in the
    ## reported horizons. A 0.043 K difference in one hindcast year is only
    ## harmless if it stays harmless AFTER the bisection amplifies it, and that
    ## amplification grows with k (the rate is smaller, so a fixed hindcast
    ## increment is a larger fraction of the realised loss).
    worst_h = 0.0
    for k in (K_GRID[0], K_GRID[-1]):
        got = {h: {lab: med_cm(lab, k, solve_rate(k, drivers[h]))[idx[2300]]
                   for _, lab in SSPS} for h in labs}
        for _, lab in SSPS:
            v = [got[h][lab] for h in labs]
            worst_h = max(worst_h, max(v) - min(v))
    if worst_h >= HIND_DRIVER_TOL_CM:
        raise SystemExit(f"HIND_DRIVER matters: choosing a different scenario's "
                         f"history moves a 2300 median by {worst_h:.3f} cm "
                         f">= {HIND_DRIVER_TOL_CM}. Pick the history explicitly "
                         f"rather than calling it inert.")
    print(f"  HIND_DRIVER = {HIND_DRIVER}: swapping the history scenario moves "
          f"2300 by at most {worst_h:.3f} cm over k = {K_GRID[0]:g}-{K_GRID[-1]:g}\n")

    print(f"hindcast {HIND[0]}-{HIND[1]} = {want_cm:.2f} cm, restored by per-draw "
          f"bisection at every k (so it never discriminates)")
    print("  2300 literature targets, m SLE:")
    for _, lab in SSPS:
        lo, hi = LIT_2300_M[lab]
        print(f"    {lab:9s} {lo:.3f}-{hi:.3f}   [{LIT_2300_NOTE[lab]}]")
    print(f"  G4 band {GATE_SPREAD_RANGE_CM[0]:.1f}-{GATE_SPREAD_RANGE_CM[1]:.1f} cm "
          f"(ensemble median, applied DIRECTLY -- this scan is per draw), and also "
          f"relative to k={G4_REF_K:g} at {100 * G4_DEGRADE_TOL:.0f}%")
    print(f"  AR6 2100 SSP5-8.5 Greenland: "
          f"{AR6_GIS_2100_SSP585_CM[0]:.0f}-{AR6_GIS_2100_SSP585_CM[1]:.0f} cm\n")

    hdr = (f"  {'k':>6s} {'rate s':>8s} {'tau_sl':>7s} | "
           + " ".join(f"{lab:>9s}" for _, lab in SSPS)
           + f" | {'585@2100':>8s} {'G4':>6s} {'vs k1':>6s}  verdict")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    rows = []
    for k in K_GRID:
        s = solve_rate(k, drivers[HIND_DRIVER])
        rec = dict(tag=TAG, k=k, rate_scale=float(np.median(s)))
        v2300, v2100 = {}, {}
        for _, lab in SSPS:
            L = med_cm(lab, k, s)
            v2300[lab] = L[idx[2300]] / 100.0            # cm -> m SLE
            v2100[lab] = L[idx[2100]]                    # cm
            rec[f"m2300_{lab}"] = v2300[lab]
            rec[f"cm2100_{lab}"] = v2100[lab]
            rec[f"in_band_{lab}"] = bool(LIT_2300_M[lab][0] <= v2300[lab]
                                         <= LIT_2300_M[lab][1])
        rec["g4_2100_cm"] = v2100["SSP5-8.5"] - v2100["SSP1-2.6"]
        rec["g4_in_band"] = bool(GATE_SPREAD_RANGE_CM[0] <= rec["g4_2100_cm"]
                                 <= GATE_SPREAD_RANGE_CM[1])
        rec["ar6_2100_ok"] = bool(AR6_GIS_2100_SSP585_CM[0] <= v2100["SSP5-8.5"]
                                  <= AR6_GIS_2100_SSP585_CM[1])
        rec["ratio_585_over_245"] = v2300["SSP5-8.5"] / v2300["SSP2-4.5"]
        T = pa["gis_alpha_s"] * TAU_REF_K * pa["gis_amp"] + pa["gis_beta_s"]
        rec["tau_slow_yr"] = float(np.median(1.0 / np.maximum(s * T, 1e-12)))
        rows.append(rec)

    g4_ref = [r["g4_2100_cm"] for r in rows if r["k"] == G4_REF_K][0]
    for r in rows:
        r["g4_rel_to_k1"] = r["g4_2100_cm"] / g4_ref
        r["keeps_2100"] = abs(r["g4_rel_to_k1"] - 1.0) <= G4_DEGRADE_TOL
        r["all_pass"] = (all(r[f"in_band_{lab}"] for _, lab in SSPS)
                         and r["keeps_2100"] and r["ar6_2100_ok"])
        cells = " ".join(f"{r[f'm2300_{lab}']:8.3f}"
                         + ("*" if r[f"in_band_{lab}"] else " ") for _, lab in SSPS)
        flags = []
        if not r["ar6_2100_ok"]:
            flags.append("AR6 2100 out")
        if not r["keeps_2100"]:
            flags.append("G4 moved")
        n_in = sum(r[f"in_band_{lab}"] for _, lab in SSPS)
        verdict = "ALL PASS" if r["all_pass"] else f"{n_in}/3 @2300" + (
            (", " + ", ".join(flags)) if flags else "")
        print(f"  {r['k']:6.2f} {r['rate_scale']:8.4f} {r['tau_slow_yr']:7.0f} | "
              + cells + f" | {r['cm2100_SSP5-8.5']:8.2f} {r['g4_2100_cm']:6.2f} "
              f"{r['g4_rel_to_k1']:6.2f}x  {verdict}")

    print(f"\n  (* = inside that scenario's 2300 literature band; tau_sl = slow-channel "
          f"1/rate at {TAU_REF_K} K, yr)")
    ## The k = 1 ROW IS NOT THE SHIPPED MODEL. Every row, k = 1 included, has its
    ## rate re-bisected onto the hindcast target, and the shipped posterior does not
    ## sit exactly on that target -- it is a calibration, not a bisection. The gate
    ## above (s = 1) is the shipped model; the k = 1 row is the shipped model moved
    ## onto the hindcast by a {:.1%} rate change. Reading the row as the deliverable
    ## would mis-state the deliverable by that much.
    print(f"  NOTE: k=1 re-bisects the rate to s = "
          f"{[r['rate_scale'] for r in rows if r['k'] == 1.0][0]:.4f}, so that ROW "
          f"is the shipped "
          f"model moved ONTO the hindcast target, not the shipped model itself "
          f"(that is the gate block above).\n")
    print("=== VERDICT ON THE THREE PRE-FLIGHT QUESTIONS ===\n")
    df = pd.DataFrame(rows)
    kwin = df.loc[df.all_pass, "k"].tolist()

    cool = [lab for _, lab in SSPS if lab != "SSP5-8.5"]
    kcool = df.loc[df[[f"in_band_{lab}" for lab in cool]].all(axis=1), "k"].tolist()
    print(f"  Q1 cool scenarios ({', '.join(cool)} inside their 2300 bands):")
    print(f"     holds at k = {kcool if kcool else 'NO k on the grid'}")
    for lab in cool:
        r2 = df.loc[df.k.isin([2.0, 3.0])]
        over = [f"k={row.k:g} {row[f'm2300_{lab}'] / LIT_2300_M[lab][1]:.2f}x band-top"
                for _, row in r2.iterrows()]
        print(f"       {lab}: " + ", ".join(over))
    print(f"\n  Q2 G4 2100 spread: k=1 reads {g4_ref:.2f} cm against the "
          f"{GATE_SPREAD_RANGE_CM[0]:.1f}-{GATE_SPREAD_RANGE_CM[1]:.1f} band; "
          f"over k = {K_GRID[0]:g}-{K_GRID[-1]:g} it spans "
          f"{df.g4_2100_cm.min():.2f}-{df.g4_2100_cm.max():.2f} cm "
          f"({df.g4_rel_to_k1.min():.3f}-{df.g4_rel_to_k1.max():.3f}x)")
    print(f"     -> raising k {'DOES NOT' if df.keeps_2100.all() else 'DOES'} "
          f"break the 2100 spread on this grid")
    print(f"\n  Q3 AR6 2100 ssp585 in "
          f"{AR6_GIS_2100_SSP585_CM[0]:.0f}-{AR6_GIS_2100_SSP585_CM[1]:.0f} cm: "
          f"holds at k = {df.loc[df.ar6_2100_ok, 'k'].tolist()}")
    print(f"     k={K_GRID[0]:g} reads "
          f"{df.loc[df.k == 1.0, 'cm2100_SSP5-8.5'].iloc[0]:.2f} cm, "
          f"k={K_GRID[-1]:g} reads {df.iloc[-1]['cm2100_SSP5-8.5']:.2f} cm")
    top = df.loc[df["m2300_SSP5-8.5"].idxmax()]
    lo585, hi585 = LIT_2300_M["SSP5-8.5"]
    print(f"\n  THE RIDGE CEILING at {TAG}: ssp585@2300 peaks at "
          f"{top['m2300_SSP5-8.5']:.3f} m (k = {top.k:g}) against a literature band of "
          f"{lo585:.3f}-{hi585:.3f} m")
    print(f"     -> the peak is {lo585 / top['m2300_SSP5-8.5']:.2f}x SHORT of the band "
          f"FLOOR; Leq clips at V0 so more k buys commitment it cannot realise")
    print(f"     ssp585/ssp245 at 2300 spans {df.ratio_585_over_245.min():.2f}x-"
          f"{df.ratio_585_over_245.max():.2f}x over the grid")
    print(f"\n  JOINT: k satisfying all three plus the 2300 ssp585 band = "
          f"{kwin if kwin else 'NONE on this grid'}")

    df.to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
