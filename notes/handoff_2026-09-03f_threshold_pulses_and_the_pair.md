# Handoff — the threshold question is ANSWERED; both stage-2 headlines were median statements

**Start here.** Written 2026-09-03, late. Supersedes `2026-09-03e` for everything about the
pulse's SUMMARY STATISTIC and its PULSE SIZE; `2026-09-03e` remains the reference for stages
3-5's mechanics, the four cross-model figure candidates, and the tap ruling. Two repos moved,
**nothing pushed** — `SLR-RFF-BRICK` (`ladrillo-dev`, 21 unpushed) and `FaIRtoFrEDI`
(`heat-ed-morbidity`, 29 unpushed).

⭐ **The session's question was Marcus's: how should a pulse that is supposed to be a MARGINAL
change be handled when it crosses a hard threshold? It is now measured and answered, and the
answer changed what stage 2 reports. Stages 3-5 are still not begun and now inherit a new
output contract.**

---

## 1. THE ANSWER, IN THREE MEASUREMENTS

### 1a. The hard annual step is UNBIASED — it is a VARIANCE problem, not a bias problem

DAIS fires disintegration on a hard annual step (`antarctic_icesheet_magdep_component.jl:241`,
`if T_ant[t] > temperature_threshold`, full rate regardless of how far above). The natural
worry is that this makes a marginal pulse a lottery whose expectation is wrong.

**It does not.** mean(**integer** years the step charges) ÷ mean(**continuous** measure of
`{t : T_ant(t) > thr}`, linearly interpolated within each annual step) = **0.917-1.039 across
all 42 cells, median 1.006.** It inflates the per-draw sd up to **8.8x** and leaves the
expectation alone.

⇒ **A hard threshold does not make a pulse marginal wrong. It makes the MEAN a Monte Carlo
problem.** More draws (or less variance) fix it; no model change is needed.

⚠ **My first pass measured the FIRST-CROSSING ADVANCE and reported a 3.9x bias. That was my
error, not the model's.** On a peak-and-decline marker the pulse buys time at BOTH ends of the
above-threshold window, so the entry-side advance understates it ~2x and over-attributes the
rest to discretization. **The continuous MEASURE is the comparator, never the crossing DATE.**
If you see a claim of large quantization bias anywhere, it predates this correction.

### 1b. The big responses are NOT bifurcations, and the gate that existed was blind

`scope_slr_pulse_vv.jl` carried exactly ONE threshold gate, `[TAP-CROSSING]`, and it watches
**Greenland**: 6 draws on vvM/CH4, 2 on vvHL, **zero** on vvH. The **Antarctic** channel in the
same shipped files moves **185 of 2000 draws past 1 cm on vvVL/CH4**, max **67.3 cm** for a
1 GtCH4 pulse, of which `gis` contributes 0.17 cm. One threshold gate watching the small
threshold reads exactly like a model with no threshold problem (`two_statistics_can_be_blind`).

Pooled channel split at 2300: smooth 20910, **quantization 7021**, **bifurcation 69** (0.25% of
draw-cells, 3.2% of the summed response). The 67.3 cm draw crosses in **BOTH** arms — **85
years above threshold at baseline, 133 under the pulse**, and the continuous measure agrees
(47.71 vs 48). Quantitative pre-check: vvVL declines through the threshold at ~3 mK/yr and the
pulse is ~57 mK in `T_ant`, so ~20 yr at the exit alone — physically consistent, not an
artifact. ⇒ **The premium is bought by draws that hover near the threshold for DECADES, not by
draws that tip only when pulsed.**

### 1c. The premium is 67-97% of E[dAIS] — the median is the wrong statistic for an expectation

Lemoine-Traeger split `E[d] = P(smooth)*E[d|smooth] + P(fired)*E[d|fired]` at 2300: vvVL/CO2
**0.028 + 0.185**; vvM/CH4 **0.030 + 0.816**; vvH/CO2 **0.068 + 0.137** (lowest share, 67%).
⇒ **A median headline deletes ~90% of the expected AIS response.**

