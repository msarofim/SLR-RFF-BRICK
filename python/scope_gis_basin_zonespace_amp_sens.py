#!/usr/bin/env python3
"""
scope_gis_basin_zonespace_amp_sens.py — the question the zone-space mock exists
to make askable: the dormant basins now tap at a LOCAL temperature, and how
much local warming a given GMST buys is UNCERTAIN. Does the pass region survive
that uncertainty?

WHY THIS EXISTS (2026-08-18, immediately after the zone-space mock)
  The zone-space run reproduced GMT space cell-for-cell (59/59). That is a
  consistency result and nothing more: W was set GMT-equivalent and the map is
  monotone, so along the MEDIAN-parameter ssp585 path the translation is close
  to a pure re-parameterisation. Quoting 59/59 as evidence FOR the basin
  structure would be quoting a near-tautology.

  What zone space genuinely adds is a knob GMT space does not have. The per-zone
  amplification is a measured quantity with real spread — north/full
  N(2.83, 0.92) with a product range 1.84-4.06 (2.2x; GISTEMP's 1200 km
  smoothing is the high outlier), central/full N(2.36, 0.53). In GMT space that
  uncertainty is invisible. In zone space it moves every dormant basin's
  activation date, and it can move a low scenario ACROSS an onset.

THE PHYSICAL FRAMING, WHICH IS THE WHOLE TEST
  The onset is a property of the BASIN, not of the emissions scenario: the
  marginal ice taps when the LOCAL temperature reaches some value. So the
  zone-space onsets T_on_zone and their widths W_zone are PINNED at the values
  the mock translated under the prior-mean amp, and amp is then varied. Nothing
  is re-translated — re-translating per amp would map straight back to GMT space
  and, by construction, find nothing. Varying amp with pinned onsets asks the
  real question: if Greenland's north amplifies more (or less) than the central
  estimate, does the structure still clear the scorecard?

THE ARMS
  Two families, both reported, neither privileged:
    RANGE   the observed PRODUCT range (lo, mean, hi) from gis_amp_prior.csv --
            the spread is product-choice-driven, not sampling noise, so the
            range is the honest envelope.
    SIGMA   (mean - sd, mean, mean + sd) -- the parametric version, for
            comparability with anything that wants a normal prior.
  Full factorial over the two dormant zones: 9 cells per family, 720 grid cells
  each.

THE QUESTIONS, FIXED BEFORE RUNNING
  A1  how many of the base 59 passers survive in each amp cell, and does any
      amp cell empty the pass region entirely?
  A2  HARD: does a high amp push a low scenario across a PINNED onset, so that
      ssp126/245 stop being bit-identical to shipped? This is the failure mode
      the zone-space move introduces and GMT space cannot see.
      MEASURED TWO WAYS, because a first draft got this wrong in exactly the way
      the zone-space Z3 gate got it wrong: counting every grid cell whose low
      scenario is non-zero charges amp for the 2.5 and 3.0 K mid onsets, which
      sit below ssp245's 2300 GMT and are ALREADY active at the mean amp (that
      draft reported 288 "leaks" in the mean/mean cell, i.e. the base itself).
      The two honest metrics are:
        A2a  leak among the cells that PASS in this amp cell -- the deliverable
             question, since only a passer would ever be shipped;
        A2b  leak in EXCESS of the mean/mean base -- i.e. attributable to amp.
  A3  which zone's amp dominates the sensitivity -- central or north?
  A4  is there an AMP-ROBUST CORE -- cells that clear the scorecard in EVERY
      amp arm? A structure whose passing set moves wholesale with amp is a
      weaker claim than one with a core that survives the whole envelope, and
      the core (if any) is what a write-up should quote.
      REPORTED TWO WAYS, and the difference matters. The FULL factorial treats
      central and north amp as INDEPENDENT, which includes anti-correlated
      corners (central at its product high while north sits at its product low).
      Those two numbers come from the SAME gridded products over ADJACENT
      latitude bands, so anti-correlation is not a physically live case -- it is
      an artefact of the factorial. The DIAGONAL (both zones at lo, both at
      mean, both at hi) is the defensible envelope. Both cores are printed;
      neither is suppressed.
  FALSIFIER: if the pass region survives only in the central amp cell, the
  structure is resting on a point estimate of a 2.2x-spread quantity, and that
  must be said plainly rather than reported as "the mock passes".

READS   the zone-space mock (grid, scorecard, pinned onsets), gis_amp_prior.csv
WRITES  outputs/scope_gis_basin_zonespace_amp_sens.csv

  source ~/climate-env/bin/activate
  python3 python/scope_gis_basin_zonespace_amp_sens.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
import scope_gis_basin_zonespace_vs_literature as zs  # noqa: E402
import scope_gis_leq_ridge_vs_literature as ridge  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    GIS_V0_M, IREF, SSPS, YEARS, gis_shape_table, gmst_rebased, regional_driver,
)
from diag_gis_zone_driver_scope import shape_fun, zone_driver  # noqa: E402

ZONE_OF, AMP_WINDOW = zs.ZONE_OF, zs.AMP_WINDOW
T_ON_MID, T_ON_HIGH = zs.T_ON_MID, zs.T_ON_HIGH
V_TOT, MID_SHARE, TAU = zs.V_TOT, zs.MID_SHARE, zs.TAU
LIT_2300_M, G4_DEGRADE_TOL = zs.LIT_2300_M, zs.G4_DEGRADE_TOL
REPRO_TOL, RIDGE_CSV = zs.REPRO_TOL, zs.RIDGE_CSV
POST, TARGETS, HIND, HIND_DRIVER = zs.POST, zs.TARGETS, zs.HIND, zs.HIND_DRIVER
MAP_SSP, INERT_TOL = zs.MAP_SSP, zs.INERT_TOL

ARM_FAMILIES = {"RANGE": ("lo", "mean", "hi"), "SIGMA": ("-1sd", "mean", "+1sd"),
                # ANCHOR: what the amp LEVEL is anchored on. The shipped driver
                # takes the level from OBSERVATIONS and only the SHAPE from
                # CMIP6 (amp = S(dT) * obs_full). For a basin that activates at
                # a warming level far outside the observed range, the models'
                # own amplification is the arguably relevant number, and CMIP6
                # runs 1.29x (south) to 1.48x (north) BELOW observations.
                "ANCHOR": ("cmip6", "mean")}
BASE_CSV = zs.OUT
OUT = os.path.join(REPO, "outputs/scope_gis_basin_zonespace_amp_sens.csv")
KEY = ["t_on_mid", "t_on_high", "v_tot", "mid_share", "tau"]


def amp_arms(zone):
    pri = pd.read_csv(os.path.join(REPO, "outputs/gis_amp_prior.csv"))
    r = pri[(pri.zone == zone) & (pri.window == AMP_WINDOW)].iloc[0]
    # the CMIP6-anchored level: R_secant at the anchor warming level, i.e. the
    # models' own amplification rather than the observed one. S(dT) is shared,
    # so this rescales the whole curve by r_anchor / obs_amp_full.
    mp = (os.path.join(REPO, "outputs/gis_amp_shape_meta.csv") if zone == "south"
          else os.path.join(REPO, f"outputs/gis_amp_shape_meta_{zone}.csv"))
    m = pd.read_csv(mp).iloc[0]
    assert abs(float(m.obs_amp_full) - float(r["mean"])) < 1e-9, (
        f"{zone}: shape-meta obs_amp_full {m.obs_amp_full} != prior mean "
        f"{r['mean']} — the two tables have drifted apart")
    return {"lo": float(r.lo), "mean": float(r["mean"]), "hi": float(r.hi),
            "-1sd": float(r["mean"] - r.sd), "+1sd": float(r["mean"] + r.sd),
            "cmip6": float(m.r_anchor)}


def main():
    base = pd.read_csv(BASE_CSV)
    base_pass = set(map(tuple, base[base.all_pass][KEY].to_numpy()))
    # the PINNED onsets/widths, straight out of the zone-space run
    pin = {}
    for b, col_t, col_w, grid in (("mid", "t_on_mid", "w_mid_zone", T_ON_MID),
                                  ("high", "t_on_high", "w_high_zone", T_ON_HIGH)):
        zcol = f"t_on_{b}_zone"
        for t in grid:
            sub = base[base[col_t] == t]
            pin[(b, t)] = (float(sub[zcol].iloc[0]), float(sub[col_w].iloc[0]))

    post = pd.read_csv(POST)
    pa = ridge.native_greenland(post.median(numeric_only=True), ridge.gis_tbar())
    S_south = gis_shape_table()
    gmt, south = {}, {}
    for ssp, lab in SSPS:
        _, rb = gmst_rebased(ssp)
        gmt[lab] = rb
        south[lab] = regional_driver(rb, np.array([pa["gis_amp"]]), S_south)[0]

    i21 = int(np.where(YEARS == 2100)[0][0])
    i23 = int(np.where(YEARS == 2300)[0][0])
    ih0 = int(np.where(YEARS == HIND[0])[0][0])
    ih1 = int(np.where(YEARS == HIND[1])[0][0])
    tgt = pd.read_csv(TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    lo, hi = 1e-4, 1e3
    for _ in range(80):
        m = np.sqrt(lo * hi)
        L = ridge.ab_series(south[dict(SSPS)[HIND_DRIVER]], pa, 1.0, m)[0]
        if 100.0 * (L[ih1] - L[ih0]) < want_cm:
            lo = m
        else:
            hi = m
    s1 = float(np.sqrt(lo * hi))
    rec = pd.read_csv(RIDGE_CSV).set_index("k")
    inc2300, inc2100 = {}, {}
    for _, lab in SSPS:
        L, _ = ridge.ab_series(south[lab], pa, 1.0, s1)
        inc2300[lab] = float(L[i23] - L[IREF].mean())
        inc2100[lab] = float(L[i21] - L[IREF].mean())
    g = [abs(s1 - float(rec.loc[1.0, "rate_scale"]))] + [
        abs(inc2300[lab] - float(rec.loc[1.0, f"m2300_{lab}"])) for _, lab in SSPS]
    if max(g) > REPRO_TOL:
        raise SystemExit(f"REPRODUCTION GATE FAILED ({max(g):.2e})")
    g4_ref = float(rec.loc[1.0, "g4_2100_cm"])
    inv_head = GIS_V0_M - float(np.clip(pa["gis_c1"] * south["SSP5-8.5"][i23]
                                        + pa["gis_c0"], 0, GIS_V0_M))
    shp = {b: shape_fun(ZONE_OF[b]) for b in ZONE_OF}
    arms = {b: amp_arms(ZONE_OF[b]) for b in ZONE_OF}

    print("DOES THE PASS REGION SURVIVE PER-ZONE AMP UNCERTAINTY?  — "
          f"Ladrillo {zs.LADRILLO_TAG}, onsets PINNED in zone units")
    print(f"  ridge k=1 gate PASSED ({max(g):.1e}); base passers "
          f"{len(base_pass)}/{len(base)}")
    for b in ZONE_OF:
        a = arms[b]
        print(f"  {b:5s}/{ZONE_OF[b]:8s} amp arms  lo {a['lo']:.3f}  "
              f"-1sd {a['-1sd']:.3f}  mean {a['mean']:.3f}  "
              f"+1sd {a['+1sd']:.3f}  hi {a['hi']:.3f}")
    print()

    rows, pass_sets = [], {}
    for fam, labels in ARM_FAMILIES.items():
        for am in labels:
            for ah in labels:
                amp = {"mid": arms["mid"][am], "high": arms["high"][ah]}
                zd = {}
                for b in ZONE_OF:
                    zd[b] = {lab: zone_driver(gmt[lab], ZONE_OF[b], amp[b],
                                              shp[b])[0] for _, lab in SSPS}
                unit = {}
                for b, grid in (("mid", T_ON_MID), ("high", T_ON_HIGH)):
                    for t in grid:
                        tz, wz = pin[(b, t)]
                        for tau in TAU:
                            for _, lab in SSPS:
                                unit[(b, t, tau, lab)] = zs.dormant_unit_zone(
                                    zd[b][lab], tz, wz, tau)

                npass, surv, passing = 0, 0, set()
                leak_cells, leak_max = 0, 0.0          # all cells (base-relative)
                leak_pass, leak_pass_max = 0, 0.0      # among PASSERS (A2a)
                for t_mid in T_ON_MID:
                    for t_high in T_ON_HIGH:
                        if t_high <= t_mid:
                            continue
                        for vt in V_TOT:
                            for sh in MID_SHARE:
                                for tau in TAU:
                                    k = (t_mid, t_high, vt, sh, tau)
                                    if sh == 0 and t_mid != T_ON_MID[0]:
                                        continue
                                    v_mid, v_high = sh * vt, (1 - sh) * vt
                                    m23, d21, ok = {}, {}, True
                                    cell_leak = 0.0
                                    for _, lab in SSPS:
                                        um = unit[("mid", t_mid, tau, lab)]
                                        uh = unit[("high", t_high, tau, lab)]
                                        d23 = v_mid * um[i23] + v_high * uh[i23]
                                        d21[lab] = v_mid * um[i21] + v_high * uh[i21]
                                        m23[lab] = inc2300[lab] + d23
                                        ok &= (LIT_2300_M[lab][0] <= m23[lab]
                                               <= LIT_2300_M[lab][1])
                                        if lab != MAP_SSP and abs(d23) > INERT_TOL:
                                            leak_cells += 1
                                            leak_max = max(leak_max, abs(d23))
                                            cell_leak = max(cell_leak, abs(d23))
                                    g4 = (100.0 * (inc2100["SSP5-8.5"]
                                                   - inc2100["SSP1-2.6"])
                                          + 100.0 * (d21["SSP5-8.5"]
                                                     - d21["SSP1-2.6"]))
                                    ok &= abs(g4 / g4_ref - 1.0) <= G4_DEGRADE_TOL
                                    ok &= vt <= inv_head
                                    if ok:
                                        npass += 1
                                        passing.add(k)
                                        if k in base_pass:
                                            surv += 1
                                        if cell_leak > INERT_TOL:
                                            leak_pass += 1
                                            leak_pass_max = max(leak_pass_max,
                                                                cell_leak)
                pass_sets[(fam, am, ah)] = passing
                rows.append(dict(family=fam, arm_mid=am, arm_high=ah,
                                 amp_mid=amp["mid"], amp_high=amp["high"],
                                 n_pass=npass, n_base_surviving=surv,
                                 frac_base_surviving=surv / max(len(base_pass), 1),
                                 leak_cells_all=leak_cells,
                                 leak_max_all_m=leak_max,
                                 leak_cells_among_passers=leak_pass,
                                 leak_max_among_passers_m=leak_pass_max))

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    for fam in ARM_FAMILIES:
        f = df[df.family == fam]
        print(f"=== {fam} arms — passers (of 720) ===\n")
        print(f.pivot_table(index="arm_mid", columns="arm_high",
                            values="n_pass").astype(int).to_string())
        print(f"\n=== {fam} arms — of the {len(base_pass)} base passers, "
              f"how many survive ===\n")
        print(f.pivot_table(index="arm_mid", columns="arm_high",
                            values="n_base_surviving").astype(int).to_string())
        print()

    b0 = df[(df.arm_mid == "mean") & (df.arm_high == "mean")
            & (df.family == "RANGE")].iloc[0]
    df["leak_cells_excess"] = df.leak_cells_all - int(b0.leak_cells_all)

    print("=== A2a HARD — leak among the cells that PASS in each amp cell ===\n")
    bad = df[df.leak_cells_among_passers > 0]
    if len(bad):
        print(bad[["family", "arm_mid", "arm_high", "amp_mid", "amp_high",
                   "n_pass", "leak_cells_among_passers",
                   "leak_max_among_passers_m"]].to_string(index=False))
        print("\n  VERDICT A2a: LEAK — a PASSING cell moves ssp126/245 at 2300, "
              "so they would no longer be bit-identical to shipped. This is the "
              "failure mode the zone-space move introduces; report it.")
    else:
        print(f"  none, in all {len(df)} amp cells across both families — "
              "VERDICT A2a: PASS")
        print("  every passing cell keeps ssp126/245 identically at their "
              "shipped values, at every amp arm")

    print(f"\n=== A2b — leak over ALL 720 grid cells, in EXCESS of the "
          f"mean/mean base ({int(b0.leak_cells_all)} cells, "
          f"max {b0.leak_max_all_m:.3f} m) ===\n")
    print("  The base count is NOT an amp effect: the 2.5 and 3.0 K mid onsets "
          "sit below\n  ssp245's 2300 GMT and are active at every amp, in GMT "
          "space too. Only the\n  EXCESS is attributable to amplification.\n")
    for fam in ARM_FAMILIES:
        f = df[df.family == fam]
        print(f"  {fam} excess leak cells:")
        print(f.pivot_table(index="arm_mid", columns="arm_high",
                            values="leak_cells_excess").astype(int)
              .to_string().replace("\n", "\n  "))
        print()

    print("\n=== A1/A3 ===\n")
    worst = df.loc[df.n_pass.idxmin()]
    print(f"  emptiest amp cell: {worst.family} mid={worst.arm_mid} "
          f"high={worst.arm_high} -> {int(worst.n_pass)} passers "
          f"({int(worst.n_base_surviving)} of the base {len(base_pass)})")
    print(f"  pass region is NON-EMPTY in "
          f"{int((df.n_pass > 0).sum())}/{len(df)} amp cells")
    for z, col in (("mid/central", "arm_mid"), ("high/north", "arm_high")):
        sp = df.groupby(col)["n_pass"].mean()
        print(f"  A3 sensitivity to {z:11s} amp: mean passers by arm "
              f"{ {k: round(v, 1) for k, v in sp.items()} }")
    print("\n=== A4 — the AMP-ROBUST CORE: cells passing in EVERY amp arm ===\n")
    for fam in ARM_FAMILIES:
        sets = [s for (f, _, _), s in pass_sets.items() if f == fam]
        core = set.intersection(*sets)
        union = set.union(*sets)
        print(f"  {fam:6s} core {len(core):3d}   union {len(union):3d}   "
              f"base-59 in core {len(core & base_pass):3d}")
        if core:
            c = pd.DataFrame(sorted(core), columns=KEY)
            for knob in KEY:
                print(f"           {knob:10s} {sorted(float(v) for v in c[knob].unique())}")
            act = c[c.mid_share > 0]
            print(f"           active-mid cells {len(act)}; single-basin "
                  f"{len(c) - len(act)}")
        print()
    print("=== A4b — the DIAGONAL core: both zones moved TOGETHER "
          "(lo/lo, mean/mean, hi/hi) ===\n")
    diag_core = {}
    for fam, labels in ARM_FAMILIES.items():
        sets = [pass_sets[(fam, a, a)] for a in labels]
        core, union = set.intersection(*sets), set.union(*sets)
        diag_core[fam] = core
        print(f"  {fam:6s} core {len(core):3d}   union {len(union):3d}   "
              f"base-59 in core {len(core & base_pass):3d}   "
              f"(arm sizes {[len(s) for s in sets]})")
        # an empty core is the headline claim here -- evidence it pairwise
        pw = {f"{a}&{b}": len(pass_sets[(fam, a, a)] & pass_sets[(fam, b, b)])
              for i, a in enumerate(labels) for b in labels[i + 1:]}
        print(f"         pairwise overlaps {pw}; three-way {len(core)} "
              f"=> the surviving sets at the two ends are "
              f"{'DISJOINT' if len(core) == 0 else 'overlapping'}")
        if core:
            c = pd.DataFrame(sorted(core), columns=KEY)
            for knob in KEY:
                print(f"           {knob:10s} "
                      f"{sorted(float(v) for v in c[knob].unique())}")
            act = c[c.mid_share > 0]
            print(f"           active-mid cells {len(act)}; single-basin "
                  f"{len(c) - len(act)}")
        print()

    rng_core = diag_core["RANGE"]
    pd.DataFrame(sorted(rng_core), columns=KEY).to_csv(
        OUT.replace(".csv", "_robust_core.csv"), index=False)   # DIAGONAL/RANGE
    print(f"wrote {os.path.relpath(OUT, REPO)}")
    print(f"wrote {os.path.relpath(OUT.replace('.csv', '_robust_core.csv'), REPO)}")


if __name__ == "__main__":
    main()
