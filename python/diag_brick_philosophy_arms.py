#!/usr/bin/env python3
"""HOW MUCH DO LADRILLO'S TWO DEPARTURES FROM BRICK'S OBS-ONLY PHILOSOPHY BUY? (Marcus 2026-09-13)

Three projection-only arms on the shipped L24 posterior, each undoing one non-observational
element, against the shipped L24 projection (with the above-threshold discharge channel, CMIP6
Greenland amp shape, sampled AIS amp).
All arms are the FIXED FaIR-mean-forcing ssp projections of project_ssps_components_ladrillo.jl
(2000 draws, medians rel 1995-2014), so the numbers are parameter-spread medians on one climate.

  1. NO above-threshold discharge channel .... outputs/ssps_components_2300_L24.csv (the --no-tap
     arm the postprocess already writes). BRICK has no such channel.
  2. CONSTANT Greenland amplification ......... LADRILLO_GIS_SHAPE=gis_amp_shape_const: S(dT)=1, i.e.
     the OBSERVED through-origin amp level (1.92) at every warming, dropping the CMIP6 shape that
     lets the amp fall with warming (1.50 -> 1.28 over 0.75-2.75 K). Tables written by this
     script's companion step (see CHANGELOG 09-13j): outputs/gis_amp_shape_const{,_meta}.csv
     (S=1 on the default grid, same anchor).
  3. AIS amplification FIXED at 1.196 ......... stock DAIS's hard-coded GMST->T_ant slope (the
     inverted paleo regression BRICK 2.0 keeps), replacing Ladrillo's sampled N(1.09, 0.180)
     CMIP6 prior (L24 posterior median 1.074). Posterior copy with the column overwritten:
     data/MimiBRICK/parameters_subsample_brick_mengel_L24aisamp1p196.csv (untracked, 10 MB;
     regenerate: read the L24 subsample, set ais_gmst_amp=1.196, write under that name), run
     as --tag=L24aisamp1p196.
     ⚠ PROJECTION-SIDE OVERRIDE, NOT A REFIT: ais_gmst_amp is prior-dominated but not
     likelihood-inert, so the other AIS parameters were drawn jointly with the sampled amp. The
     refit-based cross-check is the L21->L23 pair (memory amp_prior_mu_was_dropped): +0.14 of
     amp moved AIS@2300 ssp245 by ~53 cm on a 386 cm/unit slope; 0.122 here would give ~47 cm
     against the measured value (see the CSV). Same order; the override is if anything conservative.
     Fixing the value also removes the amp's spread; only MEDIANS are reported.

WRITES outputs/diag_brick_philosophy_arms.csv (stamped)
  python3 python/diag_brick_philosophy_arms.py
"""
import os
import subprocess
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
BASE = "outputs/ssps_components_2300_L24_tap4p69K_V5p64m_tau800_n2_ws.csv"
ARMS = {
    "no_threshold_channel": ("gis", "outputs/ssps_components_2300_L24.csv"),
    "constant_greenland_amp": ("gis", "outputs/ssps_components_2300_L24_tap4p69K_V5p64m_tau800_n2_ws_shapeconst.csv"),
    "ais_amp_fixed_1p196": ("ais", "outputs/ssps_components_2300_L24aisamp1p196_tap4p69K_V5p64m_tau800_n2_ws.csv"),
}
YEARS = (2100, 2150, 2300)
OUT = "outputs/diag_brick_philosophy_arms.csv"


def med(d, comp, ssp, year):
    return float(d[(d.component == comp) & (d.ssp == ssp) & (d.year == year)].med.iloc[0])


def main():
    base = pd.read_csv(BASE)
    commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    prov = (f"diag_brick_philosophy_arms.py | seed n/a (reads project_ssps_components outputs; their seed is "
            f"recorded in the posterior subsample) | base {BASE} | fixed FaIR-mean forcing, 2000 draws, medians "
            f"rel 1995-2014, cm | commit {commit}")
    rows = []
    for arm, (comp, path) in ARMS.items():
        d = pd.read_csv(path)
        for ssp in sorted(base.ssp.unique()):
            for y in YEARS:
                rows.append(dict(arm=arm, component=comp, ssp=ssp, year=y,
                                 shipped_cm=med(base, comp, ssp, y), arm_cm=med(d, comp, ssp, y),
                                 delta_component_cm=med(d, comp, ssp, y) - med(base, comp, ssp, y),
                                 shipped_total_cm=med(base, "total", ssp, y),
                                 delta_total_cm=med(d, "total", ssp, y) - med(base, "total", ssp, y),
                                 provenance=prov))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    for arm in ARMS:
        print(f"== {arm}")
        for ssp in sorted(base.ssp.unique()):
            s = out[(out.arm == arm) & (out.ssp == ssp)]
            print("  " + ssp + "  " + " | ".join(f"{int(r.year)}: {r.delta_component_cm:+6.1f} (total {r.shipped_total_cm:5.0f})" for _, r in s.iterrows()))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
