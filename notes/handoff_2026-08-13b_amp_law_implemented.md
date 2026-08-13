# Handoff 2026-08-13b — the amp law is implemented and it nearly closes G4; the deliverables are on L10; the memo-figure pipeline is the open item

**Self-contained pickup:** this note + the `CHANGELOG.md` entry for 2026-08-13
(second session). It CONTINUES `handoff_2026-08-13_ladrillo_step5_production_done.md`
and closes its §4 items 1–5; that note remains the record of the production run,
the acceptance, and the `ais_iceflow0` ridge (§3 there is still current and still
governs what the posterior may be used for).

Repo `SLR-RFF-BRICK`, branch **`brick-mengel-vnext`**, tip **`59e0706`**.
**All six suites pass** (`./run_ladrillo_tests.sh`) at that tip.

---

## 0. STATE IN ONE PARAGRAPH

The Greenland amp(GMST) law is implemented, gated and shipped. Measured on the
accepted L10 posterior it takes the G4 scenario spread from **9.80 → 7.37 cm**
against a 6.3–7.3 band — it closes ~97% of the gap, not the ~40% the previous
handoff estimated. The canonical posterior in the projection kernel moved
**extC → L10**, the two deliverable drivers were re-run on it
(`ssps_components_2300_L10.csv`, `postpred_L10_*`), and the pre-extC "78.02 cm"
vintage is quarantined with a README. The open item is that **five scripts,
including the memo-figure pipeline, still read the extC outputs**; migrating them
to L10 changes every number in the memo and is the next piece of work.

---

## 1. WHAT LANDED

### G4 measured on the posterior for the first time (commit `8b68d19`)
`julia/diag_gis_spread_2100_ladrillo.jl`, 10 000 draws, per-draw pairing (spread is
a difference of two runs of the SAME vector; differencing marginal quantiles would
mix draws). Horizon gate: runs to 2100 and asserts the first draw's GIS@2100 is
BIT-IDENTICAL to a 2300 run before trusting the truncation.

| arm | GIS@2100 126/245/585 | G4 q05/q50/q95 | in band |
|---|---|---|---|
| constant amp (as calibrated) | 6.81 / 9.59 / 16.59 | 7.37 / **9.80** / 12.44 | 3.8% |
| **amp law (default)** | 6.17 / 8.16 / 13.52 | 5.58 / **7.37** / 9.33 | **29.0%** |
| amp law, no flat-hold | 6.17 / 8.11 / 13.93 | 5.89 / 7.78 / 9.85 | 24.6% |

The offline cell's POINT estimate was 10.44 cm; the posterior median at the same
constant amp is 9.80.

### The anchor (sub-choice 2.2) — SETTLED at dT_eff = 0.940 K
`python/diag_gis_amp_anchor.py`. `amp = Σxy/Σx²` is an x²-weighted mean of
pointwise ratios, so its warming level is `Σx³/Σx²`: HadCRUT5 0.945, Berkeley
0.950, GISTEMP 0.925, **mean 0.940 K** — far below the 1.25 K placeholder and
below the window's own 2015–2024 level (1.53 K), because the x² weights sit where
the record is long, not where it is warm. Gate: the recomputed amp reproduces
`gis_driver_constants.csv` to 1e-9 in all 36 cells. Re-anchoring moves amp at
2.75 K from 1.670 to **1.652**.

**Stop worrying about the anchor.** An independent route — matching ESTIMATORS
rather than warming levels, i.e. dividing by CMIP6's own full-window
through-origin amplification (1.509) instead of R_secant(dT_eff) (1.494) — agrees
to **1.0%**.

### The law (`ladrillo_projection.jl`)
`amp(dT) = amp_draw × S(dT)`, S tabulated by `diag_gis_amp_cmip6.py` on a 0.01 K
grid, read by the kernel, PCHIP over 0.75–2.75 K and held flat outside.

Four design points worth not re-deriving:
1. **The anchor is a GRID NODE.** Linear interpolation of a plain 0.01 K grid gave
   S(dT_eff) = 0.99999992 and the kernel's load-time identity check fired.
   Inserting the node makes it exactly 1 in floating point.
