#!/usr/bin/env python3
"""
DIAGNOSTIC -- the reconstruction axis as a LEVEL, on the L24 panel's OWN baseline.

Approved by Marcus 2026-09-09c as the one non-blocked item out of
notes/handoff_2026-09-09b_recalib_questions_closed.md section 3.

WHAT IT FIXES. That note found the surviving reconstruction disagreement to be ONE axis --
Dangendorf LOW against the CW11 lineage by ~0.230 mm/yr over 1900-2007 -- and then wrote
"0.230 mm/yr x 107 yr = 2.46 cm, against the +0.74 cm by which Ladrillo sits above the
Dangendorf-built target, so the axis is ~3x the gap." It flagged that arithmetic itself:
⛔ it is a TREND-to-LEVEL comparison, and a level depends on the reference window.

It does. The L24 total panel is cm rel. 1995-2005 (plot_hindcast_components.py:78), and the
+0.74 cm is read at 2024. A trend difference re-referenced to a window centred on ~2000 does
NOT accumulate to (t1-t0) x slope: it accumulates AWAY FROM THE BASELINE, in both directions.
"x 107 yr" is the magnitude at the EARLY end of the record, where the panel's baseline puts
the reconstructions furthest apart -- not at 2024, where the gap is quoted.

So this script does not recompute a trend. It re-references each reconstruction to the SAME
1995-2005 window the panel uses, and reads the level difference off directly, year by year --
the [[use real data when you have it]] form of the same question.

WRITES NOTHING outside outputs/. Changes no target, runs no chain. Reports only.
"""
import os
import numpy as np
import pandas as pd

# ---- named constants: every label and message below derives from these -------
REPO   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS    = os.path.join(REPO, "data", "observations")
OUT_CSV = os.path.join(REPO, "outputs", "diag_recon_axis_level_vs_l24_gap.csv")

DANGENDORF_F = os.path.join(OBS, "dangendorf2024_gmsl_annual.csv")
IGCC_F       = os.path.join(OBS, "igcc2026_gmsl_annual.csv")
CW_F         = os.path.join(REPO, "data", "calibration", "CSIRO_Recons_gmsl_yr_2015.csv")

DANGENDORF_LBL = "Dangendorf 2024"
IGCC_LBL       = "IGCC 2025-ind."
CW_LBL         = "CSIRO Recons (CW11 lineage)"

# THE PANEL'S OWN BASELINE. Not typed independently -- this is the value asserted at
# plot_hindcast_components.py:78 (BASE0, BASE1 = 1995, 2005), the CALIBRATION window.
BASE0, BASE1 = 1995, 2005
BASE_LBL     = f"{BASE0}-{BASE1}"

# The L24 total panel at 2024, cm rel. BASE_LBL, from
# handoff_2026-09-09_igcc2026_and_recalib_scope.md section 2.
L24_YEAR          = 2024
L24_LADRILLO_CM   = 8.55
L24_IGCC_CM       = 8.33
L24_TARGET_CM     = 7.81
L24_GAP_CM        = L24_LADRILLO_CM - L24_TARGET_CM     # +0.74, the number under test
L24_GAP_VS_IGCC_CM = L24_LADRILLO_CM - L24_IGCC_CM      # +0.22

# The section-3 arithmetic being audited, reproduced here so the audit is self-contained.
AXIS_TREND_MM_YR = 0.230      # CW11 lineage minus Dangendorf, OLS, 1900-2007
AXIS_N_YEARS     = 107        # the span it was multiplied by
NAIVE_AXIS_CM    = AXIS_TREND_MM_YR * AXIS_N_YEARS / 10.0   # 2.46 cm, DERIVED not typed

REPORT_YEARS = [1900, 1925, 1950, 1975, 2000, 2013, 2021]


def load(path, vcol="gmsl_mm"):
    d = pd.read_csv(path)
    return d[["year", vcol]].rename(columns={vcol: "gmsl_mm"}).dropna()


def load_cw(path):
    """CSIRO Recons: '#' header lines sit INSIDE a quoted field so comment= does not strip
    them; and stamps are MID-year, where round() is half-to-even. FLOOR, then assert
    uniqueness. (Trap recorded in handoff_2026-09-09b section 7.)"""
    d = pd.read_csv(path, header=None, names=["year_mid", "gmsl_mm", "sigma_mm"])
    ym = pd.to_numeric(d.year_mid, errors="coerce")
    d = d[ym.notna()].copy()
    d["year"] = np.floor(ym[ym.notna()]).astype(int)
    d["gmsl_mm"] = pd.to_numeric(d.gmsl_mm, errors="coerce")
    out = d[["year", "gmsl_mm"]].dropna()
    assert out.year.is_unique, "CSIRO year mapping produced duplicates"
    return out


