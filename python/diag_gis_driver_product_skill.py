"""WHICH TEMPERATURE PRODUCT'S GREENLAND HISTORY BEST EXPLAINS THE OBSERVED MELT?

THE QUESTION (Marcus 2026-08-23). scope_gis_amp_relax_tau.py showed the amp
relaxation's preferred tau tracks the observational product, and Berkeley Earth alone
sits on CMIP6's own amplification -- so "switch to Berkeley Earth" is tempting. That
is a claim about which product is RIGHT, and it should be settled against Greenland's
own mass-loss record rather than against agreement with models.

WHAT IS ACTUALLY AT STAKE, and it is bigger than the amp law
  build_t_gis.py line ~356 sets `hp = "HadCRUT5"`: the committed driver
  t_gis_zones.csv IS HadCRUT5, for every zone. So the product choice is NOT a
  projection-side knob like the amp law -- it is the CALIBRATION DRIVER. Changing it
  moves what c1/c0/f/the rates were fitted against, and is a RECALIBRATION, not a
  prior propagation. That is the opposite of the amp law's situation and is the main
  reason this test has to be decisive before anything moves.

THE TEST, built so the answer cannot be a calibration artifact
  For each product, drive the SAME module with THAT product's south-Greenland series
  and re-fit the rate scale to the observed 1900-2025 total. Matching the total is
  therefore free for every product BY CONSTRUCTION -- the level carries no
  information and is not scored. What IS scored is the SHAPE the product cannot
  tune away:
    * sub-window rates (the record's own decadal structure)
    * acceleration over the satellite era
    * years inside the observational band, and the worst absolute miss
  A product whose Greenland warming history has the right TIME EVOLUTION reproduces
  those without being fitted to them.

⚠ THE POSTERIOR WAS FITTED ON HadCRUT5, which gives HadCRUT5 a home-field advantage
  in anything the rate scale cannot absorb. The refit removes the level advantage; it
  does not remove that c1/c0/f saw HadCRUT5's shape. Read a HadCRUT5 win as weaker
  evidence than a HadCRUT5 loss.

WRITES outputs/diag_gis_driver_product_skill.csv
  python3 python/diag_gis_driver_product_skill.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import YEARS  # noqa: E402

OBS = os.path.join(REPO, "data/observations")
ALLPROD = os.path.join(OBS, "t_gis_zones_allproducts.csv")
OUT = os.path.join(REPO, "outputs/diag_gis_driver_product_skill.csv")

ZONE = "south"
PRODUCTS = ["HadCRUT5", "BerkeleyEarth", "GISTEMP"]
CALIB_PRODUCT = "HadCRUT5"                 # what t_gis_zones.csv actually is
FIT_WIN = (1900, 2025)                     # the window the rate scale is fitted on
RATE_WINDOWS = [(1900, 1950), (1950, 1990), (1993, 2010), (2010, 2024), (1995, 2024)]
ACCEL_WIN = (1993, 2024)


def rate(series, yrs, w):
    i0, i1 = int(np.where(yrs == w[0])[0][0]), int(np.where(yrs == w[1])[0][0])
    return 10.0 * (series[i1] - series[i0]) / (w[1] - w[0])      # mm/yr from cm


def accel(series, yrs, w):
    m = (yrs >= w[0]) & (yrs <= w[1])
    return float(2.0 * 10.0 * np.polyfit(yrs[m] - yrs[m].mean(), series[m], 2)[0])


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    nd = len(post)

    zp = pd.read_csv(ALLPROD).set_index("year")
    tgt = pd.read_csv(A.TARGETS).set_index("year")
    obs = tgt["gis"]; obs_lo, obs_hi = tgt["gis_lo"], tgt["gis_hi"]
    want = float(obs.loc[FIT_WIN[1]] - obs.loc[FIT_WIN[0]])

    idx = {int(y): i for i, y in enumerate(YEARS)}
    yrs = np.asarray(YEARS)

    print(f"diag_gis_driver_product_skill — {ZONE} zone, {nd} draws")
    print(f"  the committed driver t_gis_zones.csv IS {CALIB_PRODUCT} "
          f"(build_t_gis.py: hp = \"{CALIB_PRODUCT}\")")
    print(f"  rate scale re-fitted per product to the observed {FIT_WIN[0]}-{FIT_WIN[1]} "
          f"total ({want:.3f} cm), so LEVEL is free and unscored\n")

    rows = []
    for p in PRODUCTS:
        z = zp[f"{p}_{ZONE}"].reindex(yrs)
        drv = np.tile(np.nan_to_num(z.to_numpy(float), nan=0.0), (nd, 1))
        lo, hi = np.full(nd, 1e-4), np.full(nd, 1e3)
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            L = basin2_series(drv, post, 1.0, mid)
            b = 100.0 * (L[:, idx[FIT_WIN[1]]] - L[:, idx[FIT_WIN[0]]]) < want
            lo, hi = np.where(b, mid, lo), np.where(b, hi, mid)
        s = np.sqrt(lo * hi)
        cur = np.median(rebase_cm(basin2_series(drv, post, 1.0, s)), axis=0)
        cur = cur - cur[idx[FIT_WIN[0]]] + float(obs.loc[FIT_WIN[0]])

        r = dict(product=p, s_median=float(np.median(s)))
        for w in RATE_WINDOWS:
            got, tru = rate(cur, yrs, w), rate(obs.reindex(yrs).to_numpy(float), yrs, w)
            r[f"rate_{w[0]}_{w[1]}"] = got / tru
        a_got = accel(cur, yrs, ACCEL_WIN)
        a_tru = accel(obs.reindex(yrs).to_numpy(float), yrs, ACCEL_WIN)
        r["accel"] = a_got / a_tru
        m = (yrs >= FIT_WIN[0]) & (yrs <= 2025)
        inb = ((cur[m] >= obs_lo.reindex(yrs).to_numpy(float)[m]) &
               (cur[m] <= obs_hi.reindex(yrs).to_numpy(float)[m]))
        miss = np.maximum(obs_lo.reindex(yrs).to_numpy(float)[m] - cur[m],
                          cur[m] - obs_hi.reindex(yrs).to_numpy(float)[m])
        r["frac_in_band"] = float(inb.mean())
        r["worst_miss_cm"] = float(np.max(np.maximum(miss, 0.0)))
        ## The headline: scale-free shape error over the rate windows + acceleration,
        ## which is what the level refit CANNOT absorb.
        r["shape_err"] = float(np.mean([abs(np.log(r[f"rate_{w[0]}_{w[1]}"]))
                                        for w in RATE_WINDOWS] + [abs(np.log(r["accel"]))]))
        rows.append(r)

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    print(f"  {'product':16}" + "".join(f"{f'{w[0]}-{w[1]}':>12}" for w in RATE_WINDOWS)
          + f"{'accel':>9}")
    for _, r in out.iterrows():
        print(f"  {r['product']:16}"
              + "".join(f"{r[f'rate_{w[0]}_{w[1]}']:12.3f}" for w in RATE_WINDOWS)
              + f"{r['accel']:9.3f}")
    print(f"\n  (ratios to observed; 1.000 is perfect)\n")
    print(f"  {'product':16}{'in band':>10}{'worst miss':>13}{'SHAPE ERR':>12}"
          f"{'rate scale':>12}")
    for _, r in out.iterrows():
        print(f"  {r['product']:16}{r['frac_in_band']:10.3f}"
              f"{r['worst_miss_cm']:13.3f}{r['shape_err']:12.4f}{r['s_median']:12.4f}")

    best = out.loc[out.shape_err.idxmin()]
    cal = out[out['product'] == CALIB_PRODUCT].iloc[0]
    print(f"\n  BEST SHAPE: {best['product']} ({best.shape_err:.4f})")
    print(f"  calibration product {CALIB_PRODUCT}: {cal.shape_err:.4f} "
          f"({cal.shape_err / best.shape_err:.3f}x the best)")
    if best['product'] == CALIB_PRODUCT:
        print(f"  ⚠ the winner IS the product the posterior was fitted on — home-field "
              f"advantage\n    applies, so read this as WEAK evidence for "
              f"{CALIB_PRODUCT}, not as a result.")
    else:
        print(f"  the winner is NOT the calibration product, and it wins DESPITE the "
              f"posterior\n    having been fitted on {CALIB_PRODUCT}'s shape — that "
              f"makes it the stronger direction.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
