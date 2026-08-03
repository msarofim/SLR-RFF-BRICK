# Handoff 2026-08-03 — headline metric table complete; fossil-CH4 bug found and fixed

**Self-contained pickup:** this + `CLAUDE.md` + memories
`project_ch4co2_slr_vs_temp_metric_table`, `project_fair_twopass_concentration_leak`,
`project_ch4_vs_co2_slr_marginals_brickam`.
Continues `handoff_2026-08-02_ch4co2_metric_horizons.md`; its §5 (in-flight) has landed.

---

## 0. THE HEADLINE TABLE IS COMPLETE

The §0 table of the 2026-08-02 handoff had two empty SLR cells (100 and 150 yr). Filled:

| yr after pulse | calendar | temperature (GTP-style) | total SLR | SLR ÷ temperature |
|---|---|---|---|---|
| 20 | 2050 | 3.70 | 4.63 | 1.25× |
| 70 | 2100 | 0.79 | 2.24 | 2.82× |
| **100** | **2130** | **0.52** | **1.68** | **3.23×** |
| 120 | 2150 | 0.45 | 1.45 | 3.23× |
| **150** | **2180** | **0.38** | **1.22** | **3.18×** |
| 270 | 2300 | 0.24 | 0.79 | 3.34× |

Read: at the GWP-100-matched **100-yr** horizon an SLR metric puts CH₄ at **1.68×** its
GWP-100 while an endpoint-temperature metric puts it at **0.52×**.

**Two framing points that are new and load-bearing:**

1. **The divergence OPENS with horizon** — 1.25× at 20 yr, saturating near 3.2× from 100 yr
   on. It is not a constant offset between the metrics, and the 20-yr row is worth keeping
   in the paper precisely because it shows the gap emerging.
2. **The SLR÷temperature column is GWP-INVARIANT** — the basis cancels in the ratio. So the
   headline claim does **not** depend on the unresolved GWP-basis choice (§4.3 of the prior
   handoff); that choice rescales both metrics identically. This defuses the "artifact of
   your metric choice" objection for the headline, though not for the crossover *level*.

Producer: `python/metric_horizon_table.py` — forms both metrics identically (ensemble MEAN
marginal per GWP-100-eq tonne, CO₂ ≡ 1.0 by construction), auto-discovers horizons from the
pairs header, `--ch4=bio|foss` sets SLR basis + FaIR npz stem + headline GWP together.
Outputs `outputs/metric_horizon_table_bio_pr.{csv,md}` (all GWP bases as columns).

**Regression PASS:** at the four horizons the earlier `_subann` run also covers, the
6-horizon `_pr` run is **bit-identical** (worst relative difference 0.00e+00) — the
2026-08-02 metric-packing fix perturbs nothing.

## 1. Research-plan novelty claim: one example refuted, one confirmed

Plan §1 contribution 1 offered two candidate "demonstrated consequences" of component
resolution. A `CLAUDE NOTE` is now inline at the claim (not a rewrite — wording is yours).

- **REFUTED — "CH₄-TE-led vs CO₂-AIS-led split".** Both gases are AIS-led with
  near-identical shares and the small difference runs *opposite* to the claim (AIS @2130
  CO₂ 78.8% / CH₄ 79.6%; TE 15.8% / 14.1%). The real per-gas differential is the decline
  rate with horizon.
- **CONFIRMED — "crossover horizon shifts vs a thermosteric-only estimate."** A TE-only
  calculation gives 0.84–0.89× the full-SLR metric and crosses parity **~57 yr earlier**:
  TE-only ~2184 vs full SLR ~2241. This is the stronger claim anyway — it is a
  *demonstrated consequence*, the bar that paragraph itself sets.

Caveats: both crossovers are interpolated between bracketing horizons (the 2180–2300
segment is 120 yr wide) — treat the levels as ±a decade or two and the **~57 yr shift** as
the robust quantity. **Do not extrapolate off the short 2150→2180 segment**: the metric is
convex in horizon and that gives ~2208, ~33 yr too early. SSP2-4.5 only; RFF-SP untested.

