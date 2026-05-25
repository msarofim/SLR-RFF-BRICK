# Quarantined BRICK posterior (pre-Tony-PR#93)

Moved here 2026-05-22 when Tony's post-PR#93 joint SNEASY+BRICK posterior arrived.

## What's in this directory
- `parameters_subsample_brick.csv` — 10000-row BRICK-only posterior used by all
  obs-driven and FaIR-driven BRICK runs prior to 2026-05-22.

## Why it's quarantined
This posterior was calibrated WITHOUT the Frederikse 2020 Greenland data that
Tony added in MimiBRICK PRs #91 (merged 2026-04-02) and #93 (merged 2026-05-06).

Symptom: ~97.6% of posterior draws had Greenland `b > v0`, producing essentially
zero historical GIS melt — BRICK GIS at 1850 ≈ 0 cm vs Frederikse target ≈ −6 cm.
See memory entry `project_brick_gis_posterior_pathology.md`.

## What replaces it
- Canonical post-replacement: `data/MimiBRICK/parameters_subsample_brick.csv`
  (sliced from Tony's full joint posterior `parameters_subsample_sneasybrick.csv`
  delivered 2026-05-22).

## Which outputs were produced by this pre-fix posterior
All `outputs/brick_obsdriven_*to2024.csv` files dated on/before 2026-05-21
were products of this posterior. After Tony's post-PR#93 posterior arrived
on 2026-05-22 and we re-ran the SNEASY-override 10k:

- **MOVED into `brick_obsdriven_to2024/`**: all pre-fix obs-driven outputs
  except `brick_obsdriven_sneasyMAP_override_to2024.csv`.
- **LOST (process error)**: the pre-fix
  `brick_obsdriven_sneasyMAP_override_to2024.csv` (179 MB) was overwritten
  by the post-fix 10k re-run before being quarantined. The 500-member
  quickcheck (`brick_obsdriven_sneasyMAP_override_to2024_postpr93_quickcheck.csv`)
  was retained in `outputs/`; the pre-fix sneasyMAP raw trajectories are
  irretrievable. Pre-vs-post medians were captured in stdout and pinned
  to memory entry `project_brick_gis_posterior_pathology.md` before loss.

Pre-fix headline medians (still recoverable from memory and from the other
pre-fix files in `brick_obsdriven_to2024/`):
- GIS at 1850: +0.03 cm (pathological — should be ~−6 cm vs Frederikse)
- TE at 2018: +1.07 cm (Frederikse target ~+2.31 cm; undershoot)
- TE at 2024: +1.23 cm

Post-fix (from the post-PR#93 10k SNEASY-override run, now canonical):
- GIS at 1850: −7.05 cm median (within Frederikse target range)
- TE at 2018: +3.05 cm (small overshoot vs Frederikse +2.31; previously undershoot)
- b > v0 frequency in posterior: 0.0% (was 97.6%)
