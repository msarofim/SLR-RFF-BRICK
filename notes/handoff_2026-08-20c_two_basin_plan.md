# Handoff — TWO basins decided; run `south` first, then `--gis-zone=all`

**Start-here document.** Repo `SLR-RFF-BRICK`, branch **`ladrillo-dev`**, HEAD `958a3f0`.
Predecessors: `handoff_2026-08-20b_tap_priced.md` (the evidence), then
`handoff_2026-08-20_gis_zone_and_tap.md`.

**This note is the EXECUTION PLAN. The analysis behind every number is in 20b; read this
one to do the work, read 20b to challenge it.**

---

## 0. THE ORDER, decided by Marcus 2026-08-20

1. **Run A — 2 basins on the CURRENT `south` zone.** Runnable immediately. One variable
   changes, so the result is attributable.
2. **Run B — 2 basins on `--gis-zone=all`.** Has a NAMED PREREQUISITE CHAIN (§4) that must
   be completed first. Do not start B before A has been read.

Doing A before B is the whole point: `south → all` and `3 basins → 2 basins` are two
separate changes, and this arc has repeatedly paid for moving two at once.

**L12 stays canonical (SLR@2100 45.53 cm) throughout.** Nothing below promotes anything.

---

## 1. WHAT WAS DECIDED, and the evidence in one paragraph each

**TWO basins.** `active` = {SW, CW, CE, SE, **NW**}, `high` = {NO, NE}.
`k = (0.628571, 0.371429)`, sum exactly 1. **ONE** sampled rate scale (`gis_s_high`);
`active` pinned at s = 1. *Evidence:* a full refit of every structure in the offline
harness gives `s_mid` = **1.024**; pinning it to 1 costs **Δnlp 0.0023**; the profile is
**well-curved, not flat** (+6.3 at s_mid 0.25, +7.3 at 3.98), so `s_mid` is
IDENTIFIED-and-equal-to-1, not merely unconstrained. Two basins also fit the Mouginot
windows BETTER — worst |z| **0.69 vs 1.01** — with one fewer parameter, because a single NW
scale cannot span the two-window tension 0.207 vs 0.262. The prototype's 4.47× is excluded
at Δnlp > 7. *(`03df3d2`, `outputs/scope_gis_basin_structure{,_profile}.csv`.)*

**TAP CELL: onset 6.5 K / V 2.0 m / τ 50 yr** — candidate #5 of six. *Evidence:* the 2300
scorecard identifies only `Ṽ = V·u₂₃₀₀ ∈ [1.252, 2.647] m` (reproduces `all_pass` exactly,
25/25), leaving a 2-D degenerate surface whose free direction costs up to **0.82 m at 2150**
while costing exactly **0.000 m at 2100**. Resolved by a DESIGN PRINCIPLE — *the tap must not
move any horizon at which the model has independent validation* — which is the same logic
that produced the Tier-1 bracket's 4.69 K floor (it IS ssp585's 2100 GMT). Extending it to
2150 gives **onset ≥ 6.5 K** (6.5 K first fires 2155, 7.0 K 2180). #5 was chosen over #2 on
**robustness**: #2 sits at band position 0.09, hard against the bottom of the 1.732–3.127 m
band, and the restructure MOVES THE BASE. **It is a PRIOR SPECIFICATION, not a fit — say so
in any methods text.**

**Three basins are RETAINED as the fallback**, with named revert conditions — memory
`gis_two_basin_decision`, and §7 below.

---

## 2. THE WIRING — no new component, three load-bearing items

### 2.1 NO NEW MIMI COMPONENT. Verified bit-identical.

`greenland_3basin` with **`k_mid = 0`** reproduces a genuine two-basin model EXACTLY:
`max |gis_sl_mid| = 0.0`, and active / high / total all differ by **0.000e+00 m**
(`np.array_equal` True). The two-basin model is a **`k`-CONFIGURATION** of the component
that already exists, so the nesting is exact BY CONSTRUCTION rather than by test — a
stronger position than the 3-basin restructure ever had.

Set `GIS3_VSHARE` for this mode to `(south = 0.628571, mid = 0.0, high = 0.371429)`. The
`south` slot carries the merged `active` basin; **do not rename the slot** — the output
contract (`gis_fast`/`gis_slow`/`greenland_sea_level` as basin sums) is what every
downstream consumer reads, and renaming buys nothing.

### 2.2 The three items, none optional

1. **DROP `gis_s_mid` from `FREE`.** At `k_mid = 0` it multiplies a zero-commitment basin
   and does nothing. A dead sampled parameter is a random walk that inflates the proposal
   and hides defects. **Do not leave it in "harmlessly".**
