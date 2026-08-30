# Handoff — the model document is UNBLOCKED; the next step is Marcus writing it

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, HEAD `062956a`. **L21 IS CHAMPION**
(all six modules, since 2026-08-28). Written 2026-08-30 to be picked up cold.

**Supersedes `handoff_2026-08-29_l22_and_coulon_integral.md`** — all three of its OPEN items are
closed, and one of its premises was false (§6). Read this one; go back to that one only for the
L22 arm detail and the CMIP6 portability traps.

---

## 0. THE ONE-PARAGRAPH STATE

**Nothing blocks documentation.** The concern table has C5 CLOSED, C11 resolved, C9 tested, C1
largely dissolved and C8 accepted; what is still open (C7, C10, C6, C2, C3, C4) is **disclosable,
not blocking**. Every number in `deliverables/ladrillo_model_document_DRAFT.md` was verified against
its artifact (0 mismatches over 45 checked cells), the tracked tree is clean, and the benchmark
carries 23 FAIL rows — none of them new. **The remaining work is five `[MARCUS —]` placeholders,
which are yours.** The one genuinely live science question, C7, does not gate the write-up.

---

## 1. ⇒ THE NEXT STEP: FINISH THE DOCUMENT

Five placeholders, in the order they appear:

| # | where | what |
|---|---|---|
| 1 | §1 line 13 | framing — what Ladrillo is for, and why a standalone SLR model |
| 2 | §3 line ~252 | what the hindcast gain does and does **not** license |
| 3 | §4.2 line ~358 | the ssp585@2300 factor-of-2 against MAGICC — **now a like-for-like comparison for the first time**: 1016 [691, 1585] vs 495 [389, 614] |
| 4 | §4.1 line ~448 | how to weigh C1 against the comparison models' own concerns |
| 5 | `deliverables/coulon_comparison_bound.md` | two interpretation paragraphs |

**Three things to carry into the caveats, which the tables no longer say for you:**
* **C1**: quote the **z-score (0.40 prior sd)** or the **+2.36 °C-earlier difference with its
  baseline named**. **NEVER the 3.6×** — it is a ratio of two anomalies and runs 2.41× → 31.5× under
  a sub-degree change in what counts as zero warming. The real residual problem is the **precision**:
  posterior sd ÷ prior sd = 0.0156, and the chains never cross `T_on` modes, so ±0.077 is a
  **within-mode** width.
* **C4**: 20 marginals unconverged under the disclosed `--accept-slr` gate; projected SLR is
  converged (R̂ < 1.05 at all horizons).
* **BRICK 2.0 widths** are now comparable (§4.3) — but part of Ladrillo's ssp585/2300 width is a
  **prior** (78% of the AIS band is `antarctic_lambda`), so narrowness is never scored as a win there.

---

## 2. WHAT CHANGED, AND THE TWO RESULTS THAT MOVED A READING

### C5 CLOSED — every column now carries climate uncertainty
Ladrillo is on the JOINT arm at **54/54** cells and **BRICK 2.0 now has its own joint arm** at 54/54
(`julia/scope_slr_fairunc_oldbrick.jl`). The fixed-band choice was worth **1.2–5.3×** for Ladrillo
and **1.27–6.23×** for BRICK 2.0, both worst at ssp126.

⚠ **THIS CHANGED A READING, NOT A CAVEAT.** With widths finally comparable, **Ladrillo is narrower
than BRICK 2.0 at 8 of 9 cells — 2.8× at ssp126/2100 and 4.4× at ssp126/2300** (34.3 vs 150.4 cm).
That is independent confirmation of the standing cool-scenario under-dispersion finding, against a
like-for-like comparator instead of a fixed-driver one. At ssp585 the two agree within ~13%.

### C1 largely dissolved — the 3.6× was a ratio of two anomalies
In the sampled coordinate `T_on`, where the paleo prior is actually defined (−15.636 ± 5.539), L21
sits **0.402 prior sd** from the mean. Consistent. ⚠ **amp CANCELS in the ratio**; the ORIGIN is the
lever. **Highest → Low–moderate; it should no longer lead the caveats.**

---

## 3. ⚠⚠ FOUR GATES THAT WERE VACUOUS OR ABSENT. Read before trusting any "PASS".

1. **`[GSIC-MATCH]` had NEVER ONCE FIRED.** Two independent defects: it mapped `r.ssp` to a SHORT
   form and matched it against a LONG-label file (**zero rows ever compared**), and
   `worst = max(worst, ...)` in a top-level `for` binds a **new local** in Julia's soft scope
   (**Julia warned on every run**, naming the variable and line). Fixed; now prints `n_matched` and
   errors on zero. It went from a vacuous 0.0000 to a true 0.9869 cm with no change to the data.
2. **The first tap gate had NO POWER** on `total`/ssp585/2150, where a real 1.31 cm offset is smaller
   than the total's own Monte-Carlo noise. Replaced by an **exact** difference of two shipped files.
3. **`plot_ssps_gsic_wr_vs_mengel.py` had no vintage gate** and went live-wrong when
   `ssps_gsic_2300.csv` was regenerated on 1.6.0 while its Mengel arms stayed on 1.4.5 (§5).
4. **`scope_ais_ton_band_hindcast.jl` wrote ONE untagged path** and had already lost a measurement.
   Now tag-suffixed.

