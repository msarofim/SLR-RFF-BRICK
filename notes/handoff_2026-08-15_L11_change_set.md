# Handoff 2026-08-15 — the L11 change set is BUILT; production is gated on one more tuning run

**Pickup document.** Read with `notes/spec_2026-08-14_next_calibration.md` (the
work order), `notes/design_2026-08-14_r19_replacement_term.md` (read its REVISION
first — the recommendation in §6 is withdrawn), and the CHANGELOG entries for
2026-08-14. Do not re-derive the evidence; it is all recorded.

Repo `SLR-RFF-BRICK`, branch **`brick-mengel-vnext`**, tip **`cb21def`**.
All six suites pass. Nothing pushed.

---

## 0. WHERE THINGS STAND

Thread 4's change set is implemented and verified. Thread 5's structural question
is diagnosed but not fixed. Nothing has gone to production.

| item | state |
|---|---|
| D1 — drop the total | **BUILT**, default ON, `--keep-total` restores |
| GlaMBIE R19 rate term | **BUILT**, default ON, `--no-r19-rate` |
| Rung σ tightened ÷d₂(8) | **BUILT**, default ON, `--rung-sig-legacy` |
| D2 — δ(t) on gsic+steric | **BUILT**, default ON, `--no-d2`; basis CORRECTED twice |
| Greenland (ℓ, w) reparam | **BUILT**, default ON, `--gis-native` |
| Tuning run for the proposal | **STALE** — see §4. One more needed |
| Production chains | **NOT STARTED** |
| Thread 5 (Greenland 2300) | diagnosed, unfixed, deliberately out of scope |

**55 → 53 (D1) → 57 (D2) sampled parameters.** New columns: `d2_gsic_{1,2}`,
`d2_steric_{1,2}`, `gis_slow_ell`, `gis_slow_w`. Gone: `sd_dang`, `rho_dang`,
`gis_alpha_s`, `gis_beta_s`.

---

## 1. THE FOUR VERIFICATION GATES, and what each is worth

1. **Restore-path bit-identity.** `--keep-total --no-r19-rate --rung-sig-legacy
   --no-d2 --gis-native` reproduces the pre-change calibrator with **max |diff| =
   0** over 300 iterations at seed 2026. Verified at every commit.
   **CAVEAT, important:** this holds only when the PROPOSAL is held fixed. Once
   `adapted_cov_L11tune*` exists the restore path seeds from a newer covariance
   and chains are no longer bit-identical — that is expected, the restore flags
   restore the TARGET not the proposal. To re-verify, temporarily move the L11
   covariances aside so both runs fall back to `adapted_cov_L10tune2`.
2. **Mutation tests.** Δ`log_post` at the identical θ₀: R19 rate **−1.1953**,
   rung σ **+0.1142**, total **−224.92**, D2 **−1.6969**. Nothing inert.
3. **Load-time assertions.** T̄ vs the spec's 1.963; (ℓ,w) round trip exact; the
   (ℓ,w) prior centres map to the native ones; D2 mean-zero, unit-RMS,
   ⊥`DELTA_RAMP`, ⊥`S(t)`. **Two of these caught real bugs** (§3).
4. **The suite.** `./run_ladrillo_tests.sh` — caught the θ₀ regression AND the
   assertion/basis metric mismatch. Run it BEFORE committing, not after; I got
   that ordering wrong once and the failure is on record in `eb26784`.

---

## 2. THE DESIGN DECISIONS, and why (none are obvious from the code)

**Rung σ ÷ d₂(8) = 2.847, not ÷2.** The stored `sig*` are HALF THE FULL
inter-model range of the 8 GlacierMIP3 models treated as 1σ
(`d1d_fourrung_seam.py`). For n normal draws the expected range is d₂(n)·σ and
d₂(8) = 2.847, so half-range overstates σ by 1.42×. **Order statistics, not a
chosen number.** Roughly doubles R19's rung χ² (3.47 → ~7.04); SLOWP and FAST
were already ≤0.66σ and are unaffected.

**GlaMBIE R19 σ = 0.11615, which SUPERSEDES `GLAMBIE_ERR_INFLATE` = 1.5 rather
than compounding with it.** That inflate was a partial compensation for the same
quadrature-over-24-years understatement that full serial correlation handles.
Multiplying both would double-count. The term is weak (0.42σ) and that is honest:
R19 has 8 GlaMBIE input datasets, **zero gravimetry** (GRACE cannot separate the
Antarctic periphery from the ice sheet) and one DEM-differencing estimate.

**(ℓ, w) prior: ℓ ~ N(−4.2074, 1.0), w flat on [0,1] centred 0.9328.** σ_ℓ = 1.0
is **Marcus's call** — τ_slow 23-172 yr at 1σ, to 469 at 2σ, covering L10's
posterior (29-136 yr) with room above WITHOUT admitting the millennial arm.
Widening to reach the commitment ridge's ~1300 yr was offered and **declined**:
without an external Leq(T) constraint that admits the ridge rather than resolving
it. The reparam is a CONDITIONING fix; the commitment question stays in thread 5.
Centres are DERIVED from the native ones through the transform so θ₀ is
unchanged — the calibrator centres `beta_s` at 1e-3 deliberately, off its rail.

