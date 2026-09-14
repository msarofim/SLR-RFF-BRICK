#!/usr/bin/env python3
"""dump_shared_climate_for_blocks.py — the SHARED FACTS climate as CSV, for the per-block
Ladrillo-vs-emulandice comparison (julia/diag_gsic_blocks_vs_emulandice.jl).

WHY DUMP THE NetCDF RATHER THAN RE-SPLICE THE CUBE. FACTS's emulandice ran on
facts/experiments/global.shared.<scen>.n200/input/shared_<scen>_{gsat,ohc}.nc, built by
facts/build_shared_climate_nc.py (200 evenly-spaced configs of the 841, spliced at 2014,
centred 1850-1900). Reading those files back guarantees sample k of emulandice and sample k of
Ladrillo saw IDENTICAL forcing, rather than a re-derivation that agrees to a tolerance.

Writes outputs/diag_emu_blocks/shared_<scen>_{gmst,ohc}.csv: year (1850-2300), s0..s199.
GMST in K rel 1850-1900; OHC converted J -> 1e22 J (the cube's unit; Ladrillo's `ohc` input).

    python3 python/dump_shared_climate_for_blocks.py --scen=ssp245 | --all
"""
import os
import sys
import numpy as np
import pandas as pd
import netCDF4 as nc4

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = os.path.expanduser("~/Documents/2026/CodeProjects/facts/experiments")
OUT_DIR = os.path.join(REPO, "outputs", "diag_emu_blocks")
SCENS = ["ssp126", "ssp245", "ssp585", "vvVL", "vvLN", "vvL", "vvML", "vvM", "vvHL", "vvH"]
Y0, Y1 = 1850, 2300               # Ladrillo's run window; the nc pads 2300->2500 with a HOLD
J_TO_1E22 = 1e-22
BASE = (1850, 1900)


def dump(scen):
    os.makedirs(OUT_DIR, exist_ok=True)
    for var, fn, scale in (("surface_temperature", "gsat", 1.0),
                           ("ocean_heat_content", "ohc", J_TO_1E22)):
        p = os.path.join(FACTS, f"global.shared.{scen}.n200", "input", f"shared_{scen}_{fn}.nc")
        if not os.path.exists(p):
            raise SystemExit(f"missing {p}")
        d = nc4.Dataset(p)
        yrs = d.variables["years"][:].astype(int)
        x = np.asarray(d.variables[var][:, :, 0], dtype=float) * scale   # samples x years
        sel = (yrs >= Y0) & (yrs <= Y1)
        df = pd.DataFrame(x[:, sel].T, columns=[f"s{k}" for k in range(x.shape[0])])
        df.insert(0, "year", yrs[sel])
        # [FRAME] the files are centred on 1850-1900; assert it rather than trust the attribute
        b = df[(df.year >= BASE[0]) & (df.year <= BASE[1])].iloc[:, 1:].mean()
        assert b.abs().max() < 1e-3, f"{scen} {fn}: 1850-1900 mean not ~0 (max |{b.abs().max():.3g}|)"
        out = os.path.join(OUT_DIR, f"shared_{scen}_{'gmst' if fn == 'gsat' else 'ohc'}.csv")
        df.to_csv(out, index=False, float_format="%.6f")
        print(f"  wrote {os.path.relpath(out, REPO)}  n={x.shape[0]}  "
              f"{fn}@2100 median {np.median(df.loc[df.year == 2100].iloc[:, 1:].values):.3f}")


if __name__ == "__main__":
    keys = SCENS if "--all" in sys.argv else [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--scen=")]
    keys = keys or ["ssp245"]
    for k in keys:
        dump(k)
