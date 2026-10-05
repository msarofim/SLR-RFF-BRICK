"""diag_fair_ohc_vs_earth_heat.py -- what FaIR's "ocean heat content" is, measured against IGCC's heat inventory.

FaIR 2.2.4's `ocean_heat_content_change` is the time integral of the TOP-OF-ATMOSPHERE energy imbalance over the whole
Earth (fair/fair.py:1596-1609: cumsum(toa_imbalance) * timestep * 4*pi*R^2 * seconds_per_year). It is therefore the
Earth's TOTAL heat accumulation (ocean + land + cryosphere + atmosphere), not ocean heat (Frank Errickson, 2026-10).

This script splits FaIR's rate excess over the 0-2000 m ocean (the thermal-expansion target's depth) into three factors,
on a COMMON span (IGCC's non-ocean terms end in 2020 while its ocean layers run to 2024; masking each series separately
is the 2026-10-01 TE-rate-window bug):
    FaIR / IGCC 0-2000 m  =  [IGCC full-depth / 0-2000 m]  x  [IGCC total / full-depth]  x  [FaIR / IGCC total]
                              (heat below 2000 m)               (heat on land, in ice, air)     (what is left)
Rates are OLS slopes of annual values, 1e22 J/yr. IGCC: ClimateIndicator 2024 earth_energy_imbalance.csv (ZJ).
Writes outputs/diag_fair_ohc_vs_earth_heat.csv.
"""
import os, subprocess, sys
import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FORCING_TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--forcing=")), "ssp245harm")
FAIR_OHC = os.path.join(REPO, f"data/observations/fair_mean_ohc_{FORCING_TAG}.csv")
IGCC_EEI = os.path.join(REPO, "data/observations/raw/igcc2024/ClimateIndicator-data-2cd2409/data/"
                              "earth_energy_imbalance/earth_energy_imbalance.csv")
ZJ_TO_1E22J = 0.1
WINDOWS = [(1993, None), (1971, None), (2006, 2020)]     # None = the last year every IGCC term has
OUT = os.path.join(REPO, "outputs", "diag_fair_ohc_vs_earth_heat.csv")

E = pd.read_csv(IGCC_EEI)
E["year"] = E.timebound_lower.astype(int)
E = E.set_index("year")
E["ocean_0-2000m"] = E["ocean_0-700m"] + E["ocean_700-2000m"]
F = pd.read_csv(FAIR_OHC).set_index("year").ohc_1e22J
LAST = int(E.index[E.total.notna()].max())
assert np.allclose((E["ocean_full-depth"] + E.land + E.cryosphere + E.atmosphere - E.total).dropna(), 0, atol=1e-6), \
    "IGCC components do not sum to its total"


def slope(s, w):
    s = s.loc[w[0]:w[1]]
    if s.isna().any() or len(s) != w[1] - w[0] + 1:
        raise SystemExit(f"{s.name}: gaps in {w}; refuse to mix spans")
    return float(np.polyfit(s.index.values - w[0], s.values, 1)[0])


commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
rows = []
for w0, w1 in WINDOWS:
    w = (w0, w1 or LAST)
    r = {c: slope(E[c] * ZJ_TO_1E22J, w) for c in
         ["ocean_0-2000m", "ocean_full-depth", "land", "cryosphere", "atmosphere", "total"]}
    rf = slope(F, w)
    row = dict(window=f"{w[0]}-{w[1]}", fair=rf, **{f"igcc_{k}": v for k, v in r.items()},
               nonocean_share=(r["land"] + r["cryosphere"] + r["atmosphere"]) / r["total"],
               fair_over_0_2000=rf / r["ocean_0-2000m"],
               f_deep=r["ocean_full-depth"] / r["ocean_0-2000m"],
               f_nonocean=r["total"] / r["ocean_full-depth"],
               f_residual=rf / r["total"])
    rows.append(row)
    print(f"{row['window']}: FaIR/0-2000 m {row['fair_over_0_2000']:.3f} = deep {row['f_deep']:.3f} x non-ocean "
          f"{row['f_nonocean']:.3f} x residual {row['f_residual']:.3f}   (non-ocean share of IGCC total "
          f"{row['nonocean_share']:.3f})")
out = pd.DataFrame(rows)
out["provenance"] = (f"diag_fair_ohc_vs_earth_heat.py | commit {commit} | FaIR 2.2.4 (calib 1.6.0) mean of 841 configs, "
                     f"{os.path.basename(FAIR_OHC)} | IGCC 2024 earth_energy_imbalance.csv (von Schuckmann), ZJ x 0.1 | "
                     f"OLS slopes, 1e22 J/yr, common span per window | no RNG")
out.to_csv(OUT, index=False)
print("wrote", OUT)
