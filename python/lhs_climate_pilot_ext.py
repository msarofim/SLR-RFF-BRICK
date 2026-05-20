"""
lhs_climate_pilot_ext.py

Phase C extension of lhs_climate_pilot.py.

What's new vs. lhs_climate_pilot.py
-----------------------------------
1. `--baseline-mode {rff,ssp245}` selects the emissions source.
     rff     -> sample (rff_idx, fair_cfg_idx) via LHS+random over RFF-SP draws
     ssp245  -> single RCMIP SSP2-4.5 trajectory, all 841 configs, deterministic
2. `--pulse-gtc N` adds a one-year CO2 pulse (in GtC) at `--pulse-year`.
3. `--emissions-delta-csv PATH` subtracts an annual CO2 trajectory (Mt CO2/yr)
   from baseline CO2 FFI emissions. Used for the vehicle-subtraction scenario.
4. Pulse and emissions-delta are applied on top of the same baseline grid AND
   use the same (rff_idx, fair_cfg_idx, seed_idx) triples as the baseline so
   the paired differential (pulse - baseline) cancels stochastic noise.
5. Seed scheme is upgraded to include rff_idx:
       fair_seed = 1000 * seed_idx + cal_seed + rff_idx
   This guarantees a unique noise realization per (rff, cfg, seed_idx) triple,
   AND keeps that realization identical between paired baseline/pulse/vehicle
   runs (because the seed only depends on the inputs).

Output filename pattern
-----------------------
outputs/{baseline}_{scenario_tag}_{stoch|det}_to{end_year}.npz
   e.g. outputs/rff_baseline_stoch_to2300.npz
        outputs/rff_pulse_stoch_to2300.npz
        outputs/rff_vehicle_stoch_to2300.npz
        outputs/ssp245_baseline_det_to2300.npz
        outputs/ssp245_pulse_det_to2300.npz
        outputs/ssp245_vehicle_det_to2300.npz
"""

import argparse
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pooch
from scipy.stats import qmc
from fair import FAIR
from fair.interface import fill, initialise
from fair.io import read_properties

# On Greene we run from /scratch/ms17839/SLR-RFF-BRICK.  We resolve relative to
# this file's location so the script is also runnable from a local checkout.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJ_DIR   = SCRIPT_DIR.parent
RFF_DIR    = PROJ_DIR / "data" / "RFF-SP-emissions" / "csv"
HIST_FILE  = PROJ_DIR / "data" / "volcanic_solar_hist.csv"
OUT_DIR    = PROJ_DIR / "outputs"

# Local-checkout fallback: on the dev laptop the historic override lives in the
# FaIRtoFrEDI project, not inside SLR-RFF-BRICK/data.
if not HIST_FILE.exists():
    alt = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/volcanic_solar_hist.csv")
    if alt.exists():
        HIST_FILE = alt

# RFF-SP emissions species -> FaIR species name
INF_TO_FAIR = {
    "BC": "BC", "CCl4": "CCl4", "CFC11": "CFC-11", "CFC12": "CFC-12",
    "CFC113": "CFC-113", "CFC114": "CFC-114", "CFC115": "CFC-115",
    "CH2Cl2": "CH2Cl2", "CH3Br": "CH3Br", "CH3CCl3": "CH3CCl3", "CH3Cl": "CH3Cl",
    "CH4": "CH4", "CHCl3": "CHCl3", "CO": "CO",
    "AFOLU": "CO2 AFOLU", "Energy and Industrial Processes": "CO2 FFI",
    "HCFC141b": "HCFC-141b", "HCFC142b": "HCFC-142b", "HCFC22": "HCFC-22",
    "HFC125": "HFC-125", "HFC134a": "HFC-134a", "HFC143a": "HFC-143a",
    "HFC152a": "HFC-152a", "HFC227ea": "HFC-227ea", "HFC23": "HFC-23",
    "HFC236fa": "HFC-236fa", "HFC245fa": "HFC-245fa", "HFC32": "HFC-32",
    "HFC365mfc": "HFC-365mfc", "HFC43-10": "HFC-4310mee",
    "Halon1202": "Halon-1202", "Halon1211": "Halon-1211",
    "Halon1301": "Halon-1301", "Halon2402": "Halon-2402",
    "N2O": "N2O", "NF3": "NF3", "NH3": "NH3", "NOx": "NOx", "Aviation": "NOx aviation",
    "OC": "OC", "C2F6": "C2F6", "C3F8": "C3F8", "C4F10": "C4F10", "C5F12": "C5F12",
    "C6F14": "C6F14", "C7F16": "C7F16", "C8F18": "C8F18", "CF4": "CF4",
    "cC4F8": "c-C4F8", "SF6": "SF6", "SO2F2": "SO2F2", "Sulfur": "Sulfur", "VOC": "VOC",
}
# These species are reported in Mt but FaIR wants Gt
MT_TO_GT_SPECIES = {"CO2 AFOLU", "CO2 FFI"}

