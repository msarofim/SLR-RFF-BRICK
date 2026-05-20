# Zenodo deposit setup — instructions for the maintainer

This document is for the repo maintainer (Marcus) to create the Zenodo
deposit that backs `scripts/download_data.sh`. Run through these steps
once, get the DOI, and update `scripts/download_data.sh` accordingly.

## 1. Files to upload (~6 GB total)

These all live in `outputs/` on the local machine and Torch
(`/scratch/ms17839/SLR-RFF-BRICK/outputs/`). They are gitignored
deliberately so they live on Zenodo rather than in git.

### Cubes (Torch — rsync down first)

| Filename | Size | What it is |
|---|---|---|
| `rff_baseline_stoch_to2300.npz` | 1.9 GB | FaIR production baseline cube (490 RFFs × 841 cfgs × 451 yr) |
| `rff_pulse_stoch_to2300.npz` | 1.9 GB | Paired +1 GtC pulse at 2030 |
| `rff_pulse0p01gtc_stoch_to2300.npz` | 1.9 GB | Paired +0.01 GtC small-pulse |

### Cubes (local — substack-side analyses)

| Filename | Size | What it is |
|---|---|---|
| `lhs_pilot_gmst_full_N200_to2300.npz` | ~175 MB | 398-RFF deterministic GMST cube used by substack exceedance + obs-overlay figures |
| `lhs_pilot_gmst_full_stoch_test_ohc4.npz` | ~? MB | 4-D stochastic GMST cube used for internal-variability term in updated_hawkins_sutton + obs-overlay band widening |

### Weighted ensembles (local — LHS-10k pipeline outputs)

| Filename | Size | What it is |
|---|---|---|
| `brick_lhs10k_baseline_to2300_weighted.csv` | ~80 MB | LHS-10k baseline BRICK + Wong weights |
| `brick_lhs10k_pulse_to2300_weighted.csv` | ~80 MB | Paired +1 GtC arm |
| `brick_lhs10k_pulse0p01gtc_to2300_weighted.csv` | ~80 MB | Paired +0.01 GtC arm |

### ANOVA factorial CSVs (Torch — rsync down first)

| Filename | Size | What it is |
|---|---|---|
| `brick_anova_long_2300_weighted.csv` | ~50 MB | 13,500-tuple ANOVA factorial baseline + Wong weights (Panel C input) |
| `brick_anova_pulse_long_2300.csv` | ~50 MB | Paired ANOVA pulse arm (Panel D input) |
| `brick_anova_marginal_long_2300_weighted.csv` | ~80 MB | Per-tuple pulse-baseline marginal CSV |

### Supporting CSVs

| Filename | Size | What it is |
|---|---|---|
| `brick_lB_per_post_dangendorf.csv` | 230 KB | Pre-computed l_B per BRICK posterior member (Wong-weight numerator) |

## 2. Create the deposit

1. Go to [https://zenodo.org/deposit/new](https://zenodo.org/deposit/new).
2. Upload all files listed above. (Drag-drop is fine for files up to 50 GB
   per record.)
3. Fill in metadata using the template below.
4. **Publish** (this mints the DOI). Note: Zenodo DOIs are permanent —
   once published, the deposit cannot be deleted, only superseded with
   a new version that shares a "concept DOI."

## 3. Metadata template

Copy these fields into the Zenodo metadata form:

- **Resource type:** Dataset
- **Title:** `SLR-RFF-BRICK intermediate data v1.0`
- **Creators:** `Sarofim, Marcus` (affiliation: NYU Marron Institute of Urban Management / Johns Hopkins EPCP)
- **Description:**
  > Intermediate-data deposit for the SLR-RFF-BRICK reproducible pipeline
  > (github.com/msarofim/SLR-RFF-BRICK). Contains the FaIR v2.2.4 GMST + OHC
  > cubes (baseline, +1 GtCO₂ pulse at 2030, +0.01 GtCO₂ small-pulse), the
  > LHS-10k conditional-BRICK Wong-weighted ensembles (10,000 triplets,
  > ESS = 7,037 effective sample size), and the 13,500-row balanced ANOVA
  > factorial CSVs that drive the 4-way Hawkins-Sutton variance
  > decompositions. These are too large to host in git but are required
  > for full Tier 2 reproducibility of the project's figures.
- **Keywords:** `sea-level rise; probabilistic projections; social cost of carbon; FaIR; MimiBRICK; RFF-SP; Hawkins-Sutton decomposition; climate uncertainty`
- **Version:** `1.0`
- **License:** `CC-BY-4.0` (allow derivatives + commercial use with attribution)
- **Publication date:** today
- **Related identifiers:**
  - Type: `Is supplement to` — `https://github.com/msarofim/SLR-RFF-BRICK`
  - Type: `Is derived from` — DOI `10.1038/s41586-022-05224-9` (Rennert et al. 2022, RFF-SP)
  - Type: `Is derived from` — DOI `10.5194/gmd-17-8569-2024` (Smith et al. 2024, FaIR v1.4.1 calibration)
- **Communities:** consider adding to `Open Climate Data` (zenodo community), if available
- **Funding / grants:** (whatever is appropriate)

## 4. After publication

1. Note the DOI (format: `10.5281/zenodo.XXXXXXX`) and the numeric record ID.
2. Update `scripts/download_data.sh`:
   ```bash
   ZENODO_DOI="10.5281/zenodo.XXXXXXX"
   ZENODO_RECORD_ID="XXXXXXX"
   ```
3. Test the download in a clean directory:
   ```bash
   cd /tmp && git clone /path/to/SLR-RFF-BRICK test-clone && cd test-clone
   bash scripts/download_data.sh
   python python/scripts/poster/slr_band.py   # should now succeed
   ```
4. Commit the updated download script + tag the GitHub release.

## 5. About the repo's own Zenodo DOI

`.zenodo.json` in the repo root is metadata for an *automatically-deposited*
Zenodo DOI of the GitHub repo itself, separate from this intermediate-data
deposit. To enable:

1. Log in to Zenodo with your GitHub account.
2. On the [GitHub-Zenodo integration page](https://zenodo.org/account/settings/github/),
   toggle the SLR-RFF-BRICK repo to "on."
3. Tag the repo (e.g. `git tag v1.0 && git push origin v1.0`) — Zenodo
   auto-creates a snapshot deposit with a DOI for the code itself.

The two Zenodo DOIs (code repo + intermediate data) reference each other
via `related_identifiers` so future readers can find both.
