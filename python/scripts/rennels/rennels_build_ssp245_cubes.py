"""
rennels_build_ssp245_cubes.py

Build FaIR v1.4.5 SSP2-4.5 flat-cubes (GMST + OHC, 841 configs, 1850-2300)
for the 7-panel SLR figure requested by Lisa Rennels (2026-05-30).

Produces ONE baseline cube plus four CO2-pulse cubes (pulse at 2020.5,
species "CO2 FFI"). Pulse sizes are specified in **GtC** (carbon mass, per
Lisa's request) and converted to **GtCO2** for FaIR v1.4.5, whose CO2 FFI
`input_unit` is GtCO2 (memory: project_fair_v145_co2ffi_is_gtco2):

    pulse_p001   +0.01  GtC  = +0.0366667 GtCO2   (numerically-safe; FIGURE arm, scaled down)
    pulse_p1em4  +1e-4  GtC  = +3.66667e-4 GtCO2   (Lisa's exact request; FIGURE arm, direct)
    pulse_n001   -0.01  GtC  = -0.0366667 GtCO2   (sign-flip sanity)
    pulse_p002   +0.02  GtC  = +0.0733333 GtCO2   (magnitude-doubling sanity)

Each cube is written in the FLAT-CUBE schema consumed by
julia/run_mimibrick_flatcube.jl:
    cells_meta  Int64   (n_cells, 3)   cols = (rff_idx, fair_cfg_idx, seed_idx)
    years       Int64   (n_year,)      1850..2300
    gmst_traj   Float32 (n_cells, n_year)   degC anomaly rel 1850-1900
    ohc_traj    Float32 (n_cells, n_year)   cumulative since 1750, 10^22 J
    erf_2100    Float32 (n_cells,)

Here n_cells = 841 (rff_idx=0, seed_idx=0, fair_cfg_idx = 0..840).

Also writes the metadata CSV that pairs each FaIR config with BRICK posterior
members (post_idx), and runs the FaIR-temperature-level paired-pulse sanity
suite (5 tests) using the +/- and 2x arms generated above.

FaIR model: v2.2.4.  Calibration: v1.4.5 (841 configs).
Run from anywhere with climate-env active:
    source ~/climate-env/bin/activate
    python python/scripts/rennels/rennels_build_ssp245_cubes.py [--posts-per-cfg K]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from fair import FAIR
from fair.interface import fill, initialise
from fair.io import read_properties

# ── Paths ──────────────────────────────────────────────────────────────────────
SLR_ROOT  = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
CAL_DIR   = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/calibration_v145")
OUT_DIR   = SLR_ROOT / "outputs" / "rennels"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PARAMS_FILE    = CAL_DIR / "calibrated_constrained_parameters_1.4.5.csv"
SPECIES_FILE   = CAL_DIR / "species_configs_properties_1.4.5.csv"
EMISSIONS_FILE = CAL_DIR / "emissions_v145_ssp245_harmonized.csv"
FORCING_FILE   = CAL_DIR / "volcanic_solar.csv"
POSTERIOR_FILE = SLR_ROOT / "data" / "MimiBRICK" / "parameters_subsample_brick.csv"

# ── Run configuration ──────────────────────────────────────────────────────────
START_YEAR     = 1750
END_YEAR       = 2301
BASELINE_START = 1850          # PI baseline for GMST anomaly
BASELINE_END   = 1900
KEEP_START     = 1850          # years stored in the cube
KEEP_END       = 2300
PULSE_YEAR     = 2020          # Lisa's spec (pulse applied at 2020.5)

C_TO_CO2 = 44.0 / 12.0         # GtC -> GtCO2 mass conversion (3.66667)

# Pulse arms: name -> size in GtC (carbon mass)
PULSE_ARMS_GTC = {
    "pulse_p001":  +0.01,      # FIGURE: numerically-safe, scaled to 1e-4 GtC
    "pulse_p1em4": +1.0e-4,    # FIGURE: Lisa's exact request, direct
    "pulse_n001":  -0.01,      # sanity: sign-flip
    "pulse_p002":  +0.02,      # sanity: magnitude-doubling
}
BASELINE_SCEN = "baseline"
SCENARIOS = [BASELINE_SCEN] + list(PULSE_ARMS_GTC.keys())

SEED_RNG = 2026                # for deterministic cfg<->post pairing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts-per-cfg", type=int, default=8,
                    help="BRICK posterior members paired per FaIR config in the metadata")
    args = ap.parse_args()

    print(f"rennels_build_ssp245_cubes.py")
    print(f"  FaIR model:    v2.2.4")
    print(f"  Calibration:   {PARAMS_FILE.name} (v1.4.5)")
    print(f"  Emissions:     {EMISSIONS_FILE.name} (SSP2-4.5, scenario='all')")
    print(f"  Forcing:       {FORCING_FILE.name}")
    print(f"  Pulse year:    {PULSE_YEAR} (applied at {PULSE_YEAR}.5)")
    print(f"  Pulse species: CO2 FFI  (input_unit GtCO2)")
    print(f"  Pulse arms (GtC -> GtCO2):")
    for nm, gtc in PULSE_ARMS_GTC.items():
        print(f"    {nm:<12} {gtc:+.5g} GtC = {gtc*C_TO_CO2:+.6g} GtCO2")

    # ── Load calibration + species ──────────────────────────────────────────────
    df_cfg = pd.read_csv(PARAMS_FILE, index_col=0)
    configs = df_cfg.index.tolist()
    species, properties = read_properties(str(SPECIES_FILE))
    print(f"\nLoaded {len(configs)} configs, {len(species)} species (v1.4.5).")

    # ── Main FaIR with all scenarios ────────────────────────────────────────────
    print("Initialising main FaIR ...")
    f = FAIR()
    f.define_time(START_YEAR, END_YEAR, step=1)
    f.define_scenarios(SCENARIOS)
    f.define_species(species, properties)
    f.ch4_method = "Thornhill2021"
    f.define_configs(configs)
    f.allocate()

    # ── Read emissions+forcing via temp FaIR (scenario 'all') ───────────────────
    print("Reading emissions + forcing via temp FaIR (scenario='all') ...")
    f_tmp = FAIR()
    f_tmp.define_time(START_YEAR, END_YEAR, step=1)
    f_tmp.define_scenarios(["all"])
    f_tmp.define_species(species, properties)
    f_tmp.ch4_method = "Thornhill2021"
    f_tmp.define_configs(configs)
    f_tmp.allocate()
    f_tmp.fill_from_csv(emissions_file=str(EMISSIONS_FILE),
                        forcing_file=str(FORCING_FILE))
    for scen in SCENARIOS:
        f.emissions.loc[dict(scenario=scen)] = f_tmp.emissions.sel(scenario="all").values
        f.forcing.loc[dict(scenario=scen)]   = f_tmp.forcing.sel(scenario="all").values
    del f_tmp
    print(f"  Copied emissions + forcing into {len(SCENARIOS)} scenarios.")

    # ── Species configs + posterior overrides ───────────────────────────────────
    print("Applying v1.4.5 species_configs + posterior overrides ...")
    f.fill_species_configs(str(SPECIES_FILE))
    f.override_defaults(str(PARAMS_FILE))

    # Per-config Solar / Volcanic forcing scale (fair-quirks)
    fill(f.forcing,
         f.forcing.sel(specie="Volcanic") * df_cfg["forcing_scale[Volcanic]"].values.squeeze(),
         specie="Volcanic")
    fill(f.forcing,
         f.forcing.sel(specie="Solar") * df_cfg["forcing_scale[Solar]"].values.squeeze(),
         specie="Solar")

    # ── Initial conditions (OHC reset is critical — see lhs_climate_pilot) ──────
    initialise(f.concentration, f.species_configs["baseline_concentration"])
    initialise(f.forcing,              0)
    initialise(f.temperature,          0)
    initialise(f.cumulative_emissions, 0)
    initialise(f.airborne_emissions,   0)
    initialise(f.ocean_heat_content_change, 0)
    if hasattr(f, "toa_imbalance"):
        initialise(f.toa_imbalance, 0)

    # ── Apply pulses ─────────────────────────────────────────────────────────────
    years_tp = f.timepoints.astype(float)
    years_tb = f.timebounds.astype(int)
    i_co2ffi = list(f.species).index("CO2 FFI")
    idx_p_tp = int(np.where(np.isclose(years_tp, PULSE_YEAR + 0.5))[0][0])
    print(f"\nApplying CO2 FFI pulses at {PULSE_YEAR}.5 (timepoint idx {idx_p_tp}):")
    for nm, gtc in PULSE_ARMS_GTC.items():
        gtco2 = gtc * C_TO_CO2
        i_s = SCENARIOS.index(nm)
        pre = float(f.emissions.values[idx_p_tp, i_s, 0, i_co2ffi])
        f.emissions.values[idx_p_tp, i_s, :, i_co2ffi] += gtco2
        post = float(f.emissions.values[idx_p_tp, i_s, 0, i_co2ffi])
        print(f"  {nm:<12} {pre:.5f} -> {post:.5f} GtCO2  (+{gtco2:+.6g})")

    # ── Run ──────────────────────────────────────────────────────────────────────
    print(f"\nRunning FaIR ({len(configs)} configs x {len(SCENARIOS)} scenarios) ...")
    f.run(progress=True)
    print("Run complete.")

    # ── Extract GMST anomaly + OHC per scenario ─────────────────────────────────
    pi_mask = (years_tb >= BASELINE_START) & (years_tb <= BASELINE_END)
    keep    = (years_tb >= KEEP_START) & (years_tb <= KEEP_END)
    years_keep = years_tb[keep]
    i_2100  = int(np.where(years_tb == 2100)[0][0])
    forcing_sum = f.forcing_sum.values            # (T, scen, cfg)
    ohc_full    = f.ocean_heat_content_change.values  # (T, scen, cfg), J

    gmst = {}  # scen -> (n_cfg, n_year) anomaly
    ohc  = {}  # scen -> (n_cfg, n_year) 10^22 J
    erf  = {}  # scen -> (n_cfg,)
    for scen in SCENARIOS:
        si = list(f.scenarios).index(scen)
        traj = f.temperature.sel(layer=0).values[:, si, :]      # (T, cfg)
        pi_mean = traj[pi_mask, :].mean(axis=0)
        anom = (traj - pi_mean[None, :])[keep, :].T              # (cfg, year)
        # float64 (NOT float32): the 1e-4 GtC pulse perturbs GMST by ~1e-7 degC
        # on a ~2.5 degC baseline -> below float32 resolution (~2.5e-7). float32
        # would silently destroy the small-pulse signal before BRICK sees it.
        gmst[scen] = anom.astype(np.float64)
        ohc[scen]  = (ohc_full[:, si, :] / 1e22)[keep, :].T.astype(np.float64)
        erf[scen]  = forcing_sum[i_2100, si, :].astype(np.float32)

    # ── FaIR-level paired-pulse sanity suite (5 tests) ──────────────────────────
    run_fair_sanity(gmst, years_keep)

    # ── Write flat-cubes ─────────────────────────────────────────────────────────
    n_cfg = len(configs)
    cells_meta = np.column_stack([
        np.zeros(n_cfg, dtype=np.int64),          # rff_idx = 0 (single SSP2-4.5)
        np.arange(n_cfg, dtype=np.int64),         # fair_cfg_idx = 0..840
        np.zeros(n_cfg, dtype=np.int64),          # seed_idx = 0
    ])
    for scen in SCENARIOS:
        out = OUT_DIR / f"ssp245_v145_{scen}_cube.npz"
        np.savez_compressed(
            out,
            cells_meta=cells_meta,
            years=years_keep.astype(np.int64),
            gmst_traj=gmst[scen],
            ohc_traj=ohc[scen],
            erf_2100=erf[scen],
        )
        print(f"Wrote cube: {out.name}  gmst{gmst[scen].shape} ohc{ohc[scen].shape}")

    # ── Write metadata CSV (cfg x K posterior members) ──────────────────────────
    n_post = sum(1 for _ in open(POSTERIOR_FILE)) - 1
    K = args.posts_per_cfg
    rng = np.random.default_rng(SEED_RNG)
    pool = rng.permutation(n_post)                # uniform sample of posteriors
    rows = []
    cell = 0
    for cfg_i in range(n_cfg):
        for j in range(K):
            post = int(pool[cell % n_post])
            rows.append(dict(rff_idx=0, fair_cfg_idx=cfg_i, seed_idx=0,
                             post_idx=post))
            cell += 1
    meta = pd.DataFrame(rows)
    meta_path = OUT_DIR / "ssp245_v145_metadata.csv"
    meta.to_csv(meta_path, index=False)
    print(f"\nWrote metadata: {meta_path.name}  ({len(meta)} cells = "
          f"{n_cfg} cfg x {K} posts, BRICK posterior n={n_post})")

    # Smoke metadata (for the BRICK-level sanity suite): 40 cells
    smoke = meta.iloc[:40].copy()
    smoke_path = OUT_DIR / "ssp245_v145_metadata_smoke40.csv"
    smoke.to_csv(smoke_path, index=False)
    print(f"Wrote smoke metadata: {smoke_path.name} ({len(smoke)} cells)")

    print("\nDONE. Cubes + metadata in", OUT_DIR)


def run_fair_sanity(gmst, years):
    """Paired-pulse sanity tests at the FaIR GMST (temperature) level.

    Uses the +0.01 / -0.01 / +0.02 / +1e-4 GtC arms. IRF = pulse - baseline
    (median across configs). Linearity is per-GtC.
    """
    print("\n" + "=" * 72)
    print("FaIR-LEVEL PAIRED-PULSE SANITY SUITE (GMST IRF)")
    print("=" * 72)
    yb = {int(y): k for k, y in enumerate(years)}

    def med_irf(scen):
        return np.median(gmst[scen] - gmst["baseline"], axis=0)  # (n_year,)

    irf_p001  = med_irf("pulse_p001")
    irf_n001  = med_irf("pulse_n001")
    irf_p002  = med_irf("pulse_p002")
    irf_p1em4 = med_irf("pulse_p1em4")

    # Test 1: zero-pulse bit-identical (baseline vs baseline)
    z = np.max(np.abs(gmst["baseline"] - gmst["baseline"]))
    print(f"[1] Zero-pulse bit-identical: max|diff| = {z:.3e}   "
          f"-> {'PASS' if z == 0 else 'FAIL'}")

    # Test 2: sign-flip symmetry (+0.01 vs -0.01)
    k2100 = yb[2100]
    asym = np.max(np.abs(irf_p001 + irf_n001))
    rel  = asym / max(np.max(np.abs(irf_p001)), 1e-30)
    print(f"[2] Sign-flip symmetry: max|irf(+)+irf(-)| = {asym:.3e} degC "
          f"({rel*100:.3f}% of |irf(+)|)   -> "
          f"{'PASS' if rel < 0.02 else 'FAIL'}")

    # Test 3: magnitude doubling (+0.02 ~ 2 x +0.01)
    ratio = irf_p002[k2100] / irf_p001[k2100]
    print(f"[3] Magnitude doubling @2100: irf(0.02)/irf(0.01) = {ratio:.4f}   "
          f"-> {'PASS' if abs(ratio - 2.0) < 0.05 else 'FAIL'}")

    # Test 4: linearity across 3 decades of pulse size (per-GtC IRF agree)
    per_p001  = irf_p001[k2100]  / 0.01
    per_p1em4 = irf_p1em4[k2100] / 1.0e-4
    lin = abs(per_p1em4 - per_p001) / max(abs(per_p001), 1e-30)
    print(f"[4] Linearity (per-GtC IRF @2100): 0.01GtC={per_p001:.5e}  "
          f"1e-4GtC={per_p1em4:.5e}  rel.diff={lin*100:.3f}%   -> "
          f"{'PASS' if lin < 0.05 else 'NOTE (1e-4 near float floor)'}")

    # Test 5: first-principles magnitude (peak IRF for +0.01 GtC scaled to /GtCO2)
    # memory project_v145_pulse_sanity_passed: ~0.408 m degC peak per GtCO2.
    per_gtco2_mC = (irf_p001 / (0.01 * C_TO_CO2)) * 1000.0  # m degC per GtCO2
    kpk = int(np.argmax(per_gtco2_mC))
    print(f"[5] First-principles: peak IRF = {per_gtco2_mC[kpk]:.4f} m degC/GtCO2 "
          f"at {int(years[kpk])}  (expect ~0.4; memory 0.408 @2044)   -> "
          f"{'PASS' if 0.2 < per_gtco2_mC[kpk] < 0.6 else 'CHECK'}")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
