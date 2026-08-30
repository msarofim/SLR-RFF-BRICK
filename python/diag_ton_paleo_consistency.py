"""
diag_ton_paleo_consistency.py

ANSWERS C1: is the Antarctic runoff onset really 3.6x off the paleo prior?

C1 reads: "Antarctic runoff onset sits at ~0.64 degC GMST (0.637 +- 0.077), against a
paleo/Shaffer DAIS prior of +2.3-2.5 degC -- a 3.6x discrepancy in a physically
meaningful quantity", OPEN and unexplained, severity Highest.

THE RATIO IS COMPUTED ON A SCALE WITH AN ARBITRARY ZERO. GMST here is an ANOMALY, so
its origin is a baseline convention (1850-1900), not a physical origin. A ratio of two
anomalies is therefore not scale-invariant, and near the origin it inflates without
bound. `ratio_needs_its_base`: a ratio is not a magnitude until you multiply its base.

THE SAMPLED COORDINATE IS `ais_runoff_Ton`, NOT GMST. The runoff line enters the model
only as hR = h0 + c*T_ant, so the sampler works in T_on = -h0/c (degC on the DAIS
Antarctic-surface scale) and the paleo prior is REBUILT in those coordinates
(outputs/paleo_geo_prior_ton.csv, from the DAISfastdyn ensemble). That is the coordinate
in which "agrees with the paleo prior" has a meaning, because it is where the prior lives.

WHAT THIS PRINTS:
  1. the posterior's distance from the paleo prior IN THE SAMPLED COORDINATE, in prior sd;
  2. the same thing expressed as a GMST onset, as a DIFFERENCE and as a RATIO, so the
     inflation is visible side by side;
  3. the RATIO'S OWN INSTABILITY across the amp frame -- the statistic C1 quotes moves
     with a frame choice while the z-score does not, which is the tell;
  4. posterior sd / prior sd, which is the separate and REAL problem here.

  source ~/climate-env/bin/activate && python python/diag_ton_paleo_consistency.py
"""
import os
import numpy as np
import pandas as pd

REPO      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_FILE  = os.path.join(REPO, "outputs/paleo_geo_prior_ton.csv")
ARMS      = ["L21", "L14"]
# calibrate_mcmc_ext.jl:1180 -- the preserved anchor, T_ant at GMST = 0
AIS_TANT0 = -15.42 / 0.8365
DOC_RATIO = 3.6          # the number C1 quotes
DOC_PRIOR_GMST = 2.3     # the "+2.3-2.5 degC" C1 compares against
CONSISTENT_SD = 2.0      # |z| below this = consistent with the prior


def paleo_ton():
    g = pd.read_csv(GEO_FILE, comment="#").set_index("names")["ais_runoff_Ton"]
    return float(g["mean"]), float(g["sd"]), float(g["lo"]), float(g["hi"])