`te@2300` was spliced from the `_subann` runs (the `_pr` run's `--comp-years` were
2130/2150/2180). Legitimate because the runs are bit-identical at shared horizons, but
**future runs should include 2300 in `--comp-years`** so no splice is needed.

## 2. Fossil-CH4 arm: a real bug, found before it contaminated anything

The fossil arm could not simply be run — `--fossil` is the only **two-pass** FaIR path and
it was corrupting its own baseline.

- **Bug:** `_init_state()` was built from `fair.interface.initialise()` calls, and
  `initialise()` writes the **first timebound only** (`fill(var[0, ...], value)`). Timebounds
  1…N of `f.concentration` kept pass-1 values and FaIR read some back, so pass 2 was not the
  same experiment as a single pass.
- **Ablation** (`FaIRtoFrEDI/diag_fossil_twopass_state.py`, T4 — re-dirty one array at a
  time): `concentration` is the **sole** leaking array. `emissions`, `forcing`,
  `gas_partitions`, `temperature`, `cumulative_emissions`, `airborne_emissions` are all
  harmless. Fix = clear the whole concentration array to NaN, then re-initialise timebound 0.
- **Symptom:** the fossil arm's *baseline* — untouched by the pulse — sat up to **1.07e-2 °C**
  off every other arm's. Every other arm shares a bit-identical baseline, and the CH₄-vs-CO₂
  comparison rests on that.
- **Impact bound: the marginal moved only 0.02–0.04%** (max 6.4e-08 °C) because the leak
  shifts both scenarios together. The one downstream consumer (the FaIR-vs-MAGICC pulse
  figure) was **not wrong in any reported respect**. What broke was the shared-baseline
  property.
- Pre-fix outputs **quarantined, not deleted**, at
  `FaIRtoFrEDI/fair_outputs/quarantine/20260803_fossil_twopass_concentration_leak/` (+README).
  General lesson added as **`fair-quirks` item 13**, including the gate that catches the
  class: assert `np.array_equal(new["temp_base"], canonical["temp_base"])` across arms.

New canonical fossil arms, both passing the gates (baseline bit-identical to the matching
biogenic arm, pre-pulse marginal exactly 0.0):
`fair_ensemble_v145_ssp245_pulsech4foss_1tg_2030{,_nonoise_flatsolar}.npz`.
Fossil ÷ biogenic marginal: 1.018 @2050 → 1.128 @2100 → 1.227 @2150 → 1.429 @2300.
Wide files `_ch4foss1tg{,_nonoise_flatsolar}` built; baselines byte-identical to the CO₂ and
CH₄-biogenic wides.

## 3. What is running / queued at handoff time

- **`_pr` 4-arm job** (started 11:42): arms 1–2 (CO₂ + CH₄-bio, **stochastic**) landed 12:32
  and 13:23. Arms 3–4 (both `_nonoise_flatsolar`) were still running, ~50 min each, expected
  ~14:15 and ~15:05. The headline table above is the **stochastic** arm; deterministic rows
  append on re-run.
- **Fossil BRICK arms queued** (`scratchpad/queue_fossil_brick.sh`, backgrounded): waits for
  the `_pr` job to fully exit, **gates on all four `_pr` arms existing** (aborts otherwise),
  then runs a zero-pulse wiring gate on `_ch4foss1tg` followed by the two production arms.
  **They must never run concurrently** with another `run_subannual.sh`: the wrapper patches a
  file in the SHARED MimiBRICK depot and restores it via an EXIT trap, so a second wrapper
  would restore the pristine integrator out from under a live run.

**To rebuild the tables once those land:**

```bash
python python/metric_horizon_table.py --tag=_pr --ch4=bio
```

```bash
python python/metric_horizon_table.py --tag=_pr --ch4=foss
```

## 4. Still open — do NOT silently resolve

1. **Tip-classifier threshold** (§4.1 of the prior handoff) — the documented AIS@2100 > 20 cm
   classifier selects 37.6% on BRICK-AM extA108, not ~5%. **The headline table does not depend
   on it** (MEANS are unaffected); it gates only the mode decomposition.
