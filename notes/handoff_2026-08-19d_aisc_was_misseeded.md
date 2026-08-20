# Handoff — `ais_c` was never collapsing; it was seeded with `ais_slope`'s variance

**Start-here document.** Repo `SLR-RFF-BRICK`, branch **`ladrillo-dev`**.
Predecessor: `notes/handoff_2026-08-19c_wrong_model_and_frozen_aisc.md`.

**Bottom line. 19c's one open question — "what collapsed `ais_c` inside L13tune" — has
an answer, and the premise was wrong: nothing collapsed. `ais_c` was frozen from
iteration 1 because `L11_NAMES`, the hardcoded row-order list used to read the nameless
adapted-covariance CSVs, had the four `d2_*` rows in the wrong position, shifting on-disk
rows 35–49 by four. Live `ais_c` received `ais_slope`'s proposal sd — 8.005e-07 against a
posterior spanning 95 — and RAM's multiplicative rank-one update can never re-inflate a
coordinate whose row of `L` is ~0. The whole L13 line is void and quarantined; L12 is
untouched and remains canonical at 45.53 cm. The fix is in (`57959ee`, `b61426c`) and the
re-tune is RUNNING. 19c §3.2's "the AIS block split into two non-communicating modes led
by `ais_precip0_LOG`" was describing a proposal in which three AIS parameters carried
another parameter's scale — it is not a physical finding.**

---

## 1. WHAT IS RUNNING RIGHT NOW, AND WHAT TO DO WHEN IT LANDS

```bash
julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 1000000 2026 --tag=L13tune \
  --gis-ordered --gis-basins --adcov=adapted_cov_L12_seed2026.csv
```

Launched 2026-08-19, ~1 M single chain, ETA ~1 h 50 m total, log at
`outputs/mcmc/log_L13tune_seed2026.txt`. Early behaviour is already categorically
different from the void run: acceptance opens at 0.5 and settles ~0.22–0.30, against
0.0 → 0.007 before.

**When it finishes, in order:**

1. **Read `outputs/mcmc/seed_diag_L13tune_seed2026.txt`** — new file, written before
   sampling, immune to the progress meter. It records the ADCOV, the mapping message, and
   the seven `GEO_NAMES` proposal sds. `ais_c` must read **1.282**.
2. **Verify the tune did not narrow the geometry block** — the step 19c called missing.
   `sqrt(diag(adapted_cov_L13tune_seed2026.csv))` at `ais_c`; anything below ~0.1 means
   stop and diagnose rather than proceed. The new file is written with **parameter names
   as its header**, so read it by name, not by position.
3. **Check the trace, not just the covariance.** `ais_c`'s span over the tuning chain
   should be tens of units. The one-liner that caught this:
   ```bash
   awk -F, -v c=51 'NR>1{v=$c+0;if(NR==2){mn=v;mx=v}if(v<mn)mn=v;if(v>mx)mx=v}
     END{print "span", mx-mn}' outputs/mcmc/chain_L13tune_seed2026_n1000000.csv
   ```
   (col 51 in the 59-param L13 layout, 49 in the 57-param L12 one — **confirm the index
   from the header**, do not carry it across layouts.)
4. **Rebuild the starts** from the new tuning chain and check dispersion in **`ais_c`**,
   not only `ais_iceflow0`:
   ```bash
   cp outputs/mcmc/overdispersed_starts.csv outputs/mcmc/overdispersed_starts.csv.pre_l13b_bak
   julia --project=julia_v2 julia/build_overdispersed_starts.jl \
     outputs/mcmc/chain_L13tune_seed2026_n1000000.csv
   ```
   The void line's starts had `ais_c` spread 1.15e-05 — a direct consequence of the freeze,
   not an independent defect. 19b flagged the starts and was right to, but they were a
   symptom.
5. **`julia/run_l13_production.sh`** (4 × 2 M, ~4 h 25 m in parallel), then postprocess and
   the SLR gate. The script now names this failure at the top and points at the quarantine.

**`outputs/mcmc/overdispersed_starts.csv` is currently the L12 vintage** (restored from
`.pre_l13_bak`); it has 57 columns and no `gis_s_*`, so `run_l13_production.sh` will
correctly refuse to start until step 4 is done.

---

## 2. THE BUG

### 2.1 How a name-based mapping was still positional

