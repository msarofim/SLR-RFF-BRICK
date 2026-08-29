"""
diag_ohc_partition_robustness.py

DOES THE OBSERVED DECLINE IN THE ABOVE-700 m SHARE SURVIVE (a) A SECOND
PRODUCT AND (b) A DIFFERENT WINDOW?

This gates a build decision. diag_fair_layers_vs_igcc_depth.py found FaIR's
above-700 m share trending +1.07 +/- 0.34 %-points per decade against IGCC's
-1.75 +/- 0.28 over 1993-2024, a 6.3 sigma sign disagreement that no placement
of FaIR's box boundaries can close. That result is the whole argument for
replacing FaIR's box->depth mapping with a generative "aging" module -- and it
rests on ONE product over ONE window, so it gets tested before anything is
built on it.

TWO THREATS, AND THEY ARE DIFFERENT:

  (a) PRODUCT. IGCC's ocean columns are a multi-product compilation (Palmer /
      von Schuckmann). NCEI is one of its INPUTS, so agreement is a weak check
      and only DISAGREEMENT is strongly informative. Stated rather than sold as
      independence.

  (b) OBSERVING SYSTEM, which is the bigger one. NCEI publishes annual 0-700 m
      from 1955 but annual 0-2000 m only from 2005 -- it does not consider the
      annual 700-2000 m layer well enough observed before Argo. IGCC's
      700-2000 m column does reach back to 1971, but over most of that length
      it is a reconstruction. A share trend fitted across 1993-2024 therefore
      spans a change of observing system, and a spurious trend in the
      reconstructed part would look exactly like a physical deepening.

METHOD -- AND THE FIRST VERSION OF THIS SCRIPT GOT IT WRONG, WHICH IS WHY THE
ESTIMATOR IS SPELLED OUT. Rebasing each product to a common year t0 and fitting
a trend to the resulting share gives, on IGCC alone, -1.81 %pts/decade for
t0=1971 and +9.41 for t0=2005 -- opposite signs from the same data. The cause
is the trap that has bitten this project repeatedly: the denominator is ZERO at
t0 by construction, so the first years of any recently-rebased window are a
ratio of two near-zero numbers, and their swing IS the fitted trend.

The estimator used instead is BASELINE-FREE:

    partition(window) = [Q_0-700(t1) - Q_0-700(t0)] / [Q_0-2000(t1) - Q_0-2000(t0)]

i.e. the fraction of the heat gained ACROSS the window that went above 700 m.
Adding any constant to either series leaves it unchanged, so it does not care
what climatology a product references -- which is exactly what makes NCEI and
IGCC comparable at all. Deepening then shows up as this fraction being SMALLER
in a later window than an earlier one, with no ratio of small numbers anywhere.

Its standard error comes from the ANNUAL INCREMENTS by the delta method, since
the increments are what carry independent information; the cumulative levels do
not, and regressing one cumulative series on another would give an se that is
optimistic by a large and unknown factor.

⚠ POWER. The Argo window is 20 years. Where a window cannot separate the
candidate partitions, this says so rather than reporting a null (no_power_null).

  source ~/climate-env/bin/activate && python python/diag_ohc_partition_robustness.py
"""
import os
import numpy as np
import pandas as pd

REPO   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IGCC   = os.path.join(REPO, "data/observations/raw/igcc2024",
                      "ClimateIndicator-data-2cd2409/data/earth_energy_imbalance",
                      "earth_energy_imbalance.csv")
NCEI_D = os.path.join(REPO, "data/observations/raw/ncei_ohc")
FAIR   = os.path.join(os.path.dirname(REPO), "FaIRtoFrEDI", "fair_outputs",
                      "diag_fair_ohc_layers_full.csv")

SPLIT_M      = 700.0
SNR_MIN      = 3.0
ARGO_Y0      = 2005      # NCEI's own start for annual 0-2000 m
IGCC_Y0      = 1993      # the window the original finding used
ZJ_PER_1E22J = 10.0
FAIR_F       = 0.441     # fraction of FaIR box 2 above 700 m (median implied depths)
REF_SLOPE    = -1.75     # the IGCC 1993-2024 slope this check is testing, %pts/decade


def partition(top, tot, y0, y1):
    """Fraction of the heat gained between y0 and y1 that went above 700 m,
    with a delta-method se from the annual increments. Baseline-free."""
    yrs = [y for y in range(y0, y1 + 1) if y in top.index and y in tot.index]
    if len(yrs) < 6:
        return None
    t0, t1 = yrs[0], yrs[-1]
    dtop, dtot = top.loc[t1] - top.loc[t0], tot.loc[t1] - tot.loc[t0]
    if dtot <= 0:
        return None
    f = dtop / dtot
    # se: propagate the scatter of the annual increments through f = sum(a)/sum(b)
    a = top.loc[yrs].diff().dropna().values
    b = tot.loc[yrs].diff().dropna().values
    n = len(a)
    va, vb = a.var(ddof=1), b.var(ddof=1)
    cab = np.cov(a, b)[0, 1]
    sa, sb = a.sum(), b.sum()
    var_f = (f ** 2) * (n * va / sa ** 2 + n * vb / sb ** 2 - 2 * n * cab / (sa * sb))
    return f, np.sqrt(max(var_f, 0.0)), t0, t1, n


