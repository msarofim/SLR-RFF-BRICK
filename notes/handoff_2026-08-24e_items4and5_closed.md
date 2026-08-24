# Handoff — items 4 and 5 are closed, the band survives both, and three shipped framings were wrong

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commits **`d8c49c8`** (item 4),
**`0e5e033`** (item 5), **`fc6b5e9`** (this note). Written 2026-08-24, to be picked up cold.
**Continues** `handoff_2026-08-24d_curvature_resolved_ais_sampler_next.md`, whose §5 items
**1 (ITEM 4) and 2 (ITEM 5) are now both CLOSED**. Everything in that handoff's §1–§4 stands
unchanged; its §5 items 3–6 survive and are re-ranked in §8 below.

**Marcus's 6 → 4 → 5 ordering is complete.**

---

## 0. THE ONE-PARAGRAPH VERSION

**ITEM 4 — the Antarctic block's 9-of-17 convergence failure does not corrupt the
deliverable.** The projection itself converges in **11 of 12** scenario × component × horizon
cells, including **ssp585 AIS @2300 (R̂ 1.026)**, the cell that is 55% of the total and carries
the whole λ story. **`ais_runoff_Ton` is retired** at ≤0.6% of the band everywhere;
`antarctic_alpha` is worth up to 57.22 cm (22.7%), but as a bound **measured to be 1.54× too
large**. Two things fell out that were not asked for: the input–output degeneracy is a **STIFF
direction, not a flat ridge** (so the lever is proposal scaling, not reparameterisation), and
**the direction that qualifies on item 4's own criterion is neither named parameter** — it is
the anchored net mass balance, contrast **0.249** at ssp585 @2300 against their 0.167 and 0.156.

**ITEM 5 — two more shipped framings turned out to be single-cell artefacts.** The "rank 1 vs
rank 10" scenario inversion **does not exist at 2100**; it is a 2300 property, and **one
mechanism — the tipped fraction — drives both the scenario and the horizon axis**. And the λ
prior's worth spans **~5800×** across the six cells, with its median and spread envelopes
moving in **opposite directions**, so no single number describes it.

---

## 1. WHAT WAS BUILT

**Item 4** — `julia/diag_ais_item4_sampler.jl` (three tests on one chain read; ~12 min read,
~6 min of arms) and `python/diag_ais_item4_perdraw_contrast.py` (the rank-safe follow-up).
Outputs `outputs/diag_ais_item4_{deliverable,fluxes,arms,perdraw,contrast}_L14.csv`,
`outputs/log_item4_sampler_L14.txt`.

**Item 5** — `python/diag_ais_item5_horizon_repricing.py`, outputs
`outputs/diag_ais_item5_{ranking,envelope}_L14.csv`. **No chains read**: both source CSVs
already carried all three horizons, so item 5 was post-processing of
`diag_ais_block_propagation_L14.csv` and `scope_ais_lambda_prior_L14.csv`.

**Gates, all passed and all worth keeping:**

* **[IDENT]** the control arm reproduces `diag_ais_block_propagation_L14.csv` at rel
  **0.00e+00** on all six scenario × horizon cells — same draws, same kernel.
* **[SMB]** the anchored-window SMB lands **−0.23 σ** of the Rignot A5 target the calibrator
  itself anchors (1836.7 vs 1863.4 ± 118.1) ⇒ the flux extraction is reading the quantity the
  likelihood scored, not a lookalike.
* **[HIST-IDENT]** anchored-window fluxes are **bit-identical between the two scenarios**
  (rel 0.00e+00), as the shared historical forcing requires. Without this, the "where the data
  are" leg of §3 would be asserted rather than established.
* **[RIDGE-CORR]** max |corr| **0.703** (`antarctic_alpha`, with `ais_slope`) and **0.613**
  (`ais_runoff_Ton`, with `ais_gmst_amp`) — this is what makes §4 a bound rather than a
  posterior revision.

---