Adapted covariances were written `DataFrame(covout, :auto)` → header `x1..xN`. **The file
names none of its rows.** So `embed_cov!(cov0, old, old_names)` maps by name into the
*live* layout while trusting `old_names` to be positionally faithful to the *file*.

`L11_NAMES` was built as

```julia
[k.name for k in prelayout(FREE) if !startswith(k.name, "d2_")] ++
["d2_$(st)_$(k)" for st in ["gsic","steric"] for k in 1:D2_BASIS_N] ++ noise
```

— it pulled the `d2_*` block out of its `FREE` position and re-appended it. But `FREE`
pushes `d2_*` right after `gic_s_r5` and **before** `antarctic_lambda`, so on disk they
are rows 35–38 while that literal placed them at 45–48.

| live slot | received the row of | sd it got | sd it should have |
|---|---|---|---|
| `ais_c` | `ais_slope` | **8.005e-07** | 0.6065 (L11tune3) / 1.282 (L12) |
| `ais_mu` | `antarctic_lambda` | 4.748e-04 | 0.05204 / 0.1145 |
| `ais_bedheight0` | `antarctic_gamma` | 0.1114 | 0.5672 / 0.962 |
| `ais_runoff_Ton` | `ais_bedheight0` | 0.5672 | 0.01388 / 0.0137 |
| `ais_precip0_LOG` | `ais_mu` | 0.05204 | 0.01629 / 0.0276 |
| `d2_steric_2` | `ais_c` | 0.6065 | 0.02006 |

The name **set** matched, so the seeder logged `name-mapped 57 of 57 rows … dropped
⟨nothing⟩` and returned a valid, positive-definite permutation of a valid matrix.
`isposdef` passed. Size matched. Nothing errored.

19c §5.4 said "`embed_cov!` maps by name, so it is not 19b §5.1's positional trap."
**That was wrong**, and it is why the search went to the adaptation instead of the seed.

### 2.2 Why a bad seed is fatal and not merely slow

RAM's update is `M = L(I + η(α−α*)uu'/|u|²)L'` — multiplicative, rank-one along `L·u`,
with `u ~ N(0,I)`. A coordinate whose row of `L` is ~0 contributes ~0 to **every**
proposal, so `α` carries no information about it and the direction can never be
re-inflated. **The seed is the only chance a coordinate gets.**
`RobustAdaptiveMetropolisSampler.jl` was read: there is no ridge and no ε floor, so 19c §1's
"does the adaptation carry a floor" is answered no — but that is not why this happened.

### 2.3 The receipts

| | |
|---|---|
| `ais_c` span, `chain_L13tune_seed2026` (1 M iter, 245,938 moves) | **7.84e-05** |
| `ais_c` span, `chain_L12tune_seed2026` (1 M iter, **same θ0** = 88.809137) | **95.0** (47.50–142.49) |
| `ais_c` span, `chain_L13_seed2026` (2 M iter) | 9.87e-05 |
| global acceptance, L13tune / L13 production | **0.246 / 0.245** |

Acceptance was healthy the whole time. **No run-level summary could see this**; the
diagnostic that settles it is the per-iteration trace.

### 2.4 The fix

`julia/calibrate_mcmc_ext.jl`, commits `57959ee` + `b61426c`:

1. **`L11_NAMES` is a frozen literal** transcribed from the header of
   `chain_L11tune3_seed2026_n1000000.csv` (written in `pn0` order = exactly the order RAM
   wrote the covariance in). It no longer derives from the live `FREE` — derived-from-live
   is what broke it — and a set-equality check warns if the two ever diverge.
2. **New covariances are written `DataFrame(covout, pn0)`.** The header *is* the parameter
   names, so they describe their own row order and need no vintage entry under any future
   layout. The reader prefers a file's own header whenever it is not `x1..xN`. **This is
   the fix that ends the whole bug class**; the rest are belt-and-braces for the legacy
   nameless files.
