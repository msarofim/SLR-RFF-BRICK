# SLR-RFF-BRICK

Probabilistic sea-level rise from RFF-SP × FaIR × MimiBRICK.

This repository contains the reproducible pipeline coupling Resources for the
Future's RFF-SP probabilistic socio-economic / emissions ensemble (Rennert
et al. 2022) with the FaIR v2.2.4 reduced-complexity climate model (using
the FaIR-calibrate v1.4.1 posterior of Smith et al. 2024) and MimiBRICK,
importance-weighted against observed historical GMSL via the Wong (2026)
AR(1) likelihood. Outputs include probabilistic projections of GMST and
GMSL through 2300, Hawkins-Sutton variance decomposition by uncertainty
source, and pulse-marginal climate responses for social-cost-of-GHG use.

The headline final ensemble is the **LHS-10k conditional-BRICK design**:
10,000 Latin-Hypercube-sampled (RFF, FaIR cfg, BRICK posterior) triplets,
Wong-weighted to give an effective sample size of 7,037.

A direct intellectual companion is **Darnell et al. 2025** (*Nat Clim Change*
15:1205–1211, [doi:10.1038/s41558-025-02457-0](https://doi.org/10.1038/s41558-025-02457-0)),
who decompose total-SLR uncertainty across emissions vs geophysical sources
at the multi-century horizon.

## Quick start

```bash
git clone https://github.com/msarofim/SLR-RFF-BRICK.git
cd SLR-RFF-BRICK
conda env create -f environment.yml
conda activate slr-rff-brick
```

The final figures are committed as PNGs/PDFs under `outputs/substack/` and
`outputs/poster/` — open them directly. To regenerate them:

**Tier 1 — these figures regenerate from CSVs already in the repo** (no
external download):

```bash
python python/scripts/substack/pulse_hawkins_sutton.py
python python/scripts/substack/pulse_responses_clean.py
python python/scripts/substack/updated_hawkins_sutton_slr.py
python python/scripts/substack/pulse_convergence.py
python python/scripts/poster/layout_mockup.py
```

**Tier 2 — these figures need the Zenodo data download** (GMST cube and/or
the LHS-10k baseline weighted CSV, ~6 GB total):

```bash
bash scripts/download_data.sh
python python/scripts/substack/obs_overlay.py
python python/scripts/substack/obs_overlay_slr.py
python python/scripts/substack/obs_overlay_recent.py
python python/scripts/substack/exceedance_table.py
python python/scripts/substack/exceedance_crossing_year.py
python python/scripts/substack/median_crossing_year.py
python python/scripts/substack/updated_hawkins_sutton.py
python python/scripts/poster/slr_band.py
```

The committed CSVs in `outputs/plots/` and `outputs/substack/` carry
every figure-input *summary* (variance decomposition, pulse-marginal,
exceedance summary); the gitignored large files (FaIR cubes, LHS-10k
weighted ensembles) are needed only by figures that bin / quantile from
the per-trajectory ensemble directly.

## Reproducibility tiers

| Tier | What you get | Extra setup | Compute |
|---|---|---|---|
| **1. Variance / pulse figures** | Regenerate the variance-decomposition + pulse-marginal substack/poster figures from committed CSVs | — | laptop, ~2 min |
| **2. Cube + ensemble figures** | Tier 1 + all GMST-cube-based and SLR-band figures regenerated from raw ensembles | `bash scripts/download_data.sh` (~6 GB Zenodo) | laptop, ~10 min |
| **3. Re-run BRICK from cubes** | Regenerate the LHS-10k weighted ensembles from FaIR cubes; H-S decompositions; pulse marginals | Tier 2 + MimiBRICK posterior CSV + Julia env | NYU Torch HPC, ~10 min wall |
| **4. Re-run FaIR from emissions** | Regenerate the FaIR cubes from RFF-SP emissions | Tier 3 + RFF-SP 7-Zip (~1.4 GB, Zenodo 6016583) | NYU Torch HPC, ~few hours |

See [METHODS.md](METHODS.md) for the technical pipeline description.

## Repository layout

```
SLR-RFF-BRICK/
├── README.md              you are here
├── METHODS.md             methods writeup (sampling, weighting, anchors, decompositions)
├── LICENSE                MIT
├── CITATION.cff           machine-readable citation
├── .zenodo.json           metadata for the repo's Zenodo DOI (auto-deposited on tagged release)
├── environment.yml        conda env (recommended)
├── requirements.txt       pip-only fallback
├── scripts/
│   └── download_data.sh   fetch Tier 2 intermediates from Zenodo
├── python/                Python modules and entry-point scripts (see python/scripts/)
├── julia/                 BRICK Julia driver + lockfile
├── slurm/                 NYU Torch HPC submit scripts
├── data/
│   ├── README.md          inventory; pointers to external sources
│   ├── observations/      small obs CSVs (Dangendorf, NOAA STAR, IGCC, BE) [tracked]
│   ├── MimiBRICK/         placeholder; fetch posterior CSV separately
│   ├── RFF-SP-emissions/         [gitignored — Zenodo 6016583]
│   └── RFF-SP-socioeconomics/    [gitignored — Zenodo 6016583]
├── outputs/
│   ├── README.md          inventory; what's tracked vs Zenodo
│   ├── plots/             H-S decomp CSVs + obs-vs-model CSVs + final panel PNGs
│   ├── substack/          figure-input summary CSVs + final substack figures
│   └── poster/            final poster panel figures + layout mockup
├── notes/                 working handoff notes (decision history, methods drafts)
├── docs/                  supplementary technical docs
└── BRICK_notes.md         project-specific BRICK notes
```

## Tier 3 quickstart (re-run BRICK from FaIR cubes)

```bash
# 1. Download intermediate data (~6 GB) from Zenodo
bash scripts/download_data.sh

# 2. Place the MimiBRICK posterior subsample (see data/MimiBRICK/README.md)
cp /path/to/parameters_subsample_brick.csv data/MimiBRICK/

# 3. Push to Torch and run the BRICK pipeline
rsync -avz --exclude='.git' . torch:/scratch/$USER/SLR-RFF-BRICK/
ssh torch "cd /scratch/$USER/SLR-RFF-BRICK && sbatch slurm/submit_lhs10k_brick_pipeline.sh"

# 4. Pull weighted CSVs back, regenerate figures
rsync -avz torch:/scratch/$USER/SLR-RFF-BRICK/outputs/brick_lhs10k_*_weighted.csv outputs/
python python/scripts/poster/slr_band.py
```

## Tier 4 quickstart (re-run FaIR from RFF-SP emissions)

```bash
# 1. Download RFF-SP socio-economic + emissions ensemble
# https://zenodo.org/records/6016583  ->  rffsps_v5.7z  (~1.4 GB)
7z x rffsps_v5.7z -odata/

# 2. Generate the production FaIR cube on Torch (FaIR is fast but the
#    paired production cube is hours of CPU)
ssh torch "cd /scratch/$USER/SLR-RFF-BRICK && sbatch slurm/submit_lhs_fair.sh"
# Repeat with submit_small_pulse_fair.sh for the +0.01 GtC pulse companion.

# 3. From there, Tier 2 / Tier 1 as above.
```

## Citation

If you use this code or its outputs, please cite the repository ([CITATION.cff](CITATION.cff))
plus the underlying methods papers:

- Rennert et al. 2022 (RFF-SP): [doi:10.1038/s41586-022-05224-9](https://doi.org/10.1038/s41586-022-05224-9)
- Smith et al. 2024 (FaIR-calibrate v1.4.1): [doi:10.5194/gmd-17-8569-2024](https://doi.org/10.5194/gmd-17-8569-2024)
- Wong 2026 (importance weighting): [doi:10.48550/arXiv.2604.13446](https://doi.org/10.48550/arXiv.2604.13446)
- Darnell et al. 2025 (SLR uncertainty decomposition companion): [doi:10.1038/s41558-025-02457-0](https://doi.org/10.1038/s41558-025-02457-0)
- Sweet et al. 2022 (SLR scenarios + damage-function calibration nodes): [NOAA Tech Rep NOS 01](https://oceanservice.noaa.gov/hazards/sealevelrise/sealevelrise-tech-report.html)

## Contact

Marcus Sarofim &nbsp;·&nbsp; msarofim@gmail.com
NYU Marron Institute of Urban Management / Johns Hopkins EPCP

## License

MIT — see [LICENSE](LICENSE).