2. **LEVEL form.** S multiplies the amplification (`amp·S(dT_t)·GMST_t`) because
   the estimator behind S is a SECANT. Integrating a trend ratio is the error in
   memory `project_pai_cmip6_time_diagnostic`.
3. **Anchor-preserving splice kept**: the offset uses `mean(S_t·GMST_t)` over the
   same 11-yr window, so the driver still reproduces the observed mean there
   exactly — asserted to 1e-12 in both arms.
4. **The warming-level window is immaterial** — 30-yr running mean (what CMIP6
   measured S on) vs raw annual moves the driver ≤ 0.007 K, and 0.0000 K wherever
   S is flat-held. Kept at 30 for fidelity, not because it matters.

**Suite step 6's parity assertion was RETHOUGHT, not deleted**, as asked. [1]
compared the projector's amp CONSTANT to the calibrator's; the projector's amp is
now a function, so new check **[5]** asserts the function MEETS the calibrator at
the anchor (`S(dT_eff) = 1 ⇒ amp(dT_eff) = GIS_AMP`), plus the shape's measured
form and four structural driver gates (law off reproduces the constant-amp splice
exactly; law inert over the observed years; anchor preserved; ssp585 2100 lowered).

### Deliverables on L10 (commit `3735c5a`)
`outputs/ssps_components_2300_L10.csv`, `outputs/postpred_L10_{components_timeseries,bias,coverage}.csv`.
Totals at 2100 (cm), extC → L10: SSP1-2.6 35.91 → 35.41, SSP2-4.5 49.48 → **45.01**,
SSP5-8.5 97.75 → 94.25.

### Quarantine (commit `59e0706`)
`outputs/quarantine/20260813_pre_extc_mengel_vintage/` + README — ten files, the
whole `parameters_subsample_brick_mengel{,_ext}.csv` projection vintage. Vintage
difference, not a bug; the README says so and carries the component table. The two
legitimate cross-vintage consumers were repointed at the quarantine path, gated by
`diag_mengel_to_ladrillo_attribution.py` re-running **byte-identical**.

---

## 2. TWO THINGS THE PREVIOUS HANDOFF GOT WRONG

1. **"The amp law does not close the 2100 gap — ~8.7 cm, roughly 40%."** It closes
   ~97% (9.80 → 7.37 against a 6.3–7.3 band). The 8.7 figure came from
   interpolating a stage-1 single-vector amp SCAN, which cannot see that the law
   acts DIFFERENTIALLY by scenario: ssp585 sits at S = 0.860 in 2100 while ssp126
   sits at 0.926. **General lesson: a one-parameter scan cannot stand in for a law
   whose argument varies across the arms being compared.**
2. **"Holding S flat above 2.75 K is conservative."** It is the right call on
   evidence — the 3.25 K bump is scenario composition — but it is NOT conservative
   in the G4 direction. Over 3–4.5 K the raw binned curve gives S ≈ 0.878–0.883,
   *above* the held 0.860, so flat-holding assumes slightly MORE decline than
   CMIP6 shows and LOWERS G4 by 0.41 cm. Both shapes are emitted; run the arm with
   `LADRILLO_GIS_SHAPE=gis_amp_shape_fullcurve`.

---

## 3. OPEN ITEMS, in order

1. **Migrate the extC consumers to L10.** Five scripts still read
   `ssps_components_2300_extC.csv` / `postpred_extC_*`:
   `plot_ladrillo_memo_figures.py`, `ladrillo_model_comparison.py`,
   `diag_gis_likelihood_leverage.py`, `diag_noise_model_and_grip.py`,
   `scope_greenland_{options,bochow2026}.py`. This changes **every number in the
   memo figures**, so it is a reviewed piece of work, not a path edit. Until it is
   done the `_extC` outputs are LIVE INPUTS, not archive — which is exactly why
   they were not quarantined. Quarantine them in the same pass that migrates.