## 2. ITEM 4 [1] — THE DELIVERABLE CONVERGES, WITH ONE CAVEAT THAT MUST TRAVEL

R̂ of the **projection**, not of a marginal. 11 of 12 cells pass at < 1.05.

| scen | cmp | yr | R̂ | ESS | chain-median range | p05–p95 |
|---|---|---|---|---|---|---|
| ssp245 | ais | 2100 | **1.070** | **38.4** | 1.40 cm | 35.44 |
| ssp245 | ais | 2300 | 1.025 | 183.2 | 39.25 cm | 280.77 |
| ssp585 | ais | 2300 | **1.026** | 163.8 | 37.25 cm | 252.36 |
| ssp585 | total | 2300 | 1.024 | 216.9 | 34.84 cm | 253.44 |

The one failure, **ssp245 AIS @2100**, fails on **ESS 38.4**, not displacement: it carries the
*smallest* between-chain median range in the table (1.40 cm = 0.116 within-chain sd). Before
this, `diag_slr_convergence_by_chain_ladrillo.jl` had certified only the **total at ssp245 /
2100–2150**; the AIS component, 2300, and ssp585 had never been measured — that gap *was* item 4.

⚠ **R̂ passes at ssp585 @2300 because the band is WIDE, not because the chains agree** — their
medians span **37.25 cm = 13.2% of the 281 cm median**. Carry the median range in cm beside any
R̂ verdict on this band. Generalised in memory `rhat_denominator_forgives`.

---

## 3. ITEM 4 [2] — STIFF, NOT FLAT (the prediction inverted)

`calibrate_mcmc_ext.jl:1166` documents a 34:1 input–output degeneracy, and `ais_iceflow0` /
`antarctic_alpha` are the discharge side of it. So the hypothesis with a mechanism behind it was
that the chains slide along that ridge — disagreeing on the fluxes, agreeing on their net.

| window | smb | discharge | **net** |
|---|---|---|---|
| anchored 1979–2008 | 1.012 (ESS 923) | 1.008 (ESS 1027) | **1.069 (ESS 43)** ✗ |
| unobserved 2281–2300 (ssp245) | 1.070 ✗ | 1.073 ✗ | 1.018 |
| unobserved 2281–2300 (ssp585) | 1.029 | 1.176 ✗ | 1.025 |

**Where the data are, the chains agree on BOTH fluxes and disagree on the tightly-pinned NET;
where the data are not, the pattern flips.** The likelihood squeezes the net **14:1** (28.0 vs
391 Gt/yr, the same order as the documented 34:1) and that squeeze is *why* it fails — ESS drops
24× on the quantity constrained hardest.

⇒ **A flat ridge is fixed by reparameterising onto the ridge coordinate; a stiff direction is
fixed by proposals scaled to it.** Reparameterising here would be effort spent on the wrong
geometry.

---

## 4. ITEM 4 [3] — THE PRICE IN CM, AND HOW LOOSE IT IS

Deterministic monotone transport of one column onto each chain's own marginal, every other
column untouched. ENVELOPE = the range of the four arms' medians.

| cell | `antarctic_alpha` | | `ais_runoff_Ton` | |
|---|---|---|---|---|
| ssp245 @2100 | 5.26 cm | 14.9% | 0.15 cm | 0.4% |
| ssp245 @2150 | 15.20 cm | 15.9% | 0.37 cm | 0.4% |
| ssp245 @2300 | 21.19 cm | 7.5% | 0.64 cm | 0.2% |
| ssp585 @2100 | 8.28 cm | 16.4% | 0.18 cm | 0.3% |
| ssp585 @2150 | 18.61 cm | 19.6% | 0.41 cm | 0.4% |
| ssp585 @2300 | **57.22 cm** | **22.7%** | 1.50 cm | 0.6% |

**`ais_runoff_Ton` is RETIRED** — ≤0.6% of the band in all six cells. Its rank-4 propagation
contrast and its 0.2% envelope are not in tension: the contrast is the parameter's own leverage,
the envelope is how far the **chains disagree about it**, and its four medians span only 0.88
within-chain sd.

