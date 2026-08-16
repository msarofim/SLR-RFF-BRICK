#!/usr/bin/env python3
"""
scope_ladrillo_vs_brick20_scorecard.py — Ladrillo 1.0 vs BRICK 2.0 on the
hindcast, module by module, in ONE set of metrics.

Marcus's acceptance criteria (2026-08-14) are per module: (1) formulation at
least as credible as BRICK 2.0's, (2) hindcast match at least as good, (3)
projection spread at least as good (FACTS/MAGICC match, or more physical), and
(4) the same for the joint calibration. (1) is a judgement, and (3) already has
its own output (outputs/ladrillo_model_comparison_L10_spread.csv). THIS script does
(2) and the hindcast half of (4), which had never been computed in matched
metrics: `posterior_predictive_ladrillo.jl` writes bias + coverage for L10, but
`posterior_predictive_oldbrick.jl` writes only a band timeseries.

BOTH ARMS ARE ALREADY ON THE SAME FOOTING, verified rather than assumed:
  * same re-reference window, 1995-2005 (FIT_REF in the Ladrillo script, B0/B1
    in the oldbrick one), and the targets in recalib_targets_ext.csv are
    themselves zeroed on 1995-2005 to -0.0000 cm on every component, so the
    model bands and the obs share one baseline;
  * same FaIR mean GMST + OHC forcing;
  * both bands are PARAMETRIC (no AR(1) noise added), so `coverage` here is
    comparable to L10's `coverage_param`, NOT to its `coverage_pred`.

WHAT "BRICK 2.0" MEANS HERE: stock MimiBRICK v2.0.0 run with its own published
posterior (`parameters_subsample_brick.csv`), i.e. the model as it ships and as
its authors calibrated it. It was NOT recalibrated on our extended targets, so a
bias against those targets is partly a target-vintage difference and not purely
a model defect -- stated, because it cuts in Ladrillo's favour.

  source ~/climate-env/bin/activate
  python3 python/scope_ladrillo_vs_brick20_scorecard.py
Writes outputs/scope_ladrillo_vs_brick20_scorecard.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs/scope_ladrillo_vs_brick20_scorecard.csv")

L10_TS = os.path.join(REPO, "outputs/postpred_L10_components_timeseries.csv")
B20_TS = os.path.join(REPO, "outputs/postpred_oldbrick_components_timeseries.csv")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")

REF = (1995, 2005)                 # the shared re-reference window
# component -> (L10 stem, BRICK 2.0 stem, target column)
COMPONENTS = [("AIS", "ais", "ais", "ais"),
              ("glaciers", "glaciers", "gsic", "gsic"),
              ("Greenland", "gis", "gis", "gis"),
              ("thermal exp.", "te", "te", "steric"),
              ("TOTAL", "total", "total", None)]
# Windows. The full record hides WHERE each arm misses, and the answer turned out
# to matter: every Ladrillo module except thermal expansion beats BRICK 2.0 in
# every window, while TE is worse in both pre-satellite windows and better in the
# satellite era — so "TE is the one regression" is a statement about the
# pre-1993 record, not a uniform one. Splitting at 1950 and 1993 separates the
# sparse-obs era, the pre-satellite era, and the altimetry era.
WINDOWS = [("full", None), ("1920-1949", (1920, 1949)),
           ("1950-1992", (1950, 1992)), ("1993-2026", (1993, 2026))]


def load():
    a = pd.read_csv(L10_TS).set_index("year")
    b = pd.read_csv(B20_TS).set_index("year")
    t = pd.read_csv(TARGETS).set_index("year")
    base = t.loc[REF[0]:REF[1], ["ais", "gsic", "gis", "steric"]].mean()
    if base.abs().max() > 1e-3:
        raise SystemExit("targets are not zeroed on the shared re-reference "
                         f"window {REF}: {base.to_dict()} — the two arms would "
                         "not be on one baseline")
    return a, b, t


def score(model_p50, lo, hi, obs, window):
    m = obs.notna() & model_p50.notna()
    if window is not None:
        m &= (obs.index >= window[0]) & (obs.index <= window[1])
    if m.sum() == 0:
        return None
    r = (model_p50[m] - obs[m])
    inband = ((obs[m] >= lo[m]) & (obs[m] <= hi[m])).mean()
    return dict(n=int(m.sum()), mean_bias=float(r.mean()),
                rmse=float(np.sqrt((r ** 2).mean())),
                max_abs=float(r.abs().max()), coverage90=float(inband))


def main():
    a, b, t = load()
    years = a.index.intersection(b.index)
    print("Ladrillo 1.0 vs BRICK 2.0 — hindcast scorecard")
    print(f"  overlap {years.min()}-{years.max()}, re-reference {REF[0]}-{REF[1]}, "
          f"parametric 90% bands both arms")
    print("  BRICK 2.0 = stock MimiBRICK v2.0.0 on its OWN published posterior, "
          "NOT recalibrated\n  on our extended targets — part of its bias is "
          "target vintage, which favours Ladrillo.\n")

    rows = []
    for wname, win in WINDOWS:
        print(f"  === window: {wname} ===")
        print(f"  {'component':13s} {'arm':10s} {'n':>4s} {'mean bias':>10s} "
              f"{'RMSE':>8s} {'max|err|':>9s} {'90% cov':>8s}")
        for label, la, ba, tcol in COMPONENTS:
            obs_l = (a[f"{la}_obs"] if f"{la}_obs" in a
                     else t[tcol].reindex(a.index))
            obs = obs_l.reindex(years)
            for arm, df, stem, p5 in (("Ladrillo", a, la, "p05"),
                                      ("BRICK 2.0", b, ba, "p5")):
                s = score(df[f"{stem}_p50"].reindex(years),
                          df[f"{stem}_{p5}"].reindex(years),
                          df[f"{stem}_p95"].reindex(years), obs, win)
                if s is None:
                    continue
                rows.append(dict(window=wname, component=label, arm=arm, **s))
                print(f"  {label:13s} {arm:10s} {s['n']:4d} "
                      f"{s['mean_bias']:+10.3f} {s['rmse']:8.3f} "
                      f"{s['max_abs']:9.3f} {s['coverage90']:8.1%}")
        print()

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    print("  VERDICT per component — RMSE ratio Ladrillo / BRICK 2.0 "
          "(<1 means Ladrillo is better)")
    for wname, _ in WINDOWS:
        w = df[df.window == wname]
        for label, *_ in COMPONENTS:
            l = w[(w.component == label) & (w.arm == "Ladrillo")]
            s = w[(w.component == label) & (w.arm == "BRICK 2.0")]
            if l.empty or s.empty:
                continue
            ratio = l.rmse.iloc[0] / s.rmse.iloc[0]
            print(f"    {wname:10s} {label:13s} {ratio:5.2f}x  "
                  f"{'BETTER' if ratio < 1 else 'WORSE'}")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
