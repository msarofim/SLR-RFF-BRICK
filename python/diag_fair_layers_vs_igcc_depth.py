"""
diag_fair_layers_vs_igcc_depth.py

TASK 3 sub-test (2) of notes/handoff_2026-08-29_te_residual_and_the_ohc_depth_question.md:
COMPARE FaIR's LAYER SPLIT TO AN OBSERVED DEPTH-RESOLVED OHC PRODUCT.

The handoff's phrasing -- "if FaIR's layer-0 share tracks the observed 0-700 m
share over 1993-2025, the mapping has empirical support" -- CANNOT BE TAKEN
LITERALLY, and saying so is the first result. FaIR's box 0 is 45 m thick
(diag_seawater_alpha_layer_mapping.py, 841 calib 1.6.0 configs), nothing like
the observed 0-700 m layer, so "layer-0 share vs 0-700 m share" would compare
two different reservoirs and the disagreement would be guaranteed rather than
informative. The like-for-like question is instead:

    what fraction of the ocean heat uptake sits ABOVE 700 m,
    in FaIR and in the observations, over the SAME years,
    referenced to the SAME baseline?

FaIR's side needs box 2 (median 250-1217 m) split at 700 m. Within a box the
EBM is well-mixed by construction, so heat density is uniform in depth and the
split is the depth fraction f = (700 - 250)/(1217 - 250). f is carried through
at the p5/p50/p95 of the implied depths, not as a point.

⚠ THE STRUCTURAL CAVEAT, STATED RATHER THAN BURIED. FaIR's three boxes span a
median 1217 m [638, 2296], while the observations put ~7.5% of the uptake below
2000 m and part of the 700-2000 m band below 1217 m. FaIR's box 2 therefore
STANDS IN for everything below 250 m rather than representing 250-1217 m
literally. The level comparison inherits that; the SHAPE comparison (how fast
the above-700 share declines) does not, and is the quantity the TE argument
actually turns on.

⚠ BASELINES. IGCC's ocean columns are anomalies referenced to 1971; the FaIR
layer series is referenced to 1850-1900. Shares of two differently-referenced
increments are not comparable, so FaIR is REBASED TO 1971 here before any share
is formed.

⚠ THE OBSERVED DEEP COLUMN IS PARTLY PRESCRIBED, NOT MEASURED. IGCC's
`ocean_2000-6000m` rises by EXACTLY 1.15 ZJ every year over 1993-2024 -- 32
increments, standard deviation 0.000000, one unique value. That is an assumed
constant rate, and reading it as data would let an assumption drive the result
(suspicious uniformity is a code path, not nature, until disproven). The
0-700 and 700-2000 columns are genuine, with 31 and 32 distinct increments.

So THE PRIMARY COMPARISON HERE USES THE 0-2000 m BAND ONLY, which is also the
more like-for-like one: FaIR's whole column ends at a median 1217 m, i.e. inside
0-2000, so it has no >2000 m reservoir to compare against in the first place.
The full-depth version is reported alongside as the secondary number.

⚠ SMALL DENOMINATORS. Both shares divide by a quantity that is zero at the 1971
baseline. Years are admitted only where the observed full-depth increment
exceeds SNR_MIN times its own reported 1-sigma error -- a threshold from the
data's own uncertainty, not a hand-picked year.

  source ~/climate-env/bin/activate && python python/diag_fair_layers_vs_igcc_depth.py
"""
import os
import sys
import numpy as np
import pandas as pd

# ---- provenance / labels ---------------------------------------------------
REPO        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIR_REPO   = os.path.join(os.path.dirname(REPO), "FaIRtoFrEDI")
FAIR_LAYERS = os.path.join(FAIR_REPO, "fair_outputs", "diag_fair_ohc_layers_full.csv")
FAIR_CALIB  = os.path.join(FAIR_REPO, "calibration_v160",
                           "calibrated_constrained_parameters_1.6.0.csv")
IGCC_CSV    = os.path.join(REPO, "data/observations/raw/igcc2024",
                           "ClimateIndicator-data-2cd2409/data/earth_energy_imbalance",
                           "earth_energy_imbalance.csv")
OUT_CSV     = os.path.join(REPO, "outputs", "diag_fair_layers_vs_igcc_depth.csv")

MODEL_LABEL = "FaIR 2.2.4 (calib 1.6.0), ssp245harm, ensemble mean"
OBS_LABEL   = "IGCC 2024 earth_energy_imbalance.csv (Palmer & von Schuckmann), ZJ vs 1971"

