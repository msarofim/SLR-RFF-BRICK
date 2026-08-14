#!/usr/bin/env python3
"""
diag_te_driver_vs_module.py — is Ladrillo's thermal-expansion misfit the DRIVER
(FaIR's OHC) or the MODULE (one constant expansion coefficient)?

WHY THIS TEST EXISTS (Marcus, 2026-08-14). Asked whether hemispheric temperature
patterns would help TE, the way the sub-global drivers helped glaciers and
Greenland. They cannot enter directly: MimiBRICK's thermal_expansion never sees a
temperature. It integrates OHC alone —

    te_sea_level[t] = te_sea_level[t-1] + Δ_oceanheat[t] · te_α / (te_A·te_C·te_ρ²)

so te_sea_level = te_s₀ + te_α · S(t), with S set by the OHC forcing and
te_s₀ = 0 (MimiBRICK default, not sampled). The re-referenced series is EXACTLY
proportional to `thermal_alpha`.

But the physics behind the question is real and does not need temperature to
express it. The expansion coefficient of seawater is strongly temperature- and
pressure-dependent, so the SAME joule produces more sea level in warm shallow
water than in cold deep water. If the DEPTH/LATITUDE DISTRIBUTION of heat uptake
has shifted over the record, the effective joules→cm efficiency is not constant —
and a single `te_α` cannot represent that. That is one hypothesis for the
measured window disagreement (diag_d1_vs_l10.py): the α that zeroes the steric
bias is 0.17748 over 1920-1949 but 0.13386 over 1993-2026.

THE COMPETING HYPOTHESIS, and the reason for this script: FaIR's OHC is a
MODELLED mean, not observed. If it has the wrong shape — too little early
warming, say — the fitted α would have to differ by window for a reason that has
nothing to do with the expansion coefficient. On record already:
`project_brick_te_scales_linearly_with_ohc` (ΔTE 1.86 cm on FaIR OHC vs 2.71 cm
on Tony's obs-driven OHC) says FaIR and observed OHC differ materially.

THE TEST. Rebuild S(t) from OBSERVED OHC products instead of FaIR's and redo the
window-by-window α*. Because the algebra is closed-form, this costs nothing.
  * If the early/modern α* disagreement COLLAPSES on observed OHC -> the defect
    is the DRIVER. Fixing te_α or adding δ(t) would be fixing the wrong thing.
  * If it PERSISTS on every product -> the defect is the MODULE, and a single
    constant expansion coefficient is the thing to replace.

  source ~/climate-env/bin/activate
  python3 python/diag_te_driver_vs_module.py
Writes outputs/diag_te_driver_vs_module.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS = os.path.join(REPO, "data/observations")
OUT = os.path.join(REPO, "outputs/diag_te_driver_vs_module.csv")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")

# MimiBRICK v2.0.0 thermal_expansion constants (src/MimiBRICK.jl L121-125)
TE_A, TE_C, TE_RHO, TE_S0 = 3.619e14, 3991.86795711963, 1027.0, 0.0
# raw thermal_alpha -> the "cm per 1e22 J" the spec quotes
CM_PER_1E22J = 100.0 * 1e22 / (TE_A * TE_C * TE_RHO ** 2)
FIT_REF = (1995, 2005)                     # calibration re-reference window
# 2025 is the last year every OHC product covers (the obs splices end there,
# FaIR runs on); the windows below are intersected with it.
YEARS = np.arange(1850, 2026)
L10_ALPHA = 0.15023                        # L10 posterior median thermal_alpha

DRIVERS = [
    ("FaIR ssp245harm (as calibrated)", "fair_mean_ohc_ssp245harm.csv", "ohc_1e22J"),
    ("obs: Zanna+Cheng",                "ohc_spliced_zanna_cheng.csv",  "ohc_1e22J"),
    ("obs: Zanna+IGCC",                 "ohc_spliced_zanna_igcc.csv",   "ohc_1e22J"),
]
WINDOWS = [("1920-1949", (1920, 1949)), ("1950-1992", (1950, 1992)),
           ("1993-2025", (1993, 2025)), ("full", (1900, 2025))]
# the two windows whose disagreement is the finding under test
EARLY, MODERN = "1920-1949", "1993-2025"


def load_ohc(fname, col):
    """The product on its OWN span. The splices end 2024/2025 while FaIR runs on,
    so each driver is integrated over what it actually covers and the windows are
    intersected with that — never zero-filled, which would inject a fake plateau."""
    d = pd.read_csv(os.path.join(OBS, fname), comment="#")
    s = d.set_index(d.columns[0])[col].astype(float)
    s.index = s.index.astype(int)
    s = s.reindex(YEARS).dropna()
    if s.index.min() > YEARS[0]:
        raise SystemExit(f"{fname} starts {s.index.min()}, after {YEARS[0]}")
    return s


def shape_from(ohc):
    """S(t): te_sea_level per unit te_α, cm, re-referenced to FIT_REF."""
    yrs = ohc.index.to_numpy()
    q = ohc.to_numpy(dtype=float)
    if np.any(np.diff(yrs) != 1):
        raise SystemExit("OHC series has interior gaps — cannot integrate")
    dq = np.diff(q, prepend=q[0]) * 1e22
    s_cm = 100.0 * (TE_S0 + np.cumsum(dq) / (TE_A * TE_C * TE_RHO ** 2))
    ib = (yrs >= FIT_REF[0]) & (yrs <= FIT_REF[1])
    return pd.Series(s_cm - s_cm[ib].mean(), index=yrs)


def main():
    obs = pd.read_csv(TARGETS).set_index("year")["steric"].reindex(YEARS)
    print("Thermal expansion — is the misfit the DRIVER or the MODULE?\n")
    print("  The steric target is Frederikse-derived, the same one the calibrator")
    print(f"  scores. alpha* = the thermal_alpha zeroing that window's mean bias.")
    print(f"  L10 sits at {L10_ALPHA:.5f} raw = "
          f"{CM_PER_1E22J * L10_ALPHA:.4f} cm per 1e22 J.\n")

    rows = []
    print(f"  {'driver':32s} " + "".join(f"{w:>12s}" for w, _ in WINDOWS)
          + f"{'early/modern':>14s} {'1-alpha RMSE':>13s}")
    for label, fname, col in DRIVERS:
        S = shape_from(load_ohc(fname, col))
        yrs = S.index.to_numpy()
        ob = obs.reindex(yrs)
        astar = {}
        for wname, (y0, y1) in WINDOWS:
            m = (yrs >= y0) & (yrs <= y1) & ob.notna().to_numpy()
            s, o = S[m], ob[m]
            astar[wname] = float(o.mean() / s.mean()) if s.mean() != 0 else np.nan
        # the single best-fit alpha over the full record, and what it leaves behind
        m = (yrs >= 1900) & ob.notna().to_numpy()
        s, o = S[m].to_numpy(), ob[m].to_numpy()
        a_ls = float(s @ o / (s @ s))
        rmse = float(np.sqrt(np.mean((a_ls * s - o) ** 2)))
        ratio = astar[EARLY] / astar[MODERN]
        print(f"  {label:32s} " + "".join(f"{astar[w]:12.5f}" for w, _ in WINDOWS)
              + f"{ratio:14.3f} {rmse:13.3f}")
        rows.append(dict(driver=label, last_year=int(yrs.max()),
                         **{f"alpha_{w}": astar[w] for w, _ in WINDOWS},
                         early_over_modern=ratio, best_alpha=a_ls, rmse_cm=rmse))

    print("\n  early/modern = 1.000 would mean ONE constant expansion coefficient")
    print("  fits both ends of the record. The further from 1, the more the")
    print("  joules->cm efficiency has to change over time.")

    df = pd.DataFrame(rows)
    fair = df.iloc[0]
    others = df.iloc[1:]
    print(f"\n  VERDICT")
    print(f"    FaIR-driven early/modern ratio : {fair.early_over_modern:.3f}")
    for _, r in others.iterrows():
        print(f"    {r.driver:26s}     : {r.early_over_modern:.3f}")
    spread = float(others.early_over_modern.max() - others.early_over_modern.min())
    if (others.early_over_modern - 1.0).abs().max() < 0.10:
        print("\n    The disagreement COLLAPSES on observed OHC -> the defect is the")
        print("    DRIVER (FaIR's OHC), not the expansion coefficient. Re-tuning")
        print("    te_alpha or adding a steric delta(t) would fix the wrong thing.")
    elif (others.early_over_modern - 1.0).abs().min() > 0.15:
        print("\n    The disagreement PERSISTS on every observed product -> the defect")
        print("    is the MODULE. A single constant te_alpha cannot carry the record,")
        print("    which is what a depth/latitude shift in heat uptake would look like.")
    else:
        print(f"\n    MIXED: observed products disagree among themselves by "
              f"{spread:.3f} in the\n    ratio, so this test does not separate the two "
              "hypotheses on its own.\n    The OHC product choice is itself a live "
              "uncertainty (see project_igcc_ohc_finding:\n    IGCC/Cheng 1.57x).")

    df.to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
