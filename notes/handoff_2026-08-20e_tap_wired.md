# Handoff — L14 IS CANONICAL; the tap is wired and buys the separation

**Start-here document.** Repo `SLR-RFF-BRICK`, branch **`ladrillo-dev`**.
Predecessors: `handoff_2026-08-20d_l14_running.md` (the run), `..._20c_two_basin_plan.md`
(the plan), `..._20b_tap_priced.md` (the evidence). Read this one to work; read those to
challenge it.

---

## 0. THE STATE, in six lines

* **L14 is CANONICAL** (Marcus 2026-08-20). Two-basin Greenland, `--gis-basins2`.
  **SLR@2100 45.01 cm / @2150 70.58 cm.** L12's 45.53 is superseded.
* The offline 2-basin evidence **TRANSFERRED**: `s_high` **0.2265**, worst |z| **0.56**
  (pre-registered 0.20–0.30 and ~0.69; L13 was 1.07).
* **The tap is wired** at onset 6.5 K / V 2.0 m / τ 50 yr and **buys the separation**:
  Greenland ssp585/ssp245 @2300 **2.73× → 12.58×** (literature 7.9–31.9×).
* **The AIS unconverged marginals are a REPORTING CAVEAT** — re-measured on L14, not
  carried forward from L10. Nothing to do. See §3.
* **20 parameter marginals unconverged ⇒ PROJECTIONS ONLY, not parameter-level
  inference.**
* Nothing is running. Working tree clean at the commit this note lands in.

---

## 1. WHAT "CANONICAL" NOW MEANS MECHANICALLY

`LADRILLO_POSTERIOR_CSV` in `julia/ladrillo_projection.jl` is the **authority**, and it
points at `parameters_subsample_brick_mengel_L14.csv`. Almost everything derives from it
(`project_ssps_components_ladrillo.jl`, `posterior_predictive_ladrillo.jl`,
`diag_slr_convergence_by_chain_ladrillo.jl` all compute their default tag from its
basename), so they followed automatically.

**Three things did NOT follow and were changed by hand:**

1. `validate_gis_projection_ab.jl` asserted **"the CANONICAL posterior reads as `:ab`"**.
   Promotion broke it *correctly* — L14 reads `:basins2`. Generalised to "a projectable
   A+B variant", plus a new gate pinning `LADRILLO_POSTERIOR_L12_CSV` as the `:ab`
   fixture.
2. `diag_gis_block_convergence.jl` carries a hardcoded default tag (deliberately — it is
   a pure-CSV diagnostic that must not pull in Mimi). Its own comment says *"that
   constant remains the authority, so update both together"*. Now `L14`.
3. Comments in four files named a stale canonical vintage. Labels synced.

**New named constants, following the established one-per-superseded-vintage pattern:**

* `LADRILLO_POSTERIOR_L12_CSV` — canonical 08-18 → 08-20, the provenance of every
  deliverable quoting **45.53 cm**, and **the last whole-sheet vintage**, so it is the
  `:ab` fixture. Point `:ab` tests HERE, never at the canonical constant.
* `LADRILLO_POSTERIOR_L13_CSV` — never promoted, so provenance of nothing shipped, but
  it is the **named fallback** (memory `gis_two_basin_decision`) and **the only
  `:basins` posterior**, so it is the fixture for anything needing `gis_s_mid`.

**Deliberately NOT repointed:** the eight `python/*.py` scripts carrying
`LADRILLO_TAG = "L12"` / `"L13"`. Each is a vintage-specific analysis whose unsuffixed
output *is* the measurement a past decision rested on — the same reason
`diag_gis_ordering_in_l11_posterior.py` stays on L11. **Blanket-repointing them would
silently relabel old measurements.** Re-run individually at `L14` if and when a
particular number is wanted at the new vintage.

---

## 2. THE TAP — wired, gated, and what it is NOT

`GIS_TAP_CELL = (onset_K = 6.5, V_m = 2.0, tau_yr = 50.0, ramp_w_K = 1.0)` in
`julia/greenland_3basin_component.jl`. **OFF by default** (`gis_tap_v = 0`), so every
pre-existing consumer is bit-identical until it opts in.

**IT IS A PRIOR SPECIFICATION, NOT A FIT.** The cell comes from a design principle — *the
tap must not move any horizon at which the model has independent validation* — not from
fitting anything. **Any methods text must say so.** It is prior-propagated like
`gis_amp`, **not sampled**, and needs no chain: calibration tops out at 1.385 K against a
6.5 K onset, so it is exactly likelihood-inert.