# Unit conversions for the pulse / emissions-delta logic
GTC_TO_GTCO2 = 44.0 / 12.0     # ~3.6667
GTCO2_TO_GT  = 1.0             # FaIR's CO2 FFI is in GtCO2 already
MT_TO_GT     = 1.0 / 1000.0    # 1 Mt = 0.001 Gt


# -----------------------------------------------------------------------------
# Sample generation (only used in mode=rff)
# -----------------------------------------------------------------------------
def generate_samples(n_draws, n_rff, n_cfg, seed):
    """Generate one LHS and one random sample of size n_draws over (rff, cfg)."""
    rng = np.random.default_rng(seed)
    lhs = qmc.LatinHypercube(d=2, seed=rng).random(n=n_draws)
    rff_lhs = (lhs[:, 0] * n_rff).astype(int) + 1
    cfg_lhs = (lhs[:, 1] * n_cfg).astype(int)
    rff_rnd = rng.integers(1, n_rff + 1, size=n_draws)
    cfg_rnd = rng.integers(0, n_cfg, size=n_draws)
    rows = []
    for k in range(n_draws):
        rows.append(("lhs",    k, int(rff_lhs[k]), int(cfg_lhs[k])))
    for k in range(n_draws):
        rows.append(("random", k, int(rff_rnd[k]), int(cfg_rnd[k])))
    return pd.DataFrame(rows, columns=["sample", "draw_id", "rff_idx", "fair_cfg_idx"])


# -----------------------------------------------------------------------------
# FaIR setup (calibration loading)
# -----------------------------------------------------------------------------
def setup_fair():
    print("Fetching FaIR v1.4.1 calibration (841 configs)...")
    params_file = pooch.retrieve(
        url="https://zenodo.org/records/10566813/files/calibrated_constrained_parameters.csv",
        known_hash=None,
    )
    df_cfg = pd.read_csv(params_file, index_col=0)
    return df_cfg


def configure_fair_instance(scenarios, df_cfg, stochastic=False):
    """Allocate FaIR with all 841 configs and N scenarios. Returns (f, configs)."""
    configs = df_cfg.index.tolist()
    f = FAIR(ch4_method="Thornhill2021")
    f.define_time(1750, 2301, step=1)
    f.define_scenarios(scenarios)
    f.define_configs(configs)
    species, properties = read_properties()
    f.define_species(species, properties)
    f.allocate()
    f.fill_species_configs()
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
        fill(f.climate_configs["stochastic_run"],        bool(stochastic),      config=cfg)
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
    return f, configs


# -----------------------------------------------------------------------------
# Emissions filling (RFF-SP path; identical to Phase A)
# -----------------------------------------------------------------------------
def load_rff_emissions(draw_idx):
    fname = RFF_DIR / f"emissions{draw_idx:05d}.csv"
    df = pd.read_csv(fname)
    df["species"] = df["variable"].str.split("|").str[-1]
    return df


_FILL_CACHE = {}


def precompute_fill_indices(f, fair_species, years_emis):
    species_to_j = {sp: list(fair_species).index(sp) for sp in INF_TO_FAIR.values()
                    if sp in fair_species}
    year_to_t = {int(y): t for t, y in enumerate(years_emis)}
    rff_years_kept = np.array([y for y in range(2015, 2301)])
    t_idxs = np.array([year_to_t[int(y)] for y in rff_years_kept])
    rff_year_cols_kept = [str(y) for y in rff_years_kept]
    species_recipe = []
    for inf_sp, fair_sp in INF_TO_FAIR.items():
        if fair_sp not in species_to_j:
            continue
        species_recipe.append({
            "inf_sp": inf_sp,
            "j":      species_to_j[fair_sp],
            "div":    1000.0 if fair_sp in MT_TO_GT_SPECIES else 1.0,
        })
    _FILL_CACHE["species_recipe"]    = species_recipe
    _FILL_CACHE["t_idxs"]            = t_idxs
    _FILL_CACHE["rff_year_cols"]     = rff_year_cols_kept
    _FILL_CACHE["co2_ffi_j"]         = species_to_j.get("CO2 FFI", None)
    _FILL_CACHE["ch4_j"]             = species_to_j.get("CH4", None)
    _FILL_CACHE["year_to_t"]         = year_to_t


