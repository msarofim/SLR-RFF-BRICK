# Handoff — L14 (2 basins on `south`) is WIRED, GATED, and RUNNING UNATTENDED

**Start-here document.** Repo `SLR-RFF-BRICK`, branch **`ladrillo-dev`**, HEAD `173d61c`.
Predecessor: `handoff_2026-08-20c_two_basin_plan.md` (the execution plan). **This note is
the STATE; 20c is still the plan and 20b is still the evidence.**

Launched 2026-08-20 ~10:33 with Marcus away ~4 h and his carbon-cycle work sharing the
box. **L12 remains canonical (SLR@2100 45.53 cm). Nothing here promotes anything.**

---

## 0. LANDED 2026-08-20 15:12 — RESULT FIRST

**The transfer test PASSED.** `s_high` **0.2265** (pre-registered 0.20–0.30), worst |z|
**0.56** (pre-registered ~0.69; L13 1.07). **SLR@2100 45.01 cm / @2150 70.58 cm**,
projected SLR converged at R̂ 1.017 / 1.015, ESS 953 / 967. Subsample written, 10000
members. 20 marginals unconverged (the usual AIS ridge) ⇒ projections only.
**L12 remains canonical at 45.53 cm — promotion is Marcus's call.** Full numbers and the
comparison table are in `CHANGELOG.md` 2026-08-20f and memory `gis_two_basin_decision`.

Production ran **2 h 36 m**, not the 5.5 h estimated. Both drivers completed clean.

## 0b. WHAT WAS RUNNING, and how it was checked

Two detached drivers, both polling FILES (never `pgrep` — it self-matches the waiting
shell; that hung two waiters in this arc):

| driver | log | does |
|---|---|---|
| `julia/run_l14_chain_after_tune.sh` | `outputs/mcmc/log_L14_chain_driver.txt` | waits for the tune chain → liveness-guards its acceptance → backs up + rebuilds the starts → runs `run_l14_production.sh` |
| `julia/run_l14_postprocess_after_production.sh` | `outputs/mcmc/log_L14_postprocess_driver.txt` | waits for the 4 production chains → postprocess → SLR convergence → postprocess `--accept-slr` → basin shares |

```bash
tail -5 outputs/mcmc/log_L14_chain_driver.txt outputs/mcmc/log_L14_postprocess_driver.txt
```

**The post-processing ORDER is load-bearing.** `--accept-slr` reads
`slr_convergence_L14.csv` and refuses it if it is older than the newest chain; running
the two postprocess calls back to back produces NO SUBSAMPLE. That is what left L13
without one for a day (20b §1). The driver enforces it.

Every output is tag-scoped (`chain_L14_*`, `slr_convergence_L14.csv`,
`parameters_subsample_brick_mengel_L14.csv`), so nothing can clobber L12 or L13.

**Timeline from 10:33:** tune ends ~11:20 → production ~11:22–16:50 → post-processing
done ~17:30.

---

## 1. WHAT `--gis-basins2` IS (commit `083d174`)

NO new Mimi component. `greenland_3basin` at `k_mid = 0` **is** a two-basin model, by
construction (`eq_b == k_b*eq_whole` identically). `GIS2_VSHARE` is **derived** from
`GIS3_VOL_M` in the component file, so calibrator and tests read one number.

    active = SW+CW+CE+SE+NW   k 0.628571   carried in the `south` SLOT, NOT renamed
    high   = NO+NE            k 0.371429   ONE sampled scale, gis_s_high

* `gis_s_mid` **dropped from `FREE`** — verified **NK 59 → 58**.
* Seeded from `adapted_cov_L13_seed2026.csv`: *"name-mapped 58 of 59 rows using the
  FILE'S OWN header; dropped gis_s_mid"*. Seed-diagonal gate extended to the basin
  scales (floor 1e-3); `gis_s_high` seeds at L13's tuned **0.02345**.
* Shares term on the 2-way targets, derived as active = south + mid: **0.799/0.201**,
  **0.816/0.183**, sd 0.05, **one** scored share per window.
* `--gis-check` = **0.0000** on all four gates in all three configs. Tolerances untouched.

---

## 2. THREE PRE-EXISTING DEFECTS FOUND AND FIXED — read this one first

### 2.1 The projector read a 2-basin posterior as `:ab` (`6b5f650`) — the expensive one

`ladrillo_gis_variant` decided "3-basin" by PRESENCE of `["gis_s_mid","gis_s_high"]`. An
L14 chain has `gis_s_high` but **not** `gis_s_mid`, so the test was false and it fell
through to `:ab` — projecting whole-sheet `greenland_ab` at s = 1, **a model that was
never calibrated**, with no error anywhere.

**This hole already bit once.** `diag_l13_projection_variant.jl`'s own header records an
L13 chain falling through it before 2026-08-19, worth **−1.7 cm on the 2100 median**.
Closing it by presence fixed one layout; the next layout re-opened it.

