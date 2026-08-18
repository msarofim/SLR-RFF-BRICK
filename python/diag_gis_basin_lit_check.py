#!/usr/bin/env python3
"""
diag_gis_basin_lit_check.py — is the basin mock's PASSING REGION physically
placed? The Mouginot inventory check and the onset-window check, tier 1 of
buying the basin structure.

WHAT IS CHECKED (2026-08-18, after the mock cleared the scorecard)
  The mock (scope_gis_basin_mock_vs_literature.py) found 59/720 cells clearing
  all three 2300 bands + the 2100 spread. That establishes the STRUCTURE can
  represent the literature separation. This script asks whether the passing
  cells' volumes and onsets are numbers the observational and modeling
  literature actually supports:

  1. INVENTORY (Mouginot et al. 2019, PNAS 116:9239, doi 10.1073/pnas.1904242116,
     per-region SLE from the paper's region paragraphs): the dormant-basin
     volumes must fit inside the sectors being invoked. The paper's own
     conclusion is the premise: NO+NE hold "the largest potential SLE (273 cm)
     in Greenland", currently produce LOW discharge (25.9 and 39.5 Gt/yr in
     2018) because their glacier speeds are low while ice shelves still
     buttress them, and their evolution "is therefore of greatest relevance to
     future sea level rise".
  2. DORMANCY TODAY (Mouginot 2019 Dataset S2, on disk): the northern sectors'
     observed 1972-2018 cumulative loss must be small against the active
     sectors' — the premise that the hindcast does not constrain them. Parsed
     per region with the same machinery as build_greenland_partition.py and
     GATED against the paper's printed cumulative losses.
  3. ONSET WINDOW (TC 19:6887, the two forcing arms): under STABILISED
     year-2100 ssp585 climate (GMT ~4.7 K held to 2300) GrIS realises only
     0.282-1.230 m by 2300, while CONTINUED warming to 7.81 K realises
     1.732-3.127 m. The marginal volume tap therefore activates ABOVE the
     stabilised level: onset in (GMT@2100_585, GMT@2300_585]. The ssp245
     stabilised band (0.098-0.218 m at sustained ~3.15 K) excludes large taps
     below 3.15 K. Corroboration: Aschwanden et al. 2019 (Sci. Adv. 5:eaav9396)
     RCP8.5 2300 = 94-374 cm (16-84%), NW outlets land-terminating by 2300,
     discharge still important into the 23rd century.

  NOT independently checked: tau. The relaxation timescale is constrained
  JOINTLY with onset by the scorecard itself; no publication reports a
  per-basin e-folding time to gate against. Stated, not hidden.

  NOTE the onset caveat: NE activation has technically BEGUN (Zachariae
  Isstrom lost its shelf in the 2010s) at ~1.3 K GMT — but at Gt/yr scales,
  i.e. mm/century. The mock's onset is the VOLUME-TAP onset (margin retreat
  into the deep basins), not the first-response onset. The stabilised-arm
  bracket is the right instrument for that quantity.

READS   outputs/scope_gis_basin_mock_vs_literature.csv
        ~/Documents/2026/ClaudeDocs/Papers/Mouginot/pnas.1904242116.sd02.xlsx
        data/observations/fair_mean_gmst_ssp{245,585}.csv (via the harness)
WRITES  outputs/diag_gis_basin_lit_check.csv

  source ~/climate-env/bin/activate
  python3 python/diag_gis_basin_lit_check.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
from build_greenland_partition import (  # noqa: E402  — the sd02 parser, reused
    REGIONS, find_blocks, find_year_header, load_sheet, series,
)
from scope_gis_2300_relaxation import YEARS, gmst_rebased  # noqa: E402

MOCK = os.path.join(REPO, "outputs/scope_gis_basin_mock_vs_literature.csv")
OUT = os.path.join(REPO, "outputs/diag_gis_basin_lit_check.csv")

# ---- Mouginot 2019 per-region SLE, cm (region paragraphs of the paper) ------
MOUGINOT_SLE_CM = {"SW": 74, "CW": 134, "NW": 127, "NO": 93, "NE": 180,
                   "CE": 72, "SE": 55}
MOUGINOT_CITE = "Mouginot et al. 2019, PNAS 116:9239, doi 10.1073/pnas.1904242116"
# the paper's own cumulative 1972-2018 losses, Gt — parse gates for Dataset S2
MOUGINOT_CUM_GT = {"NO": -474, "NE": -532, "NW": -1578, "CW": -738,
                   "CE": -508, "SE": -1108}
CUM_GATE_TOL_GT = 60          # published +/- errors are 30-91 Gt
DORMANCY_WIN = (1972, 2018)
RECENT_WIN = (2010, 2018)

# ---- the basin -> sector mapping being invoked ------------------------------
HIGH_SECTORS = ("NO", "NE")   # the mock's HIGH basin: shelf-buttressed north
MID_SECTORS = ("NW",)         # the mock's MID basin: northwest
V_HIGH_MAX = sum(MOUGINOT_SLE_CM[s] for s in HIGH_SECTORS) / 100.0   # 2.73 m
V_MID_MAX = sum(MOUGINOT_SLE_CM[s] for s in MID_SECTORS) / 100.0     # 1.27 m
V_SINGLE_LOOSE = V_HIGH_MAX + V_MID_MAX                              # 4.00 m

# ---- the onset window, GMT K rel 1850-1900 ----------------------------------
# derived IN-SCRIPT from the fair series; expectations only gate the frame
GMT2100_585_EXPECT, GMT2300_585_EXPECT, GMT2300_245_EXPECT = 4.69, 7.81, 3.15
GMT_TOL = 0.05
ONSET_CITE = ("TC 19:6887 (2025) stabilised arm 0.282-1.230 m vs continued "
              "1.732-3.127 m at 2300; ssp245 stabilised 0.098-0.218 m")
ASCHWANDEN_CITE = ("Aschwanden et al. 2019, Sci. Adv. 5:eaav9396: RCP8.5 2300 "
                   "= 94-374 cm (16-84%); NW outlets land-terminating by 2300")


def sd02_per_region():
    """Per-region cumulative and recent mass balance from Dataset S2, gated
    against the paper's printed cumulative losses."""
    rows = load_sheet()
    years, vcols, _ = find_year_header(rows)
    blocks = find_blocks(rows)
    out = {}
    for reg in REGIONS:
        mb = series(blocks["MB"], reg, years, vcols)
        cum = float(mb.loc[DORMANCY_WIN[0]:DORMANCY_WIN[1]].sum())
        recent = float(mb.loc[RECENT_WIN[0]:RECENT_WIN[1]].mean())
        out[reg] = dict(cum_gt=cum, recent_gt_yr=recent)
    for reg, want in MOUGINOT_CUM_GT.items():
        got = out[reg]["cum_gt"]
        if abs(got - want) > CUM_GATE_TOL_GT:
            raise SystemExit(f"sd02 parse gate FAILED: {reg} cumulative "
                             f"{got:.0f} Gt vs paper {want} Gt")
    return out