def fill_emissions_for_draw(f, scen_index, rff_df, baseline_emis, baseline_forcing):
    """Copy SSP2-4.5 historical baseline, then overwrite 2015-2300 with RFF-SP."""
    f.emissions.values[:, scen_index, :, :] = baseline_emis
    f.forcing.values [:, scen_index, :, :] = baseline_forcing

    rec       = _FILL_CACHE["species_recipe"]
    t_idxs    = _FILL_CACHE["t_idxs"]
    yr_cols   = _FILL_CACHE["rff_year_cols"]

    by_sp = rff_df.groupby("species")
    for r in rec:
        if r["inf_sp"] not in by_sp.groups:
            continue
        row = by_sp.get_group(r["inf_sp"])
        vals = row[yr_cols].values[0].astype(float)
        if r["div"] != 1.0:
            vals = vals / r["div"]
        f.emissions.values[t_idxs, scen_index, :, r["j"]] = vals[:, None]


# -----------------------------------------------------------------------------
# Pulse + emissions-delta application
# -----------------------------------------------------------------------------
def apply_pulse(f, scen_index, pulse_year, pulse_gtc, pulse_tg_ch4=0.0):
    """Add a one-year pulse to FaIR emissions at `pulse_year`.

    CO2 path (`pulse_gtc`, in GtC):
        FaIR's CO2 FFI emissions are in GtCO2 / yr; 1 GtC = 44/12 GtCO2.
    CH4 path (`pulse_tg_ch4`, in Tg CH4 = Mt CH4):
        FaIR's CH4 emissions are in Mt CH4 / yr (RCMIP units).

    Pulse is applied to every config (all 841 share the same scenario index).
    The two pulses are independent — both can be nonzero, but typical use
    fires one species at a time.
    """
    t = _FILL_CACHE["year_to_t"].get(int(pulse_year))
    if t is None and (pulse_gtc != 0.0 or pulse_tg_ch4 != 0.0):
        raise RuntimeError(f"pulse year {pulse_year} not in emissions time grid")

    if pulse_gtc != 0.0:
        j = _FILL_CACHE["co2_ffi_j"]
        if j is None:
            raise RuntimeError("CO2 FFI index not found in fill cache")
        pulse_gtco2 = pulse_gtc * GTC_TO_GTCO2
        f.emissions.values[t, scen_index, :, j] += pulse_gtco2

    if pulse_tg_ch4 != 0.0:
        j = _FILL_CACHE["ch4_j"]
        if j is None:
            raise RuntimeError("CH4 index not found in fill cache")
        # f.emissions.values shape: (T, scen, cfg, species); Tg CH4/yr.
        f.emissions.values[t, scen_index, :, j] += pulse_tg_ch4


def apply_emissions_delta(f, scen_index, delta_by_year):
    """Subtract a CO2 FFI trajectory (in GtCO2 / yr) from baseline.

    `delta_by_year` is a dict {year: GtCO2_to_subtract}, already in GtCO2.
    """
    if not delta_by_year:
        return
    j = _FILL_CACHE["co2_ffi_j"]
    if j is None:
        raise RuntimeError("CO2 FFI index not found in fill cache")
    for yr, gtco2 in delta_by_year.items():
        t = _FILL_CACHE["year_to_t"].get(int(yr))
        if t is None:
            continue  # silently skip years outside the FaIR window
        f.emissions.values[t, scen_index, :, j] -= float(gtco2)


def load_emissions_delta_csv(path):
    """Load a year, CO2_delta_mt_per_year CSV and return {year: GtCO2/yr}.

    Mt CO2 -> Gt CO2 conversion (1 Mt = 1e-3 Gt).
    Zero rows are kept so downstream code is uniform.
    """
    df = pd.read_csv(path)
    if "year" not in df.columns or "CO2_delta_mt_per_year" not in df.columns:
        raise ValueError(f"{path} must have columns year, CO2_delta_mt_per_year")
    return {int(r["year"]): float(r["CO2_delta_mt_per_year"]) * MT_TO_GT
            for _, r in df.iterrows()}


