"""diag_te_driver_timing.py -- is the thermal-expansion hindcast misfit a SCALE problem or a TIMING problem?

Thermal expansion is linear in its heat driver (dTE = alpha * dOHC / (A C rho^2)), so any CONSTANT rescaling of FaIR's
"ocean heat" (e.g. the ~0.82 that removes heat below 2000 m and heat on land, in ice and in the air;
diag_fair_ohc_vs_earth_heat.py) is absorbed by alpha and cannot change the fit. Only the driver's SHAPE in time can.

[A] Era shape: each series' OLS rate per era divided by its own 1993-2024 rate (FaIR mean OHC, observed 0-2000 m OHC =
    Zanna 2019 + IGCC 2024 splice, and the TE target's steric series).
[B] Offline weighted least-squares fit of TE = s0 + c * driver to the steric target over 1900-2024 (weights 1/sigma from
    the target band), then model/target rate per era, for FaIR, 0.82 x FaIR and the observed OHC driver.
This is a diagnostic, NOT Ladrillo's likelihood (no AR(1), no discrepancy term): its recent-era ratio is 1.05, where
Ladrillo's bare-module hindcast is 1.22. Writes outputs/diag_te_driver_timing.csv.
"""
import os, subprocess
import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ERAS = [(1900, 1949), (1950, 1992), (1993, 2024)]
FIT = (1900, 2024)
SCALE = 0.82                       # 1 / (1.107 x 1.097), diag_fair_ohc_vs_earth_heat.csv 1993-2020
OUT = os.path.join(REPO, "outputs", "diag_te_driver_timing.csv")

T = pd.read_csv(os.path.join(REPO, "outputs/recalib_targets_ext.csv")).set_index("year")
tgt = T.steric
sig = ((T.steric_hi - T.steric_lo) / (2 * 1.645)).clip(lower=0.02)
F = pd.read_csv(os.path.join(REPO, "data/observations/fair_mean_ohc_ssp245harm.csv")).set_index("year").ohc_1e22J
Z = pd.read_csv(os.path.join(REPO, "data/observations/ohc_spliced_zanna_igcc.csv"), comment="#").set_index("year").ohc_1e22J
DRIVERS = {"fair_total_heat": F, "fair_x0.82": SCALE * F, "observed_0_2000m_zanna_igcc": Z}


def rate(s, w):
    y = np.arange(w[0], w[1] + 1)
    v = s.reindex(y).values
    if not np.isfinite(v).all():
        raise SystemExit(f"{s.name}: gaps in {w}")
    return float(np.polyfit(y, v, 1)[0])


def fit(D, w):
    y = np.arange(w[0], w[1] + 1)
    d, t, s = D.reindex(y).values, tgt.reindex(y).values, sig.reindex(y).values
    if not (np.isfinite(d).all() and np.isfinite(t).all()):
        raise SystemExit(f"gaps in the fit window {w}")
    A = np.c_[np.ones_like(d), d] / s[:, None]
    b = np.linalg.lstsq(A, t / s, rcond=None)[0]
    return b[0] + b[1] * D


rows = []
for name, D in [("target_steric", tgt), ("fair_total_heat", F), ("observed_0_2000m_zanna_igcc", Z)]:
    r = [rate(D, w) for w in ERAS]
    rows.append(dict(test="A_era_shape", series=name, **{f"{a}-{b}": x / r[-1] for (a, b), x in zip(ERAS, r)}))
for name, D in DRIVERS.items():
    p = fit(D, FIT)
    rows.append(dict(test="B_wls_fit_model_over_target", series=name,
                     **{f"{a}-{b}": rate(p, (a, b)) / rate(tgt, (a, b)) for a, b in ERAS}))
out = pd.DataFrame(rows)
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
out["provenance"] = (f"diag_te_driver_timing.py | commit {commit} | FaIR 2.2.4 (calib 1.6.0) mean, fair_mean_ohc_ssp245harm | "
                     f"Zanna 2019 + IGCC 2024 0-2000 m (ohc_spliced_zanna_igcc.csv; Zanna anchored to FaIR at 1871) | "
                     f"target recalib_targets_ext.csv steric | WLS fit {FIT[0]}-{FIT[1]}, scale {SCALE} | OLS era rates | no RNG")
out.to_csv(OUT, index=False, float_format="%.4f")
print(out.drop(columns="provenance").to_string(index=False))
print("wrote", OUT)