def main():
    d = pd.read_csv(MOCK)
    winners = d[d.all_pass].copy()
    if winners.empty:
        raise SystemExit(f"{MOCK} has no passing cells — nothing to check")

    # ---- frame: the GMT levels the onset window hangs on --------------------
    i21 = int(np.where(YEARS == 2100)[0][0])
    i23 = int(np.where(YEARS == 2300)[0][0])
    g585 = gmst_rebased("ssp585")[1]
    g245 = gmst_rebased("ssp245")[1]
    lvl = {"gmt2100_585": float(g585[i21]), "gmt2300_585": float(g585[i23]),
           "gmt2300_245": float(g245[i23])}
    for got, want in ((lvl["gmt2100_585"], GMT2100_585_EXPECT),
                      (lvl["gmt2300_585"], GMT2300_585_EXPECT),
                      (lvl["gmt2300_245"], GMT2300_245_EXPECT)):
        if abs(got - want) > GMT_TOL:
            raise SystemExit(f"GMT frame check failed: {got:.3f} vs {want}")

    print("IS THE BASIN MOCK'S PASSING REGION PHYSICALLY PLACED?  — tier 1")
    print(f"  {len(winners)} passing cells from the mock; checks: inventory "
          f"({MOUGINOT_CITE}),\n  dormancy (Dataset S2), onset window "
          f"({ONSET_CITE})\n")

    # ---- 1. the dormancy premise, from the data on disk ---------------------
    per = sd02_per_region()
    print("=== DORMANCY TODAY — Mouginot Dataset S2, parse-gated vs the paper ===\n")
    print(f"  {'region':7s} {'SLE cm':>7s} {'cum 1972-2018 Gt':>17s} "
          f"{'2010-2018 Gt/yr':>16s}")
    tot_cum = sum(p["cum_gt"] for r, p in per.items() if r != "GIS")
    for reg in ("SW", "CW", "NW", "CE", "SE", "NO", "NE"):
        p = per[reg]
        print(f"  {reg:7s} {MOUGINOT_SLE_CM[reg]:7d} {p['cum_gt']:17.0f} "
              f"{p['recent_gt_yr']:16.1f}")
    hi_cum = sum(per[r]["cum_gt"] for r in HIGH_SECTORS)
    print(f"\n  {'+'.join(HIGH_SECTORS)} hold {100 * V_HIGH_MAX:.0f} cm SLE "
          f"({100.0 * (100 * V_HIGH_MAX) / sum(MOUGINOT_SLE_CM.values()):.0f}% of "
          f"the ice sheet) but contributed {100 * hi_cum / tot_cum:.0f}% of the "
          f"1972-2018 loss —")
    print("  the dormant-volume premise, in the observational record. "
          "(The paper's own words:\n  their evolution is 'of greatest relevance "
          "to future sea level rise'.)\n")

    # ---- 2 + 3. gate the passing cells --------------------------------------
    win = (lvl["gmt2100_585"], lvl["gmt2300_585"])
    winners["inv_strict"] = np.where(
        winners.mid_share == 0,
        winners.v_tot <= V_HIGH_MAX,
        (winners.v_high <= V_HIGH_MAX) & (winners.v_mid <= V_MID_MAX))
    winners["inv_loose"] = np.where(
        winners.mid_share == 0,
        winners.v_tot <= V_SINGLE_LOOSE,
        (winners.v_high <= V_HIGH_MAX) & (winners.v_mid <= V_MID_MAX))
    winners["onset_concentrated"] = ((winners.t_on_high > win[0])
                                     & (winners.t_on_high <= win[1]))
    winners["onset_wide"] = np.where(
        winners.mid_share == 0, True,
        winners.t_on_mid > lvl["gmt2300_245"])   # no tap below sustained ssp245
    winners["lit_ok_strict"] = (winners.inv_strict & winners.onset_concentrated
                                & winners.onset_wide)
    winners["lit_ok_loose"] = (winners.inv_loose & winners.onset_concentrated
                               & winners.onset_wide)

    print("=== GATES on the 59 passers ===\n")
    print(f"  inventory STRICT (high<= {V_HIGH_MAX:.2f} m = "
          f"{'+'.join(HIGH_SECTORS)}; mid <= {V_MID_MAX:.2f} m = "
          f"{'+'.join(MID_SECTORS)}; single basin <= {V_HIGH_MAX:.2f}): "
          f"{int(winners.inv_strict.sum())} / {len(winners)}")
    print(f"  inventory LOOSE  (single basin may span "
          f"{'+'.join(HIGH_SECTORS + MID_SECTORS)} <= {V_SINGLE_LOOSE:.2f} m): "
          f"{int(winners.inv_loose.sum())} / {len(winners)}")
    print(f"  onset in the stabilised-vs-continued bracket "
          f"({win[0]:.2f}, {win[1]:.2f}] K GMT: "
          f"{int(winners.onset_concentrated.sum())} / {len(winners)}")
    print(f"  mid onset above sustained-ssp245 {lvl['gmt2300_245']:.2f} K: "
          f"{int(winners.onset_wide.sum())} / {len(winners)}")
    print(f"\n  SURVIVING, strict: {int(winners.lit_ok_strict.sum())}   "
          f"loose: {int(winners.lit_ok_loose.sum())}")

    surv = winners[winners.lit_ok_strict]
    if len(surv):
        print("\n=== the literature-consistent region (strict) ===\n")
        for knob in ["t_on_mid", "t_on_high", "v_tot", "mid_share", "tau"]:
            print(f"  {knob:10s} {sorted(surv[knob].unique())}")
        print(f"  ratio span  {surv.ratio_585_over_245.min():.1f}x - "
              f"{surv.ratio_585_over_245.max():.1f}x")
        best = surv.loc[(surv["m2300_SSP5-8.5"]
                         - 0.5 * (1.732 + 3.127)).abs().idxmin()]
        print(f"\n  exemplar: onsets {best.t_on_mid:g}/{best.t_on_high:g} K, "
              f"V {best.v_tot:g} m (mid {best.v_mid:g} + high {best.v_high:g}), "
              f"tau {best.tau:g} ->\n    2300 = {best['m2300_SSP1-2.6']:.3f} / "
              f"{best['m2300_SSP2-4.5']:.3f} / {best['m2300_SSP5-8.5']:.3f} m, "
              f"ratio {best.ratio_585_over_245:.1f}x, "
              f"G4 {best.g4_rel_to_ref:.3f}x")
    print(f"\n  corroboration: {ASCHWANDEN_CITE}")
    print("  NOT independently gated: tau (jointly constrained by the "
          "scorecard; no per-basin\n  published e-folding time exists to "
          "gate against).")

    winners.to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
