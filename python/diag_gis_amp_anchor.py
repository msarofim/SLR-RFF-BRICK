#!/usr/bin/env python3
"""
diag_gis_amp_anchor.py — at WHAT warming level does the observed gis_amp sit?

Settles sub-choice 2.2 of handoff 2026-08-13. The Greenland amplification law
adopted there is `amp(dT) = OBS_AMP_FULL * S(dT)` with the CMIP6 shape factor
`S` normalised to 1 at an anchor warming level. The summary table anchored at
the 1.25 K bin as a placeholder, but the observed 1.922 does not come from a
1.25 K world: it is `build_t_gis.amp_through_origin`, a THROUGH-ORIGIN fit
over 1901-2024,

    amp = sum(x*y) / sum(x^2)                                            (1)

with x the product's own global annual anomaly and y the south-Greenland zone
anomaly, both rel. 1850-1900. Rewrite (1) as a weighted mean of the pointwise
ratios y/x:

    amp = sum(x^2 * (y/x)) / sum(x^2)                                    (2)

so the weights are x^2. The warming level this estimator actually represents is
the same weighted mean applied to x itself:

    dT_eff = sum(x^3) / sum(x^2)                                         (3)

That is the level at which S must equal 1. Anchoring at 1.25 K instead would
shift the whole curve by S(1.25)/S(dT_eff).

Nothing here re-derives the mask or the series: it imports build_t_gis and uses
that module's own loaders, zones and windows, so the anchor is measured on
exactly the data the amplification was measured on. Gate: the recomputed amp
must reproduce outputs/gis_driver_constants.csv.

  python3 python/diag_gis_amp_anchor.py
Writes:
  outputs/gis_amp_anchor.csv    per product x zone x window: amp, dT_eff, n
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_t_gis as BTG

REPO = BTG.REPO
OUT_CSV = os.path.join(REPO, "outputs/gis_amp_anchor.csv")
CONSTANTS_CSV = BTG.OUT_CONSTANTS          # the committed amp table, for the gate

ZONE = BTG.HEADLINE_ZONE                   # "south"
WINDOW_NAME = BTG.AMP_WINDOW_HEADLINE      # "full"
AMP_TOL = 1e-9                             # gate: recomputed amp vs committed

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()


def amp_and_anchor(zone, glob, win):
    """(amp, dT_eff, n) for one product x zone x window — equations (1) and (3)."""
    x = glob.loc[win[0]:win[1]]
    y = zone.reindex(x.index)
    ok = x.notna() & y.notna()
    if ok.sum() < 20:
        return np.nan, np.nan, int(ok.sum())
    xv, yv = x[ok].to_numpy(float), y[ok].to_numpy(float)
    sxx = (xv ** 2).sum()
    return float((xv * yv).sum() / sxx), float((xv ** 3).sum() / sxx), int(ok.sum())


def main():
    series, globals_, _ = BTG.build()
    committed = pd.read_csv(CONSTANTS_CSV)

    rows = []
    for pname in BTG.PRODUCTS:
        for zname in list(BTG.ZONES) + list(BTG.DIAG_ZONES):
            for wname, win in BTG.AMP_WINDOWS.items():
                a, dte, n = amp_and_anchor(series[(pname, zname)], globals_[pname], win)
                # mean warming level over the same years, for contrast: dT_eff is
                # x^2-weighted and therefore always the larger of the two.
                x = globals_[pname].loc[win[0]:win[1]]
                y = series[(pname, zname)].reindex(x.index)
                ok = x.notna() & y.notna()
                rows.append(dict(product=pname, zone=zname, window=wname,
                                 year0=win[0], year1=win[1], n_years=n,
                                 amp=a, dt_eff=dte,
                                 dt_mean=float(x[ok].mean()),
                                 dt_last=float(x[ok].iloc[-1])))
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    # ---- gate: the recomputed amp must reproduce the committed constants -------
    bad = []
    for _, r in df.iterrows():
        c = committed[(committed["product"] == r["product"])
                      & (committed.zone == r.zone)]
        if c.empty:
            continue
        want = float(c[f"amp_{r.window}"].iloc[0])
        if not (np.isnan(want) and np.isnan(r.amp)) and abs(want - r.amp) > AMP_TOL:
            bad.append(f"{r['product']}/{r.zone}/{r.window}: {r.amp:.12f} vs {want:.12f}")
    if bad:
        sys.exit("GATE FAIL — recomputed amp does not match "
                 f"{os.path.basename(CONSTANTS_CSV)}:\n  " + "\n  ".join(bad))
    print(f"GATE PASS — amp reproduces {os.path.basename(CONSTANTS_CSV)} "
          f"to {AMP_TOL:g} for all {len(df)} product x zone x window cells\n")

    # ---- the headline: zone/window actually in use -----------------------------
    h = df[(df.zone == ZONE) & (df.window == WINDOW_NAME)]
    print(f"zone {ZONE}, window {WINDOW_NAME} "
          f"{tuple(BTG.AMP_WINDOWS[WINDOW_NAME])}  (commit {COMMIT})")
    print(f"  {'product':14s} {'n':>4s} {'amp':>8s} {'dT_eff':>8s} {'dT_mean':>8s} {'dT_last':>8s}")
    for _, r in h.iterrows():
        print(f"  {r['product']:14s} {r.n_years:4d} {r.amp:8.3f} {r.dt_eff:8.3f} "
              f"{r.dt_mean:8.3f} {r.dt_last:8.3f}")
    print(f"  {'MEAN':14s} {'':4s} {h.amp.mean():8.3f} {h.dt_eff.mean():8.3f} "
          f"{h.dt_mean.mean():8.3f} {h.dt_last.mean():8.3f}")
    print(f"\nANCHOR dT_eff = {h.dt_eff.mean():.4f} K  "
          f"(cross-product mean, the same average the amp prior uses)")
    print(f"  spread over products: {h.dt_eff.min():.4f} - {h.dt_eff.max():.4f} K")
    print(f"\nwrote {OUT_CSV}")


if __name__ == "__main__":
    main()
