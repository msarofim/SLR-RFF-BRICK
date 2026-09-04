#!/usr/bin/env python3
"""
diag_magicc_overshoot_depth.py — how deep is the REAL SSP5-3.4-OS overshoot, and what
penalty does MAGICC-SLR itself carry on it?

Answers `LADRILLO.md` §7 open item 5 (and closes the loop on item 4, which the SLEIP
preprint settled: their penalty is a MEDIAN, Fig. 8H caption).

THE QUESTION. Our matched-dT pair (`note_2026-09-02_matched_dt_overshoot_pair.md`) gives a
2300 penalty of ~2.2 cm (Ladrillo) / ~2.6 cm (BRICK 2.0) as a PAIRED MEDIAN, against SLEIP's
8-29 cm across ten emulators -- with SLEIP's BRICK the LARGEST at 34 % of the SSP1-2.6 2300
total. Same model family, 5-11x apart. Two candidate explanations survive:
  (H1) SCENARIO DEPTH -- our idealised `ssp534overMATCH` peaks only +0.311 K over its
       reference, and if MAGICC's real SSP5-3.4-OS is much deeper the gap is scenario, not
       module.
  (H2) MODULE PHYSICS -- something in DAIS/Ladrillo genuinely under-responds to overshoot.
This script measures H1 directly and, as its gate, reproduces MAGICC-SLR's OWN penalty on
its OWN climate -- which is one of the ten numbers SLEIP plots in Fig. 8H.

⚠ SOURCE. The repo's canonical MAGICC extract (`extract_magicc_components.py`) reads this
same file but its SSPS list OMITS ssp534-over, so the overshoot scenario has never been
pulled before. Conventions (cm, component map, per-member sums before quantiles) are copied
from that extractor so the numbers are comparable to `data/comparison/magicc_nauels_components.csv`.

  python3 python/diag_magicc_overshoot_depth.py
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.expanduser(
    "~/Documents/2026/CodeProjects/MAGICC/slr-refresh/data/processed/"
    "SSPs_Nauels2025_withOCH_2026_06_16_100817.csv")
OURS = os.path.join(REPO, "outputs/diag_matched_dt_penalty.csv")
OUT = os.path.join(REPO, "outputs/diag_magicc_overshoot_depth.csv")

# --- the pair, named once; every label below derives from these ------------------------
SCEN_OS = "ssp534-over"          # SLEIP's overshoot arm
SCEN_REF = "ssp126"              # SLEIP's reference arm
PAIR_LABEL = f"{SCEN_OS} - {SCEN_REF}"
MODEL_LABEL = "MAGICC-SLR v7.5.3 (Nauels 2025), 600-member AR6 drawnset"

HORIZONS = [2100, 2150, 2300]
CONVERGENCE_YEAR = 2150          # SLEIP: "the two scenario GSAT trajectories reconverge"
BASE_YEARS = list(range(1995, 2015))   # AR6 / SLEIP baseline; cancels in a difference
MM_TO_CM = 0.1

# our own matched-pair numbers are READ, never retyped -- `derived_must_mean_computed`
OUR_MODELS = ["Ladrillo L24", "BRICK 2.0"]
OUR_PAIR = "matched (dT from ABOVE)"
OUR_PEAK_EXCESS_K = 0.311        # from note_2026-09-02, quoted as the thing under test

COMPONENT_MAP = {
    "te":       ["SLR_EXPANSION"],
    "glaciers": ["SLR_GL"],
    "gis":      ["SLR_GIS_SMB", "SLR_GIS_SID"],
    "ais":      ["SLR_AIS_SMB", "SLR_AIS_SID"],
    "lws":      ["SLR_LANDWATER"],
    "total":    ["Sea Level Rise"],
}
GSAT_VAR = "Surface Air Temperature Change"

# SLEIP Fig. 8H / §4.4, read off egusphere-2026-3874 -- the band our MAGICC must land in
SLEIP_PENALTY_LO_CM, SLEIP_PENALTY_HI_CM = 8.0, 29.0
SLEIP_LABEL = f"SLEIP Phase 1 (egusphere-2026-3874), 2300 penalty across 10 datasets"


def load_pair():
    df = pd.read_csv(SOURCE)
    ycols = [c for c in df.columns if c[:4].isdigit()]
    df = df.rename(columns={c: int(c[:4]) for c in ycols})
    years = sorted(int(c[:4]) for c in ycols)
    df = df[df.scenario.isin([SCEN_OS, SCEN_REF])]
    missing = [y for y in HORIZONS if y not in years]
    if missing:
        raise SystemExit(f"[YEARS-PRESENT] source lacks {missing}; spans {min(years)}-{max(years)}")
    print(f"[YEARS-PRESENT] source spans {min(years)}-{max(years)}")
    return df, years


def wide(df, var, scen):
    """members x years for one variable and scenario, indexed by ensemble_member."""
    sub = df[(df.variable == var) & (df.scenario == scen)]
    ycols = [c for c in sub.columns if isinstance(c, (int, np.integer))]
    return sub.set_index("ensemble_member")[ycols].sort_index()


def main():
    df, years = load_pair()
    os_m = wide(df, GSAT_VAR, SCEN_OS)
    rf_m = wide(df, GSAT_VAR, SCEN_REF)

    # [GATE-PAIR] per-member pairing is only valid if the member sets match exactly.
    assert os_m.index.equals(rf_m.index), "ensemble members do not align across the pair"
    print(f"[GATE-PAIR] {len(os_m)} members align across {PAIR_LABEL}")

    # [GATE-BASE] the two scenarios share history, so the AR6 baseline CANCELS in the
    # difference. Assert it rather than assume it -- if it does not hold, every number
    # below inherits a baseline offset.
    base_gap = float((os_m[BASE_YEARS].mean(axis=1) - rf_m[BASE_YEARS].mean(axis=1)).abs().max())
    print(f"[GATE-BASE] max |member baseline gap| over {BASE_YEARS[0]}-{BASE_YEARS[-1]}: "
          f"{base_gap:.3e} K -- baseline cancels in the difference")
    assert base_gap < 1e-6, f"scenarios differ over the baseline by {base_gap:.3e} K"

    # ---------------- H1: how deep is the real overshoot? ------------------------------
    dT = os_m - rf_m                                   # members x years
    med_dT = dT.median(axis=0)
    peak_of_median = float(med_dT.max())
    peak_year = int(med_dT.idxmax())
    median_of_peaks = float(dT.max(axis=1).median())

    print()
    print(f"=== H1  OVERSHOOT DEPTH -- {MODEL_LABEL}")
    print(f"    pair: {PAIR_LABEL}")
    print(f"    peak of the MEDIAN dT     : {peak_of_median:+.3f} K  (at {peak_year})")
    print(f"    median of per-member peak : {median_of_peaks:+.3f} K")
    for y in [CONVERGENCE_YEAR, 2300]:
        print(f"    median dT @{y}            : {float(med_dT[y]):+.3f} K")
    print(f"    OUR idealised pair peak   : {OUR_PEAK_EXCESS_K:+.3f} K "
          f"(ssp534overMATCH, note_2026-09-02)")
    print(f"    ⇒ MAGICC's real overshoot is {peak_of_median / OUR_PEAK_EXCESS_K:.2f}x "
          f"as deep as the pair our penalty was measured on")

    # ---------------- MAGICC-SLR's own penalty, both statistics -----------------------
    rows = []
    print()
    print(f"=== MAGICC-SLR PENALTY on its OWN climate ({PAIR_LABEL}), cm")
    print(f"{'component':>10} {'horizon':>8} {'paired med':>11} {'diff of med':>12} "
          f"{'p05':>8} {'p95':>9} {'% of ref':>9}")
    for comp, varlist in COMPONENT_MAP.items():
        o = sum(wide(df, v, SCEN_OS) for v in varlist) * MM_TO_CM
        r = sum(wide(df, v, SCEN_REF) for v in varlist) * MM_TO_CM
        o = o.sub(o[BASE_YEARS].mean(axis=1), axis=0)
        r = r.sub(r[BASE_YEARS].mean(axis=1), axis=0)
        d = o - r
        for y in HORIZONS:
            paired = float(d[y].median())
            diffmed = float(o[y].median() - r[y].median())
            ref_level = float(r[y].median())
            pct = 100.0 * paired / ref_level if ref_level else np.nan
            rows.append(dict(model="MAGICC-SLR", pair=PAIR_LABEL, component=comp, horizon=y,
                             paired_median_cm=paired, diff_of_medians_cm=diffmed,
                             p05_cm=float(d[y].quantile(.05)), p95_cm=float(d[y].quantile(.95)),
                             ref_level_cm=ref_level, pct_of_ref=pct, n=len(d)))
            print(f"{comp:>10} {y:>8} {paired:>11.2f} {diffmed:>12.2f} "
                  f"{float(d[y].quantile(.05)):>8.2f} {float(d[y].quantile(.95)):>9.2f} "
                  f"{pct:>8.1f}%")

    # [GATE-SLEIP] MAGICC-SLR is one of the ten datasets in SLEIP Fig. 8H. If our
    # reproduction of ITS OWN penalty lands outside their stated band, the disagreement
    # is in this pipeline, not in Ladrillo. ⚠ This is a RANGE check against a published
    # number, not a point identity -- their drawnset and LWS handling differ from ours.
    tot = [r for r in rows if r["component"] == "total" and r["horizon"] == 2300][0]
    inband = SLEIP_PENALTY_LO_CM <= tot["paired_median_cm"] <= SLEIP_PENALTY_HI_CM
    print()
    print(f"[GATE-SLEIP] MAGICC-SLR 2300 paired-median penalty {tot['paired_median_cm']:.2f} cm "
          f"vs {SLEIP_LABEL} band {SLEIP_PENALTY_LO_CM:.0f}-{SLEIP_PENALTY_HI_CM:.0f} cm: "
          f"{'IN BAND' if inband else '⚠ OUT OF BAND'}")

    # ---------------- side by side with our two models --------------------------------
    ours = pd.read_csv(OURS)
    ours = ours[(ours.pair == OUR_PAIR) & (ours.component == "total")]
    print()
    print(f"=== 2300 TOTAL PENALTY, cm -- MAGICC on the REAL pair vs ours on the IDEALISED pair")
    print(f"{'model':>16} {'pair':>34} {'paired med':>11} {'diff of med':>12}")
    print(f"{'MAGICC-SLR':>16} {PAIR_LABEL:>34} {tot['paired_median_cm']:>11.2f} "
          f"{tot['diff_of_medians_cm']:>12.2f}")
    for m in OUR_MODELS:
        row = ours[(ours.model == m) & (ours.horizon == 2300)]
        if row.empty:
            print(f"{m:>16} -- absent from {os.path.basename(OURS)}")
            continue
        row = row.iloc[0]
        print(f"{m:>16} {'ssp534overMATCH - ssp126':>34} {row.penalty_cm:>11.2f} "
              f"{row.diff_of_medians_cm:>12.2f}")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print()
    print(f"wrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
