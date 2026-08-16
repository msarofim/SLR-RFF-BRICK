# Handoff 2026-08-16 — L11 figures are done; `thermal_alpha` is now a finding, not an open question

**Pickup document.** Continues `handoff_2026-08-15b_L11_accepted.md`, which
remains the authority on the L11 acceptance (§2), the R19 retraction (§1), the
hindcast scorecard (§1b), the `(ℓ, w)` load-time transform (§3), and the run
ordering (§4). Its §5 open-question list is superseded only where noted below.

Repo `SLR-RFF-BRICK`, branch **`brick-mengel-vnext`**. All six suites pass.
**Nothing pushed.**

---

## 0. WHERE THINGS STAND

| item | state |
|---|---|
| L11 deliverable figures | **DONE** — `figures/ladrillo_L11_fig{1,2,3}_*.png` |
| Whole figure chain `--tag=`-driven | **DONE**, L10 regression bit-identical |
| L10↔L11 projection comparison | **DONE** — §2 |
| `thermal_alpha` (15b open question 2) | **PROMOTED to a gated finding** — §3 |
| Thread 5 (Greenland 2300) | untouched, still the one confirmed structural failure |
| Which D2 stream moves α | **OPEN, and it is the next decision** — §4 |

Commits: `725d3a0` (figures + tagging), `c41dafb` (projection diagnostic + the
α finding), `_this_` (CHANGELOG + handoff).

---

## 1. THE FIGURE CHAIN

Everything below `posterior_predictive_ladrillo.jl` still wrote a bare or
L10-hardcoded filename, so an L11 figure run would have **overwritten the L10
deliverable in place**. All of it is now `--tag=`-driven:

```bash
TAG=L11
julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl 2000 --tag=$TAG
julia --project=julia_v2 julia/posterior_predictive_ladrillo.jl 2000 --tag=$TAG
source ~/climate-env/bin/activate && python3 python/ladrillo_model_comparison.py --tag=$TAG && python3 python/plot_ladrillo_memo_figures.py --tag=$TAG
```

Runtime is trivial — the SSP projection is **36 s** for 2000 draws × 3 SSPs ×
450 yr, not the hours the chain runs take. `LADRILLO.md` carries this block.

Two conventions worth keeping:

- **Symmetric suffixes.** `ladrillo_model_comparison.csv` →
  `..._L10.csv`. There is no bare filename that silently means one vintage.
- **An undeclared tag is a hard error.** A new vintage must be added to
  `TAG_DESC` in `plot_ladrillo_memo_figures.py` or the script refuses, so a
  figure title cannot go stale behind a renamed input.

**The NaN trap, and it would have shipped.** D1 drops the Dangendorf total from
the likelihood, so the L11 total has no calibrated error model and
`total_pred_p05/p95` are all-NaN. `fill_between` draws **nothing** from NaN — the
figure-1 total panel would have looked like an ordinary result while the legend
still promised "predictive 5-95% (incl. error model)". The panel now detects the
all-NaN band **from the data, not the tag**, marks itself OUT-OF-SAMPLE in red,
and says why.

L10 regression at every step: both CSVs regenerate bit-identical; the L10 figure
differs from the retired untagged one only in pixel rows 26-54, the suptitle.

---

## 2. WHAT THE CHANGE SET DOES TO THE DELIVERABLE

`python/diag_l10_vs_l11_projection.py` → `outputs/diag_l10_vs_l11_projection.csv`.
Same 2000 draws, same FaIR-mean forcing, same 1995-2014 baseline in both arms, so
the difference is the posterior and nothing else.

**Near-neutral on the total; a partition trade underneath it.** Total at 2100,
L10 → L11:

| SSP | total @2100 | glaciers | steric | gis | ais |
|---|---|---|---|---|---|
| 1-2.6 | 35.41 → 35.14 (**−0.28**) | −1.19 | **+0.87** | +0.15 | −0.08 |
| 2-4.5 | 45.01 → 45.28 (**+0.27**) | −1.17 | **+1.14** | +0.18 | −0.06 |
| 5-8.5 | 94.25 → 95.08 (**+0.83**) | −1.04 | **+1.72** | +0.21 | −0.54 |

By 2300 under ssp585 it is glaciers +0.7, gis +2.9, te **+6.4**, total **+8.3**
cm. AIS is untouched at every horizon, exactly as the hindcast scorecard said.

**So the headline for anyone reading the two figure sets side by side:** the
change set did not move projected sea level. It moved *what projected sea level
is made of*, and the glacier↔steric trade is nearly cancelling at 2100.

---

## 3. THE FINDING — `thermal_alpha` moved AWAY, and 81% of it is D2

15b filed this as open question 2: "`thermal_alpha` sits at 0.16 against L10's
0.150 and the precision-weighted steric optimum of 0.1395. D2 has NOT pulled it
toward the steric optimum." **That framing is too mild and should be retired.**

| | value |
|---|---|
| L10, median of chain medians | 0.15026 |
| L11 | **0.16006** |
| shift | **+1.31 L10 sd** |
| worst between-chain spread, either arm | 0.00050 |
| **mix ratio** | **19.7** (threshold 2.0) → **REPORTABLE** |

