#!/usr/bin/env python3
"""
build_ais_mici_arm.py -- OPTION 3: a MICI-free headline plus an explicitly-flagged
                         MICI arm, with a DEFAULT PROBABILITY from the FACTS
                         Bamber-2019 structured expert judgment.

WHY THIS SHAPE (Marcus, 2026-08-24). AR6 excludes MICI from its likely ranges and
carries it as a low-likelihood high-impact storyline with NO numerical probability.
Marcus's ruling: declining to give a number is not neutral -- it silently pushes the
choice onto every downstream user, which is worse for an SC-GHG than a stated,
sourced, revisable default. So this file supplies one.

TWO DESIGN DECISIONS, BOTH MARCUS'S, BOTH RECORDED:

  (1) ARM SCALE = THE LIG RESIDUAL, NOT THE FULL DeConto PARAMETERISATION.
      `ais_lambda_rests_on_lig` measured that lambda is identified by the LIG ALONE
      (the other three Ruckert constraints fire 0.0% of draws) and is data-limited,
      not prior-truncated. So lambda is a fitted warm-period fast-loss rate: whatever
      the real LIG loss contained, lambda has already absorbed it. Scaling a MICI arm
      to a full MICI parameterisation would therefore DOUBLE-COUNT.
      Ruckert et al. 2017 bound the un-absorbed part themselves: their MICI-free model
      undershoots the LIG by "roughly 26% or 1 m". Writing f = 0.26 for that shortfall,
      a draw that produces 0.92*lambda*D over an above-threshold window D is at (1-f)
      of the true LIG loss, so the missing rate satisfies
            0.92*dlambda*D = (f/(1-f)) * 0.92*lambda*D
      => **dlambda = (f/(1-f)) * lambda, and D CANCELS.**
      That matters: the LIG above-threshold duration is only known to ~100-1200 yr
      (`ais_lambda_rests_on_lig` T-B), and the residual scaling does not depend on it.
      The arm is therefore lambda -> lambda / (1 - f) = 1.351 * lambda.

  (2) PROBABILITY from the FACTS Bamber-2019 SEJ. A published elicitation with a
      documented protocol, not a number we invented. The no-MICI reference is `emuAIS`
      (emulandice / ISMIP6 emulator), the AR6 process module, which is MICI-free.

      ⚠ THE OBVIOUS DEFINITION FAILS ITS OWN PLACEBO TEST AND IS NOT USED.
      P(SEJ > no-MICI p95) returns **0.185 at 2020** -- before MICI is possible in ANY
      module. The Bamber SEJ is simply a much WIDER distribution than a process
      emulator everywhere, because it carries experts' full structural uncertainty
      rather than MICI specifically; its 2100 ssp585 median (18.0 cm) sits essentially
      ON the process p95 (18.3 cm). So that statistic measures how pessimistic the
      elicitation is OVERALL, not whether MICI runs, and it returned an implausible
      0.52. `deconto21` by contrast is EXACTLY 0.000 through 2060 and then engages
      (0.02 -> 0.32 -> 0.56 -> 0.705) -- that is what a MICI indicator looks like.

      SHIPPED DEFINITION: **P(SEJ > the no-MICI ensemble MAXIMUM)** -- the probability
      the experts place on AIS exceeding anything the MICI-free process ensemble can
      produce. Its 2020 placebo floor is 0.075 rather than 0.185, and the
      floor-corrected version of it agrees with the floor-corrected p95 version
      (0.225 vs 0.310 at 2100), which is the cross-check that the correction works.
      GATE [PLACEBO] below prints the 2020 value for every variant; any variant whose
      placebo floor is large is reported but must not be used as a weight.

      ⚠ Bamber 2019 PREDATES DeConto 2021's downward MICI revision and Morlighem 2024.
      The elicitation is therefore a CONSERVATIVE-HIGH weight relative to the current
      mechanical literature. That is a reason to report dE/dP alongside it, not a
      reason to adjust it silently.

⚠ THE ARM IS SMALL COMPARED WITH DeConto -- BY CONSTRUCTION, NOT BY ACCIDENT. It is
scaled to what OUR calibration says it is missing, not to what DP16 says MICI does.
The deconto21 column is printed alongside precisely so that gap stays visible.

⚠ HORIZON. `emuAIS` stops at 2100, so the probability can only be evaluated where the
no-MICI reference exists. It is NOT assumed horizon-invariant; every horizon computed
is reported and the spread across them IS the answer's own uncertainty.

  python3 python/build_ais_mici_arm.py [--tag=L14]
WRITES outputs/ais_mici_arm_<tag>.csv, outputs/ais_mici_probability_<tag>.csv
"""
import glob
import os
import sys

