#!/usr/bin/env python3
"""
emit_gis_port_reference.py — ground truth for the Greenland A+B port.

Emits the spliced regional driver and the integrated fast/slow/total series at
the fitted A+B theta, so julia/validate_greenland_ab.jl can compare the Mimi
component against them at 1e-9. Same role that
python/emit_extc_port_reference.py plays for the glacier blocks.

Everything is re-exported from python/gis_offline_cell.py rather than
re-implemented -- if the two ever diverge the validation is worthless.

UNITS. The offline cell works in cm; BRICK components work in m. The
conversion happens HERE, once, and both are written out so a unit slip shows
up as a factor of 100 rather than silently.

  python3 python/emit_gis_port_reference.py [--forcing ssp245] [--y1 2300]
Writes:
  outputs/gis_port_reference.csv        year, driver, eq, fast, slow, sea_level
  outputs/gis_port_reference_theta.csv  the parameters, in BOTH unit systems
"""
import argparse
import importlib.util
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELL_PY = os.path.join(REPO, "python/gis_offline_cell.py")
OUT_REF = os.path.join(REPO, "outputs/gis_port_reference.csv")
OUT_THETA = os.path.join(REPO, "outputs/gis_port_reference_theta.csv")

CELL = "A+B"
CM_PER_M = 100.0
# Parameters carrying a length unit (cm in the cell, m in the component).
LENGTH_PARAMS = ("c1", "c0")


def load_cell():
    spec = importlib.util.spec_from_file_location("gis_offline_cell", CELL_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forcing", default="ssp245",
                    help="fair_mean_gmst_<tag>.csv used past the observations")
    ap.add_argument("--y1", type=int, default=2300)
    a = ap.parse_args()

    gc = load_cell()
    fits = pd.read_csv(os.path.join(REPO, "outputs/gis_offline_cell_fits.csv"))
    row = fits[fits.cell == CELL]
    assert len(row) == 1, f"cell {CELL} not found in the offline fits"
    theta = dict(kv.split("=") for kv in row.iloc[0].params.split("; "))
    theta = {k: float(v) for k, v in theta.items()}
    names = gc.cell_params(CELL)
    assert set(theta) == set(names), \
        f"parameter mismatch: fits have {sorted(theta)}, cell wants {sorted(names)}"

    drv = pd.read_csv(gc.DRIVER_CSV).set_index("year")[gc.DRIVER_ZONE]
    last_obs = int(drv.index.max())
    t_reg_obs = gc.extend(drv)
    gmst_hist = gc.extend(gc.load_gmst())
    gmst_scen = gc.extend(gc.load_gmst(a.forcing))
    driver = gc.splice_regional(t_reg_obs, gmst_hist, gmst_scen, last_obs)

    L, Lf = gc.run_cell(CELL, [theta[n] for n in names], driver, gmst_scen)
    p = dict(zip(names, [theta[n] for n in names]))
    eq = np.clip(p["c1"] * driver + p["c0"], 0.0, gc.V0_CM)

    keep = gc.YEARS <= a.y1
    ref = pd.DataFrame({
        "year": gc.YEARS[keep],
        "driver_K": driver[keep],
        "eq_cm": eq[keep], "fast_cm": Lf[keep],
        "slow_cm": (L - Lf)[keep], "sea_level_cm": L[keep],
        "eq_m": eq[keep] / CM_PER_M, "fast_m": Lf[keep] / CM_PER_M,
        "slow_m": (L - Lf)[keep] / CM_PER_M, "sea_level_m": L[keep] / CM_PER_M,
    })
    ref.to_csv(OUT_REF, index=False, float_format="%.17g")

    rows = [dict(name=k, value_cell=v,
                 value_component=(v / CM_PER_M if k in LENGTH_PARAMS else v),
                 unit_cell=("cm or cm/K" if k in LENGTH_PARAMS else "-"),
                 unit_component=("m or m/K" if k in LENGTH_PARAMS else "-"))
            for k, v in p.items()]
    rows.append(dict(name="v0", value_cell=gc.V0_CM,
                     value_component=gc.V0_CM / CM_PER_M,
                     unit_cell="cm", unit_component="m"))
    rows.append(dict(name="_forcing_tag", value_cell=np.nan,
                     value_component=np.nan, unit_cell=a.forcing,
                     unit_component=f"last_obs_year={last_obs}"))
    pd.DataFrame(rows).to_csv(OUT_THETA, index=False, float_format="%.17g")

    print(f"cell {CELL}, forcing {a.forcing}, years {ref.year.min()}-{ref.year.max()}")
    print(f"  driver: obs to {last_obs}, then amp={gc.AMP_MEAN} splice")
    print(f"  sea_level cm @2000 {np.interp(2000, ref.year, ref.sea_level_cm):.6f}  "
          f"@2100 {np.interp(2100, ref.year, ref.sea_level_cm):.6f}  "
          f"@{a.y1} {ref.sea_level_cm.iloc[-1]:.6f}")
    print(f"  fast+slow == total: max|diff| = "
          f"{np.abs(ref.fast_cm + ref.slow_cm - ref.sea_level_cm).max():.3e}")
    for f in (OUT_REF, OUT_THETA):
        print(f"wrote {os.path.relpath(f, REPO)}")


if __name__ == "__main__":
    main()
