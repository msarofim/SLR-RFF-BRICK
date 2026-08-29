"""
diag_l21_vs_l22_steric_cap.py

RESOLVES THE FOUR PREDICTIONS REGISTERED IN run_mcmc_L22.sh.

L22 = L21 with ONE change: the steric AR(1) MARGINAL sd is bounded at the
1993-2025 mean observational sigma (0.1036 cm) instead of running free at
L21's 0.267. The question the arm exists to answer is whether L21's +16.9
sigma thermal-expansion residual at 2025 was the NOISE MODEL absorbing a real
misfit, or something structural in the one-coefficient TE form.

WHAT THIS PRINTS, IN THE ORDER IT MATTERS:

  1. THE TE RESIDUAL, L21 vs L22, in units of the steric target's OWN per-year
     sigma -- the same eps the likelihood uses, 0.05 cm floor included.
     COLLAPSE toward ~2 sigma  => the noise model was the cause.
     STAYS LARGE               => the depth split becomes the live candidate.

  2. WHERE THE RESIDUAL WENT (prediction iv). The D2 discrepancy basis is
     1/eps^2-weighted -- i.e. modern-era-weighted -- with a prior sd of 0.5 cm,
     FIVE TIMES the cap. If d2_steric absorbs what the AR(1) term no longer can,
     then "the residual collapsed" is true and "the noise model was the cause"
     is only half true. Reported in units of L21's OWN posterior sd, so a shift
     is priced against the spread it has to be visible against, not in raw cm.

  3. WHAT ELSE MOVED (prediction iii). Every component's bias, both arms. The
     cap is EXPECTED to cost something somewhere; the point is to name it, not
     to be surprised by it.

  source ~/climate-env/bin/activate && python python/diag_l21_vs_l22_steric_cap.py
"""
import os
import sys
import numpy as np
import pandas as pd

REPO      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTRL, ARM = "L21", "L22"                 # control arm, capped arm
TARGETS   = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
EPS_FLOOR = 0.05                          # ϵband floor, calibrate_mcmc_ext.jl:535
EPS_Z     = 1.645                         # the band is 90%, not 95%
CAP_CM    = 0.1036209188                  # the bound L22 ran under
COLLAPSE_SIGMA = 3.0                      # "collapsed" verdict threshold, in target sigma
PARAMS    = ["thermal_alpha", "d2_steric_1", "d2_steric_2", "sd_steric", "rho_steric"]


def bias_path(tag):
    return os.path.join(REPO, f"outputs/postpred_{tag}_bias.csv")


