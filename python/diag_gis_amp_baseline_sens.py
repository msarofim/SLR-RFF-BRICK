"""DOES REBASELINING TO A MODERN PERIOD SHRINK THE BETWEEN-PRODUCT AMP DISAGREEMENT?

THE QUESTION (Marcus 2026-08-23). The three products' south-Greenland amplifications
span 1.513x on a 1850-1900 baseline, which is larger than the 1.286x obs-vs-CMIP6
offset the amp relaxation removes. The products' Greenland coverage is worst in the
early record, and with an 1850-1900 base EVERY year's anomaly inherits that early
baseline -- so a modern baseline is a candidate for removing a large part of the
disagreement without changing any underlying data.

WHAT IS AND IS NOT BEING TESTED
  Rebaselining does NOT change the temperature fields. It changes what "anomaly"
  means in a THROUGH-ORIGIN secant, which is not baseline-invariant: shifting x and y
  by constants moves Sum(x*y)/Sum(x*x). So the amp is a different (still legitimate)
  quantity under each base, and the test is whether the PRODUCTS AGREE BETTER on it --
  not whether the number goes up or down.

  ⚠ A modern baseline puts the zero near the middle of the record, so the x^2 weight
  moves to BOTH ends -- early (negative) and recent (positive). That can help by
  removing the early baseline offset, or hurt by up-weighting the sparse early years
  through a now-large |x|. Which one wins is the measurement.

WRITES outputs/diag_gis_amp_baseline_sens.csv
  python3 python/diag_gis_amp_baseline_sens.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import build_t_gis as BTG  # noqa: E402

OBS = os.path.join(REPO, "data/observations")
ALLPROD = os.path.join(OBS, "t_gis_zones_allproducts.csv")
OUT = os.path.join(REPO, "outputs/diag_gis_amp_baseline_sens.csv")

PRODUCTS = ["HadCRUT5", "BerkeleyEarth", "GISTEMP"]
ZONES = ["south", "all", "central", "north"]
## The ladder. 1850-1900 is what ships; 1971-2000 is Marcus's proposal; the other two
## bracket it so the answer is a TREND in base recency, not one alternative.
BASELINES = [(1850, 1900), (1901, 1930), (1961, 1990), (1971, 2000), (1995, 2014)]
FIT_WIN = (1901, 2024)


def secant(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 20:
        return np.nan
    xv, yv = x[ok], y[ok]
    return float((xv * yv).sum() / (xv ** 2).sum())


def main():
    zp = pd.read_csv(ALLPROD).set_index("year")
    glob = {}
    for p in PRODUCTS:
        v, yr, mo, lat, lon = BTG.PRODUCTS[p]()
        glob[p] = BTG.global_annual(v, yr, mo, lat, lon)      # UNBASED — rebased below

    rows = []
    for base in BASELINES:
        for z in ZONES:
            amps = {}
            for p in PRODUCTS:
                g = glob[p]
                zs = zp[f"{p}_{z}"]
                yrs = sorted(set(g.index) & set(zs.index))
                gg = g.reindex(yrs); zz = zs.reindex(yrs)
                ## Rebase BOTH to the same window, per the standing rule that every
                ## curve in a comparison shares one baseline.
                gb = gg - gg.loc[base[0]:base[1]].mean()
                zb = zz - zz.loc[base[0]:base[1]].mean()
                m = (np.array(yrs) >= FIT_WIN[0]) & (np.array(yrs) <= FIT_WIN[1])
                amps[p] = secant(gb.to_numpy(float)[m], zb.to_numpy(float)[m])
            v = np.array([amps[p] for p in PRODUCTS])
            rows.append(dict(baseline=f"{base[0]}-{base[1]}", zone=z,
                             **{p: amps[p] for p in PRODUCTS},
                             mean=float(np.mean(v)),
                             spread_ratio=float(np.max(v) / np.min(v)),
                             spread_abs=float(np.max(v) - np.min(v)),
                             cv=float(np.std(v) / np.mean(v))))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    print("diag_gis_amp_baseline_sens — through-origin secant on "
          f"{FIT_WIN[0]}-{FIT_WIN[1]}, per baseline\n")
    for z in ZONES:
        s = out[out.zone == z]
        star = "   <-- the driver zone" if z == "south" else ""
        print(f"=== zone {z}{star} ===")
        print(f"  {'baseline':12}" + "".join(f"{p:>15}" for p in PRODUCTS)
              + f"{'mean':>9}{'spread':>9}{'CV':>8}")
        for _, r in s.iterrows():
            print(f"  {r.baseline:12}" + "".join(f"{r[p]:15.3f}" for p in PRODUCTS)
                  + f"{r['mean']:9.3f}{r.spread_ratio:9.3f}{r.cv:8.3f}")
        b0 = s[s.baseline == "1850-1900"].iloc[0]
        bb = s.loc[s.spread_ratio.idxmin()]
        print(f"  shipped base spread {b0.spread_ratio:.3f}x -> best "
              f"({bb.baseline}) {bb.spread_ratio:.3f}x   "
              f"({b0.spread_ratio / bb.spread_ratio:.2f}x tighter)\n")

    s = out[out.zone == "south"]
    b0 = s[s.baseline == "1850-1900"].iloc[0]
    b7 = s[s.baseline == "1971-2000"].iloc[0]
    print("VERDICT for the driver zone (south)")
    print(f"  1850-1900 (ships): spread {b0.spread_ratio:.3f}x, mean amp {b0['mean']:.3f}")
    print(f"  1971-2000 (asked): spread {b7.spread_ratio:.3f}x, mean amp {b7['mean']:.3f}")
    verdict = ("HELPS" if b7.spread_ratio < b0.spread_ratio * 0.95 else
               "does NOT help" if b7.spread_ratio < b0.spread_ratio * 1.05 else "HURTS")
    print(f"  => rebaselining to 1971-2000 {verdict} "
          f"({b0.spread_ratio / b7.spread_ratio:.2f}x)")
    ## ---- THE CMIP6 SIDE, ON THE SAME FRAME -------------------------------
    ## The 1.4942 comparison value is itself computed on 1850-1900. Re-reading the
    ## obs-vs-CMIP6 offset under a new baseline is only meaningful if BOTH sides
    ## move -- otherwise the "improvement" is a frame mismatch. The CMIP6 zone
    ## series are stored in absolute K, so they rebase exactly like the products.
    import glob
    print("\n=== THE OFFSET, WITH BOTH SIDES ON THE SAME FRAME ===\n")
    cm = []
    for f in sorted(glob.glob(os.path.join(REPO, "data/cmip6_gis/*.csv"))):
        d = pd.read_csv(f)
        d = d[d.scenario.isin(("historical", "ssp245"))]
        if d.empty or d.year.max() < 2024:
            continue
        cm.append(d.drop_duplicates("year").set_index("year")[
            ["tas_global", "tas_gis_south"]])
    print(f"  {len(cm)} CMIP6 models with historical+ssp245 through 2024\n")
    print(f"  {'baseline':12}{'obs mean':>10}{'CMIP6 med':>11}{'OFFSET':>9}"
          f"{'obs spread':>12}")
    orows = []
    for base in BASELINES:
        ca = []
        for d in cm:
            g = d.tas_global - d.tas_global.loc[base[0]:base[1]].mean()
            z = d.tas_gis_south - d.tas_gis_south.loc[base[0]:base[1]].mean()
            m = (d.index >= FIT_WIN[0]) & (d.index <= FIT_WIN[1])
            ca.append(secant(g.to_numpy(float)[m], z.to_numpy(float)[m]))
        cmed = float(np.nanmedian(ca))
        r = out[(out.zone == "south") & (out.baseline == f"{base[0]}-{base[1]}")].iloc[0]
        orows.append(dict(baseline=r.baseline, obs_mean=r["mean"], cmip6_median=cmed,
                          offset=r["mean"] / cmed, obs_spread=r.spread_ratio))
        print(f"  {r.baseline:12}{r['mean']:10.3f}{cmed:11.3f}"
              f"{r['mean'] / cmed:9.3f}{r.spread_ratio:12.3f}")
    pd.DataFrame(orows).to_csv(OUT.replace(".csv", "_offset.csv"), index=False)
    o0 = orows[0]; ob = min(orows, key=lambda r: abs(np.log(r["offset"])))
    print(f"\n  shipped frame offset {o0['offset']:.3f}x; closest to 1 is "
          f"{ob['baseline']} at {ob['offset']:.3f}x")
    print(f"  => the obs-vs-CMIP6 offset is {'MOSTLY A FRAME ARTEFACT' if abs(np.log(ob['offset'])) < 0.5 * abs(np.log(o0['offset'])) else 'NOT explained by the baseline'} — "
          f"it {'shrinks' if abs(np.log(ob['offset'])) < abs(np.log(o0['offset'])) else 'does not shrink'} when both sides share a modern frame.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
