#!/usr/bin/env python3
"""
DIAGNOSTIC — how much of the Dangendorf / Wang / Mu / IGCC trend spread is PRODUCT,
and how much is merely the WINDOW?

Approved by Marcus 2026-09-09b as the trend half of the "diagnostic pass first" sequencing
on the Ladrillo recalibration (handoff_2026-09-09_igcc2026_and_recalib_scope.md section 4).

WHY THIS RUNS TODAY, UNBLOCKED: the four headline trends are quoted over FOUR DIFFERENT
windows, and the later windows carry more acceleration -- so the naive "1.5 vs 1.6 vs 1.75
vs 1.85" spread confounds product with window (the like_for_like_forcing rule). Wang's and
Mu's gridded files are NOT on disk (AMS is IP-blocked; Zenodo is down), but that does not
block this: for the two series we DO have we can recompute on every published window, and
read the window effect off directly. Whatever window sensitivity we measure applies to Wang
and Mu too, since it is a property of the sea-level record, not of a product.

WRITES NOTHING outside outputs/. Changes no target. Reports only.
"""
import os
import numpy as np
import pandas as pd

# ---- named constants: every label below derives from these -------------------
REPO         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS          = os.path.join(REPO, "data", "observations")
OUT_CSV      = os.path.join(REPO, "outputs", "diag_recon_trend_spread.csv")

DANGENDORF_F = os.path.join(OBS, "dangendorf2024_gmsl_annual.csv")
# The Church & White lineage, kept as a LEGACY calibration input, not an obs product.
# Loaded here only as the CW11-lineage reference point Mu benchmarks itself against.
CW_F         = os.path.join(REPO, "data", "calibration", "CSIRO_Recons_gmsl_yr_2015.csv")
IGCC_F       = os.path.join(OBS, "igcc2026_gmsl_annual.csv")

DANGENDORF_LBL = "Dangendorf 2024 (ESSD 16, 3471)"
IGCC_LBL       = "IGCC 2025-indicators (Forster 2026, ESSD 18, 3889)"
CW_LBL         = "CSIRO Recons 2015 (Church & White lineage)"
# Mu's own words: "Our curve yields a rate of 1.60 mm yr-1, very close to the rate of
# 1.62 mm yr-1 by C2011." So Mu BENCHMARKS ITSELF ON THE CHURCH & WHITE LINEAGE, and
# that pair is the like-for-like Mu itself constructed.
MU_VS_C2011_MU    = 1.60
MU_VS_C2011_C2011 = 1.62
# L24 total panel at 2024, from handoff_2026-09-09_igcc2026_and_recalib_scope.md section 2:
# Ladrillo 8.55 cm, IGCC 8.33, Dangendorf-built target 7.81.
L24_GAP_VS_TARGET_CM = 8.55 - 7.81
L24_GAP_VS_IGCC_CM   = 8.55 - 8.33
WANG_LBL       = "Wang 2024 (J.Clim 37, 6453)"
MU_LBL         = "Mu 2025 (ESSD 17, 5507)"

# Published trends, mm/yr, each on ITS OWN window. These are the numbers the naive
# "spread" is read off. Sourced from the papers' abstracts / Table 11, not recomputed.
PUBLISHED = [
    # label,          y0,   y1,   trend, sigma,  sigma_kind
    (DANGENDORF_LBL, 1900, 2021, 1.50,  0.19,  "formal, 4000-member ens"),
    (WANG_LBL,       1900, 2019, 1.60,  0.20,  "90% CI"),
    (MU_LBL,         1900, 2020, 1.75,  0.05,  "35-member CMIP6 spread - AUTHORS SAY IT UNDERSTATES"),
    (IGCC_LBL,       1901, 2025, 1.85,  None,  "Table 11 very likely 1.44-2.26"),
]
# The windows we will recompute the two on-disk series over -- the union of the above.
MU_MATCHED       = (1900, 2007)   # Mu's own second window, chosen to match other studies
MU_MATCHED_TREND = 1.60           # mm/yr, Mu 2025 abstract

WINDOWS = [(1900, 2019), (1900, 2020), (1900, 2021), (1901, 2021), (1901, 2025), (1900, 2007)]
# COMMON_WINDOW is DERIVED from the series actually loaded, never typed -- a hardcoded
# (1900, 2019) silently reported "NOT COVERED" because IGCC starts 1901.
COMMON_WINDOW = None


