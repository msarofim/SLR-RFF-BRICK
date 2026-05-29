# Zenodo deposit setup — instructions for the maintainer

This document walks through the two Zenodo deposits associated with this
project:

1. **Intermediate data deposit** — concept DOI `10.5281/zenodo.20312324`
   (NB: `20312325` is the *v1.0 version* DOI, not the concept; v2.1 version
   DOI is `10.5281/zenodo.20451296`), originally minted with the v1.4.1-era
   data (Sept 2025). For the v1.4.5
   pipeline this needs a **new version** (same concept DOI; new version
   DOI). See §§ 1–4 below.
2. **Code repo deposit** — auto-deposited via the GitHub–Zenodo
   integration when a tag is pushed. Not yet created. See § 5 below.

Run through both once for the v1.4.5 update; the data deposit takes most
of the effort.

> **Automated path (preferred, 2026-05-29):** the data-deposit new-version
> workflow in §§ 1–2 is now scripted by `scripts/zenodo_deposit_refresh.py`
> (Zenodo REST API). It stages the manifest (incl. an rsync of the Torch
> cubes), creates the new-version draft, replaces the inherited files,
> uploads, and sets metadata — stopping at the **draft** for manual review
> before you publish. Needs a Zenodo token in `~/.zenodo_token` (scopes
> `deposit:write` + `deposit:actions`). Use `--dry-run` first. The manual
> web steps below remain valid as a fallback / reference.
>
> **v2.1 manifest (what the script actually deposits, ~2.5 GB):** the v2.0
> selection below **plus** the v5 LHS-10k_s noise-isolated ensemble
> (`cube_v145_lhs10ks_{baseline,pulse_co2_pos_001gt}_flat2015.npz` +
> `brick_lhs10ks_{baseline_weighted,pulse_co2_pos_001gt}_to2300.csv`, which
> drive the canonical Group-Sobol H-S figures) and the 324k balanced-factorial
> ANOVA design metadata (`anova324k_{brick,fair}_metadata.csv`) for the
> model-free cross-check. The raw 324k per-cell BRICK output (~2.8 GB) stays
> excluded (regenerable from that metadata + the BRICK driver).

## 1. Files to upload to the data deposit — v1.4.5 default selection (~2.5 GB total)

These all live in `outputs/` on the local machine and Torch
(`/scratch/ms17839/SLR-RFF-BRICK/outputs/` and
`/scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145/`). They are
gitignored deliberately so they live on Zenodo rather than in git.

### FaIR v1.4.5 cubes (Torch — rsync down first; ~1.5 GB total)

The 18-cube v1.4.5 inventory: 9 LHS-10k + 9 ANOVA-18k arms, each a
baseline + 8 pulse arms (±1 GtCO₂, ±0.01 GtCO₂, ±1 Tg CH₄, ±0.01 Tg CH₄).

```
rsync -avz --progress \
  torch:/scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_*.npz \
  outputs/cubes_v145/
```

| Family | Files | Each | Total |
|---|---|---|---|
| LHS-10k | `cube_v145_lhs10k_{baseline,pulse_*}.npz` (9 cubes) | ~50 MB | ~450 MB |
| ANOVA-18k | `cube_v145_anova18k_{baseline,pulse_*}.npz` (9 cubes) | ~120 MB | ~1.1 GB |

The cubes carry `cells_meta` (n_cells × 3 = rff/cfg/seed indices), `years`
(1850–2300), `gmst_traj` (n_cells × n_year Float32), `ohc_traj`, and
`erf_2100`. Schema is the flat per-cell layout introduced for the
v1.4.5 pipeline.

### v1.4.5 BRICK slim CSVs (local — `outputs/brick_v145_slim/`; ~240 MB total)

Keys + `w_norm` + bare-year SLR columns for each cube arm; the legacy
slim-schema downstream plot scripts read these directly.

