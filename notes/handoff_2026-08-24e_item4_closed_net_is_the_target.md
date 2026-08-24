# Handoff — items 4 AND 5 are closed; the band survives both, and two shipped framings were wrong

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commit `d8c49c8`.
Written 2026-08-24, to be picked up cold. **Continues**
`handoff_2026-08-24d_curvature_resolved_ais_sampler_next.md`, whose §5 items **1 (ITEM 4)
and 2 (ITEM 5) are now BOTH CLOSED**. Everything in that handoff's §1–§4 stands unchanged;
its §5 items 3–6 survive and are re-ranked in §5 below. **Marcus's 6 → 4 → 5 ordering is
now complete.**

---

## 0. THE ONE-PARAGRAPH VERSION

**Marcus's 6 → 4 → 5 ordering is complete.** ITEM 4: **the Antarctic block's 9-of-17
convergence failure does not corrupt the deliverable.** The
projection itself converges in **11 of 12** scenario × component × horizon cells, including
**ssp585 AIS @2300 (R̂ 1.026)**, the cell that is 55% of the total and carries the whole λ
story. **`ais_runoff_Ton` is retired** — ≤0.6% of the band in every cell. `antarctic_alpha`
is worth up to 57.22 cm (22.7%), but that is an as-if-independent bound **measured to be
1.54× too large**. Two things came out that were not asked for. **The input–output
degeneracy is a STIFF direction, not a flat ridge** — where the data are, the chains agree
on both fluxes and disagree on the tightly-pinned net; where they are not, the pattern
flips — so the lever is proposal scaling, not reparameterisation. And **the direction that
qualifies on item 4's own criterion is neither named parameter**: it is the anchored net
mass balance, contrast **0.249** at ssp585 @2300 against their 0.167 and 0.156.
ITEM 5 then found that **two shipped framings were single-cell artefacts**: the
"rank 1 vs rank 10" scenario inversion **does not exist at 2100** (it is a 2300 property, and
one mechanism — the tipped fraction — drives both the scenario and the horizon axis), and the
λ prior's worth spans **~5800×** across the six cells, with its median and spread envelopes
moving in **opposite directions**.

---

## 1. WHAT WAS BUILT

`julia/diag_ais_item4_sampler.jl` — three tests on one chain read (~12 min read, ~6 min of
arms). `python/diag_ais_item4_perdraw_contrast.py` — the rank-safe follow-up.
Outputs: `outputs/diag_ais_item4_{deliverable,fluxes,arms,perdraw,contrast}_L14.csv`,
`outputs/log_item4_sampler_L14.txt`.

**Gates, all passed and all worth keeping:**
* **[IDENT]** the control arm reproduces `diag_ais_block_propagation_L14.csv` at rel
  **0.00e+00** on all six scenario × horizon cells — same draws, same kernel.
* **[SMB]** the anchored-window SMB lands **−0.23 σ** of the Rignot A5 target the
  calibrator itself anchors (1836.7 vs 1863.4 ± 118.1) ⇒ the flux extraction is reading
  the quantity the likelihood scored, not a lookalike.
* **[HIST-IDENT]** anchored-window fluxes are **bit-identical between the two scenarios**
  (rel 0.00e+00), as the shared historical forcing requires. Without this the "where the
  data are" leg of test [2] would be asserted rather than established.
* **[RIDGE-CORR]** max |corr| **0.703** (`antarctic_alpha`, with `ais_slope`) and **0.613**
  (`ais_runoff_Ton`, with `ais_gmst_amp`) — this is what makes test [3] a bound.

---

## 2. THE THREE ANSWERS

### 2.1 The deliverable converges — but read the caveat

11/12 cells pass at R̂ < 1.05. The one failure is **ssp245 AIS @2100 (R̂ 1.070)** and it
fails on **ESS 38.4**, not displacement: it carries the *smallest* between-chain median
range in the table (1.40 cm = 0.116 within-chain sd).

⚠ **R̂ passes at ssp585 @2300 because the band is WIDE, not because the chains agree** —
their medians span **37.25 cm = 13.2% of the 281 cm median**. Carry the median range in cm
beside any R̂ verdict on this band. Generalised in memory `rhat_denominator_forgives`.

