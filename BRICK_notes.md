# BRICK Setup and Usage Notes
## For Claude Code — FaIRtoFrEDI project

---

## What BRICK does in this pipeline

BRICK (Building blocks for Relevant Ice and Climate Knowledge) takes FaIR's
global mean surface temperature output and converts it to sea-level rise
projections. In this project:

  FaIR 2.2.4 → GMST trajectory → BRICK → Sea-level rise → (future use in FrEDI SLR sectors)

BRICK is not currently used in the SC-CO2 mortality calculations — that work
uses FrEDI directly with temperature as input. BRICK is for the SLR pipeline.

---

## Installation on this machine

**Location:** `~/repos/BRICK/`
**Source:** `https://github.com/scrim-network/BRICK` (v0.3, older pre-2022 version)

> Note: A newer Julia version (MimiBRICK.jl) exists at
> https://github.com/anthofflab/MimiBRICK.jl — it has better maintained
> calibration and couples more cleanly with modern tools. Worth evaluating
> as an alternative if the Fortran build continues to cause problems.

BRICK is written in **R** (interface + calibration) with **Fortran 90**
physics. The Fortran must be compiled into `.so` dynamic libraries before R
can load them.

---

## Critical build fix for Apple Silicon (M-series Mac)

The standard `make` will fail because the Makefile points to the wrong
gfortran path. The fix:

```bash
# Check where Homebrew gfortran actually is
which gfortran                  # likely /opt/homebrew/bin/gfortran

# Edit the Makefile first line to point to the correct path
cd ~/repos/BRICK/fortran
# Change: F90 = gfortran
# To:     F90 = /opt/homebrew/bin/gfortran

# Then build:
mkdir -p obj          # Makefile does NOT create this automatically — must do manually
make                  # builds all .so files into fortran/
```

**If you get "file header errors" or "wrong architecture" errors:**
The `.so` files are platform-specific (Mac vs Linux). They cannot be shared
across machines or OS versions. Always rebuild locally.

**To rebuild from scratch:**
```bash
cd ~/repos/BRICK/fortran
rm -f *.so *.mod
rm -rf obj/
mkdir -p obj
make
```

**To build only one module (faster for testing):**
```bash
make doeclim.so    # or dais.so, simple.so, gsic_magicc.so, te.so
```

---

## Directory structure

```
~/repos/BRICK/
  calibration/          R scripts for MCMC calibration
  data/                 forcing data and calibration data
  fortran/
    src/                Fortran 90 source files (.f90)
    R/                  R wrapper functions that call the .so libraries
    Makefile            build file (requires gfortran path edit on Mac)
    README              Fortran build instructions
  R/                    R physics models (slower, for testing only)
  output_model/         model output (temperature, SLR) — netCDF
  output_calibration/   MCMC posterior parameter files
```

---

## R packages required

```r
install.packages(c(
  'adaptMCMC', 'compiler', 'DEoptim', 'doParallel',
  'fExtremes', 'fields', 'fMultivar', 'foreach',
  'gplots', 'graphics', 'lhs', 'maps', 'methods',
  'ncdf4', 'plotrix', 'pscl', 'RColorBrewer',
  'sensitivity', 'sn', 'stats'
))
```

Or run the provided installer:
```r
setwd('~/repos/BRICK/calibration')
source('BRICK_install_packages.R')
```

---

## Running BRICK with FaIR temperature input

The key function for this pipeline is passing FaIR's temperature output
directly to BRICK's physical models rather than running BRICK's own climate
model (DOECLIM). BRICK has two modes:

**Mode 1 (default): DOECLIM + sea-level sub-models**
BRICK simulates its own temperature internally using DOECLIM, then drives
sea-level components. NOT what we want — we have FaIR temperatures.

**Mode 2 (for our use): External temperature → sea-level sub-models**
Pass FaIR's GMST directly to the sea-level components:
- SIMPLE (Greenland ice sheet)
- DAIS (Antarctic ice sheet)
- GSIC-MAGICC (glaciers and small ice caps)
- TE (thermal expansion)
- LWS (land water storage — optional)

The R wrapper files in `fortran/R/` load the compiled `.so` files. Example
of calling SIMPLE directly:

```r
# Load the compiled Fortran library
dyn.load('~/repos/BRICK/fortran/simple.so')

# Source the R wrapper
source('~/repos/BRICK/fortran/R/brick_te.R')
source('~/repos/BRICK/fortran/R/brick_simple.R')

# Pass FaIR temperature vector to the Greenland ice sheet model
# temp_fair = vector of GMST anomalies (°C above 1850-1900) from FaIR
result_gis <- simple(
  tstep   = 1,
  b0      = param_b0,       # SIMPLE calibrated parameters
  b1      = param_b1,
  b2      = param_b2,
  b3      = param_b3,
  alphais = param_alpha,
  Tg      = temp_fair       # <-- FaIR temperature input
)
```