⚠ **α's 57.22 cm exceeds the entire correlation-respecting between-chain range of the
deliverable (37.25 cm) from all seventeen parameters at once, by 1.54×.** One parameter cannot
really be worth more than all of them jointly; the excess *is* the broken correlation. **Quote
§2's per-chain number for what the sampler costs and §4's for an upper bound.**

---

## 5. ITEM 4 [4] — THE HYPOTHESIS I FORMED AND KILLED, AND WHAT REPLACED IT

The one failing deliverable cell (ssp245 AIS @2100: R̂ 1.070 / ESS 38.4) and the one failing flux
quantity (anchored net: 1.069 / 43.6) matched on **both** diagnostics. I hypothesised they were
the same direction. **Refuted** — per-draw decile contrast **+0.026** of the spread. Two
independently slow directions.

*Matching R̂ and ESS is not evidence of a shared direction*: a shared direction is a **joint**
claim and needs the per-draw series, which is why the control arm now writes
`diag_ais_item4_perdraw_L14.csv`. Had it not been tested, the coincidence would have shipped as
a mechanism.

**What the test found instead is the more useful result.** By item 4's own criterion — fails R̂
*and* reaches the deliverable — the **anchored net mass balance** qualifies above both named
parameters:

| quantity | contrast / spread @ ssp585 2300 |
|---|---|
| **anchored net** | **+0.249** (Pearson +0.188, Spearman +0.155) |
| anchored discharge alone | +0.081 |
| anchored SMB alone | −0.065 |
| `ais_runoff_Ton` (propagation) | 0.167 |
| `antarctic_alpha` (propagation) | 0.156 |

The net carries **3.1× either flux separately** — it is the *combination* that reaches the band.

⚠ **Its sign is counterintuitive and I have no tested mechanism**: a *less* negative present-day
net goes with *more* 2300 SLR. At that cell the projection is fast-dynamics dominated, so a
shared-geometry route is plausible and untested. **Open question, not explained.**

