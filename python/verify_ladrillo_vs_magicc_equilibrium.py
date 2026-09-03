#!/usr/bin/env python3
"""verify_ladrillo_vs_magicc_equilibrium.py -- direct check of the deliverable claim
"Ladrillo's equilibrium regrowth is similar to MAGICC's, but its rate of regrowth is
slower" (LadrilloUpdateDescription_FILLED.md, MAGICC-climate section).

Reuses scope_glacier_regrowth.py's build_drivers()/seq_of() machinery UNCHANGED so this is
Ladrillo's actual calibrated equilibrium law, not a reimplementation, driven by
gmst_override=MAGICC's own GMST (data/comparison/magicc_gmst_vv.csv) -- both models'
equilibrium curves are then read off the SAME temperature trajectory, so any difference is
the CURVE, not a climate mismatch (like_for_like_forcing).

MAGICC's own equilibrium curve comes from its actual 600-member drawnset
(slr_gl_equitemp / slr_gl_equislr), the same source scope_magicc_glacier_drawnset.py reads --
real tabulated data, not an approximation of MAGICC's law.

Both curves re-referenced to 1995-2014 (the standing PROJ_BASELINE), matching how every other
Ladrillo committed-melt number in this repo is reported.

  python3 python/verify_ladrillo_vs_magicc_equilibrium.py [--tag=L24]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from scope_glacier_regrowth import (BLOCKS, build_drivers, load_nu, load_posterior,
                                     seq_of, REPO, NDRAW)
import ladrillo_figs as lf

TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L24")
MAGICC_GMST_CSV = os.path.join(REPO, "data/comparison/magicc_gmst_vv.csv")
DRAWNSET = os.path.expanduser(
    "~/Documents/2026/CodeProjects/MAGICC/slr-refresh/data/processed/magicc-drawnsets/"
    "magicc-ar6-0fd0f62-f023edb-drawnset_with_slr.json")
REF = (1995, 2014)   # lf.PROJ_BASELINE = "cm, rel. 1995-2014" -- the standing projection window
MARKERS = ["vvVL", "vvLN", "vvL", "vvML", "vvHL"]   # the five DECLINING markers, per the claim
YEAR = 2300


def magicc_own_seq_curve():
    """MAGICC's 600-member S_eq(T) drawnset -> (T_grid (K), curves (n_member, n_T) in mm)."""
    cs = json.load(open(DRAWNSET))
    T = np.array(cs[0]["slr_gl_equitemp"], dtype=float)
    assert all(c["slr_gl_equitemp"] == cs[0]["slr_gl_equitemp"] for c in cs), "shared-axis gate"
    curves = np.array([c["slr_gl_equislr"] for c in cs], dtype=float)   # (600, nT), mm
    return T, curves


def magicc_seq_at(T_grid, curves_mm, t_query):
    """Interpolate every member's curve at t_query (scalar K); returns (array (n_member,) cm,
    in_domain bool). MAGICC's own grid starts at 0.0 K (equilibrium undefined below
    pre-industrial per scope_magicc_glacier_drawnset.py) -- np.interp CLAMPS silently past
    either end, which would silently report MAGICC's DOMAIN FLOOR as if it were its true
    equilibrium at a colder queried T. Flag it instead of hiding it (Marcus, 2026-09-03:
    caught this reading the vvLN/vvML ratios -- MAGICC hitting its own regrowth limit there,
    not out-regrowing Ladrillo)."""
    in_domain = T_grid[0] <= t_query <= T_grid[-1]
    out = np.array([np.interp(t_query, T_grid, curves_mm[i]) for i in range(curves_mm.shape[0])])
    return out / 10.0, in_domain   # mm -> cm


def rereference(years, series_2d, ref_lo, ref_hi):
    """series_2d: (n_year, n_draw). Subtract each draw's own ref-window mean."""
    m = (years >= ref_lo) & (years <= ref_hi)
    return series_2d - series_2d[m].mean(axis=0, keepdims=True)


