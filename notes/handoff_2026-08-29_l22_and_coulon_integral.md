# Handoff — L22 exonerates the noise model, the depth-split evidence is RETRACTED, and Coulon is bounded on both domains

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`. **L21 IS CHAMPION**; `champions.json`
was not touched today. Written 2026-08-29 to be picked up cold.

**Supersedes parts of `handoff_2026-08-29_te_residual_and_the_ohc_depth_question.md`** — its TASK 1
is answered, its TASK 3 is answered *and one of its sub-results was withdrawn*, and its TASK 2 lost
its premise. Read this one first; go back to that one only for the residual table and the trap list.

---

## 0. THE ONE-PARAGRAPH STATE

The 17σ modern thermal-expansion residual is **not the noise model** — L22 capped the steric AR(1)
marginal by 64% and the residual did not move. It is **not** reachable by `thermal_alpha` either, and
**nothing else in the fit moved at all**, so it is structural in the JOINT fit. The hypothesis that
explained that (D2 blind to it by construction) was tested the same day and is **REFUTED**; what
actually explains the fit's behaviour is that the likelihood's own AR(1) metric prices the residual
as cheap to carry. Separately and importantly: **the observational evidence I had produced against
FaIR's vertical heat partition was RETRACTED** — it was an estimator artifact, and on a correct
estimator FaIR and IGCC agree. So "something structural holds TE up" is supported; "that something is
the depth split" is **not**.

---

## 1. ⇒ WHAT IS OPEN, IN PRIORITY ORDER

### OPEN 1 — Why does L22 decline the 48% it could now remove? **The live question.**

In the likelihood's own AR(1) precision, the share of the TE residual removable by the D2 basis is
**19.4% under L21** and **48.2% under L22** (the cap raises it, as it should). L22 moved
`d2_steric_1` by +0.70 of L21's own posterior sd — but not further, and the residual got slightly
*worse*. Candidates, none separated:
* the D2 prior (sd 0.5 cm; `d2_steric_1` sits at 0.33, so not obviously binding),
* coupling to the **gsic** stream, which shares the D2 machinery,
* other likelihood terms pulling against it (total, GlaMBIE, rung, SMB).

Cheapest next step: refit with the steric D2 coefficients **freed from their prior** (or widened) and
see whether the residual moves. If it does, the prior is the binding constraint and that is the
answer; if it does not, the pull is from another term and the coupling is worth mapping.

### OPEN 2 — The C7 concern in the model document is now WRONG as written

`deliverables/ladrillo_model_document_DRAFT.md` C7 says TE is worse than BRICK 2.0 (1.236) and calls
it OPEN. It is still open, but the *reason* has changed: it is not the noise model, and the depth
split can no longer be offered as the explanation (§2). **C7 needs rewriting** and is the most likely
thing to be quoted stale.

### OPEN 3 — The Coulon integral is delivered; the write-up is not

Both domains are now bounded (§4). Nothing is written up, and per the ruling it must be reported as a
**bound, never a single number**.

---

## 2. ⚠⚠ READ BEFORE RE-OPENING THE DEPTH SPLIT — I RETRACTED MY OWN EVIDENCE

Earlier on 2026-08-29 I reported a **6.3σ sign disagreement** between FaIR and IGCC on the vertical
heat partition (FaIR +1.07 ± 0.34 %-pts/decade vs obs −1.75 ± 0.28 above 700 m) and said no box
boundary placement could close it. **That is withdrawn.** It came from fitting an OLS trend to a
cumulative share formed after rebasing both series to 1971 — a denominator that is zero at the base
year, so the front of the window is a ratio of two near-zero numbers whose swing enters the fit as
signal. **Diagnostic that caught it: rebasing the same IGCC data to 2005 flips the fitted trend from
−1.81 to +9.41.** Compounding it, FaIR's partition history is non-monotone (0.728 / 0.799 / 0.709
across 1971–92 / 1993–2004 / 2005–24, the middle excursion consistent with post-Pinatubo surface heat
re-entry), so a line through 1993–2024 is dominated by that sub-window.

On the **baseline-free** estimator — the fraction of heat gained *across* a window that went above
700 m — **FaIR and IGCC agree**: 1971–92 0.728 vs 0.734; 2005–24 0.709 vs 0.703; change −0.020
(−0.035…0.000 across the full box-2 split envelope) vs −0.031 ± 0.130. **Neither is resolved at 2σ.**
NCEI over the Argo window agrees too (−0.055 ± 0.083), a weak check since NCEI is one of IGCC's inputs.

Consequences: **there is no established observational mismatch in FaIR's vertical partition**, and the
empirical case for an "OHC aging module" replacing FaIR's box→depth mapping is gone. The *physical*
case for the two-coefficient split is untouched (α ratio 1.70×, EOS-80-corroborated, implying interior
water at 6.8 °C) but cannot be supported by the observed partition either — and at observed drift
rates it is worth **sub-cm at 2300**.

⚠ Two data facts worth keeping: IGCC's `ocean_2000-6000m` rises by **exactly 1.15 ZJ/yr**, 32
increments, sd 0.000000 — a prescribed rate, not data, so use the 0–2000 m band. And **NCEI publishes
no annual 700–2000 m layer before 2005**, so any trend across 1993–2024 spans a change of observing
system.

Quarantine (on disk, gitignored): `outputs/quarantine/20260829_trend_of_rebased_share/` with its own
README. The trend block was **removed** from `diag_fair_layers_vs_igcc_depth.py` rather than patched,
so a "fixed" version of a wrong estimator cannot re-supply the old number. Its level comparison stands.

---

## 3. L22 — WHAT WAS RUN AND WHAT IT SETTLED

**L22 = L21 with ONE change:** the steric AR(1) **MARGINAL** sd bounded at **0.10362 cm**, the
1993–2025 mean of `S.steric.ϵ` (the ε the likelihood sees, 0.05 cm floor included), derived in-script.
Everything else is L21's. `run_mcmc_L22.sh`, `run_l22_postprocess.sh`.

⚠ **The cap MUST bind the marginal σ/√(1−ρ²).** A cap on σ alone does not bind — ρ = 0.963 inflates
it 3.72× — and that arm would have reported a null it never tested. ⚠ **Every start in the repo
violates the cap** (default θ0 at marginal 1.155; all four `overdispersed_starts.csv` rows at
0.187–0.234), so `repair_steric_start!` scales σ holding ρ to half the cap on both start paths and
prints it. The starts file itself is untouched.

**It took:** cap line + both repair lines on all four chains, `[MAP start] = −675.78` vs L21's
−650.59, acceptance **0.236** (= L21's), convergence equal (@2100 R̂ 1.015, ESS 1271,
sd(medians)/mean(sd_wc) **0.044** vs L21 0.040). Noise genuinely bound: marginal **0.277 → 0.100**,
median at 96.5% of the cap.

**The result:** 2025 TE residual **16.94σ → 17.79σ** (bias 0.847 → 0.889 cm — *worse*).
`thermal_alpha` +0.20 sd, `d2_steric_1` +0.70 sd. **Nothing else moved**: every AIS/GIS/glacier bias
changed <0.011 cm. So a term at 5.4× the observational σ **was buying nothing**.

**The S(t) test (`diag_te_residual_onto_shape.py`) REFUTES the D2-blindness hypothesis.** D2 *is*
orthogonal to S(t) over the fit window (5e-17), but **global orthogonality is not sub-window
orthogonality** — over 1993–2025 D2 can represent 95–98% of the residual. **What decides is the
metric:** ε-weighted diagonal says 98.2% removable, the AR(1) precision the likelihood actually uses
says **19.4%**. A ρ of 0.968 makes a smooth persistent offset cheap to carry, so there is almost no
gradient to remove it — the fit is not ignoring an easy gain. ⚠ **Never read this decomposition in
the ε-weighted diagonal.**

⚠ **CORRECTION carried into four files:** the pre-registration called the D2 basis "1/ε²-weighted,
i.e. modern-era-weighted". **It is not** — `d2_basis` ACCEPTS a weight vector and **IGNORES** it,
orthogonalising in the PLAIN inner product, and says so in its source. Read the function, not the
call site's argument list. The "prior sd 0.5 cm, five times the cap" half was right.

---

## 4. COULON — [DECIDED] AND DELIVERED

**Marcus ruled option (c) 2026-08-29: report BOTH averaging domains as a bound. Rebuild nothing.**
The paper **never states its averaging domain** — verified against the PMC full text (PMC12680641),
not a summarisation pass. So (a') cannot be defended as reading the source.

⚠ **The `ais_gmst_amp` frame precedent does NOT transfer.** There, frame ambiguity was a reason to
prefer *fit* — but "fit" meant fit to our OWN observational targets. Here it would mean agreement with
the very number being compared against: tuning to the comparator.

**Delivered on the integral** (`data/cmip6_coulon_allcells/`, a companion — `data/cmip6_coulon/` is
UNTOUCHED). Acceptance gate reproduces the published endpoint table to **±0.00 K** on all four models
and both domains, from an independent build path. JOIN gates 0.009–0.156 K.

2015–2299 integral, °C-century: **land 23.59–32.89 | all cells 23.10–29.51**. Ensemble integral max
27.25, reachable to 25.72 at the median amp. **Reachable 1 of 4 under land, 2 of 4 under all cells** —
same split as the endpoint, so the domain-sensitivity finding is robust to the statistic. ⚠ But
**which** models flip changes: UKESM flips on the endpoint and not on the integral (needs amp 0.951,
47.4% of the posterior, 0 configs at the median amp — it just misses); IPSL flips on the integral.
MRI reachable throughout, CESM2-WACCM never.

⚠ **"One line in the reducer" is FALSE for 3 of 4 models.** `reduce_cmip6_tas_coulon.py` takes its
≤2100 leg from `data/cmip6_pai/`, **already land-masked**; flipping `SFTLF_MIN` splices an all-cells
tail onto a land-masked baseline. `build_coulon_allcells_series.py` re-reduces that leg from the
Pangeo zarr instead. UKESM `r4i1p1f2` is **settled** — do not re-raise. `sftgif`, the latitude cutoff
and post-processing are all **ruled out** upstream.

---

## 5. NON-OBVIOUS STATE — the things that will bite

* **Julia stdout only flushes at process exit**, and ProgressMeter owns the terminal until then, so
  `outputs/mcmc/log_L22_seed*.txt` look like nothing but a progress bar WHILE RUNNING. The header is
  not missing. Do not "fix" it.
* **`posterior_predictive_ladrillo.jl` writes the `ais`/2025 row TWICE, byte-identical**, in both arms.
  Upstream quirk, not an L22 artefact; `diag_l21_vs_l22_steric_cap.py` drops it and says so.
* **Portability traps in the CMIP6 build**, all of which crash rather than mislead: a `"YYYY-12-31"`
  slice bound is an invalid date on UKESM's **360-day calendar**; Pangeo returns `numpy.datetime64`
  for MRI-ESM2-0 but cftime for the 360-day models (use `.dt.year`, never a comprehension); and
  UKESM's **local historical** NetCDF filtered to ">2100" is an EMPTY frame that reaches the
  plausibility check as a nan and reports a bogus "coordinate mismatch".
* ⚠ **`outputs/scope_ais_ton_band_hindcast.csv` IS WRITTEN UNTAGGED** by both postprocess drivers,
  while every other output they write is tag-suffixed. It had **uncommitted** modifications from a
  prior session at the start of 2026-08-29 and the L22 driver **overwrote them** (it now holds
  L21/L22 rows; HEAD is intact and the file is regenerable by re-running
  `scope_ais_ton_band_hindcast.jl --tags=`). This is the same bug class the repo fixed for
  `--gis-check` — tag-suffix the output so a re-run cannot overwrite the measurement a decision
  rested on. **Not yet fixed. Check `git status` for uncommitted diagnostics BEFORE launching a
  postprocess driver.**
* **Disk:** L21 + L22 chains are ~18.6 GB total in `outputs/mcmc/` (gitignored).
* **`outputs/quarantine/` is gitignored** in this repo — quarantines live on disk, not in git.

## 6. MEMORY AND GLOBAL CONVENTIONS CHANGED TODAY

* **`~/.claude/CLAUDE.md`**: new "Execution hygiene (promoted 2026-08-29)" section — 5 rules
  (never edit a running script; a gate must not read its own output + mutation-test gates; thresholds
  from observation/law; check `uptime` before a long job + pin BLAS; never write .docx XML with
  ElementTree). ⚠ **The threshold rule was SOFTENED by Marcus the same day**: observations or
  physical laws *first*, **other models only if absolutely necessary** — and "another model" NEVER
  means the code under test.
* **`MEMORY.md` restructured**: content 16,504 → 12,716 bytes. New sub-index **`INDEX_diag.md`**
  (sampler / gate / band diagnostics, 18 memories, NOT auto-loaded). Two stale "L14 is canonical"
  facts fixed (root READ FIRST + `INDEX_slr` LIVE STATE) — **L21 has been champion since 08-28**.
  Snapshot at `../memory_backup_20260829/`. Integrity: 380 pointers, 0 broken, 0 orphaned.
* New memories: `l22_noise_cap_exonerates`, `te_residual_metric_decides`, `rebased_share_trend_flips`,
  `coulon_domain_unstated`.

## 7. COMMANDS

```bash
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
uptime; sysctl -n vm.swapusage          # ⚠ check FIRST (eta_in_days_is_not_a_slow_run)
source ~/climate-env/bin/activate
python python/diag_l21_vs_l22_steric_cap.py      # the L22 verdict, all 4 predictions
python python/diag_te_residual_onto_shape.py     # the S(t) test + the metric table
python python/diag_coulon_integral_bound.py      # both domains, gate + bound
```