| Family | Files | Each | Total |
|---|---|---|---|
| LHS-10k baseline + 3 pulse arms | `brick_lhs10k_{baseline,pulse_co2_pos_001gt,pulse_co2_pos_1gt,pulse_ch4_pos_001tg}_to2300{,_weighted}.csv` | 30 MB | ~120 MB |
| ANOVA-18k baseline + 1 pulse arm + marginal | `brick_anova18k_{baseline_weighted,pulse_co2_pos_1gt,marginal_co2_pos_1gt_weighted}_to2300.csv` | 40 MB | ~120 MB |

### v1.4.5 small summary CSVs (~1 MB total)

Final figure inputs; small.

| Path | Size | What it is |
|---|---|---|
| `outputs/substack/co2_pulse_slr_summary_lhs10k_0p01gtc.csv` | 20 KB | per-GtCO₂ small-pulse SLR envelope (year, mean, p5/p50/p95) |
| `outputs/substack/co2_pulse_gmst_summary_v145.csv` | 16 KB | per-GtCO₂ pulse GMST envelope from LHS-10k |
| `outputs/substack/ch4_pulse_slr_summary_lhs10k_0p01tg.csv` | 20 KB | per-Tg CH4 small-pulse SLR envelope |
| `outputs/substack/ch4_pulse_gmst_summary_v145.csv` | 16 KB | per-Tg CH4 pulse GMST envelope |
| `outputs/substack/brick_vs_grinsted_tsls_components.csv` | 2 KB | TSLS components vs Grinsted 2022 reference table |
| `outputs/plots/hawkins_sutton_slr_4way.csv` | 60 KB | Total-SLR 4-way variance decomposition (Panel C) |
| `outputs/plots/hawkins_sutton_slr_4way_pulse.csv` | 60 KB | Pulse-SLR 4-way variance decomposition (Panel D) |
| `outputs/plots/hawkins_sutton_gmst_3way_pulse_v145.csv` | 25 KB | CO₂ pulse-GMST 3-way variance decomposition |

### v1.4.5 FrEDI phaseC inputs + national output (~80 MB total)

Drives Panels F and H. The state-level long CSV (1.5 GB) is **excluded** —
regenerable from the national long + input CSVs by re-running the R
driver with `aggLevels = c("state", "modelaverage", "impactyear")`.

| Path | Size | What it is |
|---|---|---|
| `outputs/fredi_input_rff_baseline_gmst_v145.csv` | 5.4 MB | Per-draw GMST input (1000 SIR-resampled cells) |
| `outputs/fredi_input_rff_baseline_slr_v145.csv` | 5.3 MB | Per-draw SLR input (paired with above) |
| `outputs/fredi_slr_phaseC_rff_baseline_v145_long.csv` | 67 MB | National long-format FrEDI output |
| `outputs/fredi_slr_phaseC_rff_baseline_v145_quantiles.csv` | 116 KB | Per-sector quantiles aggregate |

### Wong-pipeline supporting CSVs (~250 KB)

| Path | Size | What it is |
|---|---|---|
| `outputs/brick_lB_per_post_dangendorf_postpr93.csv` | 230 KB | Pre-computed l_B per BRICK posterior member (Wong-weight numerator), against Dangendorf 2024 obs, post-PR#93 BRICK posterior |

### Files explicitly **excluded** from the default deposit

| Path | Size | Why excluded |
|---|---|---|
| `outputs/brick_v145/brick_lhs10k_{baseline,pulse_co2_pos_001gt}.csv` | 485 MB each, ~1 GB total | Full per-cell BRICK driver outputs with all 5 component trajectories. Regenerable from cubes + the Julia driver; only needed for component-level diagnostics like brick_vs_grinsted_tsls_components.py. |
| `outputs/fredi_slr_phaseC_rff_baseline_v145_state_long.csv` | 1.5 GB | State-level FrEDI output. Regenerable from national long. |
| Legacy v1.4.1-era CSVs (in `outputs/quarantine/20260524_pre_v145_e2e/`) | varies | Superseded by v1.4.5; archived locally only. |