2. **Headline basis, stochastic vs `_nonoise_flatsolar`** (§4.2) — they agree on the MEAN
   (0.04–1.7% on the `_subann` runs) but differ on tip fraction (23% vs 33%). The
   deterministic `_pr` arms will give the matched-horizon comparison; the decision is yours.
3. **GWP basis** (§4.3) — reported as a first-class function in the CSV. Note the headline
   ratio is GWP-invariant, so this now only affects the per-gas *levels* and the crossover.
4. **RFF-SP backbone + the CH₄ scenario-sensitivity gate** — untouched. RFF under-projects CH₄
   (obs ≥ p95), so the CH₄ marginal needs testing on an obs-anchored/high-CH₄ backbone before
   the RFF CH₄ baseline is trusted.

## 4b. ADDENDUM (16:20) — all four `_pr` arms in; fossil stochastic in; §4.2 settled

**Both bases now measured, and §4.2 is answerable for the headline.** Stochastic and
`_nonoise_flatsolar` agree on the MEAN to within **1.4% at every horizon**, on both the SLR
metric and the SLR÷temperature ratio. **For the headline table the basis choice is
immaterial** — pick either and label it. It stays material only for the tip-fraction / mode
decomposition (23% vs 33%), which is §4.1's separate question.

**Fossil-CH₄ stochastic arm complete**; zero-pulse gate on the new `_ch4foss1tg` basis
**PASSED** (every metric exactly 0.000e+00, all 6 horizons, all components). Deterministic
fossil arm running, due ~17:00.

| yr | SLR bio | SLR foss | temp bio | temp foss | SLR÷temp bio | SLR÷temp foss |
|---|---|---|---|---|---|---|
| 20 | 4.63 | 4.23 | 3.70 | 3.42 | 1.25 | 1.24 |
| 70 | 2.24 | 2.11 | 0.79 | 0.81 | 2.82 | 2.60 |
| 100 | 1.68 | 1.60 | 0.52 | 0.56 | 3.23 | 2.85 |
| 150 | 1.22 | 1.19 | 0.38 | 0.44 | 3.18 | 2.71 |
| 270 | 0.79 | 0.80 | 0.24 | 0.31 | 3.34 | 2.62 |

Two consequences for the paper:

1. **The ">3×" divergence is a BIOGENIC-CH₄ statement.** The oxidation CO₂ makes a fossil
   pulse more CO₂-like and compresses the divergence to ~2.6–2.85×. Both are large, but the
   arm must be labelled wherever the number appears.
2. **GWP-100 = 29.8 increasingly UNDER-corrects for the oxidation carbon.** The physical
   fossil/biogenic marginal ratio climbs 1.02 → 1.13 → 1.27 → 1.43 at 20/70/150/270 yr,
   against a fixed GWP ratio of 29.8/27 = 1.104. By 270 yr a fossil tonne is worth ~1.29× its
   biogenic counterpart per GWP-equivalent tonne on temperature — a fixed 100-yr integral
   cannot track a 270-yr endpoint. This is a metrics observation in its own right and sits
   naturally beside the plan's §9.5 GWP-basis discussion.

**Operational gotcha now in the driver header.** `_arg` is `findfirst` — the **first**
occurrence of a flag wins and later repeats are **silently ignored**. A queued fossil job
built its command as `"$BASE_ARGS $OVERRIDES"`, so an intended 3-config zero-pulse smoke gate
ran as a full 841×2000 production job. Harmless in the end (it produced the valid production
stochastic arm, and the real gate was run afterwards and passed) but it cost a duplicate
~50 min run, killed mid-flight with the depot verified pristine after. **Never append
overrides to a base arg string on this driver.**

## 5. Commits

`SLR-RFF-BRICK` (`brick-mengel-vnext`): `d577d0d` metric-table script + validation →
`93cb5c6` fossil variant support → `222c993` headline table → `2b19b13` novelty-claim note →
`a3bde83` this handoff → `aab89fd` both bases + fossil tables → `a38ba3f` arg-precedence gotcha.
`FaIRtoFrEDI` (`heat-ed-morbidity`): `e85ee67` fossil two-pass fix + quarantine →
`36ecb48` CHANGELOG.
