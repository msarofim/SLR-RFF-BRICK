"""
lhs_climate_pilot.py

LHS pilot for climate-side uncertainty (RFF-SP draw x FaIR config), no FrEDI.

Approach:
  - Generate two N=2000 samples over (rff_idx in 1..10000, fair_cfg_idx in 0..840):
      * Latin Hypercube Sample (variance-reducing stratification)
      * Independent uniform random sample (baseline for comparison)
  - For each unique RFF draw used in EITHER sample, run FaIR with all 841
    configs in one shot (~3 sec). Cache the (year x 841) GMST trajectory.
  - For each LHS / random pair, look up the GMST trajectory of its specific
    config and save (draw_id, sample, rff_idx, fair_cfg_idx, GMST_2100).
  - Save full GMST trajectories per draw for downstream BRICK runs.

This batches FaIR by RFF draw, since FaIR with 841 configs is ~the same cost
as 1 config (most time is per-timestep). Once cached, the LHS lookup is free.

Pipeline overhead:
  - Setup (calibration, configs, RCMIP base): ~5-10 sec total
  - Per unique RFF draw: ~3 sec FaIR run
  - 2000 unique RFFs (worst case for 2 N=2000 samples) = ~100 min FaIR

Outputs:
  outputs/lhs_pilot_metadata.parquet  - (sample, draw_id, rff_idx, fair_cfg_idx, GMST_2100, GMST_2050, ...)
  outputs/lhs_pilot_gmst_full.parquet - (draw_id, year, GMST) long-format for BRICK
  outputs/lhs_pilot_design.csv        - LHS + random pairings (for reproducibility)
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

PROJ_DIR  = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
RFF_DIR   = PROJ_DIR / "data" / "RFF-SP-emissions" / "csv"
HIST_FILE = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/volcanic_solar_hist.csv")
OUT_DIR   = PROJ_DIR / "outputs"

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
MT_TO_GT_SPECIES = {"CO2 AFOLU", "CO2 FFI"}


def generate_samples(n_draws, n_rff, n_cfg, seed=42):
    """Generate one LHS and one random sample of size n_draws over (rff, cfg)."""
    rng = np.random.default_rng(seed)
    # LHS in [0,1)^2, then map to discrete indices
    lhs = qmc.LatinHypercube(d=2, seed=rng).random(n=n_draws)
    rff_lhs = (lhs[:, 0] * n_rff).astype(int) + 1   # 1-based RFF
    cfg_lhs = (lhs[:, 1] * n_cfg).astype(int)       # 0-based config

    # Independent uniform random (no stratification)
    rff_rnd = rng.integers(1, n_rff + 1, size=n_draws)
    cfg_rnd = rng.integers(0, n_cfg, size=n_draws)

    rows = []
    for k in range(n_draws):
        rows.append(("lhs",    k, int(rff_lhs[k]), int(cfg_lhs[k])))
    for k in range(n_draws):
        rows.append(("random", k, int(rff_rnd[k]), int(cfg_rnd[k])))
    return pd.DataFrame(rows, columns=["sample", "draw_id", "rff_idx", "fair_cfg_idx"])


def setup_fair():
    """One-time setup: calibration, climate configs, species configs."""
    print("Fetching FaIR v1.4.1 calibration (841 configs)...")
    params_file = pooch.retrieve(
        url="https://zenodo.org/records/10566813/files/calibrated_constrained_parameters.csv",
        known_hash=None,
    )
    df_cfg = pd.read_csv(params_file, index_col=0)
    return df_cfg


def configure_fair_instance(scenarios, df_cfg, stochastic=False):
    """Allocate FaIR with all 841 configs and N scenarios. Returns (f, configs).

    stochastic: if True, set stochastic_run=True so FaIR generates internal
    variability via sigma_eta / sigma_xi from the v1.4.1 posterior. Caller is
    responsible for setting per-realization seeds before each f.run().
    """
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


def load_rff_emissions(draw_idx):
    """Load infilled emissions for one RFF-SP draw."""
    fname = RFF_DIR / f"emissions{draw_idx:05d}.csv"
    df = pd.read_csv(fname)
    df["species"] = df["variable"].str.split("|").str[-1]
    return df


# Precomputed indices (filled once per allocation) — avoid per-call np.where
_FILL_CACHE = {}


def precompute_fill_indices(f, fair_species, years_emis):
    """Build the species-name -> j and year -> tstep maps and cache them.
       Also build the fixed list of (inf_sp, j, divisor, t_idxs) tuples."""
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


def fill_emissions_for_draw(f, scen_index, rff_df, baseline_emis, baseline_forcing):
    """Fast emissions fill: copy baseline then overwrite 2015-2300 by species.
       baseline_emis / baseline_forcing are (T, n_cfg, n_species) — pre-squeezed."""
    # Copy baseline once (broadcasts (T, n_cfg, n_species) into (T, n_cfg, n_species))
    f.emissions.values[:, scen_index, :, :] = baseline_emis
    f.forcing.values [:, scen_index, :, :] = baseline_forcing

    rec       = _FILL_CACHE["species_recipe"]
    t_idxs    = _FILL_CACHE["t_idxs"]
    yr_cols   = _FILL_CACHE["rff_year_cols"]

    # Index rff_df by species name once for fast lookup
    by_sp = rff_df.groupby("species")
    for r in rec:
        if r["inf_sp"] not in by_sp.groups:
            continue
        row = by_sp.get_group(r["inf_sp"])
        vals = row[yr_cols].values[0].astype(float)
        if r["div"] != 1.0:
            vals = vals / r["div"]
        f.emissions.values[t_idxs, scen_index, :, r["j"]] = vals[:, None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-draws", type=int, default=2000)
    ap.add_argument("--seed",    type=int, default=42)
    ap.add_argument("--batch-size", type=int, default=20,
                    help="N RFF draws per FaIR allocation; trades RAM for setup overhead")
    ap.add_argument("--output-tag", type=str, default="")
    ap.add_argument("--keep-start", type=int, default=1850,
                    help="Start year of GMST trajectory to save (default 1850)")
    ap.add_argument("--keep-end",   type=int, default=2100,
                    help="End year of GMST trajectory to save (default 2100)")
    ap.add_argument("--rff-range",  type=str, default=None,
                    help="START:END (1-based, inclusive) RFF draws to process. "
                         "If set, skips LHS sample generation and processes only "
                         "this contiguous range -- used for Greene array jobs.")
    ap.add_argument("--stochastic", action="store_true",
                    help="Enable FaIR stochastic_run (uses calibrated sigma_eta, "
                         "sigma_xi per config). Default: deterministic.")
    ap.add_argument("--n-seeds",   type=int, default=1,
                    help="Number of stochastic seeds per (RFF, cfg) pair. "
                         "Only meaningful with --stochastic. Default 1.")
    args = ap.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    tag = args.output_tag if args.output_tag else f"N{args.n_draws}"

    if args.rff_range is not None:
        # Greene-array path: process a contiguous chunk of RFF draws,
        # all 841 configs each. No LHS sampling -- caller stitches later.
        start_str, end_str = args.rff_range.split(":")
        rff_start, rff_end = int(start_str), int(end_str)
        unique_rffs_override = np.arange(rff_start, rff_end + 1, dtype=int)
        design = pd.DataFrame({
            "sample":       ["chunk"] * len(unique_rffs_override),
            "draw_id":      np.arange(len(unique_rffs_override)),
            "rff_idx":      unique_rffs_override,
            "fair_cfg_idx": [-1] * len(unique_rffs_override),  # placeholder, not used
        })
        print(f"--rff-range mode: processing RFF draws {rff_start}-{rff_end} "
              f"({len(unique_rffs_override)} draws) with all 841 configs.")
    else:
        # 1) Generate LHS + random samples
        print(f"Generating LHS + random samples (n={args.n_draws} each)...")
        design = generate_samples(args.n_draws, n_rff=10000, n_cfg=841,
                                  seed=args.seed)
        design.to_csv(OUT_DIR / f"lhs_design_{tag}.csv", index=False)
        print(f"  total rows = {len(design)} (LHS + random)")
        print(f"  unique RFF draws used: {design.rff_idx.nunique()}")

    # 2) FaIR setup -- once
    df_cfg = setup_fair()
    configs = df_cfg.index.tolist()

    # 3) Build RCMIP ssp245 baseline (1750-2014 history) once
    print("Loading RCMIP ssp245 emissions/forcing baseline...")
    f_tmp = FAIR(ch4_method="Thornhill2021")
    f_tmp.define_time(1750, 2301, step=1)
    f_tmp.define_scenarios(["ssp245"])
    f_tmp.define_configs(["unperturbed"])
    species, properties = read_properties()
    f_tmp.define_species(species, properties)
    f_tmp.allocate()
    f_tmp.fill_from_rcmip()
    baseline_emis    = f_tmp.emissions.sel(scenario="ssp245").values  # (T, 1, n_species)
    baseline_forcing = f_tmp.forcing.sel(scenario="ssp245").values
    del f_tmp

    # 4) Load Solar Cycle 25 historical override
    df_hist = pd.read_csv(HIST_FILE)
    hist_solar_row = df_hist[df_hist["Variable"] == "Solar"].iloc[0]
    hist_year_cols = {int(c): float(hist_solar_row[c])
                      for c in df_hist.columns if c.isdigit()}

    # 5) Loop over unique RFF draws in batches
    unique_rffs = np.array(sorted(design.rff_idx.unique()))
    n_unique = len(unique_rffs)
    print(f"\nProcessing {n_unique} unique RFF draws in batches of {args.batch_size}...")

    # Per-draw GMST trajectory. Allow caller to pick keep range.
    keep_start = int(args.keep_start)
    keep_end   = int(args.keep_end)
    years_full = np.arange(1750, 2302)
    keep_years = (years_full >= keep_start) & (years_full <= keep_end)
    n_keep = int(keep_years.sum())

    # We will accumulate results in long-format
    n_seeds = int(args.n_seeds) if args.stochastic else 1
    metadata_rows = []
    if n_seeds == 1:
        gmst_traj_rff = np.zeros((n_unique, 841, n_keep), dtype=np.float32)
        ohc_traj_rff  = np.zeros((n_unique, 841, n_keep), dtype=np.float32)
        erf_2100_rff  = np.zeros((n_unique, 841), dtype=np.float32)
    else:
        gmst_traj_rff = np.zeros((n_unique, 841, n_seeds, n_keep), dtype=np.float32)
        ohc_traj_rff  = np.zeros((n_unique, 841, n_seeds, n_keep), dtype=np.float32)
        erf_2100_rff  = np.zeros((n_unique, 841, n_seeds), dtype=np.float32)
    print(f"GMST cube shape: {gmst_traj_rff.shape}  "
          f"({gmst_traj_rff.nbytes/1e6:.1f} MB)")
    print(f"OHC  cube shape: {ohc_traj_rff.shape}  "
          f"({ohc_traj_rff.nbytes/1e6:.1f} MB)")
    print(f"Stochastic: {args.stochastic}, n_seeds: {n_seeds}")

    fscale_volc  = df_cfg["fscale_Volcanic"].values
    fscale_solar = df_cfg["fscale_solar_amplitude"].values

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
        for jb, r_idx in enumerate(batch):
            rff_df = load_rff_emissions(int(r_idx))
            fill_emissions_for_draw(f, jb, rff_df, baseline_emis, baseline_forcing)

        years = f.timebounds.astype(int)
        # Solar Cycle 25 override (annual values) and per-config scale factors
        # for volcanic + solar are applied ONCE per batch -- they affect all
        # timesteps of f.forcing, and initialise() below only touches the
        # first timebound, so they survive across seeds.
        for tidx, yr in enumerate(years):
            if yr in hist_year_cols:
                f.forcing.values[tidx, :, :, i_solar] = hist_year_cols[yr]
        f.forcing.values[:, :, :, i_volcanic] *= fscale_volc[None, None, :]
        f.forcing.values[:, :, :, i_solar]    *= fscale_solar[None, None, :]

        cal_seeds = df_cfg["seed"].astype(int).values
        for seed_idx in range(n_seeds):
            # Re-initialise time-0 state per realization. Without this,
            # ocean_heat_content_change[0] (and toa_imbalance[0]) carry
            # forward across f.run() calls, accumulating across seeds.
            initialise(f.concentration, f.species_configs["baseline_concentration"])
            initialise(f.forcing, 0)
            initialise(f.temperature, 0)
            initialise(f.cumulative_emissions, 0)
            initialise(f.airborne_emissions, 0)
            initialise(f.ocean_heat_content_change, 0)
            if hasattr(f, "toa_imbalance"):
                initialise(f.toa_imbalance, 0)
            # gas_partitions has shape (n_scen, n_cfg, n_species, n_pools)
            # -- NO time dimension. So initialise() (which only sets the
            # first slot of the leading dim) wouldn't reset all scenarios.
            # Reset the full array directly. Without this, each f.run() in
            # the seed loop inherits the previous run's gas-pool state and
            # the carbon cycle compounds upward across seeds.
            if hasattr(f, "gas_partitions"):
                f.gas_partitions.values[:] = 0

            if args.stochastic:
                # Per-realization seed = 1000 * seed_idx + calibrated seed.
                # Reproducible and orthogonal across (config, realization).
                for k_cfg, cfg_label in enumerate(configs):
                    fill(f.climate_configs["seed"],
                         1000 * seed_idx + int(cal_seeds[k_cfg]),
                         config=cfg_label)

            f.run(progress=False)

            # Anomaly relative to 1850-1900
            years_tb = f.timebounds.astype(int)
            pi_mask = (years_tb >= 1850) & (years_tb <= 1900)
            i_2100  = int(np.where(years_tb == 2100)[0][0])
            forcing_sum = f.forcing_sum.values
            ohc_full = f.ocean_heat_content_change.values  # (T, scen, cfg), in J
            for jb, (r_idx, scen) in enumerate(zip(batch, scen_names)):
                si = list(f.scenarios).index(scen)
                traj = f.temperature.sel(layer=0).values[:, si, :]
                pi_mean = traj[pi_mask, :].mean(axis=0)
                anom = traj - pi_mean[None, :]
                # OHC: cumulative since 1750 (FaIR initialises to 0). Convert
                # J -> 10^22 J for MimiBRICK convention.
                ohc_traj = ohc_full[:, si, :] / 1e22       # (T, n_cfg)
                keep = (years_tb >= keep_start) & (years_tb <= keep_end)
                if n_seeds == 1:
                    gmst_traj_rff[batch_start + jb, :, :] = \
                        anom[keep, :].astype(np.float32).T
                    ohc_traj_rff[batch_start + jb, :, :] = \
                        ohc_traj[keep, :].astype(np.float32).T
                    erf_2100_rff[batch_start + jb, :] = \
                        forcing_sum[i_2100, si, :].astype(np.float32)
                else:
                    gmst_traj_rff[batch_start + jb, :, seed_idx, :] = \
                        anom[keep, :].astype(np.float32).T
                    ohc_traj_rff[batch_start + jb, :, seed_idx, :] = \
                        ohc_traj[keep, :].astype(np.float32).T
                    erf_2100_rff[batch_start + jb, :, seed_idx] = \
                        forcing_sum[i_2100, si, :].astype(np.float32)

        elapsed = time.time() - t_start
        done = batch_start + len(batch)
        rate = done / max(elapsed, 1e-6)
        eta = (n_unique - done) / max(rate, 1e-6)
        print(f"  batch {ib+1}: {done}/{n_unique} unique RFFs done "
              f"({elapsed:.0f}s elapsed, ETA {eta:.0f}s)")

        del f

    # 6) Build metadata table by looking up GMST_2100 for each LHS/random pair
    rff_to_pos = {int(r): k for k, r in enumerate(unique_rffs)}
    years_keep = years_full[keep_years]
    i2050 = int(np.where(years_keep == 2050)[0][0]) if 2050 in years_keep else 0
    i2100 = int(np.where(years_keep == 2100)[0][0]) if 2100 in years_keep else len(years_keep) - 1

    # Save the cube FIRST so a metadata-loop bug doesn't lose hours of compute.
    np.savez_compressed(
        OUT_DIR / f"lhs_pilot_gmst_full_{tag}.npz",
        years=years_keep,
        unique_rffs=unique_rffs,
        gmst_traj_rff=gmst_traj_rff,
        ohc_traj_rff=ohc_traj_rff,    # cumulative since 1750, units 10^22 J
    )

    rows = []
    for _, dr in design.iterrows():
        pos = rff_to_pos[int(dr.rff_idx)]
        cfg = int(dr.fair_cfg_idx)
        if n_seeds == 1:
            gmst_2100 = float(gmst_traj_rff[pos, cfg, i2100])
            gmst_2050 = float(gmst_traj_rff[pos, cfg, i2050])
            erf_2100  = float(erf_2100_rff[pos, cfg])
        else:
            # Mean across stochastic seeds for the metadata summary; full
            # seed-specific data is in the cube for variance decomposition.
            gmst_2100 = float(gmst_traj_rff[pos, cfg, :, i2100].mean())
            gmst_2050 = float(gmst_traj_rff[pos, cfg, :, i2050].mean())
            erf_2100  = float(erf_2100_rff[pos, cfg, :].mean())
        rows.append((dr["sample"], int(dr.draw_id), int(dr.rff_idx), cfg,
                     gmst_2050, gmst_2100, erf_2100))
    meta = pd.DataFrame(rows, columns=["sample","draw_id","rff_idx","fair_cfg_idx",
                                       "gmst_2050","gmst_2100","erf_2100"])
    meta_path = OUT_DIR / f"lhs_pilot_metadata_{tag}.csv"
    meta.to_csv(meta_path, index=False)
    print(f"\nWrote {meta_path}")
    print(f"Wrote {OUT_DIR}/lhs_pilot_gmst_full_{tag}.npz "
          f"(shape {gmst_traj_rff.shape}, "
          f"{gmst_traj_rff.nbytes/1e6:.1f} MB)")

    # Quick summary (guard against empty categories, e.g. when --rff-range
    # selects a slice that contains only one of lhs/random)
    print("\n=== 2100 GMST summary (degC, rel 1850-1900) ===")
    for s in ["lhs", "random"]:
        v = meta[meta["sample"] == s]["gmst_2100"].values
        if len(v) == 0:
            print(f"  {s:8s}: (no rows)")
            continue
        print(f"  {s:8s}: median={np.median(v):.3f}  "
              f"5th={np.percentile(v,5):.3f}  95th={np.percentile(v,95):.3f}  "
              f"n={len(v)}")
    print("\n=== 2100 ERF summary (W/m^2) ===")
    print("  Sarofim et al. 2024: median=5.1  5-95% range=[3.3, 7.1]")
    for s in ["lhs", "random"]:
        v = meta[meta["sample"] == s]["erf_2100"].values
        if len(v) == 0:
            print(f"  {s:8s}: (no rows)")
            continue
        print(f"  {s:8s}: median={np.median(v):.3f}  "
              f"5th={np.percentile(v,5):.3f}  95th={np.percentile(v,95):.3f}  "
              f"n={len(v)}")


if __name__ == "__main__":
    main()