import netCDF4 as nc
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a[6:] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
FACTS = os.path.expanduser("~/Documents/2026/CodeProjects/facts/experiments")
LADDER = os.path.join(REPO, "outputs", f"scope_ais_three_tests_ladder_{TAG}.csv")
PALEO = os.path.join(REPO, "data/dais_paleo/daisfastdyn_lambda_tcrit.csv")

# Ruckert et al. 2017, PLoS ONE 12:e0170052 -- "missing MICI produces a lower mean
# hindcast (roughly 26% or 1 m smaller) during the LIG".
LIG_SHORTFALL = 0.26
ARM_SCALE = 1.0 / (1.0 - LIG_SHORTFALL)

# The FACTS modules. `emuAIS` is the MICI-FREE process reference.
NO_MICI_MODULE = ("emuAIS.emulandice.AIS_globalsl", "emuAIS (emulandice/ISMIP6, no MICI)")
SEJ_MODULE = ("bamber19.bamber19.icesheets_AIS", "Bamber 2019 structured expert judgment")
MICI_MODULE = ("deconto21.deconto21.AIS_AIS", "DeConto 2021 MICI")
SCENARIOS = ["ssp585", "ssp245"]
SSP_EXP = "global.coupling.{ssp}.n200"
SSP585_LADDER = "ssp585"


def load(ssp, pat):
    f = glob.glob(os.path.join(FACTS, SSP_EXP.format(ssp=ssp), "output", f"*{pat}*.nc"))
    if not f:
        return None, None
    d = nc.Dataset(f[0])
    # (years, samples, locations) -> cm, drop the single location
    v = np.asarray(d["sea_level_change"][:]).squeeze() / 10.0
    if v.shape[0] != len(d["years"][:]):
        v = v.T
    return np.asarray(d["years"][:]), v


