# Handoff — L12: the Greenland channel ordering, imposed and accepted

**Start-here document for the next session.** Repo `SLR-RFF-BRICK`, branch
**`ladrillo-dev`**, HEAD `d510643`, **pushed and in sync with origin**.
Predecessor: `notes/handoff_2026-08-16_thread5_CD.md`.

**Bottom line: the one open decision in the predecessor's §7 is closed. The
channel ordering was priced, implemented, calibrated, accepted, and promoted.
L12 is canonical. All four pre-registered predictions held. Nothing is blocking.**

---

## 0. WHAT CHANGED IN ONE TABLE

| | L11 (was canonical) | **L12 (now canonical)** |
|---|---|---|
| Greenland channels | free — 37.53 % ordered | **constrained — 100.00 % ordered** |
| τ_fast / τ_slow @ T̄ | 71.8 / 105.4 yr | **61.7 / 194.1 yr** |
| draws with max(τ) > 221 yr | 13.61 % | **39.96 %** |
| SLR@2100 (pooled) | 45.28 | **45.53** |
| SLR@2150 (pooled) | 70.78 | **70.84** |
| R̂ SLR@2100 / @2150 | 1.002 / 1.005 | **1.002 / 1.004** |
| unconverged marginals | 18 | **16** |
| `ais_iceflow0` R̂ | 2.449 | **1.755** |
| acceptance | 0.236–0.238 | 0.237 ×4 |

---

## 1. THE ARGUMENT, BECAUSE THE CONCLUSION REVERSED MID-THREAD

The predecessor asked: buy a ~5 h re-tune to impose the ordering, or ship L11
documented? **My first answer was "don't buy it", and that answer was wrong on
framing, not on facts.**

What I measured first: **the inversion is a MAP artefact, not a posterior
property.** L11's medians were already correctly ordered (`alpha_s` 0.00220 <
`alpha_f` 0.00373), the *opposite sign* from the offline optimum's
`alpha_f − alpha_s` = −0.00424. The τ-ordering share was **flat at 61–69 %
across T = 0–15 K**, so §5's T2 crossover at `T_south` = 1.740 K is also
MAP-only — it is a labelling degeneracy, exactly as T1's bit-identical
exchangeability implies. Splitting L11 into ordered/inverted halves and
projecting both put the constraint at **≤0.85 cm @2100**, so I concluded it
wasn't worth the compute.

**Marcus's correction: the priority is a correctly-labelled model, and under
that priority the same number argues the other way.** ≤0.85 cm means the fix is
*safe* — it cannot disturb the headline SLR — so it is cheap insurance on
interpretability rather than a result-changing intervention. Both readings use
the identical measurement; only the objective differs. **If this comes up again,
do not re-litigate the cost-benefit — the number was never in dispute.**

**Why relabelling is not an option (the load-bearing subtlety).** The obvious
cheap fix is to swap labels on inverted draws. It fails: swapping the channels
also swaps the *share*, so the relabelled draw violates Mouginot (T1's 44.20
nlp, all of it that term). "SMB carries 73.5 % of the modern rate" and "SMB is
the faster channel" **pick out different channels in ~32 % of draws**. That is
an identification conflict, precisely what T2 predicted when it found a share
cannot pin a sensitivity. It has to be imposed in calibration, jointly.

---

## 2. THE CONSTRAINT — MECHANICS WORTH NOT REDISCOVERING

`--gis-ordered`, OFF by default (L11 and earlier stay bit-reproducible; verified
byte-identical control chain). Implemented as a **−∞ region in `logposterior`**,
evaluated with the other hard rejections and **before `run(m)`**, so a rejected
proposal costs no model evaluation.

**It is a WEDGE, not a box.** In the sampled coordinates:

    alpha_s = w·e^ℓ/T̄ ≤ alpha_f      AND      beta_s = (1−w)·e^ℓ ≤ beta_f

Both arms are joint in (ℓ, w) *and* coupled to `alpha_f`/`beta_f`, which are
themselves sampled. **No `lo`/`hi` change can express this** — that is why it
lives in the log-prior. `julia/test_gis_ordering_wedge.jl` asserts it in both
directions (11 checks), including that **equality is ADMITTED** (the ordered
optimum binds exactly there, so a strict `<` would exclude it) and that the same
(ℓ, w) flips verdict under different `alpha_f`.

### The trap that cost an hour: the prior centre is itself inverted

First constrained smoke run gave **acceptance exactly 0.0**, every sd ~1e-15,
chain frozen. The control without the flag gave 0.257 — which **ruled out the
ADCOV size-collision explanation** and identified the wedge.

Cause: `GIS_NATIVE_MU` is (`alpha_s` = 0.0070727, `beta_s` = 0.0010) while
`gis_alpha_f` is centred at 0.0028487. **The prior centre is the very defect the
constraint removes.** `logposterior(θ0) = -Inf` makes every MH ratio
`(-Inf) − (-Inf)` = **NaN**, which compares false, so everything is rejected.

