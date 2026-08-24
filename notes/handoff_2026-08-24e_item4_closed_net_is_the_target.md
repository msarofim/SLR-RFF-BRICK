# Handoff — item 4 is closed, the band survives it, and the sampler target is neither parameter

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commit `d8c49c8`.
Written 2026-08-24, to be picked up cold. **Continues**
`handoff_2026-08-24d_curvature_resolved_ais_sampler_next.md`, whose §5 item **1 (ITEM 4)
is now CLOSED**. Everything in that handoff's §1–§4 stands unchanged; its §5 items 2–6
are untouched and are re-listed in §5 below.

---

## 0. THE ONE-PARAGRAPH VERSION

**The Antarctic block's 9-of-17 convergence failure does not corrupt the deliverable.** The
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

1. **ITEM 5 — re-price at 2100 / 2150.** Unchanged from `2026-08-24d` §5 item 2, and now
   the top item. The ranking already differs at 2100 and the λ-inert-median finding says the
   horizon caveat is real and compounds with the scenario one.
2. **The target set's reconstruction mixing** (`2026-08-24d` §5 item 3) — score like against
   like, and settle the post-splice halving. Until then no curvature score means anything.
3. **NEW, from §3: the anchored net's counterintuitive sign at ssp585 @2300.** Cheap to
   probe — the per-draw table is on disk and carries the geometry columns' draws by index.
4. **NEW, from §3: widen the hindcast-vs-projection independence measurement** from the
   1979–2008 rate window to the whole `S.ais` 1900–2018 stream.
5. **The AIS observed driver** (`2026-08-24d` §5 item 4) — deprioritised, still real; AIS is
   only 10% of the total rate and the physically relevant driver is the ocean, not surface air.
6. **FrEDI linearity** (`2026-08-24d` §5 item 5) — do not publish dSC/dP as a durable coefficient.
7. **Marcus's prose** for module-memo §1 and §9, and the `2.0` tag decision.

**If a sampler effort is ever spent on Antarctica: target the net mass-balance direction
with proposal scaling. Not `antarctic_alpha`, not `ais_runoff_Ton`, and not
reparameterisation.**

---

## 6. FILES

**New:** `julia/diag_ais_item4_sampler.jl`, `python/diag_ais_item4_perdraw_contrast.py`,
`outputs/diag_ais_item4_{deliverable,fluxes,arms,perdraw,contrast}_L14.csv`,
`outputs/log_item4_sampler_L14.txt`. **Modified:** `CHANGELOG.md` (2026-08-24k).
**Memories:** `ais_item4_deliverable_ok`, `ais_stiff_not_flat`, `rhat_denominator_forgives`
(a working convention, promoted to the root index); `INDEX_slr.md` Antarctica section and
`MEMORY.md` live-state line both updated.