A separate "v1.4.1 archive" can be made in the future if anyone wants
to download the pre-v1.4.5 ensembles; the previous Zenodo version
(`10.5281/zenodo.20312325` v1.0) is still resolvable for that purpose.

## 2. Create the v1.4.5 version of the data deposit

The existing concept DOI is `10.5281/zenodo.20312324` (the v1.0 version DOI
was `10.5281/zenodo.20312325`). Adding a new version preserves the concept
DOI while minting a fresh version DOI.

1. Go to <https://zenodo.org/records/20312325> (the v1.0 deposit page)
   and click **New version** in the top-right action menu.
2. Replace the file inventory with the v1.4.5 selection from § 1.
3. Update the metadata per § 3.
4. Bump the version to `2.0` (semantic-versioned to match the v1.4.5
   pipeline shift).
5. **Publish.** The concept DOI stays `10.5281/zenodo.20312324`; the
   new version DOI looks like `10.5281/zenodo.<new7digits>` (v2.1 = 20451296).

## 3. Metadata template (v1.4.5)

Copy these fields into the Zenodo metadata form for the new version:

- **Resource type:** Dataset
- **Title:** `SLR-RFF-BRICK intermediate data v2.0 (FaIR v1.4.5 + post-PR#93 BRICK)`
- **Creators:** `Sarofim, Marcus` (NYU Marron Institute of Urban Management / Johns Hopkins EPCP)
- **Description:**
  > Intermediate-data deposit v2.0 for the SLR-RFF-BRICK reproducible
  > pipeline (github.com/msarofim/SLR-RFF-BRICK). This version supersedes
  > v1.0 (2025-09; v1.4.1 FaIR + pre-PR#93 BRICK; 500-cell paired
  > ensemble). v2.0 covers the v1.4.5 FaIR-calibration update + Wong et
  > al. 2026 post-PR#93 BRICK posterior, with two new ensemble designs:
  > the LHS-10k conditional-BRICK ensemble (10,000 Latin-Hypercube
  > triplets, Wong-importance-weighted ESS = 3,815 / 10,000 = 38.1%)
  > for headline projection bands and pulse-marginal sensitivities, and
  > the 54,000-row balanced ANOVA-18k factorial (400 RFF × 15 cfg × 3
  > seed × 3 BRICK posterior) for 4-way Hawkins-Sutton variance
  > decomposition. Includes the upstream FaIR v1.4.5 GMST + OHC cubes
  > (Torch-built; flat per-cell schema), the BRICK slim CSVs that drive
  > all substack/poster plots, the small per-figure summary CSVs, and
  > the 1000-cell SIR-resampled FrEDI phaseC coastal-damage inputs +
  > national long output (Panels F/H source).
- **Keywords:** `sea-level rise; probabilistic projections; social cost of carbon; FaIR; MimiBRICK; RFF-SP; Hawkins-Sutton decomposition; climate uncertainty; AIS tipping; v1.4.5 calibration`
- **Version:** `2.0`
- **License:** `CC-BY-4.0`
- **Publication date:** today
- **Related identifiers:**
  - Type: `Is supplement to` — `https://github.com/msarofim/SLR-RFF-BRICK`
  - Type: `Is new version of` — DOI `10.5281/zenodo.20312325` (v1.0, v1.4.1-era)
  - Type: `Is derived from` — DOI `10.1038/s41586-022-05224-9` (Rennert et al. 2022, RFF-SP)
  - Type: `Is derived from` — DOI `10.5194/gmd-17-8569-2024` (Smith et al. 2024, FaIR-calibrate v1.4.1; we use the v1.4.5 update of the same framework)
  - Type: `References` — DOI `10.1038/s41558-025-02457-0` (Darnell et al. 2025, SLR uncertainty companion)
  - Type: `References` — DOI `10.1029/2022EF002696` (Grinsted et al. 2022, CMIP6 TSLS — compared in the substack)
- **Communities:** keep whatever was set on v1.0

## 4. After publication