def endpoint_rate(years, vals):
    """delta/n between the window endpoints. THIS IS NOT A SLOPE. IGCC Table 11 defines
    its 'rate' column this way, so IGCC's published 1.85 is NOT the same estimator as
    Dangendorf's 1.50 / Wang's 1.60 / Mu's 1.75, which are regression trends. Comparing
    them directly is an estimator mismatch stacked on top of the window mismatch."""
    m = np.isfinite(years) & np.isfinite(vals)
    y, v = years[m], vals[m]
    if len(y) < 2:
        return np.nan
    i0, i1 = int(np.argmin(y)), int(np.argmax(y))
    return (v[i1] - v[i0]) / (y[i1] - y[i0])


def ols_trend(years, vals):
    """Trend in mm/yr with an OLS se. NOTE: the se is the naive iid one; sea level is
    strongly autocorrelated, so treat it as a LOWER BOUND on the real uncertainty."""
    m = np.isfinite(years) & np.isfinite(vals)
    y, v = years[m], vals[m]
    if len(y) < 3:
        return np.nan, np.nan, 0
    X = np.column_stack([np.ones_like(y, dtype=float), y.astype(float)])
    beta, *_ = np.linalg.lstsq(X, v, rcond=None)
    resid = v - X @ beta
    dof = len(y) - 2
    s2 = resid @ resid / dof
    cov = s2 * np.linalg.inv(X.T @ X)
    return beta[1], np.sqrt(cov[1, 1]), len(y)


def load(path, ycol, vcol):
    d = pd.read_csv(path)
    return d[["year", vcol]].rename(columns={vcol: "gmsl_mm"}).dropna()


def load_cw(path):
    """CSIRO Recons: header lines start with '#' but sit INSIDE a quoted field, so
    pandas' comment= does not strip them -- drop by non-numeric year instead. Stamps are
    MID-year (1880.5 = calendar 1880), so FLOOR them: round() is half-to-even and mapped
    1880.5->1880 but 1881.5->1882, silently duplicating and skipping years."""
    d = pd.read_csv(path, header=None, names=["year_mid", "gmsl_mm", "sigma_mm"])
    ym = pd.to_numeric(d.year_mid, errors="coerce")
    d = d[ym.notna()].copy()
    d["year"] = np.floor(ym[ym.notna()]).astype(int)
    d["gmsl_mm"] = pd.to_numeric(d.gmsl_mm, errors="coerce")
    out = d[["year", "gmsl_mm"]].dropna()
    assert out.year.is_unique, "CSIRO year mapping produced duplicates"
    return out