### 2.2 Stiff, not flat

| window | smb | discharge | **net** |
|---|---|---|---|
| anchored 1979–2008 | 1.012 (ESS 923) | 1.008 (ESS 1027) | **1.069 (ESS 43)** ✗ |
| unobserved 2281–2300 (ssp245) | 1.070 ✗ | 1.073 ✗ | 1.018 |
| unobserved 2281–2300 (ssp585) | 1.029 | 1.176 ✗ | 1.025 |

The likelihood squeezes the net **14:1** (28.0 vs 391 Gt/yr, the same order as the
calibrator's documented 34:1) and that squeeze is *why* it fails — ESS drops 24× on the
quantity constrained hardest. **A flat ridge is fixed by reparameterising onto the ridge
coordinate; a stiff direction is fixed by proposals scaled to it.** Reparameterising here
would be effort spent on the wrong geometry.

### 2.3 The price, and what it is worth

| cell | `antarctic_alpha` | `ais_runoff_Ton` |
|---|---|---|
| ssp245 @2300 | 21.19 cm (7.5%) | 0.64 cm (0.2%) |
| ssp585 @2300 | **57.22 cm (22.7%)** | 1.50 cm (0.6%) |

`ais_runoff_Ton` **retired**. Its rank-4 propagation contrast and its 0.2% envelope are not
in tension: the contrast is the parameter's own leverage, the envelope is how far the
*chains disagree about it*, and its four medians span only 0.88 within-chain sd.

⚠ α's 57.22 cm **exceeds the entire correlation-respecting between-chain range of the
deliverable (37.25 cm) from all seventeen parameters at once, by 1.54×.** One parameter
cannot really be worth more than all of them jointly; the excess *is* the broken
correlation. **Quote §2.1's per-chain number for the cost and §2.3's for an upper bound.**

---

## 3. THE HYPOTHESIS I FORMED AND KILLED — AND WHAT REPLACED IT

The one failing deliverable cell (ssp245 AIS @2100: R̂ 1.070 / ESS 38.4) and the one failing
flux quantity (anchored net: 1.069 / 43.6) matched on **both** diagnostics. I hypothesised
they were the same direction. **Refuted** — per-draw decile contrast **+0.026** of the
spread. Two independently slow directions. *Matching R̂ and ESS is not evidence of a shared
direction*; a shared direction is a joint claim and needs the per-draw series, which is why
the control arm now writes `diag_ais_item4_perdraw_L14.csv`.

**What the test found instead is the more useful result.** By item 4's own criterion — fails
R̂ *and* reaches the deliverable — the **anchored net mass balance** qualifies above both
named parameters:

| quantity | contrast / spread @ ssp585 2300 |
|---|---|
| **anchored net** | **+0.249** (Pearson +0.188, Spearman +0.155) |
| anchored discharge alone | +0.081 |
| anchored SMB alone | −0.065 |
| `ais_runoff_Ton` (propagation) | 0.167 |
| `antarctic_alpha` (propagation) | 0.156 |

The net carries **3.1× either flux separately** — it is the *combination* that reaches the
band. ⚠ **Its sign is counterintuitive and I have no tested mechanism**: a *less* negative
present-day net goes with *more* 2300 SLR. At that cell the projection is fast-dynamics
dominated, so a shared-geometry route is plausible and untested. **Open question, not
explained.**

**A fourth independent line on "the AIS band is a prior."** `ais_spread_is_lambda_prior`
rested on three legs (the calibrator's comment, a 0.027-prior-sd displacement, KS 0.0141).
This adds a fourth from a different direction: **the 1979–2008 hindcast rate is nearly
uncorrelated with the projection it is meant to constrain** — contrast +0.036 (ssp245),
−0.068 (ssp585). ⚠ NARROW: measured on the 1979–2008 rate window, **not** the whole `S.ais`
stream, which runs 1900–2018. Widening that measurement is cheap and worth doing.

---

## 3b. ITEM 5 — THE HORIZON RE-PRICING (commit `0e5e033`)

`python/diag_ais_item5_horizon_repricing.py`,
`outputs/diag_ais_item5_{ranking,envelope}_L14.csv`. **No chains read** — both source CSVs
already carried all three horizons, so this was post-processing.

### 3b.1 The scenario inversion is a 2300 property, not a scenario property

| param | ssp245 @2100 | @2150 | @2300 | ssp585 @2100 | @2150 | @2300 |
|---|---|---|---|---|---|---|
| `antarctic_temp_threshold` | **−0.68 (r1)** | −0.69 (r1) | −0.68 (r1) | **−0.48 (r2)** | −0.24 (r3) | **−0.07 (r10)** |
| `antarctic_lambda` | **+0.02 (r10)** | +0.05 (r7) | +0.56 (r3) | +0.71 (r1) | +0.90 (r1) | +0.92 (r1) |
| `ais_gmst_amp` | +0.44 (r2) | +0.61 (r2) | +0.67 (r2) | +0.48 (r3) | +0.37 (r2) | +0.30 (r2) |

`handoff_2026-08-24b` §1.1 read "rank 1 at ssp245, rank 10 at ssp585" as a **scenario**
property. It is a **2300** property: the ssp245/ssp585 contrast ratio is **1.42× at 2100,
2.92× at 2150, 9.71× at 2300**, and at 2100 the threshold is near the top in BOTH scenarios.
λ mirrors it — rank 10 at ssp245 @2100, effectively absent at 2150 (+0.05), rank 3 at 2300.

⇒ **One mechanism on both axes: the tipped fraction** (whether-vs-how-fast). Scenario and
horizon are two ways of moving it; all six cells are monotone in it.
⇒ **The standing rule upgrades to "without its scenario AND ITS HORIZON".**

### 3b.2 The λ prior's worth spans ~5800×, and no one statistic captures it

| cell | median envelope | /band | spread envelope | /band |
|---|---|---|---|---|
| ssp245 @2100 | **0.06 cm** | **0.00** | 85.96 | **2.43** |
| ssp245 @2300 | 349.52 | 1.24 | 576.78 | 2.05 |
| ssp585 @2150 | 202.83 | 2.14 | 93.81 | 0.99 |
| ssp585 @2300 | **549.81 cm** | **2.18** | 103.38 | **0.41** |

The shipped **"2.18× the band"** is an **ssp585 @2300** number.

⚠ **Median/spread trap, quantified.** At ssp245 @2100 the median envelope is **0.00× the
band** while the spread envelope is **2.43×** it (spread varies 13.3× across the λ support).
**Reading λ off the median there reports zero and it is not zero.**
⚠ **The two envelopes move in OPPOSITE directions** with horizon at ssp585 (median 1.60 →
2.18 rising, spread 1.79 → 0.41 falling), and the ssp245 spread envelope is nearly
horizon-invariant while its median envelope is not. **Name the cell AND the statistic.**

### 3b.3 A shipped ceiling was single-horizon

`handoff_2026-08-24c` §2.2: *"Nothing exceeds 6% of a band or 10.3% of a median"* — computed
on the 2300 rows. Across all six cells: **the band half SURVIVES** for what it was about (the
λ form arms stay within ±4.8% of the median, ×0.964–1.057 on the band, everywhere). **The
median half does not**: at ssp245 @2150 `tcr_full` moves the median **+47.1%**, `joint`
+42.9%. Tcrit remains the largest form effect and peaks at **2150**, a horizon nobody had
looked at.

⚠ **Do not quote the 47.1% bare.** Its base is an **11.91 cm** median; the same +5.61 cm is
**5.9% of that cell's 95.42 cm band** (`ratio_needs_its_base`). The claim is that the ceiling
was single-horizon, **not** that a 47% effect was found.

---

## 4. NON-OBVIOUS STATE

* **`--maxrows=N` smoke mode reads from iteration 1 (pre-burn-in)** and writes to a `_SMOKE`
  filename. Its [RIDGE-CORR] numbers are meaningless (0.87 vs the real 0.70 on 12 draws).
  Plumbing only, never a result. Same trap as `handoff_2026-08-24d` §4.
* **`--control-only` writes a `_CTRLONLY` suffix on purpose.** It produces a one-row arms
  table; writing that to the full run's filename would silently destroy the eight transport
  arms while leaving a file that still looks like the deliverable.
* **Pearson is the wrong statistic on ssp245 @2100** (bimodal tipped/not-tipped). The Julia
  `[SAME-Q]` block prints it as a *screen* only; the verdict is taken in the Python file on
  the decile contrast — same statistic and normalisation as the propagation ranking.
* The Python contrast script uses **interpolating quantiles**, matching the Julia `eq`. An
  integer-index quantile shifts the ssp245 net→2300 contrast by ~9% (19.81 vs 21.67 cm).
* **Chain reads are ~12 min**; judge progress by `%CPU`, not the log (Julia block-buffers).
  Poll with `pgrep -f "julia.*<script>"`, never the bare script name — it self-matches.
* Every trap in `handoff_2026-08-24d` §4, `-24c` §4 and `-24b` §3 still applies.

---

## 5. OPEN, IN PRIORITY ORDER

**Marcus's 6 → 4 → 5 ordering is complete.** What remains, re-ranked:

1. **The target set's reconstruction mixing** (`2026-08-24d` §5 item 3). The components are
   calibrated on Frederikse 2020 and the total is scored on Dangendorf 2024, whose
   acceleration is 1.83× Frederikse's. **Until this is settled no curvature score means
   anything**, which blocks a whole class of work. Also settle the post-splice halving
   (component-sum curvature 0.007189 over 1993–2018 → 0.003533 over 1993–2024, with
   `prep_recalib_targets_ext.py` holding LWS constant from 2019 by construction).
2. **NEW (§3): the anchored net's counterintuitive sign** at ssp585 @2300 — a *less* negative
   present-day net going with *more* 2300 SLR, contrast 0.249 and unexplained. Cheap: the
   per-draw table is on disk and joins to the draws by index, so a shared-geometry route can
   be tested without a chain read.
3. **NEW (§3): widen the hindcast-vs-projection independence measurement** from the 1979–2008
   rate window to the whole `S.ais` 1900–2018 stream. If it holds there, it is a fourth leg
   under "the AIS band is a prior" rather than a window artefact.
4. **NEW (§3b): re-read the other shipped Antarctic headlines at 2100/2150.** Item 5 found two
   single-horizon statements in one file. The transfer law
   `AIS₂₃₀₀(ssp585) = 70.67 + 19752·λ` and `P_UNRES`'s `dE[AIS]/dP` are both quoted per
   horizon already, but the **`UNRESOLVED_AMPLIFICATION` arm's λ = 0.014280 (paleo pctile
   86.3)** was chosen against 2300 behaviour and has not been checked for horizon sensitivity.
5. **The AIS observed driver** (`2026-08-24d` §5 item 4) — real but deprioritised; AIS is only
   10% of the total rate and the physically relevant driver is the ocean, not surface air.
6. **FrEDI linearity** (`2026-08-24d` §5 item 5) — do not publish dSC/dP as a durable coefficient.
7. **Marcus's prose** for module-memo §1 and §9, and the `2.0` tag decision.

**If a sampler effort is ever spent on Antarctica: target the net mass-balance direction with
proposal scaling. Not `antarctic_alpha`, not `ais_runoff_Ton`, and not reparameterisation.**

## 6. FILES

**New (item 4):** `julia/diag_ais_item4_sampler.jl`,
`python/diag_ais_item4_perdraw_contrast.py`,
`outputs/diag_ais_item4_{deliverable,fluxes,arms,perdraw,contrast}_L14.csv`,
`outputs/log_item4_sampler_L14.txt`.
**New (item 5):** `python/diag_ais_item5_horizon_repricing.py`,
`outputs/diag_ais_item5_{ranking,envelope}_L14.csv`.
**Modified:** `CHANGELOG.md` (2026-08-24k and 2026-08-24l).
**Memories:** `ais_item4_deliverable_ok`, `ais_stiff_not_flat`, `ais_horizon_reprice`,
`rhat_denominator_forgives` (a working convention, promoted to the root index);
`INDEX_slr.md` Antarctica section and `MEMORY.md` live-state line both updated.
**Commits:** `d8c49c8` (item 4), `6e64c5e` (this handoff), `0e5e033` (item 5).