**The transferable rule: a gate that reports a number without reporting HOW MANY ROWS IT COMPARED
can be reporting a pass on an empty set.** Print N beside the statistic; make N == 0 an error.

---

## 4. ⚠ STALENESS: TEST BY CONTENT, NOT BY mtime

The calib 1.6.0 forcing was regenerated 2026-08-28. These outputs carry their own `gmst` column, so
staleness is **checkable**, and the check disagreed with the timestamps in both directions:

* `ssps_components_2300_oldbrick.csv` and `ssps_gsic_2300.csv` were genuinely stale (0.38–0.55 K and
  0.4266 K) — both regenerated, both 1.4.5 predecessors quarantined with READMEs.
* **The two Ladrillo files are dated 14:51 against a 15:00 forcing mtime and are FINE** (0.0000 K).
  A timestamp rule would have condemned them.

---

## 5. ⚠ NON-OBVIOUS STATE — the things that will bite

* **`plot_ssps_gsic_wr_vs_mengel.py` currently REFUSES TO DRAW, and that is correct.** Its vintage
  gate fires because `ssps_gsic_2300.csv` is 1.6.0 while `ssps_gsic_2300_mengel{,_b052}.csv` are
  still 1.4.5 (0.4266 K apart). **The fix is to regenerate the Mengel arms
  (`julia/project_ssps_gsic_2300_mengel.jl`), NOT to relax the gate.** Mutation-tested both ways.
* **`bench_ladrillo.py` still scores BRICK 2.0 from the shipped FIXED panel.** Its 23 FAILs and
  module grid are unchanged all session. **Read a width comparison out of
  `ladrillo_model_comparison.py`, never out of the benchmark.**
* **`--promote` was deliberately NOT run.** L21 was already champion; promoting would reset `since`
  to today (falsifying "champion since 2026-08-28") and overwrite the `why` field carrying the
  withdrawn-numbers correction. `--freeze`/`--freeze-fixed` were run instead. If you want `since`
  refreshed to mark the 1.6.0 consistency, that is a one-line call.
* **`champions.json`'s promotion note carried two UNREPRODUCIBLE numbers** — "TE 1.245× and AIS
  1.142× WORSE". The bench run written the same minute has **no L14 arm**, and AIS vs BRICK 2.0 is
  **0.0265, far BETTER**. Withdrawn and named in the note. **Confirmed TE ratio = 1.2355** (full
  window, common years 1920–2025, both arms re-referenced 1995–2005).
* **`[SPLICE-MATCH]` can only run on ssp585** — the one SSP with a committed python-spliced cube.
  ssp126/245 share the code path but are not independently checked. True of both joint arms.
* **Both joint arms are PRIOR PROPAGATIONS, NOT REFITS.** The posteriors were calibrated under fixed
  forcing.
* **The postpred writer applies NO `d2`**, so every bias downstream of it is **pre-discrepancy**.
  The 2025 TE headline is 17.79σ raw but **4.52σ** as the likelihood scores it, and L21→L22
  **improved** it where the raw number worsened. The raw numbers stay correct for the BRICK 2.0
  benchmark ratio, which has no discrepancy term.
* **Two figure scripts still carry a stale "Mengel 2-τ" glacier label**
  (`plot_postpred_components.py:39`, `plot_ssp_projections_mengel.py`), harmless while they read
  their frozen June inputs — each now carries a vintage header — but wrong if repointed.

---

## 6. ⚠ A PREMISE IN THE PREVIOUS HANDOFF WAS FALSE

It asked "why does L22 decline the 48% it could remove?" and proposed a ~2h40m refit. **The fit
declines nothing** — it sits at the unconstrained optimum (c₁ 0.3262 vs LS 0.3286) and had already
taken 100%. The prior carries **0.45%** of the posterior precision, so the refit was provably a
null, answerable in closed form by counting the two places `d2_steric` enters the posterior.
⚠ "Posterior median 0.33 against a prior sd of 0.5, so the prior is not obviously binding" is the
WRONG test — compare **posterior sd to prior sd** (0.046 vs 0.5).

I also asserted **"BRICK 2.0 can never be made joint"**, which was wrong — `set_forcing!` takes an
arbitrary `(gmst, ohc)` pair. Withdrawn, and the joint arm is now built.

---

## 7. AFTER THE DOCUMENT

* **C7 — the TE functional form.** The one live science question; the noise model (L22) and the depth
  split (retracted evidence) are both eliminated. Disclosable, so it does not gate the write-up.
* **Regenerate the Mengel glacier arms on 1.6.0** to un-block the WR-vs-Mengel figure (§5).
* **`INDEX_ccx` memory is over its soft budget** (17,441 content bytes, 991 from the hard ceiling).
  Needs a CCX-focused session — trimming it blind risks facts I have not loaded.
* Optionally repoint `bench_ladrillo` at BRICK 2.0's joint arm, and consolidate figures into
  `figures/` (the hindcast script writes to `outputs/`).

## 8. COMMANDS

```bash
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
uptime; sysctl -n vm.swapusage          # check FIRST
source ~/climate-env/bin/activate
python python/ladrillo_model_comparison.py --tag=L21   # 54/54 joint, both models
python python/bench_ladrillo.py --tag=L21              # 23 FAILs, none new
python python/plot_postpred_components_ext.py --tag=L21 # the hindcast figure
python python/diag_ton_paleo_consistency.py            # C1
python python/diag_d2_steric_prior_binding.py          # the TE residual
```
