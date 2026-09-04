#!/usr/bin/env python3
"""diag_magiccclim_overshoot_penalty.py — the overshoot penalty with DEPTH held fixed.

THE QUESTION. `diag_magicc_overshoot_depth.py` left DEPTH and MODULE confounded: MAGICC's real
ssp534-over − ssp126 overshoot peaks at +0.659 K against FaIR's +0.308 K (2.1x, both in 2059),
while MAGICC-SLR's own 2300 penalty (12.75 cm paired median / 14.28 difference-of-medians, inside
SLEIP's published 8-29 cm band) sits 2.5-5.8x above Ladrillo's 2.21 / 3.43 and BRICK 2.0's
2.57 / 5.66 on our shallower FaIR pair. Depth 2.1x does not close a 2.5-5.8x gap arithmetically,
but penalty-vs-depth is not known to be linear, so the ratio settles nothing.

THE DESIGN. Run Ladrillo's and BRICK 2.0's UNCHANGED modules on MAGICC's OWN ssp534-over/ssp126
climate. Depth becomes IDENTICAL to MAGICC-SLR's; only the modules differ. Whatever gap survives
is structural. ⚠ THIS DECOMPOSES, IT DOES NOT ADJUDICATE — nothing here says whose climate is
right. ⚠ The reverse arm is IMPOSSIBLE (`runnable_is_not_undrivable`): MAGICC-SLR consumes
MAGICC's own climate module, so FaIR's GMST cannot be injected into it.

TWO STATISTICS, ALWAYS BOTH. SLEIP Fig. 8H reports a MEDIAN; Fig. 8B draws a difference of
medians. They separate far more for BRICK 2.0 than for Ladrillo, so quoting one alone has already
misled once here. Both are emitted for every cell.

  python3 python/diag_magiccclim_overshoot_penalty.py
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(REPO, "outputs")
OUT = os.path.join(OUTD, "diag_magiccclim_overshoot_penalty.csv")

SCEN_OS, SCEN_REF = "ssp534over", "ssp126"
PAIR_LABEL = f"{SCEN_OS} - {SCEN_REF} (MAGICC climate)"
ARM = "joint"                       # posterior x climate, the width-comparable arm
COMPONENTS = ["glaciers", "gis", "ais", "te", "lws", "total"]
HORIZONS = [2100, 2150, 2300]

LAD = "scope_slr_fairunc_draws_%s_spliced_magiccclim_L24_tap4p69K_V5p64m_tau800.csv"
BRK = "scope_slr_fairunc_draws_%s_spliced_oldbrick_magiccclim.csv"
MODELS = {"Ladrillo L24": LAD, "BRICK 2.0": BRK}

# prior results, READ not retyped (`derived_must_mean_computed`)
FAIRCLIM = os.path.join(OUTD, "diag_matched_dt_penalty.csv")
FAIRCLIM_PAIR = "matched (dT from ABOVE)"
MAGICC_OWN = os.path.join(OUTD, "diag_magicc_overshoot_depth.csv")


def draws(path_tmpl, scen):
    d = pd.read_csv(os.path.join(OUTD, path_tmpl % scen))
    return d[d.arm == ARM]


def main():
    rows = []
    for model, tmpl in MODELS.items():
        o, r = draws(tmpl, SCEN_OS), draws(tmpl, SCEN_REF)
        key = ["draw", "component", "horizon"]
        m = o.merge(r, on=key, suffixes=("_os", "_ref"))
        # [GATE-PAIR] the per-draw pairing is only meaningful if draw k used the SAME
        # posterior row AND the SAME climate member in both scenarios. Asserted, not assumed:
        # a mismatched permutation would still merge cleanly and quietly compare unlike draws.
        bad = int((m.config_os != m.config_ref).sum())
        n = m.groupby(["component", "horizon"]).size().unique()
        print(f"[GATE-PAIR] {model:<13} {len(m):6d} paired rows, {bad} config mismatches, "
              f"{n} draws/cell  {'PASS' if bad == 0 else 'FAIL'}")
        assert bad == 0, f"{model}: draw->config assignment differs between scenarios"

        for c in COMPONENTS:
            for h in HORIZONS:
                s = m[(m.component == c) & (m.horizon == h)]
                d = (s.value_cm_os - s.value_cm_ref).to_numpy()
                rows.append(dict(
                    model=model, pair=PAIR_LABEL, component=c, horizon=h,
                    penalty_cm=float(np.median(d)),
                    diff_of_medians_cm=float(np.median(s.value_cm_os) - np.median(s.value_cm_ref)),
                    se_cm=float(np.std(d, ddof=1) / np.sqrt(len(d)) * 1.2533),
                    mean_cm=float(np.mean(d)), p05_cm=float(np.percentile(d, 5)),
                    p95_cm=float(np.percentile(d, 95)),
                    ref_level_cm=float(np.median(s.value_cm_ref)), n=len(d)))
    res = pd.DataFrame(rows)
    res.to_csv(OUT, index=False)

    print(f"\n=== OVERSHOOT PENALTY on MAGICC's OWN climate, {PAIR_LABEL}, cm")
    print(f"{'model':<14}{'comp':>9}{'horiz':>7}{'paired med':>12}{'diff of med':>13}"
          f"{'mean':>9}{'p05':>8}{'p95':>9}{'% of ref':>10}")
    for _, x in res.iterrows():
        pct = 100 * x.penalty_cm / x.ref_level_cm if x.ref_level_cm else np.nan
        print(f"{x.model:<14}{x.component:>9}{x.horizon:>7}{x.penalty_cm:>12.2f}"
              f"{x.diff_of_medians_cm:>13.2f}{x.mean_cm:>9.2f}{x.p05_cm:>8.2f}"
              f"{x.p95_cm:>9.2f}{pct:>9.1f}%")

    # ---- the decomposition: same modules, two climates; and MAGICC's own -------------
    fc = pd.read_csv(FAIRCLIM)
    fc = fc[(fc.pair == FAIRCLIM_PAIR) & (fc.component == "total") & (fc.horizon == 2300)]
    mg = pd.read_csv(MAGICC_OWN)
    mg = mg[(mg.component == "total") & (mg.horizon == 2300)].iloc[0]

    print(f"\n=== 2300 TOTAL PENALTY, cm — DEPTH NOW HELD FIXED")
    print(f"{'model':<16}{'climate':<10}{'peak dT':>9}{'paired med':>12}{'diff of med':>13}")
    print(f"{'MAGICC-SLR':<16}{'MAGICC':<10}{'+0.659':>9}{mg.paired_median_cm:>12.2f}"
          f"{mg.diff_of_medians_cm:>13.2f}")
    for model in MODELS:
        n = res[(res.model == model) & (res.component == "total") & (res.horizon == 2300)].iloc[0]
        f = fc[fc.model == model]
        print(f"{model:<16}{'MAGICC':<10}{'+0.659':>9}{n.penalty_cm:>12.2f}"
              f"{n.diff_of_medians_cm:>13.2f}")
        if not f.empty:
            f = f.iloc[0]
            print(f"{'':<16}{'FaIR':<10}{'+0.303':>9}{f.penalty_cm:>12.2f}"
                  f"{f.diff_of_medians_cm:>13.2f}   <- same modules, shallower pair")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