Switch on with `ladrillo_set_tap!(bf)` (projection side) or `update_gis3_tap!(m, gmt)`.
`julia/project_ssps_components_ladrillo.jl --tap` runs the tapped 2300 projection and
**puts the cell in the output filename**.

### Both "do not assume it survives" questions resolved YES

1. **The `k_b·v0` capacity clamp NEVER binds** — `max(wanted − applied) = 0.0000 m`. The
   offline mock's tap is uncapped additive while the component clamps per basin, so this
   was the one place wiring could diverge from pricing. **It does not, at this cell**, so
   the offline pricing transfers exactly. `gis_tap_wanted` and `gis_tap_applied` are both
   exported so this stays a number, not an argument — **re-check it if the cell moves.**
2. **The Ṽ collapse survives wiring, exactly.** Cell A (V 2.00, τ 50, u₂₃₀₀ 0.9015) and
   cell B (V 4.05, τ 200, u₂₃₀₀ 0.4448), same Ṽ = 1.8031 m, agree at Greenland@2300 to
   **+0.000 cm**. The six-cell shortlist carries over.

### Two wiring decisions that will bite anyone who changes them

* **The onset is in GLOBAL mean temperature**, not the regional Greenland driver. The
  Tier-1 bracket is quoted in GMT (4.69 K *is* ssp585's 2100 GMT). The regional driver
  would fire the tap ~`gis_amp` (1.92×) early and **nothing downstream could detect it.**
* **The tap rides in `gis_slow`, NOT in `gis_slow_high`.** The latter is carried to t+1
  and relaxes toward `(1−f)·eq`, so folding the tap in would feed it back through the
  basin's own relaxation and decay it — a different model that looks entirely plausible.

### Gates: `julia/test_gis_tap_wiring.jl`, all mutation-tested

| gate | result |
|---|---|
| G3 — `V = 0` bit-identical, ignores onset/τ | 0.000e+00 cm |
| G2 — ssp585 total at 2100 and 2150 unmoved | 0.000e+00 cm |
| G2 — first divergence | **2155**, the predicted first-fire year |
| G2b — ssp126 / ssp245 deviate | **exactly 0.0** |
| MUT — onset 4.0 K moves 2150 / onset 2.0 K fires ssp245 | 132.8 / 200.2 cm |

### The numbers (full 2000-draw L14 ensemble)

| Greenland @2300 | untapped | tapped |
|---|---|---|
| ssp126 | 10.1 | 10.1 |
| ssp245 | 18.3 | 18.3 |
| ssp585 | 50.0 | **230.3** |

Total@2300 ssp585 moves **+182.1** while Greenland moves +180.3. The missing **+2.0 cm is
the AIS**, mechanism verified from the model graph rather than inferred:
`global_sea_level.sea_level_rise → antarctic_icesheet.global_sea_level`, i.e. DAIS's
grounding-line feedback responding to 1.8 m of extra meltwater. **The tap is inside the
coupled model, not bolted on.**

---

## 3. THE AIS — CLOSED. Do not re-open without new observations.

The "no ridge / `ais_iceflow0` alone / reporting caveat" verdict was measured on **L10**
and was four vintages old. L14 shows high R̂ on **three** AIS parameters, which is
consistent with that picture only if they load on one direction. **Re-measured, holds:**

* `ais_iceflow0` is one concentrated direction — loading **+0.97**, **81%** of all
  between-chain variance, correlation-matrix condition number **13**. No ridge.
* `ais_slope` loads only **0.19** on it; its R̂ 1.750 rides `iceflow0`'s.
* `antarctic_alpha` is a *separate* concentrated direction in the other block (+0.94,
  83%, condition number 8).
* **Neither reaches the deliverable.** `ais_iceflow0` explains R² = **0.004 / 0.003 /
  0.002** at 2100 / 2150 / **2300** — and 2300 had never been checked on any vintage.
  `antarctic_alpha`'s correlation is ~+0.08 throughout.
* Alignment control passes (`antarctic_temp_threshold` r ≈ −0.65, `ais_gmst_amp` ≈ +0.49),
  so the ~0 is real, not a plumbing artefact.
* The four chains **do not agree on the loose direction** (|cos| 0.583/0.625/0.857), so
  one reparameterisation would not serve all four anyway.

**The named fix is an observational grounding-line discharge constraint** — the partner
to the A5 SMB anchor — **not a better sampler**, and Marcus ruled it out of scope as
decision D5 (2026-08-14). Nothing to do here.

Tools, both now `--tag`-aware: `python/diag_block_ridge.py`,
`julia/diag_iceflow0_propagation.jl`.

---

## 4. NEXT, in the order I would take them

1. **`--gis-zone=all` (L15).** The remaining structural question, and the expensive one:
   full tune + 4×2M. **Prerequisite chain is handoff 20c §4 and it has not started.**
   Its trap stands: the row you want from `diag_gis_g_betaf.py` is **`g=0`, NOT the
   headline `A+B` row**, or `c0` looks like a 15× error. Expect the answer to MOVE — the
   `all` driver is 1.352× hotter at the anchor.
2. **A Greenland reparameterisation, which is now well posed.** The block-ridge
   diagnostic on L14 found the Greenland block at condition number **67** with **all four
   chains seeing the SAME loose direction** (|cos| 0.959/0.988/0.976):
   `gis_slow_ell −0.49, gis_f −0.47, gis_c1 +0.46, gis_c0 +0.44`, 40% of variance, with
   `gis_c0`–`gis_slow_ell` at r = −0.808 in 2 of 4 chains. **Unlike the AIS, this one has
   a well-defined ridge and all four chains agree on it** — the precondition a
   reparameterisation needs. Not acted on. Cheapest real win on convergence.
3. **Re-price the tap if the cell ever moves.** The capacity clamp not binding is a
   property of *this* cell, measured; a larger V or a lower onset could reach it.
4. **Tapped deliverables.** Only the 2300 component projection has a `--tap` arm so far.
   Anything else that should report tapped numbers needs the same flag.

---

## 5. TRAPS ADDED TODAY

* **A guard that rejects a legitimate configuration is a bug, and its own gate will find
  it.** `update_gis3_tap!` errored whenever `max(gmt) ≤ onset`, which rejected ssp126 and
  ssp245 — where a tap that never fires is *correct* and is exactly what G2b asserts.
  Narrowed to a **degenerate** driver (constant series = the builder's all-zero default).
* **A liveness gate using `min` over draws is hostage to one draw.** "`:basins2` must
  differ from `:basins`" read exactly 0.0000 because one fixture draw has
  `s_mid` = 1.0030, sitting on the null. The fix was the **exact algebraic identity**
  (`:basins2` ≡ `:basins` at `s_mid` = 1, since k_active = k_south + k_mid), which needs
  no threshold, plus liveness restricted to draws away from the null.
* **Vintage-specific artefacts at vintage-free paths.** `diag_block_ridge.py` and
  `diag_iceflow0_propagation.jl` both wrote to nameless outputs regardless of `--tag`, so
  running them on L14 **overwrote the committed L10 analyses in place** with
  valid-looking files. Both L10 originals restored from git; all outputs now tag-scoped.
  **Check the write path before running a vintage-parameterised tool.**
* **A type annotation is evaluated at definition time.** `ladrillo_set_tap!(bf::Ladrillo)`
  placed above `struct Ladrillo` parses fine and fails to load.
* **Never edit a running bash script** — bash reads incrementally and resumes at a byte
  offset that is now mid-line.
* `pgrep -f <pattern>` **self-matches** the waiting shell. Poll a file.

---

## 6. STILL OPEN, unchanged

* **The D2G / D2S arms** — whether they get re-run; bounded at ~2% of the steric effect.
* **`adapted_cov_L13.csv`** — a NAMELESS 59×59 at a canonical name, in no vintage name
  list. Nothing reads it. Anything pointing `--adcov=` at it must gate the diagonal.
* **Base G4 = 7.42 cm** sits 0.12 cm above the 6.3–7.3 cm range of the four comparison
  models. An ensemble median, so the comparison is legitimate.
* **`run_l11_production.sh` / `run_d2_stream_attribution.sh`** still carry the unpassed
  `$ADCOV` defect. Harmless today; fix when next touched.
* **`diag_l13_projection_variant.jl` still hard-requires `:basins`.** It is the L13 3-arm
  study, not on the L14 path. Generalising it would give a full draw-set
  projection-variant number for L14; the s = 1 identity is already gated at 1.4e-14 by
  `test_ladrillo_basins2_variant.jl`.