Fixed: `:basins2` = `gis_s_high` present **and `gis_s_mid` absent** (the absence is
load-bearing); `k` follows the variant through one `ladrillo_basin_k()`, because
`GIS3_VSHARE` and `GIS2_VSHARE` are *both* valid k vectors summing to 1 so the wrong one
is silent; a partial basin set is now REFUSED, not answered with `:ab`.
`test_ladrillo_basins2_variant.jl` gates it (now step 7 of `run_ladrillo_tests.sh`).

### 2.2 The calibrator↔projector parity gate was DEAD (`2006702`)

`validate_gis_projection_ab.jl` regex-scrapes the calibrator source. `GIS_ZONE` became a
flag expression and `GIS_AMP` became a CSV read (`09eec0a`), so both regexes returned
nothing, both gates FAILED, and `run_ladrillo_tests.sh` had been exiting non-zero — which
is a stated precondition of the production scripts. Verified pre-existing against HEAD
before touching it. Now reads what the calibrator reads.

### 2.3 `gis_port_reference.csv` was stale (`0e0b491`)

Regenerated by the test suite every run; the committed copy predated `09eec0a`. Diff
starts **exactly at 2025** = the splice year, which is the signature of that cause.

---

## 3. WHAT TO LOOK AT WHEN IT LANDS

Pre-registered, from the offline 2-basin refit — `diag_l13_basin_shares.jl` prints these
next to the result so no lookup is needed:

| quantity | expect | L13 (3-basin) was |
|---|---|---|
| `s_high` | **0.20–0.30** (offline 0.229) | 0.2638 |
| worst \|z\| on a scored share | **~0.69** | 1.07 |
| hindcast RMSE | ~0.0617 cm | 0.0617 |

**`s_high` near 1** ⇒ the shares term is not biting. **Below ~0.1** ⇒ it is dominating.

**WHAT WILL NOT CHANGE, so nobody reads it as failure (20c §6):** no basin structure buys
the 2300 separation. 1/2/3 basins give ssp585@2300 ratios **2.69× / 2.73× / 2.72×**, all
inside the single-law ridge ceiling 1.72–3.36×, against the literature's 7.9–31.9×. The
restructure fixes the **PARTITION**; the **TAP** fixes the **SEPARATION**. A 2-basin run
coming back at ~2.7× untapped has behaved exactly as expected.

**Revert conditions are named** in `handoff_2026-08-20c` §7 and memory
`gis_two_basin_decision`. A different 2300 number is NOT one of them.

---

## 4. STILL OPEN

* **L15 = `--gis-zone=all`.** Untouched on purpose. Its prerequisite chain is 20c §4 —
  and §4's warning stands: the row you want from `diag_gis_g_betaf.py` is `g=0`, NOT the
  headline `A+B` row, or `c0` looks like a 15× error.
* **The TAP** (onset 6.5 K / V 2.0 m / τ 50 yr) — projection-side, not sampled, no chain
  needed. 20c §5. Unstarted. Re-test the `Ṽ` collapse after wiring; the exact 1-D
  degeneracy is a property of the mock's ADDITIVE tap.
* **`diag_l13_projection_variant.jl` still hard-requires `:basins`.** It is the L13
  3-arm study, not on the L14 path, so it was left alone. Generalising it would give a
  full draw-set projection-variant number for L14; the s=1 identity is already gated by
  `test_ladrillo_basins2_variant.jl` at 1.4e-14.
* **L13 promotion** — open since 19d. L12 canonical. L14 may make it moot.
* `run_l11_production.sh` / `run_d2_stream_attribution.sh` still carry the unpassed
  `$ADCOV` defect. Harmless today; fix when next touched.

---

## 5. TRAPS ADDED THIS SESSION

* **A liveness gate that uses `min` over draws is hostage to one draw.** "`:basins2` must
  differ from `:basins`" read exactly 0.0000 because draw 3 of the fixture has
  `s_mid` = 1.0030, sitting on the null. Diagnosed, not explained away: the k identity
  (`:basins2` ≡ `:basins` at `s_mid`=1) holds at 7e-15, which is the real gate because it
  is EXACT and needs no threshold. Restrict liveness checks to draws away from the null.
* **`s_mid`'s effect on a 2100 projection is ~0.002–0.02 cm.** That smallness IS the case
  for two basins — do not read it as a weak test.
* **An L13-vintage `overdispersed_starts.csv` PASSES the calibrator's by-name guard**,
  because a `gis_s_mid` column absent from `pn0` is silently ignored.
  `run_l14_production.sh` rejects one that carries it.
* **Never edit a running bash script** — bash reads incrementally and will resume at a
  byte offset that is now mid-line. Add a sibling file.
