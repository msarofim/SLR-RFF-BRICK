# Handoff — wiring the per-sector SHARES term into the calibrator

**Start-here document for the next session.** Repo `SLR-RFF-BRICK`, branch
**`ladrillo-dev`**, HEAD `953a0fa`, **pushed and in sync with origin**.
Predecessor: `notes/handoff_2026-08-18e_sector_recalibration_design.md` (read it
for WHY the restructure exists; this one is the HOW for the calibrator step).

**Bottom line: everything upstream of the calibrator is done and Marcus has
approved the term's form — SHARES-ONLY and TIME-RESOLVED. Two scoping findings
change the job from what 18e imagined. (1) The calibrator ALREADY carries a
shares-only Mouginot term, `MOUG_SHARE`, in exactly the right place and form;
the new term is an analogue of it, not new machinery. (2) The cumulative
1972–2018 split must NOT be the target — Greenland was near balance before the
mid-1990s, so early shares are a ratio with a vanishing denominator. The
well-posed target is the MODERN RATE shares, which are stable to ±0.03. Target
numbers, the code anchors, and the known traps are all below. Nothing is
blocking; the next action is writing Julia.**

---

## 1. THE JOB, IN ONE PARAGRAPH

Add a per-sector (per-basin) **shares-only** likelihood term to
`julia/calibrate_mcmc_ext.jl`, so that a 3-basin Greenland — south {SW,CW,CE,SE}
/ mid {NW} / high {NO,NE} — is forced to reproduce the observed partition of
Greenland mass loss instead of letting one basin absorb all of it. Build it as a
direct analogue of the `MOUG_SHARE` term already in `logposterior`. Do NOT
constrain absolute sector losses; do NOT introduce a weighting knob. See §4 for
why each of those is settled rather than open.

---

## 2. THE CODE ANCHORS (all in `julia/calibrate_mcmc_ext.jl`, 1678 lines)

| what | where | note |
|---|---|---|
| **the term to copy** | **1189–1205**, gated on `GIS_AB` | fast-channel share of the EXTRA rate |
| `MOUG_SHARE, MOUG_SHARE_SD = 0.735, 0.05` | 249 | with its provenance comment at 243–248 |
| `MOUG_REF_WIN, MOUG_LATE_WIN = (1972,1990), (2000,2018)` | 250 | **do not reuse the ref window for sector shares — see §3** |
| `MOUG_I` (precomputed indices) | 1056–1057 | the index pattern to mirror |
| `logposterior(θ)` | 1061 | where the new term goes |
| `hetero_logl_ar1` | 130 | the AR(1) series likelihood — **not** what the shares term uses |
| `make_series` / the `S` NamedTuple | 358–372 | how targets become scored series |
| the component-series scoring loop | 1110–1128 | `S.ais/S.gsic/S.gis/S.steric` + the `dang` total |
| `embed_cov!` | 1458 | **critical for the ADCOV trap, §5** |
| GIS free-parameter block | ~588–600 | where new per-basin params get pushed onto `FREE` |
| the `--gis-check` diagnostic | 1624–1635 | already recomputes the Mouginot share; extend it |

**The existing term, verbatim in spirit:**

```julia
tot = m[_GIS_SLOT, :greenland_sea_level]; fst = m[_GIS_SLOT, :gis_fast]
rate(x, i0, i1, n) = (Float64(x[i1]) - Float64(x[i0])) / n
d_tot  = rate(tot, MOUG_I.l0, MOUG_I.l1, nlate) - rate(tot, MOUG_I.r0, MOUG_I.r1, nref)
d_fast = rate(fst, MOUG_I.l0, MOUG_I.l1, nlate) - rate(fst, MOUG_I.r0, MOUG_I.r1, nref)
if abs(d_tot) > 1e-12
    ll += logpdf(Normal(MOUG_SHARE, MOUG_SHARE_SD), d_fast / d_tot)
end
```

Its own comment states the design rationale we independently re-derived:
*"Scale-free, so the m-vs-cm unit difference does not enter."* **The codebase
already arrived at shares-only.** The guard `abs(d_tot) > 1e-12` matters — §3
explains why it matters far more for sectors than it did for channels.

---

## 3. THE TARGET NUMBERS, AND THE WINDOW TRAP

**Do not use the cumulative 1972–2018 split (48.1 / 31.7 / 20.2).** It mixes a
near-balance era into a ratio. Basin share of the mean mass-balance rate, by
window (`diag_gis_basin_lit_check.py` block 1c):

