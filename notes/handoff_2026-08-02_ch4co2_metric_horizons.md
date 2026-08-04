# Handoff 2026-08-02 — CH4-vs-CO2 SLR marginals, the metric message, and pulse-relative horizons

> **⚠️ CONTINUED BY `notes/handoff_2026-08-03_metric_table_and_fossil.md` — read that one first.**
> It is the authoritative current state: it carries the same completed §0 table plus the fossil-CH4
> arm, the TE-only crossover result, and the resolution of the research-plan novelty claim. The §0
> table below is retained because it is where the table was first assembled, and because it was
> computed INDEPENDENTLY (different code path, ad-hoc vs `python/metric_horizon_table.py`) and agrees
> to every reported digit — a genuine cross-validation, not a copy. Prefer the 08-03 note for anything
> beyond that.

**Self-contained pickup:** this + `CLAUDE.md` + memories `project_ch4_vs_co2_slr_marginals_brickam`,
`project_fair_brick_coupling_joint_calib`, `feedback_output_provenance_labels`.
Supersedes the Monday-launch plan in `handoff_2026-08-01_brick_fair_consistency.md` (see its addendum).

---

## 0. THE KEY MESSAGE (Marcus 2026-08-02) — frame everything around this

**CH4's sea-level impact is much longer-lasting than its temperature impact, and that is what drives the
relative CO2/CH4 comparison.** Concretely: an SLR-based equivalence metric values CH4 **above** its
GWP-100, while a GTP-style endpoint-temperature metric values it **well below** GWP-100.

The component attribution (AIS vs TE vs GIS vs GSIC) is a **necessary intermediate step, NOT part of the
key message.** An earlier draft of this work over-elevated the component split into a headline — do not
repeat that. (It is also empirically weak: both gases are AIS-led with near-identical shares; see §3.)

**COMPLETE (pulse-relative horizons landed 2026-08-03).** All per GWP-100-equivalent tonne
(CO2 ≡ 1.0 by construction); biogenic CH4, SSP2-4.5, BRICK-AM sub-annual pulse MEANS; temperature
ratios are FaIR ensemble means from the pulse npz:

| years after 2030 pulse | temperature (GTP-style) | total SLR | SLR ÷ temperature |
|---|---|---|---|
| 20 (2050)  | 3.70 | 4.63 | 1.25× |
| 70 (2100)  | 0.79 | 2.24 | 2.82× |
| **100 (2130)** | **0.52** | **1.68** | **3.23×** |
| 120 (2150) | 0.45 | 1.45 | 3.23× |
| 150 (2180) | 0.38 | 1.22 | 3.18× |
| 270 (2300) | 0.24 | 0.79 | 3.34× |

**At the GWP-100 horizon itself, an SLR-based metric values CH4 at 1.68× its GWP-100 while a
GTP-style endpoint-temperature metric values it at 0.52×** — the persistence gap Marcus identified.
At 120 yr the SLR figure is 1.45, i.e. "almost 1.5× the 100-year GWP", as stated.

**The SLR ÷ temperature column is GWP-BASIS-INVARIANT** — it is a ratio of ratios, so any CO2e metric
factor cancels exactly (verified: the GWP-free per-actual-tonne calculation gives the same 3.23 at
100 yr; switching GWP-100→GWP-20 changes both columns but not their ratio). So "CH4's sea-level
signature outlasts its temperature signature by ~3.2× from 100 yr onward, and the gap widens with
horizon" is a metric-choice-free physical statement — the strongest form of the key message. The
individual 1.68 / 0.52 figures DO depend on GWP-100 = 27 and must be labeled with that basis.

Stochastic vs deterministic basis agree to ≤0.01 on every ratio. The 2100/2150/2300 values reproduce
the earlier fixed-horizon run exactly (implicit regression check on the horizon refactor).

---

## 1. State of the pipeline (all local; no Torch run needed or pending)

Commits on `brick-mengel-vnext`: `4debe87` (pulse arm + fast engine) → `dafb300` (CO2 production) →
`08c6345` (provenance) → `5b7a9c3` (CH4 arm) → this handoff's commit.

- **`julia/weight_and_project_brick_fair.jl`** is the single driver for levels bands AND pulse marginals.
  Flags: `--pulse=off|on|zero`, `--basis=`, `--pulse-gt=`, `--pulse-unit=`, `--engine=fast|legacy`,
  `--out-tag=`, and NEW `--horizons=` / `--comp-years=`.
- **Fast engine is default and load-bearing.** `update_param!` forces a ~14 ms Mimi rebuild per run on
  this 451-yr model (integration is ~2 ms); the legacy path made a full run ~12–14 h — the originally
  staged Torch job would have TIMED OUT with nothing written. Fast path mutates the built instance in
  place: 0.8–1.3 ms/run, validated byte-identical to legacy at smoke and 24k-pair scale.
