# Handoff — test 6 fixed, the AIC/BIC test built, the AIC paragraph to write, GMD vs JOSS (09-16 evening)

**Start here.** Continues `handoff_2026-09-16_paper_start.md` (still the paper's map — its §1 to-do list,
§4 traps and §5 FACTS/MAGICC-scope argument all stand; its §3 test-6 bullet is now ✅). CHANGELOG
**09-16c** (test 6) and **09-16d** (the IC test) are the primary records. Read `INDEX_slr.md` and
`INDEX_cmp.md` before touching the deliverable; the two new memory files are
`ic_ladrillo_vs_brick20` and `gis_offline_cell_anchor_vintage`.

**STATUS:** `ladrillo-dev` clean and pushed at `7ea8ae7` (+ this note). `run_ladrillo_tests.sh` **10/10
PASS**. Marcus's GMD draft skeleton is `deliverables/GMD.Ladrillo.v1.docx` (911 words, UNTRACKED —
Marcus's file, do not sync or rebuild it). The documentation of record is still
`deliverables/LadrilloUpdateDescription_FILLED.md` ↔ `Ladrillo.9.14.26.docx`.

---

## 1. ⭐ NEXT

1. **Add the AIC paragraph to the documentation** — draft in §3 below, modelled on Wong et al. 2017
   GMD §4.2.2–4.2.3 (`~/Documents/2026/ClaudeDocs/Papers/BRICKv0.2.gmd-10-2741-2017`, pp. 2750–51),
   shorter. Two placements: (a) `LadrilloUpdateDescription_FILLED.md`, "Ladrillo Observational
   Comparison", directly after the Table 4 discussion and before the thermal-expansion paragraph, as
   **Table 5 + one paragraph**; (b) the GMD draft's "Results: Comparisons to Observations" — Marcus's
   text, so hand him §3 as a block to accept or rewrite, not an edit to his docx.
2. **Decide the venue: GMD vs JOSS** — the case is in §4. My recommendation is GMD (model-description
   paper) now, JOSS only later and only for an extracted, registered Julia package. Tony has published
   Ladrillo's ancestors in both (GMD 2017, JOSS 2022) — worth one line to him.
3. Then the 09-16 handoff's list, unchanged: package extraction for Tony's team → `facts` remote →
   the FACTS/MAGICC-scope call → the "must STATE" open-science items → benchmark freeze → the pulse
   analysis. **One addition to the "must STATE" list:** the AIC test's in-sample/out-of-sample
   asymmetry (§3, last sentence of the paragraph) — and the structure test that removes it (a BRICK 2.0
   arm recalibrated on the extended targets, `note_2026-08-14_ladrillo_vs_brick20_scorecard.md`) is still
   not run. If a reviewer asks for it, that is the answer, not another IC arm.

## 2. WHAT HAPPENED THIS SESSION (receipts in CHANGELOG 09-16c/d)

- **Test 6 fixed (`f2ade83`)** — TWO defects, not the one the 09-16 handoff named. The transcribed
  calib-1.4.5 reference, yes; but also `gis_offline_cell.project()` anchored its splice on
  `fair_mean_gmst.csv` (the 1.4.5 RFF-cube mean, never regenerated) under a 1.6.0 future: 0.027 K over
  the anchor → 0.15–0.17 cm at 2100, above the 0.10 cm tolerance. A bare regeneration would still have
  failed. Anchor now = the scenario's own history (as the kernel). Cell + variants regenerated (1 h 54 min
  + 22 min): **every fitted parameter byte-identical**, only projections moved (A+B g=0 2100: 6.93/9.83/
  17.37 → 7.28/9.80/15.54 cm; kernel matches to 0.001). Test 6 [3] now READS the g=0 row of
  `gis_g_betaf_variants.csv` (mutation-tested). `gis_port_reference.csv` regenerated and committed
  (bit-identical through 2024). Pre-fix outputs quarantined with a README.