3. **Geometry seed gate** — prints `sqrt(diag(cov0))` for the seven `GEO_NAMES` and
   `error`s out before sampling if any is below a floor (`ais_c` ≥ 0.05, ~1/30 of L12's
   1.282; `ais_slope`'s 8e-07 is five orders below). Fails at second zero, not after 4 h 25 m.
4. **`--adcov=<name-or-path>`** overrides the seed-preference list explicitly, so the choice
   lives in the run script where it is reviewable.
5. The five L12-line covariances join `L11_VINTAGE_ADCOV` (verified: all six L11/L12 chain
   headers are identical in order), so an L13-layout run can reseed from the **canonical**
   posterior's proposal.
6. **`seed_diag_<TAG>_seed<SEED>.txt`** — ProgressMeter writes cursor-up escapes to the same
   stream as the setup output, so in every redirected run log the seeding line and gate table
   are overwritten within seconds. That is half of why this survived a whole L13 line. Run
   provenance now goes to a file nothing scribbles over.

**Verified end to end:** a 200-iteration L13-config run seeded from
`adapted_cov_L12_seed2026.csv` reports `ais_c` = **1.282** and reproduces 19c §3.1's
independently measured L12 production column exactly (`ais_mu` 0.1145, `ais_bedheight0`
0.962, `ais_runoff_Ton` 0.0137, `ais_precip0_LOG` 0.0276). `ais_c` acquires sd 3.1 within
200 iterations, against 7.8e-05 over 1 M before.

---

## 3. BLAST RADIUS — measured, and it stops short of anything published

The branch fires only when the ADCOV is L11-vintage **and** `NK ≠ 57`; at `NK == 57` an
earlier branch uses the matrix as-is, which is correct. The affected list was read off the
run logs and then **verified against the chains — 6/6, with a clean control**:

| chain | `ais_c` span | |
|---|---|---|
| `D2G_seed2026` (250 k) | 4.12e-05 | FROZEN |
| `D2S_seed2026` (250 k) | 3.60e-05 | FROZEN |
| `GISB1` / `GISB2` / `GISBNOSH` (3 k) | 4.1e-07 / 1.4e-06 / 8.9e-07 | FROZEN |
| `GISBTUNE` (40 k) | 2.79e-05 | FROZEN |
| **`GISB0CTRL` (3 k)** — took the as-is branch | **31.89** | **ok** |

**Unaffected:** `L11tune3`, `L11_*`, `L12tune`, `L12_*`, `D2chk*`, `GISB0CTRL`, and the
`extC` / `ext` / `D1` lines. **The canonical L12 posterior — SLR@2100 = 45.53 cm — is not
affected.**

### 3.1 The 2026-08-16b D2 stream attribution SURVIVES

`D2S` has `ais_mu` frozen as well (sd ratio 0.004 vs L11) and **pinned at 8.42 against
L11's 10.61**, with `ais_bedheight0` 6× under-dispersed at 804.8 vs 786.2. That is a real
concern, because the D2S/D2G arms were compared against L10/L11 baselines that were
**correctly** seeded.

It does not bite, and the reason is measured. In the healthy L12 posterior the AIS
geometry block is essentially orthogonal to `thermal_alpha`:
`corr(ais_c, ·) = −0.035`, `corr(ais_mu, ·) = +0.014`, `corr(ais_bedheight0, ·) = −0.006`,
with `thermal_alpha`'s quintile medians flat to 0.10 sd across `ais_c`'s full 95-unit
range (so nothing nonlinear is hiding under the correlation). Propagating D2S's *actual*
pinning through those slopes moves `thermal_alpha` by **−0.00018 + −0.00004 ≈ −0.0002** —
about **2 % of the +0.01106 steric effect**, 0.03 L12 sd. The steric result (**+1.24 L10
sd**) stands with ~50× margin, and the gsic arm's verdict was already "250 k cannot
resolve an effect". **`ladrillo_l11_thermal` is not retracted.**

Note also that `ais_c` was frozen at 88.81, which is essentially its L12 posterior *mean*
(89.0) — the freeze pinned it in the right place, which is luck, not design.

### 3.2 Still provisional

The `GISB*` **acceptance** readings. The 3-basin `s_b` common-mode degeneracy itself is a
deterministic model-structure measurement (0.0 over c ∈ [0.25, 10]) and does not involve
the sampler, so `gis_basin_scale_degeneracy` stands. But any posterior-level or
acceptance-level claim from those four scoping runs was made on a frozen AIS block, and
should be re-measured before it is ever load-bearing.

---

## 4. WHAT 19c SAID THAT IS NOW SUPERSEDED

Keep 19c for §2 (the `:basins` projection variant — that repair is real and independent)
and §4 (the AIS split verdict — untouched by any of this). Supersede:

* §1 step 1's framing "reseed from a covariance in which `ais_c` actually moves" — correct
  action, wrong reason. The L11tune3 seed *did* have a healthy `ais_c` (0.606); it was the
  reader that misplaced it.
* §1's open question "what collapsed `ais_c` inside L13tune" — nothing did. Answered here.
* §3.2 "the geometry block has partitioned into two non-communicating modes", and the
  `ais_precip0_LOG` / `ais_runoff_Ton` / `anto_alpha` / `sd_ais` cluster table. Those two
  parameters had proposal scales 3–4× too large and `ais_c`/`ais_mu` were frozen, so the
  2+2 split is a property of a broken proposal, not of the posterior. **Do not carry the
  physical reading forward.**
* §5.4 "`embed_cov!` maps by name, so it is not the positional trap." It is the positional
  trap, one level down.

19c §3.3 (both 19b candidates refuted — `gis_amp` within-chain r = 0.028, and the shift is
in the bulk not the tail) **stands**: those are within-chain regressions on
`projection_variant_draws_L13.csv` that do not depend on the AIS block mixing.

---

## 5. TRAPS AND CONVENTIONS FROM THIS SESSION

1. **A permutation of a valid matrix is still a valid matrix.** If a serialized matrix
   does not name its own rows, a hardcoded order list will eventually be wrong and every
   ordinary guard — size, `isposdef`, "mapped N of N, dropped nothing" — will pass. **Name
   the rows on write.** Memory: `nameless_matrix_order`.
2. **Never re-derive a frozen file's layout from live state.** The file cannot change; the
   live layout moves with every flag. Transcribe from an artefact the same run wrote.
3. **"Maps by name" is not the same as "is not positional."** Check which side the names
   are asserted on — the live layout, or the file.
4. **Gate the seed, not just the output.** For a multiplicative adaptive sampler the seed
   is the only chance a coordinate gets, so a seed check is worth more than any number of
   post-hoc convergence diagnostics.
5. **Measure *when* a parameter froze before theorising about *why*.** One `awk` pass over
   the trace showed `ais_c` immobile from iteration 1, which killed the entire
   "adaptation collapsed it" family of hypotheses in about a minute. 19c reasoned about
   RAM's ε-floor behaviour instead and got a plausible, wrong story.
6. **Run provenance must not share a stream with a progress meter.** Write it to a file.
7. Column indices are layout-specific — `ais_c` is col 49 in the 57-param layout and 51 in
   the 59-param one. Always resolve from the header. (I got this wrong once mid-session and
   compared two different parameters.)
8. macOS has no `timeout`; pin `OPENBLAS_NUM_THREADS=1`.

---

## 6. FILES, COMMITS, MEMORY

**Changed:** `julia/calibrate_mcmc_ext.jl` (the five-part fix + `seed_diag`),
`julia/run_l13_production.sh` (names the failure, new re-tune command),
`outputs/mcmc/overdispersed_starts.csv` (restored to the L12 vintage), `CHANGELOG.md` (19e).

**Quarantined:** `outputs/quarantine/20260819_adcov_l11names_misorder/` — the four L13
production chains, the tuning chain, their covariances and logs, the postprocess /
convergence / projection-variant products, and the frozen-vintage starts. ~10 GB, with a
`README.md` carrying the full write-up. **Neither 47.89 nor 19c's corrected 46.23 cm may
be quoted** — both are diagnostics on chains whose AIS geometry never mixed.

**Commits:** `57959ee` (the bug + fix), `b61426c` (seed provenance file). Branch
`ladrillo-dev`.

**Memory:** `l13_wrong_model_frozen_aisc` rewritten (its §2 causal claim was wrong);
new `nameless_matrix_order` (general discipline, indexed under Working conventions in
`MEMORY.md`); `INDEX_slr.md` L13 line replaced.

**Open decisions for Marcus:**
- Whether to re-run the `D2G`/`D2S` attribution arms with a correct seed. My reading is
  **no** — §3.1 bounds the contamination at ~2 % of the effect — but the arms *are*
  formally inconsistent with their own baselines, so it is a judgement call about how much
  that matters for a reportable number.
- Whether the `GISB*` scoping runs need re-measuring (§3.2), which depends on whether
  anything beyond the degeneracy finding is load-bearing.
- `GIS_ZONE` `"south"` → `"all"`, still deferred from 19b and 19c; NOT one line
  (`GIS_AMP` 1.92→2.347 and the amp prior on [1.51, 2.28] move with it), and it will
  legitimately fail `--gis-check` — regenerate the reference, do not widen the tolerance.
- The high-basin volume tap, still deferred; only bites near 2300.
