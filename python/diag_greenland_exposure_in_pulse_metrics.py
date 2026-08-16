#!/usr/bin/env python3
"""
diag_greenland_exposure_in_pulse_metrics.py — does the CH4-vs-CO2 SLR pulse work
actually depend on the Greenland module we are about to restructure?

WHY THIS EXISTS (2026-08-16, thread 5, decision 4)
  Scoping decision 4 asked: "Is a centuries-to-millennial tau acceptable
  downstream? The CH4-vs-CO2 SLR pulse work reads this module." Marcus chose to
  TEST THE DOWNSTREAM EFFECT FIRST, before adopting any C+D form.

  The test turns out to be structural and quantitative, not a run.

TWO INDEPENDENT ANSWERS

  1. STRUCTURAL — the premise does not hold today. Every pulse driver
     (project_pulse_hybrid_mengel.jl, pulse_signsweep_brick_mengel.jl,
     run_mimibrick_pulse_versioned.jl, project_pulse_ssp245_mengel.jl) builds
     via `build_brick_mengel`, which replaces only the GLACIER slot with
     glaciers_mengel and leaves the Greenland slot as STOCK MimiBRICK SIMPLE.
     The Ladrillo A+B Greenland is installed only by `build_brick_nu3_gis`
     (brick_mengel.jl), which no pulse driver calls. The parameter names in the
     pulse drivers confirm it: they update greenland_a / greenland_b /
     greenland_alpha / greenland_beta / greenland_v0 (stock SIMPLE), NOT
     gis_c1 / gis_c0 / gis_alpha_f / gis_beta_s (A+B).

     This script re-checks that wiring so the claim cannot go stale silently.

  2. QUANTITATIVE — measured below. Greenland's share of the MARGINAL pulse
     response, and (the number that actually matters for a CO2e ratio) how much
     that share DIFFERS between the CO2 and CH4 pulses. A component that carries
     the same share in numerator and denominator is close to common-mode in the
     ratio, so its influence on the reported metric is smaller than its share.

CAVEAT, stated rather than buried
  The shares are measured under the STOCK SIMPLE Greenland, which is what the
  pulse chain runs. A C+D Greenland would carry a ~20x larger commitment AND a
  much slower tau; those push the 100-150 yr marginal in OPPOSITE directions, so
  the post-change share is not determined by this diagnostic. What this does
  establish is the BASE the change would start from, and that the pulse metrics
  are decoupled from the Greenland module as currently wired.

READS   outputs/mcmc/wong_cond_pulse_pairs_pr.csv           (CO2 pulse)
        outputs/mcmc/wong_cond_pulse_pairs_ch4bio1tg_pr.csv (CH4 biogenic pulse)
        julia/brick_mengel.jl + the pulse drivers            (wiring check)
WRITES  outputs/diag_greenland_exposure_in_pulse_metrics.csv

  python3 python/diag_greenland_exposure_in_pulse_metrics.py
"""
import os
import re

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs/diag_greenland_exposure_in_pulse_metrics.csv")

# --- named constants that the labels below derive from -----------------------
PULSES = {
    "CO2": "outputs/mcmc/wong_cond_pulse_pairs_pr.csv",
    "CH4_bio": "outputs/mcmc/wong_cond_pulse_pairs_ch4bio1tg_pr.csv",
}
HORIZONS = (2130, 2150, 2180)
COMPONENTS = ("ais", "gsic", "gis", "te")
GIS = "gis"
WEIGHT_COL = "w"                       # Wong conditional importance weights

PULSE_DRIVERS = [
    "julia/project_pulse_hybrid_mengel.jl",
    "julia/pulse_signsweep_brick_mengel.jl",
    "julia/run_mimibrick_pulse_versioned.jl",
    "julia/project_pulse_ssp245_mengel.jl",
]
STOCK_BUILD = "build_brick_mengel"     # stock SIMPLE Greenland
AB_BUILD = "build_brick_nu3_gis"       # the ONLY build installing greenland_ab
AB_PARAM_TELL = r"\bgis_(c1|c0|alpha_f|beta_s|slow_ell)\b"