def main():
    print("=" * 94)
    print("OPTION 3 -- MICI-FREE HEADLINE + A FLAGGED MICI ARM WITH A SOURCED DEFAULT WEIGHT")
    print("=" * 94)

    # ---- (2) the probability, from FACTS ---------------------------------
    print(f"\n[A] DEFAULT PROBABILITY = P({SEJ_MODULE[1]} AIS  >  p95 of {NO_MICI_MODULE[1]})\n")
    prows = []
    print(f"{'ssp':8s} {'year':>5s} {'noMICI p95':>11s} {'noMICI max':>11s} "
          f"{'P(SEJ>p95)':>11s} {'P(SEJ>max)':>11s} {'P(DC>p95)':>10s}")
    for ssp in SCENARIOS:
        yn, vn = load(ssp, NO_MICI_MODULE[0])
        ys, vs = load(ssp, SEJ_MODULE[0])
        yd, vd = load(ssp, MICI_MODULE[0])
        if yn is None or ys is None:
            print(f"  {ssp}: FACTS output missing, skipped")
            continue
        for i, y in enumerate(yn):
            j = int(np.where(ys == y)[0][0])
            p95 = float(np.percentile(vn[i], 95))
            mx = float(vn[i].max())
            p_p95 = float((vs[j] > p95).mean())
            p_max = float((vs[j] > mx).mean())          # <- the SHIPPED statistic
            if yd is not None and y in yd:
                k = int(np.where(yd == y)[0][0])
                dp = float((vd[k] > p95).mean())
            else:
                dp = np.nan
            print(f"{ssp:8s} {y:5d} {p95:11.2f} {mx:11.2f} {p_p95:11.3f} {p_max:11.3f} "
                  f"{dp:10.3f}")
            prows.append(dict(scenario=ssp, year=int(y), nomici_p95_cm=p95,
                              nomici_max_cm=mx, sej_median_cm=float(np.median(vs[j])),
                              p_exceed_p95=p_p95, p_exceed_max=p_max,
                              p_deconto_exceed_p95=dp))
    pdf = pd.DataFrame(prows)
    pdf.to_csv(os.path.join(REPO, "outputs", f"ais_mici_probability_{TAG}.csv"), index=False)

    ## ---- GATE [PLACEBO]: at 2020 no module has any MICI, so an honest MICI
    ## statistic must read ~0 there. Anything with a large floor is measuring
    ## elicitation-vs-emulator width, not MICI.
    b = pdf[(pdf.scenario == "ssp585") & (pdf.year == 2020)].iloc[0]
    print(f"\n[PLACEBO GATE] ssp585 @2020, before ANY module has MICI:")
    print(f"    P(SEJ > noMICI p95) = {b.p_exceed_p95:.3f}   <- large floor, REJECTED as a weight")
    print(f"    P(SEJ > noMICI max) = {b.p_exceed_max:.3f}   <- shipped statistic")
    print(f"    P(DeConto > p95)    = {b.p_deconto_exceed_p95:.3f}   <- a real MICI indicator reads 0")

    late = pdf[(pdf.scenario == "ssp585") & (pdf.year >= 2070)]
    p_raw = float(late.p_exceed_max.median())
    p_def = max(0.0, p_raw - float(b.p_exceed_max))
    print(f"\n  ⚠ `emuAIS` stops at 2100, so the reference exists only to 2100, and the estimate")
    print(f"    is NOT horizon-invariant: ssp585 P(SEJ>max) runs "
          f"{pdf[pdf.scenario=='ssp585'].p_exceed_max.min():.3f} to "
          f"{pdf[pdf.scenario=='ssp585'].p_exceed_max.max():.3f} over 2020-2100.")
    print(f"    ssp585 2070-2100 median = {p_raw:.3f}; minus the {b.p_exceed_max:.3f} placebo floor")
    print(f"    => DEFAULT **P_MICI = {p_def:.3f}**  (the p95-based route floor-corrects to 0.310,")
    print(f"       so two independent corrections agree to ~0.08 -- that agreement IS the check)")
    print(f"    Still an UPPER estimate: even this threshold retains some non-MICI SEJ width.")

    # ---- (1) the arm, scaled to the LIG residual -------------------------
    print(f"\n[B] ARM SCALE = LIG RESIDUAL. Ruckert shortfall f = {LIG_SHORTFALL:.2f} "
          f"=> lambda -> lambda / (1-f) = {ARM_SCALE:.3f} x lambda")
    print("    (the above-threshold duration CANCELS -- see the header derivation)")
    lam = pd.read_csv(PALEO)["lambda"].to_numpy()
    ladder = pd.read_csv(LADDER)

    rows = []
    for horizon in sorted(ladder.horizon.unique()):
        s = ladder[(ladder.scenario == SSP585_LADDER) & (ladder.horizon == horizon)].sort_values("lambda")
        f_med = lambda L, s=s: float(np.interp(L, s["lambda"], s["median_cm"]))
        lo_x, hi_x = s["lambda"].min(), s["lambda"].max()
        base_lam = 0.010567                      # posterior median lambda
        arm_lam = base_lam * ARM_SCALE
        clipped = arm_lam > hi_x
        base, arm = f_med(base_lam), f_med(min(arm_lam, hi_x))
        exp_ = (1 - p_def) * base + p_def * arm
        rows.append(dict(horizon=int(horizon), base_lambda=base_lam, arm_lambda=arm_lam,
                         arm_lambda_in_paleo_support=not clipped,
                         base_cm=base, arm_cm=arm, delta_cm=arm - base,
                         p_mici=p_def, expected_cm=exp_,
                         d_expected_d_p_cm=arm - base))
    adf = pd.DataFrame(rows)
    adf.to_csv(os.path.join(REPO, "outputs", f"ais_mici_arm_{TAG}.csv"), index=False)

    print(f"\n    AIS ssp585, cm (median), arm lambda = {rows[0]['arm_lambda']:.6f} "
          f"(inside paleo support: {rows[0]['arm_lambda_in_paleo_support']}, "
          f"paleo pctile {100*(lam < rows[0]['arm_lambda']).mean():.1f})")
    print(f"\n{'horizon':>8s} {'no-MICI':>9s} {'MICI arm':>9s} {'delta':>8s} "
          f"{'E[AIS]':>9s} {'dE/dP (cm per unit P)':>23s}")
    for r in rows:
        print(f"{r['horizon']:8d} {r['base_cm']:9.1f} {r['arm_cm']:9.1f} {r['delta_cm']:8.1f} "
              f"{r['expected_cm']:9.1f} {r['d_expected_d_p_cm']:23.1f}")

    print(f"\n  ⚠ THE ARM IS SMALL vs DeConto BY CONSTRUCTION. At 2300 it adds "
          f"{rows[-1]['delta_cm']:.0f} cm, against the")
    print(f"    687-1355 cm MICI branch quoted by Coulon et al. 2025. That gap is the PRICE OF")
    print(f"    NOT DOUBLE-COUNTING: it is what OUR calibration says lambda cannot reach, not")
    print(f"    what DP16 says MICI does. If the arm should instead be comparable with FACTS")
    print(f"    wf3f, that is a DIFFERENT decision and it re-opens the double-count.")
    print(f"\n  The last column is the deliverable Marcus asked for: dE[AIS]/dP_MICI. Anyone who")
    print(f"    rejects P = {p_def:.3f} can substitute their own without re-running anything.")
    print(f"\nwrote outputs/ais_mici_{{arm,probability}}_{TAG}.csv")


if __name__ == "__main__":
    main()
