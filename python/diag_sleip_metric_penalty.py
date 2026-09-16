#!/usr/bin/env python3
"""diag_sleip_metric_penalty.py — every arm we have, in SLEIP's OWN metric.

THE METRIC, read off egusphere-2026-3874 rather than assumed:
  * quantity  TOTAL GMSLR (not a component)
  * statistic DIFFERENCE OF MEDIANS between the overshoot arm and the reference arm.
              Fig. 8B: "Median total sea level response ... the overshoot penalty is the
              vertical gap (dashed to full line) between scenario pairs"; Fig. 8H summarises
              that as "the median total SLR difference". ⚠ NOT the paired median of per-draw
              differences -- the two separate by >2x for BRICK 2.0, so the choice is not cosmetic.
  * horizons  2150 and 2300 (Fig. 8H reports both)
  * units     metres in the abstract, cm in Sect. 4.4; both printed here
  * share     "an additional 6 % (FACTS_1f) to 34 % (BRICK) of total 2300 GMSLR relative to
              the SSP1-2.6 2300 response" -> penalty@2300 / reference-total@2300
  * forcing   MAGICC-forced. SLEIP reports NO native-forced penalty, so our FaIR-climate rows
              have no published counterpart and are OUR addition, not a comparison to theirs.

⚠ OUR FaIR-CLIMATE PAIR IS THE IDEALISED `ssp534overMATCH`, not SSP5-3.4-OS: FaIR's native pair
INVERTS after 2150. The MAGICC-climate rows use MAGICC's NATIVE pair. Post-convergence residuals
are close (+0.044 vs +0.035 K @2150) but the two are NOT identically constructed.

⛔ FACTS ON MAGICC'S CLIMATE IS **RUNNABLE, NOT RUN** (`runnable_is_not_undrivable`): the
`global.coupling.ssp245.magicc{base,pulse,p10gt}` experiments prove FACTS accepts a MAGICC climate
step, but no overshoot-pair arm exists. That cell is reported as absent, never interpolated.

  python3 python/diag_sleip_metric_penalty.py
"""
import os

import numpy as np
import pandas as pd
import ladrillo_figs as _lf  # tap stem from the Julia GIS_TAP_CELL, never a literal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(REPO, "outputs")
FACTS = os.path.expanduser("~/Documents/2026/CodeProjects/facts/experiments")
OUT = os.path.join(OUTD, "diag_sleip_metric_penalty.csv")

HORIZONS = [2150, 2300]
MM_TO_CM = 0.1
ARM = "joint"

# --- SLEIP's own published values, for the comparison column ----------------------------
SLEIP = {"range_cm": (8.0, 29.0), "lo_name": "FACTS_1f", "hi_name": "FACTS_3f",
         "lo_pct": 6.0, "hi_pct": 34.0, "hi_pct_name": "BRICK"}

# --- our FaIR-climate pair --------------------------------------------------------------
FAIR_REF, FAIR_OS = "ssp126_nomarker", "ssp534overMATCH"
LAD_T = "scope_slr_fairunc_draws_%s_spliced_" + _lf.joint_stem("L24") + ".csv"
BRK_T = "scope_slr_fairunc_draws_%s_spliced_oldbrick.csv"
# --- our MAGICC-climate pair ------------------------------------------------------------
MAG_REF, MAG_OS = "ssp126", "ssp534over"
LAD_M = "scope_slr_fairunc_draws_%s_spliced_magiccclim_" + _lf.joint_stem("L24") + ".csv"
BRK_M = "scope_slr_fairunc_draws_%s_spliced_oldbrick_magiccclim.csv"
# --- FACTS, FaIR climate only -----------------------------------------------------------
FACTS_ARMS = ("global.shared.ssp126nomarker2300.n200", "global.shared.ssp534overMATCH2300.n200")
WF = {"wf1f": "FACTS wf1f IPCC-AR5", "wf2f": "FACTS wf2f LARMIP-2",
      "wf3f": "FACTS wf3f DeConto/Kopp", "wf4": "FACTS wf4 Bamber-SEJ"}


def total_series(tmpl, scen):
    d = pd.read_csv(os.path.join(OUTD, tmpl % scen))
    d = d[(d.arm == ARM) & (d.component == "total")]
    return {h: d[d.horizon == h].value_cm.to_numpy() for h in HORIZONS}


