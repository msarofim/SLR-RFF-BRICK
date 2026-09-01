# Handoff — the draws readers are migrated, two silent defaults are loud, and the amp 2x2 has an error bar

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, HEAD **`9321758`**, **NOT PUSHED**
(9 commits ahead of origin: the predecessor's handoff commit `86b2b4d` plus 8 from this session).
Written 2026-09-01 ~17:55, continuing `handoff_2026-09-01b_adcov_and_the_parquet_migration.md`.

**⭐ FIRST THING NEXT SESSION: read L25.** Still running when this was written — 4 chains, ~60%,
ETA ~1 h. Everything needed to read it is built and cached; see §1. Nothing else here blocks.

⚠ **The other repo:** `FaIRtoFrEDI` still has **9 unpushed on `heat-ed-morbidity`** and **2 on
`magicc-comparison`** (`8f882b1`, `f81b71f`). Untouched this session. Marcus has not ruled on
pushing them, or on the 9 here.

---

## 1. ⭐ READING L25 — the tooling is BUILT, and the old anchors are RETIRED

`python/diag_amp_by_vintage.py` (`7e5199c`). When the chains land:

    source ~/climate-env/bin/activate
    python python/diag_amp_by_vintage.py            # L21 L22 L23 L23b L25, the default set

L21/L22/L23/L23b come from a per-chain `.npy` cache and cost **0.9 s**; only L25's four chains are
read (~45 s each). Then `diag_slr_convergence_by_chain_ladrillo.jl --tag=L25` BEFORE `postprocess`
(which needs `--accept-slr`). Also run `python/diag_proposal_seed_by_vintage.py` — L25 is in its
list now, and its startup diagnostic **already confirms L25 got `adapted_cov_L14tune_seed2026.csv`,
58 of 58 by the file's own header**. L25 IS the clean one-variable test it was launched as.

**⚠ DO NOT read L25 against 0.9455 / 1.0865.** Those published cells are superseded as a reference.
Recomputed over all 4M post-burn draws with a batch-means se:

| tag | pooled 4M | batch se | R-hat | 10k subsample | published | gap in se |
|---|---|---|---|---|---|---|
| L21 | 0.9438 | 0.0018 | 1.000 | 0.9441 | 0.9455 | −0.9 |
| L22 | 0.9465 | 0.0021 | 1.001 | 0.9473 | 0.9434 | +1.5 |
| L23 | 1.0824 | 0.0037 | 1.002 | 1.0833 | 1.0865 | −1.1 |
| L23b | 1.0896 | 0.0029 | 1.001 | — | 1.0850 | +1.6 |

Every published cell is within **1.6 se**, so the published table AGREES — it was read off a
noisier ~10k thinned pool. ⚠ I first said it was "not reproducible"; that was an overstatement made
before computing the bar, and I withdrew it. What does not survive is its PRECISION and one cell's
sign: **L21→L22, published −0.0021 and read as "the steric cap is not the cause", recomputes to
+0.0026 ± 0.0027** — one se from zero. Both readings are consistent with NO DIFFERENCE and neither
determines a sign. **The conclusion is STRENGTHENED**: the glacier-law cell is **0.1386 ± 0.0041,
about 34 se**. But quote that cell as "no difference", never as a signed four-decimal number.

⚠ **The i.i.d. formula hides this.** A bootstrap at n=10,000 gives se(median) 0.0012, matching
`1.253·sd/√n` = 0.00125 — **1.5–3× too small** on autocorrelated draws in a sampler where 18 of
L21's marginals fail R-hat. The se above is BATCH MEANS, 5 blocks/chain, each block ≫ amp's
autocorrelation time (amp is one of the CONVERGED marginals, τ ≤ 1e6/400 = 2500, blocks 200,000).
**amp's own R-hat is 1.000–1.002** — it mixes fine, whatever the AIS-geometry ridge is doing.

**The reading itself is unchanged from the predecessor:** does L25 return toward L21's centre
(⇒ the proposal covariance moved it, and `champions.json`'s reasoning must be rewritten) or stay
near L23's (⇒ the covariance is exonerated too, and since §2 of the predecessor already killed the
likelihood route, the 2x2 reopens from scratch)? The script prints where L25 sits on the L21→L23
span, with a bar on the difference. L23b sits at **1.05** of it (+0.0072 ± 0.0047 beyond L23).

---

## 2. THE DRAWS READERS ARE MIGRATED — the CSV deletion is now only a decision

`4104418`, `def6cfe`. The predecessor's §4 named **twelve** readers. Measured: **eight**. Three of
the twelve are Julia WRITERS (`scope_slr_fair_uncertainty.jl`, `scope_slr_fairunc_oldbrick.jl`) or
mention the stem only in a comment — that overstated the blocker by a third.

`python/draws_io.py` resolves a LOGICAL `.csv` path to whichever format exists, modelled on
`metric_horizon_table.pairs_path`. Three populations coexist and all must read: the Parquet bulk,
the CSV a fresh Julia run lands as, and `bench_ladrillo`'s frozen `.csv.gz`. `SLR_DRAWS_PARQUET=0`
forces float64.

`bench_ladrillo` needed more than a reader swap: `freeze` would have gzipped a Parquet body into a
`.csv.gz` name and `frozen_paths` would have kept serving it there, surfacing as a scoring failure
sessions later. The frozen name now follows the SOURCE format; L14/L21/L23 keep scoring as frozen.

**Equivalence measured on the PRODUCTION statistic**, all eight drivers, both bases, canonical
outputs restored. Worst relative error **1.9e-05**, everything above 1e-06 on a DIFFERENCE column;
in absolute terms the worst is **1.0e-04 cm** on `forcing_added_cm` (typical 6.4 cm). Separately,
`bench_ladrillo.py --tag=L23` was run end to end: 535 rows, identical columns, **no text
differences** (so every verdict unchanged), max rel err 4.8e-06.

⚠ **The 0.80 GB of CSVs are still NOT deleted — Marcus's call.** They are the only float64 record,
203 GB is free, and it is not a decision to take mid-calibration.

⚠ **Do not commit the float32 drift.** Re-running those drivers rewrites tracked files under
`outputs/` in the last digit (e.g. `te` spread 43.0091 → 43.009). Those were `git checkout`-ed back
twice this session. The committed results were produced on the CSV basis and say so; re-baselining
them because a verification run touched them is the silent re-baseline the measurement exists to
avoid.

---

## 3. TWO SILENT DEFAULTS IN THE CALIBRATOR, AND THREE GATES THAT WERE NOT GATING

`369755c`. ⚠ Editing `julia/calibrate_mcmc_ext.jl` was safe ONLY because the L25 chains run from
the frozen worktree's own copy — verified with `lsof -a -p <pid> -d cwd`, not assumed. Check that
again before editing it while anything is running.

* **`--adcov` now says whether the covariance was CHOSEN or INHERITED.** The banner NAMED the file
  the whole time; what it never said is that **nobody chose it**. It now prints `!! NO --adcov
  PASSED: ... came from the built-in PREFERENCE ORDER, not from this run's command line` or the
  explicit-choice line. Mutation-tested both ways on live `--gis-check` runs (evidence kept:
  `outputs/mcmc/seed_diag_ADCOVNO_seed2026.txt`, `..._ADCOVYES_...`).
* **`--gis-check` stopped transcribing its own reference.** It scored against a hardcoded
  `REF = (0.0617, 0.0146, 0.7749, 0.7351)`. Those are right, and that is the hazard — a refit of the
  offline cell moves them and a transcription cannot notice. It now reads row `g=0` of
  `outputs/gis_g_betaf_variants.csv`, a file this driver does NOT write (`python/gis_offline_cell.py`
  does), so it stays a cross-implementation check. Guard mutation-tested four ways.
* ⚠ **RUNNING it is what found two more.** (a) My first version used `@printf` with a
  `*`-CONCATENATED format string. Julia requires a LITERAL one, so it was an `ArgumentError` at LOAD
  time — the gate could not RUN — and the backgrounding wrapper still reported **exit 0**. (b) The
  tolerance column printed with `%.2f`, so `TOL.rmse = 0.005` had been DISPLAYED as `0.01`: **the
  gate showed twice the tolerance it applied.** Both fixed; all four checks pass at `|diff| 0.0000`.

---

## 4. THREE FALSE PROVENANCE LABELS, AND THE CHAMPION ANNOTATION

`be4158d`. Each with a receipt:

* `ladrillo_figs.py` said **"8 chains"** for L21. Four exist; `outputs/log_l21_postprocess_driver.txt:61`
  says "4 chains x 1000000 draws". The 8 looks like it came from the Torch design note, which
  PROPOSED an 8-seed array never run here.
* `plot_postpred_components_ext.py` said **"20 marginals unconverged"**. Its own log, line 97, says **18**.
* `ladrillo_figs.py` said the glacier law **"is the only axis that moved"** for L23. Refuted by the
  `--adcov` finding. The chain-column identity check that licensed the claim cannot see a proposal
  covariance — it is not a column.
* Flagged, NOT fixed: L23's "19 marginals" was read from a `p_postprocess.log` that is **no longer
  on disk**, so unlike L21's it has no retrievable receipt. Re-run postprocess to restore it.

**`champions.json`:** all six `why` strings KEPT VERBATIM — they are the record of what was decided
on what evidence — with a `correction_2026-09-01` field added to each stating what the two
measurements retire. Separated explicitly: the physical case for the floored law and the
`--accept-slr` acceptance still stand; the attribution of the `ais_gmst_amp` / AIS@2300 shifts does
not. **The rewrite is Marcus's, after L25.** Extra keys are safe — only `tag` is read — but a
`--promote` overwrites the whole entry and would drop the correction.

---

## 5. STATE / GOTCHAS

* **L25 runs from the PREVIOUS session's scratchpad**: `/private/tmp/claude-501/…/f4a2f0f8-…/scratchpad/adcovwt`,
  detached (root ancestor PPID 1, survived that session's exit). `outputs` and `data` are symlinks
  into the live repo. ⚠ **If that directory were cleaned up mid-run the final CSV write is at risk.**
  **Remove it when the chains finish:** `git worktree remove --force <path>`.
* **Amp column cache** at `outputs/mcmc/ampcol_<TAG>_seed<SEED>.npy` — gitignored, 122 MB, ~45 s per
  chain to rebuild. `outputs/diag_amp_by_vintage.csv` is the committed result.
* **Scratch-tag leftovers kept as evidence**: `seed_diag_{ADCOVNO,ADCOVYES,GISCHK2}_seed2026.txt`
  (the banner mutation test), plus the predecessor's `AMPPROF` / `L25smoke`.
* `ladrillo_model_comparison.py` **defaults to `--tag=L10`**, whose tapped SSP deliverable no longer
  exists, so a bare run dies. The equivalence check used `--tag=L23`. Left alone deliberately —
  changing a driver's default tag mid-calibration is a methodological choice, not a cleanup.
* **`MEMORY.md` is 16.5 KB** against a 12 KB soft target / 18 KB hard ceiling. It needs a
  RESTRUCTURE pass, not more additions. Today's finding was routed to `INDEX_slr.md` (13.9 KB).
* `ladrillo_posterior_summary.py:37` still hardcodes `ais_gmst_amp: "N(1.08, 0.15)"` as its prior.
  It targets the older `extC` vintage so this may be correct there — UNVERIFIED, worth a look.
* A slip worth naming: `4104418`'s message described the `scope_ais_amp_law_form.py` fix but staged
  an explicit file list that omitted it. Landed separately as `77fe124`. **When staging by explicit
  list, diff the message against `--stat` before committing.**
* Untouched from the predecessor: the skewed-amp prior (§6 there), L24's pipeline/benchmark, the
  phantom `wf*e` FACTS files, the `ais@2300` CONTROL exceedance, and L21's chain-count/marginal-count
  claims WHEREVER ELSE they appear (only the two live figure labels were fixed).