# ---- analysis constants ----------------------------------------------------
SPLIT_DEPTH_M   = 700.0     # the depth the observations resolve
BASE_YEAR       = 1971      # IGCC's own reference; FaIR is rebased onto it
SNR_MIN         = 3.0       # admit a year only if obs full-depth > SNR_MIN * its 1-sigma
TREND_Y0        = 1993      # altimetry era, matching the handoff's window
SEC_PER_YEAR    = 60 * 60 * 24 * 365.25
RHO_SW, CP_SW   = 1027.0, 3990.0
OCEAN_FRACTION  = 0.708
ZJ_PER_1E22J    = 10.0      # 1e22 J = 10 ZJ


def implied_depth_edges():
    """Median and p5/p95 cumulative box edges (m of ocean) from calib 1.6.0."""
    d = pd.read_csv(FAIR_CALIB, index_col=0)
    C = d[[f"ocean_heat_capacity[{k}]" for k in range(3)]].values
    h = C * SEC_PER_YEAR / (RHO_SW * CP_SW) / OCEAN_FRACTION
    edges = np.concatenate([np.zeros((len(C), 1)), np.cumsum(h, axis=1)], axis=1)
    return edges


def box2_fraction_above(edges, depth):
    """Fraction of box 2 lying above `depth`, per config, clipped to [0, 1].
    Uniform heat density within a box: the EBM's box IS well-mixed."""
    top, bot = edges[:, 2], edges[:, 3]
    return np.clip((depth - top) / (bot - top), 0.0, 1.0)


