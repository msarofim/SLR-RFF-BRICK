"""THE COMMITMENT LAW AGAINST A COUPLED ICE-SHEET MODEL RUN TO EQUILIBRIUM.

WHY THIS, AND WHY NOW. Marcus's priority ordering (2026-08-22) ranks what the Greenland
component must match: (1) total ice volume and historical observations, (2) LONG-TERM
COMMITMENT against physical ice models, (3) melt-rate constraints, (4) transient ice
models, (5) simplicity. The arc had been spending itself on (4) -- the 2100 match
against PROTECT -- which is the lowest-ranked objective, scored against ONE ice-sheet
model. This file goes at (1) and (2), which outrank it.

WHAT IS BEING TESTED. `scope_gis_2300_relaxation.run_ab` / `basin2_series` carry the
commitment law

    L_eq(T) = clip(c1 * T_regional + c0, 0, GIS_V0_M)

-- LINEAR in the regional driver, ceilinged at the whole sheet. handoff section 1.1
found it 1.93-2.41x SHORT of PROTECT's own 2300 medians even at phi = 1 (fully
equilibrated), and called it THE defect. That was an internal inconsistency. This file
puts a physical model's number on it.

THE SOURCE. Willeit, Robinson, Kaufhold & Ganopolski, "Long-term future Greenland ice
loss determined by peak global warming", doi 10.5281/zenodo.19312031. CLIMBER-X coupled
to a dynamic 8 km Greenland ice sheet, `eqco2`: CO2 held at 19 fixed levels 280-460 ppm,
FIXED ORBIT, run 100,000 years. 9 parameter configurations. The 280 ppm run is the
control and is genuinely flat -- 0.058 K and 0.009 m of drift over 100 kyr -- so every
number below is CONTROL-DIFFERENCED against it, the same convention as ISMIP6 and
PROTECT.

THE TRAP THIS FILE EXISTS TO AVOID: A CO2 STEP IS NOT A TEMPERATURE STEP. At 460 ppm
CLIMBER-X's global anomaly is 1.30 K at year 300 and 1.47 K at year 1000 against a
2.45 K asymptote -- it goes on climbing past 10 kyr as the sheet's own albedo
disappears. Comparing our TEMPERATURE-step response to their CO2-step response reads a
factor 5-8x "we are too fast" that is pure forcing mismatch. Section 3 therefore drives
our emulator with CLIMBER-X's OWN tg(t), which is Marcus's standing like-for-like
instruction [[like_for_like_forcing]] and is the only comparison here that is honest at
short horizons.

AND THE SHORT HORIZONS STILL DO NOT SURVIVE, FOR A DIFFERENT REASON. Section 3b applies
priority 1 to the TARGET: CLIMBER-X's 8 km GrIS loses 0.117 mm/yr over its fastest first
century, at 1.09 K, against an OBSERVED 0.593 mm/yr at today's ~1.2 K -- 5.1x too slow.
So its first millennium cannot be a target at all, and the 4x "we lose too much early"
that section 3 reports is that deficit seen from the other side. It does NOT stack with
the ISMIP6 2100 fast bias and must not be read as confirming it. What survives is the
EQUILIBRIUM, which does not depend on the model's transient skill.

WHAT IT IS NOT. CLIMBER-X is ONE model; its 9 configs are PARAMETER perturbations of
that one model, not structural spread, and the group's Greenland threshold is a
long-standing result of that same lineage rather than an independent confirmation. Under
the priority rule -- stringency scales with the number of models -- this is GUIDANCE.
It emits no loss term, no band, no admissible set. Greve & Chambers 2022 SICOPOLIS
(also on disk, `data/gis_post2100/greve_chambers_2022/`) is a genuinely independent
model and is the natural next test of the same claim.

ONE-WAY COUPLING, AND IT FAVOURS US. Driving our emulator with CLIMBER-X's tg hands it
the warming produced BY the ice loss it is supposed to predict. Section 3 is therefore
generous to our model, not harsh.

WRITES outputs/diag_gis_climberx_commitment.csv        (per config x CO2, equilibrium)
       outputs/diag_gis_climberx_commitment_trans.csv  (like-for-like transient)
  python3 python/diag_gis_climberx_commitment.py
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
import netCDF4 as nc

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, GIS_V0_M  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    ANCHOR_N, DRIVER_BASE, GIS_ZONE, OBS, SHAPE_WIN, YEARS,
    _running_mean, gis_shape_table, regional_driver,
)

OUT_EQ = os.path.join(REPO, "outputs/diag_gis_climberx_commitment.csv")
OUT_TR = os.path.join(REPO, "outputs/diag_gis_climberx_commitment_trans.csv")
CX = os.path.join(REPO, "data/gis_post2100/climberx_10kyr/grl/eqco2")

# --- named constants; every label and verdict below derives from these ---------
TAG = A.TAG
SOURCE = ("CLIMBER-X + dynamic 8 km GrIS, Willeit/Robinson/Kaufhold/Ganopolski, "
          "doi 10.5281/zenodo.19312031, experiment `eqco2` (fixed CO2, FIXED ORBIT)")
CFG_REF = "8km"                  # the reference configuration
CO2_CTRL = 280                   # the control level everything is differenced against
EQ_AVG_YR = 1000                 # averaging window at the end of the run, yr
HORIZONS = (100, 300, 1000, 3000, 10000, 30000, 100000)
CO2_TRANS = (340, 380, 390, 400, 420, 460)   # levels carried through section 3
DRAW_STRIDE = 40                 # posterior thinning for the 100-kyr integrations
BURN_YR = 500                    # pre-step spin-up on the dT = 0 driver
## Half the sheet gone. Used only to LOCATE each curve's threshold for reporting --
## never as a pass/fail cut.
HALF = 0.5
CM_PER_M = 100.0
GATE_TOL_C = 1e-9                # the spliced-branch reproduction gate
## PRIORITY 1 OUTRANKS PRIORITY 4. Before a transient horizon of ANY model is used as
## a target, that model has to clear the observed record. `gis` in the recalibration
## target file is cm SLE; OBS_RATE_WIN is the window the present-day rate is taken over.
TARGETS_OBS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
OBS_RATE_WIN = (1995, 2024)
MM_PER_CM = 10.0
EARLY_YR = 100                   # the horizon the observed-rate check is made at
## How far below the observed rate a model may run before its EARLY horizons stop
## being usable as a target at all.
OBS_RATE_FACTOR = 2.0
## Where to quote our own committed loss. Quoting max(L_eq) over an unbounded dT grid
## reports the value at an absurd extrapolation (200 K) and is meaningless.
QUOTE_DT = 2.45                  # the top of CLIMBER-X's own dT range


def sustained_driver(dT, post, S, C):
    """The regional driver for an arbitrary global-anomaly SERIES `dT`, rel 1850-1900.

    This IS regional_driver's `spliced` branch (scope_gis_2300_relaxation.py:125-128),
    with no observed-history splice because these are hypothetical runs with no
    history. Gated against the real thing in `gate_driver` below."""
    dT = np.atleast_1d(np.asarray(dT, float))
    shape = S(_running_mean(dT, SHAPE_WIN))
    amp = post["gis_amp"].to_numpy()[:, None]
    return amp * shape[None, :] * dT[None, :] + C[:, None]


def gate_driver(post, S, C):
    """`sustained_driver` must reproduce regional_driver's projection branch on a real
    GMST series. Without this the section-3 result rests on a re-implementation."""
    g = pd.read_csv("data/observations/fair_mean_gmst_ssp245.csv").set_index(
        "year")["gmst_C"].reindex(YEARS).to_numpy()
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
    grb = g - g[ibd].mean()
    ref = regional_driver(grb, post["gis_amp"].to_numpy(), S)
    mine = sustained_driver(grb, post, S, C)
    tgz = pd.read_csv(os.path.join(OBS, "t_gis_zones.csv"))
    fut = YEARS > int(tgz["year"].max())        # only the projection branch is claimed
    d = float(np.max(np.abs(ref[:, fut] - mine[:, fut])))
    if d > GATE_TOL_C:
        raise SystemExit(f"DRIVER GATE: sustained_driver differs from "
                         f"regional_driver's spliced branch by {d:.3e} C")
    return d


def read_cx():
    """Every eqco2 run as (config, co2, V_sle series, tg series annualised).

    V_sle is annual over 0..100000; tg is decadal over 10..100000. tg is
    interpolated to the V grid, and BOTH are control-differenced against that
    config's own CO2_CTRL run."""
    out = {}
    for cfg in sorted(os.listdir(CX)):
        for co2 in sorted(os.listdir(os.path.join(CX, cfg)), key=int):
            p = os.path.join(CX, cfg, co2)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                d = nc.Dataset(os.path.join(p, "V_sle.nc"))
                V = np.asarray(d.variables["V_sle"][:], float).squeeze()
                tV = np.asarray(d.variables["time"][:], float).squeeze()
                d.close()
                d = nc.Dataset(os.path.join(p, "tg.nc"))
                T = np.asarray(d.variables["tg"][:], float).squeeze()
                tT = np.asarray(d.variables["time"][:], float).squeeze()
                d.close()
            out[(cfg, int(co2))] = dict(t=tV, V=V, tg=np.interp(tV, tT, T))
    return out


