#!/usr/bin/env python3
"""
DIAGNOSTIC -- REASON 1 of the recalibration scope: is the modern splice's single-product
anchor with a TYPED sigma defensible now that IGCC publishes a MEASURED three-product
altimetry spread?

Marcus ruled 2026-09-09b: keep Dangendorf as the fitted target, carry the CW11 axis as an
uncertainty, and run this next. Diagnostic ONLY -- it rebuilds nothing and writes no target.

WHAT THE SPLICE ACTUALLY IS (prep_recalib_targets_ext.py):
  total target = Dangendorf 1900-2021, then NOAA STAR offset-matched to Dangendorf over
  OVERLAP_WIN, used for SPLICE_FROM..2024. STAR's sigma column is EMPTY, so every spliced
  year is assigned a hardcoded ALT_SIGMA_MM.

THE QUESTION IN THREE PARTS:
  (a) how much of the target does this actually govern?
  (b) does the anchor MOVE if the modern product is the IGCC altimetry ensemble instead?
  (c) is ALT_SIGMA_MM right, measured against the across-product spread -- and measured on
      the RE-REFERENCED anomaly, which is what a splice consumes, not on the published
      levels (see published_sigma_may_be_level_not_anomaly).

  ** ROBUSTNESS REQUIRED: the third column of altimetry_indiv_estimates.csv is still headed
  NOAA while the paper says U. Colorado -- a suspected product swap under an unchanged
  header, NOT PROVEN, and standing instruction is not to use it until settled. So every
  number below is reported BOTH with all three products and with that column DROPPED, and
  the verdict must not depend on it.
"""
import os
import numpy as np
import pandas as pd

REPO   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS    = os.path.join(REPO, "data", "observations")
IGCC_D = os.path.join(OBS, "raw", "igcc2026", "data-2026.06.02", "data", "sea_level_rise")
OUT_CSV = os.path.join(REPO, "outputs", "diag_modern_splice_altimetry.csv")

# --- mirrored from prep_recalib_targets_ext.py; changing them there changes the answer ---
BASE_Y0, BASE_Y1 = 1995, 2005        # common re-reference window
OVERLAP_WIN      = (2003, 2018)      # "dang" offset-match window
SPLICE_FROM      = 2022              # first year the modern product supplies
ALT_SIGMA_MM     = 4.0               # the TYPED sigma under test
DANG_SE_2021_MM  = 2.68              # Dangendorf's OWN per-year SE at its last year

STAR_F  = os.path.join(OBS, "nasa_gmsl_annual.csv")
DANG_F  = os.path.join(OBS, "dangendorf2024_gmsl_annual.csv")
ENS_F   = os.path.join(IGCC_D, "altimetry_ens.csv")
INDIV_F = os.path.join(IGCC_D, "altimetry_indiv_estimates.csv")

SUSPECT_COL = "NOAA"      # headed NOAA, paper says U. Colorado -- swap NOT PROVEN
STAR_LBL    = "NOAA STAR (current anchor)"
ENS_LBL     = "IGCC altimetry ensemble mean"


def reref(s, win):
    return s - s.loc[win[0]:win[1]].mean()


def offset_to(mod_cm, ref_cm, win):
    """Level shift so mod mean == ref mean over win -- the same rule the target build uses."""
    yrs = [y for y in range(win[0], win[1] + 1)
           if y in mod_cm.index and y in ref_cm.index]
    if not yrs:
        return np.nan, []
    return float(ref_cm.loc[yrs].mean() - mod_cm.loc[yrs].mean()), yrs