def subsample_path(tag):
    return os.path.join(REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{tag}.csv")


def steric_eps():
    tg = pd.read_csv(TARGETS).dropna(subset=["steric"])
    e = np.maximum((tg.steric_hi - tg.steric_lo) / (2 * EPS_Z), EPS_FLOOR)
    return dict(zip(tg.year.astype(int), e))


def main():
    missing = [p for p in (bias_path(CTRL), bias_path(ARM)) if not os.path.exists(p)]
    if missing:
        sys.exit("ERROR: missing " + ", ".join(missing) +
                 f"\n  Run posterior_predictive_ladrillo.jl --tag={ARM} first "
                 f"(run_l22_postprocess.sh does it).")
    eps = steric_eps()
    print(f"\n{'='*78}\nTHE STERIC NOISE CAP: {CTRL} (free) vs {ARM} "
          f"(marginal bounded at {CAP_CM:.4f} cm)\n{'='*78}\n")

    b = {t: pd.read_csv(bias_path(t)) for t in (CTRL, ARM)}

    # ---- 1. the TE residual ------------------------------------------------
    print(f"1. THERMAL-EXPANSION RESIDUAL, in units of the steric target's own sigma\n")
    print(f"   {'year':>6} {'eps':>7} | {CTRL+' bias':>10} {CTRL+' sig':>9} | "
          f"{ARM+' bias':>10} {ARM+' sig':>9} | {'change':>9}")
    te = {t: b[t][b[t].component == "te"].set_index("year") for t in (CTRL, ARM)}
    yrs = sorted(set(te[CTRL].index) & set(te[ARM].index))
    last = None
    for y in yrs:
        e = eps[y]
        s1, s2 = te[CTRL].loc[y, "bias"] / e, te[ARM].loc[y, "bias"] / e
        print(f"   {y:>6} {e:7.4f} | {te[CTRL].loc[y,'bias']:+10.4f} {s1:+9.2f} | "
              f"{te[ARM].loc[y,'bias']:+10.4f} {s2:+9.2f} | {s2-s1:+9.2f}")
        last = (y, s1, s2)
    y, s1, s2 = last
    verdict = ("COLLAPSED -- the noise model was the cause. The depth split is now a question "
               "about the PROJECTION, not the fit."
               if abs(s2) < COLLAPSE_SIGMA else
               "STILL LARGE -- something other than the noise model holds TE up. The depth "
               "split is the live candidate.")
    print(f"\n   VERDICT at {y}: {abs(s1):.1f} sigma -> {abs(s2):.1f} sigma.  {verdict}")

    # ---- 2. where it went --------------------------------------------------
    print(f"\n2. WHERE THE RESIDUAL WENT -- posterior medians, and the shift priced in "
          f"units of\n   {CTRL}'s OWN posterior sd\n")
    sp = {t: subsample_path(t) for t in (CTRL, ARM)}
    if all(os.path.exists(v) for v in sp.values()):
        d = {t: pd.read_csv(sp[t]) for t in (CTRL, ARM)}
        for t in (CTRL, ARM):
            d[t]["steric_marginal"] = (d[t].sd_steric /
                                       np.sqrt(1 - d[t].rho_steric ** 2))
        print(f"   {'param':>16} {CTRL+' med':>12} {ARM+' med':>12} {'shift':>10} "
              f"{'in '+CTRL+' sd':>12}")
        for p in PARAMS + ["steric_marginal"]:
            if p not in d[CTRL] or p not in d[ARM]:
                print(f"   {p:>16}  -- absent from a subsample, skipped")
                continue
            m1, m2 = d[CTRL][p].median(), d[ARM][p].median()
            sd1 = d[CTRL][p].std()
            z = (m2 - m1) / sd1 if sd1 > 0 else np.nan
            print(f"   {p:>16} {m1:12.5f} {m2:12.5f} {m2-m1:+10.5f} {z:+12.2f}")
        mm = d[ARM]["steric_marginal"]
        print(f"\n   cap check: {ARM} marginal max {mm.max():.5f} vs cap {CAP_CM:.5f} "
              f"-> {'OK' if mm.max() <= CAP_CM * (1 + 1e-6) else 'VIOLATED'}"
              f" | median sits at {100*mm.median()/CAP_CM:.1f}% of the cap")
        print(f"   ⚠ a d2_steric shift of more than ~1 {CTRL} sd means the D2 basis absorbed "
              f"what the\n     AR(1) term no longer can -- prediction (iv), and it makes "
              f"'the noise model was\n     the cause' only HALF true.")
    else:
        print("   subsample(s) not written yet -- run postprocess_mcmc_ext.jl first.")

    # ---- 3. what else moved ------------------------------------------------
    print(f"\n3. WHAT ELSE MOVED (prediction iii: expect SOMETHING to look worse)\n")
    print(f"   {'component':>10} {'year':>6} | {CTRL+' bias':>10} {ARM+' bias':>10} "
          f"{'change':>9} {'|new|-|old|':>12}")
    for comp in sorted(set(b[CTRL].component)):
        c1 = b[CTRL][b[CTRL].component == comp].set_index("year")
        c2 = b[ARM][b[ARM].component == comp].set_index("year")
        for y in sorted(set(c1.index) & set(c2.index)):
            v1, v2 = c1.loc[y, "bias"], c2.loc[y, "bias"]
            print(f"   {comp:>10} {y:>6} | {v1:+10.4f} {v2:+10.4f} {v2-v1:+9.4f} "
                  f"{abs(v2)-abs(v1):+12.4f}")
    print(f"\n   (a positive |new|-|old| is a component the cap made worse -- name it, "
          f"do not\n    read it as a regression)\n")


if __name__ == "__main__":
    main()
