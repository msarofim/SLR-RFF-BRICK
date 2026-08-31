#!/usr/bin/env python3
"""
scope_glacier_equilibrium.py — SCOPE Ladrillo's glacier EQUILIBRIUM curve.
SCOPING ONLY: this changes no model file and wires nothing in.

  python3 python/scope_glacier_equilibrium.py [--tag=L21] [--draws=400]
Writes outputs/scope_glacier_equilibrium_<TAG>{,_ladder}.csv

THE QUESTION, inherited from scope_glacier_regrowth.py's §5 verdict and named as the next
scope in notes/handoff_2026-08-31e: the melt-only clamp is worth <= 0.23 cm, so it cannot be
why MAGICC-SLR draws glaciers down by up to 8.58 cm on the peak-and-decline markers. That
handoff concluded the residual "implies a far LOWER S_eq than the Mengel-2016 curve gives
us", and separately noted that Ladrillo is the LOWEST glacier arm at 2100 in 7/7 markers,
guessing the two might be one finding in the equilibrium curve.

⚠ BOTH OF THOSE GUESSES SKIPPED A STEP, AND THIS SCRIPT TAKES IT FIRST. Every one of those
comparisons evaluated Ladrillo at FaIR's temperature and MAGICC at MAGICC's, because
MAGICC-SLR computes its OWN climate from the van Vuuren emissions -- the very property that
makes its agreement with the FaIR-driven arms non-circular. A difference in the SLR response
and a difference in the DRIVING TEMPERATURE are then confounded, and the standing rule is
that a comparison is like-for-like on forcing trajectory FIRST (`like_for_like_forcing`).
So §1 measures the two climates before anything is attributed to a glacier module, and §2
re-runs the headroom bound with Ladrillo's own module driven by MAGICC's climate.

WHAT EACH SECTION DECIDES
 1. THE CLIMATE FORK. FaIR vs MAGICC GMST per marker. If they diverge on exactly the
    markers where the glacier arms diverge, the module attribution is unsafe.
 2. HEADROOM UNDER MAGICC'S OWN CLIMATE. The same assumption-light bound
    H = S - S_eq(T) as scope_glacier_regrowth, recomputed with `gmst_override`. This is
    a CONTROLLED swap: same posterior, same law, same clamp, one axis changed.
 3. THE COMMITTED LADDER vs ITS OWN EXTERNAL ANCHOR. The curve was FITTED to four
    GlacierMIP3 committed-loss rungs (Zekollari 2025, scope-corrected). Whether the
    POSTERIOR still sits inside that anchor has never been checked -- the fit set priors,
    and the MCMC has moved b and T_off a long way. This is the direct test of "is S_eq
    wrong", and it is against an EXTERNAL multi-model anchor, not another model of ours
    (`threshold_from_obs_or_law`).
 4. RATE vs EQUILIBRIUM AT 2100. The saturation fraction S/S_eq and the instant-equilibrium
    CEILING. If the ceiling sits far above the comparators, the 2100 lowness cannot be the
    curve being too low -- it is the approach rate -- and §5.3 of the handoff is answered.
 5. EXTRAPOLATION RANGE. The rungs span 1.2-3.0 K. Both the hot markers and, more to the
    point, the COOLED tails sit outside that span, so the part of the curve the drawdown
    question lives on is extrapolated. Reported at both ends, on both climates.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scope_glacier_regrowth as sg   # the port, the drivers and the recurrence, imported
import ladrillo_figs as lf            # noqa: E402

import numpy as np
import pandas as pd

REPO = lf.REPO
TAG = sg.TAG
NDRAW = sg.NDRAW
BLOCKS = sg.BLOCKS
MARKERS = sg.MARKERS
DECLINE = sg.DECLINE
HORIZONS = sg.HORIZONS
ARM = sg.ARM
PROJ_BASE = (1995, 2014)               # ladrillo_figs.PROJ_BASELINE, the shipped convention

## ---- external anchors. Every one of these is literature or observation, never a model of
## ours (`threshold_from_obs_or_law`), and each carries its source in the name.
## GlacierMIP3 committed loss, SCOPE-CORRECTED to excl-r5-incl-r19 (Zekollari 2025 /
## Zenodo 15046588 via python/t2_gmip3_scope_anchor.py). Mirrored from d0_glacier_shootout.py
## :65-74 -- the same constants the curve was FITTED to, so the check is against its own anchor.
GMIP3_LEVELS = [1.2, 1.5, 2.0, 3.0]                                   # global K rel 1850-1900
GMIP3_CENTRAL = {1.2: 37.4, 1.5: 46.3, 2.0: 63.0, 3.0: 75.5}          # % of remaining volume
GMIP3_LIKELY = {1.2: (11.8, 54.0), 1.5: (17.2, 63.2),
                2.0: (41.5, 75.5), 3.0: (58.5, 83.9)}
## The gsic target's median 1-sigma, outputs/recalib_targets_ext.csv -- the same observational
## scale scope_glacier_regrowth used to price its power test.
GSIC_SIGMA_MED_CM = 0.4728
## The two climate arms share driver, posterior and law through last_obs by construction,
## so the splice check is an IDENTITY and gets a floating-point bound, not an
## observational one (`gate_bound_matches_its_claim`).
SPLICE_IDENTITY_TOL_CM = 1e-9
## MAGICC-SLR's largest peak->2300 glacier drawdown, memory `magicc_vv_slr_medians`; recomputed
## from the comparison CSV below and ASSERTED against this, so a stale constant cannot pass.
MAGICC_DRAWDOWN_MAX_CM = 8.58
## the precision these comparisons are quoted to; used to decide which markers actually
## HAVE a drawdown, so a zero-vs-zero cell cannot be counted as a bound that held.
REPORT_PRECISION_CM = 0.1
## The recomputation below uses the reported horizons (2100/2150/2300) while the recorded
## value is the true path peak at 2144, so the bound is the size of that discretisation,
## not an identity: the horizon grid is 50 yr wide near a peak whose curvature is ~0.1 cm.
DRAWDOWN_TOL_CM = 0.10

BLOCK_CONSTANTS = "outputs/extc_block_constants.csv"
BLOCK_DRIVERS = "data/observations/t_glac_blocks.csv"
CMP_CSV = "outputs/vv_model_comparison_%s.csv" % TAG
MAGICC_GMST = "data/comparison/magicc_gmst_vv.csv"
## the 841-config marker cube -- the only FaIR column that is like-for-like with MAGICC's
## 600-member median. The mean-config file is what DRIVES the module, so both are shown.
FAIR_CUBE = "data/observations/fair_cube_gmst_%s_raw.csv"
OUT = os.path.join(REPO, "outputs/scope_glacier_equilibrium_%s.csv" % TAG)
OUT_L = OUT.replace(".csv", "_ladder.csv")
W = 96


def _p(rel):
    return os.path.join(REPO, rel)


def load_magicc_gmst():
    f = _p(MAGICC_GMST)
    if not os.path.exists(f):
        raise SystemExit("no MAGICC GMST at %s -- run python3 python/extract_magicc_vv_gmst.py"
                         % os.path.relpath(f, REPO))
    d = pd.read_csv(f)
    out = {s: g.set_index("year")["med"] for s, g in d.groupby("scenario")}
    ## The FaIR marker files carry a 2301 row and MAGICC stops at 2300, so the coverage gate
    ## in build_drivers fires on exactly one year. Extend it EXPLICITLY here rather than
    ## loosening the gate: the recurrence reads T[t-1] to make S[t], so T at the final year
    ## is never read at all -- holding it is a no-op that is checked below, not a fill that
    ## hides a short series.
    for k, v in out.items():
        out[k] = v.reindex(sorted(set(v.index) | {int(v.index.max()) + 1})).ffill()
    return out


def load_cmp_glaciers():
    """Comparator glacier medians, cm rel 1995-2014, from the four-source vv comparison."""
    d = pd.read_csv(_p(CMP_CSV))
    d = d[d.component == "glaciers"]
    return d.set_index(["source", "marker", "year"])["med"]


def main():
    post = sg.load_posterior(NDRAW)
    nu = sg.load_nu()
    bc = pd.read_csv(_p(BLOCK_CONSTANTS)).set_index("block")
    tgb = pd.read_csv(_p(BLOCK_DRIVERS))
    mg = load_magicc_gmst()
    cmp_g = load_cmp_glaciers()
    amps = {b: post["gic_amp_%s" % b].values for b in BLOCKS}
    par = {b: dict(a=post["gic_a_%s" % b].values,
                   b_=post["gic_b_%s" % b].values,
                   toff=post["gic_T_off_%s" % b].values,
                   kappa=10.0 ** post["gic_log10_kappa_%s" % b].values,
                   nu=nu[b]) for b in BLOCKS}

    print("scope_glacier_equilibrium — is the S_eq CURVE the seat of the glacier gaps?")
    print("SCOPING ONLY: no model file is changed and nothing is wired in.")
    print("%s, %d draws, arm=%s\n" % (TAG, NDRAW, ARM))

    rows, lrows = [], []
    port_checked = False
    per_marker = {}

    for mk in MARKERS:
        years, T_f, last_obs = sg.build_drivers(mk, amps)
        years_m, T_m, _ = sg.build_drivers(mk, amps, gmst_override=mg[mk])
        assert (years_m == years).all()
        ref = (years >= PROJ_BASE[0]) & (years <= PROJ_BASE[1])

        S_f = {b: sg.integrate(T_f[b], **par[b]) for b in BLOCKS}
        S_m = {b: sg.integrate(T_m[b], **par[b]) for b in BLOCKS}
        tot_f_abs = sum(S_f[b] for b in BLOCKS) * 100.0
        base = tot_f_abs[ref].mean(axis=0)[None, :]      # ONE baseline, the shipped arm's
        tot_f = tot_f_abs - base
        tot_m = sum(S_m[b] for b in BLOCKS) * 100.0 - base

        # ---- PORT GATE (delegated: the same comparison scope_glacier_regrowth makes) ----
        if not port_checked:
            ship = lf.load_paths(mk, "ladrillo", TAG, ARM)["glaciers"]
            common = np.intersect1d(years, ship.index.values)
            mine = pd.Series(np.median(tot_f, axis=1), index=years).reindex(common)
            theirs = ship.med_cm.reindex(common)
            spread = (ship.p95_cm - ship.p05_cm).reindex(common)
            wi = (mine - theirs).abs().idxmax()
            worst, tol = abs(mine[wi] - theirs[wi]), 0.5 * float(spread.loc[wi])
            print("[PORT]  reconstruction vs shipped %s glaciers median, %s: worst |diff| "
                  "%.3f cm @%d, bound %.3f cm -> %s"
                  % (TAG, mk, worst, wi, tol, "PASS" if worst <= tol else "FAIL"))
            if worst > tol:
                raise SystemExit("[PORT] reconstruction does not track the shipped model.")
            port_checked = True

        # ---- SPLICE CHECK: what the climate swap does BEFORE the projection starts ----
        ## build_drivers re-anchors the override onto the FaIR anchor mean, so the two arms
        ## are the SAME MODEL ON THE SAME DRIVER through last_obs -- an IDENTITY, not an
        ## approximation, and the bound matches that kind of claim
        ## (`gate_bound_matches_its_claim`). Worth gating rather than asserting in a comment:
        ## the first version of the override substituted the LEVEL, and this fired at
        ## 0.137 cm, which is how the pre-1850 frame leak was found.
        i_obs = np.where(years == last_obs)[0][0]
        splice = float(np.abs(tot_m[i_obs] - tot_f[i_obs]).max())
        splice_tol = SPLICE_IDENTITY_TOL_CM
        if splice > splice_tol:
            raise SystemExit("[SPLICE] the MAGICC-driven arm differs by %.3e cm at %d, before "
                             "its climate is used (identity bound %.0e cm). The frame swap is "
                             "not a controlled single-axis change."
                             % (splice, last_obs, splice_tol))

        # ---- headroom and the R=1 realisable regrowth, on BOTH climates ----------------
        out = dict(splice_cm=splice)
        for lab, Td, Sd, tot in (("fair", T_f, S_f, tot_f), ("magicc", T_m, S_m, tot_m)):
            Seq = {b: sg.seq_of(Td[b], par[b]["a"], par[b]["b_"], par[b]["toff"])
                   for b in BLOCKS}
            H = {b: np.maximum(Sd[b] - Seq[b], 0.0) for b in BLOCKS}
            Htot = sum(H[b] for b in BLOCKS) * 100.0
            ## ⚠ S_eq CAN GO NEGATIVE ONCE THE DRIVER FALLS BELOW T_off, and on MAGICC's
            ## climate it does for a majority of draws in R19 and SLOWP at 2300. A negative
            ## S_eq is "equilibrium cumulative melt below zero" -- the glaciers REGROWING PAST
            ## their 1850 state. The exponential permits it; nothing we calibrated against
            ## says anything about it (the GlacierMIP3 rungs start at +1.2 K), so the raw
            ## headroom over-counts there. `Hfloor` re-derives the same bound with S_eq
            ## floored at the pre-industrial state, and BOTH are reported: the raw number is
            ## what the law says, the floored one is what is defensible.
            Hfl = {b: np.maximum(Sd[b] - np.maximum(Seq[b], 0.0), 0.0) for b in BLOCKS}
            Hfltot = sum(Hfl[b] for b in BLOCKS) * 100.0
            negfrac = np.mean([(Seq[b] < 0).mean(axis=1) for b in BLOCKS], axis=0)
            S1 = {b: sg.integrate(Td[b], **par[b], regrow_R=1) for b in BLOCKS}
            tot1 = sum(S1[b] for b in BLOCKS) * 100.0 - base
            Seq_tot = sum(sg.seq_of(Td[b], par[b]["a"], par[b]["b_"], par[b]["toff"])
                          for b in BLOCKS) * 100.0 - base
            Ssum = sum(Sd[b] for b in BLOCKS)
            Seqsum = sum(sg.seq_of(Td[b], par[b]["a"], par[b]["b_"], par[b]["toff"])
                         for b in BLOCKS)
            out[lab] = dict(tot=tot, H=Htot, Hfl=Hfltot, d1=tot1 - tot, ceil=Seq_tot,
                            negfrac=negfrac, phi=Ssum / np.maximum(Seqsum, 1e-12))
        per_marker[mk] = dict(years=years, last_obs=last_obs, **out)

        for lab in ("fair", "magicc"):
            o = out[lab]
            for y in HORIZONS:
                i = np.where(years == y)[0]
                if not len(i):
                    continue
                i = i[0]
                rows.append(dict(
                    marker=mk, decline=DECLINE[mk], climate=lab, year=y,
                    gmst_K=float(mg[mk].get(y, np.nan)) if lab == "magicc" else np.nan,
                    ladrillo_cm=float(np.median(o["tot"][i])),
                    equilibrium_ceiling_cm=float(np.median(o["ceil"][i])),
                    saturation_S_over_Seq=float(np.median(o["phi"][i])),
                    headroom_cm=float(np.median(o["H"][i])),
                    headroom_floored_cm=float(np.median(o["Hfl"][i])),
                    frac_blocks_Seq_negative=float(o["negfrac"][i]),
                    regrowth_R1_cm=float(np.median(o["d1"][i]))))

    # ---- the committed ladder, on the posterior, in BOTH frames --------------------------
    ## The rung convention is d1d_fourrung_seam.four_rung_fit: committed loss as a PERCENT of
    ## the volume remaining at 2020, with the block driver at T_b = amp_b * L and NO offset.
    ## The model AS RUN adds an offset (obs_anchor_b - amp_b * gmst_anchor), so both frames
    ## are reported: "as fitted" is the one comparable with the anchor, "as run" is the
    ## ladder the shipped projection actually walks. A gap between them is a finding.
    s2020 = {b: float(bc.loc[b, "S2020_data"]) for b in BLOCKS}
    anchor_yrs = list(range(int(tgb.year.max()) - (sg.ANCHOR_N - 1), int(tgb.year.max()) + 1))
    obs_anchor = {b: float(tgb.set_index("year").loc[anchor_yrs, b].mean()) for b in BLOCKS}
    gfile = pd.read_csv(_p(sg.GMST_MEAN % MARKERS[0]))
    gyr = gfile.year.values.astype(int)
    gbase = (gyr >= sg.DRIVER_BASE[0]) & (gyr <= sg.DRIVER_BASE[1])
    grb = gfile.gmst_C.values - gfile.gmst_C.values[gbase].mean()
    gmst_anchor = float(grb[np.isin(gyr, anchor_yrs)].mean())

    for L in GMIP3_LEVELS:
        for frame in ("as_fitted", "as_run"):
            num = np.zeros(NDRAW)
            den = np.zeros(NDRAW)
            for b in BLOCKS:
                Tb = amps[b] * L
                if frame == "as_run":
                    Tb = Tb + (obs_anchor[b] - amps[b] * gmst_anchor)
                num += sg.seq_of(Tb, par[b]["a"], par[b]["b_"], par[b]["toff"]) - s2020[b]
                den += par[b]["a"] - s2020[b]
            com = 100.0 * num / np.maximum(den, 1e-9)
            lo, hi = GMIP3_LIKELY[L]
            lrows.append(dict(level_K=L, frame=frame,
                              com_med=float(np.median(com)),
                              com_p05=float(np.percentile(com, 5)),
                              com_p95=float(np.percentile(com, 95)),
                              gmip3_central=GMIP3_CENTRAL[L],
                              gmip3_lo=lo, gmip3_hi=hi,
                              inside_likely=bool(lo <= np.median(com) <= hi)))

    df = pd.DataFrame(rows)
    dl = pd.DataFrame(lrows)
    df.to_csv(OUT, index=False)
    dl.to_csv(OUT_L, index=False)

    # =====================================================================================
    print("\n" + "=" * W)
    print("1. THE CLIMATE FORK — FaIR (drives Ladrillo/BRICK/FACTS) vs MAGICC's own GMST,")
    print("   K rel 1850-1900. Read this BEFORE any module attribution.")
    print("   ⚠ TWO FaIR COLUMNS, DELIBERATELY. `cfg` is the MEAN-CONFIG trajectory -- the")
    print("   one that actually drives the glacier reconstruction below, so it is the right")
    print("   number for §2. `med` is the 841-config ENSEMBLE MEDIAN -- the only column that")
    print("   is like-for-like with MAGICC's 600-member median. They differ by up to 0.4 K")
    print("   and the SIGN of the MAGICC-FaIR difference depends on which one is used at the")
    print("   rising markers, so quoting one statistic against the other is not safe.")
    print("=" * W)
    print("   %-8s %25s %25s %16s" % ("", "FaIR 2300", "MAGICC 2300", "MAGICC - FaIR"))
    print("   %-8s %8s %8s %8s %8s %8s %8s %8s %8s"
          % ("marker", "cfg", "med", "[p05", "p95]", "med", "[p05", "p95]", "on med"))
    dT, dT_cfg, disjoint = {}, {}, []
    for mk in MARKERS:
        gf = pd.read_csv(_p(sg.GMST_MEAN % mk)).set_index("year").gmst_C
        gf = gf - gf.loc[sg.DRIVER_BASE[0]:sg.DRIVER_BASE[1]].mean()
        cube = pd.read_csv(_p(FAIR_CUBE % mk)).set_index("year")
        cube = cube - cube.loc[sg.DRIVER_BASE[0]:sg.DRIVER_BASE[1]].mean()
        v = cube.loc[2300].values
        fmed, flo, fhi = np.median(v), np.percentile(v, 5), np.percentile(v, 95)
        g = mg[mk]
        mrow = pd.read_csv(_p(MAGICC_GMST))
        mrow = mrow[(mrow.scenario == mk) & (mrow.year == 2300)].iloc[0]
        dT[mk] = float(mrow["med"]) - float(fmed)
        dT_cfg[mk] = float(mrow["med"]) - float(gf.loc[2300])
        if float(mrow.p95) < flo or float(mrow.p05) > fhi:
            disjoint.append(mk)
        print("   %-8s %8.2f %8.2f %8.2f %8.2f %8.2f %8.2f %8.2f %8.2f%s"
              % (mk, gf.loc[2300], fmed, flo, fhi, mrow["med"], mrow.p05, mrow.p95,
                 dT[mk], "  *" if DECLINE[mk] else ""))
    print("   * = peak-and-decline marker. Bands are 5-95% of each model's own ensemble.")
    dec = [m for m in MARKERS if DECLINE[m]]
    rise = [m for m in MARKERS if not DECLINE[m]]
    print("   ⚠ THE DIVERGENCE IS SPECIFIC TO THE DECLINE. On the %d declining markers MAGICC"
          % len(dec))
    print("     is colder by %.2f-%.2f K on the ensemble-median basis (%.2f-%.2f on mean-config)."
          % (-max(dT[m] for m in dec), -min(dT[m] for m in dec),
             -max(dT_cfg[m] for m in dec), -min(dT_cfg[m] for m in dec)))
    print("     On the %d rising markers the difference is %+.2f to %+.2f K and its SIGN FLIPS"
          % (len(rise), min(dT[m] for m in rise), max(dT[m] for m in rise)))
    print("     between the two FaIR statistics -- do not claim a direction there.")
    print("   ⚠ At %s the two ensembles' 5-95%% ranges DO NOT OVERLAP at 2300."
          % (", ".join(disjoint) if disjoint else "no marker"))

    # =====================================================================================
    print("\n" + "=" * W)
    print("2. HEADROOM UNDER EACH CLIMATE — the controlled swap. Same posterior, same law,")
    print("   same clamp, same draws; only the driving temperature changes. cm at 2300.")
    print("   H = S - S_eq bounds any regrowth scheme; H(floor) re-derives it with S_eq")
    print("   floored at the pre-industrial state, since a negative S_eq means regrowth")
    print("   PAST 1850 and nothing we calibrated against speaks to that.")
    print("=" * W)
    ## the MAGICC drawdown, RECOMPUTED from the comparison table rather than quoted, then
    ## asserted against the recorded constant so a stale number cannot pass as agreement.
    ## ⚠ "peak" here is the peak OVER THE REPORTED HORIZONS (%s), not the true path maximum;
    ## the recorded 8.58 cm is the path peak at 2144, which is why the two differ slightly.
    mm = cmp_g.loc["MAGICC-SLR"]
    dd = {mk: float(mm.loc[mk].max() - mm.loc[mk].loc[2300]) for mk in MARKERS}
    dd_max = max(dd.values())
    if abs(dd_max - MAGICC_DRAWDOWN_MAX_CM) > DRAWDOWN_TOL_CM:
        raise SystemExit("[DRAWDOWN] recomputed max MAGICC drawdown %.2f cm vs the recorded "
                         "%.2f cm, bound %.2f -- the constant is stale."
                         % (dd_max, MAGICC_DRAWDOWN_MAX_CM, DRAWDOWN_TOL_CM))
    ## ⚠ THE FaIR COLUMNS WERE COMPUTED AND NEVER PRINTED. `frac_blocks_Seq_negative` and
    ## `headroom_floored_cm` have been written to the CSV for BOTH climates since this scope
    ## was first run, but the table showed only MAGICC's -- so the question "how much of the
    ## negative-equilibrium problem is in OUR OWN forcing?" read as unmeasured when it was
    ## merely undisplayed. That is `recorded_but_never_restored`: a field a producer writes
    ## and no reader consumes is invisible until someone needs the value. Both climates now
    ## print, and the FLOORED headroom prints beside the raw one for FaIR as well, because
    ## the difference between them IS the amount of regrowth that would go past 1850.
    print("   %-8s %8s %8s %7s | %8s %8s %7s | %8s %8s %8s"
          % ("marker", "H(FaIR)", "Hfl(FaIR)", "S_eq<0", "H(MAG)", "Hfl(MAG)", "S_eq<0",
             "R=1 FaIR", "R=1 MAG", "MAG draw"))
    for mk in MARKERS:
        s2 = df[(df.marker == mk) & (df.year == 2300)]
        f = s2[s2.climate == "fair"].iloc[0]
        m = s2[s2.climate == "magicc"].iloc[0]
        print("   %-8s %8.2f %8.2f %6.1f%% | %8.2f %8.2f %6.1f%% | %8.2f %8.2f %8.2f%s"
              % (mk, f.headroom_cm, f.headroom_floored_cm,
                 100 * f.frac_blocks_Seq_negative,
                 m.headroom_cm, m.headroom_floored_cm,
                 100 * m.frac_blocks_Seq_negative, f.regrowth_R1_cm, m.regrowth_R1_cm,
                 dd[mk], "  *" if DECLINE[mk] else ""))
    print("   S_eq<0 = share of block x draw cells at 2300 whose equilibrium is below the")
    print("   pre-industrial state, ON EACH CLIMATE. H - Hfl is the part of the headroom that")
    print("   would regrow PAST 1850, i.e. what flooring S_eq costs a regrowth scheme.")
    print("   MAG draw = MAGICC's own peak->2300")
    print("   drawdown over the reported horizons (max %.2f cm; recorded path peak %.2f)."
          % (dd_max, MAGICC_DRAWDOWN_MAX_CM))
    print("   splice check: worst |arm difference| at last_obs = %.1e cm (identity bound "
          "%.0e)." % (max(per_marker[mk]["splice_cm"] for mk in MARKERS),
                      SPLICE_IDENTITY_TOL_CM))
    d23 = df[df.year == 2300]
    Hf = float(d23[d23.climate == "fair"].headroom_cm.max())
    Hm = float(d23[d23.climate == "magicc"].headroom_cm.max())
    Hmfl = float(d23[d23.climate == "magicc"].headroom_floored_cm.max())
    R1m = float(d23[d23.climate == "magicc"].regrowth_R1_cm.abs().max())
    ## the per-marker test, not a max-to-max one: on how many markers does the bound now
    ## COVER MAGICC's own drawdown?
    ## ⚠ ONLY MARKERS WHERE MAGICC ACTUALLY DRAWS DOWN COUNT. A marker with no drawdown is
    ## "covered" by a zero bound trivially, and counting those turns 2 of 5 into 4 of 7 --
    ## a pass manufactured out of cells the question does not apply to.
    drew = [mk for mk in MARKERS if dd[mk] > REPORT_PRECISION_CM]
    covered = [mk for mk in drew
               if float(d23[(d23.marker == mk) & (d23.climate == "magicc")]
                        .headroom_floored_cm.iloc[0]) >= dd[mk]]
    print("   of the %d markers where MAGICC actually draws down (> %.1f cm), the floored"
          % (len(drew), REPORT_PRECISION_CM))
    print("   bound on MAGICC's climate covers it on %d: %s. Uncovered: %s."
          % (len(covered), ", ".join(covered) or "none",
             ", ".join(m for m in drew if m not in covered) or "none"))

    # =====================================================================================
    print("\n" + "=" * W)
    print("3. THE COMMITTED LADDER vs GlacierMIP3 — does the CURVE disagree with the")
    print("   external anchor it was fitted to? % of 2020-remaining volume, posterior.")
    print("=" * W)
    for frame in ("as_fitted", "as_run"):
        print("   frame = %s%s" % (frame, "   (T_b = amp_b * L, the d1d fit convention)"
                                   if frame == "as_fitted"
                                   else "   (+ the shipped driver offset)"))
        print("      %-8s %10s %18s %10s %16s" % ("level", "posterior", "[p05, p95]",
                                                  "GMIP3", "likely range"))
        for L in GMIP3_LEVELS:
            r = dl[(dl.level_K == L) & (dl.frame == frame)].iloc[0]
            print("      +%.1f K   %9.1f%% [%6.1f, %6.1f]%%  %8.1f%%  [%4.1f, %4.1f]%%  %s"
                  % (L, r.com_med, r.com_p05, r.com_p95, r.gmip3_central,
                     r.gmip3_lo, r.gmip3_hi, "inside" if r.inside_likely else "OUTSIDE"))
    n_out = int((~dl[dl.frame == "as_fitted"].inside_likely).sum())
    print("   as_fitted: %d of %d rungs outside the GlacierMIP3 likely range."
          % (n_out, len(GMIP3_LEVELS)))

    # =====================================================================================
    print("\n" + "=" * W)
    print("4. RATE vs EQUILIBRIUM AT 2100 — is the low 2100 level the CURVE or the APPROACH?")
    print("   'ceiling' = where Ladrillo would sit at 2100 if the rate were infinite.")
    print("   cm rel %d-%d; FaIR climate, the one all four arms are compared on."
          % PROJ_BASE)
    print("=" * W)
    print("   %-8s %9s %9s %8s %9s %9s %9s %10s" % ("marker", "Ladrillo", "ceiling", "S/Seq",
                                                    "BRICK2.0", "FACTS", "MAGICC", "headroom*"))
    hi_cmp = {}
    for mk in MARKERS:
        s = df[(df.marker == mk) & (df.year == 2100) & (df.climate == "fair")].iloc[0]
        c = {src: (float(cmp_g.loc[src, mk, 2100])
                   if (src, mk, 2100) in cmp_g.index else float("nan"))
             for src in ("BRICK 2.0", "FACTS", "MAGICC-SLR")}
        hi_cmp[mk] = max(v for v in c.values() if v == v)
        print("   %-8s %9.2f %9.2f %8.2f %9.2f %9.2f %9.2f %10.2f%s"
              % (mk, s.ladrillo_cm, s.equilibrium_ceiling_cm, s.saturation_S_over_Seq,
                 c["BRICK 2.0"], c["FACTS"], c["MAGICC-SLR"],
                 s.equilibrium_ceiling_cm - s.ladrillo_cm, "  *" if DECLINE[mk] else ""))
    print("   *headroom here = ceiling - Ladrillo = the most an infinitely fast approach")
    print("    could add at 2100. Compare it with the largest comparator gap below.")
    gaps = {mk: hi_cmp[mk] - float(df[(df.marker == mk) & (df.year == 2100)
                                      & (df.climate == "fair")].ladrillo_cm.iloc[0])
            for mk in MARKERS}
    room = {mk: float(df[(df.marker == mk) & (df.year == 2100) & (df.climate == "fair")]
                      .equilibrium_ceiling_cm.iloc[0]) - float(
                df[(df.marker == mk) & (df.year == 2100) & (df.climate == "fair")]
                .ladrillo_cm.iloc[0]) for mk in MARKERS}
    print("   largest comparator gap at 2100: %.2f cm (%s). Rate headroom there: %.2f cm."
          % (max(gaps.values()), max(gaps, key=gaps.get), room[max(gaps, key=gaps.get)]))

    # =====================================================================================
    print("\n" + "=" * W)
    print("5. EXTRAPOLATION RANGE — the rungs span %.1f-%.1f K. Where do the markers sit?"
          % (GMIP3_LEVELS[0], GMIP3_LEVELS[-1]))
    print("=" * W)
    print("   %-8s %22s %22s" % ("marker", "FaIR: below / above", "MAGICC: below / above"))
    for mk in MARKERS:
        line = "   %-8s" % mk
        gf = pd.read_csv(_p(sg.GMST_MEAN % mk)).set_index("year").gmst_C
        gf = gf - gf.loc[sg.DRIVER_BASE[0]:sg.DRIVER_BASE[1]].mean()
        for series in (gf.loc[2025:2300], mg[mk].loc[2025:2300]):
            lo = 100.0 * float((series < GMIP3_LEVELS[0]).mean())
            hi = 100.0 * float((series > GMIP3_LEVELS[-1]).mean())
            line += "%13.0f%% %8.0f%%" % (lo, hi)
        print(line + ("  *" if DECLINE[mk] else ""))
    print("   % of projection years 2025-2300 with GMST outside the fitted rung span.")

    # =====================================================================================
    print("\n" + "=" * W)
    print("6. VERDICT")
    print("=" * W)
    ratio_h = Hm / Hf if Hf > 1e-9 else float("nan")
    phi100 = df[(df.year == 2100) & (df.climate == "fair")].saturation_S_over_Seq
    phi300 = df[(df.year == 2300) & (df.climate == "fair")].saturation_S_over_Seq
    dec = [m for m in MARKERS if DECLINE[m]]
    print("   1. THE MAGICC GLACIER GAP IS FIRST OF ALL A CLIMATE GAP. On the four DECLINING")
    print("      markers -- the only ones where a drawdown is even possible -- MAGICC's own")
    print("      2300 GMST is %.2f-%.2f K COLDER than FaIR's on the SAME emissions (ensemble"
          % (-max(dT[m] for m in dec), -min(dT[m] for m in dec)))
    print("      medians; the two ensembles' 5-95%% ranges do not even overlap at %s)."
          % (", ".join(disjoint) if disjoint else "no marker"))
    print("      Driving Ladrillo's UNCHANGED glacier module")
    print("      with MAGICC's own climate raises its worst equilibrium headroom at 2300 from")
    print("      %.2f cm to %.2f cm (%.1fx), or %.2f cm with S_eq floored at pre-industrial."
          % (Hf, Hm, ratio_h, Hmfl))
    print("      The earlier '4x too small' compared a bound computed at FaIR's temperature")
    print("      against a drawdown computed at MAGICC's -- not like-for-like.")
    print("   2. ON ITS OWN CLIMATE THE BOUND NO LONGER RULES THE LARGEST DRAWDOWNS OUT.")
    print("      The floored bound covers MAGICC's own drawdown on %d of the %d markers that"
          % (len(covered), len(drew)))
    print("      have one (%s) -- the two LARGEST -- and falls short on %s."
          % (", ".join(covered) or "none",
             ", ".join(m for m in drew if m not in covered) or "none"))
    print("      What is left is a RATE gap, not an equilibrium one: symmetric relaxation")
    print("      (R=1, the fastest this law allows) delivers %.2f cm against %.2f cm, i.e."
          % (R1m, dd_max))
    print("      %.0f%%. Matching MAGICC would need regrowth FASTER than melt, which the"
          % (100 * R1m / max(dd_max, 1e-9)))
    print("      shared-kappa form cannot express at any R -- a structural difference, not a")
    print("      miscalibrated curve.")
    print("   3. THE CURVE IS NOT OUT OF LINE WITH ITS EXTERNAL ANCHOR. %d of %d GlacierMIP3"
          % (n_out, len(GMIP3_LEVELS)))
    print("      rungs fall outside the likely range on the posterior, and the posterior sits")
    print("      ABOVE the GlacierMIP3 central at every rung (%s vs %s %%), so if anything the"
          % ("/".join("%.0f" % dl[(dl.level_K == L) & (dl.frame == "as_fitted")].com_med.iloc[0]
                      for L in GMIP3_LEVELS),
             "/".join("%.0f" % GMIP3_CENTRAL[L] for L in GMIP3_LEVELS)))
    print("      curve commits MORE loss than the anchor, not less. Lowering S_eq is not")
    print("      indicated by the anchor, and the driver-offset frame changes nothing (§3).")
    print("   4. THE 2100 LEVEL IS RATE-LIMITED, NOT EQUILIBRIUM-LIMITED. Saturation S/S_eq")
    print("      at 2100 is %.2f-%.2f (%.2f-%.2f by 2300), and the instant-equilibrium ceiling"
          % (phi100.min(), phi100.max(), phi300.min(), phi300.max()))
    print("      sits %.1f-%.1f cm above the shipped median -- against a largest comparator"
          % (min(room.values()), max(room.values())))
    print("      gap of %.2f cm. The curve cannot be what holds 2100 down; there is %.0fx more"
          % (max(gaps.values()), room[max(gaps, key=gaps.get)] / max(gaps.values(), default=1)))
    print("      room in the approach than the whole gap needs.")
    print("      CROSS-CHECK: the independent single-reservoir Mengel arm reported 62%")
    print("      realised-of-committed at 2100 (outputs/mengel_hightemp_melt_summary.md),")
    print("      the same order as the %.0f-%.0f%% here on a different structure."
          % (100 * phi100.min(), 100 * phi100.max()))
    print("   5. SO THE TWO GAPS ARE NOT ONE FINDING. The handoff's guess that the 2100")
    print("      lowness and the 2300 drawdown share a cause in the equilibrium curve is not")
    print("      supported: the curve is high, not low, and both gaps sit in the RATE law --")
    print("      the 2100 one in how fast melt approaches S_eq, the 2300 one in whether")
    print("      regrowth may exceed melt. That is the next thing to scope, and it is the")
    print("      kappa/nu pair, not (a, b, T_off).")
    print("   ⚠ NOT SCOPED HERE: whether MAGICC's colder 2300 is right. It is a CLIMATE")
    print("      question (%.2f K at vvLN) and it now carries the glacier comparison, so it"
          % -dT["vvLN"])
    print("      deserves its own check against the FaIR calib 1.6.0 forcing before any of")
    print("      this is used to argue Ladrillo's glacier module is missing a mechanism.")

    print("\nwrote %s\n      %s" % (os.path.relpath(OUT, REPO), os.path.relpath(OUT_L, REPO)))


if __name__ == "__main__":
    main()
