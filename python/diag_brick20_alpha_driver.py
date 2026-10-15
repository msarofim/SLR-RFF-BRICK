"""Does the ocean-heat driver explain the BRICK 2.0 thermal_alpha gap between posteriors?

Asked 2026-10-15 (handoff_2026-10-15_tony_tw2_brick_posterior.md §2, test 2), and Marcus 10-15: should the
BRICK 2.0 arm run coupled to SNEASY instead of on FaIR?

MimiBRICK v2.0.0 constrains thermal expansion (TE) by two OLS trends, 1971-2009 (0.8 mm/yr) and 1993-2009
(1.1 mm/yr), each with sigma 0.3 mm/yr (calibration_helper_functions.jl:424-425, :552). TE is linear in ocean heat:
TE = alpha * dOHC * 1e22 / (A C rho^2) (thermal_expansion_component.jl). For each driver this script gives the
OHC trends over those windows, the alpha that best fits the two trends alone, and the TE trends that a given alpha
predicts on that driver.

Drivers:
- the SNEASY MAP trajectory that v2.0.0's standalone-BRICK calibration reads (get_model, MimiBRICK.jl:45-46), read
  straight from the MimiBRICK.jl git tag;
- the 2022 SNEASY MAP trajectories it replaced;
- FaIR mean ssp245harm (our BRICK 2.0 hindcast driver);
- Tony's coupled SNEASY-BRICK ssp245 ensemble from 2026-04-14 (pre-PR#93), as a spread of DOECLIM paths.

It also gives the rank correlation between BRICK and SNEASY parameters in our May-22 joint posterior, which a
FaIR-driven BRICK arm does not keep.

Run from SLR-RFF-BRICK/ with ~/climate-env/bin/python.
"""
import io
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

CP = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects")
MIMIBRICK = CP / "MimiBRICK.jl"
MIMIBRICK_TAG = "v2.0.0"
SNEASY_FILES = {
    "SNEASY MAP ssp245 2026-06-07 (v2.0.0 standalone calibration driver)":
        "data/model_data/sneasy_oceanheat_ssp245_1850_2300_07-06-2026.csv",
    "SNEASY MAP RCP45 2022": "data/model_data/sneasy_oceanheat_RCP45_1850_2300.csv",
    "SNEASY MAP RCP85 2022": "data/model_data/sneasy_oceanheat_RCP85_1850_2300.csv",
}
FAIR_OHC = CP / "Ladrillo/data/forcing/fair_mean_ohc_ssp245harm.csv"
FAIR_LABEL = "FaIR 2.2.4 mean ssp245harm (BRICK 2.0 arm driver)"
TONY_ENS = CP / ("FaIRtoFrEDI/external/wong_slr_repro/vehicle_emissions_slr_14Apr2026/data/"
                 "projections_ocean_heat_ssp245_sneasybrick.csv")
TONY_ENS_START = 1850
JOINT_POST = CP / "SLR-RFF-BRICK/parameters_subsample_sneasybrick.csv"   # May-22, sha256 2218bdd5...

A, C, RHO = 3.619e14, 3991.86795711963, 1027.0       # MimiBRICK.jl v2.0.0 get_model, lines 121-123
TE_WINDOWS = [(1971, 2009, 0.8), (1993, 2009, 1.1)]   # (start, end, observed TE trend mm/yr)
TE_SIGMA = 0.3                                         # mm/yr, both windows
MM_PER_ALPHA_1E22J = 1e22 / (A * C * RHO**2) * 1000.0  # mm of TE per unit alpha per 1e22 J
ALPHA_PRIOR = (0.05, 0.3)                              # create_log_posterior_brick.jl:133
ALPHA_TESTS = {"Zenodo standalone median (10-08h)": 0.054, "May-22 joint median": None}
EARLY_WINDOW = (1900, 1971)
LONG_WINDOW = (1900, 2018)
OUT = Path("outputs/diag_brick20_alpha_driver.csv")
OUT_CORR = Path("outputs/diag_brick20_alpha_driver_joint_corr.csv")


def git_sha(repo):
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


def ols_slope(yrs, v, a, b):
    m = (yrs >= a) & (yrs <= b)
    return np.polyfit(yrs[m], v[m], 1)[0]


def fit_alpha(yrs, ohc):
    """Alpha that maximises the two-trend likelihood alone (equal sigma -> least squares)."""
    k = np.array([ols_slope(yrs, ohc, a, b) * MM_PER_ALPHA_1E22J for a, b, _ in TE_WINDOWS])
    obs = np.array([o for *_, o in TE_WINDOWS])
    return float(k @ obs / (k @ k)), k


def delta(yrs, ohc, a, b):
    return float(np.interp(b, yrs, ohc) - np.interp(a, yrs, ohc))