**D2 basis ⊥ constant, ⊥`DELTA_RAMP` (gsic), ⊥`S(t)` (steric), PLAIN metric.**
See §3 — this took three attempts and the third was worse than the second.

---

## 3. THE FOUR BUGS THIS SESSION CAUGHT, and how

Carry these; each was a silent failure mode that would not have shown up in a
posterior.

1. **D2 basis was not mean-zero.** Projecting out `ones` then a non-orthogonal
   `DELTA_RAMP` re-introduces a constant (gsic col 1 mean 0.605). Classic
   Gram-Schmidt error — the protect set must be orthogonalised against itself
   first. Caught by its own load-time assertion.
2. **The (ℓ, w) prior centres silently moved θ₀.** Centring ℓ on the offline
   optimum discarded the calibrator's deliberate off-rail `beta_s` = 1e-3, moving
   θ₀ from (0.00707, 0.00100) to (0.00354, 0.00695). Caught by the suite as
   Mouginot surface share 0.7716 vs 0.7351. A θ₀-equivalence assertion now fails
   at load instead.
3. **The ADCOV positional-index trap.** `adapted_cov_L11tune` is 57×57 and NK is
   also 57, so the exact-size branch fired and would have applied `gis_alpha_s`'s
   proposal scale (~0.005) to `gis_slow_ell` (~−4.2). **SIZE IS NOT IDENTITY.**
   Nothing downstream would have flagged it — just a badly-scaled chain. Guarded;
   L11tune is now name-mapped (55 of 57, fresh diagonal for the Greenland pair).
4. **The D2 steric basis was degenerate with `thermal_alpha` anyway** (§ below).
5. **A run that died at load looked "still running" for 11 hours.** `D2chk3` was
   launched in the same command that reverted the `ip` function but BEFORE the
   assertions were aligned, so the file did not load and Julia exited during
   setup. Two compounding errors: launching a run without first checking the file
   loads, and then status-checking with `pgrep -f calibrate_mcmc_ext`, which
   MATCHES THE BASH WATCHER'S OWN COMMAND STRING (it contains the julia
   invocation as text). The check was structurally incapable of detecting the
   death. **Match the specific invocation** (`calibrate_mcmc_ext.jl 200000`) and
   wait on the PROCESS exiting, then test for the output file — a watcher that
   only waits on a file spins forever when the job dies.

### The D2 basis, three attempts — read this before touching it
`thermal_alpha` rescales the SHAPE `S(t)`, not the level, so orthogonality to the
constant does not protect it. Measured on 100k post-burn draws each:

| basis | corr(d2_steric_1, α) | corr(d2_gsic_1, gic_delta) | thermal_alpha |
|---|---|---|---|
| 1. ⊥ constant only | **−0.724** | +0.085 | 0.16521 |
| 2. ⊥ S(t), plain metric — **SHIPPED** | +0.349 | **+0.161** | 0.15781 |
| 3. + 1/ε² likelihood-metric weighting | −0.297 | **+0.787** | 0.14593 |

**Construction 3 was the "obvious improvement" and is worse.** The posterior
metric is neither the plain nor the diagonal one — it is the full AR(1)-correlated
heteroskedastic precision plus prior curvature — so chasing posterior correlation
by changing the DESIGN metric is whack-a-mole. Construction 2 is justified
physically (⊥ the driver shape it must not duplicate), not by minimising a
number. `D2_WT` is retained ONLY to document the rejected weights. Do not re-try 3.

`S(t)` is simply the OHC forcing up to an additive constant: `te_sea_level`
accumulates `Δ_oceanheat`, so the sum telescopes to OHC(t) − OHC(1).

---

## 4. THE IMMEDIATE NEXT STEP — a third tuning run

`adapted_cov_L11tune2_seed2026.csv` is **STALE**: it was tuned on the
constant-only D2 basis (construction 1), before the S(t) correction.
`adapted_cov_L11tune_seed2026.csv` is staler still (pre-reparam Greenland).

```bash
OPENBLAS_NUM_THREADS=1 nohup julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 1000000 2026 --tag=L11tune3 > outputs/mcmc/log_L11tune3_seed2026.txt 2>&1 &
```

~1 hour, common-start (**NOT** `--overdisperse` — `overdispersed_starts.csv` has
no `d2_*` or `gis_slow_*` columns and the calibrator will correctly refuse).
Then **add `adapted_cov_L11tune3_seed2026.csv` to the head of the ADCOV
preference chain**, above `l11b`.

Expect acceptance ~0.24. Cold-start acceptance is ~0.4 now that 55 of 57 rows
name-map.