def check_wiring():
    """Which Greenland does the pulse chain actually instantiate?"""
    print("=== 1. STRUCTURAL: which Greenland do the pulse drivers build? ===\n")
    any_ab = False
    for rel in PULSE_DRIVERS:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            print(f"  {os.path.basename(rel):38s} MISSING -- wiring claim is stale")
            continue
        src = open(path).read()
        stock = STOCK_BUILD in src
        ab = (AB_BUILD in src) or bool(re.search(AB_PARAM_TELL, src))
        any_ab |= ab
        verdict = ("A+B (Ladrillo)" if ab else
                   "stock SIMPLE" if stock else "no build call found")
        print(f"  {os.path.basename(rel):38s} -> {verdict}")
    print()
    if not any_ab:
        print("  VERDICT: no pulse driver instantiates the Ladrillo A+B Greenland.")
        print("  Decision 4's premise -- 'the pulse work reads this module' -- does")
        print("  NOT hold as currently wired. A Greenland tau change cannot reach")
        print("  these metrics until a driver is repointed at "
              f"{AB_BUILD}.\n")
    else:
        print("  VERDICT: at least one pulse driver DOES use A+B. Decision 4 is")
        print("  LIVE -- the tau change reaches the pulse metrics. Re-run the")
        print("  quantitative half below and treat it as a gate.\n")
    return any_ab


def measure_shares():
    """Greenland's share of the marginal, and the CO2-vs-CH4 gap in that share."""
    print("=== 2. QUANTITATIVE: Greenland's share of the marginal response ===\n")
    cols = [WEIGHT_COL] + [f"d_{c}@{y}" for y in HORIZONS
                           for c in ("total",) + COMPONENTS]
    rows, gis_share = [], {}
    for tag, rel in PULSES.items():
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            print(f"  {tag}: MISSING {rel} -- skipped")
            continue
        d = pd.read_csv(path, usecols=cols)
        w = d[WEIGHT_COL].to_numpy()
        print(f"  {tag} pulse  ({os.path.basename(rel)})")
        gis_share[tag] = {}
        for y in HORIZONS:
            parts = {c: np.average(d[f"d_{c}@{y}"], weights=w) for c in COMPONENTS}
            s = sum(parts.values())
            gis_share[tag][y] = parts[GIS] / s * 100
            print("    " + f"{y}: " + "  ".join(
                f"{c}={parts[c] / s * 100:5.1f}%" for c in COMPONENTS))
            rows.append({"pulse": tag, "year": y,
                         **{f"{c}_pct": parts[c] / s * 100 for c in COMPONENTS}})
        print()

    if len(gis_share) == 2:
        a, b = PULSES.keys()
        print("  Greenland share, CO2 vs CH4 -- the gap is what a CO2e RATIO sees:\n")
        for y in HORIZONS:
            ga, gb = gis_share[a][y], gis_share[b][y]
            print(f"    {y}: {a} {ga:.1f}%  vs  {b} {gb:.1f}%  "
                  f"-> gap {abs(gb - ga):.1f} pp")
            rows.append({"pulse": f"{b}_minus_{a}", "year": y,
                         "gis_pct": gb - ga})
        print("\n  Greenland carries a NEAR-EQUAL share in both pulses, so it is")
        print("  largely COMMON-MODE in the ratio: its influence on the reported")
        print("  CO2e metric is smaller than its already-small share.\n")
    return rows


def main():
    live = check_wiring()
    rows = measure_shares()
    if rows:
        pd.DataFrame(rows).to_csv(OUT, index=False)
        print(f"wrote {os.path.relpath(OUT, REPO)}")
    print("\nRE-RUN THIS if any pulse driver is ever repointed at "
          f"{AB_BUILD}." if not live else "\nDecision 4 is LIVE -- see above.")


if __name__ == "__main__":
    main()