**A fourth independent line on "the AIS band is a prior."** `ais_spread_is_lambda_prior` rested
on three legs (the calibrator's own comment, a 0.027-prior-sd displacement, KS 0.0141). This adds
a fourth from a different direction: **the 1979–2008 hindcast rate is nearly uncorrelated with
the projection it is meant to constrain** — contrast **+0.036** (ssp245), **−0.068** (ssp585).
⚠ NARROW: measured on the **1979–2008 rate window**, not the whole `S.ais` stream (1900–2018).
Widening it is cheap and worth doing.

---

## 6. ITEM 5 — THE HORIZON RE-PRICING

### 6.1 The scenario inversion is a 2300 property, not a scenario property

| param | ssp245 @2100 | @2150 | @2300 | ssp585 @2100 | @2150 | @2300 |
|---|---|---|---|---|---|---|
| `antarctic_temp_threshold` | **−0.68 (r1)** | −0.69 (r1) | −0.68 (r1) | **−0.48 (r2)** | −0.24 (r3) | **−0.07 (r10)** |
| `antarctic_lambda` | **+0.02 (r10)** | +0.05 (r7) | +0.56 (r3) | +0.71 (r1) | +0.90 (r1) | +0.92 (r1) |
| `ais_gmst_amp` | +0.44 (r2) | +0.61 (r2) | +0.67 (r2) | +0.48 (r3) | +0.37 (r2) | +0.30 (r2) |

`handoff_2026-08-24b` §1.1 read "rank 1 at ssp245, rank 10 at ssp585" as a **scenario** property.
It is a **2300** property: the ssp245/ssp585 contrast ratio is **1.42× at 2100, 2.92× at 2150,
9.71× at 2300**, and at 2100 the threshold is near the top in BOTH scenarios (r1 and r2). λ
mirrors it — rank 10 at ssp245 @2100, effectively absent at 2150 (+0.05), rank 3 only at 2300.

⇒ **One mechanism on both axes: the TIPPED FRACTION.** Where few draws have crossed, *whether* a
draw tips dominates; where nearly all have, *how fast* takes over. Scenario and horizon are two
ways of moving that fraction, and all six cells are monotone in it.
⇒ **The standing rule upgrades to "without its scenario AND ITS HORIZON".**

### 6.2 The λ prior's worth spans ~5800×, and no one statistic captures it

| cell | control median | band | median envelope | /band | spread envelope | /band |
|---|---|---|---|---|---|---|
| ssp245 @2100 | 5.58 | 35.44 | **0.06 cm** | **0.00** | 85.96 | **2.43** |
| ssp245 @2150 | 11.91 | 95.42 | 0.89 | 0.01 | 207.00 | 2.17 |
| ssp245 @2300 | 131.35 | 280.77 | 349.52 | 1.24 | 576.78 | 2.05 |
| ssp585 @2100 | 37.07 | 50.56 | 81.06 | 1.60 | 90.56 | 1.79 |
| ssp585 @2150 | 94.35 | 94.79 | 202.83 | 2.14 | 93.81 | 0.99 |
| ssp585 @2300 | 281.19 | 252.36 | **549.81 cm** | **2.18** | 103.38 | **0.41** |

The shipped **"2.18× the band"** is an **ssp585 @2300** number; the median envelope runs
**0.06 → 549.81 cm**, a factor of **~5800**.

⚠ **Median/spread trap, quantified.** At ssp245 @2100 the **median** envelope is **0.00× the
band** while the **spread** envelope is **2.43×** it, with the spread varying **13.3×** across
the λ support. **Reading λ's worth off the median there reports zero, and it is not zero.**
⚠ **The two envelopes move in OPPOSITE directions** with horizon at ssp585 (median 1.60 → 2.14 →
2.18 rising, spread 1.79 → 0.99 → 0.41 falling), while the ssp245 spread envelope is nearly
horizon-invariant (2.43 / 2.17 / 2.05) and its median envelope is not (0.00 → 0.01 → 1.24).
**Name the cell AND the statistic.**

### 6.3 A shipped ceiling was single-horizon

`handoff_2026-08-24c` §2.2 concluded *"Nothing exceeds 6% of a band or 10.3% of a median"*,
computed on the 2300 rows. Across all six cells:

* **The band half SURVIVES for what it was about** — the λ FORM arms (`lam_box`, `lam_full`)
  stay within **±4.8% of the median** and **×0.964–1.057 on the band** at every cell. The
  functional-form error is not where the uncertainty lives, at any horizon.
* **The median half does NOT survive** — at **ssp245 @2150 `tcr_full` moves the median +47.1%**
  (+5.61 cm) and `joint` +42.9%, 4.6× the quoted ceiling. Tcrit remains the largest form effect
  and it peaks at **2150**, a horizon nobody had looked at.

⚠ **Do not quote the 47.1% bare.** Its base is an **11.91 cm** median; the same +5.61 cm is only
**5.9% of that cell's 95.42 cm band** (`ratio_needs_its_base`). The claim is that the earlier
ceiling was single-horizon and does not generalise — **not** that a 47% effect was discovered.

---

## 7. NON-OBVIOUS STATE

* **`--maxrows=N` smoke mode reads from iteration 1 (pre-burn-in)** and writes to a `_SMOKE`
  filename. Its [RIDGE-CORR] numbers are meaningless (0.87 on 12 draws vs the real 0.70).
  Plumbing only, never a result. Same trap as `handoff_2026-08-24d` §4.
* **`--control-only` writes a `_CTRLONLY` suffix on purpose.** It produces a one-row arms table;
  writing that to the full run's filename would silently destroy the eight transport arms while
  leaving a file that still looks like the deliverable.
* **Pearson is the wrong statistic on ssp245 @2100** (bimodal tipped/not-tipped). The Julia
  `[SAME-Q]` block prints it as a **screen** only; the verdict is taken in the Python file on the
  decile contrast — the same statistic and normalisation the propagation ranking uses.
* The Python contrast script uses **interpolating quantiles**, matching the Julia `eq`. An
  integer-index quantile shifts the ssp245 net→2300 contrast by ~9% (19.81 vs 21.67 cm).
* **Chain reads are ~12 min**; judge progress by `%CPU`, not the log (Julia block-buffers).
  Poll with `pgrep -f "julia.*<script>"`, never the bare script name — it self-matches.
* **Both item-4 runs reproduced each other exactly** (gates 0.7031 / 0.6130, every arm median to
  the printed digit), so the transport path is deterministic — as designed.
* Every trap in `handoff_2026-08-24d` §4, `-24c` §4 and `-24b` §3 still applies.

---

## 8. OPEN, IN PRIORITY ORDER

**Marcus's 6 → 4 → 5 ordering is complete.** What remains, re-ranked:

1. **The target set's reconstruction mixing** (`2026-08-24d` §5 item 3). Components are
   calibrated on Frederikse 2020 and the total is scored on Dangendorf 2024, whose acceleration
   is 1.83× Frederikse's. **Until this is settled no curvature score means anything**, which
   blocks a whole class of work. Also settle the post-splice halving (component-sum curvature
   0.007189 over 1993–2018 → 0.003533 over 1993–2024, with `prep_recalib_targets_ext.py` holding
   LWS constant from 2019 by construction).
2. **NEW (§5): the anchored net's counterintuitive sign** at ssp585 @2300 — contrast 0.249 and
   unexplained. Cheap: the per-draw table is on disk and joins to the draws by index, so a
   shared-geometry route can be tested with no chain read.
3. **NEW (§5): widen the hindcast-vs-projection independence measurement** from the 1979–2008
   rate window to the whole `S.ais` 1900–2018 stream. If it holds there it is a fourth leg under
   "the AIS band is a prior"; if not, it was a window artefact.
4. **NEW (§6): re-read the other shipped Antarctic headlines at 2100/2150.** Item 5 found two
   single-horizon statements in one file. The transfer law and `dE[AIS]/dP` are already quoted
   per horizon, but the **`UNRESOLVED_AMPLIFICATION` arm's λ = 0.014280 (paleo pctile 86.3)** was
   chosen against 2300 behaviour and has not been checked for horizon sensitivity.
5. **The AIS observed driver** (`2026-08-24d` §5 item 4) — real but deprioritised; AIS is only
   10% of the total rate and the physically relevant driver is the ocean, not surface air.
6. **FrEDI linearity** (`2026-08-24d` §5 item 5) — do not publish dSC/dP as a durable coefficient.
7. **Marcus's prose** for module-memo §1 and §9, and the `2.0` tag decision.

**If a sampler effort is ever spent on Antarctica: target the net mass-balance direction with
proposal scaling. Not `antarctic_alpha`, not `ais_runoff_Ton`, and not reparameterisation.**

---

## 9. FILES AND COMMITS

**New (item 4):** `julia/diag_ais_item4_sampler.jl`,
`python/diag_ais_item4_perdraw_contrast.py`,
`outputs/diag_ais_item4_{deliverable,fluxes,arms,perdraw,contrast}_L14.csv`,
`outputs/log_item4_sampler_L14.txt`.
**New (item 5):** `python/diag_ais_item5_horizon_repricing.py`,
`outputs/diag_ais_item5_{ranking,envelope}_L14.csv`.
**Modified:** `CHANGELOG.md` (entries `2026-08-24k` and `2026-08-24l`).
**Memories:** `ais_item4_deliverable_ok`, `ais_stiff_not_flat`, `ais_horizon_reprice`, and
`rhat_denominator_forgives` (a working convention, promoted to the root index); `INDEX_slr.md`
Antarctica section and the `MEMORY.md` live-state line both updated.
**Commits:** `d8c49c8` (item 4), `0e5e033` (item 5), `fc6b5e9` (this note).