### Then, before production
- **Rebuild `overdispersed_starts.csv` BY NAME from the tuning posterior**, at
  `ais_iceflow0` quantiles 0.02/0.35/0.65/0.98. Spec §7.1: rebuild, don't slice.
  Random jitter FAILS (200/200 draws gave non-finite logposterior).
- Production = large N_ITER × ≥4 seeds, then `postprocess_mcmc_ext.jl`.

---

## 5. OPEN QUESTIONS, in priority order

1. **Does R19 actually land near GlaMBIE now?** The rate term is only 0.42σ, so
   the tightened rung is carrying it. The width ratios will NOT tell you — that
   was spec §2.2's mistake. Read R19's modern rate against GlaMBIE's 0.049251
   mm/yr directly. L10 sat 3.03× above it.
2. **`thermal_alpha` sits at 0.158** against L10's 0.150 and the
   precision-weighted steric optimum of 0.1395. D2 has not pulled it toward the
   steric-optimal value. Not obviously wrong in a joint likelihood, but watch it.
3. **Thread 5 — Greenland at 2300** is untouched and is the one confirmed
   structural failure: commitment 19-24× below Bochow, unidentified along the
   φ·Leq ridge (14.6 → 58.3 cm at identical hindcast fit). Needs an external
   Leq(T) target, i.e. re-opening Option C, which failed once.
4. **The glacier blocks over-commit and under-realise** (φ 0.61-0.81, commitments
   16-76% above GlacierMIP3 in % terms though ≤0.66σ for SLOWP/FAST). The errors
   partly cancel at 2100 and do not at 2300. Same shape as the Greenland ridge.
5. Branch rename, carried over from handoff 13d.

---

## 6. NON-OBVIOUS STATE

- **Five restore flags**, and all five together restore the pre-change target:
  `--keep-total --no-r19-rate --rung-sig-legacy --no-d2 --gis-native`.
- **`chain_L11tune_seed2026_n1000000.csv` (1.15 GB) and
  `chain_L11tune2_...` (1.15 GB) are both superseded.** Keep the
  `adapted_cov_*` files; the chains are regenerable in ~1 hour each.
- Chains are **seed-reproducible**; the `accept_rate` column is NOT (its
  denominator depends on the requested N). Compare parameter columns only.
- `L11A_NAMES` describes the L11tune layout (current FREE set with Greenland in
  NATIVE coordinates) so that covariance can still be name-mapped.
- **GlacierMIP3 τ provenance is settled** — see
  `notes/note_2026-08-14_tau_provenance_and_johannesson.md`. `tau15` is
  GlacierMIP3's published **τ80** at 1.5 °C (Table S1a col 9); `tau30` is a
  **τ50** at 3.0 °C. Different thresholds; state which when writing the paper.
- Zekollari/GloGEM/OGGM Zenodo archives are NOT committed; fetch commands are in
  `python/scope_glacier_model_constraints.py`'s header.
- Julia `--project=julia_v2`; Python `source ~/climate-env/bin/activate`; pin
  `OPENBLAS_NUM_THREADS=1` for parallel chains (4.8× on this M4).
- Naming: **Ladrillo**. Never `sed s/brickf/ladrillo/g` — `brickf` ⊂ `brickfm`.
- `D2chk3` (200k, construction 2) has **completed** and confirms row 2. It also
  corrected it: I had carried construction 1's `corr(d2_gsic_1, gic_delta)` of
  +0.085 into row 2 without measuring it — the real value is **+0.161**. The
  conclusion is unchanged (construction 3's +0.787 is still far worse), but the
  number was wrong in the first version of this handoff and in `cb21def`.

---

## 7. THIS SESSION'S COMMITS

| commit | what |
|---|---|
| `b253dbf` | thread 5 step 2 — the 2300 flatness is a COMMITMENT defect |
| `205f34c` | Ladrillo vs BRICK 2.0 hindcast scorecard |
| `fbb4920` | AIS spread is inherited from DAIS; our changes NARROW it 42% |
| `cc1e2bc` | D1 behind `--drop-total`, bit-identical when off |
| `22635dd` | D1 short chains — R19 moves, TE does not |
| `859d864` | TE misfit is the OHC DRIVER, not the module |
| `dfb499a` | RETRACT "TE is the one module worse than BRICK 2.0" |
| `06f70ca` / `2095269` | R19 replacement term designed, then bannered |
| `3a9e64b` | WITHDRAW Option B — the total pins R19 at a saturated state |
| `77fbc83` / `67e5b45` / `d51dde9` | Zekollari 2024: fetched, scoped, and what the three products ARE |
| `752839f` / `979a361` / `1c81eae` | SLOWP gap → timescale → dissolves; τ provenance + Jóhannesson |
| `23474a8` | the R19 change set implemented |
| `03f2706` | D2 built |
| `eb26784` / `44be3d6` | Greenland (ℓ, w); then FIX the θ₀ regression |
| `579db33` | ADCOV preference + positional-index guard |
| `cb21def` | D2 steric basis ⊥ S(t) — the third and final construction |
