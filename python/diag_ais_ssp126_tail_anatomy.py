#!/usr/bin/env python3
"""
diag_ais_ssp126_tail_anatomy.py — IS THE ssp126 "SPREAD DEFICIT" A MODEL DEFECT OR A
                                  METRIC ARTIFACT? Measure before changing the physics.

Marcus 2026-08-25 chose to settle the cool-scenario MODEL FORM before running step 5.
The named step-1 defect was:

    "At ssp126 the band has no tipping tail at all -- the fast-dynamics term is EXACTLY
     0.000 cm in every arm and horizon -- while every literature module keeps one."
     (handoff_2026-08-25b §1(3))

⚠ THAT STATEMENT IS A FIXED-DRIVER STATEMENT AND IS FALSE UNDER THE JOINT BAND, which
is the reported band since 2026-08-25. `outputs/diag_ais_tipping_under_forcing_L14.csv`:
per-draw config, the ssp126 tipped fraction is 3.95% / 3.75% / 6.30% at 2100 / 2150 /
2300 -- it is 0.05% / 0.00% / 0.00% only under the shipped MEAN driver. The tail exists.

SO WHY DOES THE BENCHMARK SCORE OUR ssp126 SPREAD AT 0.24-0.33x THE LITERATURE? Because
a p05-p95 spread is STRUCTURALLY BLIND to a mode carrying less than 5% of the mass. At
2100 and 2150 the tipped fraction is BELOW the p95 cut, so the entire tipping tail sits
outside the statistic being scored. This script measures that directly rather than
inferring it: the tipped fraction against the quantile cut, the two subpopulations
separately, and what the band looks like at quantiles the tail can actually reach.

WHAT THIS DOES NOT SETTLE, stated up front so the result is not over-read. It cannot say
whether 3.95% is the RIGHT tipped fraction -- that is a physical question about marine
ice-sheet instability under low forcing, and answering it needs a literature comparison
this repo does not have. What it settles is which QUESTION step 5's precondition is:
"why is our band narrow" (a width problem, fixable by widening) or "is our tipped
fraction right" (a threshold problem, and a different fix entirely).

⚠ THE COMPARISON IS NOT LIKE-FOR-LIKE AT THE TAIL AND SAYS SO. FACTS ships as p05/p17/
med/p83/p95 only (`outputs/facts_components_n200.csv` -- the n=200 samples are reduced
before we see them), so their p99 and their mean cannot be computed here. Every
cross-quantile number below is therefore a BOUND on the question, not a matched
comparison, and is labelled as one.

    source ~/climate-env/bin/activate
    python python/diag_ais_ssp126_tail_anatomy.py [--tag=L14]
Reads   outputs/scope_slr_fairunc_draws_<ssp>_spliced_<TAG>.csv
        outputs/diag_ais_tipping_under_forcing_<TAG>.csv
        benchmark/reference/_fixed/literature_rows.csv
Writes  outputs/diag_ais_ssp126_tail_anatomy_<TAG>.csv
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draws_io import read_draws  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
OUT = os.path.join(REPO, "outputs", f"diag_ais_ssp126_tail_anatomy_{TAG}.csv")
DRAWS = os.path.join(REPO, "outputs", "scope_slr_fairunc_draws_{ssp}_spliced_" + TAG + ".csv")
TIPCSV = os.path.join(REPO, "outputs", f"diag_ais_tipping_under_forcing_{TAG}.csv")
LIT = os.path.join(REPO, "benchmark/reference/_fixed/literature_rows.csv")

COMPONENT = "ais"
ARM = "joint"                      # the reported band since 2026-08-25
SSPS = ["ssp126", "ssp245", "ssp585"]
HORIZONS = [2100, 2150, 2300]
QLO, QHI = 5, 95                   # the benchmark's spread definition -- the thing under test
QHI_TAIL = 99                      # a quantile a <5% mode CAN reach
DRIVER = "per-draw config"         # the joint band's driver; the MEAN driver is the old one
rows = []


def emit(**kw):
    rows.append(kw)


tip = pd.read_csv(TIPCSV)
lit = pd.read_csv(LIT) if os.path.exists(LIT) else None

print("=" * 100)
print(f"ssp126 AIS TAIL ANATOMY ({TAG}) — is the spread deficit a model defect or a metric artifact?")
print("=" * 100)

print("\n[1] THE TIPPED FRACTION AGAINST THE QUANTILE CUT")
print("    A p05-p95 spread cannot see a mode carrying less than 5% of the mass. That is")
print("    arithmetic, not an opinion: the p95 cut sits BELOW the mode's lower edge.")
print(f"\n    {'ssp':8s} {'horizon':8s} {'tipped %':>9s} {'MEAN-driver %':>14s} "
      f"{'p{} sees it?'.format(QHI):>14s}")
for ssp in SSPS:
    for H in HORIZONS:
        a = tip[(tip.ssp == ssp) & (tip.horizon == H) & (tip.driver == DRIVER)]
        b = tip[(tip.ssp == ssp) & (tip.horizon == H) & (tip.driver == "shipped MEAN")]
        if a.empty:
            continue
        f = float(a.tipped_frac.iloc[0])
        sees = f > (100 - QHI) / 100
        print(f"    {ssp:8s} {H:8d} {100*f:9.2f} {100*float(b.tipped_frac.iloc[0]):14.2f} "
              f"{'YES' if sees else 'NO -- BLIND':>14s}")
        emit(block="tipping", ssp=ssp, horizon=H, key="tipped_frac", value=f,
             note=f"MEAN driver {float(b.tipped_frac.iloc[0]):.4f}; "
                  f"p{QHI} {'sees' if sees else 'is BLIND to'} the mode")

print("\n[2] THE TWO SUBPOPULATIONS, SEPARATELY")
print("    A bimodal distribution has no single 'spread'. Splitting at the empirical gap")
print("    shows what each mode contributes -- and whether the untipped mode alone is")
print("    narrow, which is a different defect from the tail being invisible.")
print(f"\n    {'ssp':8s} {'H':>5s} {'p05-p95':>9s} {f'p05-p{QHI_TAIL}':>9s} {'ratio':>6s} "
      f"{'median':>8s} {'MEAN':>8s} {'untipped p50':>13s} {'tipped p50':>11s} {'n_tip':>6s}")
for ssp in SSPS:
    d = read_draws(DRAWS.format(ssp=ssp))
    for H in HORIZONS:
        v = d[(d.horizon == H) & (d.component == COMPONENT) & (d.arm == ARM)].value_cm.values
        if len(v) == 0:
            continue
        f = tip[(tip.ssp == ssp) & (tip.horizon == H) & (tip.driver == DRIVER)]
        frac = float(f.tipped_frac.iloc[0]) if not f.empty else np.nan
        # The split is taken at the tipped FRACTION, not at a hand-picked value: the
        # closed-form tipping calculation already says how many draws tipped, so the
        # top `frac` of the sorted values ARE the tipped mode. No threshold is invented.
        k = int(round(frac * len(v))) if np.isfinite(frac) else 0
        s = np.sort(v)
        tipped, untipped = (s[-k:], s[:-k]) if k > 0 else (np.array([]), s)
        sp95 = np.percentile(v, QHI) - np.percentile(v, QLO)
        sp99 = np.percentile(v, QHI_TAIL) - np.percentile(v, QLO)
        print(f"    {ssp:8s} {H:5d} {sp95:9.2f} {sp99:9.2f} {sp99/sp95:6.2f} "
              f"{np.median(v):8.2f} {v.mean():8.2f} "
              f"{(np.median(untipped) if len(untipped) else np.nan):13.2f} "
              f"{(np.median(tipped) if len(tipped) else np.nan):11.2f} {k:6d}")
        emit(block="subpop", ssp=ssp, horizon=H, key="spread_p05_p95", value=sp95,
             note=f"p05-p{QHI_TAIL} {sp99:.2f} = {sp99/sp95:.2f}x; mean {v.mean():.2f}; "
                  f"median {np.median(v):.2f}; n_tipped {k}")
        emit(block="subpop", ssp=ssp, horizon=H, key="untipped_median",
             value=float(np.median(untipped)) if len(untipped) else np.nan,
             note=f"tipped median {float(np.median(tipped)) if len(tipped) else np.nan:.2f}")

print("\n[3] WHAT THE BENCHMARK IS ACTUALLY SCORING AT ssp126")
print("    ⚠ CROSS-QUANTILE, NOT LIKE-FOR-LIKE. FACTS ships reduced to p05/p17/med/p83/p95,")
print("      so their p99 and their mean do not exist for us to match. The rows below BOUND")
print("      the question -- they do not answer it.")
if lit is not None:
    for H in (2100, 2150):
        L = lit[(lit.component == COMPONENT) & (lit.scenario == "ssp126") & (lit.year == H)]
        if L.empty:
            continue
        lsp = (L.p95.astype(float) - L.p05.astype(float)).dropna().values
        d = read_draws(DRAWS.format(ssp="ssp126"))
        v = d[(d.horizon == H) & (d.component == COMPONENT) & (d.arm == ARM)].value_cm.values
        sp95 = np.percentile(v, QHI) - np.percentile(v, QLO)
        sp99 = np.percentile(v, QHI_TAIL) - np.percentile(v, QLO)
        print(f"\n    ssp126 @{H}: literature p05-p95 {lsp.min():.2f}-{lsp.max():.2f} "
              f"(median {np.median(lsp):.2f}), n={len(lsp)}")
        print(f"      ours p05-p95  {sp95:7.2f} cm = {sp95/np.median(lsp):.2f}x  "
              f"<= what the benchmark scores, and it is BLIND to our tail")
        print(f"      ours p05-p{QHI_TAIL}  {sp99:7.2f} cm = {sp99/np.median(lsp):.2f}x  "
              f"of the literature's p05-p95 -- a BOUND, not a match")
        emit(block="score", ssp="ssp126", horizon=H, key="spread_ratio_p95",
             value=sp95 / np.median(lsp), note=f"lit p05-p95 median {np.median(lsp):.2f}")
        emit(block="score", ssp="ssp126", horizon=H, key="spread_ratio_p99_vs_lit_p95",
             value=sp99 / np.median(lsp), note="CROSS-QUANTILE bound, not like-for-like")

print("\n\n" + "=" * 100)
print("WHAT THIS ESTABLISHES, AND WHAT IT DOES NOT")
print("=" * 100)
print("  ESTABLISHED  The ssp126 tail EXISTS under the joint band (3.75-6.30% of draws) and")
print("               the 'exactly 0.000 cm in every arm and horizon' statement is a")
print("               FIXED-DRIVER statement that does not survive the band we now report.")
print("  ESTABLISHED  At 2100 and 2150 the tipped fraction is BELOW the p95 cut, so the")
print("               scored statistic is arithmetically blind to the tail. The 0.24-0.33x")
print("               'under-dispersion' is therefore NOT evidence of a missing tail.")
print("  NOT SETTLED  Whether 3.95% is the RIGHT tipped fraction at ssp126@2100. That is a")
print("               physical question about marine ice-sheet instability under low forcing")
print("               and it needs a literature comparison this repo does not have.")
print("  ⇒ THE QUESTION CHANGES from 'why is our band narrow' (a WIDTH problem, and the fix")
print("    would be to widen it) to 'is our tipped FRACTION right' (a THRESHOLD problem,")
print("    with a different fix and a different piece of evidence needed).")
print("  ⚠ AND THE MAGNITUDE-DEPENDENT FORK DOES NOT ADDRESS EITHER OF THEM AT ssp126.")
print("    g = (excess/ref)^n is ZERO below threshold for every n, so it changes nothing")
print("    for the 96% of ssp126 draws that never tip. It is the ssp245/ssp585 SEPARATION")
print("    fix (ais_binary_form_priced), not the ssp126 one. Two different binary features:")
print("    binary in MAGNITUDE (the fork fixes it) and binary in ONSET (it does not).")
pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"\nwrote {os.path.relpath(OUT, REPO)}")
