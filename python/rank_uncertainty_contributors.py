#!/usr/bin/env python3
"""
rank_uncertainty_contributors.py — WHAT ACTUALLY CARRIES THE REPORTED BAND NOW?

WHY THIS EXISTS (2026-08-25)
  Marcus promoted the FaIR-uncertainty band to the reported band, then asked for a
  new priority ranking. Every ranking in handoff_2026-08-24i was computed on the
  FIXED-driver band, where AIS was 94.7-100.9% of the total spread at every cell.
  With the forcing spread restored that share falls to 73-79%
  (`ais_share_was_a_fixed_driver_artifact`), so the ranking's own denominator moved
  and the ordering has to be recomputed, not adjusted.

WHAT IT RANKS, AND THE ONE HONEST WAY TO DO IT
  A p05-p95 spread is NOT additive, so "component X is N% of the total spread" is a
  ratio of widths, not a decomposition, and the shares do not sum to 1. Two
  complementary measures are reported and BOTH are labelled:

    share_of_width   spread(component) / spread(total). Intuitive, not additive,
                     and can exceed 100% (it does, at ssp585 fixed).
    var_share        var(component) / sum over components of var(). Additive by
                     construction, and the covariances are reported separately as
                     `cov_residual` so the non-additivity is VISIBLE rather than
                     hidden inside a normalisation.

  The FORCING contribution per component is spread(joint) - spread(fixed), i.e. what
  restoring the climate uncertainty added to that component specifically.

  THE METRIC THAT ACTUALLY RANKS THE WORK is `pct_forcing` = (joint - fixed)/joint:
  the fraction of a component's band that is INHERITED FROM FaIR rather than
  generated inside BRICK. Model work on that component can only ever address the
  complement, `pct_parametric`. A component can therefore be simultaneously the
  biggest recipient of the restored uncertainty AND the least worth working on --
  which is exactly what happens to thermal expansion here. Ranking on "which band
  grew most" would invert the priority order; ranking on `pct_parametric x spread`
  does not.

READS  outputs/scope_slr_fairunc_draws_<ssp>_spliced_L14.csv  (per-draw values)
WRITES outputs/rank_uncertainty_contributors_L14.csv

    source ~/climate-env/bin/activate
    python python/rank_uncertainty_contributors.py
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draws_io import draws_exists, read_draws  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG, FORCING = "L14", "spliced"
SSPS = ["ssp126", "ssp245", "ssp585"]
HORIZONS = [2100, 2150, 2300]
PARTS = ["glaciers", "gis", "ais", "te", "lws"]
OUT = os.path.join(REPO, "outputs", f"rank_uncertainty_contributors_{TAG}.csv")

def load(ssp):
    p = os.path.join(REPO, "outputs", f"scope_slr_fairunc_draws_{ssp}_{FORCING}_{TAG}.csv")
    if not draws_exists(p):
        print(f"  MISSING {os.path.basename(p)} — skipped"); return None
    return read_draws(p)

def spread(v):
    return float(np.percentile(v, 95) - np.percentile(v, 5))

rows = []
for ssp in SSPS:
    d = load(ssp)
    if d is None:
        continue
    print("=" * 100)
    print(f"{ssp} — what carries the band, fixed driver vs joint (FaIR uncertainty in)")
    print("=" * 100)
    for H in HORIZONS:
        sub = d[d.horizon == H]
        w = {a: {c: sub[(sub.arm == a) & (sub.component == c)].sort_values("draw").value_cm.values
                 for c in PARTS + ["total"]} for a in ("fixed", "joint")}
        print(f"\n  --- {H} " + "-" * 84)
        print(f"  {'component':10s} {'sprd fix':>9s} {'sprd joint':>11s} {'forcing add':>12s} "
              f"{'%of add':>8s} | {'width share':>12s} {'var share':>10s} "
              f"{'%forcing':>8s} {'ADDRESSABLE':>12s}")
        add = {c: spread(w['joint'][c]) - spread(w['fixed'][c]) for c in PARTS}
        add_tot = sum(v for v in add.values())
        for a in ("fixed", "joint"):
            vars_ = {c: float(np.var(w[a][c], ddof=1)) for c in PARTS}
            sv = sum(vars_.values())
            tot_var = float(np.var(w[a]["total"], ddof=1))
            for c in PARTS:
                sj = spread(w["joint"][c])
                rows.append(dict(ssp=ssp, horizon=H, arm=a, component=c,
                                 spread_cm=round(spread(w[a][c]), 4),
                                 share_of_width=round(spread(w[a][c]) / spread(w[a]["total"]), 4),
                                 var_share=round(vars_[c] / sv, 4),
                                 forcing_added_cm=round(add[c], 4) if a == "joint" else np.nan,
                                 pct_of_forcing_added=round(100 * add[c] / add_tot, 2) if a == "joint" and add_tot else np.nan,
                                 pct_forcing=round(100 * add[c] / sj, 2) if a == "joint" and sj else np.nan,
                                 addressable_cm=round(sj - add[c], 4) if a == "joint" else np.nan))
            rows.append(dict(ssp=ssp, horizon=H, arm=a, component="cov_residual",
                             spread_cm=np.nan, share_of_width=np.nan,
                             var_share=round((tot_var - sv) / tot_var, 4),
                             forcing_added_cm=np.nan, pct_of_forcing_added=np.nan))
        vj = {c: float(np.var(w['joint'][c], ddof=1)) for c in PARTS}
        svj = sum(vj.values())
        for c in sorted(PARTS, key=lambda x: -(spread(w['joint'][x]) - add[x])):
            sj = spread(w['joint'][c])
            print(f"  {c:10s} {spread(w['fixed'][c]):9.2f} {sj:11.2f} "
                  f"{add[c]:+12.2f} {100*add[c]/add_tot if add_tot else float('nan'):7.1f}% | "
                  f"{sj/spread(w['joint']['total']):11.1%} {vj[c]/svj:9.1%} "
                  f"{100*add[c]/sj if sj else float('nan'):8.0f}% {sj-add[c]:12.2f}")
        tv = float(np.var(w['joint']['total'], ddof=1))
        print(f"  (rows sorted by ADDRESSABLE cm = the part of the band model work could move)")
        print(f"  {'TOTAL':10s} {spread(w['fixed']['total']):9.2f} {spread(w['joint']['total']):11.2f} "
              f"{spread(w['joint']['total'])-spread(w['fixed']['total']):+12.2f} "
              f"{'':8s} |         --   cov {(tv-svj)/tv:+.1%}")
    print()

if rows:
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"wrote {OUT}")