def facts_total(key, wf):
    import netCDF4 as nc4
    p = os.path.join(FACTS, key, "output", "%s.total.workflow.%s.global.nc" % (key, wf))
    if not os.path.exists(p):
        return None, None
    d = nc4.Dataset(p)
    return np.asarray(d.variables["sea_level_change"][:, :, 0]) * MM_TO_CM, \
        np.asarray(d.variables["years"][:])


def add(rows, model, climate, os_, ref):
    for h in HORIZONS:
        a, b = os_[h], ref[h]
        rows.append(dict(model=model, climate=climate, horizon=h,
                         diff_of_medians_cm=float(np.median(a) - np.median(b)),
                         paired_median_cm=float(np.median(a - b)) if a.shape == b.shape else np.nan,
                         ref_total_cm=float(np.median(b)), n=len(a)))


def main():
    rows = []
    for model, tf, tm in (("Ladrillo L24", LAD_T, LAD_M), ("BRICK 2.0", BRK_T, BRK_M)):
        add(rows, model, "FaIR", total_series(tf, FAIR_OS), total_series(tf, FAIR_REF))
        add(rows, model, "MAGICC", total_series(tm, MAG_OS), total_series(tm, MAG_REF))

    for wf, label in WF.items():
        B, yb = facts_total(FACTS_ARMS[0], wf)
        A, ya = facts_total(FACTS_ARMS[1], wf)
        if A is None or B is None:
            print(f"  [MISSING] {label}")
            continue
        assert np.array_equal(ya, yb) and A.shape == B.shape
        o = {h: A[:, int(np.where(ya == h)[0][0])] for h in HORIZONS}
        r = {h: B[:, int(np.where(yb == h)[0][0])] for h in HORIZONS}
        add(rows, label, "FaIR", o, r)

    # MAGICC-SLR itself, already in SLEIP's metric from the depth diagnostic
    mg = pd.read_csv(os.path.join(OUTD, "diag_magicc_overshoot_depth.csv"))
    mg = mg[mg.component == "total"]
    for h in HORIZONS:
        x = mg[mg.horizon == h].iloc[0]
        rows.append(dict(model="MAGICC-SLR", climate="MAGICC", horizon=h,
                         diff_of_medians_cm=float(x.diff_of_medians_cm),
                         paired_median_cm=float(x.paired_median_cm),
                         ref_total_cm=float(x.ref_level_cm), n=int(x.n)))

    res = pd.DataFrame(rows)
    ref2300 = {(m, c): float(v) for (m, c), v in
               res[res.horizon == 2300].set_index(["model", "climate"]).ref_total_cm.items()}
    res["pct_of_ref_2300"] = [100 * r.diff_of_medians_cm / ref2300[(r.model, r.climate)]
                              for _, r in res.iterrows()]
    res.to_csv(OUT, index=False)

    lo, hi = SLEIP["range_cm"]
    print("=" * 100)
    print("OVERSHOOT PENALTY IN SLEIP'S METRIC — total GMSLR, DIFFERENCE OF MEDIANS, "
          "overshoot minus reference")
    print(f"SLEIP abstract: 'roughly 0.1 to 0.3 m persists by 2300'  = {lo:.0f}-{hi:.0f} cm "
          f"({SLEIP['lo_name']} to {SLEIP['hi_name']}), {SLEIP['lo_pct']:.0f}-{SLEIP['hi_pct']:.0f} % "
          f"of the SSP1-2.6 2300 total")
    print("=" * 100)
    print(f"{'model':<24}{'climate':<9}{'@2150 m':>10}{'@2300 m':>10}{'@2300 cm':>10}"
          f"{'% of ref':>10}{'in 0.1-0.3 m?':>15}")
    for m in ["MAGICC-SLR", "BRICK 2.0", "Ladrillo L24"] + list(WF.values()):
        for c in ["MAGICC", "FaIR"]:
            s = res[(res.model == m) & (res.climate == c)]
            if s.empty:
                continue
            a = float(s[s.horizon == 2150].diff_of_medians_cm.iloc[0])
            b = float(s[s.horizon == 2300].diff_of_medians_cm.iloc[0])
            p = float(s[s.horizon == 2300].pct_of_ref_2300.iloc[0])
            print(f"{m:<24}{c:<9}{a/100:>10.3f}{b/100:>10.3f}{b:>10.2f}{p:>9.1f}%"
                  f"{('YES' if lo <= b <= hi else 'below' if b < lo else 'above'):>15}")
        if m.startswith("FACTS"):
            print(f"{'':<24}{'MAGICC':<9}{'— RUNNABLE, NOT RUN (no overshoot-pair arm)':>60}")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
