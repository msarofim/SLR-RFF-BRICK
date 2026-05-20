"""
run_fair_rff.py

Run FaIR 2.2.4 on a single RFF-SP draw using the infilled emissions from
Sarofim et al. 2024 Nat Comm (Zenodo 7759089). Pulls historical (1750-2014)
emissions from RCMIP-ssp245, then OVERWRITES 2015-2300 with the draw's
infilled emissions for all 53 species.

Then either:
  - runs all 841 FaIR posterior configs and saves the median trajectory, OR
  - runs a single representative config

For the smoke test we'll run all 841 and save the per-config 2100 GMST so we
can pick the median config (matching what we did for SSP2-4.5 in FaIRtoFrEDI).

Usage:
    source ~/climate-env/bin/activate
    python python/run_fair_rff.py --draw 1 --output-dir outputs/

Inputs:
    --draw N    1-based RFF-SP draw index (1..10000)

Outputs:
    outputs/rff_draw{N}_temp_all841.csv      year x 841 GMST trajectories
    outputs/rff_draw{N}_temp_median.csv      year, GMST_median, GMST_2.5, GMST_97.5
"""

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pooch
from fair import FAIR
from fair.interface import fill, initialise
from fair.io import read_properties

PROJ_DIR  = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
RFF_DIR   = PROJ_DIR / "data" / "RFF-SP-emissions" / "csv"
HIST_FILE = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/volcanic_solar_hist.csv")

# ─── Mapping from infilled-CSV "variable" names to FaIR species names ─────────
INF_TO_FAIR = {
    "BC": "BC",
    "CCl4": "CCl4",
    "CFC11": "CFC-11",
    "CFC12": "CFC-12",
    "CFC113": "CFC-113",
    "CFC114": "CFC-114",
    "CFC115": "CFC-115",
    "CH2Cl2": "CH2Cl2",
    "CH3Br": "CH3Br",
    "CH3CCl3": "CH3CCl3",
    "CH3Cl": "CH3Cl",
    "CH4": "CH4",
    "CHCl3": "CHCl3",
    "CO": "CO",
    "AFOLU": "CO2 AFOLU",
    "Energy and Industrial Processes": "CO2 FFI",
    "HCFC141b": "HCFC-141b",
    "HCFC142b": "HCFC-142b",
    "HCFC22": "HCFC-22",
    "HFC125": "HFC-125",
    "HFC134a": "HFC-134a",
    "HFC143a": "HFC-143a",
    "HFC152a": "HFC-152a",
    "HFC227ea": "HFC-227ea",
    "HFC23": "HFC-23",
    "HFC236fa": "HFC-236fa",
    "HFC245fa": "HFC-245fa",
    "HFC32": "HFC-32",
    "HFC365mfc": "HFC-365mfc",
    "HFC43-10": "HFC-4310mee",
    "Halon1202": "Halon-1202",
    "Halon1211": "Halon-1211",
    "Halon1301": "Halon-1301",
    "Halon2402": "Halon-2402",
    "N2O": "N2O",
    "NF3": "NF3",
    "NH3": "NH3",
    "NOx": "NOx",
    "Aviation": "NOx aviation",
    "OC": "OC",
    "C2F6": "C2F6",
    "C3F8": "C3F8",
    "C4F10": "C4F10",
    "C5F12": "C5F12",
    "C6F14": "C6F14",
    "C7F16": "C7F16",
    "C8F18": "C8F18",
    "CF4": "CF4",
    "cC4F8": "c-C4F8",
    "SF6": "SF6",
    "SO2F2": "SO2F2",
    "Sulfur": "Sulfur",
    "VOC": "VOC",
}

# CO2 species need Mt -> Gt conversion. Everything else matches RCMIP units.
MT_TO_GT_SPECIES = {"CO2 AFOLU", "CO2 FFI"}