2. **NK goes 59 → 58.** No existing covariance matches by size ⇒ `embed_cov!` **BY NAME**.
   This is the THIRD layout change in this arc and **both previous ones bit**: the ADCOV
   size collision that gave acceptance exactly 0.0 (`ladrillo_adcov_size`), and the
   `L11_NAMES` mis-order that voided L13's first line (`nameless_matrix_order`).
   **Gate the diagonal after mapping** — `sqrt(diag(cov0))[ais_c] >= 0.05` already exists in
   `run_l13_production.sh`; keep it and add one for `gis_s_high`.
3. **`GISB_TERM` switches to the 2-way targets.** Only ONE share is independent now:

   | window | active | high |
   |---|---|---|
   | 2002–2011 | **0.799** | 0.201 |
   | 2012–2018 | **0.816** | 0.183 |

   σ = 0.05, as before. Score ONE of the two per window (they sum to 1, so scoring both
   double-counts). The existing `abs(d_tot) > 1e-12` guard is load-bearing — keep it.

### 2.3 Acceptance references from the offline refit

The offline 2-basin fit gives **`s_high` = 0.229**, worst |z| **0.69**, RMSE **0.0617 cm**,
all pre-registered gates passing. L13's 3-basin posterior gave `s_high` = 0.268 and the
offline 3-basin refit 0.259. **Expect the calibrated `s_high` in roughly 0.20–0.30.** A
value near 1 means the shares term is not biting; a value below ~0.1 means it is dominating.

---

## 3. RUN A — 2 basins on `south` (runnable NOW)

Mirror `julia/run_l13_production.sh` exactly; the only intended differences are the basin
mode and the resulting layout.

**Proposed tag: `L14`.** (Naming is a choice, not a finding — say so in the log.)

1. **Wire** per §2, behind a flag (`--gis-basins2`), NOT a source edit. Same discipline as
   `--gis-zone` and `--adcov`: the arm must be runnable, reviewable in the run script, and
   recorded in the log.
2. **Nesting test FIRST**, before any chain. Add to `julia/test_greenland_3basin_nesting.jl`
   (or a sibling): with `k = (0.628571, 0, 0.371429)` and `s_high = 1`, the component must
   reproduce whole-sheet A+B at the floating-point level, exactly as the 3-basin nesting
   test does at `k = (1,0,0)`. **Mutation-test it** — per `mutation_test_gates`, confirm it
   FAILS if you perturb a `k`. A gate that has only ever passed proves nothing.
3. **`--gis-check`** must still score 0.0000. **DO NOT WIDEN ITS TOLERANCE.**
4. **Re-tune** (~1.4 h), then **4 × 2 M production** (~5.5 h). Seed from the L13 production
   covariance by NAME.
5. **Postprocess**: `postprocess_mcmc_ext.jl --tag=L14`, then
   `diag_slr_convergence_by_chain_ladrillo.jl`, THEN re-run postprocess with `--accept-slr`.
   **Order matters** — doing it the other way round is exactly what left L13 without a
   subsample for a day (20b §1).
6. **Diagnose**: `diag_l13_basin_shares.jl` adapted to 2 basins. Target worst |z| ≈ 0.7.

---

## 4. RUN B — 2 basins on `--gis-zone=all` (PREREQUISITE CHAIN)

The calibrator **refuses to start** on any zone but `south` and its error message names the
prerequisite. Do these in order:

1. `python3 python/gis_offline_cell.py --zone=all`
   → `outputs/gis_offline_cell_fits_all.csv` (zone-tagged; the south artefacts are the
   provenance of the shipped calibration and must not be overwritten).
2. `python3 python/diag_gis_g_betaf.py --zone=all`
   → `outputs/gis_g_betaf_variants_all.csv`. **The row you want is `g=0`, NOT the headline
   `A+B` row** — the calibrator's centres are the g = 0 arm (`c0 = 4.04 cm at g = 0`, not
   the headline's `61.99 cm at g = 0.917`). Four of the five centres agree to 4 significant
   figures either way, **so `c0` alone looks like a 15× error if you check the wrong file.**
3. **REPORT the new centres before adopting them.** Marcus has authorised the `all` arm, but
   the specific numbers going into `GIS_NATIVE_MU`, the five `gis_*` centres and
   `GIS_OFFLINE_G0` should be shown, not silently baked in.
4. Regenerate the `--gis-check` reference. **DO NOT WIDEN ITS TOLERANCE.**
5. Relax the `GIS_ZONE` gate branch in `calibrate_mcmc_ext.jl`.
6. Then Run A's steps 1–6 with `--gis-zone=all`. **Proposed tag: `L15`.**

