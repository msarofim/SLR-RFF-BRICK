"""IS THE OBSERVED-MINUS-CMIP6 AMPLIFICATION OFFSET NATURAL VARIABILITY, OR THE
OBSERVATIONAL PRODUCT CHOICE?

WHY THIS RUNS BEFORE ANY NAO/PDO WORK. scope_gis_amp_relax_tau.py found that relaxing
the law's 1.2864x level offset with tau ~ 25 yr improves the shipped model 1.52x under
Marcus's 2100 > 2300 weighting, and Marcus's proposed mechanism is that the observed
excess is mostly NAO/PDO -- both decadal, which would make a fast tau physical rather
than fitted. That is a good hypothesis. It has a confound of LARGER magnitude sitting
in front of it:

    the anchor 1.9222 is the MEAN of three products spanning 1.510-2.285 (1.513x),
    while the offset being explained is 1.286x,

and Berkeley Earth ALONE lands on CMIP6's own south secant (1.510 vs 1.4942, 1.011x).
Under a BE anchor there is no discrepancy for variability to explain. Fitting a
physical timescale to what may be a product-processing difference is the failure mode
this file exists to rule in or out first.

THE TWO TESTS, and what each would show

  T1  ROLLING 30-yr AMPLIFICATION per product. Variability predicts an OSCILLATION
      whose amplitude is comparable to the offset and whose decorrelation time is
      decadal. That decorrelation time is a MEASUREMENT of tau -- independent of
      ISMIP6, which is what would make tau a prediction rather than a fit. A product
      artifact instead predicts a roughly CONSTANT per-product offset: the three
      curves stay separated by their own systematic gaps at every window.

  T2  THE DISCRIMINATOR. Variability lives in the real world, not in a processing
      chain, so the three products should show the SAME excursions at the SAME times:
      high between-product correlation of the rolling amp, with the spread in LEVEL.
      A product artifact predicts the opposite -- the products disagree in the
      wiggles, not just the mean.

  Neither test can be passed by construction; both have a stated failure direction.

⚠ NOT TESTED HERE: whether the excursions, if real, are NAO/PDO specifically. That
needs the indices, which are not in this repo.

WRITES outputs/diag_gis_amp_variability{,_rolling}.csv
  python3 python/diag_gis_amp_variability.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import build_t_gis as BTG  # noqa: E402

OBS = os.path.join(REPO, "data/observations")
ALLPROD = os.path.join(OBS, "t_gis_zones_allproducts.csv")
OUT = os.path.join(REPO, "outputs/diag_gis_amp_variability.csv")
OUT_ROLL = os.path.join(REPO, "outputs/diag_gis_amp_variability_rolling.csv")

ZONE = "south"
PRODUCTS = ["HadCRUT5", "BerkeleyEarth", "GISTEMP"]
WIN = 30                       # yr, the rolling window — decadal-mode scale
R_ANCHOR_CMIP6 = 1.4942493826789536
OBS_AMP_FULL = 1.9221976385152952
LEVEL_OFFSET = OBS_AMP_FULL / R_ANCHOR_CMIP6


def secant_amp(x, y):
    """The repo's estimator: through-origin secant, x^2-weighted. Same as
    diag_gis_amp_anchor.amp_and_anchor so the rolling numbers are comparable to the
    committed table rather than a second definition of the same word."""
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 20:
        return np.nan
    xv, yv = x[ok], y[ok]
    return float((xv * yv).sum() / (xv ** 2).sum())


def main():
    zp = pd.read_csv(ALLPROD).set_index("year")
    ## The GLOBAL series are rebuilt through build_t_gis's own loader + area-weighted
    ## annual mean + per-product baseline, exactly as build_t_gis.main does it. Not
    ## re-derived here: a second definition of "global mean anomaly" would make the
    ## rolling amps incomparable to the committed table they are being read against.
    glob = {}
    for p in PRODUCTS:
        v, yr, mo, lat, lon = BTG.PRODUCTS[p]()
        glob[p] = BTG.rebase(BTG.global_annual(v, yr, mo, lat, lon),
                             BTG.PRODUCT_BASELINE[p])

    rows = []
    for p in PRODUCTS:
        gser = glob[p]
        z = zp[f"{p}_{ZONE}"]
        yrs = sorted(set(gser.index) & set(z.index))
        gv = gser.reindex(yrs); zv = z.reindex(yrs)
        for y1 in range(min(yrs) + WIN - 1, max(yrs) + 1):
            y0 = y1 - WIN + 1
            m = (np.array(yrs) >= y0) & (np.array(yrs) <= y1)
            a = secant_amp(gv.to_numpy(float)[m], zv.to_numpy(float)[m])
            rows.append(dict(product=p, year_end=y1, year0=y0, amp=a))
    roll = pd.DataFrame(rows).dropna(subset=["amp"])
    roll.to_csv(OUT_ROLL, index=False)

    print(f"diag_gis_amp_variability — {ZONE} zone, {WIN}-yr rolling secant amp\n")
    print(f"  the anchor 1.9222 is the MEAN of the three full-record product amps")
    print(f"  CMIP6's own south secant at the anchor = {R_ANCHOR_CMIP6:.4f}")
    print(f"  the offset being explained = {LEVEL_OFFSET:.4f}x\n")

    print("=== T1 — rolling amplification, per product ===\n")
    print(f"  {'product':16}{'n win':>7}{'median':>9}{'min':>8}{'max':>8}"
          f"{'max/min':>9}{'sd':>8}{'sd/med':>8}")
    summ = []
    for p in PRODUCTS:
        v = roll[roll["product"] == p].amp
        summ.append(dict(product=p, n=len(v), median=v.median(), lo=v.min(),
                         hi=v.max(), sd=v.std()))
        print(f"  {p:16}{len(v):7d}{v.median():9.3f}{v.min():8.3f}{v.max():8.3f}"
              f"{v.max()/v.min():9.3f}{v.std():8.3f}{v.std()/v.median():8.3f}")

    ## Decorrelation time of the rolling-amp anomaly: e-folding lag of its
    ## autocorrelation. THE ROLLING WINDOW ITSELF IMPOSES autocorrelation out to WIN
    ## years, so a value at or below WIN is NOT evidence of a decadal mode -- it is
    ## the window. Only a value WELL ABOVE WIN would be.
    print(f"\n  decorrelation e-folding lag of the rolling-amp anomaly")
    print(f"  (⚠ the {WIN}-yr window alone forces ~{WIN} yr of autocorrelation — "
          f"only a value\n     WELL ABOVE {WIN} is evidence of a real decadal mode)\n")
    print(f"  {'product':16}{'e-fold lag (yr)':>18}")
    for p in PRODUCTS:
        v = roll[roll["product"] == p].amp.to_numpy(float)
        a = v - v.mean()
        ac = np.array([np.corrcoef(a[:-k], a[k:])[0, 1] if k else 1.0
                       for k in range(len(a) // 2)])
        below = np.where(ac < np.exp(-1.0))[0]
        lag = int(below[0]) if len(below) else len(ac)
        print(f"  {p:16}{lag:18d}")

    print(f"\n=== T2 — THE DISCRIMINATOR: do the products WIGGLE together? ===\n")
    piv = roll.pivot(index="year_end", columns="product", values="amp").dropna()
    print(f"  {len(piv)} common windows, {piv.index.min()}-{piv.index.max()}\n")
    print(f"  LEVEL: between-product spread of the window-median amp")
    med = piv.median()
    print(f"    " + "   ".join(f"{p} {med[p]:.3f}" for p in PRODUCTS)
          + f"    max/min {med.max()/med.min():.3f}x")
    print(f"\n  SHAPE: correlation of the DETRENDED-BY-MEAN anomalies")
    an = piv - piv.mean()
    print(f"  {'':16}" + "".join(f"{p:>16}" for p in PRODUCTS))
    for a_ in PRODUCTS:
        print(f"  {a_:16}" + "".join(f"{an[a_].corr(an[b_]):16.3f}"
                                     for b_ in PRODUCTS))
    rs = [an[a_].corr(an[b_]) for i, a_ in enumerate(PRODUCTS)
          for b_ in PRODUCTS[i + 1:]]
    print(f"\n  mean off-diagonal r = {np.mean(rs):.3f}")
    print(f"    r near 1  => the products SEE THE SAME EXCURSIONS: real-world "
          f"variability,\n                 and the level spread is a separate "
          f"systematic offset.")
    print(f"    r near 0  => the products DISAGREE ABOUT THE WIGGLES: the spread is "
          f"processing,\n                 and a decadal timescale fitted to it is "
          f"fitting the products.")

    pd.DataFrame(summ).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT_ROLL, REPO)}, {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