def load_rff_draw(draw_idx: int) -> pd.DataFrame:
    fname = RFF_DIR / f"emissions{draw_idx:05d}.csv"
    if not fname.exists():
        raise FileNotFoundError(fname)
    df = pd.read_csv(fname)
    df["species"] = df["variable"].str.split("|").str[-1]
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draw", type=int, required=True,
                    help="RFF-SP draw index (1..10000)")
    ap.add_argument("--output-dir", type=Path, default=PROJ_DIR / "outputs")
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    START_YEAR, END_YEAR = 1750, 2301
    PI_BASELINE = (1850, 1900)

    # 1) Calibration -----------------------------------------------------------
    print("Fetching FaIR v1.4.1 calibration (841 configs)...")
    params_file = pooch.retrieve(
        url="https://zenodo.org/records/10566813/files/calibrated_constrained_parameters.csv",
        known_hash=None,
    )
    df_cfg = pd.read_csv(params_file, index_col=0)
    configs = df_cfg.index.tolist()
    print(f"  {len(configs)} configs")

    # 2) Initialize FaIR -------------------------------------------------------
    print("Initializing FaIR 2.2.4...")
    f = FAIR(ch4_method="Thornhill2021")
    f.define_time(START_YEAR, END_YEAR, step=1)
    scen = f"rff_draw{args.draw}"
    f.define_scenarios([scen])
    f.define_configs(configs)
    species, properties = read_properties()
    f.define_species(species, properties)
    f.allocate()

    # 3) Fill species/climate configs ------------------------------------------
    f.fill_species_configs()
    print("Filling 841 climate configs from calibration CSV...")
    for cfg in configs:
        row = df_cfg.loc[cfg]
        fill(f.climate_configs["gamma_autocorrelation"], row["clim_gamma"],     config=cfg)
        fill(f.climate_configs["ocean_heat_capacity"],   row["clim_c1"],        config=cfg, layer=0)
        fill(f.climate_configs["ocean_heat_capacity"],   row["clim_c2"],        config=cfg, layer=1)
        fill(f.climate_configs["ocean_heat_capacity"],   row["clim_c3"],        config=cfg, layer=2)
        fill(f.climate_configs["ocean_heat_transfer"],   row["clim_kappa1"],    config=cfg, layer=0)
        fill(f.climate_configs["ocean_heat_transfer"],   row["clim_kappa2"],    config=cfg, layer=1)
        fill(f.climate_configs["ocean_heat_transfer"],   row["clim_kappa3"],    config=cfg, layer=2)
        fill(f.climate_configs["deep_ocean_efficacy"],   row["clim_epsilon"],   config=cfg)
        fill(f.climate_configs["sigma_eta"],             row["clim_sigma_eta"], config=cfg)
        fill(f.climate_configs["sigma_xi"],              row["clim_sigma_xi"],  config=cfg)
        fill(f.climate_configs["forcing_4co2"],          row["clim_F_4xCO2"],   config=cfg)
        fill(f.climate_configs["stochastic_run"],        False,                 config=cfg)
        fill(f.climate_configs["use_seed"],              True,                  config=cfg)
        fill(f.climate_configs["seed"],                  int(row["seed"]),      config=cfg)
        fill(f.species_configs["iirf_0"],                row["cc_r0"],  config=cfg, specie="CO2")
        fill(f.species_configs["iirf_uptake"],           row["cc_rU"],  config=cfg, specie="CO2")
        fill(f.species_configs["iirf_temperature"],      row["cc_rT"],  config=cfg, specie="CO2")
        fill(f.species_configs["iirf_airborne"],         row["cc_rA"],  config=cfg, specie="CO2")
        fill(f.species_configs["baseline_concentration"], row["cc_co2_concentration_1750"],
             config=cfg, specie="CO2")
        for specie, col in [
            ("BC", "ari_BC"), ("OC", "ari_OC"), ("Sulfur", "ari_Sulfur"),
            ("NOx", "ari_NOx"), ("VOC", "ari_VOC"), ("NH3", "ari_NH3"),
            ("CH4", "ari_CH4"), ("N2O", "ari_N2O"),
            ("Equivalent effective stratospheric chlorine",
             "ari_Equivalent effective stratospheric chlorine"),
        ]:
            fill(f.species_configs["erfari_radiative_efficiency"],
                 row[col], config=cfg, specie=specie)
        fill(f.species_configs["aci_shape"], row["aci_shape_so2"], config=cfg, specie="Sulfur")
        fill(f.species_configs["aci_shape"], row["aci_shape_bc"],  config=cfg, specie="BC")
        fill(f.species_configs["aci_shape"], row["aci_shape_oc"],  config=cfg, specie="OC")
        fill(f.species_configs["aci_scale"], row["aci_beta"],      config=cfg)
        for specie, col in [
            ("CH4", "o3_CH4"), ("N2O", "o3_N2O"),
            ("Equivalent effective stratospheric chlorine",
             "o3_Equivalent effective stratospheric chlorine"),
            ("CO", "o3_CO"), ("VOC", "o3_VOC"), ("NOx", "o3_NOx"),
        ]:
            fill(f.species_configs["ozone_radiative_efficiency"],
                 row[col], config=cfg, specie=specie)
        for specie, col in [
            ("CH4", "fscale_CH4"), ("N2O", "fscale_N2O"), ("CO2", "fscale_CO2"),
            ("Volcanic", "fscale_Volcanic"), ("Solar", "fscale_solar_amplitude"),
            ("Stratospheric water vapour", "fscale_Stratospheric water vapour"),
            ("Land use", "fscale_Land use"),
            ("Light absorbing particles on snow and ice",
             "fscale_Light absorbing particles on snow and ice"),
        ]:
            fill(f.species_configs["forcing_scale"], row[col], config=cfg, specie=specie)
        for sp2 in ["CCl4", "CFC-11", "CFC-12", "CFC-113", "CFC-114", "CFC-115",
                    "HCFC-22", "HCFC-141b", "HCFC-142b", "CH3CCl3", "CH3Cl",
                    "CH3Br", "CH2Cl2", "CHCl3",
                    "Halon-1202", "Halon-1211", "Halon-1301", "Halon-2402",
                    "CF4", "C2F6", "C3F8", "C4F10", "C5F12", "C6F14",
                    "C7F16", "C8F18", "c-C4F8", "NF3", "SF6", "SO2F2",
                    "HFC-125", "HFC-134a", "HFC-143a", "HFC-152a", "HFC-227ea",
                    "HFC-23", "HFC-236fa", "HFC-245fa", "HFC-32", "HFC-365mfc",
                    "HFC-4310mee"]:
            fill(f.species_configs["forcing_scale"],
                 row["fscale_minorGHG"], config=cfg, specie=sp2)

    # 4) Load SSP2-4.5 from RCMIP into a tmp instance to get historical period -
    print("Loading RCMIP ssp245 emissions/forcing for 1750-2014 historical baseline...")
    f_tmp = FAIR(ch4_method="Thornhill2021")
    f_tmp.define_time(START_YEAR, END_YEAR, step=1)
    f_tmp.define_scenarios(["ssp245"])
    f_tmp.define_configs(["unperturbed"])
    species_tmp, props_tmp = read_properties()
    f_tmp.define_species(species_tmp, props_tmp)
    f_tmp.allocate()
    f_tmp.fill_from_rcmip()

    # Copy RCMIP emissions/forcing into our scenario as the starting point
    f.emissions.loc[dict(scenario=scen)] = f_tmp.emissions.sel(scenario="ssp245").values
    f.forcing.loc[dict(scenario=scen)]   = f_tmp.forcing.sel(scenario="ssp245").values
    del f_tmp

    # 5) Overwrite 2015-2300 emissions with RFF-SP infilled draw ---------------
    print(f"Loading RFF-SP draw {args.draw} infilled emissions...")
    rff = load_rff_draw(args.draw)

    years_emis = f.timebounds[:-1].astype(int)
    rff_year_cols = [c for c in rff.columns if c.isdigit()]
    rff_years     = np.array([int(c) for c in rff_year_cols])

    n_overwritten = 0
    n_missing     = 0
    n_zero        = 0
    for inf_sp, fair_sp in INF_TO_FAIR.items():
        rows = rff[rff["species"] == inf_sp]
        if len(rows) == 0:
            n_missing += 1
            print(f"  WARN: '{inf_sp}' not found in draw — keeping RCMIP values")
            continue
        if fair_sp not in list(f.species):
            print(f"  WARN: FaIR has no species '{fair_sp}' — skipping")
            continue
        j = list(f.species).index(fair_sp)
        vals = rows[rff_year_cols].values.astype(float).flatten()
        if fair_sp in MT_TO_GT_SPECIES:
            vals = vals / 1000.0          # Mt CO2/yr -> Gt CO2/yr
        for k, yr in enumerate(rff_years):
            if yr < 2015 or yr > 2300:
                continue
            t = int(np.where(years_emis == yr)[0][0])
            f.emissions.values[t, 0, :, j] = vals[k]
        n_overwritten += 1
        if np.all(vals == 0):
            n_zero += 1
    print(f"  overwrote {n_overwritten}/{len(INF_TO_FAIR)} species "
          f"(missing={n_missing}, zero-throughout={n_zero})")

    # 6) Initial conditions and historical solar override ----------------------
    years      = f.timebounds.astype(int)
    i_volcanic = list(f.species).index("Volcanic")
    i_solar    = list(f.species).index("Solar")

    initialise(f.concentration, f.species_configs["baseline_concentration"])
    initialise(f.forcing, 0)
    initialise(f.temperature, 0)
    initialise(f.cumulative_emissions, 0)
    initialise(f.airborne_emissions, 0)

    if HIST_FILE.exists():
        df_hist = pd.read_csv(HIST_FILE)
        hist_solar_row = df_hist[df_hist["Variable"] == "Solar"].iloc[0]
        hist_year_cols = {int(c): float(hist_solar_row[c])
                          for c in df_hist.columns if c.isdigit()}
        n_solar_overrides = 0
        for tidx, yr in enumerate(years):
            if yr in hist_year_cols:
                f.forcing.values[tidx, :, :, i_solar] = hist_year_cols[yr]
                n_solar_overrides += 1
        print(f"Solar Cycle 25 historical override: {n_solar_overrides} years")

    # Per-config solar/volcanic scale factors
    fscale_volc  = df_cfg["fscale_Volcanic"].values
    fscale_solar = df_cfg["fscale_solar_amplitude"].values
    f.forcing.values[:, :, :, i_volcanic] *= fscale_volc[np.newaxis, np.newaxis, :]
    f.forcing.values[:, :, :, i_solar]    *= fscale_solar[np.newaxis, np.newaxis, :]

    # 7) Run --------------------------------------------------------------------
    print(f"\nRunning FaIR ({len(configs)} configs)...")
    f.run(progress=True)

    # 8) Extract GMST anomalies -------------------------------------------------
    pi_mask    = (years >= PI_BASELINE[0]) & (years <= PI_BASELINE[1])
    temp_raw   = f.temperature.sel(layer=0).values[:, 0, :]   # (time, configs)
    pi_mean    = temp_raw[pi_mask, :].mean(axis=0)
    temp_anom  = temp_raw - pi_mean[np.newaxis, :]

    # 9) Save -------------------------------------------------------------------
    df_all = pd.DataFrame(temp_anom, columns=[f"config_{c}" for c in configs])
    df_all.insert(0, "year", years)
    df_all = df_all[df_all["year"] >= 1850]
    out_all = args.output_dir / f"rff_draw{args.draw}_temp_all841.csv"
    df_all.to_csv(out_all, index=False)
    print(f"\nWrote per-config trajectories: {out_all}")

    df_summary = pd.DataFrame({
        "year":        years,
        "temp_median": np.median(temp_anom, axis=1),
        "temp_p2.5":   np.percentile(temp_anom,  2.5, axis=1),
        "temp_p97.5":  np.percentile(temp_anom, 97.5, axis=1),
    }).query("year >= 1850")
    out_sum = args.output_dir / f"rff_draw{args.draw}_temp_median.csv"
    df_summary.to_csv(out_sum, index=False)
    print(f"Wrote ensemble summary: {out_sum}")

    # 10) Print sanity-check checkpoints ---------------------------------------
    print("\n=== GMST anomaly (degC, rel 1850-1900), median across 841 configs ===")
    for yr in (1900, 2000, 2020, 2050, 2100, 2200, 2300):
        if yr in years:
            row = df_summary[df_summary["year"] == yr].iloc[0]
            print(f"  {yr}: {row['temp_median']:.3f} "
                  f"[{row['temp_p2.5']:.3f}, {row['temp_p97.5']:.3f}]")


if __name__ == "__main__":
    main()