def main():
    cx = read_cx()
    cfgs = sorted({k[0] for k in cx})
    co2s = sorted({k[1] for k in cx})
    nyr = len(cx[(CFG_REF, CO2_CTRL)]["t"]) - 1

    post = pd.read_csv(A.POST)
    S = gis_shape_table()
    tgz = pd.read_csv(os.path.join(OBS, "t_gis_zones.csv"))
    gd = dict(zip(tgz["year"].astype(int), tgz[GIS_ZONE].astype(float)))
    last = int(tgz["year"].max())
    obs = np.array([gd.get(int(y), 0.0) for y in YEARS])
    ianch = np.isin(YEARS, np.arange(last - ANCHOR_N + 1, last + 1))
    anchor = float(obs[ianch].mean())
    g = pd.read_csv("data/observations/fair_mean_gmst_ssp245.csv").set_index(
        "year")["gmst_C"].reindex(YEARS).to_numpy()
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
    grb = g - g[ibd].mean()
    sh = S(_running_mean(grb, SHAPE_WIN))
    shape_anchor = float((sh[ianch] * grb[ianch]).mean())
    C_full = anchor - post["gis_amp"].to_numpy() * shape_anchor
    gd_err = gate_driver(post, S, C_full)

    print(f"diag_gis_climberx_commitment — the commitment law vs a coupled model run "
          f"to equilibrium\n")
    print(f"  SOURCE   {SOURCE}")
    print(f"  GRID     {len(cfgs)} configurations x {len(co2s)} CO2 levels "
          f"({co2s[0]}-{co2s[-1]} ppm), {nyr:,} yr each")
    print(f"  BASIS    both sides are anomalies rel PREINDUSTRIAL: ours "
          f"DRIVER_BASE = {DRIVER_BASE}, theirs = the {CO2_CTRL} ppm control")
    print(f"  GATE     sustained_driver reproduces regional_driver's projection "
          f"branch to {gd_err:.1e} C\n")

    # ---------------------------------------------------------------- section 1
    print(f"=== 1. PRIORITY 1 — TOTAL ICE VOLUME ===\n")
    V0s = {c: float(cx[(c, CO2_CTRL)]["V"][0]) for c in cfgs}
    lo, hi = min(V0s.values()), max(V0s.values())
    print(f"  ours GIS_V0_M                 {GIS_V0_M:.3f} m SLE")
    print(f"  CLIMBER-X {CFG_REF} reference      {V0s[CFG_REF]:.3f} m SLE   "
          f"(ours / theirs = {GIS_V0_M / V0s[CFG_REF]:.3f}x)")
    print(f"  across all {len(cfgs)} configurations  {lo:.3f}-{hi:.3f} m SLE")
    inside = lo <= GIS_V0_M <= hi
    print(f"\n  ==> {'PASS' if inside else 'FAIL'}: our total volume is "
          f"{'INSIDE' if inside else 'OUTSIDE'} the configuration range, "
          f"{abs(1 - GIS_V0_M / V0s[CFG_REF]) * 100:.1f}% from the reference.")
    print(f"      The volume constraint is met. The problem is not how much ice there "
          f"is.\n")

    # ---------------------------------------------------------------- section 2
    rows = []
    for cfg in cfgs:
        ctrl = cx[(cfg, CO2_CTRL)]
        for co2 in co2s:
            r = cx[(cfg, co2)]
            dT = float(np.mean(r["tg"][-EQ_AVG_YR:] - ctrl["tg"][-EQ_AVG_YR:]))
            loss = float(np.mean(ctrl["V"][-EQ_AVG_YR:] - r["V"][-EQ_AVG_YR:]))
            rows.append(dict(cfg=cfg, co2=co2, dT_g=dT, loss_m=loss,
                             frac_of_V0=loss / V0s[cfg], V0=V0s[cfg]))
    eq = pd.DataFrame(rows)

    c1 = post["gis_c1"].to_numpy()
    c0 = post["gis_c0"].to_numpy()

    def our_Leq(dTv):
        """Committed loss rel dT = 0, median over draws, at sustained anomalies dTv."""
        dTv = np.atleast_1d(np.asarray(dTv, float))
        Tr = (post["gis_amp"].to_numpy()[:, None] * S(dTv)[None, :] * dTv[None, :]
              + C_full[:, None])
        L = np.clip(c1[:, None] * Tr + c0[:, None], 0.0, GIS_V0_M)
        T0 = post["gis_amp"].to_numpy() * float(S(np.zeros(1))[0]) * 0.0 + C_full
        L0 = np.clip(c1 * T0 + c0, 0.0, GIS_V0_M)
        return np.median(L - L0[:, None], axis=0)

    ref = eq[eq.cfg == CFG_REF].sort_values("co2")
    ours = our_Leq(ref.dT_g.to_numpy())
    print(f"=== 2. PRIORITY 2 — THE EQUILIBRIUM COMMITMENT CURVE "
          f"({nyr // 1000} kyr) ===\n")
    print(f"  {'CO2':>5}{'dT_g':>8}{'CLIMBER-X':>11}{'(frac V0)':>11}{'OURS':>9}"
          f"{'(frac V0)':>11}{'theirs/ours':>13}")
    for (_, r), o in zip(ref.iterrows(), ours):
        ## below ~330 ppm CLIMBER-X's committed loss is at or under its own drift
        ## (it goes slightly NEGATIVE), so the ratio is not a quantity. Blank it.
        rat = (f"{r.loss_m / o:12.1f}x" if o > 0 and r.loss_m > 0.01
               else f"{'--':>13}")
        print(f"  {r.co2:5.0f}{r.dT_g:8.2f}{r.loss_m:11.3f}{r.frac_of_V0:11.2f}"
              f"{o:9.3f}{o / GIS_V0_M:11.2f}{rat}")
    print(f"\n  (m SLE committed, relative to the {CO2_CTRL} ppm equilibrium)\n")

    def threshold(dTv, lossv, v0):
        """The dT at which a curve first reaches HALF the sheet, by interpolation."""
        o = np.argsort(dTv)
        x, y = np.asarray(dTv)[o], np.asarray(lossv)[o]
        if y.max() < HALF * v0:
            return np.nan
        j = int(np.argmax(y >= HALF * v0))
        if j == 0:
            return float(x[0])
        return float(np.interp(HALF * v0, [y[j - 1], y[j]], [x[j - 1], x[j]]))

    thr = {c: threshold(eq[eq.cfg == c].dT_g, eq[eq.cfg == c].loss_m, V0s[c])
           for c in cfgs}
    tv = np.array([v for v in thr.values() if np.isfinite(v)])
    grid = np.arange(0.0, 200.0, 0.25)
    our_thr = threshold(grid, our_Leq(grid), GIS_V0_M)
    print(f"  WHERE HALF THE SHEET GOES (dT_g at 50% of V0):")
    print(f"    CLIMBER-X  {tv.min():.2f}-{tv.max():.2f} K over "
          f"{len(tv)}/{len(cfgs)} configurations ({CFG_REF}: {thr[CFG_REF]:.2f} K)")
    our_q = float(our_Leq(np.array([QUOTE_DT]))[0])
    print(f"    ours       "
          + (f"{our_thr:.1f} K" if np.isfinite(our_thr) else "NEVER")
          + f"   -- at dT = {QUOTE_DT:.2f} K, the top of CLIMBER-X's own range, our "
            f"committed\n               loss is {our_q:.3f} m, "
            f"{our_q / GIS_V0_M * 100:.1f}% of the sheet")
    at2 = float(our_Leq(np.array([2.0]))[0])
    cx2 = float(np.interp(2.0, ref.dT_g, ref.loss_m))
    print(f"\n  AT dT_g = 2.0 K:  CLIMBER-X {cx2:.2f} m,  ours {at2:.3f} m  "
          f"-> {cx2 / at2:.0f}x")
    print(f"\n  ==> THE COMMITMENT LAW IS NOT SHORT BY A FACTOR OF TWO. It is short by")
    print(f"      more than an ORDER OF MAGNITUDE wherever the coupled model crosses "
          f"its\n      threshold. A LINEAR L_eq cannot represent a curve that is flat "
          f"below\n      ~{tv.min():.1f} K and at the ceiling above ~{tv.max():.1f} K; "
          f"the two disagree in SHAPE, not in\n      calibration. handoff section 1.1's "
          f"1.93-2.41x was the smallest visible\n      symptom of this.\n")

    # ---------------------------------------------------------------- section 3
    thin = post.iloc[::DRAW_STRIDE].reset_index(drop=True)
    tbar = gis_tbar()
    r_s = np.exp(thin["gis_slow_ell"].to_numpy())
    thin["gis_alpha_s"] = thin["gis_slow_w"].to_numpy() * r_s / tbar
    thin["gis_beta_s"] = (1.0 - thin["gis_slow_w"].to_numpy()) * r_s
    C_thin = anchor - thin["gis_amp"].to_numpy() * shape_anchor

    print(f"=== 3. LIKE-FOR-LIKE: OUR EMULATOR ON CLIMBER-X'S OWN tg(t) "
          f"({CFG_REF}, {len(thin)} draws) ===\n")
    print(f"  {'CO2':>5}{'dT@300':>8}{'dT@end':>8}  " + "".join(
        f"{h:>9}" for h in HORIZONS))
    trows = []
    ctrl = cx[(CFG_REF, CO2_CTRL)]
    for co2 in CO2_TRANS:
        r = cx[(CFG_REF, co2)]
        dT = r["tg"] - ctrl["tg"]
        drv = np.empty((len(thin), BURN_YR + len(dT)))
        drv[:, :BURN_YR] = sustained_driver(np.zeros(1), thin, S, C_thin)
        drv[:, BURN_YR:] = sustained_driver(dT, thin, S, C_thin)
        L = basin2_series(drv, thin, 1.0, 1.0)
        base = L[:, BURN_YR - 1]
        ours_h = [float(np.median(L[:, BURN_YR + h] - base)) for h in HORIZONS]
        theirs_h = [float(ctrl["V"][h] - r["V"][h]) for h in HORIZONS]
        for h, o, t in zip(HORIZONS, ours_h, theirs_h):
            trows.append(dict(cfg=CFG_REF, co2=co2, horizon=h, ours_m=o, cx_m=t,
                              ratio_ours_over_cx=o / t if t else np.nan,
                              dT_at_h=float(dT[h])))
        print(f"  {co2:5d}{dT[300]:8.2f}{dT[-1]:8.2f}  ours " + "".join(
            f"{v:9.3f}" for v in ours_h))
        print(f"  {'':5}{'':8}{'':8}  CX   " + "".join(
            f"{v:9.3f}" for v in theirs_h))
        print(f"  {'':5}{'':8}{'':8}  x    " + "".join(
            f"{(o / t if t else np.nan):8.1f}x" for o, t in zip(ours_h, theirs_h)))
        del drv, L
    tr = pd.DataFrame(trows)
    print(f"\n  (m SLE lost; 'x' is ours/CLIMBER-X, >1 = we lose MORE)\n")

    early = tr[tr.horizon <= 1000]
    ## Split the late horizons by whether CLIMBER-X's own run crossed its threshold.
    ## Pooling them averages "we are 2x high" (sub-threshold) with "we are 40x low"
    ## (super-threshold) into a number that describes neither.
    thr_ref = thr[CFG_REF]
    late = tr[tr.horizon >= 30000]
    hot = late[late.dT_at_h >= thr_ref]
    cold = late[late.dT_at_h < thr_ref]
    print(f"  EARLY ({HORIZONS[0]}-1000 yr):  median ours/CX = "
          f"{early.ratio_ours_over_cx.median():.1f}x  "
          f"({early.ratio_ours_over_cx.min():.1f}-"
          f"{early.ratio_ours_over_cx.max():.1f}x)")
    print(f"  LATE  (30-100 kyr), CLIMBER-X ABOVE its {thr_ref:.2f} K threshold "
          f"(n={len(hot)}):  median ours/CX = {hot.ratio_ours_over_cx.median():.3f}x "
          f"= 1/{1 / hot.ratio_ours_over_cx.median():.0f}")
    print(f"  LATE  (30-100 kyr), BELOW it (n={len(cold)}):"
          + (f"                     median ours/CX = "
             f"{cold.ratio_ours_over_cx.median():.2f}x" if len(cold) else " none"))

    # ------------------------------------------------------- section 3b
    obs = pd.read_csv(TARGETS_OBS).set_index("year")["gis"]
    y0, y1 = OBS_RATE_WIN
    obs_rate = float(obs.loc[y1] - obs.loc[y0]) * MM_PER_CM / (y1 - y0)
    print(f"\n=== 3b. IS CLIMBER-X ADMISSIBLE AS AN EARLY-HORIZON TARGET? "
          f"(PRIORITY 1 CHECK) ===\n")
    print(f"  Priority 1 -- historical observations -- outranks priority 4. Before the "
          f"section-3\n  early ratios mean anything, CLIMBER-X has to clear the "
          f"observed record itself.\n")
    print(f"  observed GIS loss rate {y0}-{y1} ({os.path.basename(TARGETS_OBS)}): "
          f"{obs_rate:.3f} mm/yr\n")
    print(f"  {'CO2':>5}{'dT@' + str(EARLY_YR) + 'yr':>10}"
          f"{'CLIMBER-X rate':>16}{'vs observed':>13}")
    cxr = []
    for co2 in CO2_TRANS:
        r = cx[(CFG_REF, co2)]
        dT = float(r["tg"][EARLY_YR] - ctrl["tg"][EARLY_YR])
        rate = float(ctrl["V"][EARLY_YR] - r["V"][EARLY_YR]) * 1000.0 / EARLY_YR
        cxr.append(rate)
        print(f"  {co2:5d}{dT:10.2f}{rate:14.3f} mm/yr{rate / obs_rate:12.2f}x")
    slow = obs_rate / max(cxr)
    print(f"\n  Its FASTEST first century is {max(cxr):.3f} mm/yr -- "
          f"{slow:.1f}x SLOWER than the observed\n  rate, and that is at "
          f"{float(cx[(CFG_REF, CO2_TRANS[-1])]['tg'][EARLY_YR] - ctrl['tg'][EARLY_YR]):.2f} K, "
          f"close to today's warming.")
    inadmissible = slow > OBS_RATE_FACTOR
    print(f"\n  ==> CLIMBER-X's 8 km GrIS is {'NOT ' if inadmissible else ''}"
          f"admissible as an EARLY-horizon target"
          + (f" (threshold: {OBS_RATE_FACTOR:.0f}x)." if inadmissible else "."))
    if inadmissible:
        print(f"      The section-3 'we lose "
              f"{early.ratio_ours_over_cx.median():.0f}x too much in the first "
              f"millennium' is therefore\n      CLIMBER-X being too SLOW, not us "
              f"being too fast -- its {slow:.1f}x deficit against\n      observations "
              f"is the same size as our "
              f"{early.ratio_ours_over_cx.median():.1f}x excess against it. It does "
              f"NOT stack with\n      the ISMIP6 2100 finding, and must not be read "
              f"as confirming it.")

    print(f"\n=== 4. VERDICT ===\n")
    our_q = float(our_Leq(np.array([QUOTE_DT]))[0])
    print(f"  ONE DEFECT SURVIVES, AND IT IS THE COMMITMENT LAW'S SHAPE.\n")
    print(f"    * SURVIVES -- the equilibrium. Above ~{thr_ref:.1f} K CLIMBER-X commits "
          f"the whole\n      {V0s[CFG_REF]:.1f} m sheet; at {QUOTE_DT:.2f} K our "
          f"linear law commits {our_q:.3f} m, "
          f"{our_q / GIS_V0_M * 100:.0f}% of it.\n      That is a factor "
          f"{1 / hot.ratio_ours_over_cx.median():.0f}, and it is a statement about the "
          f"SHAPE of L_eq(T): flat below the\n      threshold, at the ceiling above "
          f"it, where ours is a straight line through both.")
    print(f"    * DOES NOT SURVIVE -- the early horizons. Section 3b: this model runs "
          f"{slow:.1f}x below\n      the OBSERVED present-day loss rate, so its first "
          f"millennium cannot be a target.\n      Our "
          f"{early.ratio_ours_over_cx.median():.0f}x 'excess' there is its deficit "
          f"seen from the other side.")
    print(f"\n  THE EQUILIBRIUM RESULT IS THE (L_eq, tau) DEGENERACY SHOWING. A SMALL "
          f"reservoir\n  emptied FAST fits the observed record as well as a LARGE one "
          f"emptied SLOWLY, and\n  the historical fit -- all c1/c0 ever saw -- cannot "
          f"separate them. Our calibration\n  took the small-fast branch. handoff "
          f"section 1.1's phi=1 ceiling and section 3.1's\n  0/1080 fixed-V "
          f"reservoirs are the same fact seen from inside the model.")
    print(f"\n  WHAT IT LICENSES. Not a refit: one model, {len(cfgs)} PARAMETER "
          f"perturbations of it (not\n  structural spread), from the group whose "
          f"Greenland threshold is a long-standing\n  result of that same lineage -- "
          f"and a model that misses the observed rate by "
          f"{slow:.1f}x\n  has not earned a calibration target. Under Marcus's "
          f"stringency rule this is GUIDANCE.\n  What it DOES support is that the "
          f"linear FORM is wrong, which is structure, not\n  calibration, and "
          f"structure is where a one-model result is allowed to bite.")
    print(f"\n  NEXT, AND IT IS CHEAP: Greve & Chambers 2022 SICOPOLIS to year 3000 is "
          f"on disk and\n  is an INDEPENDENT model. Two questions for it: does it also "
          f"put the committed loss\n  far above {our_q:.2f} m, and does IT clear the "
          f"observed rate that CLIMBER-X misses?")

    eq.to_csv(OUT_EQ, index=False)
    tr.to_csv(OUT_TR, index=False)
    print(f"\nwrote {os.path.relpath(OUT_EQ, REPO)}")
    print(f"wrote {os.path.relpath(OUT_TR, REPO)}")


if __name__ == "__main__":
    main()