# -----------------------------------------------------------------------------
# Main driver
# -----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    # baseline / scenario knobs
    ap.add_argument("--baseline-mode", choices=["rff", "ssp245"], default="rff",
                    help="Emissions source: RFF-SP draws (rff) or RCMIP SSP2-4.5 (ssp245).")
    ap.add_argument("--scenario-tag", type=str, default="baseline",
                    help="Suffix for output filenames (baseline, pulse, vehicle, ...).")
    ap.add_argument("--pulse-gtc",  type=float, default=0.0,
                    help="One-year CO2 pulse magnitude in GtC. 0 = no pulse.")
    ap.add_argument("--pulse-tg-ch4", type=float, default=0.0,
                    help="One-year CH4 pulse magnitude in Tg CH4 (= Mt CH4). "
                         "0 = no pulse. Common SC-CH4 convention is 1 Tg.")
    ap.add_argument("--pulse-year", type=int, default=2030,
                    help="Year in which the pulse is applied (added to FFI / CH4).")
    ap.add_argument("--emissions-delta-csv", type=str, default=None,
                    help="Optional CSV (year, CO2_delta_mt_per_year). Subtracted "
                         "from baseline CO2 FFI emissions year-by-year.")
    # sampling / sizing (only relevant in mode=rff)
    ap.add_argument("--n-draws", type=int, default=2000,
                    help="LHS+random sample size for mode=rff (ignored in ssp245 mode).")
    ap.add_argument("--seed-base", type=int, default=2027,
                    help="Master seed for LHS sampling. Phase A used 42; "
                         "Phase C uses 2027 to get a fresh pool of paired draws.")
    ap.add_argument("--batch-size", type=int, default=20,
                    help="Number of scenarios (RFF draws) per FaIR allocation.")
    ap.add_argument("--rff-range",  type=str, default=None,
                    help="Optional 'START:END' (1-based inclusive) RFF chunk.")
    ap.add_argument("--rff-list",   type=str, default=None,
                    help="Optional comma-separated explicit list of rff_idx values "
                         "(1-based). Alternative to --rff-range. Used for the 4-way "
                         "SLR decomp to extend a specific ANOVA-subset of RFFs to 2300.")
    # stochastic
    ap.add_argument("--stochastic", action="store_true",
                    help="Enable FaIR internal variability (sigma_eta, sigma_xi).")
    ap.add_argument("--n-seeds",    type=int, default=1,
                    help="Stochastic seeds per (RFF, cfg) pair. Default 1.")
    # save window
    ap.add_argument("--keep-start", type=int, default=1850)
    ap.add_argument("--keep-end",   type=int, default=2300,
                    help="Last year to save in the cube (default 2300 for Phase C).")
    args = ap.parse_args()

    if args.stochastic and args.batch_size > 1:
        raise ValueError(
            "--batch-size > 1 is not supported with --stochastic because "
            "FaIR 2.2.x's climate_configs[\"seed\"] is per-config, not "
            "per-(scenario, config). With batch_size > 1 the per-scenario "
            "seed assignment silently broadcasts to a wrong shape. "
            "Use --batch-size 1."
        )

    OUT_DIR.mkdir(exist_ok=True)

    # ---- Output path ------------------------------------------------------
    stoch_tag = "stoch" if args.stochastic else "det"
    out_path = OUT_DIR / (
        f"{args.baseline_mode}_{args.scenario_tag}_{stoch_tag}_to{args.keep_end}.npz"
    )
    print(f"Output target: {out_path}")

    # ---- Emissions delta (vehicle subtraction) ----------------------------
    if args.emissions_delta_csv is not None:
        delta_by_year = load_emissions_delta_csv(args.emissions_delta_csv)
        nz = sum(1 for v in delta_by_year.values() if v != 0.0)
        print(f"Loaded emissions delta: {len(delta_by_year)} rows, {nz} nonzero "
              f"(units GtCO2/yr; first nonzero year subtracts "
              f"{next((v for v in delta_by_year.values() if v != 0.0), 0.0):.3f} GtCO2).")
    else:
        delta_by_year = {}

    # ---- Branch on baseline-mode ------------------------------------------
    if args.baseline_mode == "ssp245":
        # Force deterministic, single "scenario" with all 841 configs.
        run_ssp245(args, delta_by_year, out_path)
        return

    # ---- mode == "rff" ----------------------------------------------------
    run_rff(args, delta_by_year, out_path)