- **`scripts/run_subannual.sh`** applies the sub-annual DAIS patch and **guarantees restore via an EXIT
  trap** (success, failure, or interrupt). ALWAYS use it — the patch overwrites a file in the SHARED
  MimiBRICK depot, so a crash mid-run would silently give every later BRICK job different physics. It
  resolves the depot from the MimiBRICK that `julia_v2` actually loads (several slugs are installed).
- **Provenance** (`julia/run_provenance.jl`): every run writes `wong_cond_runmeta<sfx>.csv` (29 fields)
  and stamps 8 `prov_*` columns into the bands CSVs. Auto-detected, not hardcoded: DAIS integrator read
  off the loaded depot, posterior + forcing files content-hashed, git commit with dirty flag.
  `julia/retrofit_provenance.jl` covers the four pre-wiring CO2 runs; those sidecars are explicitly
  marked `provenance_source = RECONSTRUCTED … NOT emitted by the run`.

## 2. Settled results (Marcus-accepted)

- **Independent pipeline is the production basis** (decision 2026-08-02). The conditional importance
  weighting is a documented consistency check, not a pipeline change: coupling is immaterial to LEVELS
  (total@2100 COUPLED 46.68 vs INDEP 46.38 cm) and to the PULSE MARGINAL (mean ratio 1.003–1.009, TE
  1.000, tip fraction 23.31→23.41%). The "coupling may matter more on the marginal" conjecture: **NO.**
- **Reporting protocol:** MEAN, plus a mode decomposition in place of the median. The pooled median is
  sample-fragile (a large tip-advance mode puts the 50th percentile in a bimodal density gap; early-841
  draws gave 1.06e-2 vs full-ensemble 5.8e-3 at IDENTICAL tip fractions). MEANS need no classifier.
- **Sub-annual patch is mandatory for quotable pulse numbers.** Annual-step medians are tip-frozen.
  Validation: cross-product sub-annual mean @2100 = 1.469e-2 cm/GtCO2 vs the July artifact's 1:1-paired
  1.498e-2 (within 2%); basis-consistent to 0.05%.

## 3. CH4 arm — results and the flag on the novelty claim

FaIR CH4 biogenic **1 Tg @2030**, SSP2-4.5, 841 cfg, both bases. Pre-pulse marginal exactly 0.0.
CH4 and CO2 arms share the same baseline (2.5e-12 cm through BRICK; zero tip-classifier flips) → cleanly
paired. MEAN total-SLR marginal, sub-annual:

| horizon | CO2 cm/GtCO2 | CH4 cm/Tg | CH4 per GtCO2e | CH4/CO2 |
|---|---|---|---|---|
| 2100 | 1.470e-2 | 8.893e-4 | 3.294e-2 | 2.24 |
| 2150 | 2.507e-2 | 9.782e-4 | 3.623e-2 | 1.45 |
| 2300 | 4.956e-2 | 1.057e-3 | 3.914e-2 | 0.79 |

Reproduces the research plan's placeholder crossover on a DIFFERENT posterior (BRICK-AM vs pre-FM
Mengel) and DIFFERENT backbone (SSP2-4.5 vs RFF-SP); stochastic vs deterministic agree to 0.04–1.7%.

**FLAG — the plan's "CH4-TE-led vs CO2-AIS-led split" (§1 contribution 1) is NOT supported.** Both gases
are AIS-led with near-identical shares (@2100 AIS 76% CH4 / 75% CO2; TE 17% / 19%) and the per-gas ratio
is near-uniform across components (ais 2.26, gsic 2.66, gis 2.59, te 2.05). The genuine differential is
the DECLINE RATE (TE 2.05→0.53 by 2300; AIS 2.26→0.82). Per §0 this is a supporting detail, not a
headline — but the written novelty claim needs rewording or dropping. (SSP2-4.5 only; RFF-SP untested.)

## 4. Open methodological choices (do NOT silently resolve)

1. **Tip-classifier threshold for the mode decomposition.** The documented baseline-AIS@2100 > 20 cm
   classifier (mimibrick-quirks item 11, ~5% on LHS-10k) selects **37.6%** on BRICK-AM extA108 — amp 1.08
   puts far more mass near tipping (baseline AIS p50 6.99 / p75 32.50 cm, no razor-sharp separator).
   MEANS are unaffected. Needs a re-tuned or differently-derived threshold.
2. **Headline basis** — stochastic vs `_nonoise_flatsolar`. They agree on the MEAN; they differ on tip
   fraction (23% vs 33%), so the decomposition components are basis-dependent and must be labeled.
   Suggested (not decided): deterministic for cross-model panels, stochastic for the RFF-SP band.
3. **GWP basis** for the CO2e framing (20 vs 100, biogenic 27 vs fossil 29.8) — per the plan, report as
   a first-class function, not a footnote.

## 5. DONE — pulse-relative horizons (was in flight; completed 2026-08-03)