The exact parameter names depend on which calibration file you use.
The pre-calibrated parameter files from the Wong et al. 2017 paper are
available from: https://download.scrim.psu.edu/Wong_etal_BRICK/

---

## Calibrated parameter files

BRICK's sea-level sub-models have calibrated parameters from MCMC fits to
observational data. These are large files not stored in the GitHub repo.

**Pre-calibrated (Wong et al. 2017):**
```bash
cd ~/repos/BRICK/output_model
curl -O https://download.scrim.psu.edu/Wong_etal_BRICK/BRICK-model_physical_control_02Apr2017.nc
```

This netCDF file contains projections for RCP 2.6, 4.5, and 8.5.

**To use existing projections without recalibrating:**
```r
library(ncdf4)
ncdata <- nc_open('output_model/BRICK-model_physical_control_02Apr2017.nc')
slr.gsic <- ncvar_get(ncdata, 'GSIC_RCP45')
slr.gis  <- ncvar_get(ncdata, 'GIS_RCP45')
slr.ais  <- ncvar_get(ncdata, 'AIS_RCP45')
slr.te   <- ncvar_get(ncdata, 'TE_RCP45')
slr.lws  <- ncvar_get(ncdata, 'LWS_RCP45')
t.proj   <- ncvar_get(ncdata, 'time_proj')
nc_close(ncdata)
```

---

## Local sea-level projection

To project sea level at a specific location (fingerprinting):

```r
setwd('~/repos/BRICK/R')
source('BRICK_LSL.R')

lsl <- brick_lsl(
  lat.in   = 40.7128,   # New York City
  lon.in   = -74.0060,
  n.time   = length(t.proj),
  slr_gis  = slr.gis,
  slr_gsic = slr.gsic,
  slr_ais  = slr.ais,
  slr_te   = slr.te,
  slr_lws  = slr.lws
)
# lsl is a matrix: (n.years × n.ensemble)
```

---

## Integration with FaIR: what needs to be built

The FaIR → BRICK pipeline is **not yet fully implemented** in this project.
The plan is:

1. FaIR outputs: `temp_pulse_baseline.csv` and `temp_pulse_1Gt_2030.csv`
   (already done — these are GMST relative to 1850-1900)

2. BRICK input: needs GMST in the same reference period (1850-1900 ✓)
   BUT: BRICK's calibration uses a different scenario structure than SSP2-4.5.
   Check whether the DAIS parameters are valid for the temperature range
   we're passing from FaIR.

3. Key question: should we use BRICK's pre-calibrated parameters (from
   RCP4.5) with our FaIR SSP2-4.5 temperatures? SSP2-4.5 ≈ RCP4.5 so this
   is probably fine as a first pass.

4. Output needed: global mean SLR trajectory to pass to FrEDI's SLR sector
   (`aggLevels` for SLR sectors uses `slr` model type, not `gcm`)

---

## Known issues and gotchas

1. **The .so files will NOT run on a different OS or architecture.** Always
   build on the target machine. Do not commit .so files to git.

2. **`mkdir -p obj` must be run manually.** The Makefile does not create
   the obj/ directory. Build will silently fail or give cryptic errors
   without it.

3. **gfortran path must match exactly.** On Apple Silicon with Homebrew:
   `/opt/homebrew/bin/gfortran`. On Intel Mac: `/usr/local/bin/gfortran`.

4. **DAIS calibration takes ~12 hours.** If you need to recalibrate from
   scratch, budget significant time. Use the pre-calibrated files for now.

5. **BRICK v0.3 vs MimiBRICK.jl:** The scrim-network version is older and
   not actively maintained. MimiBRICK.jl (Julia) is the current version and
   has better documentation. If starting fresh, consider MimiBRICK.

6. **netCDF output:** BRICK writes projections to netCDF. Requires the
   `ncdf4` R package and the netCDF system library (`brew install netcdf`).

---

## Quick build check

To verify BRICK is working correctly after a build:

```bash
cd ~/repos/BRICK/fortran
ls *.so   # should show: doeclim.so, simple.so, dais.so, gsic_magicc.so, te.so
```

Then in R:
```r
dyn.load('~/repos/BRICK/fortran/doeclim.so')
# If no error: the library loaded successfully
```

---

## Contact / citation

Tony E. Wong (tony.wong@rit.edu)
Wong et al. (2017), Geoscientific Model Development, 10: 2741-2760.
doi: 10.5194/gmd-10-2741-2017
