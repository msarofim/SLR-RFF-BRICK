"""THE OBS-vs-CMIP6 AMPLIFICATION OFFSET FOR THE GLACIER BLOCKS, ACROSS BASELINE FRAMES.

THE QUESTION (Marcus 2026-08-23). The Greenland module carries a projection-side
amplification law anchored to an OBSERVED level that sits 1.286x above CMIP6's own --
and diag_gis_amp_baseline_sens.py showed that offset is largely an artefact of the
1850-1900 frame, reversing sign under four of five alternatives. The glacier module has
no such law, and its blocks' between-product spread is LARGER than Greenland's
(SLOWP 1.863x, R19 1.472x, FAST 1.366x vs south 1.513x). This asks whether the two
modules have the SAME problem, so one treatment can serve both rather than a
Greenland-only knob.

  IF THE GLACIER OFFSET BEHAVES LIKE GREENLAND'S -- large and positive on 1850-1900,
      shrinking or reversing on a modern frame -- then the frame is the common cause
      and neither module needs an amplification correction, only a consistent frame.
  IF THE GLACIER OFFSET IS SMALL AT EVERY FRAME, then the Greenland offset is a
      Greenland fact and the two modules are NOT symmetric.
  IF IT IS LARGE AT EVERY FRAME, the frame story fails for glaciers and the amp
      question reopens for both.

BOTH SIDES ARE REBASED TO THE SAME WINDOW, always. The CMIP6 block series are absolute
K (reduce_cmip6_tas_glac.py) and the observed ones are anomalies rel 1850-1900;
subtracting each one's own window mean puts them on a common frame either way.

⚠ THE OBSERVED SIDE HERE IS HadCRUT5 ONLY -- it is what t_glac_blocks.csv is, and it
is the calibration driver. The between-PRODUCT spread is a separate axis, quoted from
diag_amp_dataset_comparison.csv at 1850-1900 and not rescanned here.

WRITES outputs/diag_glac_amp_cmip6_offset.csv
  python3 python/diag_glac_amp_cmip6_offset.py
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

OBS_BLOCKS = os.path.join(REPO, "data/observations/t_glac_blocks.csv")
OBS_GLOB = os.path.join(REPO, "data/observations/t_glac_hadcrut5.csv")
CMIP_DIR = os.path.join(REPO, "data/cmip6_glac")
OUT = os.path.join(REPO, "outputs/diag_glac_amp_cmip6_offset.csv")

BLOCKS = ["R19", "SLOWP", "FAST"]
BASELINES = [(1850, 1900), (1901, 1930), (1961, 1990), (1971, 2000), (1995, 2014)]
FIT_WIN = (1901, 2024)
GIS_OFFSETS = {"1850-1900": 1.274, "1901-1930": 0.729, "1961-1990": 0.692,
               "1971-2000": 0.445, "1995-2014": 0.903}     # diag_gis_amp_baseline_sens


def secant(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 20:
        return np.nan
    return float((x[ok] * y[ok]).sum() / (x[ok] ** 2).sum())


def main():
    ob = pd.read_csv(OBS_BLOCKS).set_index("year")
    og = pd.read_csv(OBS_GLOB).set_index("year")["gmst_hadcrut5_C"]

    files = sorted(glob.glob(os.path.join(CMIP_DIR, "tas_series_glac_*.csv")))
    cm = []
    for f in files:
        d = pd.read_csv(f)
        d = d[d.scenario.isin(("historical", "ssp245"))].drop_duplicates("year")
        d = d.set_index("year")
        if d.index.max() < 2024 or d.index.min() > 1850:
            continue
        cm.append(d)
    print(f"diag_glac_amp_cmip6_offset — {len(cm)} CMIP6 models, "
          f"secant on {FIT_WIN[0]}-{FIT_WIN[1]}\n")
    if not cm:
        raise SystemExit("no CMIP6 glacier reductions — run "
                         "python/reduce_cmip6_tas_glac.py first")

    rows = []
    for base in BASELINES:
        bl = f"{base[0]}-{base[1]}"
        for b in BLOCKS:
            yrs = np.array(sorted(set(og.index) & set(ob.index)))
            m = (yrs >= FIT_WIN[0]) & (yrs <= FIT_WIN[1])
            g = og.reindex(yrs); z = ob[b].reindex(yrs)
            g = g - g.loc[base[0]:base[1]].mean()
            z = z - z.loc[base[0]:base[1]].mean()
            a_obs = secant(g.to_numpy(float)[m], z.to_numpy(float)[m])

            ca = []
            for d in cm:
                gg = d.tas_global - d.tas_global.loc[base[0]:base[1]].mean()
                zz = d[f"tas_{b}"] - d[f"tas_{b}"].loc[base[0]:base[1]].mean()
                mm = (d.index >= FIT_WIN[0]) & (d.index <= FIT_WIN[1])
                ca.append(secant(gg.to_numpy(float)[mm], zz.to_numpy(float)[mm]))
            a_cm = float(np.nanmedian(ca))
            rows.append(dict(baseline=bl, block=b, obs_amp=a_obs, cmip6_median=a_cm,
                             cmip6_p05=float(np.nanpercentile(ca, 5)),
                             cmip6_p95=float(np.nanpercentile(ca, 95)),
                             offset=a_obs / a_cm, n_models=int(np.isfinite(ca).sum())))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    for b in BLOCKS:
        s = out[out.block == b]
        print(f"=== {b} ===")
        print(f"  {'baseline':12}{'obs (HadCRUT5)':>16}{'CMIP6 med':>11}"
              f"{'CMIP6 p05-p95':>18}{'OFFSET':>9}")
        for _, r in s.iterrows():
            print(f"  {r.baseline:12}{r.obs_amp:16.3f}{r.cmip6_median:11.3f}"
                  f"{f'{r.cmip6_p05:.2f}-{r.cmip6_p95:.2f}':>18}{r.offset:9.3f}")
        cv = s.cmip6_median.std() / s.cmip6_median.mean()
        ov = s.obs_amp.std() / s.obs_amp.mean()
        print(f"  frame sensitivity (CV across baselines): CMIP6 {cv:.3f}  "
              f"obs {ov:.3f}   ({ov/cv:.1f}x)\n")

    print("=== SIDE BY SIDE WITH GREENLAND — the offset at each frame ===\n")
    print(f"  {'baseline':12}" + "".join(f"{b:>10}" for b in BLOCKS)
          + f"{'GIS south':>12}")
    for bl in [f"{a}-{b}" for a, b in BASELINES]:
        s = out[out.baseline == bl].set_index("block")
        print(f"  {bl:12}" + "".join(f"{s.loc[b].offset:10.3f}" for b in BLOCKS)
              + f"{GIS_OFFSETS.get(bl, float('nan')):12.3f}")

    sh = out[out.baseline == "1850-1900"]
    md = out[out.baseline == "1995-2014"]
    print(f"\n  glacier offsets on the SHIPPED frame: "
          f"{', '.join(f'{r.block} {r.offset:.2f}' for _, r in sh.iterrows())}")
    print(f"  glacier offsets on 1995-2014:         "
          f"{', '.join(f'{r.block} {r.offset:.2f}' for _, r in md.iterrows())}")
    same = np.mean([abs(np.log(r.offset)) for _, r in sh.iterrows()]) > \
        np.mean([abs(np.log(r.offset)) for _, r in md.iterrows()])
    print(f"\n  => the glacier blocks {'SHARE Greenland pattern: the 1850-1900 frame maximises the offset' if same else 'DO NOT share Greenland pattern — the frame is not the common cause'}")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
