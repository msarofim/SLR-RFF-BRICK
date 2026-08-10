#!/usr/bin/env python3
"""
set_gis_dt_prior.py — the prior on dT, the Greenland threshold-location shift in
V_eq(T) = pchip_PISM(T - dT).

dT is the one V_eq parameter the calibrator samples (python/fit_gis_veq_pism.py:
no smooth parametric form fits the ladder, and dT is the only quantity the
scenario answers are actually sensitive to). This file decides its prior, from
sources OUTSIDE the PISM ladder, and records the arithmetic.

WHY THE PRIOR CANNOT BE CENTRED ON PISM
    Our PISM collapse sits at GMT ~2.4. Both published assessments put the
    Greenland threshold BELOW that:

      Bochow et al. 2023, Nature 622:528 (the source of our own ladder;
      2 models, so NOT independent evidence)      threshold 1.7-2.3 C
      doi:10.1038/s41586-023-06503-9

      Armstrong McKay et al. 2022, Science 377:eabn7950 (multi-model
      tipping-element synthesis; independent of Bochow)
      central 1.5 C, range 0.8-3.0 C

    A prior centred on dT = 0 therefore encodes "PISM's threshold is the best
    estimate", which neither source supports. PISM is at or slightly above the
    top of Bochow's own stated range and well above Armstrong McKay's central.

WHY IT ALSO CANNOT BE CENTRED ON THE LITERATURE CENTRAL
    Shifting dT negative raises V_eq at EVERY temperature, including today's.
    Present-day committed loss is an observable, and Box et al. 2022
    (Nat Clim Chang 12:808, doi:10.1038/s41558-022-01441-2) measured it:
    274 +/- 68 mm committed by the ice sheet's disequilibrium with the
    2000-2019 climate, from 3.3 +/- 0.9% volume loss. That is explicitly a
    LOWER BOUND ("at least"), and it is a near-term current-geometry number
    rather than a multi-millennial equilibrium, so the equilibrium commitment
    should EXCEED it -- but not without limit. This bounds dT from below.

    So the prior is built from a threshold range on one side and an
    observed-commitment floor on the other, and is deliberately left wide
    enough that the historical calibration does the rest. Over-tightening it
    would hand the answer to the prior.

  python3 python/set_gis_dt_prior.py
Writes outputs/gis_dt_prior.csv
"""
import os
import subprocess

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURVE_CSV = os.path.join(REPO, "outputs/gis_veq_pism_curve.csv")
OUT = os.path.join(REPO, "outputs/gis_dt_prior.csv")

V0_M = 7.42
THRESHOLD_FRAC = 0.50           # "threshold" = GMT at which half the volume is committed
PRESENT_GMT = 1.25              # IGCC 2015-2024, canonical anchor 1.254 C
SCENARIO_PEAKS = {"SSP1-2.6": 1.92, "SSP2-4.5": 3.19, "SSP5-8.5": 7.81}

# --- external evidence, each with its citation ------------------------------
BOCHOW23 = dict(name="Bochow et al. 2023 (Nature 622:528)", lo=1.7, mid=2.0, hi=2.3,
                independent=False, note="source of our ladder; 2 models")
MCKAY22 = dict(name="Armstrong McKay et al. 2022 (Science 377:eabn7950)",
               lo=0.8, mid=1.5, hi=3.0, independent=True,
               note="multi-model tipping-element synthesis")
BOX22_MM = (274.0, 68.0)        # committed SLR, mm, +/- 1 sd; a LOWER bound
BOX22_CITE = "Box et al. 2022 (Nat Clim Chang 12:808)"
# Observed melt rate, mm/yr SLE, from outputs/recalib_targets_ext.csv (Frederikse
# GIS target). Used for the dT-vs-tau trade-off check below.
OBS_RATE_MODERN = 0.841         # 2003-2018
OBS_RATE_1993_2018 = 0.655
# Stock SIMPLE e-folding times at the current posterior (scoping §2), years.
TAU_STOCK = (836, 1218)