def main():
    for p in (FAIR_LAYERS, FAIR_CALIB, IGCC_CSV):
        if not os.path.exists(p):
            sys.exit(f"ERROR: missing {p}")
    print(f"\n{'='*80}\nFaIR LAYER SPLIT vs AN OBSERVED DEPTH-RESOLVED OHC PRODUCT")
    print(f"  model: {MODEL_LABEL}\n  obs:   {OBS_LABEL}")
    print(f"  split at {SPLIT_DEPTH_M:.0f} m | both referenced to {BASE_YEAR}\n{'='*80}\n")

    # ---- FaIR side ---------------------------------------------------------
    edges = implied_depth_edges()
    e50 = np.median(edges, axis=0)
    f_all = box2_fraction_above(edges, SPLIT_DEPTH_M)
    f5, f50, f95 = np.percentile(f_all, [5, 50, 95])
    print(f"  box edges (median, m): 0 - {e50[1]:.0f} - {e50[2]:.0f} - {e50[3]:.0f}")
    print(f"  fraction of box 2 above {SPLIT_DEPTH_M:.0f} m: "
          f"f = {f50:.3f}  [p5 {f5:.3f}, p95 {f95:.3f}]")
    print(f"  ⚠ FaIR's column ends at a median {e50[3]:.0f} m; the observations place")
    print(f"    heat below that, so box 2 stands in for ALL water below {e50[2]:.0f} m.\n")

    fa = pd.read_csv(FAIR_LAYERS).set_index("year")
    if BASE_YEAR not in fa.index:
        sys.exit(f"ERROR: FaIR layer series has no {BASE_YEAR} row to rebase on")
    fa = (fa[["H0", "H1", "H2"]] - fa.loc[BASE_YEAR, ["H0", "H1", "H2"]]) * ZJ_PER_1E22J

    # ---- obs side ----------------------------------------------------------
    ig = pd.read_csv(IGCC_CSV)
    ig["year"] = ig["timebound_lower"].astype(int)
    ig = ig.set_index("year")
    obs_tot = ig["ocean_full-depth"]
    obs_err = ig["ocean_full-depth_error"].abs()
    ok = obs_tot > SNR_MIN * obs_err
    yrs = [y for y in ig.index[ok] if y in fa.index]
    print(f"  years admitted by the SNR gate (obs full-depth > {SNR_MIN:.0f}x its own "
          f"1-sigma): {min(yrs)}-{max(yrs)}, n={len(yrs)}")
    print(f"  (rejected: {int((~ok).sum())} early years where the 1971-referenced "
          f"denominator is near zero)\n")

    rows = []
    for y in yrs:
        H0, H1, H2 = fa.loc[y, ["H0", "H1", "H2"]]
        tot_f = H0 + H1 + H2
        s_f50 = (H0 + H1 + f50 * H2) / tot_f
        s_f5 = (H0 + H1 + f5 * H2) / tot_f
        s_f95 = (H0 + H1 + f95 * H2) / tot_f
        o07, o72 = ig.loc[y, "ocean_0-700m"], ig.loc[y, "ocean_700-2000m"]
        rows.append(dict(year=y, fair_above700=s_f50, fair_above700_p5=min(s_f5, s_f95),
                         fair_above700_p95=max(s_f5, s_f95),
                         obs_above700_of2000=o07 / (o07 + o72),      # PRIMARY
                         obs_above700_offull=o07 / obs_tot.loc[y],   # secondary
                         fair_total_ZJ=tot_f, obs_total_ZJ=obs_tot.loc[y],
                         obs_0_2000_ZJ=o07 + o72))
    r = pd.DataFrame(rows).set_index("year")

    print(f"  SHARE OF THE UPTAKE ABOVE {SPLIT_DEPTH_M:.0f} m -- obs on the 0-2000 m band")
    print(f"  {'year':>6} {'FaIR (p5-p95 on f)':>30} {'obs 0-2000':>11} {'diff':>7}"
          f" {'obs full':>9} {'FaIR ZJ':>8} {'obs ZJ':>7}")
    for y in [c for c in (1995, 2000, 2010, 2020, 2023) if c in r.index]:
        q = r.loc[y]
        print(f"  {y:>6}   {q.fair_above700:6.3f} [{q.fair_above700_p5:.3f}, "
              f"{q.fair_above700_p95:.3f}] {q.obs_above700_of2000:11.3f} "
              f"{q.fair_above700 - q.obs_above700_of2000:+7.3f} "
              f"{q.obs_above700_offull:9.3f} {q.fair_total_ZJ:8.0f} "
              f"{q.obs_0_2000_ZJ:7.0f}")

    # ---- the SHAPE test: how fast does each share decline? ------------------
    tw = r.loc[r.index >= TREND_Y0]

    def slope_se(v):
        """OLS slope in %-points per decade, with its standard error. A SIGN
        DISAGREEMENT IS A CLAIM AND NEEDS THE BAR (curvature_needs_an_error_bar):
        the observed share is a noisy ratio and 30-odd years is not many."""
        x = tw.index.values.astype(float)
        y = v.values.astype(float)
        n = len(x)
        b, a = np.polyfit(x, y, 1)
        resid = y - (a + b * x)
        s2 = float(resid @ resid) / (n - 2)
        se = np.sqrt(s2 / float(((x - x.mean()) ** 2).sum()))
        return b * 1000.0, se * 1000.0

    bf, sf = slope_se(tw.fair_above700)
    bo, so = slope_se(tw.obs_above700_of2000)
    bofull, sofull = slope_se(tw.obs_above700_offull)
    b5, _ = slope_se(tw.fair_above700_p5)
    b95, _ = slope_se(tw.fair_above700_p95)
    print(f"\n  DECLINE IN THE ABOVE-{SPLIT_DEPTH_M:.0f} m SHARE, {TREND_Y0}-{tw.index.max()}"
          f" (OLS, %-points per decade, +/- 1 se):")
    print(f"     FaIR  {bf:+6.2f} +/- {sf:.2f}   "
          f"[f-sensitivity across p5-p95: {b5:+.2f} to {b95:+.2f}]")
    print(f"     obs   {bo:+6.2f} +/- {so:.2f}   [0-2000 m band, the measured one]")
    print(f"     obs   {bofull:+6.2f} +/- {sofull:.2f}   [vs full depth -- steeper only "
          f"because the >2000 m column is a PRESCRIBED 1.15 ZJ/yr]")
    zdiff = (bf - bo) / np.sqrt(sf ** 2 + so ** 2)
    print(f"     difference {bf - bo:+.2f} +/- {np.sqrt(sf**2 + so**2):.2f}"
          f"  ->  {abs(zdiff):.1f} sigma"
          f"   [{'SIGN DISAGREEMENT SURVIVES ITS BAR' if abs(zdiff) > 2 and bf * bo < 0 else 'NOT RESOLVED AT 2 SIGMA' if abs(zdiff) <= 2 else 'DIFFERENT BUT SAME SIGN'}]")
    print(f"     ⚠ the FaIR series is an ENSEMBLE MEAN, so its se is a fit residual,")
    print(f"       NOT a sampling uncertainty on the model. The obs bar is the real one.")
    print(f"\n  The LEVEL comparison inherits the structural caveat above; the DECLINE")
    print(f"  RATE is the quantity a one-coefficient TE form has to get right, since")
    print(f"  that form credits deep heat at an efficiency calibrated when heat was")
    print(f"  shallower.")

    r.to_csv(OUT_CSV)
    print(f"\n  wrote {OUT_CSV}\n")


if __name__ == "__main__":
    main()
