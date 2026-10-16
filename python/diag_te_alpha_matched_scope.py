#!/usr/bin/env python3
"""diag_te_alpha_matched_scope.py -- the "alpha within 4 %" comparison on matched scopes (GMD queued item 4).

  python3 python/diag_te_alpha_matched_scope.py [--tag=L27] [--forcing=ssp245harm]

Writes outputs/diag_te_alpha_matched_scope_<TAG>.csv. Reads committed outputs and observations; runs no model.

THE SENTENCE. Sect. 2.2.4: "The posterior median of alpha is 0.167 (5-95% 0.148-0.186), within 4% of the value the
0-2000 m observations imply." Its receipt is diag_te_rate_attribution.py block C, which divides
    alpha_model = rate(TE, Ladrillo median) / rate(FaIR OHC)
by  alpha_obs   = rate(steric target)       / rate(observed 0-2000 m ocean heat).
FaIR's "ocean heat content" is its time-integrated top-of-atmosphere imbalance, i.e. Earth's TOTAL heat uptake
(fair.py:1596-1609; CHANGELOG 2026-10-05), so the two denominators have different scopes (handoff 10-01c sect. 1c
item 4). This script puts alpha_obs on three denominators, each an IGCC 2024 Earth-heat-inventory term:
    0-2000 m ocean    block C's denominator (scope MISMATCHED with FaIR's)
    full-depth ocean  adds IGCC's >2000 m layer (still excludes land, cryosphere, atmosphere)
    total Earth heat  the scope of FaIR's OHC: the MATCHED comparison
On the total-heat basis the ratio is also the ratio of "model per ocean heat" to "observed per ocean heat" if the model's
heat is split by IGCC's own ocean share, so the full-depth reading with that split is the same number.

The NUMERATOR is the steric target in both alphas (the series alpha is calibrated against), so its own depth scope
(a Frederikse + NOAA 0-2000 m splice; see diag_te_rate_attribution.py block E) cancels in the ratio.

ALPHA UNITS. Rates give alpha in cm per 1e22 J. The parameter (kg m^-3 degC^-1, the paper's 0.167) is that divided by
1e22 / (A C rho^2) cm per unit alpha with MimiBRICK v2.0.0's A, C, rho (CHANGELOG 2026-10-01: 0.6563).

WINDOWS. IGCC's non-ocean terms end in 2020, so every rate is an OLS slope over the SAME window for every series;
1993-2020 is primary (Sect. 4.1's E064 window), 2006-2020 and 1971-2020 are sensitivity rows.
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L27")
FORCING_TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--forcing=")), "ssp245harm")
TARGETS = os.path.join(REPO, "outputs", "recalib_targets_ext.csv")
POSTPRED = os.path.join(REPO, "outputs", f"postpred_{TAG}_components_timeseries.csv")
OLDBRICK = os.path.join(REPO, "outputs", "postpred_oldbrick_components_timeseries.csv")
POSTERIOR = os.path.join(REPO, "data", "MimiBRICK", f"parameters_subsample_brick_mengel_{TAG}.csv")
FAIR_OHC = os.path.join(REPO, f"data/observations/fair_mean_ohc_{FORCING_TAG}.csv")
IGCC_EEI = os.path.join(REPO, "data/observations/raw/igcc2024/ClimateIndicator-data-2cd2409/data/"
                              "earth_energy_imbalance/earth_energy_imbalance.csv")
OUT = os.path.join(REPO, "outputs", f"diag_te_alpha_matched_scope_{TAG}.csv")
ZJ_TO_1E22J = 0.1
A_OCEAN, C_SW, RHO_SW = 3.619e14, 3991.86795711963, 1027.0     # MimiBRICK.jl v2.0.0 get_model, lines 121-123
CM_PER_1E22J_PER_ALPHA = 1e22 / (A_OCEAN * C_SW * RHO_SW ** 2) * 100.0
PRIMARY = (1993, 2020)
WINDOWS = [PRIMARY, (2006, 2020), (1971, 2020)]
SCOPES = [("0-2000 m ocean", "ocean_0-2000m", "MISMATCHED (block C)"),
          ("full-depth ocean", "ocean_full-depth", "partial: no land/cryosphere/atmosphere"),
          ("total Earth heat", "total", "MATCHED to FaIR's OHC")]

assert abs(CM_PER_1E22J_PER_ALPHA - 0.6563) < 1e-4, CM_PER_1E22J_PER_ALPHA   # CHANGELOG 2026-10-01


def slope(year, val, w):
    """OLS slope over EVERY year of w; refuses a gap so that a ratio never mixes spans."""
    s = pd.Series(np.asarray(val, float), index=np.asarray(year, int)).loc[w[0]:w[1]]
    if len(s) != w[1] - w[0] + 1 or s.isna().any():
        raise SystemExit(f"gap in {w}: {len(s)} years, {int(s.isna().sum())} NaN; refuse to mix spans")
    return float(np.polyfit(s.index.values - w[0], s.values, 1)[0])


E = pd.read_csv(IGCC_EEI)
E["year"] = E.timebound_lower.astype(int)
E["ocean_0-2000m"] = E["ocean_0-700m"] + E["ocean_700-2000m"]
t = pd.read_csv(TARGETS)
a = pd.read_csv(POSTPRED)
b = pd.read_csv(OLDBRICK)
f = pd.read_csv(FAIR_OHC)
P = pd.read_csv(POSTERIOR)
q05, q50, q95 = np.quantile(P.thermal_alpha.values, [0.05, 0.5, 0.95])
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

print("=" * 108)
print(f"ALPHA ON MATCHED SCOPES -- Ladrillo {TAG}, FaIR mean OHC ({FORCING_TAG}), IGCC 2024 Earth heat inventory")
print("=" * 108)
print(f"posterior thermal_alpha ({len(P)} rows): median {q50:.4f}, 5-95% {q05:.4f}-{q95:.4f} kg m^-3 degC^-1")
print(f"1 unit of alpha = {CM_PER_1E22J_PER_ALPHA:.4f} cm per 1e22 J\n")
rows = []
for w in WINDOWS:
    r_tgt = slope(t.year, t.steric, w)
    r_mod = slope(a.year, a.te_p50, w)
    r_b20 = slope(b.year, b.te_p50, w)
    r_fair = slope(f.year, f.ohc_1e22J, w)
    a_mod = r_mod / r_fair
    a_b20 = r_b20 / r_fair
    print(f"[{w[0]}-{w[1]}] TE Ladrillo/target {r_mod / r_tgt:.3f}x, BRICK 2.0/target {r_b20 / r_tgt:.3f}x; "
          f"alpha model (rate ratio) {a_mod:.5f} cm/1e22 J = {a_mod / CM_PER_1E22J_PER_ALPHA:.4f}")
    for label, col, note in SCOPES:
        r_obs = slope(E.year, E[col] * ZJ_TO_1E22J, w)
        a_obs = r_tgt / r_obs
        rows.append(dict(window=f"{w[0]}-{w[1]}", primary=(w == PRIMARY), denominator=label, scope_note=note,
                         rate_target_cm_yr=r_tgt, rate_ladrillo_te_cm_yr=r_mod, rate_brick20_te_cm_yr=r_b20,
                         rate_fair_ohc_1e22J_yr=r_fair, rate_obs_heat_1e22J_yr=r_obs,
                         fair_over_obs_heat=r_fair / r_obs,
                         alpha_model_cm_per_1e22J=a_mod, alpha_obs_cm_per_1e22J=a_obs,
                         alpha_model_param=a_mod / CM_PER_1E22J_PER_ALPHA, alpha_obs_param=a_obs / CM_PER_1E22J_PER_ALPHA,
                         alpha_model_over_obs=a_mod / a_obs, alpha_brick20_over_obs=a_b20 / a_obs,
                         posterior_median_param_over_obs=q50 / (a_obs / CM_PER_1E22J_PER_ALPHA)))
        print(f"    alpha_obs per {label:17s} {a_obs:.5f} cm/1e22 J = {a_obs / CM_PER_1E22J_PER_ALPHA:.4f}  "
              f"Ladrillo/obs {a_mod / a_obs:.3f}  posterior-median/obs {q50 / (a_obs / CM_PER_1E22J_PER_ALPHA):.3f}  "
              f"BRICK 2.0/obs {a_b20 / a_obs:.3f}   [{note}]")
    print()

out = pd.DataFrame(rows)
out["posterior_alpha_median"], out["posterior_alpha_p05"], out["posterior_alpha_p95"] = q50, q05, q95
out["provenance"] = (f"diag_te_alpha_matched_scope.py @ {commit} | Ladrillo {TAG} TE p50 ({os.path.basename(POSTPRED)}) | "
                     f"BRICK 2.0 TE p50 ({os.path.basename(OLDBRICK)}, Zenodo 20592337 posterior) | steric target "
                     f"recalib_targets_ext.csv | FaIR 2.2.4 (calib 1.6.0) mean OHC {os.path.basename(FAIR_OHC)} | IGCC 2024 "
                     f"earth_energy_imbalance.csv (ZJ, x0.1 -> 1e22 J) | OLS slope over every year of the window | "
                     f"alpha param = cm per 1e22 J / {CM_PER_1E22J_PER_ALPHA:.5f}")
out.to_csv(OUT, index=False)
pm = out[out.primary]
print("PRIMARY (%s): Ladrillo alpha / obs-implied alpha = " % pm.window.iloc[0] +
      ", ".join(f"{r.alpha_model_over_obs:.3f} per {r.denominator}" for r in pm.itertuples()))
print(f"wrote {os.path.relpath(OUT, REPO)}")