**What does NOT need re-deriving, and this was got wrong once already:** the `(ell, w)`
reparameterisation priors. `GIS_ELL_MU`/`GIS_W_MU` already derive from `GIS_TBAR` and
re-anchor automatically (south `ell −4.2074, w 0.93282` → all `−3.9234, 0.94943`).
`GIS_TBAR` for `all` is **2.6543 K** (south 1.9631). The `gis_amp` prior also derives from
`gis_amp_prior.csv` now (`09eec0a`), so it follows the zone by itself: all/full mean
**2.3470378**, sd **0.5594**, `[1.6696, 3.0395]`.

**Expect the answer to MOVE.** The `all` driver is **1.352× hotter at the anchor**, so the
same rate constants produce more melt. That is the entire reason the centres must be
re-derived rather than reused.

---

## 5. THE TAP — separate work, projection side

Wire at **onset 6.5 K / V 2.0 m / τ 50 yr** into the Greenland component on the projection
side, prior-propagated like `gis_amp`. **It is not sampled and needs no chain** — that was
20b's main analytical result (calibration tops out at 1.385 K in 2025, 5.1 K below this
onset).

**Verification, non-negotiable:** tap-on and tap-off must be **bit-identical through 2150**
and diverge only from 2155. G2/G2b/G3 in `python/scope_gis_tap_l13.py` are the offline
versions of exactly that check; port them.

**AND re-test the `Ṽ` collapse after wiring.** The exact 1-D degeneracy is a property of the
mock's ADDITIVE tap. Inside the component the tap interacts with the basin's own relaxation
and its `k_b·v0` clamp. **Do not assume it survives.** If it does not, the six-cell shortlist
must be recomputed — the design principle (§1) still holds, but the specific cell may move.

---

## 6. WHAT WILL NOT CHANGE, so nobody reads it as failure

**No basin structure buys the 2300 separation.** One / two / three basins give ssp585@2300 =
46.2 / 55.1 / 54.1 cm and ratios **2.69× / 2.73× / 2.72×** — all inside the single-law ridge
ceiling of 1.72–3.36×, against the literature's 7.9–31.9×. **The restructure fixes the
PARTITION; the TAP fixes the SEPARATION.** They are different jobs. A 2-basin run that comes
back at ratio ~2.7× untapped has behaved exactly as expected and is **not** evidence against
the structure.

---

## 7. FALLBACK — revert to three basins if, and only if

1. the 2-basin recalibration **cannot hit the Mouginot windows** (expect worst |z| ≈ 0.7; a
   materially worse outcome means the offline result did not transfer);
2. the merged `active` basin **degrades the 1900–2025 hindcast beyond L13's** (offline says
   it should not — identical RMSE 0.0617 cm, all gates pass);
3. a **per-sector deliverable** appears that genuinely needs NW resolved separately — the
   2-basin model cannot produce a south-vs-NW split at all, only their sum.

**A different 2300 number does NOT justify reverting** (see §6).

L13 is intact: certified at SLR@2100 44.97 cm, subsample at
`data/MimiBRICK/parameters_subsample_brick_mengel_L13.csv`.

**Standing caveat on all the offline evidence:** it is the Greenland-**only** cell — no BRICK
coupling, no AR(1) noise, none of the other likelihood terms. It is strong on the Greenland
block in isolation and has **not** been shown to transfer. That transfer is what Run A tests.

---

## 8. STILL OPEN (not touched by any of the above)

* **L13 promotion** — open since 19d. L12 canonical. Runs A/B may make it moot.
* **The D2G / D2S arms** — whether they get re-run; bounded at ~2 % of the steric effect.
* **`adapted_cov_L13.csv`** — a NAMELESS 59×59 at a canonical name, in no vintage name list.
  Nothing reads it today. Anything that later points `--adcov=` at it must gate the diagonal.
* **Base G4 = 7.42 cm** sits 0.12 cm above the 6.3–7.3 cm range of the four comparison
  models. An ensemble median, so the comparison is legitimate. Worth a look at promotion;
  nothing turns on it.
* **`run_l11_production.sh` / `run_d2_stream_attribution.sh`** still carry the unpassed
  `$ADCOV` defect. Currently harmless; fix when next touched.

---

## 9. TRAPS, collected

* **`pgrep -f <pattern>` SELF-MATCHES** the waiting shell, whose own command line contains
  the pattern — `! pgrep` never becomes true and the loop spins to timeout. Two waiters hung
  this way. Poll an output file instead.
* **`postprocess` before `diag_slr_convergence`** silently produces no subsample.
* **The `g = 0` vs headline row** of the offline fit (§4.2) — the 15× `c0` trap.
* **BSD grep on macOS does not treat `\|` as alternation.** Use `grep -E` in audit scripts.
* **Python buffers stdout through `tee`** — use `python3 -u` for long runs you want to watch.
