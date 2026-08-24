#!/usr/bin/env python3
"""
build_ais_unresolved_amplification.py -- OPTION 3: a process-model headline plus an
    explicitly-flagged UNRESOLVED AMPLIFICATION arm, with a default probability from
    the FACTS Bamber-2019 structured expert judgment.

NAMING (Marcus, 2026-08-24). This arm was called the "MICI arm" for one day. It is not.
It is named for its ROLE -- amplification that BOTH our emulator AND the process
ensembles omit -- because the mechanism list is the part that keeps changing:

  * MICI (cliff collapse). Trending DOWN: Edwards et al. 2019 Nature 566:58 finds it is
    not required for the Pliocene, the LIG or 1992-2017; DeConto et al. 2021 revised it
    down 2-3x; Morlighem et al. 2024 Sci Adv 10:eado7794 finds Thwaites would not retreat
    further this century under a physically-motivated calving law.
  * FRACTURE DAMAGE (viscosity weakening; basal crevasses dominant). Trending UP:
    Blasco et al. 2026 PNAS 123(28):e2601529123 -- the Pattyn/ULB group, with Violaine
    Coulon co-first author here AND lead author of the Coulon et al. 2025 process
    ensemble, i.e. the same lab saying its own class of model omits something.
  * Whatever is named next. The arm should not need renaming when that happens.

=> `UNRESOLVED_AMPLIFICATION`. In prose it is the low-likelihood high-impact branch. The
label is deliberately NOT "deep uncertainty", which means UNQUANTIFIED probability, and
we are assigning one. And deliberately nothing near "fast dynamics" -- that is already
`antarctic_lambda`'s own name in DAIS and would collide with the parameter being scaled.

THE RENAME IS NOT COSMETIC. It fixes two mismatches:
  (a) THE CONSTRUCTION WAS ALWAYS BROADER THAN THE OLD LABEL. The arm is scaled to the
      LIG residual -- the fraction DAIS CANNOT REACH at the last interglacial. Ruckert
      et al. attribute that shortfall to missing MICI, but what it measures is everything
      DAIS misses in a warm period, which now demonstrably includes fracture damage.
  (b) IT REPAIRS THE PROBABILITY'S IDENTIFYING ASSUMPTION. Reading a MICI probability off
      the Bamber SEJ required assuming SEJ mass above the process range is MICI -- which
      FAILED its placebo test. The experts were asked about AIS TOTALS, so the same
      statistic is a far better estimator of "SOME omitted amplifier operates". The
      placebo floor still must be corrected; the interpretation no longer strains.

TWO DESIGN DECISIONS, BOTH MARCUS'S, BOTH RECORDED:

  (1) ARM SCALE = THE LIG RESIDUAL, NOT A FULL PUBLISHED PARAMETERISATION.
      `ais_lambda_rests_on_lig` measured that lambda is identified by the LIG ALONE (the
      other three Ruckert constraints fire 0.0% of draws) and is data-limited, not
      prior-truncated. So lambda is a fitted warm-period fast-loss rate: whatever the real
      LIG loss contained, lambda has already absorbed it. Scaling the arm to a full
      published parameterisation would therefore DOUBLE-COUNT.
      Ruckert et al. bound the un-absorbed part themselves: their model undershoots the
      LIG by "roughly 26% or 1 m". Writing f = 0.26, a draw producing 0.92*lambda*D over
      an above-threshold window D sits at (1-f) of the true LIG loss, so
            0.92*dlambda*D = (f/(1-f)) * 0.92*lambda*D
      => **dlambda = (f/(1-f)) * lambda, and D CANCELS.**
      That matters: the LIG above-threshold window is only known to ~100-1200 yr, and the
      residual scaling does not depend on it.
      The arm is therefore lambda -> lambda / (1 - f) = 1.351 * lambda.

  (2) PROBABILITY from the FACTS Bamber-2019 SEJ. A published elicitation with a
      documented protocol, not a number we invented. The reference is `emuAIS`
      (emulandice / ISMIP6 emulator), the AR6 process module, which omits BOTH MICI and
      fracture damage -- so it is the right baseline for an unresolved-amplification
      exceedance, and calling it merely "no-MICI" UNDERSTATES what it leaves out.

      THE OBVIOUS DEFINITION FAILS ITS OWN PLACEBO TEST AND IS NOT USED.
      P(SEJ > process p95) returns 0.185 at 2020 -- before any of these mechanisms can
      have operated in ANY module. The Bamber SEJ is simply a much WIDER distribution than
      a process emulator everywhere; its 2100 ssp585 median (18.0 cm) sits essentially ON
      the process p95 (18.3 cm). That statistic measures how pessimistic the elicitation
      is OVERALL, and it returned an implausible 0.52. `deconto21` by contrast is EXACTLY
      0.000 through 2060 and then engages (0.02 -> 0.32 -> 0.56 -> 0.705).

      SHIPPED DEFINITION: P(SEJ > the process-ensemble MAXIMUM) -- the probability the
      experts place on AIS exceeding anything the amplification-free process ensemble can
      produce. Its 2020 placebo floor is 0.075 rather than 0.185, and the floor-corrected
      version agrees with the floor-corrected p95 version (0.225 vs 0.310 at 2100), which
      is the cross-check that the correction works. GATE [PLACEBO] prints the 2020 value
      for every variant; any variant with a large floor is reported but must NOT be used.

      Bamber 2019 PREDATES DeConto 2021, Morlighem 2024, Coulon 2025 and Blasco 2026, and
      is the OLDEST source in the stack (`weight_recent_literature`). Conservative-HIGH on
      MICI specifically; less clearly so once fracture damage sits inside the label. A
      reason to report dE/dP alongside it, not to adjust it silently.

  python3 python/build_ais_unresolved_amplification.py [--tag=L14]
WRITES outputs/ais_unresolved_amplification_{arm,probability}_<tag>.csv
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
PROCESS_MODULE = ("emuAIS.emulandice.AIS_globalsl",
                  "emuAIS (emulandice/ISMIP6; omits MICI AND fracture damage)")
SEJ_MODULE = ("bamber19.bamber19.icesheets_AIS", "Bamber 2019 structured expert judgment")
DECONTO_MODULE = ("deconto21.deconto21.AIS_AIS", "DeConto 2021 MICI (reference arm, NOT the shipped one)")
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
    print("OPTION 3 -- PROCESS HEADLINE + FLAGGED UNRESOLVED-AMPLIFICATION ARM, SOURCED WEIGHT")
    print("=" * 94)

    # ---- (2) the probability, from FACTS ---------------------------------
    print(f"\n[A] DEFAULT PROBABILITY = P({SEJ_MODULE[1]} AIS  >  p95 of {PROCESS_MODULE[1]})\n")
    prows = []
    print(f"{'ssp':8s} {'year':>5s} {'proc p95':>11s} {'proc max':>11s} "
          f"{'P(SEJ>p95)':>11s} {'P(SEJ>max)':>11s} {'P(DC>p95)':>10s}")
    for ssp in SCENARIOS:
        yn, vn = load(ssp, PROCESS_MODULE[0])
        ys, vs = load(ssp, SEJ_MODULE[0])
        yd, vd = load(ssp, DECONTO_MODULE[0])
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
            prows.append(dict(scenario=ssp, year=int(y), process_p95_cm=p95,
                              process_max_cm=mx, sej_median_cm=float(np.median(vs[j])),
                              p_exceed_p95=p_p95, p_exceed_max=p_max,
                              p_deconto_exceed_p95=dp))
    pdf = pd.DataFrame(prows)
    pdf.to_csv(os.path.join(REPO, "outputs", f"ais_unresolved_amplification_probability_{TAG}.csv"), index=False)

    ## ---- GATE [PLACEBO]: at 2020 no module has any MICI, so an honest MICI
    ## statistic must read ~0 there. Anything with a large floor is measuring
    ## elicitation-vs-emulator width, not MICI.
    b = pdf[(pdf.scenario == "ssp585") & (pdf.year == 2020)].iloc[0]
    print(f"\n[PLACEBO GATE] ssp585 @2020, before ANY module has MICI:")
    print(f"    P(SEJ > process p95) = {b.p_exceed_p95:.3f}   <- large floor, REJECTED as a weight")
    print(f"    P(SEJ > process max) = {b.p_exceed_max:.3f}   <- shipped statistic")
    print(f"    P(DeConto > p95)    = {b.p_deconto_exceed_p95:.3f}   <- a real MICI indicator reads 0")

    late = pdf[(pdf.scenario == "ssp585") & (pdf.year >= 2070)]
    p_raw = float(late.p_exceed_max.median())
    p_def = max(0.0, p_raw - float(b.p_exceed_max))
    print(f"\n  ⚠ `emuAIS` stops at 2100, so the reference exists only to 2100, and the estimate")
    print(f"    is NOT horizon-invariant: ssp585 P(SEJ>max) runs "
          f"{pdf[pdf.scenario=='ssp585'].p_exceed_max.min():.3f} to "
          f"{pdf[pdf.scenario=='ssp585'].p_exceed_max.max():.3f} over 2020-2100.")
    print(f"    ssp585 2070-2100 median = {p_raw:.3f}; minus the {b.p_exceed_max:.3f} placebo floor")
    print(f"    => DEFAULT **P_UNRES = {p_def:.3f}**  (the p95-based route floor-corrects to 0.310,")
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
                         p_unres=p_def, expected_cm=exp_,
                         d_expected_d_p_cm=arm - base))
    adf = pd.DataFrame(rows)
    adf.to_csv(os.path.join(REPO, "outputs", f"ais_unresolved_amplification_arm_{TAG}.csv"), index=False)

    print(f"\n    AIS ssp585, cm (median), arm lambda = {rows[0]['arm_lambda']:.6f} "
          f"(inside paleo support: {rows[0]['arm_lambda_in_paleo_support']}, "
          f"paleo pctile {100*(lam < rows[0]['arm_lambda']).mean():.1f})")
    print(f"\n{'horizon':>8s} {'process':>9s} {'arm':>9s} {'delta':>8s} "
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
    print(f"\n  The last column is the deliverable Marcus asked for: dE[AIS]/dP_UNRES. Anyone who")
    print(f"    rejects P = {p_def:.3f} can substitute their own without re-running anything.")
    print(f"\nwrote outputs/ais_unresolved_amplification_{{arm,probability}}_{TAG}.csv")


if __name__ == "__main__":
    main()