Repaired the **start only** — to L11's ORD-half medians (`alpha_s` 0.00147,
`beta_s` 0.00237, `alpha_f` 0.00415, `beta_f` 0.00754), which are strictly
interior and carry real posterior mass. Deliberately **not** §5's T3 ordered
optimum, which binds at equality *and* rails `beta_s` at 1e-6 — that would start
on a boundary and a rail. **Priors untouched**, so the constraint is the clean
operation "the same prior, TRUNCATED", not a different prior.

Added a **structural guard**: `logposterior(θ0)` must be finite on the default
path. `--overdisperse` already asserted this; the default path only *printed*
it, which is how a −∞ start surfaced as "accept 0.0" instead of an error.

---

## 3. THE PRE-REGISTRATION, AND HOW IT SCORED

Written 2026-08-17 before any L12 chain existed (`b4d59af`).

| | prediction | outcome |
|---|---|---|
| **P1** | SLR@2100 within ~1 cm | **+0.04 / +0.13 / +0.24 cm** (585/245/126) — PASS |
| **P2** | ordering → 100 % | **100.00 %**, 10000/10000 — PASS |
| **P3** | τ separate, max(τ) > 113 yr | **61.7 / 194.1 yr**, ordered at 100 % across T = 0–15 K — PASS |
| **P4** | acceptance > ~0.15 | **0.237** — PASS |

**P1 was flagged in advance as "the one I could be flattered by."** It passed,
and the corroboration is stronger than the pass: GIS moved in the predicted
direction and roughly the predicted amount — ssp585@2300 **41.97 → 45.59**
(+3.61) against the ORD-vs-INV forecast of +4.35, with ORD's absolute 44.51
landing within ~1 cm of L12's 45.59. **The ORD-filter was a fair proxy for a
constrained calibration** — worth reusing before buying compute again.

**P3's falsifier did not fire.** The risk was the constraint being satisfied
trivially by collapsing both channels onto the boundary — D2's failure mode
("fit by deleting the machinery it was given"). Instead the pair separated.

---

## 4. THINGS I RAISED THAT DID **NOT** SURVIVE — do not re-inherit

1. **"p95@2100 widened ~3 cm."** Flagged at the gate from the convergence
   diagnostic (75.57 → 78.55). On the full projection the band widths are
   essentially unchanged (ssp585@2100 49.6 → 47.9). It was that diagnostic's own
   1600-draw sampling. **Not a real change in posterior spread.**
2. **"The `beta_s` 1e-6 rail is fixed."** It is absent (0.000 % of `beta_f` at
   the rail) — but that rail was a **native-coordinate artefact already gone in
   L11** under the (ℓ, w) reparameterisation. **L12 did not fix it**, and the
   predecessor's "still undiagnosed" note applies to the offline optimum only.
3. **The four chains all reporting acceptance 0.237** looks like suspicious
   uniformity. It is not: `RAM_sample(..., opt_α=0.234)`
   (`calibrate_mcmc_ext.jl:1658`) — the sampler *targets* it. Checked, not
   assumed.

**Open and NOT explained:** `ais_iceflow0` improved 2.449 → **1.755**, and 18 →
16 unconverged marginals. The wedge truncates the *Greenland* block; there is no
obvious mechanism by which that improves an *AIS* marginal. Could be real (a
smaller wandering volume) or chain-to-chain luck on a known-bad ridge. **It does
not affect the deliverable criterion, and I did not test it.** If someone wants
it, the test is a second constrained vintage on different seeds.

---

## 5. STATE OF THE POINTERS

`LADRILLO_POSTERIOR_CSV` → **L12**. `LADRILLO_POSTERIOR_L11_CSV` and
`..._L10_CSV` exist as named constants on the extC precedent.

**The trap to know about.** `diag_r19_modern_rate.jl --check-l10` anchors on the
L10 constant *deliberately* — L10 is the last NATIVE-Greenland posterior, so it
is the only fixture exercising the branch where `ladrillo_native_greenland!` is
a no-op. Repointing it at the canonical constant would silently load a newer
vintage under an "L10" label and fail the 0.1490 value. **Verified still 0.1490
[0.0544, 0.2300], 3.03× after both promotions.** Nothing anchors on L11 the same
way — swept and confirmed.

Tag defaults in `project_ssps_components_ladrillo.jl`,
`posterior_predictive_ladrillo.jl`, `diag_slr_convergence_by_chain_ladrillo.jl`
**derive from the canonical constant** and follow automatically. Hand-maintained:
`diag_gis_block_convergence.jl` (pure-CSV, no Mimi include) and
`scope_greenland_bochow2026.py` (+ its `LADRILLO_TAG` label).

**Deliberately NOT repointed** — pinned provenance, not staleness: the extA108
pulse drivers, the extC variant-detection fixtures, the stock-SIMPLE Mengel
pulse drivers, and the L10-vs-D1 comparison arms in
`diag_r19_{vs_zekollari2024,hindcast_visibility,option_b_evidence}.jl`.
`diag_gis_ordering_in_l11_posterior.py` **defaults to L11 on purpose**: its
unsuffixed output IS the measurement the L12 decision rested on.