# -----------------------------------------------------------------------------
# SSP2-4.5 branch (no LHS, deterministic, 1 x 841 cube)
# -----------------------------------------------------------------------------
def run_ssp245(args, delta_by_year, out_path):
    """Run SSP2-4.5 once with all 841 configs. Optional pulse / delta applied."""
    df_cfg = setup_fair()
    configs = df_cfg.index.tolist()

    # Stochastic disabled for SSP runs -- we want a clean deterministic baseline
    # so that the pulse / vehicle differential is exactly attributable to the
    # emissions perturbation, not to noise.
    if args.stochastic:
        print("[ssp245] --stochastic ignored; SSP2-4.5 baseline is deterministic.")
    stochastic = False

    f, _ = configure_fair_instance(["ssp245"], df_cfg, stochastic=stochastic)
    f.fill_from_rcmip()

    # Build the fill cache so we know the CO2 FFI species index + year map
    species_list = list(f.species)
    years_emis = f.timebounds[:-1].astype(int)
    precompute_fill_indices(f, species_list, years_emis)

    # Solar / volcanic historical override -- same recipe as the RFF branch
    df_hist = pd.read_csv(HIST_FILE)
    hist_solar_row = df_hist[df_hist["Variable"] == "Solar"].iloc[0]
    hist_year_cols = {int(c): float(hist_solar_row[c])
                      for c in df_hist.columns if c.isdigit()}
    i_volcanic = species_list.index("Volcanic")
    i_solar    = species_list.index("Solar")
    fscale_volc  = df_cfg["fscale_Volcanic"].values
    fscale_solar = df_cfg["fscale_solar_amplitude"].values
    years_tb = f.timebounds.astype(int)
    for tidx, yr in enumerate(years_tb):
        if yr in hist_year_cols:
            f.forcing.values[tidx, :, :, i_solar] = hist_year_cols[yr]
    f.forcing.values[:, :, :, i_volcanic] *= fscale_volc[None, None, :]
    f.forcing.values[:, :, :, i_solar]    *= fscale_solar[None, None, :]

    # Apply scenario perturbations to the single scen index = 0
    apply_pulse(f, 0, args.pulse_year, args.pulse_gtc, args.pulse_tg_ch4)
    apply_emissions_delta(f, 0, delta_by_year)

    initialise(f.concentration, f.species_configs["baseline_concentration"])
    initialise(f.forcing, 0)
    initialise(f.temperature, 0)
    initialise(f.cumulative_emissions, 0)
    initialise(f.airborne_emissions, 0)
    initialise(f.ocean_heat_content_change, 0)
    if hasattr(f, "toa_imbalance"):
        initialise(f.toa_imbalance, 0)
    if hasattr(f, "gas_partitions"):
        f.gas_partitions.values[:] = 0

    print("[ssp245] running FaIR (1 scenario, 841 configs)...")
    t0 = time.time()
    f.run(progress=False)
    print(f"[ssp245] done in {time.time() - t0:.1f}s")

    # ---- Build cube and save ---------------------------------------------
    keep_mask = (years_tb >= args.keep_start) & (years_tb <= args.keep_end)
    years_keep = years_tb[keep_mask]
    pi_mask = (years_tb >= 1850) & (years_tb <= 1900)

    traj = f.temperature.sel(layer=0).values[:, 0, :]  # (T, n_cfg)
    pi_mean = traj[pi_mask, :].mean(axis=0)
    anom = traj - pi_mean[None, :]
    gmst = anom[keep_mask, :].astype(np.float32).T  # (n_cfg, n_keep)

    ohc = f.ocean_heat_content_change.values[:, 0, :] / 1e22  # 10^22 J
    ohc_keep = ohc[keep_mask, :].astype(np.float32).T

    forcing_sum = f.forcing_sum.values[keep_mask, 0, :].astype(np.float32).T  # (n_cfg, n_keep)

    # Shape (1, 841, n_keep) so paired-BRICK driver can treat ssp245 like a
    # single-RFF cube without special-casing.
    gmst_cube = gmst[None, :, :]
    ohc_cube  = ohc_keep[None, :, :]
    erf_cube  = forcing_sum[None, :, :]

    np.savez_compressed(
        out_path,
        years=years_keep,
        unique_rffs=np.array([0]),       # placeholder; SSP has no RFF index
        gmst_traj_rff=gmst_cube,
        ohc_traj_rff=ohc_cube,
        erf_traj_rff=erf_cube,
        baseline_mode=np.array(["ssp245"]),
        scenario_tag=np.array([args.scenario_tag]),
        pulse_gtc=np.array([args.pulse_gtc], dtype=np.float32),
        pulse_year=np.array([args.pulse_year], dtype=np.int32),
        pulse_tg_ch4=np.array([args.pulse_tg_ch4], dtype=np.float32),
    )
    print(f"Wrote {out_path}  cube shape={gmst_cube.shape}")

    # Minimal metadata CSV
    meta = pd.DataFrame({
        "sample":       ["ssp245"] * len(df_cfg),
        "draw_id":      np.arange(len(df_cfg)),
        "rff_idx":      [0] * len(df_cfg),
        "fair_cfg_idx": np.arange(len(df_cfg)),
        "gmst_2100":    gmst_cube[0, :, np.where(years_keep == 2100)[0][0]]
                          if 2100 in years_keep else np.full(len(df_cfg), np.nan),
    })
    meta_path = out_path.with_suffix("").as_posix() + "_metadata.csv"
    meta.to_csv(meta_path, index=False)
    print(f"Wrote {meta_path}")


