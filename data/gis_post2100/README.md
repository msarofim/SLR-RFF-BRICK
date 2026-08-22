# Independent Greenland sources fetched 2026-08-22 — provenance only, NOTHING WIRED IN

**Why these exist.** Handoff §8 and `diag_gis_scorecard_logo.py`: every post-2100 anchor
in the Ladrillo scorecard is **NORCE-CISM** — one ice-sheet model — with **1–5 GCMs per
arm**, and the two cool arms have no constraining power at all
(`diag_gis_k_vs_residual.py`). That is the root cause limiting every structural
conclusion in the 2026-08-22 arc, and no reanalysis of the PROTECT runs can fix it.

**No driver, scorecard or gate has been touched.** These are downloaded and indexed only.

| dir | source | size | what it gives |
|---|---|---|---|
| `greve_chambers_2022/` | Greve & Chambers 2022 — doi 10.5281/zenodo.6029867 | 4.6 GB | **SICOPOLIS to year 3000** under sustained late-21st-C climate. An ice-sheet model **independent of CISM**, on the exact horizon our τ ≈ 3300 yr prior cites. |
| `climberx_10kyr/` | Willeit, Robinson & Kaufhold — doi 10.5281/zenodo.19312031 | 256 MB | **CLIMBER-X coupled, 10,000 yr**, dynamic GrIS, extended SSPs, interactive CO₂/CH₄. Carries `grl/*/8km/V_sle.nc` (ice volume in SLE) and `tg.nc` (global T) as **scalars**, plus `eqco2` equilibrium branches with γ variants. |
| `ismip6_scalars/` | Payne, Nowicki et al. — doi 10.5281/zenodo.4498331 | 2.1 MB | **16 ICE-SHEET MODELS** at 2100 (`GrIS/Ice/scalars_mm_cr_GIS_*.nc`: ISSM ×5, PISM ×2, SICOPOLIS ×2, BISICLES, GRISLI2, CISM, IMAUICE2, GISMHOM…) **plus** per-GCM atmosphere and **ocean thermal** forcing scalars. |

## Read this before using them

* **`ismip6_scalars` is the one that closes the "1 ISM" gap — but only at 2100.**
  16 independent ice-sheet models, which is exactly the structural spread §8 says the
  post-2100 anchors do not have. It does **not** extend past 2100. It also carries
  **ocean thermal forcing**, which our emulator has no term for at all.
* **`greve_chambers_2022` and `climberx_10kyr` are each SINGLE-model.** They break the
  "one ice-sheet model" limitation *post-2100* by being independent of CISM, but they do
  **not** supply structural spread on their own. Two independent models is not an
  ensemble.
* **Greve is 4.6 GB of full model output** for what we need as a scalar SLE time series.
  `run_specs_headers.zip` (0.2 MB) + `_README.pdf` describe the experiment set; a future
  fetch should pull selectively.
* **`climberx_10kyr` is the most immediately usable** — `V_sle.nc` / `tg.nc` are already
  the scalars the commitment question needs.

## The obvious first uses, none of them done

1. **ISMIP6's 16 models at 2100** against our 2100 over-prediction — §8's separate,
   still-open, ridge-invariant defect, which `diag_gis_amp_likeforlike_2100.py` showed
   is a *systematic* ~1.4× shared by all 9 GCM-cases (so: model-side, not driver-side).
   2100 is also the only horizon with independent evaluation.
2. **Greve's year-3000 runs** against the τ prior in `greenland_3basin_component.jl` —
   which is currently a PRIOR SPECIFICATION, NOT A FIT, cited to this very paper.
3. **CLIMBER-X `eqco2` branches** against the φ=1 commitment ceiling (§1.1), the one
   conclusion that survived the whole arc.
