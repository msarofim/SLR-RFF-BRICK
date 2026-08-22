#!/usr/bin/env python3
"""
scope_gis_ridge_vs_protect.py — score the commitment/rate RIDGE against the
PROTECT matched-forcing TRAJECTORIES, which is the constraint the ridge scan
never had.

WHY THIS, AND NOT "LENGTHEN THE SLOW CHANNEL'S TAU" (2026-08-21e)
  The r2300 arm diagnosed a 7.2x late-rate deficit and the obvious reading is
  "our slow channel relaxes too fast". This repo has already measured why that
  cannot be acted on directly:

  * [[ladrillo_gis_commitment]] (2026-08-14): realised fraction phi = L/Leq at
    2300 is 0.987-0.991 -- A+B is 99% EQUILIBRATED, and its relaxation is FASTER
    than the stock model it replaced. "Raising c1 alone is wrong; LENGTHENING TAU
    ALONE MAKES 2300 LOWER." Slowing the channel moves 2300 the WRONG WAY.
  * The 1900-2025 hindcast constrains only the PRODUCT phi*Leq, so scaling
    (c1, c0) by k and re-solving the rate fits the hindcast IDENTICALLY at every
    k. tau is not identified separately from the commitment; they are one ridge.
  * [[ladrillo_leq_ridge_ceiling]] (2026-08-18): that ridge was scanned against
    2300 LITERATURE BANDS and the ssp585/ssp245 ratio. k = 1 -- the shipped model
    -- was the best point on it, and the ssp585/ssp245 invariant stayed 1.72-3.36x
    against a literature 7.9-31.9x at EVERY k.

  So the honest version of "modify the relaxation time" is: move along the ridge
  (both coordinates together, hindcast held) and score it on something the earlier
  scans did not have. THE PROTECT ARMS ARE EXACTLY THAT -- 200 years of SHAPE
  under a KNOWN forcing, rather than a 2300 endpoint compared to a literature
  band. Moving along the ridge changes phi(t), so unlike the 1900-2025 target this
  one should DISCRIMINATE.

THE TWO FAMILIES DO DIFFERENT JOBS HERE
  r2300 plateaus at 5.58 K and never fires the tap, so it scores the base model
  cleanly. x2300 runs to 13.6 K where Leq's V0 clip is live, so it also probes the
  ceiling that made the earlier ridge non-monotone.

REPRODUCTION GATE, per the standing discipline: at (k = 1, s = 1) this offline
2-basin emulator must reproduce the Julia untapped runs at every reported horizon
to GATE_TOL, on BOTH families, before any k is reported.

  IT RUNS PER-DRAW AND TAKES THE ENSEMBLE MEDIAN, which is what the Julia reports.
  (That was NOT what made the first three attempts fail the gate -- switching from
  median parameters to the ensemble median moved 2300 by under 2 cm. It is kept
  because it is the faithful comparison, not because it was the fix.)

  TWO REAL BUGS THE GATE CAUGHT, both one-signed and both growing with time, which
  is exactly why a growing one-signed residual must not be explained away as
  "medians are not multiplicative":
    1. the channels were initialised at f*eq[0] instead of 0. gis_g -- the fraction
       of the 1850 commitment already realised -- is FIXED AT 0 (LADRILLO_GIS_G).
    2. the basin rate scales are LOG10 in the posterior (10.0^theta); using the
       raw column made the high basin ~7x too slow.
    3. the GMST driver was rebased on 1995-2014. It must be rebased on
       DRIVER_BASE = (1850, 1900); 1995-2014 is the SLR reporting baseline, a
       different window for a different quantity. Rebasing the driver on the wrong
       window rescales amp*S(dT)*gmst_rb and therefore the whole regional driver.

WRITES outputs/scope_gis_ridge_vs_protect.csv
  python3 python/scope_gis_ridge_vs_protect.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scope_gis_leq_ridge_vs_literature import (
    GIS_V0_M, YEARS, gis_shape_table, gis_tbar, native_greenland, regional_driver,
)
## gis_g is the fraction of the 1850 commitment already realised and is FIXED AT 0
## (LADRILLO_GIS_G, ladrillo_projection.jl item 4.1), so BOTH channels start at
## zero, NOT at equilibrium. Imported rather than retyped -- initialising them at
## f*eq[0] instead was the first version of this file and it failed the gate by
## 30 cm at 2300, in the same direction at every horizon.
from scope_gis_2300_relaxation import GIS_G, DRIVER_BASE

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = "L14"
POST = os.path.join(REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{TAG}.csv")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
OUT = os.path.join(REPO, "outputs/scope_gis_ridge_vs_protect.csv")
HIND = (1900, 2025)
HORIZONS = (2100, 2150, 2200, 2300)
K_GRID = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 12.0, 14.0, 22.6, 50.0]
GATE_TOL = 0.5                      # cm; the offline emulator vs the Julia runs
## L14 two-basin FIXED geometry, julia/greenland_3basin_component.jl GIS2_VSHARE.
## south = 3-basin south+mid; high = NO+NE. Asserted against the Julia constant.
K_SOUTH, K_HIGH = 0.6286, 0.3714
FAMILIES = ("r2300", "x2300")
ARM = "spliced"
## 1995-2014 is the SLR REPORTING baseline (not DRIVER_BASE, which rebases GMST).
IB = [int(np.where(YEARS == y)[0][0]) for y in range(1995, 2015)]


def basin2_series(T, P, k_c, s_r, gamma=0.0, gamma_on="both"):
    """L14 two-basin Greenland, VECTORISED OVER DRAWS. T is (ndraw, nyear) -- each
    draw carries its own amp, so the regional driver differs per draw. k_c scales
    the commitment, s_r scales BOTH channel rates (broadcast per draw or scalar).
    Mirrors greenland_3basin_component.jl with k_mid = 0, s_south = 1,
    s_high = gis_s_high.

    `gamma` (2026-08-21j, handoff 2026-08-21e §3) adds the STATE-DEPENDENT
    relaxation rate  r = r0(T) * (1 + gamma * L_b / (k_b * V0))  -- the relaxation
    accelerates as loss proceeds (elevation-SMB feedback + marine-terminus retreat).
    `gamma_on` selects which channel carries it: "both" (the handoff's form),
    "slow", or "fast".

    AT gamma = 0.0 THE FEEDBACK BRANCH IS NOT ENTERED AT ALL, so this is
    bit-identical to the pre-gamma kernel by construction rather than by tolerance
    -- the G3-style nesting gate, and the reason every caller that does not pass
    gamma is unaffected. Asserted in scope_gis_gamma_offline.py."""
    if gamma_on not in ("both", "slow", "fast"):
        raise ValueError(f"gamma_on must be both|slow|fast, got {gamma_on!r}")
    col = lambda c: P[c].to_numpy()[:, None]
    f, c1, c0 = col("gis_f"), col("gis_c1"), col("gis_c0")
    af, bf = col("gis_alpha_f"), col("gis_beta_f")
    a_s, bs = col("gis_alpha_s"), col("gis_beta_s")
    s_r = np.atleast_1d(np.asarray(s_r, float)).reshape(-1, 1)
    out = np.zeros_like(T)
    ## THE BASIN RATE SCALES ARE LOG10 in the posterior, matching the calibrator's
    ## 10.0^theta[GISB_IDX3[b]] (LADRILLO_GIS_BASIN_COLS docstring). Using the raw
    ## column as a linear multiplier was the third bug this gate caught: it made the
    ## high basin 0.23x instead of 1.68x, i.e. ~7x too slow, one-signed and growing.
    ## gis_s_south is the PINNED reference s = 1 and is never sampled.
    for kb, sb in ((K_SOUTH, np.ones((len(P), 1))), (K_HIGH, 10.0 ** col("gis_s_high"))):
        eq = np.clip(kb * k_c * (c1 * T + c0), 0.0, kb * GIS_V0_M)
        rf = np.clip(sb * s_r * (af * T + bf), 1e-9, 1.0)
        rs = np.clip(sb * s_r * (a_s * T + bs), 1e-9, 1.0)
        fast = np.zeros_like(T); slow = np.zeros_like(T)
        fast[:, 0] = GIS_G * f[:, 0] * eq[:, 0]
        slow[:, 0] = GIS_G * (1 - f[:, 0]) * eq[:, 0]
        cap = kb * GIS_V0_M
        for i in range(1, T.shape[1]):
            rfi, rsi = rf[:, i-1], rs[:, i-1]
            if gamma:
                ## The feedback reads the PREVIOUS step's realised loss in THIS
                ## basin, normalised by that basin's own capacity -- so a basin that
                ## has lost little is untouched, which is the whole point. Clipped
                ## at 1.0 like the base rates: a relaxation increment above 1 would
                ## overshoot the target within a single annual step.
                fb = 1.0 + gamma * (fast[:, i-1] + slow[:, i-1]) / cap
                if gamma_on in ("both", "fast"):
                    rfi = np.minimum(rfi * fb, 1.0)
                if gamma_on in ("both", "slow"):
                    rsi = np.minimum(rsi * fb, 1.0)
            fast[:, i] = fast[:, i-1] + (f[:, 0] * eq[:, i-1] - fast[:, i-1]) * rfi
            slow[:, i] = slow[:, i-1] + ((1 - f[:, 0]) * eq[:, i-1] - slow[:, i-1]) * rsi
        out = out + fast + slow
    return out


def rebase_cm(L):
    """m SLE -> cm rel 1995-2014, per draw."""
    return 100.0 * (L - L[:, IB].mean(axis=1, keepdims=True))


def main():
    post = pd.read_csv(POST)
    tbar = gis_tbar()
    ## native_greenland maps the sampled (ell, w) back to (alpha_s, beta_s). It is
    ## written for a Series; applied here to the whole frame, per draw.
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    pa = native_greenland(post.median(numeric_only=True), tbar)
    S = gis_shape_table()
    idx = {y: int(np.where(YEARS == y)[0][0]) for y in list(HORIZONS) + list(HIND)}

    drivers, julia = {}, {}
    for fam in FAMILIES:
        f = pd.read_csv(os.path.join(REPO, f"outputs/protect_{fam}_forcing_gmst.csv")).set_index("year")
        g = f[f"gmst_{ARM}"].reindex(YEARS).to_numpy()
        ## DRIVER_BASE (1850-1900), NOT the 1995-2014 SLR baseline — see docstring bug 2.
        ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
        rb = g - g[ibd].mean()
        drivers[fam] = regional_driver(rb, post["gis_amp"].to_numpy(), S)   # (ndraw, nyear)
        suf = "" if fam == "x2300" else f"_{fam}"
        d = pd.read_csv(os.path.join(REPO,
            f"outputs/diag_protect_forcing_matched_{TAG}{suf}_untapped.csv"))
        julia[fam] = d[(d.component == "gis") & (d.arm == ARM)].set_index("year").med

    # --- REPRODUCTION GATE ------------------------------------------------------
    print(f"reproduction gate at (k=1, s=1) vs the Julia untapped runs, tol {GATE_TOL} cm")
    worst = 0.0
    for fam in FAMILIES:
        L = np.median(rebase_cm(basin2_series(drivers[fam], post, 1.0, 1.0)), axis=0)
        for y in HORIZONS:
            d = abs(L[idx[y]] - julia[fam].loc[y])
            worst = max(worst, d)
            print(f"    {fam} {y}: offline {L[idx[y]]:7.2f}  julia {julia[fam].loc[y]:7.2f}  "
                  f"diff {L[idx[y]] - julia[fam].loc[y]:+.2f}")
    if worst >= GATE_TOL:
        sys.exit(f"GATE FAILED: worst |offline - julia| = {worst:.2f} cm >= {GATE_TOL}. "
                 f"The offline emulator is not the shipped model; no k is reportable.")
    print(f"  GATE PASSED, worst {worst:.2f} cm\n")

    # --- the ridge --------------------------------------------------------------
    tgt = pd.read_csv(TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    Th = drivers["r2300"]          # history is the observed driver in both; choice inert


    def solve_rate(k):
        """Per-draw bisection: every draw's rate is re-solved so that draw still hits
        the 1900-2025 hindcast. Holding it only at median parameters would let the
        ensemble drift off the target it is supposed to be pinned to."""
        lo = np.full(len(post), 1e-4)
        hi = np.full(len(post), 1e3)
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            L = basin2_series(Th, post, k, mid)
            below = 100.0 * (L[:, idx[HIND[1]]] - L[:, idx[HIND[0]]]) < want_cm
            lo = np.where(below, mid, lo)
            hi = np.where(below, hi, mid)
        return np.sqrt(lo * hi)


    ann = pd.read_csv(os.path.join(REPO, "outputs/protect_greenland_gis_annual.csv"))
    OFF = float(pd.read_csv(os.path.join(REPO,
        f"outputs/diag_protect_forcing_matched_{TAG}_untapped.csv")
        ).query("component=='gis' and arm=='ours' and year==2015").med.iloc[0])
    band = {}
    for fam in FAMILIES:
        sub = ann[ann.exp.str.contains(f"ssp585-{fam}")] if fam == "x2300" else \
              ann[ann.exp.str.contains("r2300") & ann.exp.str.contains("ssp585|rcp85")
                  & ~ann.exp.str.startswith("ACCESS1.3")]
        q = sub.groupby("year").gis_cm
        band[fam] = {y: (q.quantile(.05)[y] + OFF, q.median()[y] + OFF, q.quantile(.95)[y] + OFF)
                     for y in HORIZONS}

    print(f"hindcast {HIND[0]}-{HIND[1]} = {want_cm:.2f} cm, restored by bisection at every k "
          f"(so it never discriminates)")
    print(f"{'k':>6} {'rate s':>8} {'tau@5.6K':>9} | " +
          " ".join(f"{fam} {y}" for fam in FAMILIES for y in (2150, 2300)) +
          "   in-band  RMSlog")
    rows = []
    for k in K_GRID:
        s = solve_rate(k)
        rec = dict(k=k, rate_s=float(np.median(s)))
        hits, lsq = 0, []
        for fam in FAMILIES:
            L = np.median(rebase_cm(basin2_series(drivers[fam], post, k, s)), axis=0)
            for y in HORIZONS:
                lo, med, hi = band[fam][y]
                rec[f"{fam}_{y}"] = L[idx[y]]
                rec[f"{fam}_{y}_in"] = bool(lo <= L[idx[y]] <= hi)
                hits += int(lo <= L[idx[y]] <= hi)
                lsq.append(np.log(L[idx[y]] / med) ** 2)
        rec["n_in_band"] = hits
        ## RMS LOG-MISFIT is the metric the k = 2-3 recommendation was reported on
        ## (CHANGELOG 2026-08-21e). It was computed ad hoc and never written to the
        ## CSV, so the headline number could not be regenerated from the committed
        ## code. It is a column now. Log, not level, so that all eight horizons --
        ## which span 8 to 300 cm -- weigh equally; band membership is the coarse
        ## companion test and the two disagree, deliberately (see the printout).
        rec["rms_log_misfit"] = float(np.sqrt(np.mean(lsq)))
        rec["n_horizons"] = len(FAMILIES) * len(HORIZONS)
        T56 = pa["gis_alpha_s"] * 5.6 * pa["gis_amp"] + pa["gis_beta_s"]
        rec["tau_slow_yr"] = float(np.median(1.0 / np.maximum(s * T56, 1e-12)))
        rows.append(rec)
        print(f"{k:6.2f} {rec['rate_s']:8.4f} {rec['tau_slow_yr']:9.0f} | " +
              " ".join(f"{rec[f'{fam}_{y}']:9.1f}" for fam in FAMILIES for y in (2150, 2300)) +
              f"   {hits}/{rec['n_horizons']}   {rec['rms_log_misfit']:.3f}")

    print("\nPROTECT bands (p05-p95, our basis):")
    for fam in FAMILIES:
        print(f"  {fam}: " + "  ".join(
            f"{y} {band[fam][y][0]:.0f}-{band[fam][y][2]:.0f}" for y in HORIZONS))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    best = out.loc[out.n_in_band.idxmax()]
    print(f"\nbest ridge point: k = {best.k:g} ({int(best.n_in_band)}/{int(best.n_horizons)} "
          f"horizons in band), shipped k = 1 scores "
          f"{int(out.loc[out.k == 1.0, 'n_in_band'].iloc[0])}/{int(best.n_horizons)}")
    ## Band membership saturates -- the p05-p95 PROTECT bands are wide enough that
    ## most of the ridge scores 5/8 -- so it is the RMS log-misfit, not the count,
    ## that locates the optimum. Reported explicitly so the two are never confused.
    bl = out.loc[out.rms_log_misfit.idxmin()]
    k1 = float(out.loc[out.k == 1.0, "rms_log_misfit"].iloc[0])
    print(f"best by RMS log-misfit: k = {bl.k:g} ({bl.rms_log_misfit:.3f}), shipped "
          f"k = 1 scores {k1:.3f} -- {k1 / bl.rms_log_misfit:.2f}x worse")
    print(f"wrote {os.path.relpath(OUT, REPO)}")



if __name__ == "__main__":
    main()