Gated under the rule `22635dd` established, and it clears by an order of
magnitude — all eight chains agree, so this is not the non-mixing artefact that
gate exists to catch. There is also no confounder: `te_sea_level` is exactly
`te_s0 + te_α·S(t)` with `te_s0 = 0` (MimiBRICK default, not sampled) and `S` set
by the OHC forcing alone, so α *is* the te panel.

- **Attribution.** D1 alone moved α 0.15023 → 0.15205 (`22635dd`) = **19%** of
  the move. The other **81% is D2**. Quoted, not recomputed — the `chain_D1_seed*`
  files were deleted after that analysis; only `adapted_cov_D1_seed*` and the
  logs survive. Re-deriving it means 4 × 250k fresh chains.
- **Direction.** Level-implied optimum **0.1395**. L10 sat 0.0108 above; L11
  sits 0.0206 above — **1.91× further**.

**Why this is not a cosmetic complaint.** The D2 basis was made orthogonal to the
constant *for exactly this reason*. From the design entry: a mean-zero δ(t) "can
absorb SHAPE and *cannot* absorb LEVEL, so `thermal_alpha` stays identified by
the level. Sub-choice 4 resolved by construction." **The construction did not do
the job it was designed for.** And it is not free: it is what puts the extra
+1.7 cm of steric into the 2100 ssp585 deliverable.

---

## 4. THE OPEN QUESTION, and the test that settles it

**Which D2 stream moves α?** Two hypotheses, both consistent with everything
measured so far:

- **H-A, steric-basis leak.** The `d2_steric_*` basis absorbs level despite the
  orthogonality construction, freeing α to drift.
- **H-B, gsic partition trade.** The `d2_gsic_*` term weakens the modelled
  glacier response; with the total gone from the likelihood (D1) nothing holds
  the component sum, and α rises to take up the slack.

**H-B is not the weaker hypothesis.** Glaciers fall ~1.2 cm while steric rises
~1.1 cm at 2100 in every scenario, and the total barely moves — that *is* the
signature of a partition trade. Do not assume the steric term is the culprit
because it is the one attached to steric.

**No existing chain separates them.** `D2chk`/`D2chk2`/`D2chk3` all carry both
`d2_gsic_*` and `d2_steric_*` (verified in the headers). The discriminating run
is one short chain per stream — D2-steric-only and D2-gsic-only, same tuning, and
read α under the same mixing gate. `22635dd`'s D1 chains were 4 × 250k; the same
size should do.

Downstream of that: whether L11 stands as the deliverable. It is accepted and the
figures are produced, so nothing is blocked — but if H-A holds, the D2 steric
basis needs rework and the accepted posterior carries a known-misidentified α.

---

## 5. OPEN QUESTIONS, re-ranked

1. **Which D2 stream moves `thermal_alpha`** (§4). Promoted above the old #1
   because it now has a number, a gate, and a decisive test.
2. **Thread 5 — Greenland at 2300**, untouched, still the one confirmed
   structural failure: commitment 19-24× below Bochow, unidentified along the
   φ·Leq ridge (14.6 → 58.3 cm at identical hindcast fit). Needs an external
   Leq(T) target, i.e. re-opening Option C.
3. **The glacier blocks over-commit and under-realise** (φ 0.61-0.81,
   commitments 16-76% above GlacierMIP3 in % terms though ≤0.66σ for
   SLOWP/FAST). Same shape as the Greenland ridge — and note §2 now shows the
   glacier projection *fell* ~1.2 cm under D2, so this interacts with #1.
4. Branch rename, carried from handoff 13d.

*(Old #1, deliverable figures, is done. Old #2, `thermal_alpha`, is now #1 in
sharper form.)*

---

## 6. NON-OBVIOUS STATE

- **Disk unchanged from 15b** — 9.2 GB of L11 chains, 2.8 GB superseded L11tune /
  D2chk, 8.8 GB L10. Nothing downstream reads them once the subsample and
  covariance exist. The L10 and L11 chains ARE still needed for the §3 mixing
  gate, so do not clear them before §4 is settled.
- `chain_D1_seed*.csv` are **gone**; the D1 α number is quotable only from
  `22635dd`'s commit message and `outputs/diag_d1_vs_l10.csv`.
- The L11 canonical posterior carries **`gis_slow_ell`/`gis_slow_w` only** — by
  design. Anything reading it must go through `ladrillo_posterior` or call
  `ladrillo_native_greenland!` itself.
- Julia `--project=julia_v2`; pin `OPENBLAS_NUM_THREADS=1` for parallel chains.
- Naming: **Ladrillo**. Never `sed s/brickf/ladrillo/g` — `brickf` ⊂ `brickfm`.
- The **MAY / MAY NOT** from 15b still governs: the posterior may be used for
  projected SLR and anything derived from it; it may NOT be used for
  parameter-level inference on the AIS-geometry block. §3 is a `thermal_alpha`
  claim, not an AIS-block claim, and is separately mixing-gated.