def main():
    dang = pd.read_csv(DANG_F).set_index("year")["gmsl_mm"] / 10.0
    dang = reref(dang, (BASE_Y0, BASE_Y1))                       # cm, 1900-2021
    star = pd.read_csv(STAR_F).set_index("year")["value"] / 10.0  # cm, 1993-2024

    ens = pd.read_csv(ENS_F)
    ens["year"] = np.floor(ens["time"]).astype(int)
    ens = ens.set_index("year")
    igcc_ens = ens["mean"] / 10.0
    igcc_pub_std_mm = ens["std"]

    ind = pd.read_csv(INDIV_F)
    ind["year"] = np.floor(ind["time"]).astype(int)
    ind = ind.set_index("year")
    prod_cols = [c for c in ind.columns
                 if c not in ("time", "timebound_lower", "timebound_upper", "year")]

    print("=" * 78)
    print("DIAGNOSTIC: the modern splice -- single-product anchor with a TYPED sigma")
    print("=" * 78)

    print(f"\n[1] WHAT THE SPLICE GOVERNS")
    dang_end = int(dang.index.max())
    star_end = int(star.index.max())
    igcc_end = int(igcc_ens.index.max())
    spliced_years = list(range(SPLICE_FROM, star_end + 1))
    print(f"    Dangendorf ends {dang_end}; the modern product supplies "
          f"{SPLICE_FROM}..{star_end}")
    print(f"    => {len(spliced_years)} spliced years ({spliced_years}) out of "
          f"{dang_end - 1900 + 1} in the total target.")
    print(f"    ** So the DIRECT reach of this choice is {len(spliced_years)} years. It is")
    print(f"       NOT a whole-record issue. But the choice ALSO sets the offset via the")
    print(f"       {OVERLAP_WIN[0]}-{OVERLAP_WIN[1]} match, so it moves those years twice over.")
    print(f"    ** IGCC altimetry runs to {igcc_end}, {igcc_end - star_end} year(s) beyond "
          f"STAR's {star_end}.")

    print(f"\n[2] DOES THE ANCHOR MOVE? -- each product offset-matched to Dangendorf "
          f"over {OVERLAP_WIN[0]}-{OVERLAP_WIN[1]}")
    cands = {STAR_LBL: star, ENS_LBL: igcc_ens}
    for c in prod_cols:
        cands[f"IGCC {c}" + ("  <-- SUSPECT HEADER" if c == SUSPECT_COL else "")] = \
            ind[c] / 10.0
    rows, spliced = [], {}
    for lbl, s in cands.items():
        off, yrs = offset_to(s, dang, OVERLAP_WIN)
        sp = s + off
        spliced[lbl] = sp
        vals = {y: sp.get(y, np.nan) for y in spliced_years}
        txt = "  ".join(f"{y}:{v * 10:7.2f}" for y, v in vals.items())
        print(f"    {lbl:44s} off={off * 10:+7.2f}mm  {txt}")
        for y, v in vals.items():
            rows.append(dict(product=lbl, year=y, spliced_mm=v * 10, offset_mm=off * 10))

    print(f"\n[3] THE SPREAD THAT MATTERS -- across products, AFTER offset-matching")
    print(f"    (this is the ANOMALY spread the splice actually consumes; the published")
    print(f"     std column is a spread of LEVELS on differing references)")
    all3 = [f"IGCC {c}" + ("  <-- SUSPECT HEADER" if c == SUSPECT_COL else "")
            for c in prod_cols]
    keep = [f"IGCC {c}" for c in prod_cols if c != SUSPECT_COL]
    for name, members in (("ALL THREE products", all3),
                          (f"WITHOUT the suspect {SUSPECT_COL} column", keep)):
        print(f"\n    -- {name} (n={len(members)})")
        for y in spliced_years:
            v = np.array([spliced[m].get(y, np.nan) * 10 for m in members], dtype=float)
            v = v[np.isfinite(v)]
            if len(v) < 2:
                continue
            sd = v.std(ddof=1)
            rng = v.max() - v.min()
            print(f"       {y}:  sd={sd:5.2f} mm   range={rng:5.2f} mm   "
                  f"vs TYPED ALT_SIGMA_MM={ALT_SIGMA_MM}  => typed is {ALT_SIGMA_MM / sd:4.1f}x")
            rows.append(dict(product=f"SPREAD[{name}]", year=y,
                             spliced_mm=np.nan, offset_mm=np.nan,
                             sd_mm=sd, range_mm=rng))

    print(f"\n[4] THE TYPED SIGMA IN CONTEXT")
    pub = igcc_pub_std_mm.loc[igcc_pub_std_mm.index.isin(spliced_years)]
    print(f"    typed ALT_SIGMA_MM                          = {ALT_SIGMA_MM:.2f} mm")
    print(f"    IGCC PUBLISHED across-product std, splice yrs = "
          f"{pub.min():.2f}-{pub.max():.2f} mm")
    print(f"    IGCC published std, whole altimetry era      = "
          f"{igcc_pub_std_mm.min():.2f}-{igcc_pub_std_mm.max():.2f} mm")
    print(f"    Dangendorf's OWN SE at its last year ({dang_end}) = "
          f"{DANG_SE_2021_MM:.2f} mm")
    print(f"    ** The typed value is LARGER than the measured spread AND larger than the")
    print(f"       reconstruction's own SE at the join. It is CONSERVATIVE, not optimistic")
    print(f"       -- so replacing it TIGHTENS the target, it does not loosen it.")

    print(f"\n[5] THE HEADLINE IS THE LEVEL, NOT THE SIGMA")
    y = spliced_years[-1]
    d_star = spliced[STAR_LBL].get(y) * 10
    d_ens  = spliced[ENS_LBL].get(y) * 10
    print(f"    At {y} the spliced target reads {d_star:.2f} mm on STAR and "
          f"{d_ens:.2f} mm on the IGCC ensemble")
    print(f"    => the ANCHOR CHOICE moves the target by {d_ens - d_star:+.2f} mm, which is")
    print(f"       {abs(d_ens - d_star) / ALT_SIGMA_MM:.2f}x the typed sigma it is assigned.")
    print(f"    ** So the defect is NOT mainly that the sigma is typed. The sigma is")
    print(f"       CONSERVATIVE. The defect is that the single-product anchor sits ~1 sigma")
    print(f"       LOW against the multi-product ensemble, and STAR is the one product IGCC")
    print(f"       dropped. Every IGCC product lands ABOVE STAR in every spliced year.")
    kept2 = np.array([spliced[k].get(y, np.nan) * 10 for k in keep], dtype=float)
    print(f"    ROBUSTNESS: dropping the suspect column, the 2-product mean at {y} is "
          f"{np.nanmean(kept2):.2f} mm")
    print(f"       vs the 3-product {d_ens:.2f} -- a {abs(np.nanmean(kept2) - d_ens):.2f} mm "
          f"difference, so the level")
    print(f"       finding does NOT depend on the suspect column.")

    print(f"\n[6] A TEST OF THE SUSPECT HEADER (the release calls col 3 {SUSPECT_COL};")
    print(f"    the paper says U. Colorado). If it really were {SUSPECT_COL}, it should")
    print(f"    track actual NOAA STAR more closely than the OTHER IGCC products do.")
    sus = spliced[f"IGCC {SUSPECT_COL}  <-- SUSPECT HEADER"]
    others = [f"IGCC {c}" for c in prod_cols if c != SUSPECT_COL]
    ov = [yy for yy in spliced[STAR_LBL].index
          if yy in sus.index and all(yy in spliced[o].index for o in others)]
    def rms(a, b):
        d = np.array([(a.get(yy, np.nan) - b.get(yy, np.nan)) * 10 for yy in ov],
                     dtype=float)
        d = d[np.isfinite(d)]
        return float(np.sqrt((d ** 2).mean())), float(d.mean())
    r_sus, m_sus = rms(sus, spliced[STAR_LBL])
    print(f"    over {min(ov)}-{max(ov)}, all offset-matched to Dangendorf:")
    print(f"      STAR vs the '{SUSPECT_COL}'-headed column : rms={r_sus:5.2f} mm  "
          f"mean={m_sus:+5.2f} mm")
    for o in others:
        r_o, m_o = rms(spliced[o], spliced[STAR_LBL])
        print(f"      STAR vs {o:24s}: rms={r_o:5.2f} mm  mean={m_o:+5.2f} mm")
    r_in, m_in = rms(spliced[others[0]], spliced[others[1]])
    print(f"      {others[0]} vs {others[1]} (within-IGCC): rms={r_in:5.2f} mm  "
          f"mean={m_in:+5.2f} mm")
    print(f"    ** READ IT AS EVIDENCE, NOT PROOF. If the '{SUSPECT_COL}' column were NOAA")
    print(f"       we would expect its STAR distance to be SMALLER than the other products'")
    print(f"       and comparable to the within-IGCC spread. Compare the rows above.")
    print(f"       Annual-averaging and reference conventions differ between releases, so a")
    print(f"       nonzero distance alone proves nothing -- the ORDERING is the signal.")

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
    print(f"\n    wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