| window | total Gt/yr | south | mid | high | usable? |
|---|---|---|---|---|---|
| 1972–1981 | **+15.9** | 2.272 | −0.911 | −0.361 | **NO — near balance** |
| 1982–1991 | −40.0 | −0.052 | 0.786 | 0.266 | **NO** |
| 1992–2001 | −43.5 | 0.691 | 0.289 | 0.020 | **NO** |
| 2002–2011 | −245.6 | **0.592** | **0.207** | **0.201** | yes |
| 2012–2018 | −264.3 | **0.554** | **0.262** | **0.183** | yes |
| 1995–2018 | −196.4 | 0.593 | 0.223 | 0.183 | yes |
| 2000–2018 | −233.8 | 0.581 | 0.231 | 0.188 | yes |
| 2010–2018 | −286.2 | 0.587 | 0.236 | 0.177 | yes |

**Greenland was close to balance until the mid-1990s — the south basin was
GAINING mass in 1972–1990.** So the instability is a vanishing denominator, not
a drifting partition. Post-2002 the split is stable to about **±0.03**.

**Recommended target — two well-separated modern windows, time-resolved:**

| window | south | mid | high |
|---|---|---|---|
| **2002–2011** | 0.592 | 0.207 | 0.201 |
| **2012–2018** | 0.554 | 0.262 | 0.183 |

with **σ ≈ 0.05** per share (matching `MOUG_SHARE_SD`, and comfortably covering
the ±0.03 window-to-window spread). Two windows make it time-resolved as
approved, and the drift between them is itself information about whether the
model reproduces the *evolution* of the partition, not just its level.

**Only two of three shares are independent** (they sum to 1). Score south and
mid and let high follow, or score all three and state that the term is
rank-deficient by one — do not treat three shares as three independent
observations.

**If instead you mirror the existing extra-rate form** (2000–2018 over
1972–1990), the observed per-basin extra-rate shares are **south 0.694 / mid
0.141 / high 0.164**. These are well behaved even though the *level* shares on
that reference window are not (−1.458 / 1.850 / 0.608) — which is exactly why
the existing term uses the extra rate. Either form is defensible; the two-window
level form is recommended because it is more directly interpretable and does not
depend on a reference window that straddles balance.

---

## 4. WHAT IS SETTLED, AND WHY (do not reopen these)

Marcus approved **shares-only, time-resolved**. The four parts of the weighting
decision, and why each is closed:

1. **Absolute sector losses vs shares** → **shares.** The target series and
   Mouginot disagree on the 1972–2018 total by **1.227×** (1.689 vs 1.377 cm),
   far outside Mouginot's published per-region errors (30–91 Gt against a
   ~1,100 Gt gap). Shares make the sector term orthogonal to the total term:
   the total sets magnitude, the sectors set the split.
2. **Double counting** → avoided by shares. The existing total term already
   spans 1900–2025, which includes the sector window; a ratio carries no
   magnitude information, so it cannot double-count. **There is precedent in
   this very file** — the comment at 592–596 records `--gis-check` catching
   exactly this class of error for `gis_f`.
3. **Effective sample size** → moot under shares. Absolute sector numbers would
   have been ~3 observations against 126 annual points (~40:1) and thus inert
   unless up-weighted by an arbitrary factor. That knob does not exist here.
4. **Sector-term uncertainty** → σ ≈ 0.05 on a share, as above, NOT Mouginot's
   published mass errors (too tight to accommodate the inter-dataset gap).

**The ~25% two-window tension is NOT this term's problem.** Fitting 1972–2018
and predicting 1900–2025 misses by −23.1% for the 3-basin model and **−25.1%
for the single basin with no partition at all** — it is pre-existing in the
model / driver / target and unrelated to the sector split. Do not try to fix it
with the shares term; do not let it be blamed on the restructure.

---

## 5. TRAPS, EACH ALREADY PAID FOR ONCE

1. **ADCOV size collision — this one produced acceptance EXACTLY 0.0 before.**
   The L10 and L11 layouts were both 57 parameters and the size-based dispatch
   silently loaded the wrong adapted covariance. Adding per-basin parameters
   changes the layout. **Use `embed_cov!` (1458), which embeds by NAME**, and
   make sure the new layout cannot be confused with an existing one by size
   alone. Memory: `ladrillo_adcov_size`.
2. **The existing `MOUG_SHARE` term is ice-sheet-WIDE.** It reads
   `m[_GIS_SLOT, :greenland_sea_level]` and `:gis_fast`, which in a 3-basin
   model must become **sums over basins**, not one basin's channels. If it
   silently keeps scoring only the south basin, the fast/slow split will be
   calibrated against the wrong denominator.
3. **Sum-to-one rank deficiency** — see §3.
4. **The `abs(d_tot) > 1e-12` guard is load-bearing** and must be carried into
   any sector analogue. With sectors the denominator genuinely approaches zero
   in the early record (total +15.9 Gt/yr in 1972–1981), so a term that divides
   without guarding will produce garbage rather than a mild bias.