---

## 6. CAVEATS THAT STILL SHIP WITH THE DELIVERABLE

Unchanged from the predecessor except where noted:

- **16 marginals unconverged** (was 18) — L12 may be used for projected SLR and
  anything derived from it, **NOT for parameter-level inference**.
- the commitment is **unidentified** (the φ·L_eq ridge);
- the **amp(GMST) law is projection-side only** — the calibrator runs at constant
  `GIS_AMP` = 1.92. Justify or align. **Still open.**
- `gis_g` = 0 and `gis_v0` = 7.42 m are **fixed by argument, not fitted**;
- G4 divergence per the predecessor's §6;
- **the channel ordering is IMPOSED, not identified.** L12 does not make the data
  prefer it — T1's exchangeability is unchanged. What L12 changes is that the
  shipped posterior is now *consistently* labelled.
- **Option C remains abandoned**; the recommended surviving use (a committed-loss
  diagnostic reporting both PISM and Yelmo arms) is **still not built**.

---

## 7. WHAT IS ACTUALLY LEFT

**No blockers.** In rough priority:

1. **The committed-loss diagnostic** (predecessor §4's surviving use of C) —
   evaluate `V_eq` per scenario as post-processing, report both ladder arms
   (3.52× at SSP1-2.6), label as multi-millennial equilibrium, keep separate from
   realised SLR. Needs no refit and no vintage. Data are on disk
   (`greenland_equilibrium_bochow2023.csv`, 31 rows, both families).
2. **The `d2_basis` one-liner** — deferred to "whatever vintage this Greenland
   work produces". **L12 was that vintage and it did NOT go in.** Still parked.
3. **The amp(GMST) calibration/projection mismatch** — the largest unaddressed
   methodological caveat.
4. Regenerate any L11-vintage deliverable figures/tables against L12 if they are
   to be shown; the numbers move by <1 cm at 2100 but labels must track.

---

## 8. NON-OBVIOUS STATE

- **All work is PUSHED**, `9c7658d` → `d510643` (8 commits this session).
- **L11's `overdispersed_starts.csv` is backed up** to
  `overdispersed_starts.csv.pre_l12_bak` — the live file is now built from the
  L12tune chain. Rebuilding L11 requires restoring it.
- The four L12 chains (~2.29 GB each) and `chain_L12tune_seed2026_n1000000.csv`
  (~1.1 GB) are on disk and **gitignored**, as are the posterior subsamples.
  `parameters_subsample_brick_mengel_L11{ord,inv}.csv` are likewise gitignored
  but **deterministically regenerable** from `split_l11_by_gis_ordering.py`
  (fixed seed 2026).
- **Log banners are stdout-block-buffered when redirected** — they appear only
  at process exit, because the progress bar writes to stderr. A live log with no
  config banner is NOT a sign the flag was dropped; check `ps` instead. Confirmed
  by the banner appearing on completion.
- `run_l12_production.sh` carries a precondition the L11 script did not need:
  `overdispersed_starts.csv` must be **newer** than the tune chain, because
  starts built from an unconstrained chain would place chains outside the wedge.
- **macOS has no `timeout`** — do not reach for it in these drivers.
- Pin `OPENBLAS_NUM_THREADS=1` for parallel chains (4.8× on this M4). L12
  production ran ~4h45 for 4 × 2M.

---

## 9. FILES

**Created this session**
| file | purpose |
|---|---|
| `python/diag_gis_ordering_in_l11_posterior.py` | ordering share, τ sweep, wedge-not-box (`--tag=`) |
| `python/split_l11_by_gis_ordering.py` | ORD/INV split, size-matched, seeded |
| `python/diag_gis_ordering_projection_cost.py` | prices the constraint on the deliverable; mixture + signature gates, AIS null control |
| `julia/test_gis_ordering_wedge.jl` | 11-check mutation test of the wedge |
| `julia/run_l12_production.sh` | 4 × 2M launcher |

**Modified:** `julia/calibrate_mcmc_ext.jl` (wedge, start repair, θ0 guard,
banner), `julia/ladrillo_projection.jl` (L12 canonical, L11/L10 constants, header),
`julia/diag_r19_modern_rate.jl`, `julia/project_ssps_components_ladrillo.jl`,
`julia/posterior_predictive_ladrillo.jl`,
`julia/diag_slr_convergence_by_chain_ladrillo.jl`,
`julia/diag_gis_block_convergence.jl`, `python/scope_greenland_bochow2026.py`,
`CHANGELOG.md`.

**Key outputs:** `data/MimiBRICK/parameters_subsample_brick_mengel_L12.csv`,
`outputs/ssps_components_2300_L12.csv`, `outputs/mcmc/slr_convergence_L12.csv`,
`outputs/diag_gis_ordering_in_l11_posterior{,_L12}.csv`,
`outputs/diag_gis_ordering_projection_cost.csv`, `outputs/mcmc/adapted_cov_L12.csv`.