- **The AIC/BIC test (`7ea8ae7`)** — `julia/ic_hindcast_residuals.jl` (per-draw residuals of both
  posteriors on the L24 targets; GATED: medians reproduce both postpred p50 series to 1e-16, so these
  are the Table 4 residuals) → `python/ic_ladrillo_vs_brick20.py --rho-max=` (two likelihoods applied
  identically; k = every sampled parameter, 58 vs 35). Result table in §3. The one BIC tie (AR(1),
  ρ ≤ 0.99) is diagnosed, not mysterious: the profiled ρ sits AT the bound for every BRICK 2.0 series.
  Steric ties **by construction** (same TE module). Optimiser validated against a multistart (≤0.04 ln L).

## 3. THE AIC PARAGRAPH — draft for the documentation (methodology/results text; Marcus's voice for the paper)

Wong et al. 2017's template: state the metrics and what each penalises (their Eqs. 12–13), give the free
parameter counts, compute at the maximum-likelihood ensemble member, report AIC and BIC, read a mixed
verdict as "not unreasonably over-parameterized". Ours is shorter because the verdict is not mixed except
in one arm, and that arm's tie is explained.

**Table 5.** Information criteria for the Ladrillo L24 and BRICK 2.0 hindcasts on the same four component
series (Antarctica, glaciers, Greenland, thermal expansion; N = 502 observation-years, 1900–2026, cm relative
to 1995–2005). ln L is the maximum over posterior draws; k counts every sampled parameter of each posterior.
AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L; lower is better. Δ columns are BRICK 2.0 minus Ladrillo (positive
favours Ladrillo).