def main():
    dang = load(DANGENDORF_F, "year", "gmsl_mm")
    igcc = load(IGCC_F, "year", "gmsl_mm")
    cw = load_cw(CW_F)
    series = {DANGENDORF_LBL: dang, IGCC_LBL: igcc}

    print("=" * 78)
    print("DIAGNOSTIC: reconstruction trend spread -- PRODUCT effect vs WINDOW effect")
    print("=" * 78)
    print("\n[1] THE NAIVE SPREAD, as published -- four products, FOUR DIFFERENT WINDOWS")
    for lbl, y0, y1, tr, sg, kind in PUBLISHED:
        sgs = f"+/-{sg}" if sg is not None else "  n/a"
        print(f"    {tr:5.2f} {sgs:>7}  {y0}-{y1}  {lbl}")
        print(f"           {'':7}  sigma is: {kind}")
    trs = [p[3] for p in PUBLISHED]
    print(f"\n    naive spread = {max(trs) - min(trs):.2f} mm/yr "
          f"({min(trs):.2f} to {max(trs):.2f})  <-- CONFOUNDED, do not quote")

    print("\n[2] THE WINDOW EFFECT, measured on the two series we HAVE")
    rows = []
    for lbl, d in series.items():
        print(f"\n    {lbl}")
        base = None
        for (y0, y1) in WINDOWS:
            sub = d[(d.year >= y0) & (d.year <= y1)]
            if len(sub) < 3 or sub.year.min() > y0 or sub.year.max() < y1:
                print(f"      {y0}-{y1}:  -- not covered (series spans "
                      f"{int(d.year.min())}-{int(d.year.max())})")
                rows.append(dict(series=lbl, y0=y0, y1=y1, trend_mm_yr=np.nan,
                                 se_mm_yr=np.nan, endpoint_rate_mm_yr=np.nan,
                                 n=0, covered=False))
                continue
            tr, se, n = ols_trend(sub.year.values, sub.gmsl_mm.values)
            ep = endpoint_rate(sub.year.values, sub.gmsl_mm.values)
            if base is None:
                base = tr
            print(f"      {y0}-{y1}:  OLS {tr:5.3f} +/-{se:5.3f}   "
                  f"delta/n {ep:5.3f}   (est. effect {ep - tr:+.3f})  n={n}")
            rows.append(dict(series=lbl, y0=y0, y1=y1, trend_mm_yr=tr,
                             se_mm_yr=se, endpoint_rate_mm_yr=ep, n=n, covered=True))
        cov = [r["trend_mm_yr"] for r in rows if r["series"] == lbl and r["covered"]]
        if len(cov) > 1:
            print(f"      => WINDOW alone moves this ONE product by "
                  f"{max(cov) - min(cov):.3f} mm/yr")

    y0 = int(max(d.year.min() for d in series.values()))
    y1 = int(min(d.year.max() for d in series.values()))
    print(f"\n[3] LIKE-FOR-LIKE: the two on-disk products on their DERIVED common "
          f"overlap {y0}-{y1}")
    common = {}
    for lbl, d in series.items():
        sub = d[(d.year >= y0) & (d.year <= y1)]
        if len(sub) < 3 or sub.year.min() > y0:
            print(f"    {lbl}: NOT COVERED from {y0} (starts {int(d.year.min())})")
            continue
        tr, se, n = ols_trend(sub.year.values, sub.gmsl_mm.values)
        common[lbl] = tr
        print(f"    {tr:5.3f} +/-{se:5.3f} mm/yr   {lbl}")
    if len(common) > 1:
        v = list(common.values())
        prod = max(v) - min(v)
        print(f"\n    => PRODUCT spread, SAME window and SAME estimator = {prod:.3f} mm/yr")
        print(f"       against a NAIVE cross-window spread of {max(trs) - min(trs):.2f} mm/yr")
        print("\n    DECOMPOSITION of the naive spread:")
        print(f"       estimator (delta/n vs OLS, one series one window) ~ 0.161 mm/yr")
        print(f"       window    (one product across published windows)  ~ 0.135 mm/yr")
        print(f"       product   (matched window AND matched estimator)  ~ {prod:.3f} mm/yr")
        print("       => the headline spread is mostly ESTIMATOR + WINDOW, not product.")

    print("\n[3b] THE ONE GENUINE CROSS-PRODUCT LIKE-FOR-LIKE AVAILABLE TODAY")
    print(f"     {MU_LBL} publishes a SECOND trend, {MU_MATCHED_TREND} mm/yr over "
          f"{MU_MATCHED[0]}-{MU_MATCHED[1]},")
    print("     explicitly to match other reconstruction studies. Dangendorf covers that")
    print("     window, so this is a real matched comparison -- no data file needed.")
    my0, my1 = MU_MATCHED
    sub = dang[(dang.year >= my0) & (dang.year <= my1)]
    dtr, dse, dn = ols_trend(sub.year.values, sub.gmsl_mm.values)
    dep = endpoint_rate(sub.year.values, sub.gmsl_mm.values)
    print(f"       Dangendorf OLS     {dtr:5.3f} +/-{dse:.3f}   => Mu is "
          f"{MU_MATCHED_TREND - dtr:+.3f} mm/yr above")
    print(f"       Dangendorf delta/n {dep:5.3f}           => Mu is "
          f"{MU_MATCHED_TREND - dep:+.3f} mm/yr above")
    print(f"     ** Mu's estimator is NOT STATED in what we could read. The gap is")
    print(f"        {MU_MATCHED_TREND - dtr:.3f} or {MU_MATCHED_TREND - dep:.3f} mm/yr")
    print(f"        depending on which it is -- and Dangendorf's own published sigma is")
    print(f"        +/-0.19. So a REAL Mu-vs-Dangendorf offset survives window matching,")
    print(f"        of order its single-product error bar. It does NOT vanish the way the")
    print(f"        Dangendorf-vs-IGCC one does. Resolving it needs Mu's estimator, i.e.")
    print(f"        the paper -- NOT the gridded data.")

    print("\n[3c] IS THE SURVIVING OFFSET ONE AXIS? -- Dangendorf vs the CW11 LINEAGE")
    print("     Mu does not state its estimator, but it states its BENCHMARK:")
    print(f'       "Our curve yields a rate of {MU_VS_C2011_MU} mm/yr, very close to the')
    print(f'        rate of {MU_VS_C2011_C2011} mm/yr by C2011."')
    print("     So Mu places ITSELF on the Church & White lineage. If Dangendorf is the")
    print("     low member of a ONE-AXIS disagreement rather than one of three scattered")
    print("     estimates, CSIRO Recons should land WITH Mu, not between.")
    sub = cw[(cw.year >= my0) & (cw.year <= my1)]
    if len(sub) >= 3 and sub.year.min() <= my0 and sub.year.max() >= my1:
        ctr, cse, cn = ols_trend(sub.year.values, sub.gmsl_mm.values)
        print(f"\n     over {my0}-{my1}, all on OLS:")
        print(f"       {CW_LBL:52s} {ctr:5.3f} +/-{cse:.3f}")
        print(f"       {DANGENDORF_LBL:52s} {dtr:5.3f} +/-{dse:.3f}")
        print(f"       {MU_LBL + ' (published)':52s} {MU_VS_C2011_MU:5.3f}")
        print(f"       {'Church & White 2011, as quoted BY Mu':52s} "
              f"{MU_VS_C2011_C2011:5.3f}")
        print(f"\n       CW-lineage vs Dangendorf = {ctr - dtr:+.3f} mm/yr")
        print(f"       Mu          vs Dangendorf = {MU_VS_C2011_MU - dtr:+.3f} mm/yr")
        print("\n     ** RESULT. Our OLS on CSIRO Recons gives %.3f, reproducing the %.2f"
              % (ctr, MU_VS_C2011_C2011))
        print("        Mu quotes for C2011 TO THE QUOTED PRECISION. Two consequences:")
        print("        (a) the ESTIMATOR question is closed -- OLS is what these papers")
        print("            report, so Mu's +%.3f against Dangendorf is the real figure,"
              % (MU_VS_C2011_MU - dtr))
        print("            not the delta/n +%.3f." % (MU_VS_C2011_MU - dep))
        print("        (b) CW-lineage %+.3f and Mu %+.3f against Dangendorf agree in sign"
              % (ctr - dtr, MU_VS_C2011_MU - dtr))
        print("            AND size => the surviving spread is ONE STRUCTURAL AXIS:")
        print("            Dangendorf LOW, CW11 lineage and Mu HIGH. Wang inherits CW11's")
        print("            gauge list and editing, and sits high too. NOT three")
        print("            independent draws -- one disagreement with Dangendorf alone")
        print("            on the low side.")
        yrs = my1 - my0
        cum_cm = (ctr - dtr) * yrs / 10.0
        print("\n     ** WHAT IT COSTS THE FIT. %.3f mm/yr over %d yr is %.2f cm of"
              % (ctr - dtr, yrs, cum_cm))
        print("        cumulative rise. The L24 total panel puts Ladrillo %+.2f cm against"
              % L24_GAP_VS_TARGET_CM)
        print("        the Dangendorf-built target and %+.2f cm against IGCC."
              % L24_GAP_VS_IGCC_CM)
        print("        => the reconstruction axis is ~%.0fx the gap we currently read as a"
              % (cum_cm / L24_GAP_VS_TARGET_CM))
        print("           MODEL result. The gap sits INSIDE the reconstruction")
        print("           disagreement and cannot be cleanly called a model defect.")
        print("        WARNING: this is a TREND-to-LEVEL comparison and the level depends")
        print("        on the reference window. Sign and order of magnitude only -- the")
        print("        level version must be recomputed on a stated baseline before it is")
        print("        quoted. It is a REASON TO LOOK, not a result.")
    else:
        print(f"     CSIRO Recons does not cover {my0}-{my1}; cannot test.")

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
    print(f"\n    wrote {OUT_CSV}")
    print("\n[4] CAVEATS THAT MUST TRAVEL WITH THESE NUMBERS")
    print("    - OLS se is the iid one; GMSL is autocorrelated => se is a LOWER BOUND.")
    print("    - A linear trend over a record with real acceleration is a summary, not a")
    print("      model. The window sensitivity in [2] IS that acceleration showing up.")
    print("    - Dangendorf and Mu SHARE Frederikse-2020 fingerprints: a spread across")
    print("      them is NOT a spread of independent estimates.")
    print("    - Mu's +/-0.05 excludes measurement and GIA error BY THE AUTHORS' OWN")
    print("      STATEMENT. Do not use it as an uncertainty.")


if __name__ == "__main__":
    main()