# --- prior construction rule ------------------------------------------------
# Centre on the mean of the two assessments' central estimates; take sigma from
# the independent one's range read as +/- 2 sd. Truncate at the Box floor and at
# the upper end of the wider published range.
PRIOR_SIGMA_FROM = MCKAY22      # the independent assessment sets the width
SIGMA_RANGE_IN_SD = 4.0         # lo..hi spans this many sd


def main():
    c = pd.read_csv(CURVE_CSV)
    g, p = c["gmt_K"].to_numpy(), c["pchip"].to_numpy()

    def loss(T, dT=0.0):
        return float(np.interp(T - dT, g, p))

    # PISM's own threshold, on the stated definition
    t_pism = float(np.interp(THRESHOLD_FRAC * V0_M, p, g))
    to_dt = lambda T: T - t_pism          # a threshold of T means this dT

    print(f"PISM threshold ({THRESHOLD_FRAC:.0%} of V0 = {THRESHOLD_FRAC * V0_M:.2f} m "
          f"committed): GMT {t_pism:.2f} C")
    print(f"present-day committed loss at dT=0, GMT {PRESENT_GMT}: "
          f"{loss(PRESENT_GMT) * 1000:.0f} mm\n")

    print("EXTERNAL THRESHOLD ASSESSMENTS, mapped to dT")
    print(f"  {'source':52s} {'threshold C':>18s} {'-> dT':>18s}  indep")
    rows = []
    for s in (BOCHOW23, MCKAY22):
        print(f"  {s['name']:52s} {s['lo']:5.1f} {s['mid']:5.1f} {s['hi']:5.1f}  "
              f"{to_dt(s['lo']):5.2f} {to_dt(s['mid']):5.2f} {to_dt(s['hi']):5.2f}  "
              f"{'yes' if s['independent'] else 'NO'}")
        rows.append(dict(kind="threshold_assessment", source=s["name"],
                         thresh_lo=s["lo"], thresh_mid=s["mid"], thresh_hi=s["hi"],
                         dt_lo=to_dt(s["lo"]), dt_mid=to_dt(s["mid"]),
                         dt_hi=to_dt(s["hi"]), independent=s["independent"],
                         note=s["note"]))

    # --- the observational floor -------------------------------------------
    print(f"\nPRESENT-DAY COMMITMENT vs {BOX22_CITE} = "
          f"{BOX22_MM[0]:.0f} +/- {BOX22_MM[1]:.0f} mm (a LOWER bound)")
    print(f"  {'dT':>6s} {'committed at present GMT, mm':>30s} {'x Box central':>15s}")
    dt_grid = np.arange(-2.0, 1.01, 0.1)
    for dT in np.arange(-1.6, 0.81, 0.4):
        v = loss(PRESENT_GMT, dT) * 1000
        print(f"  {dT:+6.1f} {v:30.0f} {v / BOX22_MM[0]:15.1f}")
    # dT at which the equilibrium commitment first exceeds the Box lower bound
    vals = np.array([loss(PRESENT_GMT, d) * 1000 for d in dt_grid])
    dt_meets_box = float(np.interp(BOX22_MM[0], vals[::-1], dt_grid[::-1]))
    print(f"\n  equilibrium commitment equals the Box central at dT = "
          f"{dt_meets_box:+.2f}; dT ABOVE this understates a measured lower bound.")

    # --- the prior ----------------------------------------------------------
    mu = float(np.mean([to_dt(BOCHOW23["mid"]), to_dt(MCKAY22["mid"])]))
    sigma = (PRIOR_SIGMA_FROM["hi"] - PRIOR_SIGMA_FROM["lo"]) / SIGMA_RANGE_IN_SD
    lo = to_dt(min(BOCHOW23["lo"], MCKAY22["lo"]))
    hi = min(to_dt(max(BOCHOW23["hi"], MCKAY22["hi"])), dt_meets_box)
    print(f"\nPRIOR  dT ~ Normal({mu:.2f}, {sigma:.2f}) truncated to "
          f"[{lo:.2f}, {hi:.2f}]")
    print(f"  centre  = mean of the two assessments' centrals "
          f"({to_dt(BOCHOW23['mid']):.2f}, {to_dt(MCKAY22['mid']):.2f})")
    print(f"  sigma   = {PRIOR_SIGMA_FROM['name'].split(' (')[0]} range "
          f"{PRIOR_SIGMA_FROM['lo']}-{PRIOR_SIGMA_FROM['hi']} read as "
          f"+/-{SIGMA_RANGE_IN_SD / 2:.0f} sd")
    print(f"  lower   = widest published threshold lower bound "
          f"({min(BOCHOW23['lo'], MCKAY22['lo'])} C)")
    print(f"  upper   = min(widest published upper bound, the Box floor) -> "
          f"{'Box floor binds' if hi == dt_meets_box else 'literature binds'}")
    print(f"  NOTE: dT = 0 (pure PISM) sits at "
          f"{(0 - mu) / sigma:+.2f} sd of this prior -- PISM is a late-threshold "
          f"member, not the centre.")

    print(f"\nWHAT THE PRIOR IMPLIES, committed loss m SLE")
    print(f"  {'dT':>18s} " + "".join(f"{s:>12s}" for s in SCENARIO_PEAKS) +
          f"{'present':>10s}")
    for lab, dT in [("prior lo", lo), ("mu - sigma", mu - sigma), ("mu", mu),
                    ("mu + sigma", mu + sigma), ("prior hi", hi), ("PISM (dT=0)", 0.0)]:
        print(f"  {lab + f' ({dT:+.2f})':>18s} " +
              "".join(f"{loss(T, dT):12.2f}" for T in SCENARIO_PEAKS.values()) +
              f"{loss(PRESENT_GMT, dT) * 1000:10.0f}")

    # --- the trade-off the offline cell has to break ------------------------
    # In a one-channel relaxation, dV/dt = (V_eq - V)/tau, so the modern melt
    # rate is (commitment)/tau. A more negative dT raises the commitment and
    # therefore DEMANDS a longer tau to keep the observed rate -- which makes
    # the scenario response worse, the opposite of what pass 1 is for. dT and
    # tau are not separately identified in a one-channel model. Breaking that
    # is precisely what option B's fast channel is supposed to do.
    print(f"\ndT-vs-TAU TRADE-OFF -- one-channel implication, modern rate = "
          f"commitment / tau")
    print(f"  observed {OBS_RATE_MODERN} mm/yr (2003-2018), "
          f"{OBS_RATE_1993_2018} mm/yr (1993-2018); stock tau {TAU_STOCK[0]}-"
          f"{TAU_STOCK[1]} yr")
    print(f"  {'dT':>7s} {'commit mm':>10s} " +
          "".join(f"{'rate@tau=' + str(t):>16s}" for t in TAU_STOCK) +
          f"{'tau needed, yr':>16s}")
    for dT in (lo, mu - sigma, mu, mu + sigma, 0.0, hi):
        cm = loss(PRESENT_GMT, dT) * 1000
        print(f"  {dT:+7.2f} {cm:10.0f} " +
              "".join(f"{cm / t:16.2f}" for t in TAU_STOCK) +
              f"{cm / OBS_RATE_MODERN:16.0f}")
    print("  -> a one-channel fit absorbs a negative dT as a LONGER tau, which is"
          "\n     the pathology pass 1 exists to remove. Pre-registered check for the"
          "\n     offline cell: does the two-channel structure break the dT-tau ridge?")

    rows.append(dict(kind="prior", source="derived", dt_mid=mu, dt_lo=lo, dt_hi=hi,
                     sigma=sigma, note=f"Normal({mu:.4f}, {sigma:.4f}) truncated "
                                       f"[{lo:.4f}, {hi:.4f}]"))
    rows.append(dict(kind="obs_floor", source=BOX22_CITE, dt_hi=dt_meets_box,
                     note=f"{BOX22_MM[0]:.0f} +/- {BOX22_MM[1]:.0f} mm, lower bound; "
                          f"binds dT above {dt_meets_box:.4f}"))
    rows.append(dict(kind="reference", source="PISM-dEBM ladder",
                     thresh_mid=t_pism, dt_mid=0.0,
                     note=f"{THRESHOLD_FRAC:.0%}-of-V0 crossing; present-day "
                          f"commitment {loss(PRESENT_GMT) * 1000:.0f} mm"))
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
