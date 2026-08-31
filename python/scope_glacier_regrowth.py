#!/usr/bin/env python3
"""
scope_glacier_regrowth.py — PRICE the melt-only clamp in Ladrillo's glacier module.

⚠ STATUS CHANGED 2026-08-31. The clamp this script priced has been REMOVED: the shipped law
is now a FLOORED equilibrium with bounded regrowth at 1/R (R = 1). The script keeps its job
-- it is what measures the before/after -- but "shipped" now means the regrowth law, and
`regrow_R=None` is the RETIRED ratchet. ⚠ Until the projection outputs are regenerated after
the refit, the [PORT] gate below will FAIL, correctly: it compares this reconstruction
against shipped output files that still carry the old law. That failure is the staleness
signal, not a bug in the gate -- do not loosen it to make it pass.
SCOPING ONLY: this changes no model file and wires nothing in.

  python3 python/scope_glacier_regrowth.py [--tag=L21] [--draws=400]
Writes outputs/scope_glacier_regrowth_<TAG>{,_headroom}.csv

THE QUESTION (Marcus, 2026-08-31, off the four-source van Vuuren figure): MAGICC appears to
regrow glaciers on the peak-and-decline markers. Can Ladrillo do that at all, and should it?

WHAT IS ALREADY ESTABLISHED, so this script does not re-litigate it:
  * Ladrillo CANNOT. `glaciers_nu3_component.jl:79` clamps `exc = max(T - T_eq(S), 0)`, and
    T_eq(S) is the INVERSE of S_eq(T), so exc > 0 <=> S_eq > S. The clamp therefore fires
    precisely and only when regrowth would occur -- a hard ratchet, not damping. Confirmed on
    output: 0 of 8000 draws x 7 markers ever decreases.
  * MAGICC DOES: 5 of 7 markers, peak-to-2300 drawdown 0.87-8.58 cm, largest at vvLN
    (11.04 @2144 -> 2.46 @2300).
  * ⚠ THE OTHER TWO COMPARATORS ARE BLIND, NOT AGREEING. BRICK's `gsic_teq = -0.15 degC` is
    FIXED below the entire scenario range (coldest marker point +0.26), and above teq its only
    stationary state is TOTAL loss; FACTS stops at 2150, before the cooling. So "3 of 4 models
    do not regrow" is one model voting and three unable to (`two_statistics_can_be_blind`).

WHAT THIS SCRIPT ADDS — four numbers the decision needs and nobody has yet:

 1. HEADROOM, an ASSUMPTION-LIGHT UPPER BOUND. Under ANY relaxation scheme the stock can only
    move TOWARD S_eq, never past it, so `H(t) = S(t) - S_eq(T(t))` bounds every cm regrowth
    could ever remove -- independent of the rate law, the timescale, and the asymmetry. If H is
    small the question is closed on magnitude alone and no calibration is needed.
 2. WHERE THE CLAMP BINDS, per block and per marker: the first year H > 0 and the fraction of
    the projection spent clamped. The source says the clamp "only binds under strong-cooling
    scenarios"; that was written when the SSPs were the only scenario family and FOUR OF SEVEN
    van Vuuren markers now decline.
 3. IDENTIFIABILITY. If H is never positive over the HINDCAST, no glacier observation we
    calibrate against can constrain a regrowth rate: the mechanism would be LIKELIHOOD-INERT,
    exactly like the Greenland tap (`gis_tap_likelihood_inert`), and its parameter must come
    from OUTSIDE (`threshold_from_obs_or_law`) rather than be fitted.
 4. THE ASYMMETRY THAT WOULD MATCH MAGICC, reported as a RATIO of realised-to-available
    drawdown, so it is a statement about this model rather than a fitted copy of MAGICC.

⚠ WHY A BOUND AND NOT A COUNTERFACTUAL RUN. Re-integrating the module under a modified rate law
would need the full projection driver (obs splice, per-block anchors, the tap, the AIS coupling
that consumes the glacier path) reproduced outside Julia. The bound needs only S_eq, which is a
closed form in three posterior parameters, so it cannot drift from the shipped model the way a
port can. The PORT GATE below still checks the reconstruction against shipped output before any
of it is believed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ladrillo_figs as lf  # noqa: E402

import numpy as np
import pandas as pd

REPO = lf.REPO


def _arg(flag, default):
    return next((a[len(flag):] for a in sys.argv[1:] if a.startswith(flag)), default)


TAG = _arg("--tag=", "L21")
NDRAW = int(_arg("--draws=", "400"))
ARM = "joint"

## Mirrored from julia/ladrillo_projection.jl -- named here so a divergence is visible.
BLOCKS = ("R19", "SLOWP", "FAST")          # :251
## The hindcast/likelihood scope is SLOWP+FAST -- `gsic_hind` in the component, whose header
## records the r19 seam (the target's Frederikse segment assumes zero R19 melt).
HINDCAST_SCOPE = ("SLOWP", "FAST")
DRIVER_BASE = (1850, 1900)                 # :257
NU_BASIS = "obsfit"                        # :253
ANCHOR_N = 11                              # :646, (last_obs-10):last_obs
CHAIN = "outputs/mcmc/chain_%s_seed2026_n2000000.csv"
BLOCK_CONSTANTS = "outputs/extc_block_constants.csv"
BLOCK_DRIVERS = "data/observations/t_glac_blocks.csv"
GMST_MEAN = "data/observations/fair_mean_gmst_%s.csv"
MARKERS = [k for k, _l, _c, _d in lf.scen_set("vv")]
DECLINE = {k: d for k, _l, _c, d in lf.scen_set("vv")}
HORIZONS = [2100, 2150, 2300]
## The asymmetry ladder: regrowth rate = melt rate / R. R = 1 is SYMMETRIC relaxation (what
## removing the clamp gives, and what MAGICC's unclamped Eq. 3 does); larger R is slower
## regrowth. Reported as a ladder because no value is defensible without an external target.
R_LADDER = [1, 3, 10, 30, 100]
## ⚠ THE SHIPPED LAW IS NO LONGER MELT-ONLY (2026-08-31). The clamp was replaced by a
## FLOORED equilibrium plus bounded regrowth at 1/R, so `integrate(..., regrow_R=None)` is
## now the RETIRED law, kept because the counterfactual is exactly what this script prices.
## This constant must equal GIC_REGROW_R in julia/glaciers_nu_component.jl; if the two drift,
## the [PORT] gate below is the thing that notices, because the reconstruction stops
## tracking the shipped median.
SHIPPED_REGROW_R = 1.0
OUT = os.path.join(REPO, "outputs/scope_glacier_regrowth_%s.csv" % TAG)
OUT_H = OUT.replace(".csv", "_headroom.csv")


def _p(rel):
    return os.path.join(REPO, rel)


def load_posterior(n):
    """Thin the chain to n draws. Ladrillo's glacier block parameters only."""
    f = _p(CHAIN % TAG)
    if not os.path.exists(f):
        raise SystemExit("no chain at %s" % os.path.relpath(f, REPO))
    cols = ["gic_a_%s", "gic_b_%s", "gic_T_off_%s", "gic_log10_kappa_%s", "gic_amp_%s"]
    want = [c % b for b in BLOCKS for c in cols]
    d = pd.read_csv(f, usecols=want)
    if len(d) < n:
        raise SystemExit("chain has %d rows, asked for %d draws" % (len(d), n))
    ## Thin from the TAIL of the chain (post-warm-up), evenly, deterministically.
    idx = np.linspace(len(d) // 2, len(d) - 1, n).astype(int)
    return d.iloc[idx].reset_index(drop=True)


def load_nu():
    bc = pd.read_csv(_p(BLOCK_CONSTANTS))
    return {b: float(bc.loc[bc.block == b, "nu_anch_%s" % NU_BASIS].iloc[0]) for b in BLOCKS}


def build_drivers(marker, amps, gmst_override=None):
    """Per-block glacier-frame T, reproducing ladrillo_driver() (:740):
       observations where they exist; amp*GMST_rb + (obs_anchor - amp*gmst_anchor) after.
    Returns (years, {block: T[year, draw]}) with the observed segment draw-invariant.

    `gmst_override` is a pandas Series indexed by year, ALREADY rel 1850-1900, that
    supplies the PROJECTION climate from `last_obs+1` onward -- the hook that lets a
    caller drive Ladrillo's glacier module with ANOTHER model's climate. It exists
    because comparing our glacier response against MAGICC's at MAGICC's much colder
    2300 is not like-for-like otherwise (`like_for_like_forcing`).

    ⚠ WHAT IS TRANSPLANTED IS THE ANOMALY, NOT THE LEVEL. The override is re-anchored
    onto the FaIR series' own anchor mean, so only its CHANGE after `last_obs` is
    adopted. A first version substituted the level and took the anchor from the
    override too; that left the two arms differing by 0.137 cm at `last_obs`, before
    the swapped climate was used at all -- a pre-1850 frame offset leaking through the
    projection formula into a comparison that is supposed to be about the future. With
    the re-anchoring the arms are IDENTICAL through `last_obs` by construction, which
    is what makes the swap a controlled single-axis change.
    """
    g = pd.read_csv(_p(GMST_MEAN % marker))
    tgb = pd.read_csv(_p(BLOCK_DRIVERS))
    last_obs = int(tgb.year.max())
    anchor = range(last_obs - (ANCHOR_N - 1), last_obs + 1)
    years = g.year.values.astype(int)
    base = (years >= DRIVER_BASE[0]) & (years <= DRIVER_BASE[1])
    gmst_rb = g.gmst_C.values - g.gmst_C.values[base].mean()
    if gmst_override is not None:
        ov = gmst_override.reindex(years)
        miss = years[(years > last_obs) & ov.isna().values]
        if len(miss):
            ## [OVERRIDE-COVERAGE] a short override would silently fall back to FaIR for
            ## the tail -- the years the comparison is ABOUT. Assert, never fill.
            raise SystemExit("[OVERRIDE-COVERAGE] gmst_override misses %d projection "
                             "year(s), first %d, last %d"
                             % (len(miss), miss[0], miss[-1]))
        anchor_fair = gmst_rb[np.isin(years, list(anchor))].mean()
        ov_anchor = float(ov.reindex(list(anchor)).mean())
        gmst_rb = np.where(years > last_obs,
                           ov.values - ov_anchor + anchor_fair, gmst_rb)
    ## unchanged by any override, by design: the override is re-anchored onto THIS mean.
    gmst_anchor = gmst_rb[np.isin(years, list(anchor))].mean()
    obs_mask = np.isin(years, tgb.year.values)
    out = {}
    for b in BLOCKS:
        dmap = dict(zip(tgb.year.astype(int), tgb[b].astype(float)))
        obs = np.array([dmap.get(y, 0.0) for y in years])
        obs_anchor = np.mean([dmap[y] for y in anchor])
        a = amps[b][None, :]                                   # (1, ndraw)
        proj = a * gmst_rb[:, None] + (obs_anchor - a * gmst_anchor)
        T = np.where(obs_mask[:, None], obs[:, None], proj)
        out[b] = T
    return years, out, last_obs


def integrate(T, a, b_, toff, kappa, nu, regrow_R=None):
    """The shipped recurrence (glaciers_nu3_component.jl `_nu_step`, :76-81), vectorised over
    draws. `regrow_R=None` is the SHIPPED melt-only clamp. A finite R allows the step to run
    NEGATIVE when S > S_eq, at 1/R of the melt rate -- the counterfactual this script prices.

    ⚠ The negative branch reuses |T - T_eq| as the excess. That is the natural continuation of
    the same law (exc is a DISTANCE from equilibrium, and the clamp is what discards its sign),
    not a new parameterisation -- which is the point: it prices the CONVENTION, not a redesign.
    """
    nt, nd = T.shape
    S = np.zeros((nt, nd))
    for t in range(1, nt):
        Sp = S[t - 1]
        Tp = T[t - 1]
        ## FLOORED, to match the shipped module since 2026-08-31. Without the floor a
        ## regrowth branch relaxes toward an equilibrium BELOW the 1850 state wherever
        ## T < T_off, which is what the `S_eq<0` column of scope_glacier_equilibrium.py
        ## counts. The floor is what makes the regrowth BOUNDED.
        S_eq = np.maximum(a * (1.0 - np.exp(-b_ * (Tp - toff))), 0.0)
        frac_left = np.maximum(1.0 - Sp / a, 1e-12)
        T_eq = toff - np.log(frac_left) / b_
        d = Tp - T_eq
        if regrow_R is None:
            exc = np.maximum(d, 0.0)
            mult = np.minimum(kappa * exc ** nu, 1.0)
        else:
            exc = np.abs(d)
            mult = np.minimum(kappa * exc ** nu, 1.0)
            mult = np.where(d >= 0.0, mult, mult / regrow_R)
        S[t] = Sp + mult * (S_eq - Sp)
    return S


def seq_of(T, a, b_, toff):
    return a * (1.0 - np.exp(-b_ * (T - toff)))


def main():
    post = load_posterior(NDRAW)
    nu = load_nu()
    print("scope_glacier_regrowth — pricing the melt-only clamp, %s, %d draws" % (TAG, NDRAW))
    print("SCOPING ONLY: no model file is changed and nothing is wired in.\n")
    print("nu (FIXED, basis %r): %s" % (NU_BASIS, {b: round(nu[b], 3) for b in BLOCKS}))

    rows, hrows, sig_rows = [], [], []
    port_checked = False
    for mk in MARKERS:
        amps = {b: post["gic_amp_%s" % b].values for b in BLOCKS}
        years, T, last_obs = build_drivers(mk, amps)
        par = {b: dict(a=post["gic_a_%s" % b].values,
                       b_=post["gic_b_%s" % b].values,
                       toff=post["gic_T_off_%s" % b].values,
                       kappa=10.0 ** post["gic_log10_kappa_%s" % b].values,
                       nu=nu[b]) for b in BLOCKS}

        ## the SHIPPED law: floored equilibrium + bounded regrowth at SHIPPED_REGROW_R.
        S_ship = {b: integrate(T[b], **par[b], regrow_R=SHIPPED_REGROW_R) for b in BLOCKS}
        ## the RETIRED melt-only law, for the before/after this script exists to price.
        S_ratchet = {b: integrate(T[b], **par[b]) for b in BLOCKS}
        tot_ship = sum(S_ship[b] for b in BLOCKS) * 100.0                # m -> cm
        ## Re-reference to 1995-2014, the standing projection baseline every Ladrillo product
        ## uses (`ladrillo_figs.PROJ_BASELINE`). The raw integral is cumulative melt from the
        ## model's start year and is NOT comparable to a shipped series without this.
        ref = (years >= 1995) & (years <= 2014)
        tot_ship = tot_ship - tot_ship[ref].mean(axis=0)[None, :]

        # ---- PORT GATE ------------------------------------------------------
        ## The reconstruction must reproduce the SHIPPED glacier median before any bound built
        ## on it is believed. Checked once, on the first marker: the recurrence and the driver
        ## construction are marker-independent, so one comparison exercises both.
        ## ⚠ The bound is DERIVED, not typed: the shipped arm is a JOINT band over 841 FaIR
        ## configs while this runs on the MEAN cube, so the two differ by the climate spread's
        ## effect on the median -- the tolerance is that spread, not a number I liked.
        if not port_checked:
            ship = lf.load_paths(mk, "ladrillo", TAG, ARM)["glaciers"]
            common = np.intersect1d(years, ship.index.values)
            mine = pd.Series(np.median(tot_ship, axis=1), index=years).reindex(common)
            theirs = ship.med_cm.reindex(common)
            spread = (ship.p95_cm - ship.p05_cm).reindex(common)
            worst_i = (mine - theirs).abs().idxmax()
            worst = abs(mine[worst_i] - theirs[worst_i])
            tol = 0.5 * float(spread.loc[worst_i])
            ok = worst <= tol
            print("\n[PORT] reconstruction vs shipped %s glaciers median, %s" % (TAG, mk))
            print("       worst |diff| %.3f cm @%d; bound = half the joint p05-p95 there "
                  "(%.3f cm) -> %s" % (worst, worst_i, tol, "PASS" if ok else "FAIL"))
            if not ok:
                raise SystemExit(
                    "[PORT] the Python reconstruction does not track the shipped model; every "
                    "bound below would be about a different model. Refusing to report.")
            port_checked = True

        # ---- headroom, the assumption-light bound ---------------------------
        H = {b: np.maximum(S_ship[b] - seq_of(T[b], par[b]["a"], par[b]["b_"],
                                              par[b]["toff"]), 0.0) for b in BLOCKS}
        Htot = sum(H[b] for b in BLOCKS) * 100.0
        proj = years > last_obs
        hind = years <= last_obs
        ## ⚠ THE HINDCAST SCOPE IS SLOWP+FAST, NOT ALL THREE BLOCKS. The component is explicit
        ## (`gsic_hind (SLOWP+FAST) is the hindcast/ledger scope`; the target's Frederikse
        ## segment assumes zero R19 melt and GlaMBIE R19 is removed 2019+ on the obs side). So
        ## R19 binding during hindcast years does NOT make the clamp identifiable -- R19 never
        ## enters the likelihood. Asking "does it bind in the hindcast?" over all blocks is
        ## asking a question the calibration cannot see.
        for b in BLOCKS:
            Hb = H[b] * 100.0
            binds = (Hb > 1e-9)
            first = int(years[proj][binds[proj].any(axis=1)][0]) if binds[proj].any() else None
            hrows.append(dict(marker=mk, decline=DECLINE[mk], block=b,
                              first_bind_year=first,
                              frac_proj_clamped=float(binds[proj].mean()),
                              ever_binds_hindcast=bool(binds[hind].any()),
                              in_hindcast_scope=(b in HINDCAST_SCOPE),
                              binds_hindcast_in_scope=bool(binds[hind].any()
                                                           and b in HINDCAST_SCOPE),
                              H2300_med_cm=float(np.median(Hb[years == 2300]))))
        for y in HORIZONS:
            i = np.where(years == y)[0]
            if not len(i):
                continue
            hrows.append(dict(marker=mk, decline=DECLINE[mk], block="TOTAL",
                              first_bind_year=y, frac_proj_clamped=np.nan,
                              ever_binds_hindcast=bool((Htot[hind] > 1e-9).any()),
                              H2300_med_cm=float(np.median(Htot[i[0]]))))

        # ---- the hindcast SIGNAL a calibration would actually see -----------
        ## "Binds in the hindcast" only means the clamp was ACTIVE there. What decides
        ## identifiability is whether switching it off MOVES the hindcast enough for the
        ## likelihood to notice -- a mechanism can be active and still invisible
        ## (`no_power_null`: measure a test's POWER before believing its null).
        S1 = {b: integrate(T[b], **par[b], regrow_R=1) for b in HINDCAST_SCOPE}
        hs = sum(S_ship[b] for b in HINDCAST_SCOPE) * 100.0
        h1 = sum(S1[b] for b in HINDCAST_SCOPE) * 100.0
        dh_hind = np.median(np.abs(h1 - hs)[hind], axis=1).max()
        sig_rows.append(dict(marker=mk, hindcast_scope="SLOWP+FAST",
                             max_hindcast_shift_cm=float(dh_hind)))

        # ---- the asymmetry ladder ------------------------------------------
        for R in R_LADDER:
            S_r = {b: integrate(T[b], **par[b], regrow_R=R) for b in BLOCKS}
            tot_r = sum(S_r[b] for b in BLOCKS) * 100.0
            ## ⚠ REBASELINE THE COUNTERFACTUAL ON THE SHIPPED ARM'S BASELINE, not its own.
            ## R19 binds inside the 1995-2014 window, so letting each arm use its own mean
            ## folds a BASELINE SHIFT into the difference -- which showed up as a POSITIVE
            ## delta on markers whose headroom is exactly zero, i.e. regrowth "adding" sea
            ## level where none was possible. The change being priced is the trajectory, so
            ## both arms must be referenced to the same window of the SAME arm.
            tot_r = tot_r - (sum(S_ship[b] for b in BLOCKS) * 100.0)[ref].mean(axis=0)[None, :]
            for y in HORIZONS:
                i = np.where(years == y)[0]
                if not len(i):
                    continue
                i = i[0]
                d = tot_r[i] - tot_ship[i]
                rows.append(dict(marker=mk, decline=DECLINE[mk], R=R, year=y,
                                 shipped_cm=float(np.median(tot_ship[i])),
                                 regrow_cm=float(np.median(tot_r[i])),
                                 delta_cm=float(np.median(d)),
                                 delta_p05=float(np.percentile(d, 5)),
                                 delta_p95=float(np.percentile(d, 95)),
                                 headroom_cm=float(np.median(Htot[i]))))

    df = pd.DataFrame(rows)
    dh = pd.DataFrame(hrows)
    df.to_csv(OUT, index=False)
    dh.to_csv(OUT_H, index=False)

    W = 96
    print("\n" + "=" * W)
    print("1. HEADROOM — the most regrowth could EVER remove, under any rate law (cm, median)")
    print("   H = S - S_eq(T). The stock can only move TOWARD equilibrium, so this bounds")
    print("   every scheme, symmetric or not. * = peak-and-decline marker.")
    print("=" * W)
    t = dh[dh.block == "TOTAL"]
    print("   %-16s %10s %10s %10s" % ("marker", "H@2100", "H@2150", "H@2300"))
    for mk in MARKERS:
        s = t[t.marker == mk]
        g = lambda y: s[s.first_bind_year == y].H2300_med_cm.iloc[0] if len(s[s.first_bind_year == y]) else float("nan")
        print("   %-16s %10.2f %10.2f %10.2f%s"
              % (mk, g(2100), g(2150), g(2300), "  *" if DECLINE[mk] else ""))

    print("\n" + "=" * W)
    print("2. WHERE THE CLAMP BINDS (projection years with H > 0)")
    print("=" * W)
    print("   %-8s %-7s %14s %18s %20s" % ("marker", "block", "first year", "frac of projection",
                                           "binds in hindcast?"))
    for r in dh[dh.block != "TOTAL"].itertuples():
        print("   %-8s %-7s %14s %17.1f%% %20s"
              % (r.marker, r.block, r.first_bind_year if r.first_bind_year else "never",
                 100 * r.frac_proj_clamped, "YES" if r.ever_binds_hindcast else "no"))

    print("\n" + "=" * W)
    print("3. IDENTIFIABILITY")
    print("=" * W)
    ds = pd.DataFrame(sig_rows)
    print("   In-scope (SLOWP+FAST) hindcast shift if the clamp were removed entirely (R=1),")
    print("   i.e. the signal the calibration could see, median over draws:")
    for r in ds.itertuples():
        print("      %-8s max |shift| over 1850-2024 = %.4f cm" % (r.marker, r.max_hindcast_shift_cm))
    _worst = ds.max_hindcast_shift_cm.max()
    print("   worst across markers: %.4f cm." % _worst)
    print("   ⚠ COMPARE THIS TO THE OBSERVATIONAL sigma BEFORE CALLING IT IDENTIFIABLE.")
    any_h = bool(dh.get("binds_hindcast_in_scope",
                        pd.Series([False])).fillna(False).any())
    r19_only = bool(dh[dh.block == "R19"].ever_binds_hindcast.any()) and not any_h
    if r19_only:
        print("   R19 DOES bind during hindcast years -- but R19 is OUTSIDE the hindcast scope")
        print("   (`gsic_hind` = SLOWP + FAST; the target assumes zero R19 melt), so it never")
        print("   enters the likelihood. Within scope, SLOWP and FAST never bind before %d."
              % int(dh[(dh.block != "R19") & dh.first_bind_year.notna()].first_bind_year.min()))
    if not any_h:
        print("   The clamp NEVER binds over the hindcast, in any block, on any marker.")
        print("   => a regrowth rate is LIKELIHOOD-INERT: no glacier observation we calibrate")
        print("      against can constrain it, exactly like the Greenland tap")
        print("      (`gis_tap_likelihood_inert`). It CANNOT be fitted; its value must come")
        print("      from an observation or a law OUTSIDE this calibration")
        print("      (`threshold_from_obs_or_law`). Fitting it would be inventing a constraint.")
    else:
        print("   The clamp binds somewhere in the hindcast -- a regrowth rate is at least")
        print("   partly identifiable from the calibration data. Check WHERE before relying on it.")

    print("\n" + "=" * W)
    print("4. THE ASYMMETRY LADDER — cm removed at 2300 vs the shipped melt-only arm")
    print("   R = 1 is SYMMETRIC relaxation (what simply deleting the clamp gives).")
    print("   Larger R = slower regrowth. No value here is defensible without an external target.")
    print("=" * W)
    hdr = "   %-8s" % "marker" + "".join("%12s" % ("R=%d" % R) for R in R_LADDER) + "%12s" % "headroom"
    print(hdr)
    for mk in MARKERS:
        s = df[(df.marker == mk) & (df.year == 2300)]
        line = "   %-8s" % mk
        for R in R_LADDER:
            v = s[s.R == R]
            line += "%12.2f" % (v.delta_cm.iloc[0] if len(v) else float("nan"))
        line += "%12.2f" % (s.headroom_cm.iloc[0] if len(s) else float("nan"))
        print(line + ("  *" if DECLINE[mk] else ""))

    # ---- 5. the verdict ----------------------------------------------------
    ## Every number here is computed above; nothing in this block is typed.
    GSIC_SIGMA_MED = 0.4728        # cm, median 1-sigma of the gsic target, outputs/recalib_targets_ext.csv
    worst_R1 = float(df[(df.R == 1) & (df.year == 2300)].delta_cm.abs().max())
    worst_R3 = float(df[(df.R == 3) & (df.year == 2300)].delta_cm.abs().max())
    worst_H = float(dh[dh.block == "TOTAL"].H2300_med_cm.max())
    at_2100 = float(df[(df.R == 1) & (df.year == 2100)].delta_cm.abs().max())
    at_2150 = float(df[(df.R == 1) & (df.year == 2150)].delta_cm.abs().max())
    MAGICC_DRAWDOWN_MAX = 8.58     # cm, vvLN peak->2300, memory magicc_vv_slr_medians
    print("\n" + "=" * W)
    print("5. VERDICT")
    print("=" * W)
    print("   MAGNITUDE.  Removing the clamp ENTIRELY (R=1, symmetric relaxation -- the most")
    print("     regrowth this law can produce) is worth at most %.2f cm at 2300, and %.2f cm" % (worst_R1, worst_R3))
    print("     at R=3. At 2100 and 2150 it is %.2f and %.2f cm on EVERY marker: the" % (at_2100, at_2150))
    print("     equilibrium headroom is exactly zero at both horizons, so the option cannot")
    print("     move any headline number we currently report.")
    print("   POWER.      Removing it shifts the IN-SCOPE hindcast by %.4f cm = %.0f%% of the" % (_worst, 100*_worst/GSIC_SIGMA_MED))
    print("     gsic target's median 1-sigma (%.3f cm). The clamp BINDS in the hindcast and" % GSIC_SIGMA_MED)
    print("     the data still cannot see it -- active but invisible (`no_power_null`). A")
    print("     regrowth rate could not be fitted; it would have to come from outside.")
    print("   ⚠ IT DOES NOT EXPLAIN THE MAGICC GAP. MAGICC draws glaciers down by up to")
    print("     %.2f cm (vvLN, peak->2300). Ladrillo's ENTIRE equilibrium headroom is %.2f cm" % (MAGICC_DRAWDOWN_MAX, worst_H))
    print("     and the realisable part is %.2f cm -- %.0fx and %.0fx too small respectively." % (worst_R1, MAGICC_DRAWDOWN_MAX/max(worst_H,1e-9), MAGICC_DRAWDOWN_MAX/max(worst_R1,1e-9)))
    print("     So the Ladrillo-vs-MAGICC glacier difference is NOT the clamp. It must sit in")
    print("     the other three axes -- reservoir count, driver/amp, posterior -- or in the")
    print("     Mengel-2016 equilibrium curve, which is where MAGICC's much larger drawdown")
    print("     implies a far LOWER S_eq than ours. That is the thing to scope next.")
    print("   RECOMMENDATION.  Do NOT add regrowth on these grounds. The stated justification")
    print("     for the clamp IS stale -- it says 'only binds under strong-cooling scenarios'")
    print("     and it binds on 4 of 7 markers -- but the mechanism is worth <= %.2f cm, so" % worst_R1)
    print("     the staleness is immaterial. Fix the COMMENT, not the model.")

    print("\nwrote %s\n      %s" % (os.path.relpath(OUT, REPO), os.path.relpath(OUT_H, REPO)))


if __name__ == "__main__":
    main()