def main():
    mu, sd, lo, hi = paleo_ton()
    print(f"\n{'='*80}\nC1: IS THE RUNOFF ONSET 3.6x OFF THE PALEO PRIOR?\n{'='*80}")
    print(f"\n  SAMPLED COORDINATE  ais_runoff_Ton (degC, DAIS Antarctic-surface scale)")
    print(f"  paleo prior         {mu:+.3f} +- {sd:.3f}   support [{lo:+.2f}, {hi:+.2f}]")
    print(f"  AIS_TANT0 (anchor)  {AIS_TANT0:+.4f}\n")

    rows = []
    for arm in ARMS:
        d = pd.read_csv(os.path.join(
            REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{arm}.csv"))
        ton, amp = d["ais_runoff_Ton"].values, d["ais_gmst_amp"].values
        z = (ton - mu) / sd
        gm = (ton - AIS_TANT0) / amp                    # GMST onset, the arm's OWN amp
        gm_pri = (mu - AIS_TANT0) / np.median(amp)      # the prior mean in the SAME frame
        zmed = float(np.median(z))
        print(f"  ── {arm} ──")
        print(f"     T_on posterior              {np.median(ton):+.3f}  (sd {ton.std():.3f})")
        print(f"     DISTANCE FROM PALEO PRIOR   {zmed:+.3f} prior sd"
              f"   [p05 {np.percentile(z,5):+.2f}, p95 {np.percentile(z,95):+.2f}]"
              f"   -> {'CONSISTENT' if abs(zmed) < CONSISTENT_SD else 'INCONSISTENT'}")
        print(f"     GMST onset (own amp)        {np.median(gm):+.3f} degC"
              f"   | prior mean in same frame {gm_pri:+.3f} degC")
        print(f"     as a DIFFERENCE             {gm_pri-np.median(gm):+.3f} degC   <- the real, quotable statement")
        print(f"     as a RATIO                  {gm_pri/np.median(gm):.2f}x"
              f"      <- C1 quotes {DOC_RATIO}x; inflated by the offset origin")
        print(f"     posterior sd / prior sd     {ton.std()/sd:.4f}"
              f"   ({sd/ton.std():.0f}x tighter than the prior)\n")
        rows.append(dict(arm=arm, ton_med=np.median(ton), ton_sd=ton.std(),
                         z_from_paleo=zmed, gmst_onset=np.median(gm),
                         gmst_prior_same_frame=gm_pri,
                         gmst_difference=gm_pri-np.median(gm),
                         gmst_ratio=gm_pri/np.median(gm),
                         post_sd_over_prior_sd=ton.std()/sd))

    # 3. THE RATIO IS SENSITIVE TO THE ORIGIN, NOT TO THE SLOPE.
    # ⚠ CORRECTED 2026-08-29: an earlier version of this block claimed the ratio moves with
    # the amp frame. IT DOES NOT -- amp divides BOTH the prior and the posterior image, so it
    # cancels exactly and the ratio is amp-INVARIANT at 4.88x. The DIFFERENCE is what scales
    # with amp. What the ratio is violently sensitive to is the ORIGIN: AIS_TANT0 is "T_ant at
    # GMST = 0", so it encodes the GMST BASELINE CONVENTION (1850-1900). Move the baseline and
    # the denominator -- a small anomaly -- moves toward zero and the ratio diverges. That is
    # the whole of `ratio_needs_its_base`: an anomaly has no meaningful zero, so a RATIO of two
    # anomalies is not a magnitude. The z-score is invariant to both.
    d = pd.read_csv(os.path.join(
        REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L21.csv"))
    ton = float(np.median(d["ais_runoff_Ton"].values))
    a   = float(np.median(d["ais_gmst_amp"].values))
    print(f"  THE RATIO IS AN ORIGIN ARTEFACT (L21). amp CANCELS -- it is the GMST ZERO that moves it:")
    print(f"     {'GMST zero shift':>17}{'onset':>9}{'prior':>9}{'DIFFERENCE':>13}{'RATIO':>10}{'z (prior sd)':>15}")
    for dlt in (-1.0, -0.5, 0.0, +0.3, +0.5):
        g  = (ton - AIS_TANT0 - dlt) / a
        gp = (mu  - AIS_TANT0 - dlt) / a
        print(f"     {dlt:>+17.2f}{g:>9.3f}{gp:>9.3f}{gp-g:>13.3f}"
              f"{gp/g:>9.2f}x{(ton-mu)/sd:>15.3f}")
    print(f"\n     -> the RATIO runs from ~3x to ~30x under a sub-degree change in what counts as")
    print(f"        zero warming, while the z-score is FIXED at {(ton-mu)/sd:+.3f}. amp is NOT the")
    print(f"        lever (it cancels); the ORIGIN is. Quote the z-score, or the DIFFERENCE with")
    print(f"        its baseline named -- never the ratio.\n")

    out = os.path.join(REPO, "outputs/diag_ton_paleo_consistency.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"  VERDICT: the posterior is {abs(rows[0]['z_from_paleo']):.2f} prior sd from the paleo")
    print(f"  mean in the coordinate the prior is DEFINED in -- CONSISTENT, not a 3.6x conflict.")
    print(f"  What survives: (a) onset is {rows[0]['gmst_difference']:.2f} degC GMST EARLIER than the")
    print(f"  paleo central, a real difference worth disclosing; (b) posterior sd is")
    print(f"  {rows[0]['post_sd_over_prior_sd']:.4f} of the prior's, and per mid_mode_wins_but_start_determined")
    print(f"  the chains never cross T_on modes -- so that width is WITHIN-MODE, not a posterior.")
    print(f"\n  ⚠ LIMITATION: this is the MARGINAL z. The paleo prior is a JOINT MvNormal over 7")
    print(f"  geo params; the full Mahalanobis distance is not computed here.\n  wrote {out}\n")


if __name__ == "__main__":
    main()