2. **Re-run the acceptance record under the law.** `outputs/mcmc/slr_convergence_L10.csv`
   was computed CONSTANT-AMP. The law is a deterministic transformation applied
   identically to every chain and Greenland is ~9 of ~46 cm at 2100, so the
   between/within ratio (0.010 vs a 1.05 R̂ threshold) has room to spare — but the
   certificate and the shipped model are not literally the same run. Note the
   diagnostic writes to `slr_convergence_$(TAG).csv`, so a re-run under the law
   **overwrites the acceptance record**; give it a distinct tag or accept the
   overwrite deliberately.
3. **Sub-choice 1 (flat-hold above 2.75 K) is still Marcus's call.** Measured at
   0.41 cm on G4, both arms runnable. Default = flat-hold.
4. **Report G4 honestly**: 7.37 cm is 0.07 cm ABOVE the band, not inside it. 29%
   of draws fall inside.

### Owed, not blocking (carried forward)
- **4.4** ν sensitivity once. **4.5** refit with the four glacier set-asides at
  prior centres. **4.6** structural-uncertainty caveat wherever bands are compared
  to FACTS.
- `parameters_subsample_brick_mengel_extC.csv` still says "brick_mengel" although
  extC has no Mengel glaciers — and now so does `..._L10.csv`. Wrong before the
  rename; kept separate.
- After 1.0, the noise-model note §6: the total stream is 56% algebraically
  redundant and no AR(1) member whitens any stream → an explicit discrepancy term.
  Not before 1.0.
- Etymology sentence for the sharing memo — **Marcus drafts prose**.
- Branch is still `brick-mengel-vnext`.

---

## 4. NON-OBVIOUS STATE

- **The A+B Greenland slot has NO defaults.** `ladrillo_setup(gis_ab=true)` leaves
  the seven `gis_*` parameters unset and Mimi refuses to build until a draw is
  applied. This is a FEATURE (a placeholder would run and look plausible) and it
  is why `test_ladrillo_projection.jl` now seeds one draw right after setup.
- **`LADRILLO_USED_COLS` is gone.** It silently meant `:stock` and would have
  checked the wrong column contract on an L10 posterior. Ask
  `ladrillo_used_cols(VARIANT)`; get VARIANT from `ladrillo_posterior_variant()`.
- **`LADRILLO_GIS_SHAPE=<stem>`** selects an alternative shape table from
  `outputs/`; the stem names both `<stem>.csv` and `<stem>_meta.csv` so they
  cannot be mismatched. Sensitivity arms only — deliverables use the default. The
  spread diagnostic puts the arm in its OUTPUT FILENAME so an arm cannot overwrite
  the deliverable's numbers.
- **`outputs/quarantine/` is gitignored wholesale**, but past quarantine READMEs
  were force-added and this one is too. The moved CSVs/PNGs staged as renames
  (ignore rules do not apply to already-tracked files).
- **One clobber, caught and reverted:** the first `posterior_predictive_ladrillo`
  run wrote `postpred_extC_coverage.csv` because that filename was a literal rather
  than a constant. Fixed to `OUT_COVER` and the extC file restored from git. If you
  see a coverage file with an unexpected mtime, check it that way.
- `python/diag_gis_amp_cmip6.py` now REQUIRES `outputs/gis_amp_anchor.csv`
  (from `diag_gis_amp_anchor.py`) and errors without it. No fallback constant —
  anchoring at a guessed warming level is the error it used to make.
- Python env `source ~/climate-env/bin/activate`; Julia `--project=julia_v2`.
- Naming: **Ladrillo**. Never `sed s/brickf/ladrillo/g` — `brickf` ⊂ `brickfm`.
- Greenland option C failed and is out of pass 1; the same criticism applies to
  A+B at high warming, where it is invisible rather than absent. Flag it wherever
  2300 or high-warming Greenland is reported, and note it compounds the flat-hold
  caveat above.

---

## 5. COMMITS THIS SESSION

| commit | what |
|---|---|
| `8b68d19` | amp(GMST) law implemented; G4 9.80 → 7.37 on the L10 posterior |
| `3735c5a` | deliverables regenerated on L10 with the law |
| `59e0706` | quarantine the pre-extC "78.02 cm" vintage |