The paper's key variable is **years since the emission pulse** (Marcus's plan note: 100 and 150 yr from
the emission point, consistent with GWP-100 framing), not calendar 2100/2150. With a 2030 pulse that is
**2130 / 2180**, and the 120-yr point is 2150. The driver's horizons were fixed at 2050/2100/2150/2300,
so the §0 table's 100- and 150-yr SLR cells are missing.

Launched: 4 arms (CO2/CH4 × stochastic/deterministic), `--horizons=2050,2100,2130,2150,2180,2300
--comp-years=2130,2150,2180`, `--out-tag=_pr`, under `scripts/run_subannual.sh`, ~3 h total.
**To re-launch if it did not finish** (scratchpad script is session-local — reconstruct it):

```bash
scripts/run_subannual.sh julia --project=julia_v2 julia/weight_and_project_brick_fair.jl \
  2000 2026 --amp-mu=1.08 --amp-sigma=0.15 --draws=2000 --configs=all --pulse=on --out-tag=_pr \
  --horizons=2050,2100,2130,2150,2180,2300 --comp-years=2130,2150,2180
```
(then repeat with `--basis=_ch4bio1tg --pulse-gt=1 --pulse-unit="Tg CH4"`, and the two
`_nonoise_flatsolar` variants.) Outputs: `wong_cond_pulse_{bands,pairs}_*_pr.csv` + runmeta sidecars.

**BUG FOUND AND FIXED while wiring this (2026-08-02).** The metric-packing offset was hardcoded
`b = 4 + 4*(ci-1)` (the old horizon count) instead of `length(HORIZONS)`. With >4 horizons the component
writes clobbered horizon slots and left the tail of `met` uninitialized → NaN. **Caught by the
zero-pulse gate**, which is the argument for running it after every driver change. **No prior result is
affected**: with 4 horizons the expressions are identical, and a default-horizon re-run byte-compares
0.0 against the original pre-change staged reference. No quarantine needed.

## 5b. PARALLEL-SESSION WORK — reconcile before citing (noted 2026-08-04)

Work continued in parallel and is **already committed and validated** (`aab89fd`, `ea38edc`,
`bc07ada`, and handoff `notes/handoff_2026-08-03_metric_table_and_fossil.md`). Superseding what an
earlier draft of this section speculated:
- **Fossil-CH4 arms are complete on both bases, with the shared-baseline gate verified end-to-end
  through BRICK** (`ea38edc`, `bc07ada`) — not unvalidated output. Use the 08-03 handoff for them.
- **A FaIR two-pass concentration leak** was found and FIXED (memory
  `project_fair_twopass_concentration_leak`: `initialise()` sets timebound 0 only; fossil BASELINE off
  by 1.07e-2 °C; marginal impact 0.02%). Specific to the `--fossil` two-pass path, so the biogenic
  numbers in §0/§3 are unaffected.
- **ARG-PRECEDENCE TRAP (now in the driver header):** `_arg` is `findfirst`, so the FIRST occurrence of
  a flag wins and later repeats are SILENTLY ignored. Never compose commands as `"$BASE $OVERRIDES"`.
  State every flag exactly once per command line. This turned an intended 3-config smoke into a full
  841×2000 job on 2026-08-03.
- **Table producer:** `python/metric_horizon_table.py` is the maintained artifact (auto-discovers
  horizons, `--ch4=bio|foss`, emits all GWP bases). Use it rather than ad-hoc recomputation.

## 6. Next steps, in order

1. ~~Fill the §0 table's 100/150-yr SLR cells~~ **DONE** — §0 is complete, and the GWP-invariant
   SLR÷temperature column is the headline-ready form. Next is turning §0 into the paper's figure/table.
2. Resolve §4.1 (tip classifier) and §4.2 (headline basis) with Marcus.
3. Reword or drop the §3 component-split novelty claim in the research plan.
4. **Fossil-CH4 arm** — `fairtable7_v145_pulse.py --specie ch4 --fossil` (time-distributed oxidation CO2
   companion), then the same BRICK driver. Note the plan's doc-vs-lock split: MAGICC arm is
   superposition; the FaIR→BRICK reference arm was specified as a REAL time-distributed run.
5. **RFF-SP backbone** for the gas headline (SSP2-4.5 is the cross-model panel backbone), and the
   **CH4 scenario-sensitivity gate** the plan requires — RFF under-projects CH4 (obs ≥ p95), so the CH4
   marginal must be tested on an obs-anchored/high-CH4 backbone before the RFF CH4 baseline is trusted.
6. Torch is OPTIONAL (cross-check only). It is NOT a git repo there, has only the Aug-1 drivers, only 2
   of the wide files, and no `julia/patches/` — an rsync of the repo + the pulse wide files is the sync
   path. If the patch is ever used there, do it with a job-local depot copy, never on the shared depot.