5. **Julia consumers read drivers by COLUMN NAME** (`ladrillo_projection.jl`,
   `calibrate_mcmc_ext.jl:320`) — verified unaffected by the zone additions, but
   re-check if the driver column changes to `all` (see §6).
6. **`build_t_gis.py` has a permanent driver guard**: a rebuild must reproduce
   the existing south/all columns to 1e-9 or it aborts. The untracked raw `.nc`
   files under `data/observations/raw/` are load-bearing for it.

---

## 6. AN OPEN ITEM THE PROTOTYPE ASSUMED

The offline prototype used the **`all`** driver column (single Greenland amp
2.347, `outputs/gis_amp_shape_all.csv`, built this session), per Marcus's
"a single Greenland amplification number would probably be acceptable". **The
shipped calibrator still uses `GIS_ZONE = "south"`** (line ~320). Switching it is
a one-line change with a large blast radius — it moves the driver every existing
result was fitted on. Decide deliberately; it is not implied by the shares term
and could be deferred to a second commit so the two effects stay separable.

---

## 7. WHAT THE OFFLINE WORK ALREADY ESTABLISHED (so it is not re-derived)

- **P1** — the 3-basin structure predicts the 1900–2025 total to −23.1%, against
  a single-basin control of **−25.1%**: the partition slightly REDUCES a
  pre-existing tension.
- **P2** — whole-sheet 2300 moves **0.899× (SSP2-4.5) / 0.934× (SSP5-8.5)**.
  **Expect SLR@2100 = 45.53 cm to move**; say so before it surprises anyone.
- **P3** — the 2300 scorecard still clears with the mid tap REMOVED: **10 of 64**
  tap cells, three fewer parameters than the mock.
- Modern shares confirm the design: high still dormant (0.19 vs 0.37 volume,
  ratio ~0.51), mid still over-active (0.23 vs 0.17, ~1.3).
- Aschwanden (**PMC6584365**, not local): NW land-terminating *"by the year 2300
  (RCP 8.5) or 2500 (RCP 4.5) … ice discharge there is greatly reduced"* — a
  DECELERATION at the horizon's edge, which is why mid gets no tap.

---

## 8. SUGGESTED ORDER OF WORK

1. Extend `--gis-check` (1624–1635) to print the per-basin modern shares from a
   given θ **before** adding the likelihood term. A diagnostic that can already
   measure the thing is how you tell a wiring bug from a physics result.
2. Add the 3-basin state to the Greenland component
   (`julia/greenland_ab_component.jl`) and the per-basin free parameters, with
   the shares term **switched off**. Confirm the total is unchanged when the
   basins are collapsed — a nesting check, the analogue of the mock's 6e-17 gate.
3. Turn the shares term on. Re-run `--gis-check`.
4. Short smoke chain BEFORE production; watch acceptance for trap 1.
5. Only then a production chain, and expect the headline to move.

---

## 9. NON-OBVIOUS STATE

- **L12 remains canonical and untouched.** Nothing since handoff c has run a
  chain or moved a posterior.
- **Two inherited modified files, sixth handoff carrying them:**
  `outputs/mcmc/overdispersed_starts.csv` (all 4 start rows replaced Aug 17;
  backups `.pre_extc_bak` / `.pre_l12_bak`) — **committing it changes what a
  future chain starts from, so it is Marcus's call**, and it is about to become
  live since this work runs chains; and `figures/diag_gis_regional_driver.png`.
- Stray zero-value file in the WRONG repo:
  `FaIRtoFrEDI/outputs/log_scope_gis_basin_mock.txt` (288 bytes, a mis-`cd`
  error log). Left in place, flagged.
- macOS has no `timeout`; pin `OPENBLAS_NUM_THREADS=1`.
- Mouginot paper + SI + sd01 + sd02 are at
  `~/Documents/2026/ClaudeDocs/Papers/Mouginot/`. Aschwanden and TC 19:6887 are
  NOT local.

---

## 10. FILES

**Python, this arc:** `scope_gis_3basin_partition.py` (the prototype),
`diag_gis_basin_lit_check.py` (blocks 1b partition + 1c stationarity/window
scan), `diag_gis_zone_driver_scope.py`,
`scope_gis_basin_zonespace{,_amp_sens}_*.py`.

**Key outputs:** `outputs/scope_gis_3basin_partition.csv`,
`outputs/diag_gis_basin_lit_check.csv`, `outputs/gis_amp_shape_all.csv`.

**CHANGELOG:** entries i–o and 19a carry the full reasoning, including the
framings that were corrected rather than deleted.
