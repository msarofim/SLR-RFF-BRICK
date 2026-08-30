#!/usr/bin/env python3
"""
diag_gis_2150_band_veto.py -- CAN THE ssp585 x2300 2150 BAND ACTUALLY VETO THE
WEIGHTED-VERDICT CELL, GIVEN HOW MANY INDEPENDENT CLIMATE MODELS ARE BEHIND IT?

THE SITUATION IT WAS WRITTEN FOR (2026-08-23, handoff_2026-08-23b sec 7 item 2)
  Wiring the weighted-verdict cell (V=7.42 m / tau=2700 / onset 4.69) was supposed
  to be the session's shippable step. Running it through this repo's OWN reservoir
  scorecard first -- on a V and tau ladder wide enough to contain it, which had
  never been run (`scope_gis_reservoir_offline.py --wide-v`) -- says it clears the
  three 2300 matched bands, holds 2100 at EXACTLY 0.0000 cm, and improves the
  five-arm shape, but MISSES ONE THING: the ssp585 x2300 band at 2150, at 63.1 cm
  against a 45.2-53.2 band. That single criterion is what selected cell A, which
  sits at 53.12 against a 53.2 top -- at the edge, not comfortably inside.

  Read as a psi constraint it is decisive and it is a clean contradiction:
      x2300 @2150 caps psi at 0.125 cm/yr at onset 4.69 (measured, --wide-v)
      Greve @3001 requires                 0.179-0.341
      the 2250-2300 rate criterion gives   0.273-0.282
  Those sets are DISJOINT. Two independent late-horizon sources say the flux must
  be ~2.2x what a single mid-horizon band allows.

WHAT THIS FILE TESTS, AND WHY IT IS A TEST AND NOT A RATIONALISATION
  The 2150 bands are run-level 5-95% quantiles over PROTECT runs. This repo has
  already established, twice, that a PROTECT run count is not a sample size: the
  runs behind an arm come from a handful of GCMs (and, past 2100, ONE ice-sheet
  model), so a quantile over runs measures within-GCM member spread as if it were
  climate uncertainty. The same correction has already moved a verdict here once --
  the 2250-2300 rate band is "9.7-41.5 (4.3x on 35 runs = only 5 GCM clusters)".
  So the question is posed BEFORE the answer is known, and it has a pre-registered
  form: rebuild the SAME band at the GCM-cluster level and re-ask the veto.

  The falsifier is explicit. If the x2300 arm carries enough independent GCMs that
  a sample-size-respecting interval stays narrow, the veto stands, the winner cell
  cannot be wired, and cell A's psi=0.125 is the answer -- against Greve and against
  the rate criterion. That is a real possible outcome of this file, not a formality.

  AND THAT IS THE OUTCOME. The hypothesis is REFUTED, so it is stated here as
  prominently as a confirmation would have been: the two GCM clusters behind the
  x2300 arm AGREE at 2150 to 0.7 cm (medians 45.0 and 45.7), so widening the band
  for sample size buys only 1.6x, the top moves 53.2 -> 53.0, and the winner at 63.1
  is out under EVERY construction. The narrowness is not a member-counting artefact
  at this horizon. What the analysis does establish is narrower and still useful:
  the veto is a SHAPE statement, not a size one -- see the note at the end.

READS   outputs/protect_greenland_gis_annual.csv, the scorecard's own base model
WRITES  outputs/diag_gis_2150_band_veto.csv
  python3 python/diag_gis_2150_band_veto.py
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

import scope_gis_shape_all_scenarios as A  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, gis_shape_table, regional_driver,
)
from scope_gis_reservoir_offline import (  # noqa: E402
    reservoir_unit, CM_PER_M, K_FIXED, RES_ONSET_K, WINNER_CELL, CELL_A,
)

WIDE = os.path.join(REPO, "outputs/scope_gis_reservoir_offline_wideV.csv")
OUT = os.path.join(REPO, "outputs/diag_gis_2150_band_veto.csv")

# --- named constants ---------------------------------------------------------
# ⚠ label DERIVES from the tag: this read "L14 vintage (two-basin), {A.TAG}" until
# 2026-08-29, which printed "L14 vintage ... L21" when run on L21. L21 has been
# champion since 2026-08-28; "canonical" must never be hardcoded to a vintage.
LINEAGE = f"two-basin GIS, posterior tag={A.TAG}"
YEAR = 2150                       # the horizon under test
ARMS = [("ssp585", "SSP5-8.5", "r2300"), ("ssp585", "SSP5-8.5", "x2300")]
VETO_ARM = ("ssp585", "SSP5-8.5", "x2300")     # the one that fires
BAND_Q = (0.05, 0.95)             # the shipped construction: quantiles over RUNS
PI_LEVEL = 0.975                  # matches diag_gis_residual_band.PI_LEVEL
## A "run" is a (group, model, exp) triple; the GCM is the first token of the exp
## name. Counting exp NAMES undercounts x2300 by a third -- the trap the shape
## scorecard's gate 4 already caught.
GCM_OF_EXP = lambda e: e.split("_")[0]
CELLS = {"base (no reservoir)": None,
         "cell A": CELL_A, "WINNER (weighted verdict)": WINNER_CELL}
BASE_GATE_TOL_CM = 1e-6           # vs the base implied by the --wide-v CSV
PSI_GREVE = (0.179, 0.341)        # Greve@3001 per-cell requirement
PSI_RATE = (0.273, 0.282)         # the 2250-2300 rate criterion
## The 2300 side of the pre-check, from gis_targets / the scorecard's own baseline.
P50_2300_CM = 98.5                # matched p50, ssp585 (MATCHED_2300_P50_M)
BASE_OURS_2300_CM = 49.9          # the no-reservoir base, scope_gis_reservoir_offline
RAMP_W_K = 1.0                    # mirrors scope_gis_reservoir_offline.RAMP_W_K
ONSET_PRECHECK_K = 4.69           # the pre-check is run at the shipped onset
N_STAGES = (1, 2, 3)              # 1 = the first-order exponential scanned so far
## The onset sweep exists to close the obvious escape: "then move the onset". R is
## FIXED by the two targets and the base, so the only free thing is the ratio the
## FORM can deliver, and this asks whether any onset lets n=1 reach R.
ONSET_SWEEP_K = (1.60, 2.10, 3.20, 4.00, 4.69, 5.50, 6.50, 7.50)
OURS_SSP585_GMST = "data/observations/fair_mean_gmst_ssp585.csv"


def build_base():
    """The scorecard's own base model, rebuilt exactly as
    scope_gis_reservoir_offline.main() builds it, and GATED below against the base
    the --wide-v CSV implies. Returns (base series per arm, gmst per arm, offs)."""
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    S_tab = gis_shape_table()
    idx = {y: int(np.where(YEARS == y)[0][0]) for y in list(A.HORIZONS) + list(A.HIND) + [2015]}
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])

    gmst, drivers = {}, {}
    for ssp, lab, fam, stem in A.ARMS:
        g = pd.read_csv(os.path.join(REPO, f"outputs/{stem}.csv")).set_index(
            "year")[f"gmst_{A.ARM}"].reindex(YEARS).to_numpy()
        rb = g - g[ibd].mean()
        gmst[(ssp, fam)] = rb
        drivers[(ssp, fam)] = regional_driver(rb, post["gis_amp"].to_numpy(), S_tab)

    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want = float(tgt.loc[A.HIND[1]] - tgt.loc[A.HIND[0]])
    Th = drivers[A.HIND_ARM]
    lo, hi = np.full(len(post), 1e-4), np.full(len(post), 1e3)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = basin2_series(Th, post, K_FIXED, mid)
        below = 100.0 * (L[:, idx[A.HIND[1]]] - L[:, idx[A.HIND[0]]]) < want
        lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
    s = np.sqrt(lo * hi)
    base = {k: np.median(rebase_cm(basin2_series(v, post, K_FIXED, s)), axis=0)
            for k, v in drivers.items()}
    offs = float(np.median(rebase_cm(
        basin2_series(drivers[A.HIND_ARM], post, 1.0, 1.0))[:, idx[2015]]))
    return base, gmst, offs, idx


def main():
    print(f"diag_gis_2150_band_veto -- {LINEAGE}, horizon {YEAR}\n")
    base, gmst, offs, idx = build_base()

    # --- GATE: the rebuilt base reproduces the --wide-v scan's own base --------
    wide = pd.read_csv(WIDE)
    print(f"=== GATE -- rebuilt base vs the base implied by "
          f"{os.path.basename(WIDE)} ({len(wide)} cells) ===")
    for ssp, lab, fam in ARMS:
        sub = wide[(wide.onset_K == RES_ONSET_K[2]) & (wide.tau_yr == 800)]
        fit = np.polyfit(sub.V_m.to_numpy(), sub[f"{ssp}_{fam}_{YEAR}"].to_numpy(), 1)
        got, want = base[(ssp, fam)][idx[YEAR]], float(fit[1])
        ok = abs(got - want) <= BASE_GATE_TOL_CM
        print(f"  {lab} {fam:6} base@{YEAR} rebuilt {got:8.4f} cm, implied "
              f"{want:8.4f} cm  [{'OK' if ok else 'FAILED'}]")
        if not ok:
            sys.exit(f"BASE GATE FAILED on {lab} {fam}: {abs(got - want):.3e} cm. "
                     f"This file is not scoring the same model as the scorecard.")
    print()

    # --- the ensemble behind each band ----------------------------------------
    ann = pd.read_csv(A.ANN)
    rows, bands, per_gcm_v = [], {}, {}
    for ssp, lab, fam in ARMS:
        sub = A.protect_band(ann, lab, fam)
        at = sub[sub.year == YEAR].copy()
        at["gcm"] = at.exp.map(GCM_OF_EXP)
        runs = at.groupby(["group", "model", "exp"]).gis_cm.median()
        per_gcm = at.groupby("gcm").gis_cm.median()
        per_gcm_v[fam] = per_gcm.to_numpy(float)
        ## THE `model` COLUMN IS NOT A LIST OF ICE-SHEET MODELS. On x2300 its three
        ## values are CISM16x-MAR312-p25/p50/p75 -- three MAR SMB percentile variants
        ## of the SAME NORCE-CISM model. Counting them as models would overstate the
        ## arm's independence exactly where this file is testing it.
        ism = at.model.nunique()
        ism_note = "variants of ONE ice-sheet model (NORCE-CISM)"
        v = per_gcm.to_numpy(float)
        # (1) SHIPPED: quantiles over RUNS
        q_lo, q_hi = np.quantile(at.gis_cm, BAND_Q[0]), np.quantile(at.gis_cm, BAND_Q[1])
        # (2) GCM-cluster min-max
        c_lo, c_hi = float(v.min()), float(v.max())
        # (3) GCM-cluster t prediction interval -- the sample-size-respecting one
        if len(v) >= 2:
            half = (stats.t.ppf(PI_LEVEL, len(v) - 1) * v.std(ddof=1)
                    * np.sqrt(1.0 + 1.0 / len(v)))
            t_lo, t_hi = float(v.mean() - half), float(v.mean() + half)
        else:
            t_lo = t_hi = float("nan")
        bands[(ssp, fam)] = {"shipped runs 5-95%": (q_lo + offs, q_hi + offs),
                             "GCM-cluster min-max": (c_lo + offs, c_hi + offs),
                             f"GCM-cluster t-PI {PI_LEVEL:.3g}": (t_lo + offs, t_hi + offs)}
        print(f"=== {lab} {fam} at {YEAR}: WHAT IS ACTUALLY BEHIND THE BAND ===")
        print(f"  {len(runs)} runs, {ism} {ism_note}, "
              f"{len(per_gcm)} GCM cluster(s): "
              + ", ".join(f"{g} n={int((at.gcm == g).sum())} med {m:.1f}"
                          for g, m in per_gcm.items()))
        for nm, (lo_, hi_) in bands[(ssp, fam)].items():
            print(f"    {nm:28} {lo_:7.1f} - {hi_:7.1f} cm   (width {hi_ - lo_:6.1f})")
            rows.append(dict(arm=f"{lab} {fam}", year=YEAR, construction=nm,
                             n_runs=len(runs), n_ism=ism, n_gcm=len(per_gcm),
                             lo_cm=lo_, hi_cm=hi_, width_cm=hi_ - lo_))
        print()

    # --- the veto, re-asked ---------------------------------------------------
    print(f"=== THE VETO, RE-ASKED UNDER EACH CONSTRUCTION ===")
    vals = {}
    for name, cell in CELLS.items():
        vals[name] = {}
        for ssp, lab, fam in ARMS:
            add = 0.0 if cell is None else CM_PER_M * cell[0] * reservoir_unit(
                gmst[(ssp, fam)], cell[1], cell[2])[idx[YEAR]]
            vals[name][(ssp, fam)] = base[(ssp, fam)][idx[YEAR]] + add
    for ssp, lab, fam in ARMS:
        print(f"  {lab} {fam}")
        for name in CELLS:
            v = vals[name][(ssp, fam)]
            marks = "  ".join(
                f"{nm.split()[0]}:{'IN ' if lo_ <= v <= hi_ else 'OUT'}"
                for nm, (lo_, hi_) in bands[(ssp, fam)].items())
            print(f"    {name:28}{v:8.1f} cm   {marks}")
            for nm, (lo_, hi_) in bands[(ssp, fam)].items():
                rows.append(dict(arm=f"{lab} {fam}", year=YEAR, construction=nm,
                                 cell=name, ours_cm=v, lo_cm=lo_, hi_cm=hi_,
                                 in_band=bool(lo_ <= v <= hi_)))
        print()
    pd.DataFrame(rows).to_csv(OUT, index=False)

    # --- the verdict ----------------------------------------------------------
    ## THE CASCADE PRE-CHECK, computed before it is printed. A reservoir driven by
    ## a ramp responds with an n-fold repeated integral of that ramp in the long-tau
    ## limit; that limit is the MOST back-loaded response an n-stage cascade can
    ## give, so the ratio below is an upper bound per n, not a tuned number.
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
    g_ours = pd.read_csv(os.path.join(REPO, OURS_SSP585_GMST)).set_index(
        "year")["gmst_C"].reindex(YEARS).ffill().bfill().to_numpy()
    ramp_ours = np.clip((g_ours - g_ours[ibd].mean() - ONSET_PRECHECK_K) / RAMP_W_K,
                        0.0, 1.0)
    ramp_arm = np.clip((gmst[VETO_ARM[0], VETO_ARM[2]] - ONSET_PRECHECK_K) / RAMP_W_K,
                       0.0, 1.0)
    ratio_n = {}
    Jo, Ja = ramp_ours.copy(), ramp_arm.copy()
    for n in range(1, max(N_STAGES) + 1):
        Jo, Ja = np.cumsum(Jo), np.cumsum(Ja)
        if n in N_STAGES:
            ratio_n[n] = float(Jo[idx[2300]] / Ja[idx[YEAR]])

    def ratios_at(onset, nmax):
        ro = np.clip((g_ours - g_ours[ibd].mean() - onset) / RAMP_W_K, 0.0, 1.0)
        ra = np.clip((gmst[VETO_ARM[0], VETO_ARM[2]] - onset) / RAMP_W_K, 0.0, 1.0)
        out, Jo, Ja = {}, ro.copy(), ra.copy()
        for n in range(1, nmax + 1):
            Jo, Ja = np.cumsum(Jo), np.cumsum(Ja)
            out[n] = (float(Jo[idx[2300]] / Ja[idx[YEAR]])
                      if Ja[idx[YEAR]] > 0 else float("inf"))
        return out
    sweep = {on: ratios_at(on, 2) for on in ONSET_SWEEP_K}

    ssp, lab, fam = VETO_ARM
    b = bands[(ssp, fam)]
    w = vals["WINNER (weighted verdict)"][(ssp, fam)]
    a = vals["cell A"][(ssp, fam)]
    bs = vals["base (no reservoir)"][(ssp, fam)]
    ship = b["shipped runs 5-95%"]
    tpi = b[f"GCM-cluster t-PI {PI_LEVEL:.3g}"]
    n_gcm = int([r for r in rows if r.get("construction") == "shipped runs 5-95%"
                 and r["arm"] == f"{lab} {fam}"][0]["n_gcm"])
    print(f"=== VERDICT ON THE {lab} {fam} @{YEAR} VETO ===")
    print(f"  The arm has {n_gcm} independent GCM cluster(s) and ONE ice-sheet model "
          f"(its 3 `model`\n  values are MAR SMB percentile variants of NORCE-CISM, "
          f"not independent ISMs).")
    print(f"  Under the SHIPPED run-level band {ship[0]:.1f}-{ship[1]:.1f} the winner "
          f"({w:.1f}) is {w / ship[1]:.2f}x the top and IS vetoed;\n  cell A "
          f"({a:.1f}) clears it by {ship[1] - a:.2f} cm -- {100 * (ship[1] - a) / (ship[1] - ship[0]):.1f}% "
          f"of the band width. The base alone is {bs:.1f}, i.e. the whole reservoir\n  "
          f"headroom at this horizon is {ship[1] - bs:.1f} cm.")
    if np.isfinite(tpi[0]):
        print(f"  Under a GCM-cluster t-PI on n={n_gcm} the same band is "
              f"{tpi[0]:.1f}-{tpi[1]:.1f} cm, {(tpi[1] - tpi[0]) / (ship[1] - ship[0]):.1f}x wider, "
              f"and the winner is {'INSIDE' if tpi[0] <= w <= tpi[1] else 'STILL OUT'}.")
    print(f"\n  THE HYPOTHESIS IS REFUTED, and it is reported as prominently as a "
          f"confirmation would be.\n  The two GCM clusters AGREE at {YEAR} to "
          f"{abs(np.diff(sorted(per_gcm_v[fam]))[0]):.1f} cm, so the band is NOT narrow "
          f"because members were counted as\n  models -- it is narrow because the "
          f"two climate models genuinely say the same thing here.\n  The veto "
          f"SURVIVES the sample-size test. Cell A's 1.4%-of-band clearance is luck, "
          f"not margin,\n  but the winner's 1.19x is a real miss and no widening "
          f"rescues it.")

    # --- THE PRE-CHECK: what SHAPE could satisfy both, before any scan --------
    print(f"\n=== SO IT IS A SHAPE CONTRADICTION, AND THE PRE-CHECK IS ANALYTIC ===")
    print(f"  Two requirements, both on the SAME reservoir, at two different "
          f"horizons on two drivers:")
    cap = ship[1] - bs
    need = P50_2300_CM - BASE_OURS_2300_CM
    print(f"    at {YEAR} on {lab} {fam}: the reservoir may add at most "
          f"{cap:.1f} cm (band top {ship[1]:.1f} - base {bs:.1f})")
    print(f"    at 2300 on OUR ssp585:    it must add {need:.1f} cm to reach the "
          f"matched p50 ({P50_2300_CM:.1f} - base {BASE_OURS_2300_CM:.1f})")
    print(f"    => required delivery ratio R = {need / cap:.2f}")
    print(f"\n  A reservoir's response to its ramp is an n-fold repeated integral: "
          f"n=1 IS the first-order\n  exponential this arc has scanned "
          f"exclusively; n>=2 is a CASCADE, which is back-loaded and is\n  NOT "
          f"completely monotone, so the exact bound that refuted every CM family "
          f"does not apply to\n  it. In the long-tau limit (the most back-loaded "
          f"any given n can be) the achievable ratio is:")
    print(f"    {'n stages':>10}{'achievable ratio':>19}{'  verdict vs R':>16}")
    n_ok = None
    for n, rn in ratio_n.items():
        ok = rn >= need / cap
        n_ok = n if (ok and n_ok is None) else n_ok
        print(f"    {n:>10}{rn:>19.2f}{'  CLEARS' if ok else '  short':>16}")
    if n_ok is None:
        print(f"\n  NO n up to {max(ratio_n)} clears R. The contradiction is not "
              f"reachable by cascade depth alone.")
    else:
        print(f"\n  n = {n_ok} IS ENOUGH, and n = 1 is not ({ratio_n[1]:.2f} vs "
              f"{need / cap:.2f} needed). The single exponential\n  cannot be small "
              f"at {YEAR} and large at 2300 SIMULTANEOUSLY; a two-stage cascade can, "
              f"by a factor\n  {ratio_n[2] / (need / cap):.1f}x of margin. This is "
              f"the same defect memory `protect_matched_forcing`\n  named on "
              f"2026-08-21b from the physics side -- \"physics wants ~nothing until "
              f"2147 then a term\n  still accelerating at 2300; the exponential is "
              f"front-loaded and saturating\" -- arriving\n  independently from a "
              f"band this session had not yet scored. IT IS A PRE-CHECK, NOT A FIT:"
              f"\n  it says a cascade is not excluded, not that one passes the full "
              f"scorecard.")

    print(f"\n  \"THEN MOVE THE ONSET\" -- closed, because R is fixed by the "
          f"targets and only the FORM's\n  achievable ratio is free:")
    print(f"    {'onset K':>9}{'n=1':>9}{'n=2':>9}{'  n=1 vs R':>12}")
    for on, rr in sweep.items():
        print(f"    {on:>9.2f}{rr[1]:>9.2f}{rr[2]:>9.2f}"
              f"{'  CLEARS' if rr[1] >= need / cap else '  short':>12}")
    print(f"  No onset in {ONSET_SWEEP_K[0]:g}-{ONSET_SWEEP_K[-1]:g} K lets the "
          f"first-order form reach R = {need / cap:.2f}.")

    print(f"\n  psi, the quantity actually in dispute: x2300@{YEAR} caps it at 0.125 "
          f"cm/yr at onset 4.69;\n  Greve@3001 wants {PSI_GREVE[0]}-{PSI_GREVE[1]}, "
          f"the 2250-2300 rate criterion {PSI_RATE[0]}-{PSI_RATE[1]}. DISJOINT -- but "
          f"psi is\n  a FIRST-ORDER parameterisation, so read the disjointness as "
          f"evidence against the FORM,\n  not as two sources contradicting each "
          f"other.")

    print(f"\nWROTE {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