def main():
    joint = pd.read_csv(JOINT_POST)
    ALPHA_TESTS["May-22 joint median"] = float(joint.thermal_alpha.median())

    drivers = {}
    for label, path in SNEASY_FILES.items():
        txt = subprocess.run(["git", "-C", str(MIMIBRICK), "show", f"{MIMIBRICK_TAG}:{path}"],
                             capture_output=True, text=True, check=True).stdout
        d = pd.read_csv(io.StringIO(txt))
        drivers[label] = (d.iloc[:, 0].to_numpy(float), d.iloc[:, 1].to_numpy(float), f"{MIMIBRICK_TAG}:{path}")
    f = pd.read_csv(FAIR_OHC)
    drivers[FAIR_LABEL] = (f.year.to_numpy(float), f.ohc_1e22J.to_numpy(float), str(FAIR_OHC.relative_to(CP)))
    ens = pd.read_csv(TONY_ENS)
    ens_yrs = np.arange(TONY_ENS_START, TONY_ENS_START + len(ens), dtype=float)
    ens_label = f"Tony coupled SNEASY-BRICK ssp245 2026-04-14, median path of {ens.shape[1]} draws"
    drivers[ens_label] = (ens_yrs, ens.median(axis=1).to_numpy(float), str(TONY_ENS.relative_to(CP)))

    rows = []
    for label, (yrs, ohc, src) in drivers.items():
        alpha_fit, k = fit_alpha(yrs, ohc)
        row = dict(driver=label, source=src,
                   ohc_slope_1971_2009=k[0] / MM_PER_ALPHA_1E22J, ohc_slope_1993_2009=k[1] / MM_PER_ALPHA_1E22J,
                   dohc_1900_1971=delta(yrs, ohc, *EARLY_WINDOW), dohc_1900_2018=delta(yrs, ohc, *LONG_WINDOW),
                   alpha_fit_te_trends_only=alpha_fit)
        for name, a in ALPHA_TESTS.items():
            for (s, e, _), kk in zip(TE_WINDOWS, k):
                row[f"te_trend_{s}_{e}_mm_yr | alpha={a:.3f} ({name})"] = a * kk
        rows.append(row)
    out = pd.DataFrame(rows)
    per_draw = np.array([fit_alpha(ens_yrs, ens[c].to_numpy(float))[0] for c in ens.columns])

    prov = (f"diag_brick20_alpha_driver.py @ SLR-RFF-BRICK {git_sha(CP / 'SLR-RFF-BRICK')}; MimiBRICK.jl tag "
            f"{MIMIBRICK_TAG}; TE trend windows {TE_WINDOWS} mm/yr sigma {TE_SIGMA}; OHC units 1e22 J; alpha units "
            f"kg m-3 degC-1, prior U{ALPHA_PRIOR}; Zenodo alpha from SLR CHANGELOG 2026-10-08h (file not on disk); "
            f"no RNG")
    out["provenance"] = prov
    OUT.parent.mkdir(exist_ok=True)
    out.to_csv(OUT, index=False)

    clim = ["climate_sensitivity", "heat_diffusivity", "rf_scale_aerosol", "ocean_heat_0", "temperature_0"]
    slr = ["thermal_alpha", "glaciers_beta0", "greenland_a", "anto_alpha", "antarctic_temp_threshold"]
    corr = joint[slr + clim].corr(method="spearman").loc[slr, clim]
    corr["provenance"] = f"Spearman, {JOINT_POST.name} ({len(joint)} draws, May-22 joint SNEASY-BRICK posterior)"
    corr.to_csv(OUT_CORR)

    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 60)
    show = ["driver", "ohc_slope_1971_2009", "ohc_slope_1993_2009", "dohc_1900_1971", "dohc_1900_2018",
            "alpha_fit_te_trends_only"]
    print(out[show].round(3).to_string(index=False))
    print(f"\nObserved TE trends: {[(s, e, o) for s, e, o in TE_WINDOWS]} mm/yr, sigma {TE_SIGMA}")
    for name, a in ALPHA_TESTS.items():
        print(f"\nalpha = {a:.3f} ({name}): predicted TE trends, mm/yr")
        for label, (yrs, ohc, _) in drivers.items():
            _, k = fit_alpha(yrs, ohc)
            z = [(a * kk - o) / TE_SIGMA for kk, (*_, o) in zip(k, TE_WINDOWS)]
            print(f"  {label[:62]:62s} {a * k[0]:.2f} ({z[0]:+.1f} sd)  {a * k[1]:.2f} ({z[1]:+.1f} sd)")
    q = np.percentile(per_draw, [5, 50, 95])
    print(f"\nTony 04-14 ensemble, per-draw alpha fit to the trends alone: median {q[1]:.3f} [5-95 {q[0]:.3f}, {q[2]:.3f}]")
    jq = joint.thermal_alpha.quantile([0.05, 0.5, 0.95]).to_numpy()
    print(f"May-22 joint posterior thermal_alpha: median {jq[1]:.3f} [5-95 {jq[0]:.3f}, {jq[2]:.3f}]; prior U{ALPHA_PRIOR}")
    print("\nSpearman correlation, May-22 joint posterior (BRICK rows x SNEASY columns):")
    print(corr.drop(columns="provenance").round(2).to_string())
    print(f"\nWrote {OUT} and {OUT_CORR}")


if __name__ == "__main__":
    main()