def main():
    print(f"\n{'='*80}\nIS THE OBSERVED DEEPENING ROBUST? — the gate on the aging-module build")
    print(f"  partition = fraction of the heat GAINED ACROSS a window that went")
    print(f"              above {SPLIT_M:.0f} m.  Baseline-free; deepening = a SMALLER")
    print(f"              number in a later window.\n{'='*80}\n")

    ig = pd.read_csv(IGCC)
    ig["year"] = ig.timebound_lower.astype(int)
    ig = ig.set_index("year")
    ig_top = ig["ocean_0-700m"]
    ig_tot = ig["ocean_0-700m"] + ig["ocean_700-2000m"]     # the MEASURED band

    def rd(f):
        d = pd.read_csv(os.path.join(NCEI_D, f), sep=r"\s+")
        d["year"] = d.YEAR.astype(float).astype(int)
        return d.set_index("year")
    n7, n20 = rd("h22-w0-700m.dat"), rd("h22-w0-2000m.dat")
    nc_top = (n7.WO * ZJ_PER_1E22J).reindex(n20.index)      # align to the shorter span
    nc_tot = n20.WO * ZJ_PER_1E22J
    print(f"  NCEI spans: 0-700 m {n7.index.min()}-{n7.index.max()} | "
          f"0-2000 m {n20.index.min()}-{n20.index.max()}")
    print(f"  ⚠ the 0-2000 m span IS the observing-system caveat: NCEI publishes no")
    print(f"    annual 700-2000 m layer before Argo, while IGCC's reaches back to 1971")
    print(f"    as a reconstruction.\n")

    fa = pd.read_csv(FAIR).set_index("year")[["H0", "H1", "H2"]] * ZJ_PER_1E22J
    fa_top = fa.H0 + fa.H1 + FAIR_F * fa.H2
    fa_tot = fa.H0 + fa.H1 + fa.H2

    WINDOWS = [(1971, 1992), (1993, 2004), (2005, 2024), (1993, 2024), (1971, 2024)]
    SERIES = [("IGCC", ig_top, ig_tot), ("NCEI", nc_top, nc_tot),
              ("FaIR", fa_top, fa_tot)]
    rows = []
    print(f"  {'window':>11} {'IGCC':>18} {'NCEI':>18} {'FaIR':>18}")
    for y0, y1 in WINDOWS:
        cells = []
        for nm, top, tot in SERIES:
            r = partition(top, tot, y0, y1)
            if r is None:
                cells.append(f"{'--':>18}")
                continue
            f, se, t0, t1, n = r
            cells.append(f"{f:12.3f} +/-{se:5.3f}")
            rows.append(dict(product=nm, y0=t0, y1=t1, n=n, partition=f, se=se))
        print(f"  {f'{y0}-{y1}':>11} " + " ".join(cells))

    r = pd.DataFrame(rows)
    print(f"\n  DEEPENING TEST — is the partition SMALLER in the recent window than the")
    print(f"  early one, within each product?\n")
    for nm in ("IGCC", "FaIR"):
        e = r[(r["product"] == nm) & (r.y0 == 1971) & (r.y1 == 1992)]
        l = r[(r["product"] == nm) & (r.y0 == 2005)]
        if len(e) and len(l):
            d = float(l.partition.iloc[0] - e.partition.iloc[0])
            sd = float(np.hypot(l.se.iloc[0], e.se.iloc[0]))
            verdict = ("DEEPENS" if d < 0 and abs(d) > 2 * sd else
                       "SHOALS" if d > 0 and abs(d) > 2 * sd else "NOT RESOLVED")
            print(f"     {nm}: 1971-1992 {float(e.partition.iloc[0]):.3f} -> "
                  f"2005-2024 {float(l.partition.iloc[0]):.3f}  "
                  f"change {d:+.3f} +/- {sd:.3f}  [{verdict}]")
    ig05 = r[(r["product"] == "IGCC") & (r.y0 == 2005)]
    nc05 = r[(r["product"] == "NCEI") & (r.y0 == 2005)]
    if len(ig05) and len(nc05):
        d = float(nc05.partition.iloc[0] - ig05.partition.iloc[0])
        sd = float(np.hypot(nc05.se.iloc[0], ig05.se.iloc[0]))
        print(f"\n  PRODUCT AGREEMENT over the Argo window: NCEI - IGCC = {d:+.3f} "
              f"+/- {sd:.3f}"
              f"  [{'AGREE' if abs(d) <= 2 * sd else 'DISAGREE'}]")
        print(f"     ⚠ NCEI is an INPUT to IGCC's compilation, so agreement is a weak")
        print(f"       check; disagreement would have been the informative outcome.")

    out = os.path.join(REPO, "outputs", "diag_ohc_partition_robustness.csv")
    r.to_csv(out, index=False)
    print(f"\n  wrote {out}\n")


if __name__ == "__main__":
    main()