def main():
    post = load_posterior(NDRAW)
    nu = load_nu()
    amps = {b: post["gic_amp_%s" % b].values for b in BLOCKS}
    par = {b: dict(a=post["gic_a_%s" % b].values, b_=post["gic_b_%s" % b].values,
                   toff=post["gic_T_off_%s" % b].values) for b in BLOCKS}

    gmst_magicc = pd.read_csv(MAGICC_GMST_CSV)
    T_grid, curves_mm = magicc_own_seq_curve()
    print("MAGICC drawnset: %d members, T grid %.1f to %.1f K" % (curves_mm.shape[0], T_grid[0], T_grid[-1]))
    print("Ladrillo TAG=%s, %d posterior draws\n" % (TAG, NDRAW))

    print("%-8s %8s %10s %10s %10s %10s %10s %8s" % (
        "marker", "T@2300", "Lad_own", "Lad_own", "Lad@MAGICC", "Lad@MAGICC", "MAGICC_own", "ratio"))
    print("%-8s %8s %10s %10s %10s %10s %10s %8s" % (
        "", "(MAGICC)", "climate", "S_eq", "climate", "S_eq", "S_eq", "Lad/MAG"))

    rows = []
    for mk in MARKERS:
        gser = gmst_magicc[gmst_magicc.scenario == mk].set_index("year")["med"]
        ## Ladrillo's own driver runs one year past MAGICC's extract (2301 vs 2300) -- a
        ## padding artifact of FaIR's pipeline, not a real difference. Hold 2300 forward;
        ## only year==2300 is ever read below.
        if 2301 not in gser.index:
            gser.loc[2301] = gser.loc[2300]

        # ---- Ladrillo on ITS OWN climate (reproduces the "19.1 -> 2.2" style number) ----
        years, T_own, last_obs = build_drivers(mk, amps)
        seq_own_cm = np.zeros((len(years), NDRAW))
        for b in BLOCKS:
            seq_own_cm += np.maximum(seq_of(T_own[b], par[b]["a"], par[b]["b_"], par[b]["toff"]), 0.0) * 100.0
        seq_own_cm = rereference(years, seq_own_cm, *REF)
        iy = int(np.flatnonzero(years == YEAR)[0])
        lad_own_seq = seq_own_cm[iy]

        # ---- Ladrillo driven by MAGICC's own GMST (like_for_like_forcing) ----
        years2, T_mag, _ = build_drivers(mk, amps, gmst_override=gser)
        seq_magclim_cm = np.zeros((len(years2), NDRAW))
        for b in BLOCKS:
            seq_magclim_cm += np.maximum(seq_of(T_mag[b], par[b]["a"], par[b]["b_"], par[b]["toff"]), 0.0) * 100.0
        seq_magclim_cm = rereference(years2, seq_magclim_cm, *REF)
        iy2 = int(np.flatnonzero(years2 == YEAR)[0])
        lad_mag_seq = seq_magclim_cm[iy2]

        # ---- MAGICC's OWN equilibrium curve, evaluated at ITS OWN T(2300) ----
        t2300 = float(gser.loc[YEAR])
        t_ref = float(gser.loc[REF[0]:REF[1]].mean())
        magicc_seq_2300, dom2300 = magicc_seq_at(T_grid, curves_mm, t2300)
        magicc_seq_ref, domref = magicc_seq_at(T_grid, curves_mm, t_ref)
        magicc_seq_rereffed = magicc_seq_2300 - magicc_seq_ref.mean()
        flag = "" if dom2300 else "  *** T@2300 BELOW MAGICC's domain floor (0K) -- clamped, not a true eq ***"

        ratio = np.median(lad_mag_seq) / np.median(magicc_seq_rereffed)
        print("%-8s %8.2f %10.2f %10.2f %10.2f %10.2f %10.2f %8.2f%s" % (
            mk, t2300, np.median(lad_own_seq), np.median(lad_own_seq),
            np.median(lad_mag_seq), np.median(lad_mag_seq),
            np.median(magicc_seq_rereffed), ratio, flag))
        rows.append(dict(marker=mk, magicc_T2300=t2300, magicc_T2300_in_domain=dom2300,
                         ladrillo_own_climate_seq2300_med=float(np.median(lad_own_seq)),
                         ladrillo_own_climate_seq2300_p05=float(np.percentile(lad_own_seq, 5)),
                         ladrillo_own_climate_seq2300_p95=float(np.percentile(lad_own_seq, 95)),
                         ladrillo_on_magicc_climate_seq2300_med=float(np.median(lad_mag_seq)),
                         ladrillo_on_magicc_climate_seq2300_p05=float(np.percentile(lad_mag_seq, 5)),
                         ladrillo_on_magicc_climate_seq2300_p95=float(np.percentile(lad_mag_seq, 95)),
                         magicc_own_seq2300_med=float(np.median(magicc_seq_rereffed)),
                         magicc_own_seq2300_p05=float(np.percentile(magicc_seq_rereffed, 5)),
                         magicc_own_seq2300_p95=float(np.percentile(magicc_seq_rereffed, 95)),
                         ratio_ladrillo_over_magicc=float(ratio)))

    out = pd.DataFrame(rows)
    outp = os.path.join(REPO, "outputs/verify_ladrillo_vs_magicc_equilibrium_%s.csv" % TAG)
    out.to_csv(outp, index=False)
    print("\nAll cm, rel. 1995-2014 (Ladrillo's own PROJ_BASELINE). 'Lad@MAGICC S_eq' and")
    print("'MAGICC_own S_eq' are evaluated at the SAME temperature (MAGICC's own T(2300)),")
    print("so the ratio column isolates the CURVE difference, not a climate difference.")
    print("wrote", os.path.relpath(outp, REPO))


if __name__ == "__main__":
    main()
