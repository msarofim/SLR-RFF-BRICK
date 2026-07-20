# Handoff — FACTS sea-level framework: install scoping (for a mid-July 2026 pickup)

**Date scoped:** 2026-06-21
**Status:** DEFERRED by Marcus to ~mid-July 2026 (after Alaska) — deliberately, so the
build uses whatever is latest on `master` then (repo is actively moving; pins were
recently refreshed). This note is the cold-start spec; re-verify the live files before acting.

## Goal
Stand up FACTS (radical-collaboration/facts) locally to compare its **global mean SLR (GMSL)**
projections against our **MAGICC** and **BRICK** SLR work (sibling to the existing
MAGICC-comparison study — see memory `project_magicc_comparison`).

## Headline feasibility finding
- **FACTS does NOT run natively on macOS.** Docs (quickstart.rst) state plainly: *"The RADICAL
  toolkit does not support MacOS or Windows. Therefore, to run on a Mac… you need to run within
  a Linux virtual machine or container."* → On this M4 Mac the only supported path is the shipped
  **Docker container** (`facts/docker/`).
- **Likely builds NATIVE arm64 on the M4** (good — no x86 emulation). Dockerfile is
  `FROM ubuntu:noble`, installs everything via apt + pip wheels + in-container `gfortran`/`cmake`;
  no x86-only binaries. Residual risk = a science module shipping precompiled/arch-sensitive code,
  but the image carries a Fortran toolchain so modules compile in-container. Confirm on first real run.

## Machine state (2026-06-21)
- macOS 26.5.1, Apple **M4**, 10 cores, **16 GB RAM**, **503 GB free** disk.
- **Docker NOT installed** (the one real host prerequisite). Homebrew + gfortran present (host gfortran
  irrelevant — build happens in-container). Host Python 3.14 / no conda — irrelevant (container has own venv).
- 16 GB RAM is fine for **global-only** GMSL runs; full local/regional CMIP runs are memory-hungry — avoid.

## "FACTS 2.0" naming
No `v2.0` git tag exists — published tags top out at **v1.1.4**. "2.0" ≈ current **`master`**
(modernized: RADICAL 1.92, Ubuntu Noble, numpy 2, Docker workflow) + the `module/emulandice2`
branch (2nd-gen ice-sheet emulator). Default to `master`. Re-check tags in mid-July in case a real
2.x release lands.

## Install sequence (Docker route) — re-verify each step against live repo first
```bash
# 1. Install Docker Desktop for Mac (Apple Silicon):  brew install --cask docker   (then launch it once)
# 2. Clone
git clone https://github.com/radical-collaboration/facts.git
# 3. Download ONLY global modules (NOT the full ~60 GB / 29-file set)
wget -P facts/modules-data -i facts/modules-data/modules-data.global_only.urls.txt
# 4. Build container (native arm64)
cd facts/docker && sh develop.sh        # builds images: facts-core, facts-jupyter
# 5. Validate engine with dummy experiment
docker run -it --volume=$HOME/facts:/opt/facts -w /opt/facts facts \
  python3 runFACTS.py experiments/dummy
# (Jupyter variant: ... -p 8888:8888 facts-jupyter jupyter lab --ip=0.0.0.0 --port=8888)
```

## Data sizing
- Full module data = **~60 GB, 29 files**, split across two Zenodo entries
  (10.5281/zenodo.7478191 + .7478447).
- **`modules-data.global_only.urls.txt` = 12 files** — the right subset for GMSL-vs-BRICK/MAGICC.
  Contents map directly onto BRICK components:
  `fair_temperature` (FaIR driver), `ipccar5_glaciers` (GSIC), ice sheets
  (`FittedISMIP`, `bamber19`, `deconto21_AIS`, `larmip`) (AIS/GIS), `ssp_landwaterstorage` (LWS),
  `tlm_sterodynamics` (thermal expansion / ocean dynamics, ≈ BRICK TE).
- Sandbox: each run copies inputs to `~/radical.pilot.sandbox` (inside container by default;
  can mount out). Watch its size.

## Why the comparison is clean
FACTS's global pipeline is **driven by a FaIR temperature module** and decomposes GMSL into the
same physical components as BRICK. → can drive FACTS with the **same FaIR temperature ensemble**
we feed BRICK = apples-to-apples, and FACTS additionally gives the full *structural*-uncertainty
fan (multiple competing ice-sheet modules) that BRICK's single emulator lacks. Natural 3rd leg to
the MAGICC-native vs FaIR→BRICK-Mengel comparison.

## Open work for the mid-July session (in priority order)
1. **Re-pull live repo** (Dockerfile, quickstart.rst, `modules-data.global_only.urls.txt`, tags) —
   pins/paths may have changed. This note's commands are 2026-06-21 snapshots.
2. Install Docker Desktop → build → pass `experiments/dummy`. (~1–2 hrs hands-on; risk is in the
   science modules running on arm64, not the install.)
3. **FaIR-coupling scoping** (the real research step, not yet investigated): how a FACTS experiment
   `config.yml` ingests an *external* FaIR temperature ensemble instead of its bundled FaIR module.
   `runFACTS.py --shellscript experiments/<onemodule>` runs a single module outside EnTK — use for
   debugging the coupling. Start from an `experiments/coupling.ssp585/config.yml` template.
4. Run a global SSP2-4.5 / SSP5-8.5 ensemble; line up @2100 GMSL vs our MAGICC-native (53 cm SSP2-4.5)
   and FaIR→BRICK-Mengel (78 cm) numbers from `project_magicc_comparison`.

## Source-doc pointers
- Docs: https://fact-sealevel.readthedocs.io  | Repo: https://github.com/radical-collaboration/facts
- Model paper: Kopp et al. 2023, GMD 16, 7461–7489 (doi:10.5194/gmd-16-7461-2023)
- Key files inspected: `docker/Dockerfile`, `docker/develop.sh`, `docs/source/quickstart.rst`,
  `modules-data/modules-data.global_only.urls.txt`, `facts_requirments.txt`, `environment.yml`.