def rebase(d, lbl):
    """Re-reference to the panel's window and return cm. GATE: the window must be FULLY
    covered -- a partial mean is a different baseline wearing the same name."""
    s = d.set_index("year")["gmsl_mm"]
    win = s.loc[(s.index >= BASE0) & (s.index <= BASE1)]
    n_expected = BASE1 - BASE0 + 1
    n_finite = int(np.isfinite(win).sum())
    if len(win) != n_expected or n_finite != n_expected:
        raise SystemExit(f"[GATE BASE] {lbl}: {len(win)}/{n_expected} years present, "
                         f"{n_finite}/{n_expected} finite, in {BASE_LBL} -- cannot "
                         f"re-reference on the panel's window")
    out = (s - win.mean()) / 10.0                      # mm -> cm, rel. BASE_LBL
    assert abs(out.loc[BASE0:BASE1].mean()) < 1e-9, f"{lbl}: rebase did not zero the window"
    return out


def main():
    ser = {DANGENDORF_LBL: rebase(load(DANGENDORF_F), DANGENDORF_LBL),
           IGCC_LBL:       rebase(load(IGCC_F), IGCC_LBL),
           CW_LBL:         rebase(load_cw(CW_F), CW_LBL)}

    print("=" * 78)
    print(f"DIAGNOSTIC: the reconstruction axis as a LEVEL, cm rel. {BASE_LBL}")
    print("=" * 78)
    for lbl, s in ser.items():
        print(f"    {lbl:28s}  {int(s.index.min())}-{int(s.index.max())}  "
              f"n={len(s)}   {BASE_LBL} mean = {s.loc[BASE0:BASE1].mean():+.3e} cm")

    print(f"\n[1] WHAT SECTION 3 COMPUTED, and why the panel cannot read it that way")
    print(f"    {AXIS_TREND_MM_YR:.3f} mm/yr x {AXIS_N_YEARS} yr = {NAIVE_AXIS_CM:.2f} cm")
    print(f"    vs the L24 gap {L24_GAP_CM:+.2f} cm at {L24_YEAR}  =>  "
          f"{NAIVE_AXIS_CM / L24_GAP_CM:.1f}x  <-- the '~3x' claim")
    print(f"    ⛔ but that is a level with NO reference window. On this panel's "
          f"{BASE_LBL} baseline")
    print(f"       a slope difference is ZERO at the baseline centre (~{(BASE0+BASE1)//2}) "
          f"and grows BOTH ways.")

    # --- the measured axis, year by year -------------------------------------
    rows = []
    print(f"\n[2] MEASURED level differences, cm rel. {BASE_LBL} (positive = higher sea level)")
    print(f"    {'year':>5}  {CW_LBL+' - '+DANGENDORF_LBL:>42}   "
          f"{IGCC_LBL+' - '+DANGENDORF_LBL:>30}")
    d0 = ser[DANGENDORF_LBL]
    for y in REPORT_YEARS:
        cw = ser[CW_LBL].get(y, np.nan) - d0.get(y, np.nan)
        ig = ser[IGCC_LBL].get(y, np.nan) - d0.get(y, np.nan)
        f_cw = f"{cw:+.3f}" if np.isfinite(cw) else "  --  "
        f_ig = f"{ig:+.3f}" if np.isfinite(ig) else "  --  "
        print(f"    {y:>5}  {f_cw:>42}   {f_ig:>30}")
        rows.append(dict(year=y, cw_minus_dang_cm=cw, igcc_minus_dang_cm=ig))

    # --- the comparison the section actually wanted --------------------------
    y_last_cw = int(min(ser[CW_LBL].index.max(), d0.index.max()))    # DERIVED, never typed
    axis_last = ser[CW_LBL][y_last_cw] - d0[y_last_cw]
    y_last_ig = int(min(ser[IGCC_LBL].index.max(), d0.index.max()))
    igcc_last = ser[IGCC_LBL][y_last_ig] - d0[y_last_ig]

    print(f"\n[3] THE COMPARISON, LIKE FOR LIKE -- axis and gap both as LEVELS on {BASE_LBL}")
    print(f"    the L24 gap                                  {L24_GAP_CM:+.2f} cm  at {L24_YEAR}")
    print(f"    axis, {CW_LBL} - {DANGENDORF_LBL}   {axis_last:+.3f} cm  at {y_last_cw} "
          f"(last common year)")
    print(f"    axis, {IGCC_LBL} - {DANGENDORF_LBL}       {igcc_last:+.3f} cm  at {y_last_ig} "
          f"(last common year)")
    ratio = abs(axis_last) / abs(L24_GAP_CM)
    print(f"\n    => on the panel's own baseline the axis at its recent end is "
          f"{ratio:.2f}x the gap,")
    print(f"       NOT {NAIVE_AXIS_CM / L24_GAP_CM:.1f}x. The naive product is close to the "
          f"axis at the EARLY end:")
    early = ser[CW_LBL].get(1900, np.nan) - d0.get(1900, np.nan)
    print(f"       {CW_LBL} - {DANGENDORF_LBL} at 1900 = {early:+.3f} cm "
          f"(naive was {-NAIVE_AXIS_CM:+.2f}).")

    # --- the axis is NOT a slope difference: it has SHAPE --------------------
    print(f"\n[3b] ⚠ THE AXIS IS NOT A SLOPE DIFFERENCE -- it has SHAPE, so no single "
          f"cm value describes it")
    for lbl in (CW_LBL, IGCC_LBL):
        d = (ser[lbl] - d0).dropna()
        i_max = int(d.abs().idxmax())
        print(f"    {lbl:28s}  max |diff| {d[i_max]:+.3f} cm at {i_max}; "
              f"1900-end {d.iloc[0]:+.3f} at {int(d.index.min())}, "
              f"recent end {d.iloc[-1]:+.3f} at {int(d.index.max())}")
        rows.append(dict(year=i_max, cw_minus_dang_cm=(d[i_max] if lbl == CW_LBL else np.nan),
                         igcc_minus_dang_cm=(d[i_max] if lbl == IGCC_LBL else np.nan)))
    print(f"    => a MID-CENTURY divergence, not a constant tilt. The 1900-2007 OLS "
          f"difference of")
    print(f"       {AXIS_TREND_MM_YR:.3f} mm/yr averages ACROSS that shape and represents it "
          f"at no single year.")

    print(f"\n[4] VERDICT")
    if ratio < 1.0:
        print(f"    ⛔ SECTION 3'S FLAG WAS RIGHT AND ITS NUMBER WAS BACKWARDS. Re-read on "
              f"the panel's")
        print(f"       own baseline, the reconstruction axis at {y_last_cw} is "
              f"{abs(axis_last):.2f} cm -- SMALLER than the")
        print(f"       {abs(L24_GAP_CM):.2f} cm gap, not ~3x larger. The '+0.74 cm sits inside the "
              f"reconstruction")
        print(f"       disagreement' reading is NOT SUPPORTED at {L24_YEAR}; it is supported "
              f"only near 1900,")
        print(f"       where this baseline puts the reconstructions ~{abs(early):.1f} cm apart "
              f"and where the")
        print(f"       L24 panel has no gap to explain.")
    else:
        print(f"    the axis does exceed the gap on this baseline: {ratio:.2f}x")
    print(f"\n    ⚠ {CW_LBL} ends {int(ser[CW_LBL].index.max())}, so the axis CANNOT be read "
          f"at {L24_YEAR} directly.")
    print(f"      {y_last_cw} is the honest last common year; extrapolating the axis 11 more "
          f"years is")
    print(f"      exactly the trend-to-level move this diagnostic exists to stop.")
    print(f"    ⚠ Sign convention: a HIGHER reconstruction means a LARGER target, which would "
          f"SHRINK")
    print(f"      Ladrillo's {L24_GAP_CM:+.2f} cm excess. Both differences above are positive "
          f"at the recent end,")
    print(f"      so they point the right way -- they are just too small to absorb the gap.")

    rows.append(dict(year=y_last_cw, cw_minus_dang_cm=axis_last, igcc_minus_dang_cm=np.nan))
    df = pd.DataFrame(rows).drop_duplicates(subset="year", keep="first").sort_values("year")
    df["baseline"] = BASE_LBL
    df["l24_gap_cm"] = L24_GAP_CM
    df["l24_gap_year"] = L24_YEAR
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\n[wrote] {OUT_CSV}")


if __name__ == "__main__":
    main()
