"""a-vs-b FaIR test on marker ML. The FaIR setup is copied from Ladrillo tools/forcing/build_fair_cube_vv_v160.py
(@ 4da4d97) line for line; only the emissions file varies, and ERF by group is saved as well.
IDENTITY GATE: the LIVE arm's GMST and OHC cubes must be byte-identical to Ladrillo data/forcing/fair_cube_*_vvML_raw.csv.
Deterministic: stochastic_run=False for every config, no RNG is drawn."""
import sys, hashlib
from pathlib import Path
import numpy as np, pandas as pd
from fair import FAIR
from fair.interface import fill, initialise
from fair.io import read_properties

CAL_DIR, OUT, SHIPPED = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
ARMS = dict(arg.split("=", 1) for arg in sys.argv[4:])          # label=emissions_csv
MARKER, SCEN_KEY, SCEN_NAME = "ML", "vvML", "Medium-to-Low - SSP2 (Marker)"
START_YEAR, END_YEAR = 1750, 2301
BASELINE_START, BASELINE_END = 1850, 1900
CUBE_FIRST_YEAR, CUBE_LAST_YEAR, CUBE_DECIMALS = 1850, 2300, 6
CALIB_VERSION = "1.6.0"
HALO_TYPES = {"cfc-11", "other halogen", "f-gas"}

params = CAL_DIR / f"calibrated_constrained_parameters_{CALIB_VERSION}.csv"
species_file = CAL_DIR / f"species_configs_properties_{CALIB_VERSION}.csv"
forcing_file = CAL_DIR / f"volcanic_solar_{MARKER}.csv"
df_configs = pd.read_csv(params, index_col=0)
configs = df_configs.index.tolist()
species, properties = read_properties(str(species_file))
prescribed = [s for s in species if properties[s]["input_mode"] == "forcing"]
groups = {"halogens": [s for s in species if properties[s]["type"] in HALO_TYPES],
          "ozone": [s for s in species if properties[s]["type"] == "ozone"],
          "aerosol": [s for s in species if properties[s]["type"] in ("ari", "aci")],
          "ch4": [s for s in species if properties[s]["type"] == "ch4"],
          "n2o": [s for s in species if properties[s]["type"] == "n2o"],
          "co2": [s for s in species if properties[s]["type"] == "co2"]}
print("groups:", {k: len(v) for k, v in groups.items()})

def run(emis):
    f = FAIR(); f.define_time(START_YEAR, END_YEAR, step=1); f.define_scenarios([SCEN_KEY])
    f.define_species(species, properties); f.ch4_method = "Thornhill2021"; f.define_configs(configs); f.allocate()
    t = FAIR(); t.define_time(START_YEAR, END_YEAR, step=1); t.define_scenarios(["all"])
    t.define_species(species, properties); t.ch4_method = "Thornhill2021"; t.define_configs(configs); t.allocate()
    t.fill_from_csv(emissions_file=None, forcing_file=str(forcing_file))
    forc_arr = t.forcing.sel(scenario="all").values; del t
    e = FAIR(); e.define_time(START_YEAR, END_YEAR, step=1); e.define_scenarios([SCEN_NAME])
    e.define_species(species, properties); e.ch4_method = "Thornhill2021"; e.define_configs(configs); e.allocate()
    e.fill_from_csv(emissions_file=str(emis), forcing_file=None)
    emis_arr = e.emissions.sel(scenario=SCEN_NAME).values; del e
    idx = {s: i for i, s in enumerate(species)}
    ed = [s for s in species if properties[s]["input_mode"] == "emissions"]
    miss = sorted({s for s in ed if np.isnan(emis_arr[:, :, idx[s]]).any()})
    assert not miss, f"NaN emissions for {miss}"
    f.emissions.loc[dict(scenario=SCEN_KEY)] = emis_arr
    f.forcing.loc[dict(scenario=SCEN_KEY)] = forc_arr
    f.fill_species_configs(str(species_file)); f.override_defaults(str(params))
    f.climate_configs["stochastic_run"][:] = False
    assert bool(np.all(f.climate_configs["stochastic_run"].values == False))
    for sp in prescribed:
        fill(f.forcing, f.forcing.sel(specie=sp) * df_configs[f"forcing_scale[{sp}]"].values.squeeze(), specie=sp)
    initialise(f.concentration, f.species_configs["baseline_concentration"]); initialise(f.forcing, 0)
    initialise(f.temperature, 0); initialise(f.cumulative_emissions, 0); initialise(f.airborne_emissions, 0)
    initialise(f.ocean_heat_content_change, 0)
    f.run(progress=False)
    years = f.timebounds.astype(int)
    pi = (years >= BASELINE_START) & (years <= BASELINE_END)
    graw = f.temperature.sel(layer=0).values[:, 0, :]                     # K rel. the 1750 model start
    gmst = graw - graw[pi, :].mean(axis=0)[None, :]
    ohc = f.ocean_heat_content_change.values[:, 0, :]
    ohc = (ohc - ohc[pi, :].mean(axis=0)[None, :]) / 1e22
    erf = {"total": f.forcing_sum.values[:, 0, :]}                         # W/m2 rel. 1750, NOT re-referenced
    for g, sps in groups.items():
        erf[g] = f.forcing.sel(specie=sps).sum(dim="specie").values[:, 0, :]
    return years, graw, gmst, ohc, erf

def cube_csv(years, arr, path):
    cy = (years >= CUBE_FIRST_YEAR) & (years <= CUBE_LAST_YEAR)
    cube = pd.DataFrame(np.round(arr[cy, :], CUBE_DECIMALS), columns=[f"cfg_{c}" for c in configs])
    cube.insert(0, "year", years[cy]); cube.to_csv(path, index=False)

OUT.mkdir(parents=True, exist_ok=True)
for lab, emis in ARMS.items():
    print(f"== arm {lab}: {emis}", flush=True)
    years, graw, gmst, ohc, erf = run(emis)
    np.savez_compressed(OUT / f"ml_{lab}.npz", years=years, gmst_raw=graw, gmst=gmst, ohc=ohc,
                        configs=np.array(configs), **{f"erf_{k}": v for k, v in erf.items()},
                        provenance=np.array(f"FaIR 2.2.4 (calib {CALIB_VERSION}); vvML; emissions {emis} "
                                            f"(sha256 {hashlib.sha256(open(emis,'rb').read()).hexdigest()[:16]}); "
                                            f"volcanic_solar_ML; stochastic_run=False (no RNG); GMST/OHC rel "
                                            f"{BASELINE_START}-{BASELINE_END}; ERF rel 1750 (FaIR native)"))
    if lab == "live":
        for q, arr in (("gmst", gmst), ("ohc", ohc)):
            p = OUT / f"fair_cube_{q}_vvML_raw.csv"; cube_csv(years, arr, p)
            same = p.read_bytes() == (SHIPPED / f"fair_cube_{q}_vvML_raw.csv").read_bytes()
            print(f"  [IDENTITY] {q} cube vs shipped: {'BYTE-IDENTICAL' if same else 'DIFFERS'}", flush=True)
            if not same: sys.exit("ERROR: the scratch driver does not reproduce production; stop")
print("done")