1. Note the new version DOI (format `10.5281/zenodo.<NEW>`).
2. Update three places in the repo:
   - `README.md` — update the line about intermediate data
   - `outputs/poster/iec_graphics_handoff/README.md` — same
   - `outputs/poster/iec_graphics_handoff/poster_text.txt` — section "ACKNOWLEDGEMENTS" near line 277
3. The poster's bottom-right data-availability block prints the **v2.1
   version DOI** `10.5281/zenodo.20451296` (decision 2026-05-29: pin to the
   exact data behind this poster, not the auto-latest concept DOI
   `10.5281/zenodo.20312324`). The printed DOI MUST be bumped if a future
   poster uses a newer data version.

## 5. Code repo Zenodo deposit (first time)

`.zenodo.json` in the repo root carries the metadata for an
auto-deposited Zenodo DOI of the GitHub repo itself, separate from the
intermediate-data deposit above. To enable:

1. Log in to Zenodo with your GitHub account.
2. On the [GitHub–Zenodo integration page](https://zenodo.org/account/settings/github/),
   toggle the SLR-RFF-BRICK repo to "on."
3. Tag and push: `git tag -a v2.0-poster-agu-chapman -m "..." && git push origin v2.0-poster-agu-chapman`
4. Zenodo auto-creates the snapshot deposit with a DOI matching the
   `.zenodo.json` metadata. The concept DOI for the code repo is
   minted on the first tag; subsequent tags add new versions under it.

The two Zenodo DOIs (code repo + intermediate data) reference each
other via `related_identifiers` so future readers can find both.

## 6. Timing notes — AGU Chapman SLR poster

The poster's QR code resolves to the GitHub URL
<https://github.com/msarofim/SLR-RFF-BRICK/tree/v2.0-poster-agu-chapman>.
The poster's bottom-right also prints the intermediate-data v2.1 version
DOI (`10.5281/zenodo.20451296`), which pins to the exact data behind the
poster (concept DOI `10.5281/zenodo.20312324` is the all-versions pointer).

Recommended sequence as the poster nears delivery:

1. Land the print-ready poster PDF at `outputs/poster/poster_final.pdf`.
2. Tag: `git tag -a v2.0-poster-agu-chapman -m "Poster delivered to AGU Chapman SLR conference"`
3. Push the tag: `git push origin v2.0-poster-agu-chapman`
4. Publish the v2.0 data deposit per § 2.

## 7. Optional: ESS Open Archive deposit for the poster

AGU runs [ESS Open Archive](https://essopenarchive.org/) (successor to
ESSOAr), which mints a poster-specific DOI separate from this
repository's Zenodo deposits. Worth considering for poster citability
in conference proceedings and follow-up papers.

Once the poster PDF lands as `outputs/poster/poster_final.pdf`:

1. Go to <https://essopenarchive.org/users/login>.
2. Create a new submission of type "Conference Presentation"
   (or "Poster" if available).
3. Upload `outputs/poster/poster_final.pdf`.
4. Metadata:
   - **Title:** _[poster title from ABSTRACT.md]_
   - **Authors:** Marcus C. Sarofim, James E. Neumann, Megan Sheahan
   - **Conference:** AGU Chapman Conference on Sea Level Rise
   - **Abstract:** _[from ABSTRACT.md]_
   - **License:** CC-BY-4.0
   - **Related identifiers:**
     - Code repo: github.com/msarofim/SLR-RFF-BRICK (`v2.0-poster-agu-chapman`)
     - Code DOI (once minted via the GitHub–Zenodo integration in § 5)
     - Intermediate data DOI (this deposit's v2.0 version)
     - Substack post: <https://thesaraphreport.substack.com/p/certainties-and-uncertainties>
5. Publish. Add the ESS Open Archive DOI to `CITATION.cff` alongside the
   others.

ESS Open Archive is free and indexed by AGU; it's the natural home for
the poster artifact specifically. The Zenodo deposits remain the home
for the code and intermediate data.
