#!/usr/bin/env python3
"""
build_greenland_equilibrium_ladder.py — the Greenland equilibrium committed-loss
ladder from Bochow et al. 2023, into a tracked CSV.

This is the Greenland analogue of the GlacierMIP3 committed-loss rungs: how much
of the ice sheet is lost at equilibrium under a sustained warming level. It is
the piece of physics no observation can supply — nothing has been observed to
equilibrate — and it is what option C (a nonlinear V_eq) has to be anchored to.

SOURCE
  Bochow, N. et al. (2023) "Overshooting the critical threshold for the
  Greenland ice sheet", Nature 622:528, doi 10.1038/s41586-023-06503-9.
  Model output, CC-BY-4.0, Zenodo doi 10.5281/zenodo.8155423:
    yelmo_rembo.zip   27 MB  — Yelmo-REMBO output, used here
    pism_debm.zip    1.1 GB  — PISM-dEBM-simple output
    Code.zip        5.4 MB  — the authors' figure scripts

  The ladder is taken from `gris-rembo-ramp06b.nc`, the runs with no overshoot
  (f_max == f_conv): warm to a convergence temperature, hold, integrate 150 kyr.
  Equilibrium loss is the 90-100 kyr mean, following the authors' own figure
  code (Code/Fig_2_3.py).

CONVENTIONS, taken from the authors' figure code rather than assumed
  * `f_conv` is GREENLAND REGIONAL SUMMER warming, not global. The conversion
    used in their own axes (Code/Fig_2_3.py line 111) is
        GMT = f_conv / 1.19 + 0.5
    which reproduces the paper's "~1.4 C regional summer warming (1.7 C GMT)".
    Note the +0.5 offset: their zero-forcing reference is about +0.5 C GMT
    above pre-industrial, not pre-industrial itself.
  * Volume is converted to sea-level equivalent as
        loss = (V_init - V) / V_init * 7.42 m
    again following the authors' code. Yelmo's own V_sle_init is 8.31 m.

NOTE 2026-08-10: the output file now also carries the PISM-dEBM ladder, built
from the 16 no-overshoot runs (Tmax == convT, 0.0-7.5 K in 0.5 K steps) inside
pism_debm.zip, whose `ice_volume` is normalised by each run's own initial volume
and scaled by 7.42 m on the same basis. Those 16 files are tracked under
data/observations/raw/bochow2023/pism_eq/; the 1.1 GB source archive is not.
Max equilibrium drift over the averaging window is 0.16 m for PISM against
0.000 m for Yelmo. Re-running this script rebuilds the Yelmo rows only, so do
not overwrite the merged file without re-adding PISM.

  python3 python/build_greenland_equilibrium_ladder.py [--src DIR]
Writes data/observations/greenland_equilibrium_bochow2023.csv
"""
import argparse
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data/observations/greenland_equilibrium_bochow2023.csv")

RAMP_FILE = "gris-rembo-ramp06b.nc"
EQ_WINDOW = (90000, 100000)        # yr; the authors' equilibrium averaging window
SLE_SCALE_M = 7.42                 # authors' volume -> sea-level-equivalent scale
GMT_SLOPE, GMT_OFFSET = 1.19, 0.5  # GMT = f_conv / GMT_SLOPE + GMT_OFFSET


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.expanduser(
        "~/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/observations/raw/bochow2023"),
        help="directory holding the unpacked Zenodo output")
    args = ap.parse_args()

    import netCDF4
    path = os.path.join(args.src, RAMP_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found — unpack yelmo_rembo.zip from Zenodo 10.5281/zenodo.8155423 "
            f"into {args.src}")
    d = netCDF4.Dataset(path)

    f_conv = np.array(d["f_conv"][:]).ravel()
    f_max = np.array(d["f_max"][:]).ravel()
    v_init = float(np.array(d["V_sle_init"][:]).ravel()[0])
    time = np.array(d["time"][:])
    vol = np.array(d["v"][:])

    # no-overshoot runs only: the ladder is loss as a function of the SUSTAINED level
    keep = np.isclose(f_conv, f_max)
    i0 = int(np.where(time[:, 0] == EQ_WINDOW[0])[0][0])
    i1 = int(np.where(time[:, 0] == EQ_WINDOW[1])[0][0])

    rows = []
    for j in np.where(keep)[0]:
        window = vol[i0:i1, j]
        if not np.isfinite(window).any():
            continue
        loss_frac = (v_init - np.nanmean(window)) / v_init
        # drift over the averaging window, as an equilibrium check
        drift = float(np.nanmean(window[-10:]) - np.nanmean(window[:10])) / v_init * SLE_SCALE_M
        rows.append(dict(model="Yelmo-REMBO",
                         dT_summer_K=float(f_conv[j]),
                         gmt_K=float(f_conv[j]) / GMT_SLOPE + GMT_OFFSET,
                         loss_m_sle=loss_frac * SLE_SCALE_M,
                         loss_frac_of_volume=loss_frac,
                         drift_over_window_m=drift))
    out = pd.DataFrame(rows).sort_values("gmt_K").reset_index(drop=True)
    out.to_csv(OUT, index=False)

    print(f"Greenland equilibrium ladder | Bochow et al. 2023, {RAMP_FILE}")
    print(f"  V_sle_init {v_init:.2f} m, equilibrium window {EQ_WINDOW[0]}-{EQ_WINDOW[1]} yr, "
          f"{len(out)} no-overshoot runs\n")
    print(f"  {'dT summer':>10s} {'GMT':>7s} {'loss m SLE':>11s} {'% of volume':>12s} "
          f"{'drift m':>9s}")
    for _, r in out.iterrows():
        print(f"  {r.dT_summer_K:10.2f} {r.gmt_K:7.2f} {r.loss_m_sle:11.2f} "
              f"{100 * r.loss_frac_of_volume:11.1f}% {r.drift_over_window_m:9.3f}")

    # where does it turn over?
    steps = out.loss_m_sle.diff() / out.gmt_K.diff()
    k = int(np.nanargmax(steps.to_numpy()))
    print(f"\n  steepest rise between GMT {out.gmt_K[k - 1]:.2f} and {out.gmt_K[k]:.2f} "
          f"({steps.iloc[k]:.1f} m SLE per K) — the threshold")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