# -----------------------------------------------------------------------------
# RFF branch (LHS + random over RFF-SP draws)
# -----------------------------------------------------------------------------
def run_rff(args, delta_by_year, out_path):
    OUT_DIR.mkdir(exist_ok=True)
    tag = f"{args.scenario_tag}_N{args.n_draws}"

    # ---- Sample design ----------------------------------------------------
    if args.rff_list is not None:
        rff_array = np.array(
            [int(x) for x in args.rff_list.split(",") if x.strip()],
            dtype=int,
        )
        design = pd.DataFrame({
            "sample":       ["subset"] * len(rff_array),
            "draw_id":      np.arange(len(rff_array)),
            "rff_idx":      rff_array,
            "fair_cfg_idx": [-1] * len(rff_array),
        })
        print(f"--rff-list mode: processing {len(rff_array)} explicit RFFs "
              f"(min={rff_array.min()}, max={rff_array.max()}) with all 841 configs.")
    elif args.rff_range is not None:
        start_str, end_str = args.rff_range.split(":")
        rff_start, rff_end = int(start_str), int(end_str)
        unique_rffs_override = np.arange(rff_start, rff_end + 1, dtype=int)
        design = pd.DataFrame({
            "sample":       ["chunk"] * len(unique_rffs_override),
            "draw_id":      np.arange(len(unique_rffs_override)),
            "rff_idx":      unique_rffs_override,
            "fair_cfg_idx": [-1] * len(unique_rffs_override),
        })
        print(f"--rff-range mode: processing RFFs {rff_start}-{rff_end} "
              f"({len(unique_rffs_override)} draws) with all 841 configs.")
    else:
        print(f"Generating LHS + random samples (n={args.n_draws} each, "
              f"seed-base={args.seed_base})...")
        design = generate_samples(args.n_draws, n_rff=10000, n_cfg=841,
                                  seed=args.seed_base)
        design.to_csv(OUT_DIR / f"design_{args.scenario_tag}_N{args.n_draws}.csv",
                      index=False)
        print(f"  total rows = {len(design)}  unique RFFs = {design.rff_idx.nunique()}")

    # ---- FaIR setup -------------------------------------------------------
    df_cfg = setup_fair()
    configs = df_cfg.index.tolist()

    print("Loading RCMIP SSP2-4.5 baseline (history + forcing template)...")
    f_tmp = FAIR(ch4_method="Thornhill2021")
    f_tmp.define_time(1750, 2301, step=1)
    f_tmp.define_scenarios(["ssp245"])
    f_tmp.define_configs(["unperturbed"])
    species, properties = read_properties()
    f_tmp.define_species(species, properties)
    f_tmp.allocate()
    f_tmp.fill_from_rcmip()
    baseline_emis    = f_tmp.emissions.sel(scenario="ssp245").values
    baseline_forcing = f_tmp.forcing.sel(scenario="ssp245").values
    del f_tmp

    df_hist = pd.read_csv(HIST_FILE)
    hist_solar_row = df_hist[df_hist["Variable"] == "Solar"].iloc[0]
    hist_year_cols = {int(c): float(hist_solar_row[c])
                      for c in df_hist.columns if c.isdigit()}

    unique_rffs = np.array(sorted(design.rff_idx.unique()))
    n_unique = len(unique_rffs)
    print(f"\nProcessing {n_unique} unique RFF draws in batches of {args.batch_size}...")

    keep_start = int(args.keep_start)
    keep_end   = int(args.keep_end)
    years_full = np.arange(1750, 2302)
    keep_years = (years_full >= keep_start) & (years_full <= keep_end)
    n_keep = int(keep_years.sum())

    n_seeds = int(args.n_seeds) if args.stochastic else 1
    if n_seeds == 1:
        gmst_cube = np.zeros((n_unique, 841, n_keep), dtype=np.float32)
        ohc_cube  = np.zeros((n_unique, 841, n_keep), dtype=np.float32)
        erf_cube  = np.zeros((n_unique, 841, n_keep), dtype=np.float32)
    else:
        gmst_cube = np.zeros((n_unique, 841, n_seeds, n_keep), dtype=np.float32)
        ohc_cube  = np.zeros((n_unique, 841, n_seeds, n_keep), dtype=np.float32)
        erf_cube  = np.zeros((n_unique, 841, n_seeds, n_keep), dtype=np.float32)
    print(f"GMST cube shape: {gmst_cube.shape}  ({gmst_cube.nbytes/1e6:.1f} MB)")
    print(f"Scenario: tag={args.scenario_tag}, pulse_gtc={args.pulse_gtc}, pulse_tg_ch4={args.pulse_tg_ch4}, "
          f"delta_csv={args.emissions_delta_csv}, stochastic={args.stochastic}, "
          f"n_seeds={n_seeds}")

    fscale_volc  = df_cfg["fscale_Volcanic"].values
    fscale_solar = df_cfg["fscale_solar_amplitude"].values
    cal_seeds    = df_cfg["seed"].astype(int).values

    t_start = time.time()
    for ib, batch_start in enumerate(range(0, n_unique, args.batch_size)):
        batch = unique_rffs[batch_start:batch_start + args.batch_size]
        scen_names = [f"rff{r}" for r in batch]

        f, _ = configure_fair_instance(scen_names, df_cfg,
                                       stochastic=args.stochastic)
        species_list = list(f.species)
        i_volcanic = species_list.index("Volcanic")
        i_solar    = species_list.index("Solar")
        years_emis = f.timebounds[:-1].astype(int)
        precompute_fill_indices(f, species_list, years_emis)

        # Fill baseline emissions per scenario, then apply pulse/delta
        for jb, r_idx in enumerate(batch):
            rff_df = load_rff_emissions(int(r_idx))
            fill_emissions_for_draw(f, jb, rff_df, baseline_emis, baseline_forcing)
            apply_pulse(f, jb, args.pulse_year, args.pulse_gtc, args.pulse_tg_ch4)
            apply_emissions_delta(f, jb, delta_by_year)

        # Volcanic / solar history overrides (apply once per FaIR allocation;
        # initialise() in the seed loop only touches t=0, so these persist).
        years_tb = f.timebounds.astype(int)
        for tidx, yr in enumerate(years_tb):
            if yr in hist_year_cols:
                f.forcing.values[tidx, :, :, i_solar] = hist_year_cols[yr]
        f.forcing.values[:, :, :, i_volcanic] *= fscale_volc[None, None, :]
        f.forcing.values[:, :, :, i_solar]    *= fscale_solar[None, None, :]

        for seed_idx in range(n_seeds):
            initialise(f.concentration, f.species_configs["baseline_concentration"])
            initialise(f.forcing, 0)
            initialise(f.temperature, 0)
            initialise(f.cumulative_emissions, 0)
            initialise(f.airborne_emissions, 0)
            initialise(f.ocean_heat_content_change, 0)
            if hasattr(f, "toa_imbalance"):
                initialise(f.toa_imbalance, 0)
            if hasattr(f, "gas_partitions"):
                f.gas_partitions.values[:] = 0

            if args.stochastic:
                # Phase C seed scheme: include rff_idx so each (rff, cfg, seed_idx)
                # triple has a unique noise realization. Paired runs
                # (baseline/pulse/vehicle) with the same triple share the same
                # noise realization because the seed only depends on the
                # inputs -- this is what makes the paired SCC differential
                # cancel stochastic noise.
                #
                # NOTE: FaIR 2.2.x's climate_configs["seed"] is shape (n_cfg,)
                # -- per-config only, no scenario dim. That's why argparse
                # rejects batch_size > 1 with --stochastic. With batch_size==1
                # the assignment below is shape (1, n_cfg) -> (n_cfg,) which
                # broadcasts cleanly; with batch_size>1 it would silently
                # mis-broadcast.
                assert len(batch) == 1, "stochastic path requires batch_size=1"
                seed_arr = f.climate_configs["seed"]
                rff_col = np.array([int(r) for r in batch], dtype=np.int64)[:, None]
                cal_row = cal_seeds.astype(np.int64)[None, :]
                seed_matrix = 1000 * seed_idx + cal_row + rff_col  # (1, n_cfg)
                seed_arr.values[:] = seed_matrix

            f.run(progress=False)

            years_tb = f.timebounds.astype(int)
            pi_mask = (years_tb >= 1850) & (years_tb <= 1900)
            forcing_sum = f.forcing_sum.values
            ohc_full = f.ocean_heat_content_change.values

            for jb, (r_idx, scen) in enumerate(zip(batch, scen_names)):
                si = list(f.scenarios).index(scen)
                traj = f.temperature.sel(layer=0).values[:, si, :]
                pi_mean = traj[pi_mask, :].mean(axis=0)
                anom = traj - pi_mean[None, :]
                keep = (years_tb >= keep_start) & (years_tb <= keep_end)
                ohc_traj = ohc_full[:, si, :] / 1e22
                erf_traj = forcing_sum[:, si, :]
                if n_seeds == 1:
                    gmst_cube[batch_start + jb, :, :] = anom[keep, :].astype(np.float32).T
                    ohc_cube[batch_start + jb, :, :]  = ohc_traj[keep, :].astype(np.float32).T
                    erf_cube[batch_start + jb, :, :]  = erf_traj[keep, :].astype(np.float32).T
                else:
                    gmst_cube[batch_start + jb, :, seed_idx, :] = anom[keep, :].astype(np.float32).T
                    ohc_cube[batch_start + jb, :, seed_idx, :]  = ohc_traj[keep, :].astype(np.float32).T
                    erf_cube[batch_start + jb, :, seed_idx, :]  = erf_traj[keep, :].astype(np.float32).T

        elapsed = time.time() - t_start
        done = batch_start + len(batch)
        rate = done / max(elapsed, 1e-6)
        eta = (n_unique - done) / max(rate, 1e-6)
        print(f"  batch {ib+1}: {done}/{n_unique} unique RFFs done "
              f"({elapsed:.0f}s elapsed, ETA {eta:.0f}s)")
        del f

    # ---- Save cube + metadata --------------------------------------------
    years_keep = years_full[keep_years]
    np.savez_compressed(
        out_path,
        years=years_keep,
        unique_rffs=unique_rffs,
        gmst_traj_rff=gmst_cube,
        ohc_traj_rff=ohc_cube,
        erf_traj_rff=erf_cube,
        baseline_mode=np.array([args.baseline_mode]),
        scenario_tag=np.array([args.scenario_tag]),
        pulse_gtc=np.array([args.pulse_gtc], dtype=np.float32),
        pulse_year=np.array([args.pulse_year], dtype=np.int32),
        pulse_tg_ch4=np.array([args.pulse_tg_ch4], dtype=np.float32),
    )
    print(f"\nWrote {out_path}  cube shape={gmst_cube.shape}  "
          f"({gmst_cube.nbytes/1e6:.1f} MB)")

    # Lookup helper: (rff_idx -> position in unique_rffs)
    rff_to_pos = {int(r): k for k, r in enumerate(unique_rffs)}
    i2100 = int(np.where(years_keep == 2100)[0][0]) if 2100 in years_keep else len(years_keep) - 1
    i2050 = int(np.where(years_keep == 2050)[0][0]) if 2050 in years_keep else 0

    rows = []
    for _, dr in design.iterrows():
        pos = rff_to_pos[int(dr.rff_idx)]
        cfg = int(dr.fair_cfg_idx)
        if cfg < 0:    # rff-range mode -- no LHS pairings, just leave NaN
            rows.append((dr["sample"], int(dr.draw_id), int(dr.rff_idx), cfg,
                         np.nan, np.nan))
            continue
        if n_seeds == 1:
            g50  = float(gmst_cube[pos, cfg, i2050])
            g100 = float(gmst_cube[pos, cfg, i2100])
        else:
            g50  = float(gmst_cube[pos, cfg, :, i2050].mean())
            g100 = float(gmst_cube[pos, cfg, :, i2100].mean())
        rows.append((dr["sample"], int(dr.draw_id), int(dr.rff_idx), cfg, g50, g100))
    meta = pd.DataFrame(rows, columns=["sample","draw_id","rff_idx","fair_cfg_idx",
                                       "gmst_2050","gmst_2100"])
    meta_path = out_path.with_suffix("").as_posix() + "_metadata.csv"
    meta.to_csv(meta_path, index=False)
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    main()