| likelihood | k (Ladrillo / BRICK) | ln L (Ladrillo / BRICK) | ΔAIC | ΔBIC |
|---|---|---|---|---|
| Independent Gaussian, observational σ | 50 / 27 | 75.6 / −1252.1 | +2610 | +2512 |
| AR(1) + observational σ, ρ ≤ 0.99 (the calibration's bound) | 58 / 35 | 248.5 / 180.9 | +89 | −8 |
| AR(1) + observational σ, ρ ≤ 0.95 | 58 / 35 | 246.1 / 148.2 | +150 | +53 |
| AR(1) + observational σ, ρ ≤ 0.90 | 58 / 35 | 240.7 / 106.9 | +222 | +125 |

> **Paragraph (documentation version).** Ladrillo has more free parameters than BRICK 2.0 (58 against
> 35, counting the AR(1) noise parameters of each), so the hindcast gains in Table 4 could in principle be
> bought by the extra 23. Following Wong et al. (2017), we test this with the Akaike and Bayesian
> information criteria, AIC = 2k − 2 ln L and BIC = k ln N − 2 ln L, evaluated at the maximum-likelihood
> posterior draw of each model on the same four component series (N = 502 observation-years), charging
> every sampled parameter (Table 5). Under a likelihood with independent observational errors the
> log-likelihood gain (+1328) is two orders of magnitude larger than the 23-parameter charge. Under the
> calibration's own AR(1)-plus-observational-error likelihood, with the autocorrelation and noise scale
> profiled per series for both models, the gain is +68 log-likelihood units: three times the AIC charge
> (ΔAIC = +89) but level on BIC (−8), because at the calibration's ρ ≤ 0.99 bound the AR(1) term acts as a
> near-random-walk discrepancy that absorbs BRICK 2.0's smooth component biases at little cost; bounding ρ
> at 0.95 restores a BIC margin of +53. The gain is carried by glaciers and Greenland (+33 and +30) and
> Antarctica (+6); thermal expansion is a tie by construction, since both models use the same module and
> the same ocean-heat driver. As in Wong et al. (2017), the criteria therefore do not indicate that
> Ladrillo is over-parameterized relative to BRICK 2.0. Two limits apply: the maximum over draws is a lower
> bound on each model's true maximum likelihood, and Ladrillo was calibrated to these targets while
> BRICK 2.0 was calibrated to its own — the criteria correct for a fitted model's optimism, not for a
> comparator fitted to different data.

(**Paper version**: the same with the ρ-sensitivity sentence and the glacier/Greenland split moved to a
footnote or the supplement, ≈120 words. The numbers are all in `outputs/ic_ladrillo_vs_brick20_L24*.md`;
regenerate with `julia … ic_hindcast_residuals.jl` (90 s) then `scripts/run_ic_arms_20260916.sh` (~35 min).
Cite Akaike 1974 and Schwarz 1978 as Wong does; Kass & Raftery 1995 for reading ΔBIC.)

## 4. GMD vs JOSS — the case either way (Marcus's call)

What the two venues ARE, from the two BRICK papers in the Papers folder:
- **GMD (Wong et al. 2017, BRICK v0.2, 20 pp.)** — a *model description paper*: physics of each component,
  calibration method and likelihood, hindcast evaluation with RMSE/AIC/BIC, projections, an application.
  Reviewed on the science; requires a version number, archived code + data at submission (Zenodo), and
  a persistent code-availability section. Typically 4–8 months.
- **JOSS (Wong et al. 2022, MimiBRICK.jl, 4 pp., 1,869 words)** — a *software paper*: statement of need,
  what the package does, how it couples. Reviewed on the SOFTWARE (installation, tests, documentation,
  API, community guidelines) in a public GitHub review; no evaluation, no scientific claims, no tables of
  hindcast skill. Weeks to a few months. JOSS explicitly wants "substantial scholarly effort" in the
  software itself and is wary of thin wrappers.

The GMD draft skeleton already IS a model-description paper: two SLEIP-scope tables, five component
sections, "Comparisons to Observations", "Future Projections". None of that content is publishable in JOSS.

**For GMD (recommended):**
- Every claim the draft makes — the "niche" among SLEIP's seven, the 20th-century hindcast gains, Table
  4/5, the FACTS/MAGICC placement — is a scientific claim that needs a science venue to be citable.
- GMD is where BRICK v0.2 lives; a "spinoff of BRICK" is naturally reviewed by the same community, and
  the DOI-versioned model is what SLEIP Phase 2 would cite.
- The Zenodo-at-submission requirement matches the plan already agreed (Zenodo after Tony's team review).
- The 09-16 handoff's §5 scope question resolves more easily here: a GMD model-description paper is
  EXPECTED to carry an evaluation section, and "hindcast vs BRICK + Table 5 + FIG 12" satisfies it
  without the FACTS/MAGICC comparators, which can wait for the pulse paper.

**For JOSS (or both):**
- Faster, lighter, and reviews the thing Tony's team is about to review anyway (code quality, tests,
  docs); the package extraction in the 09-16 handoff's §1.1 is exactly the JOSS deliverable.
- Wong's precedent is BOTH: GMD for the model (2017), JOSS for the Julia/Mimi package (2022). The same
  two-step is open to Ladrillo, but the JOSS half needs a standalone, registered `Ladrillo.jl` (or a
  MimiBRICK v3 branch — Tony's call from the 09-16 handoff) with its own tests and docs, not the
  4,016-file research repo.
- Against JOSS alone: it would leave the science unreviewed and uncitable, and JOSS may judge a package
  that reuses MimiBRICK's components a derivative.

**Recommendation:** GMD now for the model (the draft's content), with JOSS as a possible second paper once
the package extraction exists — in that order, as Wong did. Ask Tony which he'd co-author; his answer
may settle it.

## 5. DECISIONS MADE (and why)

- IC design: k = EVERY sampled parameter (the maximal charge against Ladrillo — Ladrillo's 4 ledger + 4
  d2 columns are inert on these series and charged anyway); ln L = max over draws (Ladrillo 2000 = the
  postpred's thinning, BRICK all 10,000 = its postpred — the asymmetry favours BRICK); two likelihood
  arms, both applied identically, with the AR(1) sd/ρ PROFILED per series on both (BRICK's own noise
  params are on different series and cannot be used like-for-like); no delta ramp, no d2 (Ladrillo-only
  devices); the total reported separately as out-of-sample for both. DIC/p_V kept in the CSV only —
  p_V is not an effective parameter count when the likelihood is not the fitted one (BRICK 158 vs 35).
- Test 6: the reference is READ from the variants file, not re-transcribed (the calibrator's 08-19
  discipline); the offline cell's anchor made like-for-like with the kernel rather than regenerating
  `fair_mean_gmst.csv` (larger blast radius, and an RFF-vs-SSP history would still mismatch).
- `gis_port_reference.csv` committed regenerated (precedent `0e0b491`); it is a python-vs-julia
  cross-implementation reference the suite rebuilds, not a frozen one.

## 6. FILES

**New:** `julia/ic_hindcast_residuals.jl`, `python/ic_ladrillo_vs_brick20.py`,
`scripts/run_ic_arms_20260916.sh`, `scripts/regen_gis_offline_cell_20260916.sh`,
`outputs/ic_hindcast_obs_sigma.csv`, `outputs/ic_ladrillo_vs_brick20_L24{,_rho0.95,_rho0.9}.{csv,md}`,
`outputs/ic_ladrillo_vs_brick20_L24_perdraw.csv`, `outputs/quarantine/20260916_gis_offline_cell_v145_anchor/`.
**Changed:** `python/gis_offline_cell.py` (`project()` signature lost `gmst_hist`), `python/diag_gis_g_betaf.py`,
`python/emit_gis_port_reference.py`, `julia/validate_gis_projection_ab.jl`, `outputs/gis_offline_cell_fits.csv`,
`outputs/gis_g_betaf_variants.csv`, `outputs/gis_port_reference.csv`, `figures/gis_offline_cell.png`,
`.gitignore`, CHANGELOG 09-16c/d, the 09-16 handoff §3.
**Memory:** `ic_ladrillo_vs_brick20`, `gis_offline_cell_anchor_vintage`; pointers in `INDEX_slr`, `INDEX_gis`.

## 7. ⚠ NON-OBVIOUS STATE / TRAPS

- **Gitignored, regenerable:** `outputs/ic_hindcast_residuals_*.csv` (132 + 25 MB, 90 s) and the
  `_rho*_perdraw.csv` tables. The headline `_perdraw.csv` (5 MB) IS tracked.
- **`fair_mean_gmst.csv` is STILL calib 1.4.5** (the RFF-cube mean). Any script reading it beside a 1.6.0
  scenario file mixes vintages — remaining readers are off the live path (`calibrate_mengel_glacier.py`,
  `glacier_2tau_validate.py`, `plot_recalib_components.py`, legacy `calibrate_mcmc.jl`). The `--zone=all`
  offline-cell arm carries the same stale projections.
- **The AR(1) arm's size depends on the ρ bound** — report ρ ≤ 0.99 as the headline (the calibrator's
  bound) with 0.95/0.90 as sensitivity; never quote one row alone.
- **Runtimes:** `gis_offline_cell.py` 1 h 54 min (11 cells — the 08-12 "35–40 min" predates D/D2),
  `diag_gis_g_betaf.py` 22 min, the IC script ~10 min per ρ arm. All run under `nohup … & disown`
  (tool-driven background shells die at 10 min). ⚠ A `pkill -f "climate-env/bin/python3 …"` does NOT
  match the resolved interpreter path — one orphaned first run wrote to the same log for ~50 s before I
  caught it by PID; outputs were unaffected (written at the end). Kill by PID.
- **The `pgrep -f` self-match** bit once more this session (a suite wait-loop): the work was already done.
  Match on the interpreter+script or wait on the PID.
- Two `outputs/mcmc/seed_diag_*_seed2026.txt` files changed when the suite ran (the 09-16b named-adcov
  cleanup, not this arc) and were committed with the test-6 fix.