This RECONCILES two memories that looked opposed: `dais_fastdynamics_quant` ("do NOT quote the
AIS mean") and `paired_mean_crosses_on_a_tail` ("report the paired median"). **The mean was
unusable because it was UNDER-SAMPLED, not because it was biased.**

---

## 2. ⭐⭐ MARCUS'S TWO RULINGS THIS SESSION

1. **The headline is the Lemoine-Traeger PAIR, not the median alone** — report
   `P(smooth)*E[.|smooth]` and `P(fired)*E[.|fired]` as two numbers, never the sum alone.
   Consistent with mimibrick-quirks #11, METHODS §3.5, and the standing view that not giving a
   probability is not neutral (`unresolved_amplification_arm`).
2. **Re-run the pulse-size ladder for L24 before stages 3-5 lock the spec at 10 GtCO2.**

**Both are done. See §3 and §4.** ⚠ Ruling 1 binds stages 3-5: **each comparator arm must emit
the pair, not a median.** BRICK 2.0 has the same DAIS step so the classifier ports directly;
MAGICC and FACTS need their own equivalent or an explicit statement that they have none.

---

## 3. THE LADDER — the MEDIAN is the size-biased statistic, NOT the mean

`julia/diag_pulse_size_vv_ladder.jl` (`c385554`), vvM/CO2, tapped, 2000 draws, six rungs
0.1-30 GtCO2 IRF-scaled from the real 10 Gt pair.

**Gates, two of them exact:**
- `[BASE-IDENTITY]` **0.000e+00** — the 1 Gt and 10 Gt FaIR builds' baseline arms are the same
  climate exactly (a real check on the builder's determinism).
- `[P0-IDENTITY]` **0.000e+00** — the P=10 rung reproduces the SHIPPED stage-2 draws file
  bit-identically. A ladder that cannot reproduce the number it audits is auditing something else.
- `[IRF-VALID]` **0.06-0.11%** of the median response — the scaled 1 Gt climate against a REAL
  1 Gt FaIR cube, pushed through Ladrillo PER DRAW.

**Per-GtCO2, total @2300, relative to the 1 Gt rung:**

| pulse | p_fired | median/Gt | mean/Gt |
|---|---|---|---|
| 0.1 | 0.35% | 0.981 | 1.129 *(7 fired draws — unusable)* |
| 1   | 2.85% | 1.000 | 1.000 |
| 3   | 6.85% | 1.033 | 0.927 |
| **10** | 20.3% | **1.206** | **0.943** |
| 30  | 55.2% | **2.386** | 0.956 |

⭐⭐ **THE MEDIAN AND THE MEAN HAVE OPPOSITE PULSE-SIZE PATHOLOGIES.** The median tracks whether
the MEDIAN DRAW has crossed, so it inflates as `p_fired` climbs toward 50%; the AIS median at
30 Gt is **5.4x**. The mean integrates over all draws and is flat to ~5% over a **30x** range —
it is the SMALL rungs where the mean fails, on 4-14 fired draws.

⇒ ⭐ **THERE IS NO SINGLE PULSE SIZE AT WHICH BOTH STATISTICS ARE GOOD.** This is an independent
and much better argument for the pair than the one in §1c.

⇒ ✅ **THE 10 GtCO2 SPEC STANDS**, because the headline is now the mean/pair.
⚠ **But the shipped stage-2 MEDIANS carry the size bias: +1.8% at 2100 and +20.6% at 2300.**

Reproduces `dais_fastdynamics_quant`'s July BRICK-Mengel 9-20% AND agrees with its ≤1 Gt half
exactly: our 0.1/0.3/1.0 rungs span **1.9%**.

---

## 4. ⭐ HALF THE VARIANCE WAS FREE — Rao-Blackwellising P(fired)

**Measured first, so the effort went where the variance was:** a median **53%** (range 23-75%)
of the AIS mean's Monte Carlo variance is carried by **`P(fired)` ALONE**, not by either
conditional mean.

And `P(fired)` needs no model run. Since `amp > 0`,

    T_ant[t] > thr   <=>   GMST[t-1] > (thr - TANT0)/amp

— one `gcrit` per draw — so the whole classification is a threshold on the **config's own
GMST**. Sorting each config's window once makes the year count a binary search, and P is
evaluated exactly on all **2000 x 841** pairings (841x the sample the paired run sees) in
seconds.

**Measured effect (`f703cb8`, all 14 cells re-run):** `se(RB)/se(plain)` = **0.65 median
(0.34-0.89)** = **equivalent to 2.35x the draws, for zero compute.** Estimator shift ≤1.29 se
everywhere (median 0.29 se, **0 of 84 cells beyond 2 se**) — same quantity, lower variance.

⚠ **Valid ONLY because the draw→config permutation is UNIFORM over configs**, so the paired
sample is an unbiased sample of the cross-product P is computed on. Stated at the site.
`[P-FIRED-CONSISTENT]` gates the paired P against the exact one at 3 of its own binomial se —
and it is a check on the PAIRING, since a mis-permuted map biases the paired P while leaving
the exact one untouched. Measured z = **0.02-0.58** on all 14.

✅ **±5% is ALREADY MET on the TOTAL**: rel se @2300 = **1.0-6.4%**, only vvVL/CH4 outside.
On the AIS sub-component alone, **5 of 14** remain outside — all cool markers with low `p_fired`.

---

## 5. ⚠⚠ A 5x UNIFORM RE-RUN IS THE WRONG TOOL FOR WHAT REMAINS

**This is new information Marcus did not have when he asked for more draws, and it is why I
have NOT run 10,000 draws.**

- **`ais_gmst_amp` is autocorrelation-exhausted.** tau ≈ **5,500-6,800**, so the FULL 1M
  post-burn chain holds only ~150-180 independent values per seed — **~650 over all four**. The
  current 2,000 draws already exceed that, so **10,000 adds ZERO independent `amp` information**
  — and amp carries ~386 cm/unit (`ais_amp_prior_widened`).
- `antarctic_temp_threshold` is different: tau ≈ 430-525, **~8,500 available**, so it WOULD gain.
- **Between-chain se corroborates that the iid se is roughly honest**: 0.51-1.69x, median 0.91x
  (4 chains, so that ratio has ~3 df and is itself noisy). The 841-config axis does the
  decorrelating.

⇒ **What is left is `E[d|fired]` on 127-251 fired draws in the cool cells. STRATIFY toward the
threshold; do not sample uniformly.** OPEN, and Marcus's call.

---

## 6. ⭐⭐ THE PAIR IMMEDIATELY CORRECTED TWO SHIPPED HEADLINES

All 14 cells re-run (`d90aaea`). **Zero gate failures.** **Every prior number is bit-identical**
— max |new − old| is **0.000e+00** on `paired_med_cm` across all 14 cells files and on
`med_diff_cm` across all 14 paths files. The model path is untouched; what changed is what is
reported. `[AIS-CROSSING]`'s `int_over_cont` came back **1.012-1.020** on the production driver,
corroborating §1a independently.

**Both `2026-09-03e` headlines are statements about the MEDIAN, and both weaken on the mean:**

| finding, as shipped | on the median | **on the mean** |
|---|---|---|
| CO2 scenario-invariance @2100 | 1.6% spread | **1.35x** |
| CH4 U-shape @2100 | 2.70x | **1.34x** |
| CH4 U-shape @2300 | 4.4x | **1.37x** |

- **CO2:** the invariance belongs to the **SMOOTH TERM** (0.006896-0.007528 = **9.2%**); the
  **PREMIUM spans 1.85x** (0.005896-0.01093). ⇒ Restate as *"CO2's smooth response is
  scenario-invariant; its tipping premium is not."* At 2300 the mean spans 1.79x vs 1.48x.
- **CH4:** the median jumps exactly where `p_fired` crosses 50% — ML→M at 2300 (0.324 → 0.633)
  and vvH at 2100 (0.569), i.e. **where the MEDIAN DRAW itself starts crossing**. ⇒ Much of the
  U's MAGNITUDE is the `ais_threshold_median_artifact` mechanism. **The component decomposition
  (all four rising +17-25% together ⇒ a climate input) still STANDS for the SMOOTH CHANNEL**;
  what does not stand is the SIZE of the U as a physical statement.

⚠ **`smooth_term_cm` is `(1-P)*E[.|smooth]`, so it falls partly because P RISES.** Do not read
its decline across markers as physical saturation without separating the two factors.
⚠ **The pair's two terms are comparable across runs only AT THE SAME PULSE SIZE** — P is
size-dependent by construction (§3).

---

## 7. FILES — what changed, and where

**`SLR-RFF-BRICK` (`ladrillo-dev`), 6 commits this session:**

| file | state |
|---|---|
| `julia/diag_ais_crossing_pulse_vv.jl` | NEW (`7f45411`). Standalone closed-form classifier; `--mutate=seed\|shuffle` harness. |
| `julia/diag_pulse_size_vv_ladder.jl` | NEW (`c385554`). The ladder; `[BASE-IDENTITY]`/`[P0-IDENTITY]`/`[IRF-VALID]`/`[FLAT]`. |
| `julia/scope_slr_pulse_vv.jl` | `[AIS-CROSSING]` + `[P-FIRED-CONSISTENT]` gates; RB'd P; pair + `se_mean_cm` into `cells`; **`mean_diff_cm` + `se_mean_cm` into `paths`**. |
| `outputs/pulse_ladrillo_{cells,gates,paths}_vv*` | all 14 re-run, tracked, committed. |
| `outputs/pulse_ladder_{cells,gates}_vvM_CO2_*` | NEW, committed. |
| `outputs/diag_ais_crossing_pulse_vv_{L24,gates_L24}.csv` | NEW, committed. |
| `outputs/diag_ais_crossing_pulse_vv_draws_L24.csv` | **8.3 MB, UNTRACKED** — same convention as `pulse_ladrillo_draws_*`. Regenerate in ~4 min. |
| `.gitignore` | `outputs/*_MUT*.csv` — see §8. |
| `CHANGELOG.md` | four entries: `2026-09-03f/g/h` + the gitignore note. |

**`FaIRtoFrEDI` (`heat-ed-morbidity`), 1 commit:** `scripts/build_fair_pulse_vv_v160.py` gains
`--pulse-size` (`1b7f1bb`). The size and the label move together from ONE number — the label is
the filename AND the per-tonne divisor. Built `fair_cube_{gmst,ohc}_vvM_{pulsebase,pulse}_CO2_1Gt_2030_raw.csv`.

**Memory:** `pulse_threshold_is_variance_not_bias`, `pulse_size_the_median_is_the_biased_one`,
both indexed in `INDEX_cmp_pulse.md` (now 5.3 KB against a 14 KB soft budget — room to spare).

⚠ **Pre-existing dirt NOT mine, untouched:** `deliverables/LadrilloUpdateDescription_L24.docx`
(modified) and two untracked `.docx` at the repo root; `FaIRtoFrEDI`'s
`deliverables/vanvuuren_H_erf_2000_2250.csv` and `magicc_comparison/processed/vv_wide_20260831/`.
All four were dirty at session start.

---

## 8. NON-OBVIOUS STATE AND TRAPS

1. ⚠ **The mutation harness clobbered the canonical table the first time it ran.** A
   `--mutate=seed` run wrote the sweep's own filename with a deliberately-wrong table. Fixed by
   `OUTSUF` (mutation and single-marker runs get a suffix) AND by gitignoring + deleting
   `outputs/*_MUT*.csv`. **`gate_reads_its_own_output` in the OUTPUT direction** — the same
   hazard, one step later in the pipeline. Both gates ARE mutation-tested: `--mutate=seed` fails
   `[CONFIG-IDENTITY]` 1999/2000; `--mutate=shuffle` fails `[EXPLAINS-TAIL]` **alone**, which is
   the discriminating outcome.
2. ⚠ **`T_ant` reads `GMST[t-1]`, not `GMST[t]`** (`antarctic_icesheet_magdep_component.jl:165`).
   The pre-existing `diag_ais_tipping_under_forcing.jl` uses `GMST[t]` — immaterial for a
   tipped-FRACTION at 2300, material for a crossing-YEAR comparison. The new files use the lag.
3. ⚠ **`[EXPLAINS-TAIL]` is an ORDERING between two MEASURED quantities**, not a chosen cut: the
   smooth population's p99.9 must sit below the fired population's median (`threshold_from_obs_or_law`).
4. **Frozen copies** `julia/_frozen_ladder.jl` and `julia/_frozen_scope_slr_pulse_vv.jl` are on
   disk and gitignored. They MUST live under `julia/` — the drivers include
   `ladrillo_projection.jl` by `@__DIR__`.
5. **Torch verdict: stayed local, correctly.** Ladder ~20 min single process; the 14-run sweep
   4-concurrent with BLAS pinned to 1 thread each. Stages 3-5 are the same order.
6. **The L24 docx is CANONICAL**, not `FILLED.md`. Run `python3 deliverables/sync_filled_from_docx.py
   --verify` before any text edit. Not touched this session.

---

## 9. WHAT TO DO NEXT

1. **Stage 3 (BRICK 2.0)** — still the cheapest, still not begun; `2026-09-03e` §3 has the recipe
   and it is unchanged. ⭐ **NEW REQUIREMENT: it must emit the Lemoine-Traeger pair.** BRICK 2.0
   has the same DAIS hard step, so port `[AIS-CROSSING]` and the RB'd P directly — check its own
   `ais_temperature_{coefficient,intercept}` convention rather than assuming Ladrillo's `1/amp`.
2. **Decide the stratification** (§5) for the five cool-marker AIS cells, or accept 5-8.5% rel se
   on the AIS sub-component and say so in the caption. Marcus's call; the total is already inside ±5%.
3. **The cross-model FIGURE design is STILL OPEN** — `2026-09-03e` §6, four candidates, my
   recommendation was form 2 (nested "spread of models" vs "spread of draws" bands) + form 3.
   ⚠ **That recommendation now needs revisiting**: with the pair as the headline, a figure whose
   band is a p05-p95 of draws no longer shows the statistic being reported. Bring it back to
   Marcus WITH the pair in mind — do not pick it silently.
4. ⚠ **The premium's MAGNITUDE still rests on the BINARY FLUX FORM**, which `ais_binary_form_priced`
   prices at **26-750x of the scenario separation**. Unbiased discretization does not make the
   form right. This is the largest un-priced uncertainty in every number in §1c and §6.
5. **Restate the two headlines** in any deliverable that carries them (§6) before they travel further.
