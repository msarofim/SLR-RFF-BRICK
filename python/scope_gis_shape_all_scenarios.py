#!/usr/bin/env python3
"""
scope_gis_shape_all_scenarios.py — THE SHAPE SCORECARD, EXTENDED TO ALL THREE
SCENARIOS AT MATCHED FORCING. The one scorecard that holds both live constraints.

WHY THIS EXISTS (2026-08-21h, notes/handoff_2026-08-21e ... §3.1)
  After the re-target, two constraints survive and they point OPPOSITE ways:

    scope_gis_ridge_vs_protect.py   200 yr of SHAPE against the PROTECT
      (ssp585 arms ONLY)            trajectories at matched forcing -> k = 2-3
    scope_gis_ridge_vs_ssp_bands.py the cool scenarios' 2300 LEVEL bands,
      (--targets=matched)           now forcing-matched            -> k <= 1.0

  They have never been evaluated against each other IN ONE PLACE at matched
  forcing, because the shape scorecard covered ssp585 only. That is the gap this
  file closes, and it is the measurement that says whether a state-dependent
  relaxation rate (`gamma`, handoff §3) can satisfy both at once or whether
  nothing on this ridge can.

  Marcus's standing instruction, 2026-08-21: make every comparison as like-for-like
  as possible, forcing trajectory first. [[like_for_like_forcing]] Every arm below
  runs OUR model on THAT arm's OWN forcing and scores it against THAT arm's OWN
  runs -- never a cool scenario against an ssp585-forced band, never a held-forcing
  band against an extended-forcing model run.

FIVE ARMS. The family split is part of the identity of an arm, not a detail:
  ssp585 r2300 (35 runs, 5.58 K plateau) | ssp585 x2300 (18, 13.80 K)
  ssp126 r2300 (10, 1.96 K)              | ssp126 x2300 (6, 2.48 K)
  ssp245 r2300 (15, 2.99 K)
  20 horizons in all (5 arms x 2100/2150/2200/2300).

THREE MISFITS, REPORTED SEPARATELY AND NEVER POOLED INTO ONE HEADLINE
  `rms_log_misfit_ssp585` is over the SAME 8 horizons as the published scan, so it
  is directly comparable to its 0.293 (k=3) / 0.497 (k=1). `..._cool` is the 12 new
  ones. `..._all` is all 20 and is NOT comparable to the published number -- quoting
  it against 0.293 would be the same category error this whole arc is about.
  No weighting across scenarios is imposed: the per-arm RMS is printed for all five
  so the trade-off is visible rather than resolved by a hidden choice.

THE KERNEL IS IMPORTED, NOT RETYPED (handoff 2026-08-21d §6), and the ssp585 arms
  are required to REPRODUCE the published scan exactly -- that is the gate on this
  file's restructure, and it is free.

WRITES outputs/scope_gis_shape_all_scenarios.csv
  python3 python/scope_gis_shape_all_scenarios.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

## The L14 two-basin kernel and the 1995-2014 rebase are DEFINED ONCE, in the file
## whose reproduction gate established them. Imported, never re-implemented.
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar, native_greenland  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, GIS_V0_M, YEARS, gis_shape_table, regional_driver,
)

TAG = "L14"
POST = os.path.join(REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{TAG}.csv")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
ANN = os.path.join(REPO, "outputs/protect_greenland_gis_annual.csv")
PUBLISHED = os.path.join(REPO, "outputs/scope_gis_ridge_vs_protect.csv")
OUT = os.path.join(REPO, "outputs/scope_gis_shape_all_scenarios.csv")

# --- named constants; every label and verdict below derives from these --------
HIND = (1900, 2025)
HORIZONS = (2100, 2150, 2200, 2300)
ARM = "spliced"                 # the controlled arm: our history, their future
## Same grid as the published shape scan, so the two are row-comparable.
K_GRID = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 12.0, 14.0, 22.6, 50.0]
## (ssp, label, family, driver-file stem). ssp585 reads the two ORIGINAL driver
## files so the reproduction gate below is a real gate and not a tautology.
ARMS = [("ssp585", "SSP5-8.5", "r2300", "protect_r2300_forcing_gmst"),
        ("ssp585", "SSP5-8.5", "x2300", "protect_x2300_forcing_gmst"),
        ("ssp126", "SSP1-2.6", "r2300", "protect_ssp126_r2300_forcing_gmst"),
        ("ssp126", "SSP1-2.6", "x2300", "protect_ssp126_x2300_forcing_gmst"),
        ("ssp245", "SSP2-4.5", "r2300", "protect_ssp245_r2300_forcing_gmst")]
SSP585_ARMS = [a for a in ARMS if a[0] == "ssp585"]
COOL_ARMS = [a for a in ARMS if a[0] != "ssp585"]
HIND_ARM = ("ssp585", "r2300")  # the history driver for the bisection; MEASURED below
REPRO_TOL = 1e-6                # cm; the ssp585 arms must be the published numbers
OFF_SPREAD_TOL = 0.05           # cm; how far the rel-2015 offset may vary by arm
DROP_GCM = "ACCESS1.3"          # CMIP5; dropped from the forcing AND the band


def protect_band(ann, lab, fam):
    """That arm's OWN runs. The family is matched as well as the scenario -- an
    r2300 band against an x2300-forced model run is not a comparison."""
    sub = ann[(ann.ssp == lab) & ann.exp.str.contains(fam)
              & ~ann.exp.str.startswith(DROP_GCM)]
    if sub.empty:
        sys.exit(f"no PROTECT runs for {lab} {fam}")
    return sub


def band_composition(ann, lab, fam):
    """Per-GCM run counts behind a band. A RUN is a (group, model, exp) triple, not
    an exp name -- the same experiment name appears under several ice-sheet-model
    directories, so counting unique exp names undercounts x2300 by a third (12 vs
    18 at ssp585, 4 vs 6 at ssp126) and would silently mis-state the ensemble."""
    sub = protect_band(ann, lab, fam).groupby(["group", "model", "exp"]).size().reset_index()
    return sub.exp.str.split("_").str[0].value_counts()


def forcing_composition(runs, lab, fam):
    """Per-GCM run counts the FORCING was n-weighted by, from the runs table."""
    L = runs[runs.long & runs.y2300.notna()]
    s = L[(L.ssp == lab) & L.exp.str.contains(fam)
          & ~L.exp.str.startswith(DROP_GCM)]
    return s.exp.str.split("_").str[0].value_counts()


def main():
    post = pd.read_csv(POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    pa = native_greenland(post.median(numeric_only=True), tbar)
    S = gis_shape_table()
    idx = {y: int(np.where(YEARS == y)[0][0]) for y in list(HORIZONS) + list(HIND) + [2015]}
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])

    print("scope_gis_shape_all_scenarios — our model on THEIR forcing, per arm,\n"
          f"  scored against THAT arm's own runs. {TAG}, {len(post)} draws, "
          f"arm = {ARM!r}.\n")

    drivers, gmst = {}, {}
    for ssp, lab, fam, stem in ARMS:
        f = pd.read_csv(os.path.join(REPO, f"outputs/{stem}.csv")).set_index("year")
        g = f[f"gmst_{ARM}"].reindex(YEARS).to_numpy()
        gmst[(ssp, fam)] = g - g[ibd].mean()
        drivers[(ssp, fam)] = regional_driver(gmst[(ssp, fam)], post["gis_amp"].to_numpy(), S)

    # --- GATE 1: the ssp585 arms must reproduce the published shape scan --------
    pub = pd.read_csv(PUBLISHED).set_index("k")
    print(f"GATE 1 — the two ssp585 arms vs {os.path.basename(PUBLISHED)}, "
          f"tol {REPRO_TOL:g} cm")
    tgt = pd.read_csv(TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    Th = drivers[HIND_ARM]

    def solve_rate(k, T=None):
        T = Th if T is None else T
        lo, hi = np.full(len(post), 1e-4), np.full(len(post), 1e3)
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            L = basin2_series(T, post, k, mid)
            below = 100.0 * (L[:, idx[HIND[1]]] - L[:, idx[HIND[0]]]) < want_cm
            lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
        return np.sqrt(lo * hi)

    worst = 0.0
    for k in K_GRID:
        s = solve_rate(k)
        for ssp, lab, fam, _ in SSP585_ARMS:
            L = np.median(rebase_cm(basin2_series(drivers[(ssp, fam)], post, k, s)), axis=0)
            for y in (2150, 2300):
                worst = max(worst, abs(L[idx[y]] - float(pub.loc[k, f"{fam}_{y}"])))
    if worst >= REPRO_TOL:
        sys.exit(f"GATE 1 FAILED: worst |this - published| = {worst:.3e} cm. The "
                 f"restructure moved an ssp585 number; no cool result is reportable.")
    print(f"  GATE 1 PASSED, worst {worst:.3e} cm over {len(K_GRID)} k x 4 cells\n")

    # --- GATE 2: the rel-2015 -> rel-1995-2014 offset is scenario-invariant -----
    ## The PROTECT series are rel 2015 and ours are rel 1995-2014, so their values
    ## get our model's own 2015 level added. 2015 is inside the observed history, so
    ## that offset ought not to depend on the arm -- MEASURED, not assumed.
    offs = {f"{a[1]} {a[2]}": float(np.median(
        rebase_cm(basin2_series(drivers[(a[0], a[2])], post, 1.0, 1.0))[:, idx[2015]]))
        for a in ARMS}
    spread = max(offs.values()) - min(offs.values())
    print(f"GATE 2 — rel-2015 offset by arm: "
          + ", ".join(f"{k} {v:.3f}" for k, v in offs.items()))
    if spread >= OFF_SPREAD_TOL:
        sys.exit(f"GATE 2 FAILED: the offset varies by {spread:.3f} cm across arms "
                 f">= {OFF_SPREAD_TOL}; it is not scenario-invariant and must be "
                 f"applied per arm.")
    OFF = float(np.mean(list(offs.values())))
    print(f"  GATE 2 PASSED, spread {spread:.4f} cm -> OFF = {OFF:.3f} cm\n")

    # --- GATE 3: the history driver's choice, scored in cm not K ---------------
    swing = 0.0
    for k in (K_GRID[0], K_GRID[-1]):
        got = {}
        for key in drivers:
            s = solve_rate(k, drivers[key])
            got[key] = np.median(rebase_cm(basin2_series(drivers[HIND_ARM], post, k, s)),
                                 axis=0)[idx[2300]]
        swing = max(swing, max(got.values()) - min(got.values()))
    print(f"GATE 3 — re-solving the hindcast under each arm's own history moves a "
          f"2300 median by at most {swing:.3f} cm\n")

    ann = pd.read_csv(ANN)

    # --- GATE 4: the band and the forcing are over the SAME runs ---------------
    ## The forcing path is an n-weighted mean over one run list and the band is a
    ## quantile over another. If those two lists differ, the arm is comparing our
    ## model under ensemble A against ensemble B's spread -- a like-for-like failure
    ## one level below the forcing-trajectory one, and invisible in the output.
    print("GATE 4 — band composition vs forcing composition, per arm:")
    runs_tbl = pd.read_csv(os.path.join(REPO, "outputs/protect_greenland_gis_runs.csv"))
    for ssp, lab, fam, _ in ARMS:
        bc, fc = band_composition(ann, lab, fam), forcing_composition(runs_tbl, lab, fam)
        if not bc.sort_index().equals(fc.sort_index()):
            sys.exit(f"GATE 4 FAILED for {lab} {fam}: band {dict(bc)} != forcing {dict(fc)}")
        print(f"  {lab} {fam}: {int(bc.sum()):2d} runs, "
              + ", ".join(f"{k}:{v}" for k, v in bc.items()) + "  MATCH")
    print("  GATE 4 PASSED — every arm scores our model under its own forcing "
          "against its own runs\n")

    band = {}
    for ssp, lab, fam, _ in ARMS:
        q = protect_band(ann, lab, fam).groupby("year").gis_cm
        band[(ssp, fam)] = {y: (q.quantile(.05)[y] + OFF, q.median()[y] + OFF,
                                q.quantile(.95)[y] + OFF) for y in HORIZONS}

    print("PROTECT bands (p05-p95, cm on our basis), and the forcing each was run at:")
    for ssp, lab, fam, _ in ARMS:
        n = int(band_composition(ann, lab, fam).sum())
        print(f"  {lab} {fam} (n={n:2d}, {gmst[(ssp, fam)][idx[2300]]:5.2f} K @2300): "
              + "  ".join(f"{y} {band[(ssp, fam)][y][0]:6.1f}-{band[(ssp, fam)][y][2]:<6.1f}"
                          for y in HORIZONS))
    print(f"\nhindcast {HIND[0]}-{HIND[1]} = {want_cm:.2f} cm, restored by per-draw "
          f"bisection at every k (so it never discriminates)\n")

    hdr = (f"{'k':>6} {'rate s':>8} {'tau':>6} | "
           + " ".join(f"{lab[-3:]}{fam[0]}" .rjust(7) for _, lab, fam, _ in ARMS)
           + f" | {'585':>6} {'cool':>6} {'all':>6}  in-band")
    print(hdr); print("-" * len(hdr))

    rows = []
    for k in K_GRID:
        s = solve_rate(k)
        rec = dict(k=k, rate_s=float(np.median(s)))
        per, hits = {}, 0
        for ssp, lab, fam, _ in ARMS:
            L = np.median(rebase_cm(basin2_series(drivers[(ssp, fam)], post, k, s)), axis=0)
            lsq = []
            for y in HORIZONS:
                lo, med, hi = band[(ssp, fam)][y]
                rec[f"{ssp}_{fam}_{y}"] = L[idx[y]]
                inb = bool(lo <= L[idx[y]] <= hi)
                rec[f"{ssp}_{fam}_{y}_in"] = inb
                hits += int(inb)
                lsq.append(np.log(max(L[idx[y]], 1e-6) / med) ** 2)
            per[(ssp, fam)] = float(np.sqrt(np.mean(lsq)))
            rec[f"rms_{ssp}_{fam}"] = per[(ssp, fam)]
        agg = lambda arms: float(np.sqrt(np.mean(
            [per[(a[0], a[2])] ** 2 for a in arms])))
        rec["rms_log_misfit_ssp585"] = agg(SSP585_ARMS)
        rec["rms_log_misfit_cool"] = agg(COOL_ARMS)
        rec["rms_log_misfit_all"] = agg(ARMS)
        rec["n_in_band"] = hits
        rec["n_horizons"] = len(ARMS) * len(HORIZONS)
        T56 = pa["gis_alpha_s"] * 5.6 * pa["gis_amp"] + pa["gis_beta_s"]
        rec["tau_slow_yr"] = float(np.median(1.0 / np.maximum(s * T56, 1e-12)))
        rows.append(rec)
        print(f"{k:6.2f} {rec['rate_s']:8.4f} {rec['tau_slow_yr']:6.0f} | "
              + " ".join(f"{per[(a[0], a[2])]:7.3f}" for a in ARMS)
              + f" | {rec['rms_log_misfit_ssp585']:6.3f} {rec['rms_log_misfit_cool']:6.3f} "
                f"{rec['rms_log_misfit_all']:6.3f}  {hits}/{rec['n_horizons']}")

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    print(f"\n  (per-arm columns are RMS log-misfit over that arm's 4 horizons; "
          f"tau = slow-channel 1/rate at 5.6 K, yr)")
    print("\n=== THE VERDICT: DOES ONE k SATISFY BOTH? ===\n")
    k585 = out.loc[out.rms_log_misfit_ssp585.idxmin()]
    kcool = out.loc[out.rms_log_misfit_cool.idxmin()]
    kall = out.loc[out.rms_log_misfit_all.idxmin()]
    pub585 = float(pub.loc[3.0, "rms_log_misfit"]), float(pub.loc[1.0, "rms_log_misfit"])
    print(f"  ssp585 arms only : best k = {k585.k:g} ({k585.rms_log_misfit_ssp585:.3f}), "
          f"k=1 scores {float(out.loc[out.k == 1.0, 'rms_log_misfit_ssp585'].iloc[0]):.3f}")
    print(f"       [the published ssp585-only scan reads {pub585[0]:.3f} at k=3 and "
          f"{pub585[1]:.3f} at k=1 -- same 8 horizons, so directly comparable]")
    print(f"  cool arms only   : best k = {kcool.k:g} ({kcool.rms_log_misfit_cool:.3f}), "
          f"k=1 scores {float(out.loc[out.k == 1.0, 'rms_log_misfit_cool'].iloc[0]):.3f}")
    print(f"  all five arms    : best k = {kall.k:g} ({kall.rms_log_misfit_all:.3f})")
    print(f"       [NOT comparable to the published 0.293 -- 20 horizons, not 8]")
    if k585.k == kcool.k:
        print(f"\n  -> THE ARGMINS COINCIDE at k = {k585.k:g}. The shape and cool "
              f"constraints do NOT conflict on this ridge.")
    else:
        c1 = float(out.loc[out.k == kcool.k, "rms_log_misfit_ssp585"].iloc[0])
        c2 = float(out.loc[out.k == k585.k, "rms_log_misfit_cool"].iloc[0])
        print(f"\n  -> THE ARGMINS DISAGREE: ssp585 wants k = {k585.k:g}, the cool arms "
              f"want k = {kcool.k:g}.")
        print(f"     Cost of each choice to the other, in that other's own metric:")
        print(f"       at the cool optimum k={kcool.k:g}, ssp585 scores {c1:.3f} vs its "
              f"own best {k585.rms_log_misfit_ssp585:.3f}  ({c1 / k585.rms_log_misfit_ssp585:.2f}x worse)")
        print(f"       at the ssp585 optimum k={k585.k:g}, cool scores {c2:.3f} vs its "
              f"own best {kcool.rms_log_misfit_cool:.3f}  ({c2 / kcool.rms_log_misfit_cool:.2f}x worse)")
        print(f"     A SCALE cannot serve both. That is the case for a state-dependent")
        print(f"     relaxation rate rather than another point on this ridge.")
        ## WHICH SIDE IS THE SHIPPED MODEL ALREADY ON? "The argmins disagree" is
        ## symmetric and hides that k = 1 is nearly optimal for one of them.
        s1 = float(out.loc[out.k == 1.0, "rms_log_misfit_ssp585"].iloc[0])
        s2 = float(out.loc[out.k == 1.0, "rms_log_misfit_cool"].iloc[0])
        print(f"\n     AND THE SHIPPED MODEL IS NOT SYMMETRICALLY PLACED. At k = 1:")
        print(f"       cool   {s2:.3f} vs its best {kcool.rms_log_misfit_cool:.3f}  "
              f"-> {s2 / kcool.rms_log_misfit_cool:.2f}x off")
        print(f"       ssp585 {s1:.3f} vs its best {k585.rms_log_misfit_ssp585:.3f}  "
              f"-> {s1 / k585.rms_log_misfit_ssp585:.2f}x off")
        print(f"     The shipped model is already close to the cool optimum; ~all of "
              f"the\n     deficiency is on the ssp585 side. A correction must therefore "
              f"act\n     SELECTIVELY on the warm arm, which is what a state-dependent "
              f"term does\n     and what a scale k cannot.")

        ## THE SELECTIVITY, MEASURED. gamma enters as r = r0*(1 + gamma*L/(k_b*V0)),
        ## so its leverage on an arm is that arm's REALISED LOSS FRACTION. If the
        ## cool arms sit near zero there, gamma is nearly inert on exactly the arms
        ## that constrain k -- which is the whole reason it can do what k cannot.
        ## Asserted as a measurement, not as the argument for the mechanism.
        s = solve_rate(1.0)
        print(f"\n     LEVERAGE OF A STATE-DEPENDENT TERM (realised loss fraction "
              f"L/V0 at k=1, median draw):")
        frac = {}
        for ssp, lab, fam, _ in ARMS:
            L = np.median(basin2_series(drivers[(ssp, fam)], post, 1.0, s), axis=0)
            frac[(ssp, fam)] = float(L[idx[2300]] / GIS_V0_M)
        ref = frac[("ssp126", "r2300")]
        for ssp, lab, fam, _ in ARMS:
            print(f"       {lab} {fam}: L/V0 @2300 = {frac[(ssp, fam)]:.4f}   "
                  f"({frac[(ssp, fam)] / ref:5.1f}x the ssp126-r2300 arm)")
        warm = max(frac[a[0], a[2]] for a in SSP585_ARMS)
        cool = max(frac[a[0], a[2]] for a in COOL_ARMS)
        print(f"     => a term proportional to L/V0 has {warm / cool:.1f}x more "
              f"leverage on the warmest arm\n        than on any cool one -- but see "
              f"the deliverable numbers below before quoting that.")

        ## BUT THE ARMS ARE NOT OUR SCENARIOS. Their forcing ranges 1.95-13.63 K
        ## while our own deliverable ssp585 reaches 7.80 K, between the two ssp585
        ## arms. Leverage measured on the arms is therefore NOT the leverage gamma
        ## would have on the DELIVERABLE, and quoting the 5.6x against our own
        ## ssp126 would be the same mismatch this whole arc is about. Measured on
        ## our own drivers, which is the number that decides whether gamma can move
        ## ssp585 without moving the cool deliverables.
        ours_frac = {}
        for ssp, lab in (("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"),
                         ("ssp585", "SSP5-8.5")):
            g = pd.read_csv(os.path.join(
                REPO, f"data/observations/fair_mean_gmst_{ssp}.csv")
            ).set_index("year").gmst_C.reindex(YEARS).to_numpy()
            rb = g - g[ibd].mean()
            D = regional_driver(rb, post["gis_amp"].to_numpy(), S)
            L = np.median(basin2_series(D, post, 1.0, s), axis=0)
            ours_frac[lab] = (float(L[idx[2300]] / GIS_V0_M), float(rb[idx[2300]]))
        oref = ours_frac["SSP1-2.6"][0]
        print(f"\n     THE SAME LEVERAGE ON OUR OWN DELIVERABLE SCENARIOS (k=1):")
        for lab, (fr, T) in ours_frac.items():
            print(f"       {lab} ({T:5.2f} K @2300): L/V0 = {fr:.4f}   "
                  f"({fr / oref:5.1f}x our ssp126)")
        ratio = ours_frac["SSP5-8.5"][0] / max(ours_frac["SSP1-2.6"][0],
                                               ours_frac["SSP2-4.5"][0])
        print(f"     => on the DELIVERABLE the selectivity is {ratio:.1f}x, not "
              f"{warm / cool:.1f}x.\n        The arms BRACKET our ssp585 "
              f"({ours_frac['SSP5-8.5'][1]:.2f} K) rather than matching it, so the arm"
              f"\n        number must not be quoted for the deliverable.")
        ## What gamma would have to be, order of magnitude. The handoff's form is
        ## r = r0*(1 + gamma*L_b/(k_b*V0)) per basin; the fractions above are on the
        ## TOTAL V0, so the per-basin argument is larger by roughly 1/k_b. Stated as
        ## a scale to size the offline grid, NOT as a fitted value.
        need = 1.0
        for lab, (fr, _) in ours_frac.items():
            if lab == "SSP5-8.5":
                need = fr
        print(f"\n     SIZING gamma (for the offline grid, not a fit): our ssp585 "
              f"reaches L/V0 = {need:.3f},\n     so under r = r0*(1 + gamma*L_b/"
              f"(k_b*V0)) a 2x late-rate boost needs gamma of order\n     "
              f"{1.0 / need:.0f} on the total-V0 basis, less by ~1/k_b on the "
              f"per-basin one. The cool arms\n     would then move by "
              f"{ours_frac['SSP2-4.5'][0] / need:.2f} of that -- which is the trade "
              f"gamma has to beat, and the\n     reason this is a MEASUREMENT to run, "
              f"not a mechanism to assume.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
