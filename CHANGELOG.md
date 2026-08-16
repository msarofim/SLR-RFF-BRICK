# Changelog

All notable changes to this project. Older history reconstructed from the
commit log; recent entries are explicit.

## [unreleased] — 2026-08-16c — Thread 5 decisions; "PISM graded vs Yelmo step" is a SAMPLING ARTEFACT

Marcus settled the four blocking decisions in
`notes/scoping_2026-08-16_thread5_greenland_2300.md` §6. Three as recommended:
Bochow **2026 preprint = benchmark only** (the C calibration target is the
*published* Bochow **2023** ladder — verified, see below, so calibration embeds
no preprint); **offline first**, no vintage committed; **test the downstream τ
effect before adopting any form**. Decision 2 was conditional — carry the
PISM/Yelmo arm *unless* outside information tips it to one family.

**Two provenance facts verified before starting** (§6.1 asked for exactly this):

| object | status | role |
|---|---|---|
| Bochow et al. **2023**, Nature 622:528, doi 10.1038/s41586-023-06503-9 | **published**, Zenodo CC-BY-4.0 model output | the equilibrium ladder → `V_eq(T)` fits = the Option-C **calibration target** |
| Bochow et al. **2026**, EGUsphere doi 10.5194/egusphere-2026-614 | **preprint**, provisional; and its Table 2 is already **retracted** by scoping §20 | benchmark projections only |

### The handoff mis-attributed its own load-bearing number
`scoping_2026-08-16_thread5_greenland_2300.md` §2 cites "**28 cm (PISM-like) vs
86 cm (Yelmo-like)**, a factor of three" as a **§19** finding arguing the arm is
decisive. It is not. That number is **§16**'s, from `scope_greenland_commitment.py`
run on curves §16 itself labels *"illustrative … not proposed calibration forms"*,
and it is superseded from both directions:

- **§19.3** ("CORRECTION 1 — the threshold-location arm is not decisive after
  all") explicitly retracts it as an artefact of a ten-times-too-fast transient;
- **§20** then voids §19.3's own basis — the Bochow-2026 Table 2 transcription
  gives `a, c` both negative, so the cubic is strictly monotonic and **has no
  fold at all** — downgrading §19.3 to "plausible and **unverified**", and
  states the 85.7 cm figure "came from my own illustrative logistic (§16), which
  is also **superseded**".

So the arm's decisiveness was an **open question**, not a settled argument, and
the handoff would have had the next session defend a retracted figure.

### Resolved from the raw ladder: `python/diag_ladder_transition_resolution.py`
§18 item 4 and §20 both left "confirm the PISM ladder shape from `pism_debm.zip`"
outstanding. The PISM ladder has been extracted since (2026-08-10), so this is
now cheap — and it kills the last practical argument for preferring PISM:

| family | rungs | GMT grid | largest jump | width | in its OWN finest intervals | drift at jump |
|---|---|---|---|---|---|---|
| PISM-dEBM | 16 | **0.420 K uniform** | 4.64 m | 0.420 K | **1.0× → UNRESOLVED** | 0.047 / 0.106 m |
| Yelmo-REMBO | 15 | 0.084–1.681 K (**refined near its threshold**) | 4.14 m | 0.084 K | **1.0× → UNRESOLVED** | 0.000 / 0.000 m |

**Both transitions are exactly one grid interval wide.** Neither ladder resolves
its own transition, so each apparent width is an **upper bound set by the
sampling design**, not a measured model property. PISM looks "graded" only
because its grid is 5× coarser there than Yelmo's refinement. This confirms
§19.4's "both are cliffs, they differ only in *where*" **from the raw model
output** rather than from the retracted preprint text.

### Where the arm IS decisive — committed loss at low warming only
| SSP | peak GMT (L11) | PISM committed | Yelmo committed | ratio |
|---|---|---|---|---|
| **SSP1-2.6** | **1.92 K** | **1.48–1.64 m** | **4.90–6.05 m** | **3.52×** |
| SSP2-4.5 | 3.19 K | 6.79–7.01 m | 6.60–7.05 m | 1.01× |
| SSP5-8.5 | 7.81 K | saturated 7.40 m | saturated 7.42 m | 1.00× |

Brackets are deliberately **not interpolated** — interpolating across a
transition neither model resolved would invent a shape. This reproduces §19.5
point 2 exactly: **threshold location matters for *commitment*, not for realised
2300 sea level.** Note SSP5-8.5's peak (7.81 K) lies **above the ladder's top
rung** (6.80 K); both families are saturated there, so extrapolation is harmless
at the top but must be stated.

### Tried, and it does NOT adjudicate: the Last Interglacial
The one candidate external constraint. Published GrIS LIG contributions cluster
**3.7–5.5 m** (ranges from 0.4–4.4 up to 4.1–6.2 across methods), which taken at
face value sits near **Yelmo's** post-threshold branch, not PISM's — the
*opposite* of the direction a PISM lean would want. **It cannot be used**, and
the reason is quantified in the source: only ~55% of the Eemian surface-mass-
balance change is attributable to ambient temperature, **~45% to higher
insolation and associated nonlinear feedbacks** (van de Berg et al., Nature
Geoscience doi 10.1038/ngeo1245), whose own conclusion is that projections built
on Eemian temperature–melt relations "may **overestimate** the future
vulnerability of the ice sheet". LIG forcing is orbital / NH-summer; the
ladder's axis is sustained GHG-driven GMT. The mapping is confounded in the
direction that would spuriously favour Yelmo, and the published spread brackets
both families anyway.

### DECISION 2 RESOLVED → carry the arm
No outside information tips it. Bochow's own authors decline to adjudicate and
call for a coordinated intercomparison; **standing** favours PISM (twice in
ISMIP6-Greenland, Goelzer et al. 2020 TC 14:3071; Yelmo not in that ensemble);
**physics on the disputed mechanism** favours Yelmo (REMBO's retreat-precipitation
negative feedback, which dEBM-simple cannot represent); the **graded-vs-cliff**
tiebreak is now measured to be a sampling artefact; and the **paleo** constraint
is confounded. Marcus's stated condition therefore resolves to **carry both arms
through to the reported results**, per scoping §19.5's committed-loss diagnostic.

### DECISION 4 RESOLVED → not blocking; the premise does not hold
Marcus chose "test the downstream τ effect first". The test is structural and
quantitative, not a run (`python/diag_greenland_exposure_in_pulse_metrics.py`).

**Structural.** Decision 4 assumed "the CH4-vs-CO2 SLR pulse work reads this
module". **It does not.** All four pulse drivers (`project_pulse_hybrid_mengel`,
`pulse_signsweep_brick_mengel`, `run_mimibrick_pulse_versioned`,
`project_pulse_ssp245_mengel`) build via **`build_brick_mengel`**, which replaces
only the **glacier** slot with `glaciers_mengel` and leaves Greenland as **stock
MimiBRICK SIMPLE**. The Ladrillo A+B Greenland is installed **only** by
`build_brick_nu3_gis`, which no pulse driver calls. The drivers' own parameter
lists confirm it — they update `greenland_a/b/α/β/v₀` (stock SIMPLE), never
`gis_c1/gis_c0/gis_alpha_f/gis_beta_s` (A+B). A Greenland τ change cannot reach
these metrics until a driver is repointed.

**Quantitative** — Greenland's share of the weighted marginal pulse response:

| horizon | AIS | GSIC | **GIS** | TE | | CO2 GIS | CH4 GIS | gap |
|---|---|---|---|---|---|---|---|---|
| 2130 | 78.8% | 1.6% | **3.9%** | 15.7% | | 3.9% | 4.6% | **0.7 pp** |
| 2150 | 80.2% | 1.3% | **3.9%** | 14.6% | | 3.9% | 4.6% | **0.7 pp** |
| 2180 | 81.6% | 1.1% | **4.0%** | 13.3% | | 4.0% | 4.7% | **0.7 pp** |

(AIS/GSIC/TE columns are the CO2 pulse; Antarctica dominates at ~79–83%.)
Greenland is ~4% of the marginal and carries a **near-equal share in both
pulses**, so it is largely **common-mode in the CO2e ratio** — its influence on
the reported metric is smaller still than its 4% share.

**Caveat, stated not buried:** those shares are measured under the stock SIMPLE
Greenland. A C+D Greenland carries a ~20× larger commitment *and* a much slower
τ, which push the 100–150 yr marginal in **opposite** directions, so the
post-change share is not determined by this diagnostic. What is established is
the base the change starts from, and the decoupling. **C+D is not gated on the
pulse work**; re-run this diagnostic if a pulse driver is ever repointed at
`build_brick_nu3_gis`.

## [unreleased] — 2026-08-16b — ANSWERED: the D2 **steric** basis carries the `thermal_alpha` shift

8 chains, 4 x 250k per arm, acceptance 0.279-0.295
(`julia/run_d2_stream_attribution.sh`), measured by
`python/diag_d2_stream_attribution.py` under `22635dd`'s mixing gate.

| arm | median | vs L10 | L10 sd | MIX | verdict |
|---|---|---|---|---|---|
| L10 no D2 | 0.15026 | — | — | — | — |
| L11 both streams | 0.16006 | +0.00980 | +1.31 | 19.7 | REPORTABLE |
| **D2S steric only** | **0.16133** | **+0.01106** | **+1.48** | **11.5** | **REPORTABLE** |
| D2G gsic only | 0.15265 | +0.00239 | +0.32 | 1.4 | NOT RESOLVED at 250k |

**H-A confirmed.** Netting out D1's own +0.24 sd, the steric stream alone moves
`thermal_alpha` **+1.24 L10 sd**. **H-B not supported** — the gsic arm fails the
gate at 1.4x, and it has the widest between-chain spread of any arm (0.00170), so
the honest reading is "250k cannot resolve an effect", not "the effect is zero".
Net of D1, gsic alone is +0.08 sd, i.e. nothing.

**The prediction came first, and that is the point.** D1 removed the total from
the likelihood, so nothing rewards the component sum and there was no pathway for
a gsic partition trade. The glaciers-down/steric-up near-cancellation in the
projected total is **two independent effects of similar size, not a trade**. The
first 2026-08-16 handoff asserted "H-B is not the weaker hypothesis"; that was
wrong, was corrected before these chains finished, and the chains agree with the
correction.

**The streams are SUB-ADDITIVE.** Steric-only moves alpha *further* (+1.48) than
both streams together (+1.31); the two arms sum to 137% of the joint move. Adding
the gsic term slightly pulls the steric-driven shift back. Not diagnosed.

### What this opens — and it is a one-line change
`d2_basis` uses the **plain** inner product, a measured and justified choice —
but the justification was driven by the **gsic** side: weighting by `1/eps^2`
moved `corr(d2_steric_1, thermal_alpha)` from +0.349 to −0.297 ("no real gain")
while pushing `corr(d2_gsic_1, gic_delta)` from +0.161 to **+0.787** ("much
worse"). We now know the gsic stream does essentially nothing to alpha. **So the
weighted metric can be applied to the steric stream ONLY**, keeping the plain
metric on gsic — which sidesteps the exact objection that killed it. One line at
the `d2_basis` call site, plus a tuning run.

### Quarantine
`outputs/quarantine/20260816_adcov_size_collision/` — four pre-fix smoke chains.
Two were genuinely bugged (acceptance 0.0 under the covariance size collision);
all four are quarantined because they share the `chain_<TAG>_seed*.csv` **glob**
that `per_chain_medians` uses, and a 2000-iteration stub pollutes a per-chain
median just as badly as a bugged one does. The diagnostic now asserts a minimum
chain length rather than trusting the glob.

## [unreleased] — 2026-08-16 — L11 deliverable figures; the change set is neutral on the total and moves `thermal_alpha` AWAY

### The figure chain is `--tag=`-driven end to end
The three memo figures existed only on L10, and every driver below
`posterior_predictive_ladrillo.jl` still wrote a bare or L10-hardcoded filename —
so producing L11 figures would have silently overwritten the L10 deliverable in
place. Tagged the rest of the chain the way the hindcast driver already was:

| driver | now |
|---|---|
| `julia/project_ssps_components_ladrillo.jl` | `--tag=`; `OUT` follows it |
| `python/ladrillo_model_comparison.py` | `--tag=`; outputs suffixed **symmetrically** |
| `python/plot_ladrillo_memo_figures.py` | `--tag=`; drives inputs, figure filenames, and a `VINTAGE` title stamp |

**Symmetrically** is the choice worth recording: there is no bare filename that
silently means one vintage. `ladrillo_model_comparison.csv` became
`..._L10.csv`. And an undeclared tag is a hard error — a new vintage must be
added to `TAG_DESC` or the figure script refuses to run, so a title cannot go
stale behind a renamed input.

**Regression-gated on L10 at every step.** `ssps_components_2300_L10.csv` and
`ladrillo_model_comparison_L10{,_spread}.csv` regenerate **bit-identical**;
`ladrillo_L10_fig1` differs from the retired untagged figure only in pixel rows
26-54, the suptitle. All six suites pass. Retired
`figures/ladrillo_fig{1,2,3}_*.png`; nothing referenced those names.

**Figure 1's total panel, L11.** D1 drops the Dangendorf total from the
likelihood, so the total has no calibrated error model and its predictive band is
all-NaN. `fill_between` draws *nothing* from NaN — the panel would have looked
like an ordinary result while the legend still promised a predictive band. It is
now marked OUT-OF-SAMPLE in red with the reason on the panel, keyed off the data
rather than off the tag.

### The projection half of the comparison — `python/diag_l10_vs_l11_projection.py`
The scorecard scores the hindcast, which is where the change set was argued and
accepted. This asks what it does to what the posterior is actually licensed to
produce.

**Near-neutral on the TOTAL; a partition trade underneath it.** Total at 2100
moves **−0.28 / +0.27 / +0.83 cm** across SSP1-2.6 / 2-4.5 / 5-8.5 — but in every
scenario glaciers fall ~1.0-1.2 cm while steric rises ~0.9-1.7 cm. By 2300 under
ssp585: glaciers +0.7, gis +2.9, te +6.4, **total +8.3 cm**. AIS untouched, as
the hindcast scorecard already said.

**`thermal_alpha` 0.15026 → 0.16006, +1.31 L10 sd — and this one is a finding.**
Mixing-gated under the `22635dd` rule: worst between-chain spread in either arm
is 0.00050, so the **mix ratio is 19.7** against a threshold of 2.0. All eight
chains agree. `te_sea_level` is exactly `te_s0 + te_α·S(t)` with `te_s0 = 0` and
`S` set by the OHC forcing alone, so α *is* the te panel — no confounder.

- **Attribution.** D1 alone moved α only 0.15023 → 0.15205 (`22635dd`; those
  chains were deleted, so quoted, not recomputed) = **19%** of the move. The
  other 81% is D2.
- **Direction — and the metric has to be named, because the claim reverses.**
  `diag_te_weighted_and_seam.py` CHECK 2 produces *two* optima and L10 sits
  **between** them:

  | optimum | value | L10 → L11 |
  |---|---|---|
  | precision-weighted (**what the likelihood optimises**) | 0.13950 | 0.0108 → 0.0206 = **1.91× FURTHER** |
  | zero-mean-bias (unweighted level) | 0.17711 | 0.0268 → 0.0170 = 0.64× closer |

  So this is an **era trade**, and the residuals say the same: steric 1900-1919
  bias 0.418 → 0.162 and 1920-49 0.555 → 0.348 (wide bands, low weight) bought at
  1993-2026 0.133 → **0.216** with coverage 21.2% → **15.2%** (tiny bands, high
  weight). **The projection is anchored on the era that got worse** — which is
  where the +1.7 cm of extra 2100 ssp585 steric comes from.

**Correcting the record within this entry.** The first draft called 0.1395 "the
level-implied optimum" and concluded the D2 orthogonality "did not hold". Both
were wrong. 0.1395 is the *precision-weighted* optimum; the level-implied one is
0.17711, in the opposite direction. And the steric basis is orthogonal to **S(t)
itself**, not merely to the constant — corrected 2026-08-14 (`cb21def`) after
`L11tune2` measured `corr(d2_steric_1, thermal_alpha) = −0.724` — so δ cannot
mimic a rescaling of α *in the plain inner product*. The likelihood metric is the
AR(1)-correlated heteroskedastic precision, in which that orthogonality does not
hold, and `d2_basis` says so explicitly ("the posterior metric is neither the
plain nor the diagonal one ... chasing posterior correlation by changing the
design metric is whack-a-mole"). So the α shift is **documented residual
coupling, not a failed gate.** What is open is its magnitude and which stream
carries it.

**NOT resolved:** *which* D2 stream. `D2chk3` carries both `d2_gsic_*` and
`d2_steric_*`, so no existing chain separates a steric-basis leak from a gsic
partition trade — glaciers falling while steric rises by a similar amount is
equally the signature of the latter. Separating them needs one chain per stream.

## [unreleased] — 2026-08-15 — L10 → L11 hindcast scorecard: D2 works, and D1's price is quantified

`posterior_predictive_ladrillo.jl` is now `--tag=`-driven (posterior AND every
output filename from one constant, so a run on one posterior cannot write files
labelled with another). The default L10 path reproduces its existing outputs
**bit-identically** — same three MD5s — so this is a parameterisation, not a
change. New `python/scope_l10_vs_l11_scorecard.py`; both arms use the same
script, forcing, baseline, targets, 2000 draws and noise seed.

### D2 did what it was built to do on glaciers
Coverage of the 90% parameter band **63.7% → 79.8%** overall, and **35.5% →
80.6% in the satellite era** (+45.2 points), with the median essentially
unmoved (|Δbias| ≤ 0.05 cm in every window). A mean-zero discrepancy term
should reshape the band and not the median; it did.

### D2 on steric moved the early-century bias, and traded the satellite era for it
`te` mean bias **+0.281 → +0.175 cm** overall, concentrated where it was worst:
1900-1919 **+0.418 → +0.162**, 1920-1949 **+0.555 → +0.348**. But 1993-2026 got
WORSE, +0.133 → +0.216, and its coverage fell 21.2% → 15.2%. Consistent with
`thermal_alpha` still sitting at 0.16 rather than the precision-weighted steric
optimum of 0.1395 — the open question is unchanged and this is a second symptom
of it, not a new one.

### AIS and Greenland are unchanged, as they should be
`ais` bias identical to 3 decimals in every window (the change set does not
touch AIS). `gis` bias |Δ| ≤ 0.006 cm, coverage −2.4 points — the (ℓ, w)
reparameterisation was a CONDITIONING fix, and it behaved like one.

### D1's price, measured: ~+0.7 to +1.0 cm of early-century total bias
The total is **OUT-OF-SAMPLE for L11** (D1 dropped it) and in-sample for L10, so
its L11 row is a prediction and its L10 row is a residual. That asymmetry is the
measurement, and it is carried in the output rather than left to the reader.

| window | total bias L10 → L11 | coverage L10 → L11 |
|---|---|---|
| 1900-1919 | +0.146 → **+1.125** | 100.0% → 30.0% |
| 1920-1949 | +0.201 → **+0.918** | 80.0% → 30.0% |
| 1950-1992 | +0.300 → +0.617 | 30.2% → 4.7% |
| 1993-2026 | +0.181 → **+0.130** | 21.9% → **40.6%** |
| full | +0.221 → +0.646 | 51.2% → 24.0% |

Without the total, nothing holds the component sum to the observed total, and
the sum runs high **pre-1950 only** — the satellite era actually IMPROVED on
both bias and coverage. This does not say D1 was wrong (its case was that the
total pins R19 at a saturated state, `3a9e64b`); it puts a number on what the
spec called "a deliberate discard of an independent observational constraint,
not a tidy-up".

### An error I made and caught
Glaciers must be scored against `glaciers_obs_delta_corrected`, not the raw
`glaciers_obs`: the gsic obs carry a per-draw M15/Roe-2021 ramp on the OBS side
over 1900-1959. Scoring against the raw target inflates the early-century
glacier bias ~7× (+1.28 rather than +0.20 cm over 1900-1919 on L10) and reports
a large spurious regression. I did that first; the scorecard now uses the
corrected series and says why in its header.

## [unreleased] — 2026-08-15 — L11 ACCEPTED on deliverable; the R19 overcorrection is RETRACTED

4 × 2M, seeds 2026-29, ~2h46m each, acceptance **0.236-0.238**. Accepted on the
deliverable criterion (Marcus 2026-07-19): **18 marginals not converged**
— one fewer than L10's 19, same compensating AIS-geometry ridge, `ais_iceflow0`
R̂ **2.449** against L10's 2.359 — while projected SLR converges at
**R̂ 1.002 @2100 / 1.005 @2150**, ESS ~1300, chain-median spread 0.028-0.029 of
the within-chain sd. Wrote `parameters_subsample_brick_mengel_L11.csv` (10k of
4M pooled) and `adapted_cov_L11.csv`.

Pooled projected SLR, cm rel. 1995-2014: **2100 = 45.28** [41.63, 75.57];
**2150 = 70.78** [62.64, 155.29].

### R19: the overcorrection does NOT survive convergence — RETRACT the §5.1 alarm

| posterior | R19 modern rate 2000-2024 | vs GlaMBIE |
|---|---|---|
| L10, before | 0.1490 [0.0544, 0.2300] | **+0.86σ**, 3.03× |
| D2chk3 (200k, single common-start, NOT converged) | 0.0057 [0.0000, 0.0755] | −0.38σ, 0.12× |
| **L11 production, pooled 4×2M** | **0.0229 [0.0002, 0.1298]** | **−0.23σ**, 0.46× |

The handoff reported the point estimate swinging from ~3× too high to "**~9×
too LOW**" and concluded the constraint pair was unbalanced — that the rung
tightening may need to be less aggressive for R19, or GlaMBIE needs more weight.
**On the converged posterior it is 0.46×, i.e. about 2.2× too low, not 9×**, and
−0.23σ against L10's +0.86σ. That remedial work is not indicated. The unconverged
diagnostic was ~4× off, in the direction that would have triggered it; its own
caveat ("indicative, not definitive") was the right call and was load-bearing.

Per-chain **0.0172 / 0.0231 / 0.0235 / 0.0309 → −0.16σ to −0.28σ: all four
agree**, so this is not a pooled median hiding a split. Cross-checked through a
second code path — the 10k canonical subsample gives 0.0242, −0.22σ, 0.49×.

**What still holds:** the 5-95% lower bound is 0.0002, so near-zero modern R19
melt remains admitted.

Measured by `julia/diag_r19_modern_rate.jl`, new. Its `--check-l10` anchor
reproduces L10's recorded 0.1490 [0.0544, 0.2300] and 3.03× exactly at the same
400 draws, which is what makes the L11 row trustworthy rather than merely
computed.

### The blocker: L11's posterior could not be read by anything

Found by running it, not by inspection. `postprocess_mcmc_ext.jl` writes the
canonical subsample with the CHAIN's column names, so an L11 posterior carries
the sampled `(gis_slow_ell, gis_slow_w)` and no native `(gis_alpha_s,
gis_beta_s)` — and `ladrillo_gis_variant` rejects that header by design ("no
default and no fallback"). Every downstream consumer failed, starting with
`diag_slr_convergence_by_chain_ladrillo.jl`, which is the diagnostic that GATES
`postprocess --accept-slr`. So L11 could not be accepted and no deliverable
could be projected from it. Fixed: the transform derives at LOAD in
`ladrillo_projection.jl` (Marcus's call), so the posterior file keeps exactly
the sampled coordinates and no deliverable carries derived columns someone could
perturb inconsistently. Eight new gates, because all six suites passed
throughout and never touched the branch.

### Ordering correction, for whoever runs the next one
`diag_slr_convergence_by_chain_ladrillo.jl` must run BEFORE
`postprocess_mcmc_ext.jl --accept-slr`, not after: `--accept-slr` READS
`slr_convergence_<TAG>.csv` and refuses if it is absent. I ran postprocess first
and it correctly refused to write anything.

### Still open
`thermal_alpha` **0.16** against L10's 0.150 and the precision-weighted steric
optimum of 0.1395 — D2 has not pulled it toward the steric optimum, unchanged
from the tuning run. Thread 5 (Greenland at 2300) untouched.

## [unreleased] — 2026-08-15 — L11 production launched: tuned on the shipped D2 basis

The L11 change set was built on 2026-08-14 but could not go to production: both
existing tuning covariances were tuned on a D2 basis that no longer ships.
`L11tune` predates the Greenland (ℓ, w) reparameterisation AND used construction
1 (⊥ the constant alone); `L11tune2` used construction 1. The shipped basis is
construction 2 (steric column ⊥ `S(t)`, `cb21def`). This closes that gap.

### `L11tune3` — the third and final tuning run
`calibrate_mcmc_ext.jl 1000000 2026 --tag=L11tune3`, common start, 71 min,
**acceptance 0.239** against the predicted ~0.24. The config header confirms all
five parts live and none accidentally reverted: `total DROPPED | GlaMBIE R19 rate
ON (0.0493 +/- 0.1162 mm/yr) | rung sigma x0.702` (= 2/2.847, the d₂(8) order
statistic, not a chosen number), Greenland `(log r_s, w)` at T̄ = 1.9631 K, and
D2 `orthogonal to the constant, to DELTA_RAMP on gsic, and to S(t) on steric`.
It seeded from `L11tune2` — positionally valid, since all three L11 covariances
share the 57-name layout; only `L11tune`'s native-coordinate Greenland rows are
not, and that case is still name-mapped by the existing guard.

### The ADCOV preference chain: `L11tune3` at the head, and a refactor
`adapted_cov_L11tune3_seed2026.csv` is now preferred above `l11b`. The nested
ternary was replaced with an explicit ordered candidate list — adding a sixth
level to a chain already 8 parens deep is a paren-counting error waiting to
happen, and the selection logic is unchanged (verified: with `l11c` absent it
still resolves to `l11b`).

### `overdispersed_starts.csv` rebuilt BY NAME, per spec §7.1
Rebuilt from the `L11tune3` post-burn half via `build_overdispersed_starts.jl`
(already chain-agnostic; no code change needed). 55 → **57 columns**, now
carrying `d2_{gsic,steric}_{1,2}` and `gis_slow_{ell,w}`, with `sd_dang`,
`rho_dang`, `gis_alpha_s`, `gis_beta_s` correctly absent. Real posterior draws at
`ais_iceflow0` quantiles 0.02/0.35/0.65/0.98 — **0.645 / 0.762 / 0.877 / 1.079**
against a 2nd-half range of 0.602-1.12. Not random jitter, which fails 200/200.

### The pre-launch gate: four seeds, not one
A 300-iteration run per seed confirmed (a) the edit resolves to
`adapted_cov_L11tune3_seed2026.csv`, and (b) all four start rows pass the
calibrator's by-name assertion with a finite logposterior (**217.9 / 219.3 /
220.4 / 217.9**). Those sit ~846 above the common start θ₀ (−628.65), which
looks alarming and is not: θ₀ is a CONSTRUCTED vector (the offline g=0 Greenland
fit, prior centres, `beta_s` deliberately off-rail at 1e-3), not a posterior
mode. Checked directly rather than assumed — the chain's post-burn `log_post` is
p05 211.9 / p50 220.9 / p95 228.5, so the starts sit at the **28th percentile**,
squarely in the typical set. They are below the median because they are selected
on `ais_iceflow0` tails, not on `log_post`.

### Production: 4 × 2M, seeds 2026-29 (Marcus green-light 2026-08-15)
`julia/run_l11_production.sh`, new. Matches the L10 and extC precedent exactly so
that L11-vs-L10 stays like-for-like — which is what the R19 question needs, since
L10's +0.88σ is the comparison point. **No `--amp-mu`/`--amp-sigma`:** L10 was
launched without them and the file defaults (0.95/0.10) are canonical; extC's
1.08/0.15 belongs to the A6 study and would silently shift the AIS amp prior.
All thread vars pinned to 1 (`OPENBLAS`/`OMP`/`VECLIB`, `--threads=1`) — measured
at launch, four chains at ~95% CPU each, i.e. one core apiece, versus the ~200%
of BLAS spin-wait that gave L10 an 11 h ETA before pinning. The script hard-fails
if the covariance is missing or the starts file lacks `d2_gsic_1` /
`gis_slow_ell`; the calibrator's by-name assertion remains the real gate.

### Still open, unchanged by this entry
`thermal_alpha` sits at **0.16 ± 0.0075** in the L11tune3 posterior against L10's
0.150 and the precision-weighted steric optimum of 0.1395 — D2 has not pulled it
toward the steric-optimal value. The R19 overcorrection (point estimate ~9× below
GlaMBIE at −0.38σ, from a single unconverged 200k diagnostic) is to be
re-measured on this production posterior, not before it.

## [unreleased] — 2026-08-14 — D2 built: a mean-zero discrepancy term on gsic and steric

Spec §3. Scope unchanged from the spec: only gsic and steric have residuals
approaching their own observation bands (resid sd / mean band σ on L10: ais 0.17,
**gsic 1.06**, gis 0.33, **steric 0.95**). Greenland is not here — its pathology
was the MODULE, fixed by A+B.

### The design decision: a BASIS, and orthogonality instead of a tight prior
Spec §3 left the form open (GP vs low-order basis) and flagged the
`thermal_alpha` identifiability risk as "the main risk in D2". Today's TE work
sharpened that risk into a number: `te_sea_level` is exactly `te_α·S(t)`, so a
LEVEL offset in the steric residual is **degenerate with `thermal_alpha`** — and
the steric misfit IS a persistent level bias (+0.553 / +0.140 / +0.133 cm over
1920-49 / 1950-92 / 1993-2026), with a precision-weighted α of 0.1395 against
L10's 0.1502.

So the term is a **low-order polynomial basis made orthogonal to the things it
must not steal**, rather than a GP with a hopeful prior:

- **Orthogonal to the constant, on both streams.** A mean-zero δ(t) can absorb
  SHAPE and *cannot* absorb LEVEL, so `thermal_alpha` stays identified by the
  level. Sub-choice 4 resolved by construction.
- **Orthogonal to `DELTA_RAMP`, on gsic.** gsic already carries a one-parameter
  obs-side early-century discrepancy (`gic_delta`, the M15/Roe-2021 ramp over
  1900-1959). Orthogonalising means the new term describes only what that ramp
  does not, instead of fighting it.
- 2 dof per stream, unit-RMS normalised so the coefficient is an RMS discrepancy
  in cm and the prior `N(0, 0.5)` cm is interpretable against 0.3-0.6 cm
  residuals. 53 → **57** sampled parameters.
- δ is added to the MODEL, so the per-year band σ and the AR(1) noise are
  untouched — spec §3 sub-choice 2.

### The orthogonality is ASSERTED at load, and it immediately caught a bug
A basis that quietly acquired a constant component would silently re-open the
`thermal_alpha` degeneracy with nothing downstream to show it, so mean-zero,
unit-RMS and ⊥`DELTA_RAMP` are checked at load like the amp-law `S(anchor)=1`
identity. The check **failed on the first run**: projecting out `ones` and then a
non-orthogonal `DELTA_RAMP` re-introduces a constant (gsic col 1 had mean 0.605).
The protect set is now orthogonalised against itself first. Classic Gram-Schmidt
error, caught by its own assertion rather than by a wrong posterior.

### Verification
- **`--keep-total --no-r19-rate --rung-sig-legacy --no-d2` reproduces the
  pre-change calibrator BIT-IDENTICALLY** (300 iter, seed 2026, max |diff| = 0).
- **Mutation-tested**: Δ`log_post` at the identical θ₀ = **−1.6969** with D2 on;
  new columns `d2_gsic_{1,2}`, `d2_steric_{1,2}`. Not inert.
- All six suites pass.

### Known and NOT yet addressed
- **Acceptance drops to 0.045** on a cold start: the 4 new parameters get a fresh
  diagonal proposal. A tuning run to build an adapted covariance is required
  before production, exactly as the two-stage launch in the calibrator header
  describes.
- Spec §3 sub-choice 3 (do ais/gis drop to white?) is left as-is — the spec's own
  recommendation, since changing it "buys nothing measurable and costs
  comparability".
- δ and AR(1) can in principle both absorb correlated structure on the same
  stream. The low order and mean-zero constraint limit it, but the posterior
  correlation between `d2_*` and `sd_*`/`rho_*` should be read off the first
  diagnostic chain.

## [unreleased] — 2026-08-14 — the R19 change set: drop the total, add the GlaMBIE R19 rate, tighten the rung

Approved by Marcus 2026-08-14 as ONE change set, because the three interact. The
total was the only thing constraining R19, and what it was imposing is not
defensible: **R19 pinned at 97-99% committed at EVERY warming level** (1.2 → 3.0 K
moves it 97.4 → 99.6, i.e. no scenario response at all), **3.03× GlaMBIE's
observed modern rate**, and **1.0-1.8 σ above the GlacierMIP3 rungs**. R19 is the
one component with no target of its own — Frederikse excludes it, the gsic
channel is SLOWP+FAST, the GlaMBIE term is a share — so it is the only direction
the likelihood can move penalty-free, and it absorbs the Frederikse-vs-Dangendorf
budget non-closure (+0.74 cm over 1950-1980). Dropping the total removes the
cause; the other two give R19 constraints of its own.

| change | default | restore flag |
|---|---|---|
| total ("dang") stream dropped, `sd_dang`/`rho_dang` gone (55 → 53 params) | ON | `--keep-total` |
| GlaMBIE R19 modern-rate term, 0.049251 ± 0.11615 mm SLE/yr | ON | `--no-r19-rate` |
| rung σ ÷ d₂(8) = 2.847 instead of ÷2 (×0.702) | ON | `--rung-sig-legacy` |

**The rung tightening is principled, not chosen.** The stored `sig*` columns are
HALF THE FULL INTER-MODEL RANGE of the 8 GlacierMIP3 models treated as 1 σ
(`d1d_fourrung_seam.py`: `(hi-lo)/2`). For n normal draws the expected range is
d₂(n)·σ, and d₂(8) = 2.847, so half-range overstates σ by 1.42×. Dividing by d₂
is the correction. At the L10 median this roughly doubles R19's rung χ²
(3.47 → ~7.04) while leaving SLOWP and FAST, already at ≤0.66 σ, comfortable.

**The GlaMBIE R19 σ is the serially-correlated value, not the as-coded
quadrature.** `GLAMBIE_SD["R19"]` = 0.0361 is quadrature-over-24-years ×
`GLAMBIE_ERR_INFLATE` = 1.5; the GlaMBIE restructure established that serial
independence understates by ~4.7× and that the 1.5× was a partial compensation
for exactly that. Summing the per-year errors gives **0.11615**, which SUPERSEDES
the inflate rather than compounding with it. The term is weak by construction
(0.42 σ) — region 19 contributes 8 GlaMBIE input datasets with **zero
gravimetry** (GRACE cannot separate the Antarctic periphery from the ice sheet)
and a single DEM-differencing estimate — but it is the only DIRECT measurement of
the block.

### Verification
- **`--keep-total --no-r19-rate --rung-sig-legacy` reproduces the pre-change
  calibrator BIT-IDENTICALLY** (300 iterations, seed 2026, max |diff| = 0 over
  all sampled parameters and `log_post`), so the L10 configuration stays exactly
  reproducible.
- **Mutation-tested** (spec §7.4 — a dead term looks exactly like a working one).
  Δ`log_post` at the identical θ₀: removing the R19 rate term **−1.1953**,
  reverting the rung σ **+0.1142**, keeping the total **−224.92**. Neither new
  term is inert.
- All six suites pass.

### Not done here
No production chains. The rest of the thread-4 change set (D2's δ(t) on
gsic+steric, the Greenland (log r_s, w) reparameterisation) is still unbuilt, and
the spec's "one change set, because each item invalidates the posterior" logic
applies — this should not go to production on its own.

## [unreleased] — 2026-08-14 — the AIS spread is inherited from DAIS, and the D1 short chains say R19 moves while TE does not

Marcus's two asks after the Ladrillo-vs-BRICK-2.0 scorecard. Both done; neither
changes a shipped output.

### 1. AIS 2100 scenario response — reading (b) is dead, and (a) is stronger than claimed
`julia/diag_ais_spread_decomposition.jl`, 500 draws. **Method correction on
record:** freeze-at-posterior-median was tried first and DISCARDED — the quantity
is `med(ssp585) − med(ssp126)`, a scenario response *of* the median, so freezing a
group at its own median barely moves it (every group retained 95-120%). The arm
that answers the question is **revert-to-BRICK-2.0**:

| arm | 2100 spread | of base |
|---|---|---|
| BASE (L10 as shipped) | 31.83 cm | — |
| revert A6 temp map → 1.196 | 46.86 cm | **147.2%** |
| revert fast_dyn → medoid | 30.91 cm | 97.1% |
| revert geometry_B → medoid | 35.44 cm | 111.3% |
| revert `ais_iceflow0` → medoid | 33.03 cm | 103.8% |
| **ALL AIS → BRICK 2.0** | **54.88 cm** | **172.4%** |

`ais_iceflow0` accounts for **−3.8%** of the response, not the bulk, so its
R̂ 2.359 is a reporting caveat exactly as thread 3 said. And Ladrillo's AIS
changes did not widen the scenario response — they **narrowed it by 42%**, with
the A6 transient map the single biggest damper. Mechanism: the share of draws
whose T_ant reaches `antarctic_temp_threshold` is **0.0% / 27.8% / 99.8%** at
SSP1-2.6 / 2-4.5 / 5-8.5, i.e. the DAIS fast-dynamics tail switching on — stock
BRICK 2.0 machinery. **Criterion 4 for AIS resolves in Ladrillo's favour**: still
above every FACTS module, but that is a DAIS structural property and our changes
moved it toward FACTS.

### 2. D1 implemented behind `--drop-total`, verified bit-identical when off
Opt-in flag rather than a deletion, per the house pattern, so L10 stays exactly
reproducible. Three traps handled: `σn[5]` would be an out-of-bounds read with 4
streams (the term is guarded, not deleted); the five `OLD*_NAMES` proposal-
embedding tables all ended with `for s in SERIES` and would have silently
shortened (now `ALL_SERIES`, with only `pn0` following the live list); and a new
`L10_NAMES` table lets a 53-param run still name-map the 55×55 L10-tuned
proposal ("name-mapped 53 of 55 rows; dropped sd_dang, rho_dang"). **With the flag
off, 300 iterations at seed 2026 reproduce the pre-change calibrator
BIT-IDENTICALLY** (max |diff| = 0 over all 57 columns).

### 3. The D1 short chains — 4 × 250k, acceptance 0.236-0.241
`python/diag_d1_vs_l10.py`.

**Q1 (spec §7.2) — R19 DOES move.** `gic_T_off_R19` goes −1.9095 → −0.3236
(**+2.05 L10 sd**) and widens 1.39×; the other four R19 marginals move ≤0.19 sd.
The 1.586 shift is **5.5× the worst between-chain spread** in either arm, so it is
a real posterior shift. **Spec §2.2's width-ratio reading was the wrong one — the
total WAS constraining R19, and D1 needs an R19 replacement term before
production.**

A **mixing gate** was added, and it changes 6 of 7 secondary results: `rho_gis`,
`ais_iceflow0`, `ais_slope`, `anto_beta`, `rho_gsic` and `antarctic_alpha` all
move >0.5 L10 sd but by LESS than the between-chain disagreement → NOT findings.
Only `gic_u_unch` (2.1×) and `gic_T_off_R19` (5.5×) survive, both glacier-block.

**Q2 — D1 does NOT fix thermal expansion, and TE is not a mis-tuned coefficient.**
`te_sea_level` is exactly `te_s₀ + te_α·S(t)` with `te_s₀ = 0` and not sampled, so
the re-referenced steric series is exactly proportional to `thermal_alpha` and the
bias is closed-form (gated: max |te_p50 − α_L10·S(t)| = 0.0023 cm). D1 moves
`thermal_alpha` 0.15023 → 0.15205 (+0.24 L10 sd) and the full-record steric bias
+0.280 → +0.261 cm. **The α that would zero the bias is 0.17748 in 1920-1949 but
0.13386 in 1993-2026** — the early and modern windows want OPPOSITE corrections
and L10 sits between them (in the spec's derived units, ×0.656288: 0.0986 now,
0.1165 early-implied, 0.0879 modern-implied, against the 0.1043 quoted as
observationally implied). No single `thermal_alpha` fits both, so a
one-coefficient SLE-∝-cumulative-OHC form cannot fit the observed steric record.
**A free δ(t) on steric would absorb exactly this and hide it** — the D2 design
risk, now with a number on it.

## [unreleased] — 2026-08-14 — thread 5 step 2: the 2300 Greenland flatness is a COMMITMENT defect, and the spec's framing of thread 5 is retracted

Sequencing call (Marcus, 2026-08-14): scope thread 5 before committing to the
thread-4 calibration. Done, offline — no chain, no calibrator edit, no shipped
output changed. `python/scope_gis_2300_relaxation.py` →
`outputs/scope_gis_2300_relaxation.csv`; full write-up in
`notes/note_2026-08-14_thread5_commitment_not_relaxation.md`.

Both Greenland modules re-implemented in numpy from
`julia/greenland_ab_component.jl` and MimiBRICK's `greenland_icesheet_component.jl`
(t−1 lag, clamps, the V/V0 rate damping A+B drops). **Reproduction gate: all 18
medians within 0.05 cm** of the recorded L10 and quarantined extC projections;
the script refuses to diagnose otherwise.

### The finding
Spec `notes/spec_2026-08-14_next_calibration.md` §9 frames thread 5 as "what
replaces proportional relaxation at high warming". **Retracted.** A+B's
relaxation is *faster* than the stock SIMPLE it replaced, and A+B is **98.7-99.1%
equilibrated by 2300** (stock: 26-30%). Under SSP1-2.6 the shipped Greenland has
stopped — 0.002 cm/yr at 2300, 2 mm of commitment left. The 2300 gap decomposes
with the realisation term running the WRONG way (+0.41 to +0.84 m) and a
commitment term of −0.54 to −0.97 m.

The 2×2 cross-test (each arm's `Leq(t)` fed to the other's relaxation, median
params, SSP2-4.5/SSP5-8.5, cm rel 1995-2014) does not depend on that
linearisation: A+B commitment × stock relaxation = 4.33 / 11.63; stock
commitment × A+B relaxation = 65.72 / 137.31, against diagonals 14.57 / 39.51 and
25.46 / 49.90.

### Why the commitment is a defect and not a difference
Stock is not a benchmark — ~0.73 m of its commitment is a temperature-INDEPENDENT
intercept (73% of its SSP1-2.6/2300 value). Against Bochow et al. 2026 (preprint,
provisional) at each scenario's own 2300 GMST, committed loss in m SLE: A+B
**0.137 / 0.205 / 0.454** vs 3.11-3.37 / 4.84-5.06 / 8.56-8.71, i.e. **23× / 24× /
19× low**. A+B commits 6% of the ice sheet at ~6.5 K of warming.

### Why the calibration cannot simply find a bigger commitment
The hindcast constrains only the PRODUCT `phi·Leq`. Scaling `(c1, c0)` by k and
re-solving the rate scale that restores the 1900-2025 target of 5.78 cm fits
**identically** at every k, while 2300 (SSP2-4.5) moves **14.59 → 58.29 cm**:

| k | Leq(2300) m | rate scale | tau_slow @2300 | 2300 cm |
|---|---|---|---|---|
| 1.0 (as calibrated) | 0.204 | 1.0034 | 30 yr | 14.59 |
| 5.0 | 1.020 | 0.1117 | 272 yr | 46.30 |
| 22.6 (Bochow-matched) | 4.610 | 0.0231 | 1316 yr | 58.29 |

So `gis_c1`'s posterior/prior sd ratio of 0.12 (spec §8.4, "strongly
constrained") is a CONDITIONAL width at the timescales the module can express —
not evidence the commitment is identified. The identifying constraint has to be
an external `Leq(T)` target, which is what Option C (the PISM equilibrium ladder)
was reaching for and where it failed (CHANGELOG 2026-08-10).

### A second, smaller defect: the channels are labelled backwards
At posterior medians `alpha` AND `beta` are both larger on the "slow (dynamic)"
channel than on the "fast (SMB)" one, so the slow channel relaxes FASTER
everywhere above `T_south = −1.41 K`; 76.6% of draws have slow > fast at 2 K.
tau_fast/tau_slow = 76.0/51.8 yr at 2025 and 20.2/13.8 yr at SSP5-8.5/2300.
**Nothing in the module exceeds ~80 yr**, so there is no slow reservoir at all,
and the Mouginot partition pins the *surface* share onto the slower channel.
NB the posterior medians are NOT the offline optimum the spec quotes
(`alpha_s = 0.00708, beta_s = 1e-6`): the optimum rails `beta_s`, the posterior
median does not, so channel-timescale reasoning from the offline fit does not
carry.

### Scope
The 2100 deliverable is unaffected (`phi` = 0.68-0.84 there; the ridge has not
collapsed). All six suites pass. Thread 4 D1/D2/1.2 remain NOT STARTED. Open for
Marcus: whether an external `Leq(T)` constraint joins the same change set, or
Ladrillo 1.0 ships its 2300 column with the ridge stated as a caveat.

## [unreleased] — 2026-08-14 — thread 4 item 1.0: the two calibration diagnostics re-measured on L10, and the noise-model premise changes

Handoff `notes/handoff_2026-08-13d_threads_4_and_5.md` §1.0, the prerequisite that
had to run before any of thread 4 could be designed. Both diagnostics were pinned
to the quarantined extC vintage; both are now `--vintage {L10,extC}`, default
**L10**, with the vintage in every output path, figure title and markdown header.
`--vintage extC` reproduces the recorded extC numbers (gis step cost 27.69 vs the
recorded 27.71, net +25.36 vs +25.37), so the re-pointing is faithful. The eight
extC-vintage output files moved to `outputs/quarantine/20260813_extc_vintage/`
(README §7).

### 0. Cost: ~40 min → 2 s and 18 s, by reading the posterior subsample
Both scripts read the four 2.2 GB chains only for posterior medians of
`thermal_alpha` and `sd_*`/`rho_*`. `postprocess_mcmc_ext.jl` writes the
10,000-member subsample as a **uniform stride over the pooled post-burn draws**,
so its marginal medians ARE the pooled medians. Verified, not assumed: a
stride-100 read of all four L10 chains (40,000 draws) agrees with the subsample
to **< 0.01 posterior sd on every one of the 11 parameters**. `--post-source=chains`
restores the full read. (The `cut`-based extraction is the cheap way to do this —
`awk -F,` on 55 fields × 2M rows × 4 files does not finish in 2 minutes; `cut`
takes 46 s per file.)

### 1. The Greenland noise pathology is GONE — it was the module, not the noise model
The extC headline was `rho_gis = 0.985`, AR(1) τ 67.5 yr, **n_eff 0.93** — one
effective observation in 126 years, the mechanism by which a decades-long
Greenland miss survived as "correlated noise". On L10, with A+B inside the joint
likelihood:

| | extC | L10 |
|---|---|---|
| `rho_gis` (sampled, posterior median) | 0.985 | **0.789** |
| AR(1) τ | 67.5 yr | 4.2 yr |
| **n_eff (gis)** | **0.93** | **14.85** |
| stationary sd of the gis noise process | 0.318 cm | 0.025 cm |
| cost of a 0.65 cm step over 1942-1982 | 27.7 logl | **311.8 logl** |
| leverage the AR(1) removes (gis) | 14× | 1× |
| gis residual, mean over 1942-1982 | −0.822 cm | **+0.008 cm** |

So the sampler was inflating the Greenland noise process to absorb a structural
miss; give it a module that fits, and the process collapses and the channel gets
~11× more grip. **This reverses the reading of `diag_gis_likelihood_leverage.py`'s
original conclusion for gis** — that file identified the AR(1) as the mechanism
that let the miss survive, and on the shipped model that mechanism is no longer
loaded. It is unchanged for the other four streams.

### 2. "AR(1) is misspecified on all five streams" is still true, but only two streams are under load
New column, `resid sd / mean band σ` — a stream whose residual sits well inside
its own observation band gives the noise model nothing to do, so "AR(1) vs white"
on it compares two terms that barely enter the likelihood:

| stream | extC | L10 |
|---|---|---|
| ais | 0.17 | 0.17 |
| gsic | 1.06 | **1.06** |
| gis | **1.84** | 0.33 |
| steric | 0.90 | **0.95** |
| dang | 0.21 | 0.12 |

Ljung-Box still rejects every member of the family on every stream (p = 0.0000
throughout, against p = 0.84 on the self-test's own simulated data), so the
specification finding stands. But on L10 the streams that actually put it under
load are **gsic and steric only** — and BIC agrees: `white − AR(1)` is +18.7
(gsic) and +108.0 (steric), against −2.5 to −4.2 for ais/gis/dang, where white is
now marginally *preferred*. A discrepancy term aimed at gsic and steric is a much
narrower change than replacing AR(1) on all five.

### 3. The "56% redundant total stream" figure is a p50 artefact — the redundancy is 100%
Section A's "variance of the total residual explained by the identity" read 55.9%
on extC and **−322% on L10**, with the underlying algebra completely unchanged.
Diagnosed at the source rather than from the statistic: `calibrate_mcmc_ext.jl`
scores `tot_full = ais + gsic_tot + gis + te` plus observed LWS, while the gsic
COMPONENT channel scores `gsic_flow` (hindcast scope), so **per draw**
`total_model − Σ(component_models) = gsic_tot − gsic_flow` = the R19 seam,
exactly; `posterior_predictive_ladrillo.jl` assembles its `total` the same way.
The diagnostic computes this on posterior MEDIANS, and medians are not additive.
The L10 total residual is half extC's (sd 0.246 vs 0.415 cm) while the
non-additivity term grew with the Greenland distribution change (gap sd 0.276 →
0.505 cm), which is the whole of the sign flip.

Consequence for thread 4 design axis 2: the total stream is **100% redundant**
with the components apart from one model term (the R19 seam), the observed LWS,
and its own likelihood weight — a stronger statement than the 56% it replaces.
Section A now says so and labels the p50 statistic as not-the-redundancy.

### 4. Thread 5 first step — Bochow 2026 re-run against A+B, and A+B is FLATTER at 2300 than the module it replaced
`scope_greenland_bochow2026.py` compared the Bochow tipping emulator to extC's
stock-SIMPLE Greenland via three hardcoded numbers. Those are now READ from
`outputs/ssps_components_2300_L10.csv` (median plus posterior 5-95%), which is
the live comparison the quarantine README flagged as "work, not a path edit".

Greenland, cm rel 1995-2014, median:

| year | | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|---|
| 2100 | Ladrillo 1.0 | 6.2 | 8.2 | 13.6 |
| 2100 | Bochow, sampled across families | 7.9 | 10.6 | 17.9 |
| 2300 | Ladrillo 1.0 | **7.8** | **14.6** | **39.1** |
| 2300 | Bochow, sampled across families | **24.5** | **54.5** | **167.1** |

At 2100 the two are within 1.7-4.3 cm. At 2300 Bochow is **3.1× / 3.7× / 4.3×**
higher. Under SSP1-2.6 the shipped model puts Greenland at 6.2 cm in 2100 and
7.8 cm in 2300 — 1.6 cm of further loss in two centuries — while Bochow's own
committed-loss diagnostic at that sustained warming is **3.0-3.6 m SLE**.

**And the comparison to the module A+B REPLACED runs the other way at 2300.**
Against extC's stock SIMPLE (gis median, cm):

| year | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|
| 2100 | −0.45 | +0.90 | **+4.78** |
| 2150 | −2.88 | −0.53 | +8.45 |
| 2300 | **−11.37 (−59%)** | **−11.13 (−43%)** | **−9.52 (−20%)** |

A+B was selected on its 2100 scenario responsiveness and it delivers that, but by
2300 it sits 9.5-11.4 cm BELOW stock SIMPLE on every scenario. **This is not the
amp law**: the law removes 6.9% of the driver at SSP1-2.6/2300 and 14.0% at
SSP5-8.5/2300 (flat-held), so its damping runs OPPOSITE to the effect — the
least-damped scenario declines the most (−59%) and the most-damped the least
(−20%). The decline is structural to the two-channel relaxation form. That is
thread 5's open question with a number on it, and it strengthens the criticism
already recorded: the slow channel that would carry the multi-millennial
commitment is exactly the one the 1900-2024 record cannot identify.

Bochow carries its own caveat, unchanged and still binding: EGUsphere preprint in
open discussion, referees have raised UQ and verification concerns, code
availability a placeholder. Its sampled 5-95% at 2300 spans 4.5-140.7 cm at
SSP1-2.6 — it is not a tight benchmark, but the median gap is not inside that
noise either.

### 5. Thread 4 spec written; T̄ measured and chosen (`diag_gis_slow_reparam.py`)
Marcus's three calls on 2026-08-14: **drop the total stream**, **discrepancy term
on gsic + steric only**, **measure the closure-sigma double-count before
re-deriving any sigma**. Written up as one change set in
`notes/spec_2026-08-14_next_calibration.md`. Two consequences of the drop worked
out there rather than discovered later: `closure_sigma()` is referenced only in
the `isdang` branch of `make_series`, so the drop removes the gate-3.1 closure
inflation outright and makes the third call moot (retained as a *check* on that
reasoning); and R19, excluded from `HIND_BLOCKS`, loses its only sea-level
timeseries constraint — measured as cheap (`gic_b_R19` posterior/prior width
ratio **0.95** against `gic_b_FAST` **0.09**, i.e. already prior-and-rung
dominated), with the caveat that a width ratio cannot separate that reading from
"rung + inventory already do it".

For item 1.2 Marcus asked for both T̄ candidates compared offline first. Mean
within-chain |corr| between the two sampled slow-channel coordinates, four L10
chains:

| coordinates | mean \|corr\| | pooled |
|---|---|---|
| `(α_s, β_s)` as sampled | **0.578** | 0.319 |
| `(log r_s, w)`, T̄ = 1.169 (hindcast mean) | 0.282 | 0.173 |
| **`(log r_s, w)`, T̄ = 1.963 (2015-2024 anchor)** | **0.139** | 0.137 |
| `(log r_s, α_s)`, T̄ = 1.963 | 0.575 | 0.655 |

A T̄ scan bottoms out at 0.135 at T̄ = 1.900 K, so **the anchor is essentially at
the optimum and the hindcast mean is twice as correlated** — T̄ = the 2015-2024
anchor. The *tilt* choice matters more than T̄: `tilt = α_s` at the anchor scores
0.575, no better than the coordinates already in use. Refit gate passes — every
reparameterised arm reaches the native optimum's nlp (17.8559) over the same
feasible set.

Two corrections to the item's premise, both measured:
- **The rail is `β_s`, not `α_s`.** The offline A+B optimum on record sits at
  `α_s = 0.00708, β_s = 1e-6` and rails **β_s**. Posterior draws within 1e-4 of
  the `α_s = 0` bound are 0.36-1.61% per chain; at the `β_s` rail, 0.00-0.01%.
- **The reparameterisation un-rails nothing.** `α_s = 0` → `w = 0` and `β_s = 0`
  → `w = 1`, so both bounds move into the tilt; the refit still rails `β_s` in
  every arm. The gain is the unbounded level coordinate, not rail removal.

Also worth knowing before the priors are rewritten: only **33.2%** of draws from
the current `(α_s, β_s)` priors fall inside the native bounds, so what is in
force is a pair of heavily truncated half-normals rather than the N(μ, σ) the
code appears to state. And the induced prior correlation runs opposite to the
posterior (0.102 at the hindcast mean vs 0.315 at the anchor) — specify the
prior directly in `(ℓ, w)` rather than inheriting it through the transform.

Method note: pooling matters. The as-sampled pooled |corr| is 0.319 against a
within-chain 0.578 — pooling a non-converged block hides the very ridge the
reparameterisation removes. Thread 3's trap, live again.

### 6. Obsolete material stripped, and GlaMBIE checked (spec §8)
Marcus, 2026-08-14: importance weighting was determined not helpful for recent
model versions — check whether removing it helps, and look for other obsolete
constraints.

**The D1 "blocker" was withdrawn.** `sd_dang`/`rho_dang` are referenced by three
scripts, but all three are dead paths: the conditional FaIR↔BRICK weighting was
measured immaterial on levels (46.68 vs 46.38 cm total@2100) *and* pulse
marginals (1.003-1.009), and the Wong weights are already OFF for the Mengel/FM
arm — "its posterior is already MCMC-calibrated to Dangendorf, Wong would
double-count", and Tony Wong excluded that arm for the same reason. Grepping for
symbol references finds call sites, not live paths. **Note the corollary:** with
the Wong weights already off, total GMSL enters exactly ONCE today, so D1 is a
deliberate discard of an independent constraint, not a de-duplication.

**Stripped:**
- `--gsic-early-sigma-x2` (the extB3b pre-1940 GSIC σ×2 fallback) **removed** from
  `calibrate_mcmc_ext.jl`. Never passed to any shipped run, and the pathology it
  remedied cannot recur: its cause was free `gic_nu`, now fixed and not sampled,
  and L10 sits at σ_gsic 0.0156 / ρ 0.649 vs the 0.032 / 0.96 signature.
- `weight_brick_conditional_fair.jl`, `weight_and_project_brick_fair.jl`,
  `compute_lB_per_post_mengel.jl` **banner-marked RETIRED** in the house
  `‼ STATUS` style — not deleted, since they are the provenance for the
  coupling-is-immaterial finding. `compute_lB_per_post.jl` and
  `apply_wong_weights.py` stay LIVE: the pre-#93 and BRICK-2.0 arms *are*
  Wong-weighted; only the Mengel/FM arm is not.

**GlaMBIE: checked, restructured, and one flagged conflict RETRACTED.**

| quantity | value |
|---|---|
| GlaMBIE SLOWP+FAST constraint on the SUM | 0.6063 ± 0.0476 mm/yr |
| gsic channel's own grip on the same window's rate | σ 0.0587 mm/yr (ratio 0.81) |
| gsic TARGET (Frederikse-derived) rate | +0.7292 mm/yr |
| **discrepancy** | **2.59 GlaMBIE-σ** |
| L10 model's own rate | +0.6911 mm/yr — **between them, 69% toward Frederikse** |

GlaMBIE is the only term separating SLOWP from FAST in the modern era, so it
stays. But its *sum* component duplicates the gsic channel at comparable weight
AND disagrees with it by 2.59 σ, and the model splits the difference — the
gate-3.1 total-vs-components conflict one level down. **Sequencing consequence:
`gsic` is one of the two streams D2 puts a discrepancy term on, and part of its
"under load" status may be this target conflict rather than model error. A δ(t)
would absorb and hide it, exactly as ρ = 0.985 hid Greenland's miss. Settle
GlaMBIE before designing D2's gsic term.** Recommended: re-express GlaMBIE as a
constraint on the SLOWP/FAST *partition* rather than two absolute rates. Caveat:
the 2.59 σ assumes independent SLOWP/FAST errors, as the code does; shared
methodology likely correlates them and would shrink it.

**The covariance was then checked, and it retracts the 2.59 σ.** GlaMBIE as
archived publishes only `combined_gt_errors` — a per-region per-year σ, with **no
covariance matrix at any level**, so the correlation can only be bracketed.
`glambie_block_stats` sums those errors in quadrature over all 24 years and
across regions; relaxing that to within-region serial correlation inflates
σ_SLOWP **×4.72** and σ_FAST **×4.80** against √24 = 4.90 — the whole ratio is the
quadrature assumption, and `GLAMBIE_ERR_INFLATE = 1.5` covers a third of it. The
discrepancy goes **2.58 σ → 0.54 σ**. So there is no Frederikse-vs-GlaMBIE target
conflict, and **no sequencing constraint on D2 from it**. What remains is plainer:
the absolute-rate σ was too tight by ~4.7×.

**IMPLEMENTED — GlaMBIE is now a partition constraint.** The two absolute-rate
terms in `calibrate_mcmc_ext.jl` are replaced by one term on the SLOWP/FAST share,
**0.6876 ± 0.0500**, leaving the aggregate modern rate to the gsic channel that
already scores it. The share is the right quantity twice over: it is what the
aggregate channel cannot see, and it is the combination in which the correlated
common-mode error cancels, so it does not inherit the untrustworthy σ. Same
construction as the existing Mouginot surface-share term, guard included.
`GLAMBIE_SHARE_SD = 0.05` is a **flagged methodological choice** — the two
internally consistent corners give 0.0296 and 0.0493. Verified:
`--glambie-absolute` reproduces the pre-change likelihood **bit-identically**
(max|diff| = 0 over all 57 chain columns, 2000 iterations, seed 2026); the share
form shifts `log_post` by +5.51 at the shared start.

### 7. Unchanged on L10
- **The total is still the loosest constraint in every window** (§E): σ on a
  window-mean offset 0.232-0.565 cm for `dang` against 0.014-0.062 for `ais`/`gis`.
- **Item 4.3 (TE)** still passes: `thermal_alpha` p50 0.1502 (was 0.1540) →
  **0.0986 cm per 1e22 J**, against observed 0.1043 (Zanna+IGCC) / 0.1133
  (Zanna+Cheng) and a physics range of 0.1011-0.1348. Slightly low-side, as before.

## [unreleased] — 2026-08-13 (second session) — the amp law is IMPLEMENTED, and it very nearly closes G4

Handoff `notes/handoff_2026-08-13_ladrillo_step5_production_done.md` §4 items 1-3.

### 1. G4 measured ON THE POSTERIOR for the first time (`diag_gis_spread_2100_ladrillo.jl`)
G4 — the 2100 SSP1-2.6 → SSP5-8.5 Greenland spread — had only ever been evaluated
at the offline cell's converged POINT (10.44 cm). On the accepted L10 posterior,
10 000 draws, per-draw pairing (the spread is a difference of two runs of the SAME
vector, so differencing marginal quantiles would mix draws):

| arm | GIS@2100 ssp126 / 245 / 585 | G4 spread q05/q50/q95 | draws in band |
|---|---|---|---|
| constant amp (the model as calibrated) | 6.81 / 9.59 / 16.59 | 7.37 / **9.80** / 12.44 | 3.8% |
| **amp law (default)** | 6.17 / 8.16 / 13.52 | 5.58 / **7.37** / 9.33 | **29.0%** |
| amp law, no flat-hold (sensitivity) | 6.17 / 8.11 / 13.93 | 5.89 / 7.78 / 9.85 | 24.6% |

**The previous entry's expectation is WRONG and is retracted.** It put the amp law
at ~8.7 cm, "roughly 40% of the gap". Measured, the law takes G4 from **9.80 to
7.37 cm against the 6.3-7.3 band** — it closes ~97% of the gap and lands 0.07 cm
above the band's top edge. The 8.7 cm figure was interpolated off a stage-1
single-vector amp SCAN, which cannot see the two things that do the work: the law
acts DIFFERENTIALLY across scenarios (ssp585 sits at S = 0.860 in 2100 while
ssp126 sits at 0.926), and the anchor moved (item 2). The posterior's own
spread-vs-amp slope is 6.51 cm per unit `gis_amp` constant-amp (the stage-1 scan
said ~6.7) and 4.89 with the law on.

Horizon gate: the diagnostic runs to 2100 and asserts the first draw's GIS@2100 is
BIT-IDENTICAL to a 2300 run before trusting the truncation.

### 2. Sub-choice 2.2 SETTLED — the anchor is dT_eff = 0.940 K, not 1.25 K (`diag_gis_amp_anchor.py`)
`amp = Σxy/Σx²` is an x²-weighted mean of the pointwise ratios, so the warming
level it represents is `dT_eff = Σx³/Σx²` over the observed window. Measured on
build_t_gis's own series and mask: HadCRUT5 0.945, Berkeley 0.950, GISTEMP 0.925,
**cross-product mean 0.940 K** — well below the 1.25 K placeholder, and below the
window's own 2015-2024 level (1.53 K) because the x² weights sit where the record
is long, not where it is warm. Gate: the recomputed amp reproduces
`gis_driver_constants.csv` to 1e-9 in all 36 product × zone × window cells.

Re-anchoring moves amp at 2.75 K from 1.670 to **1.652**. **Cross-check, and the
reason to stop worrying about the anchor:** an independent route — matching
ESTIMATORS instead of warming levels, i.e. dividing by CMIP6's own full-window
through-origin amplification (1.509) rather than by R_secant(dT_eff) (1.494) —
agrees to **1.0%**.

### 3. The law implemented (`ladrillo_projection.jl`, suite step 6 check [5])
`amp(dT) = amp_draw × S(dT)`, S tabulated by `diag_gis_amp_cmip6.py` on a 0.01 K
grid and read by the kernel. Design points worth keeping:
- **The anchor is a GRID NODE.** Without it, linear interpolation of the emitted
  grid gave S(dT_eff) = 0.99999992 and the kernel's load-time identity check
  fired. Inserting the node makes S(dT_eff) == 1 exactly, in floating point.
- **LEVEL form**: S multiplies the amplification (`amp·S(dT_t)·GMST_t`), because
  the estimator behind S is a secant. Integrating a trend ratio is the error in
  memory `project_pai_cmip6_time_diagnostic`.
- **Anchor-preserving splice retained**: the offset uses `mean(S_t·GMST_t)` over
  the same 11-yr window, so the driver still reproduces the observed mean there
  exactly — asserted to 1e-12, in both arms.
- **Suite step 6's parity assertion was RETHOUGHT, not deleted** (as the handoff
  asked). [1] compared the projector's amp CONSTANT to the calibrator's; now the
  projector's amp is a function, so [5] asserts the function MEETS the calibrator
  at the anchor (S(dT_eff) = 1 ⇒ amp(dT_eff) = GIS_AMP exactly), plus the shape's
  measured form and four structural gates on the driver (law off reproduces the
  constant-amp splice exactly; law inert over the observed years; anchor
  preserved; ssp585 2100 lowered).
- **Warming-level window is immaterial**: 30-yr running mean (what CMIP6 measured
  S on) vs the raw annual level moves the driver by ≤ 0.007 K, and by 0.0000 K
  wherever S is flat-held. Kept at 30 for fidelity, not because it matters.
- **PROJECTION-SIDE ONLY**, as the handoff specified: the calibrator runs to 2026,
  so two of its years fall past the seam and `gis_amp` is likelihood-inert there.
  No chain re-run.

### 4. Deliverables regenerated on L10 + the amp law
All six suites pass. The canonical posterior in `ladrillo_projection.jl` moves
**extC → L10** with the variant read off the file (`ladrillo_posterior_variant`),
and the two deliverable drivers follow: `outputs/ssps_components_2300_L10.csv`
and `outputs/postpred_L10_{components_timeseries,bias,coverage}.csv`.

The switch caught two latent traps, both of the "would have silently used the
wrong thing" class the kernel exists to prevent:
- **`LADRILLO_USED_COLS` silently meant `:stock`** — the column contract the
  posterior test checks. Deleted; ask for `ladrillo_used_cols(VARIANT)`.
- **The A+B Greenland slot has no defaults**, so Mimi refuses to build until a
  draw is applied. KEPT as a feature (a placeholder would run and look
  plausible); the test seeds one draw and says why.

**Vintage difference, extC → L10, medians at 2100 (cm):**

| ssp | glaciers | gis | ais | te | **total** |
|---|---|---|---|---|---|
| SSP1-2.6 | 8.54 → 9.01 | 6.63 → 6.18 | 4.88 → 4.77 | 13.18 → 12.86 | **35.91 → 35.41** |
| SSP2-4.5 | 10.56 → 11.03 | 7.27 → 8.17 | 11.74 → 5.95 | 17.27 → 16.85 | **49.48 → 45.01** |
| SSP5-8.5 | 14.69 → 15.16 | 8.80 → 13.57 | 45.78 → 37.72 | 25.91 → 25.28 | **97.75 → 94.25** |

- **Greenland moves BOTH ways** — down at SSP1-2.6, up at SSP5-8.5 — because two
  changes act against each other: A+B is a more responsive module than stock
  SIMPLE, the amp law damps it, and the damping is strongest exactly where A+B
  is most responsive. Do not describe the amp law as "lowering Greenland".
- **AIS still dominates the shift** and it is the least data-constrained block:
  the same `ais_iceflow0` ridge that is R̂ 2.359. Quote AIS as a distribution and
  carry the tipping-probability framing, per the 2026-08-12 reporting rule.
- **Glaciers move +0.47 cm at 2100 in ALL THREE scenarios** — flagged under the
  suspicious-uniformity rule, and it holds up: the scenario spread is unchanged
  to the digit (585−126 = 6.15 cm in both vintages), so it is a level shift, not
  a sensitivity change, and the glacier marginals show where it lives — R19 moved
  (`gic_b_R19` +0.40 sd, `gic_T_off_R19` −0.63 sd) while SLOWP and FAST moved
  ≤0.16 sd. R19's driver amp is 0.72, i.e. the reservoir with the weakest
  scenario dependence, so a shift there is a near-constant offset at 2100. (The
  R19 attribution is INFERRED from the marginals, not measured per component.)

**Owed:** `outputs/mcmc/slr_convergence_L10.csv`, the acceptance record, was
computed CONSTANT-AMP. The law is a deterministic transformation applied
identically to every chain and Greenland is ~9 of ~46 cm at 2100, so the
between/within variance ratio (0.010 against a 1.05 R̂ threshold) has room to
spare — but the certificate and the shipped model are not literally the same run.
Re-run it under the law before anything is shared.

### 5. Quarantine sweep — the pre-extC "78.02 cm" vintage
`outputs/quarantine/20260813_pre_extc_mengel_vintage/` + README, per the standing
rule. Ten files: everything `project_ssps_2100_mengel.jl` wrote from
`parameters_subsample_brick_mengel{,_ext}.csv`, plus the two figures. The README
says explicitly that this is a **vintage difference, not a bug**, carries the
mengel → extC → L10 component table, and repeats the two consequences that
survive (do not write "28 cm lower" — quote a distribution; the largest movement
in the programme is in the least data-constrained block).

**Deliberately NOT swept, with reasons in the README:**
- The **MAGICC-comparison and pulse study** outputs also run on
  `..._brick_mengel.csv`, but they are deliverables of a study *about that model
  version* — and Mengel is canonical in its own right in MimiBRICK-FM.
  Quarantining them would misfile them.
- The **extC outputs** are genuinely superseded by L10, but **five live consumers
  still read them** (`plot_ladrillo_memo_figures.py`, `ladrillo_model_comparison.py`,
  `diag_gis_likelihood_leverage.py`, `diag_noise_model_and_grip.py`,
  `scope_greenland_*.py`). Migrating those to L10 changes every number in the memo
  figures and is its own reviewed piece of work; moving the files first would only
  break the pipeline. **That migration is the top open item.**

The two legitimate cross-vintage consumers (`diag_mengel_to_ladrillo_attribution.py`,
`plot_ssp_projections_ext_compare.py`) were repointed at the quarantine path with a
comment saying why. Gate: the attribution diagnostic re-runs **byte-identical**
after the move.

### 6. Sub-choice 1 SETTLED — the flat-hold is what the data support (`diag_gis_amp_scenario_split.py`)
Marcus asked for the per-scenario rebuild. Both confounds have to be closed at
once — ONE scenario **and** a balanced MODEL panel — because within a scenario the
model population still changes with the bin. `ssp585` is the only scenario with
coverage above ~3 K and carries the verdict; `ssp126`/`ssp245` panels shrink to
9 and 10-27 models and are non-monotone even below 2.75 K, which is the
small-panel noise this test exposes rather than a contradiction.

**Three results, in order of how much they matter:**

1. **The shipped support (0.75-2.75 K) is composition-free.** Within `ssp585`
   alone, balanced across all 40 models, the curve falls monotonically
   **1.489 → 1.303**; the pooled curve the shape was actually built from falls
   1.498 → 1.284 over the same range. The part of the law in use does not depend
   on scenario mixing at all.
2. **The pooled bump IS mostly composition, as hypothesised** — within `ssp585`
   it is **+0.015 [−0.031, +0.043]** at the first bin above 2.75 K against
   **+0.057** pooled.
3. **But the region above 2.75 K is flat-within-noise, not declining**: slope
   **−0.0164/K [−0.0425, +0.0459]**, CI spanning zero. So the flat-hold is
   neither conservative nor aggressive — it is the reading the
   composition-controlled data support.

**RETRACTED: "the flat-hold is not conservative in the G4 direction."** That was
computed on the POOLED curve's values above 2.75 K (S ≈ 0.878-0.883 vs the held
0.860), which is exactly the object this test disqualifies up there. The 0.41 cm
difference between the flat-hold and full-curve arms stands as a sensitivity, but
the **full-curve arm is now the LESS defensible of the two** and the shipped
default is unchanged and better supported than when it was chosen.

The verdict is decided on the bootstrap INTERVAL, never the sign of a point
estimate — calling +0.015 a bump because it is positive is the
argmax-on-flat-optima trap, and the first version of this script did exactly that
before it was fixed.

### 7. The Greenland block's convergence, asked directly (`diag_gis_block_convergence.jl`)
`postprocess_mcmc_ext.jl` names only the worst four of its 19 failing marginals,
one of which is Greenland (`gis_f`). That understates it. Asked for the block:

| param | R̂ | ESS | per-chain medians | |
|---|---|---|---|---|
| `gis_c1` | 1.015 | 273 | 0.0334 / 0.0334 / 0.0318 / 0.0330 | ok |
| `gis_alpha_f` | 1.029 | 223 | 0.0031 / 0.0041 / 0.0033 / 0.0037 | ok |
| `gis_beta_f` | 1.025 | 229 | 0.0052 / 0.0055 / 0.0042 / 0.0052 | ok |
| `gis_c0` | 1.102 | 52 | 0.0416 / 0.0413 / 0.0472 / 0.0406 | **FAIL** |
| `gis_beta_s` | 1.137 | 39 | 0.0074 / 0.0055 / 0.0134 / 0.0062 | **FAIL** |
| `gis_alpha_s` | 1.180 | 34 | 0.0067 / 0.0027 / 0.0076 / 0.0044 | **FAIL** |
| `gis_f` | 1.335 | 21 | 0.8177 / 0.7218 / 0.8475 / 0.7656 | **FAIL** |
| `gis_amp` | 1.001 | 6476 | 1.905 / 1.912 / 1.908 / 1.915 | ok (control) |

**The pattern is the finding: the FAST/SMB channel converges and the SLOW/dynamic
channel does not.** `alpha_f`/`beta_f`/`c1` sit at R̂ ≤ 1.03 with ESS 220-270,
while both slow-channel parameters, the initial condition and the partition fail —
and `gis_alpha_s`'s chain medians span **2.8×** (0.0027-0.0076), the same
four-chains-in-four-places signature as `ais_iceflow0` rather than a marginal
statistic. `gis_amp` is included as the CONTROL: it is likelihood-inert, and its
R̂ 1.001 / ESS 6476 localises the failure to the Greenland likelihood rather than
the sampler.

Two consequences:
- **The parameter-level prohibition extends to Greenland**, not just AIS. No
  channel-split credible intervals; `f = 0.78` is a point fit that reproduces
  Mouginot, not a posterior result.
- It gives the "proportional relaxation cannot serve a 7.42 m commitment" caveat a
  numerical fingerprint: **the channel carrying the multi-millennial commitment is
  precisely the one the 1900-2024 record cannot identify.** The hindcast
  constrains what it can see.

### 8. A CLEAN BASELINE — `LADRILLO.md` + tag `ladrillo-1.0`
Marcus asked for a clean current version of Ladrillo to keep working from. Four
parts:

**(a) `LADRILLO.md`** — the single definition: what the model is, which posterior,
what that posterior may and may not be used for, the canonical files and the
commands that reproduce each deliverable, the headline numbers, the standing
caveats to carry into any report, the quarantined vintages, and the open threads.
`README.md`/`METHODS.md` describe the public RFF × FaIR × BRICK pipeline, not this
development line, which is why it needed its own door.

**(b) extC consumers resolved — two migrated, five pinned.** The distinction that
matters: a script that USES a vintage gets migrated; a script that DESCRIBES one
gets pinned to its quarantine, because repointing it would make its own prose
wrong rather than update it.
- Migrated to L10: `plot_ladrillo_memo_figures.py`, `ladrillo_model_comparison.py`
  (both re-run; the memo figure set and the comparison tables are now L10).
- Pinned to `outputs/quarantine/20260813_extc_vintage/`: `scope_greenland_options.py`
  (the study that SELECTED A+B by showing stock SIMPLE under-responds — its
  premise IS extC), `scope_greenland_bochow2026.py`, `diag_gis_likelihood_leverage.py`,
  `diag_noise_model_and_grip.py`, and the extC arm of
  `diag_mengel_to_ladrillo_attribution.py` (whose attribution on record is
  mengel → extC, so both its arms are now archived vintages — correct).
- Both migrated scripts carry a single `LADRILLO_TAG` constant so the vintage
  travels into every row and label they emit.

**(c) The acceptance certificate now describes the SHIPPED model.** Re-run under
the amp law; the constant-amp original is preserved as
`quarantine/20260813_extc_vintage/slr_convergence_L10_constamp.csv`. The
certificate gained a **`gis_shape` column** so a constant-amp and an amp-law
certificate can never again be indistinguishable on disk.

| horizon | R̂ | ESS | sd(medians) | ratio | (was, constant-amp) |
|---|---|---|---|---|---|
| SLR@2100 | 1.000 | 1586 | 0.110 cm | 0.009 | 0.122, 0.010 |
| SLR@2150 | 1.000 | 1685 | 4.641 cm | 0.137 | 4.415, 0.130 |

The acceptance holds under the law, as predicted from the law being a
deterministic transformation applied identically to every chain. The 2150 caveat
is unchanged in character (ratio 0.137 vs 0.009 at 2100).

**(d) extC quarantined** — `outputs/quarantine/20260813_extc_vintage/` + README,
which separates the THREE superimposed changes (new posterior, new Greenland
module, amp law) so "the amp law lowered Greenland" cannot be read off the
component table. Greenland moves both ways: −0.45 cm at SSP1-2.6, +4.78 at
SSP5-8.5.

### 9. Thread 3 — the ridge hypothesis is FALSIFIED, and the two blocks have DIFFERENT diseases
`python/diag_block_ridge.py` + `python/diag_iceflow0_identifiability.py`.

**The decisive move was to stop looking at within-chain covariance.** A chain with
ESS 12 on an axis has not moved along it, so its own covariance describes the
slice it is stuck in, not the problem. What names the problem is the generalised
eigenproblem `B v = λ W v` (between-chain over within-chain covariance on
z-scores) — a directional R̂ whose top eigenvector is the direction the sampler
fails to mix.

**AIS: there is no ridge.** The standing hypothesis — that `ais_iceflow0` rides a
correlated ridge with `(bedheight0, slope, c)` and that a reparameterisation along
it is the fix, as `ais_runoff_Ton` was for `(h0, c)` — is **wrong**:

- worst-mixing direction = **`ais_iceflow0 +1.00`**, every other loading ≤ 0.06,
  carrying **98%** of all between-chain variance. It is a *coordinate*, not a
  combination.
- within-chain correlation matrix of the geometry block: **condition number 8**,
  eigen-spectrum 26/17/15/14/13/11/3%. No pair reaches |r| ≥ 0.8. There is
  nothing to rotate.

Following up on what it IS: pooled marginal **0.65 of the prior width**, mean
within-chain sd **0.49 of the pooled**, chain p05–p95 intervals that barely
overlap, decile traces that wander without dwell-and-jump structure, and
chain-mean `log_post` spanning **0.67 against a within-chain sd of 4.67**. So:
not a ridge, not multimodal, and not merely mis-scaled — a **weakly identified,
nearly flat axis** the sampler diffuses along at τ ≈ 3.3e5, with four chains
sitting in different places at indistinguishable objective values.

**Greenland: a different disease, and a milder one.** Worst-mixing direction is
`gis_alpha_s +0.70, gis_beta_s +0.65` — both slow-channel rate parameters with
the SAME sign, i.e. the overall level of `rate_s(T) = α_s·T + β_s`, 93% of the
between-chain variance. But the widths say the chains OVERLAP heavily:

| param | pooled/prior | within/pooled | reading |
|---|---|---|---|
| `ais_iceflow0` | 0.65 | **0.49** | chains in different places, weakly identified |
| `gis_f` | 0.30 | **0.81** | well constrained, chains overlap — just slow |
| `gis_alpha_s` | 0.19 | **0.88** | same |

So Greenland is **identified but slow**, the one case where sampling it better
actually buys something. And there is a concrete mechanism: `gis_alpha_s` has a
hard lower rail at 0 and its chain p05 values are 0.001 / 0.000 / 0.001 / 0.000 —
a random-walk proposal against a boundary, which is exactly what sticks.

**Thread 2 answered as a by-product.** `gis_beta_f`'s posterior is **0.05 of its
prior width** — the tightest ratio in the block — and it loads only 0.10 on the
worst-mixing direction, while the within-chain direction it does load on
(`c1`/`alpha_f`/`beta_f`, the fast channel) mixes fine. It is not riding an
unmixed ridge with `gis_f`. **Re-bounding its prior to the data support would
change essentially nothing**; option (a), keep it free, stands on measurement now
rather than on judgement.

**What this implies for the fixes** (was: "reparameterise the AIS geometry"):
- AIS — a reparameterisation is the WRONG fix, and so is a longer chain (it would
  sample the prior more thoroughly). The two real options are a **targeted
  large-step mixture proposal on that single axis** (cheap, directly targets
  diffusion, testable by ESS) and **adding information that grips it** — a
  grounding-line discharge constraint, the physically right partner to the A5 SMB
  anchor. The second belongs in the thread-4 calibration spec.
- Greenland — remove the zero rail: sample the slow channel as
  `(log r_s(T̄), tilt)` rather than `(α_s, β_s)`, which puts the unmixed direction
  on its own coordinate AND moves the boundary to infinity.

### 10. Thread 3, part 2 — the unmixed axis does NOT reach the deliverable
`julia/diag_iceflow0_propagation.jl` (400 draws/chain, ssp245, to 2300) +
`julia/diag_ais_param_sensitivity.jl` (the alignment control).

| comp | year | ratio@p50 | ratio@p95 | r with `ais_iceflow0` | chain medians (cm) |
|---|---|---|---|---|---|
| ais | 2100 | 0.012 | 0.183 | +0.000 | 5.76 .. 6.07 |
| ais | 2150 | 0.167 | 0.188 | −0.010 | 12.19 .. 24.83 |
| ais | 2300 | 0.058 | 0.122 | −0.003 | 133.02 .. 147.13 |
| total | 2100 | 0.009 | 0.209 | −0.004 | 44.91 .. 45.17 |
| total | 2150 | 0.137 | 0.159 | −0.013 | 69.57 .. 80.01 |
| total | 2300 | 0.051 | 0.095 | −0.005 | 215.82 .. 228.34 |

`ais_iceflow0` explains **R² < 0.001** of the projected Antarctic contribution at
every horizon, and the chains agree on the projection everywhere — including at
**p95**, which is the statistic R̂ cannot see and where the bimodal tipping tail
would show if it were going to.

**So the AIS sampler work is NOT load-bearing.** R̂ 2.359 on that axis is a
reporting caveat, not a defect to engineer away; thread 4 should spend its effort
on the noise model instead.

**The alignment control, because r ≈ 0 for a grounding-line flux coefficient is a
surprising result and a surprising result is presumptively a bug.** A
draw/projection misalignment would produce exactly that table. Correlating the
same projections against parameters the AIS must depend on:

| parameter | r@2100 | r@2150 | r@2300 |
|---|---|---|---|
| `antarctic_temp_threshold` | −0.590 | −0.659 | −0.645 |
| `ais_gmst_amp` | +0.413 | +0.461 | +0.467 |
| `ais_iceflow0` | −0.019 | −0.032 | −0.033 |
| `antarctic_alpha` / `antarctic_gamma` / `ais_mu` | ≤ 0.05 | ≤ 0.05 | ≤ 0.05 |

The kernel resolves parameter→projection dependence at **20× the axis**, with
physically correct signs (a higher tipping threshold means less loss; more
Antarctic warming per degree global means more). The ~0 is physics. The AIS
projection is governed by **when it tips**, not by how fast ice flows once it
does — which is the same story the bimodality has been telling all along.

**2300 checked across chains for the FIRST time, and it is BETTER than 2150**
(0.051/0.095 against 0.137/0.159). Physically coherent: by 2300 most draws have
tipped and the distributions re-converge. The standing caveat is refined —
**2150 is the worst horizon**, not the start of a worsening trend.

**One process note worth keeping.** Two runs of the propagation script died just
after printing the first control row and I attributed it to memory pressure from
a `pkill` race. That was wrong: it is Julia SOFT SCOPE — a top-level `for` makes
an accumulator assigned inside it a new local, so `ctlmax` was undefined at the
verdict line. The memory-pressure story was plausible because the box really does
swap on these 2.2 GB reads, which is exactly why it went unexamined for two runs.

### The flat-hold above 2.75 K — the original reasoning, superseded by item 6
Sub-choice 1 recommended holding S flat above 2.75 K because the 3.25 K bump is
scenario composition. That is still the right call on evidence, but the label
"conservative" does not survive measurement: over 3-4.5 K the raw binned curve
gives S ≈ 0.878-0.883, *above* the held 0.860, so flat-holding assumes slightly
MORE decline than CMIP6 shows and lowers G4 by 0.41 cm (7.78 → 7.37). Both arms
are emitted (`gis_amp_shape.csv`, `gis_amp_shape_fullcurve.csv`, selected with
`LADRILLO_GIS_SHAPE=<stem>`) so the arm is run, not argued. **Still Marcus's
call**; the default is the flat-hold.

## [unreleased] — 2026-08-13 — Ladrillo 1.0 step 5 stages 2+3 DONE; accepted on the deliverable; the Greenland amp law measured

### Stage 2 — `overdispersed_starts.csv` rebuilt for 55 params (commit `2ddb971`)
The file on disk was the **52-param extC vintage**, so `--overdisperse` hard-errored.
Rebuilt from the 2nd half of `chain_L10tune2_seed2026_n2000000.csv` at `ais_iceflow0`
quantiles 0.02/0.35/0.65/0.98, in seed order. The extC file is preserved as
`overdispersed_starts_extC52.csv` — its working copy differed from BOTH HEAD (39 cols)
and `.pre_extc_bak`, so it was the only copy of that vintage.

**Gate worth reusing:** the recomputed logposteriors reproduce the chain's stored
`log_post` **to the digit** (42.20 / 44.79 / 46.02 / 45.84). That is an exact round-trip
through the calibrator's own likelihood; a bare "is it finite" check would have passed a
permutation of same-scale parameters.

### Stage 3 — production run, and a 4.8× launch bug (commits `304f99e`, run complete)
4 × 2M, seeds 2026–2029, acceptance 0.236–0.237, all seeded from
`adapted_cov_L10tune2_seed2026.csv` **as-is with no "name-mapped" fallback**.

**Tried and corrected:** the naive parallel launch reported ETA ~11h. Since stage 1's
*solo* chain did the same 2M in 2h25m, that was treated as contention, not cost. Julia
defaults to `BLAS.get_num_threads() == 4` and the box is an **Apple M4 with only 4
performance cores** (+6 efficiency), so four chains put 16 BLAS threads on 4 P-cores with
about half of each process's ~200% CPU being spin-wait. Pinning `OPENBLAS_NUM_THREADS=1`:
**ETA 11:01 → 2:17**, run finished in ~2h15m. Threaded BLAS was never buying anything —
the RAM sampler's per-iteration work is a 55×55 Cholesky. Recipe now in the calibrator
header.

### Convergence — parameters FAIL, deliverable PASSES (commit `322387a`)
`postprocess_mcmc_ext.jl --tag=L10` reports **19 non-converged marginals** led by the AIS
geometry block (`ais_iceflow0` **R̂ 2.359**, ESS 12.0, τ 3.3e5; `antarctic_alpha` 1.505;
`gis_f` 1.335) and correctly REFUSED to write the canonical subsample.

Read as the diagnostic working: the base diagnostic's header already records
`ais_iceflow0` at R̂ 1.320 / ESS 10.6 in the 35-param v-next calibration, and ours is worse
for a mechanical reason — **the starts are dispersed along `ais_iceflow0` itself**, and at
τ≈3.3e5 a 1e6-draw post-burn half holds only ~3 effective samples of that axis.

**Blocker found:** `diag_slr_convergence_by_chain{,_extc}.jl` are hard-wired to
`greenland_a` and die on L10 chains — the same class as the hard-wired-to-stock-SIMPLE
projection kernel. New `diag_slr_convergence_by_chain_ladrillo.jl` **delegates** the
draw→BRICK mapping to `ladrillo_projection.jl` rather than re-implementing it inline
(inline duplication is how the kernel drifted before), so it cannot certify a different
model than the projections use.

| horizon | R̂ | ESS | sd(medians) | mean(sd within) | ratio |
|---|---|---|---|---|---|
| SLR@2100 | **1.000** | 1588 | 0.122 cm | 12.487 | 0.010 |
| SLR@2150 | **1.000** | 1680 | 4.415 cm | 33.867 | 0.130 |

Pooled SLR@2100 q05/q50/q95 = **43.57 / 46.59 / 79.19 cm**; @2150 = 64.74 / 74.23 / 161.12
(rel 1995–2014, ssp245). The AIS ridge does not propagate to the projection.
**Caveat:** the 2150 median spread is 13× the 2100 value, consistent with the AIS tipping
tail being the slowest-mixing feature — flag it wherever 2150 is reported.

### The Greenland amp(GMST) law, measured (commit `26914eb`)
40 CMIP6 models, `{historical, ssp126/245/585}` (ssp370 excluded as the aerosol outlier,
as in the Antarctic work). `reduce_cmip6_tas_gis.py` **imports `build_t_gis`'s mask
machinery** — same GTN-G polygon, subgrid, Berkeley land fraction, 59–70 N zone — because
otherwise the CMIP6-vs-observed comparison measures the mask. Mask validated: lat
58.9–70.2, lon −55..−22.5, Iceland weight exactly 0.

- **The decline is real:** secant slope **−0.0503/K [−0.0792, −0.0120]**, through-origin
  −0.0487/K (agreeing to 0.002/K). Balanced 40-model panel falls monotonically
  **1.498 → 1.284 over 0.75–2.75 K**.
- **ABANDONED as evidence — the observed window sequence.** early 3.604 → modern 1.792 is
  a factor 2.01; the SAME estimator on the SAME windows in CMIP6 gives 0.91, and CMIP6 does
  not reproduce the observed early ≫ full > modern ordering at all. The early window's
  CMIP6 span is [0.247, 3.853], i.e. the estimator is enormously **noisy rather than biased
  high**, so the observed 3.604 is one noisy draw. **Do not cite 3.60 → 1.79 as a physical
  decline.**
- **Keep the observed LEVEL.** 1.922 is only **+0.52 sd** above the CMIP6 full-window mean
  1.604 (15% of models exceed it) — high side, inside the spread, not an outlier. Adopting
  CMIP6's ~1.51 would discard an observational constraint the models do not contradict.
- **Unresolved above ~3 K:** a bump at 3.25 K SURVIVES the balanced panel, so it is not
  model dropout — likely scenario composition (a model only reaches 3.25 K under ssp585).
- **The amp law does NOT close the 2100 gap.** Anchored, amp → ~1.67, putting the spread
  near 8.7 cm against the 6.3–7.3 band: roughly 40% of the gap, not "most of the
  explanation" as expected. Recompute on the production posterior.

MCM-UA-1-0 dropped from the reduction (nonstandard coord names).

## [unreleased] — 2026-08-12 — Greenland A+B is wired into the joint calibrator: step 5 can run

The module was validated in isolation but nothing referenced it from
`calibrate_mcmc_ext.jl` (`grep greenland_ab` returned 0). This is the wiring, so
step 5 is now launchable. Commit `0e53c2d`.

### What changed
- **Model**: `build_brick_nu3_gis` puts `greenland_ab` in the Greenland slot.
  **`--stock-gis` reverts** and reproduces the extC setup exactly — 52 params,
  `logpost(θ0) = −849.24`, matching the pre-build run to the digit.
- **Driver**: the REGIONAL south-Greenland series, built **inside the
  calibrator** from `t_gis_zones.csv` with the same anchor-preserving
  `amp × GMST` splice the glacier blocks use (amp 1.92). **The external
  interface stays GMST + OHC only** — the drop-in property that separates
  Ladrillo from MAGICC-SLR.
- **7 sampled parameters** `gis_{c1,c0,f,alpha_f,beta_f,alpha_s,beta_s}`, with
  **`gis_g` FIXED at 0** (item 4.1) and `gis_v0` structural. Centres are the
  converged offline fit **at g = 0**, not the g = 0.917 fit: `(c0, g)` is a flat
  manifold and `c0` moves 4.04 → 61.99 cm along it at identical nlp.
- **Mouginot 2019 partition ported into the joint likelihood.** The offline cell
  is explicit that this is what makes the two-channel split identifiable, so
  omitting it would have left `f` unidentified in the joint fit.
- **Covariance**: `OLD52_NAMES` name-maps the extC1 tuned proposal into the new
  54-parameter set — **47 of 52 rows carried over**, 7 fresh diagonal. The
  glacier rows ARE mapped this time (extC and Ladrillo 1.0 share that structure).
- `update_brick_params!` gains `skip_greenland`, mirroring `skip_glaciers`:
  stock SIMPLE's five parameters do not exist on `greenland_ab` and Mimi throws
  `KeyError` rather than ignoring them.

### New gate — suite step 5/5
`--gis-check` runs the calibrator's model at the **exact offline g = 0 vector**
and compares the four numbers the offline cell reports for it.
`validate_greenland_ab.jl` tests the **component**; the driver, the fixed `g`
and `v0`, the re-reference frame and the Mouginot windows all live in the
**calibrator** and none of them was covered.

**It earned its place immediately**, catching two errors in the build it was
written to check: the `gis_f` prior had been centred on the Mouginot share
(0.735) rather than the offline fitted `f` (0.7826) — which would have counted
Mouginot in **both** the prior and the likelihood — and a sign flip in the
mid-century bias convention. All four now match the offline cell to **0.0000**:
RMSE 0.0617, 1942–1982 bias +0.0146 cm, 2003–2018 rate 0.7749 mm/yr, Mouginot
surface share 0.7351.

### Smoke
4000 iterations, seed 2026: **acceptance 0.227**, all seven new parameters
mixing, **logpost −845 → −696**. The joint likelihood is taking the Greenland
deal rather than suppressing it. Not converged — the pre-registration read
belongs to the production run.

### Priors — signed off, with the caveat on record
Marcus 2026-08-12 chose the weak offline-centred priors over flat (σ = 1e3) and
over a 10×-wider variant. **The caveat is that the offline fit was made against
the same gis target the joint likelihood scores**, so the centres re-use data
the likelihood already uses. The σ's are wide enough that the prior contributes
little (the smoke moved `alpha_s` 0.0071 → 0.039 and `f` 0.78 → 0.89), so the
centres function as a starting point rather than as information. **Any methods
section must say so.**

## [unreleased] — 2026-08-12 — AR(1) is misspecified on every stream, the total stream is 56% redundant, and Vivek's mechanism does not transfer

Combined diagnostic `python/diag_noise_model_and_grip.py`, full argument in
`notes/note_2026-08-12_noise_model_stream_dependence_and_grip.md`. Three threads
run as one: §6.1 of the Vivek note, the AR(1) double-counting caveat flagged
when the gate-3.1 σ ruling landed, and item 4.3 (TE vs a modern OHC target).

### The machinery was validated before its rejections were believed
Self-test on simulated AR(1)+band: ρ recovered, Ljung-Box **p = 0.84**, BIC
prefers the true model by 24.8. Two earlier versions of the self-test failed —
signal-to-noise, then genuine indistinguishability at ρ = 0.97 — and both
failures were the test's design. A **resolution probe** then establishes that
BIC separates AR(1) from a random walk reliably only up to **ρ ≈ 0.8**
(12/12 draws), falling to 8–10/12 above ρ = 0.9. So a ±6 ΔBIC on a series with
ρ ≈ 0.99 means "the data cannot tell".

### The five streams are not independent — algebraically
`dang_resid = sum(component resids) + closure (+ R19 + the gsic δ ramp)`. The
identity explains **55.9%** of the total residual's variance;
corr(dang, Σcomponents) = **+0.81**; the remainder (sd 0.276 cm) is the two
genuine model terms. **Over half the total stream's information is already in
the component streams**, and the likelihood scores it as a fifth independent
observation anyway. Stronger than Vivek's finding: his cross-stream correlation
is empirical, ours is algebraic.

### No noise model in the family fits
Ljung-Box on the Cholesky-whitened residuals gives **p = 0.0000 for every one of
the five streams against every one of six models** (white, AR(1), AR(2),
ARMA(1,1), random walk, trend+AR(1)); best case p = 0.0001. Q runs 47–482
against a χ²₁₀ critical ~18. A **random walk is never excluded** — the 95%
profile for ρ includes 1 on all five streams. And the **re-referencing is not
the cause**: repeating everything under a REML transform of the 1995–2005
re-reference operator moves no verdict by more than ~2 BIC, which
**disconfirms** the hypothesis flagged with the σ ruling. The honest description
is that these residuals are **systematic model error, not noise**.

### Vivek's mechanism does NOT transfer — §6.1 closes as a negative
Projecting out the leading common factor (50.3% of cross-stream variance) moves
ρ by less than 0.01, and for gis (0.992 → 0.994) and steric (0.981 → 0.986) it
moves the **wrong way**. The persistence is intrinsic, not cross-stream leakage.
**Step 5 does not need a dual pre-registration**, and there is now a second
reason not to adopt an R-sampling likelihood on top of the 32× wall clock.

### The total is the loosest constraint in every window
σ on a window-mean offset, cm: over 1942–1982, gis **0.085** vs the total
**0.300** — and 0.252 with the closure term switched OFF. **The total was never
what limits a mid-century Greenland correction; the gis component target is.**
So a step-5 outcome-3 cannot be blamed on the total or on the closure σ. What
the closure σ cost, in these units: **+19% mid-century, +62% modern** — the
untuned ruling loosens the well-observed present ~3× more in relative terms,
which is defensible (the shape is Frederikse's) but is worth having on record.

### Item 4.3 CLOSED — TE's expansion efficiency is right
extC `thermal_alpha` p50 **0.1540** kg m⁻³ °C⁻¹ = **0.1010 cm per 10²² J**,
against **0.1043** observed (NOAA 0–2000 m steric on Zanna+IGCC OHC, 2005–2024,
like-for-like) and 0.1133 on Zanna+Cheng; physics range 0.1011–0.1348. So extC
is 3% below the IGCC-based value at the bottom edge of physics. **The
"te_α ~3× below physics" concern refers to Wong's v1.2 calibration (0.057),
which extC already superseded.** What remains is a **level** offset — the steric
residual averages +0.242 cm — which is a `thermal_s0` question, not 4.3's.

### Not changing the noise model before step 5
The misspecification is real, but it is not new, extC was calibrated under it,
and changing it now would make Ladrillo 1.0 incomparable to extC on top of
everything else in flight. Queued for after 1.0, ranked in the note §6.

## [unreleased] — 2026-08-12 — Vivek's joint-vs-original BRICK calibration artifacts reviewed; Zemp rejected as a new stream, Dangendorf retained over Wang 2024

`notes/note_2026-08-12_vivek_joint_calibration_artifacts.md`. Two figure-only artifacts
comparing a Turing per-block RAM sampler **with a sampled cross-stream correlation matrix R**
against the original independent-per-stream scheme, on standalone BRICK (Zemp glaciers,
Wang et al. 2024 GMSL, 4×10M sweeps).

**Headline:** joint costs **33.8 h vs 1.06 h** (31.8× more wall clock) for 2.7× median ESS
(234,829 vs 86,117) and a clean R̂ (1.0059 vs 1.0231) — **11.7× less efficient per hour**.
Projections barely move: ≈ +0.02 m on 2100 SSP2-4.5 GMSL, essentially all of it Greenland
(+≈11%) and thermal (+≈6%); glaciers, AIS and LWS unchanged.

**What it changes for us — one item, and it is a pre-registration item, not a code item.**
Sampling R drops `rho_gmsl` **0.9596 → 0.8828**. Gate 3.1's verdict rests on near-unity
per-series AR(1) (ρ_gis 0.985, ρ_steric 0.973) removing 14–16× of the leverage on the
mid-century GIS offset, and `prep_recalib_targets_ext.py` already flags that an
anchor-shaped closure σ may double-count level correlation. This is independent evidence
for that mechanism: a near-unity per-series ρ can be cross-stream correlation with nowhere
else to go. **Step 5's pre-registration should state the expected posterior under both
likelihood structures** so an ≈-extC result is not misattributed. Cheap test proposed:
empirical cross-stream correlation of the extC residuals.

**Zemp — REJECTED as a calibration stream (would double-count).** Verified from Frederikse
2020's published Methods this session: the glacier component draws each ensemble member
randomly between Marzeion-2015 and **Zemp 2019** for 1961+, and uses Marzeion alone before
1961. Zemp is therefore already inside our C3 target, and cannot help the 1900–1940 era
where C3 is weakest (its record starts 1961). Confirms `memo_2026-08-05` §2c from the paper
rather than from Frederikse's code. Retained as optional work: split the 5000-member
ensemble by branch to separate *method-choice* from *within-method* σ in C3's mid-century band.

**Wang et al. 2024 vs Dangendorf 2024 — Dangendorf RETAINED.** Wang (J. Climate 37(24)) is a
Church-&-White-lineage RSOI tide-gauge reconstruction; published 1900–2019 trend
**1.6 ± 0.2 mm/yr (90%)** vs our Dangendorf CSV's computed **1.499** over the same window —
**+0.10 mm/yr ≈ +1.2 cm cumulative**, inside both stated uncertainties. Computed here for
context: Church & White 2011 vs Dangendorf 2024 = 1.689/1.427 (1900–2013), 1.526/1.380
(1900–1990), 2.149/1.580 (1961–2013) mm/yr. Wang sits between its ancestor and Dangendorf.
Switching would invalidate the gate-3.1 closure work, which lives in the
Frederikse-vs-Dangendorf frame; Wang is carried as a **documented sensitivity** instead.

**Also logged:** every original-scheme R̂ failure is an AIS parameter (`antarctic_slope`
1.0231, `precip0` 1.0120, `c` 1.0119, `runoff_height0` 1.0110), all cleared by the joint
scheme — so AIS non-convergence has a *sampling* component on top of the prior-dominance
one the red team recorded. And the DAIS block's cross-scheme agreement to 3–4 s.f. is
*consistent with* prior-dominance but is **not** evidence for it without a prior-vs-posterior
overlap test, which we should run on our own block.

**Not adopted:** joint/R sampling for step 5 — 32× wall clock for a ≈0.02 m projection
change on a model whose Greenland and glacier blocks we have replaced anyway.

## [unreleased] — 2026-08-12 — The Greenland cell-comparison fits were never converged; items 4.1 and 4.2 decided against the corrected table

### The bug
`python/gis_offline_cell.py` reported optima that were not optima. Starts were
drawn **uniformly** over rate bounds spanning five orders of magnitude
(`[1e-6, 0.2]`), 60 of them, and the best Nelder-Mead result was taken without a
restart. **The tell was already in the committed output:** 214 of the 225 A+B
`(f, beta_f)` ridge points — which *fix two parameters* and re-optimise the rest
with a *weaker* inner optimiser — scored **below** the reported 8-parameter
optimum of 42.52. A constrained fit cannot beat an unconstrained one.
Re-evaluating the committed parameter vector under the corrected code reproduces
42.5228 exactly, so this is one objective at two points, not two objectives.

Pre-fix outputs quarantined with the full impact table at
`outputs/quarantine/20260812_gis_offline_cell_underconverged/`.

### Corrected protocol, and the invariants that now guard it
Log-uniform draws on the rate axes; `N_MULTISTART` 60 → 240; restart-until-no-
improvement `polish()`; **basin-hopping** jitter (multiplicative on log axes);
and **nested warm starts** — `stock → B`, `A → A+B`, lifting one channel into two
identical ones with `f` = the observed Mouginot share so the lifted point carries
zero extra penalty. The first three alone were not enough: B still landed at
234.92 on one run and 245.06 on the next, both above the value stock — which B
nests — had already reached.

Three checks now run every time and **assert**:
- `convergence_check()` — no constrained ridge point may beat the optimum.
- **nesting** — a container cell may not score above the cell it nests.
- **repair pass** — a violating ridge point is re-used as a *start* before the
  assert fires, so the gate reports genuine failures rather than optimiser luck.
  It fired on this run: B 234.92 → **232.07** via a 232.18 witness point.

### The corrected table (nlp, RMSE cm, 2100 spread cm)

| cell | npar | nlp was → is | RMSE was → is | spread was → is | G4 |
|---|---|---|---|---|---|
| incumbent | 5 | 980.04 → 980.04 | 0.533 → 0.533 | 2.29 → 2.29 | — |
| stock | 5 | 234.92 → 234.92 | 0.325 → 0.325 | 7.25 → 7.25 | OK |
| A | 5 | 17.87 → 17.87 | 0.061 → 0.061 | 10.85 → 10.85 | — |
| B | 8 | 246.61 → **232.07** | 0.315 → 0.282 | 6.90 → 7.27 | OK |
| **A+B** | 8 | 42.52 → **17.856** | 0.099 → **0.062** | **6.30 → 10.44** | **OK → —** |
| A+B' | 7 | 62.78 → **19.15** | 0.068 → 0.077 | 6.27 → **0.00** | — |
| A+B+C | 7 | 2038.31 → **563.20** | 1.675 → 0.844 | 51.99 → 0.28 | — |
| A+B'+C | 6 | 724.26 → **118.15** | 1.009 → 0.350 | 13.08 → 6.24 | — |

**Decision 4 (A+B is the module) SURVIVES, and on better evidence.** A+B has the
best score of any cell, matches A's hindcast (RMSE 0.062 vs 0.061, G1/G2/G3 all
pass) and *additionally* reproduces the Mouginot partition to four figures
(0.7351 against the 0.735 constraint), which single-channel A cannot represent at
all. The regional driver is what does the work: stock/B ≈ 232–235 against
A/A+B ≈ 17.9. Option C still fails decisively (563 / 118).

**What changed and must be re-reported: G4.** A+B's 2100 scenario spread is
**10.44 cm, ABOVE the 6.3–7.3 evaluation band**, not 6.30 on its floor. The
handoff statement "the joint calibration can only push it down" is retired —
pushing it down is now the desirable direction.

**Also flagged:** A+B' (the SMB-rate variant) now returns a 2100 spread of
**exactly 0.00 cm** — all three scenarios give 1.31 cm — because its
anti-overshoot clamp saturates at the converged optimum. Suspicious uniformity,
and a structural pathology of that cell. It is not the module, so it is recorded
rather than chased.

### 4.1 — `g` is FIXED AT 0
Not sampled in step 5. The hindcast cannot see it: profiled over [0, 0.8] the
objective moves **4e-4 nlp** and the 2100 projections do not move at all
(max |Δ| 0.000 cm); LR accepts `g = 0` at 2Δ = +0.001 against χ²₁ = 3.841. It is
**confounded with `c0`** — two converged runs returned (c0 61.99, g 0.917) and
(c0 5.21, g 0.183) at the same nlp = 17.856 with 2100 projections agreeing to
**< 0.001 cm**. It only ever existed so the since-rejected ladder cells could
start sensibly. `g = 0` restores stock SIMPLE's own initial condition.

### 4.2 — `beta_f` stays FREE (Marcus, 2026-08-12), and the handoff's premise is falsified
"Fixing it at a literature SMB response time costs nothing measurable" is
**wrong**: `beta_f = 1/10 yr` is rejected at **2Δ = +133** and collapses the
Mouginot surface share to **0.34** against a 0.735 constraint. In the share form
the SMB channel drains a multi-millennial commitment, so "fast" names which
*physics* the channel carries, not a short time constant — at the optimum
τ_f = 86 yr. The data bound `beta_f < ~1e-2/yr` and cannot resolve below that
(flat to Δ < 2.3 across five decades, 1e-6 → 9.8e-3). But it is unidentified
**and consequential**: `beta_f = 0` costs only 2Δ = +0.55 yet moves 2100
SSP5-8.5 by **1.70 cm** and the spread by 1.28 cm. Marcus ruled: keep it free
and let the joint likelihood try to identify it, rather than hide 1.7 cm inside
a point value. Re-bounding the prior to the data support was offered and
declined; the prior spans four decades the offline fit excludes, so sampler
efficiency there is worth watching.

**The old separability claim is void either way.** "100% of its local range
within Δ < 2.3" was measured against the wrong reference, over a ×30 window
pinned to a railed optimum (1e-6 to 3e-5), with point-to-point optimiser scatter
of ±6 nlp — larger than the Δ = 2.30 threshold being applied to it.
`python/diag_gis_g_betaf.py` profiles the full prior range instead.

## [unreleased] — 2026-08-12 — Gate 3.1 ruling landed: the total target's σ now carries Frederikse's own budget-closure spread

**Marcus's ruling** on the open methodological decision left by gate 3.1 (the
five component targets sum **+0.74 cm above** the independent total target over
1950–1980, which
`notes/note_2026-08-11_gate31_target_conflict_verdict.md` established is
**Frederikse 2020's own mid-century budget non-closure**, our closure sitting at
z = +0.006 against their 5000-member ensemble median):

> **Carry it as uncertainty on the total, across the WHOLE span** — not the
> 1950–1980 window alone — **using the ensemble's own per-year closure spread**,
> with no tuning.

Marcus asked whether the inflation could be larger in the poorly-observed past
and smaller in the well-observed present *without* inventing a decay function.
It can, and the shape is not ours to choose: the weighted sd of
(Σ components − their GMSL) **across the 5000 members, per year**, with each
member re-referenced to 1995–2005 exactly as the targets are, is

| 1900 | 1950 | 1980 | 2000 | 2018 |
|---|---|---|---|---|
| 2.375 cm | 1.389 | 0.776 | 0.460 | 0.775 |

In quadrature with the existing total σ (Dangendorf SE ⊕ LWS band) that is
**1.37× at 1900, 1.25× at 1950, 1.11× at 2000, 1.90× at 2018**. The modern
rise is not an artifact to be removed: the spread is pinned at the 1995–2005
anchor and grows away from it in **both** directions, which is the correct
structure for a level anomaly scored in that frame, and Dangendorf's own σ
collapses to 0.44 cm in the altimetry era so the *ratio* rises even as the
absolute inflation falls. Two alternatives (flatten after the anchor;
pre-1993 only) were offered and **declined** — both buy monotonicity with a
discretionary choice.

**CAVEAT ON RECORD, flagged not corrected:** the total channel also carries a
sampled AR(1) with ρ_steric ≈ 0.97, so an anchor-shaped σ may partly
double-count level correlation.

### Implementation
- `python/prep_recalib_targets_ext.py`: new `load_closure_sigma()` and a
  `dang_closure_sig` column. Ensemble ends 2018, target runs to 2024 → held
  flat past the ensemble, the same FLAGGED convention already used for LWS.
  **Every pre-existing column is bit-identical** (max|diff| 0.0 across all 18);
  only the column is added.
- `julia/calibrate_mcmc_ext.jl`: the `isdang` branch of `make_series` adds it in
  quadrature alongside the LWS band term, and the run log now prints the
  inflation at 1900/1950/2000/last year. `--no-closure-sigma` reverts.
- Verified live: `logpost(θ0)` = −831.74 with the flag, −849.24 without it, so
  the term is reaching the likelihood and the toggle is not inert.

## [unreleased] — 2026-08-12 — The model is now **Ladrillo** (was BRICK-F\*)

Marcus, 2026-08-12. `ladrillo` is Spanish for *brick* — the name keeps the
provenance explicit while marking that the model has diverged from BRICK.
*(Etymology / rationale sentence for the sharing memo and any paper: **Marcus to
draft** — placeholder only.)*

### Version definition (Marcus, 2026-08-12)
**Ladrillo 1.0 = the version carrying the Greenland update as well as the GSIC and
Antarctic updates** — i.e. the posterior produced by Greenland pass-1 **step 5**
(the joint recalibration), which has NOT been run yet. Everything on this branch
today is **pre-1.0**: `extC` has the GSIC and Antarctic work but *not* Greenland.
Do not label current outputs 1.0.

### Scope — three axes, only two renamed
Full inventory and hazard analysis in `notes/scoping_2026-08-11_ladrillo_rename.md`.
- **Display name** `BRICK-F*` → `Ladrillo`, and **code identity**
  `brickf_`/`BRICKF_`/`BrickF` → `ladrillo_`/`LADRILLO_`/`Ladrillo`: **renamed**.
- **Vintage and component tags** (`extC`, `greenland_ab`, `glaciers_nu3`):
  **unchanged** — they are orthogonal axes. "Ladrillo, extC posterior" still parses.
- **Repo name and Zenodo DOI: untouched.** `README.md` and `CITATION.cff` never
  named the model, so repo identity and model identity were already decoupled.

### The hazard, and how it was handled
`brickf` is a substring of `brickfm` — **BRICK-FM is a different model** (the
MimiBRICK-FM / Mengel line), with 130 references in this repo. A naive
`sed s/brickf/ladrillo/g` would have corrupted every one of them. Instead:
- Five **anchored** patterns, each provably unable to match BRICK-FM
  (`BRICK-F\*` needs the literal `*`; `BRICKF_`/`brickf_` need the underscore;
  `BrickF` is case-sensitive; `_brickf` is negative-lookahead-guarded against
  `_brickfm`). Verified `\bbrickf\b` matches 0 times, so the set is exhaustive.
- Per-file assertion that the BRICK-FM count is unchanged; the script aborts otherwise.
- **297 substitutions across 21 files; BRICK-FM references before = after = 130.**

### Verification — the rename is semantically null, so the gate was byte-identity
1. `run_ladrillo_tests.sh` (all four suites) **passes**, and its output is
   **byte-identical** to the pre-rename run once the renamed identifiers are
   normalised.
2. No tracked output changed content — only `git mv` renames are staged. (The two
   files dirty in `git status` were already dirty before this work and are
   unrelated: `figures/diag_gis_regional_driver.png`,
   `outputs/mcmc/overdispersed_starts.csv`.)

### Path mapping — frozen notes reference the OLD names
Dated `notes/` keep their filenames **and** their contents: they are records of
what was known when written, and rewriting them would falsify provenance (same
principle as quarantining outputs rather than deleting them). Use this table to
resolve any old path a note mentions:

| old | new |
|---|---|
| `julia/brickf_projection.jl` | `julia/ladrillo_projection.jl` |
| `julia/posterior_predictive_brickf.jl` | `julia/posterior_predictive_ladrillo.jl` |
| `julia/project_ssps_components_brickf.jl` | `julia/project_ssps_components_ladrillo.jl` |
| `julia/test_brickf_projection.jl` | `julia/test_ladrillo_projection.jl` |
| `python/brickf_committed_ladder.py` | `python/ladrillo_committed_ladder.py` |
| `python/brickf_data.py` | `python/ladrillo_data.py` |
| `python/brickf_model_comparison.py` | `python/ladrillo_model_comparison.py` |
| `python/brickf_posterior_summary.py` | `python/ladrillo_posterior_summary.py` |
| `python/plot_brickf_memo_figures.py` | `python/plot_ladrillo_memo_figures.py` |
| `python/test_brickf_data.py` | `python/test_ladrillo_data.py` |
| `python/diag_mengel_to_brickf_attribution.py` | `python/diag_mengel_to_ladrillo_attribution.py` |
| `run_brickf_tests.sh` | `run_ladrillo_tests.sh` |
| `outputs/brickf_*.csv`, `figures/brickf_*.png` | `outputs/ladrillo_*.csv`, `figures/ladrillo_*.png` |

**Frozen on purpose (names unchanged):** `notes/memo_2026-08-10_brickf_sharing.md`,
`notes/redteam_2026-08-11_brickf.md`,
`notes/note_2026-08-11_gate32_mengel_to_brickf_attribution.md`. Code references to
these three were repaired back after the substitution rewrote them; every
`notes/*.md` path referenced from code was then checked to exist on disk.

### Deliberate remaining occurrences of `BRICK-F*`
`CHANGELOG.md` (history above this entry), dated `notes/`, this scoping note, and
`outputs/scope_greenland_bochow2026.csv` — the last being a **retracted** artefact
(Bochow-2026 emulator retraction) that must not be used regardless.

### Not done
- `data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv` still says
  "brick_mengel" although extC has no Mengel glaciers. **Already wrong before this
  rename**; kept as a separate correctness fix so the rename diff stayed
  byte-identity-checkable.
- Branch is still `brick-mengel-vnext`.
- Stale outputs under old names await the quarantine sweep already owed from gate 3.2.

## [unreleased] — 2026-08-11 — Gate 3.2 cleared: the 28 cm Mengel→F\* shift is 110% Antarctic, and it is a tipping-PROBABILITY shift

Second gated diagnostic. Full argument in
`notes/note_2026-08-11_gate32_mengel_to_brickf_attribution.md`.
Script `python/diag_mengel_to_brickf_attribution.py`.

### The proposed experiment was ill-posed and was not run
- The handoff proposed swapping the AIS block to BRICK-Mengel medians. Mengel
  sampled **6** AIS params; extC samples those 6 **plus 11 more** — and those 11
  *are* the re-parameterisation. A 6-Mengel/11-extC hybrid describes no
  calibrated model. Glacier structures also differ (2-τ vs 3-reservoir), so no
  single kernel runs both posteriors.
- Replaced by a **component decomposition** of the two projections, after
  checking both use the same forcing files, FaIR **mean** climate, and the
  1995–2014 baseline. (`proj_matched_ssp245_mengel_timeseries.csv` is NOT usable
  — it carries climate spread too.)

### Attribution, SSP2-4.5 medians @2100 (cm)
- Antarctic **43.05 → 11.74 (−31.32)**; glaciers 6.27 → 10.56 (+4.29); TE
  18.45 → 17.27 (−1.18); **Greenland 7.42 → 7.27 (−0.15)**; LWS 0.00;
  **total 78.02 → 49.48 (−28.54)**. Median non-additivity 0.18 cm.
- **The Antarctic is 110% of the shift**; glaciers partly offset it. The
  expectation on record ("mostly the Antarctic recalibration") is **confirmed**.
- Memory's 77.7 cm should read **78.02 cm** (`proj_ssps_mengel_summary.csv`).

### The correction that matters — it is NOT a level shift
- The shift is **−0.01 cm at SSP1-2.6**, −28.54 at SSP2-4.5, −19.09 at SSP5-8.5.
  The Antarctic distribution is **bimodal** (tipped vs not tipped by 2100) and
  the large movement sits at a *different quantile in every scenario* — always
  the one nearest that scenario's tipping fraction:
  SSP1-2.6 p95 46.29 → 6.12 (−40.16); SSP2-4.5 p50 43.05 → 11.74 (−31.32);
  SSP5-8.5 p05 54.14 → 21.98 (−32.16), p95 86.20 → 80.15 (only −6.05).
- What changed is **the probability of Antarctic tipping by 2100**, not the
  contribution conditional on tipping.
- **Reporting rule: "BRICK-F\* is 28 cm lower at SSP2-4.5 2100" is misleading**
  and should not appear. Quote a distribution, not a median.
- **And it is substantially prior-driven**: the red team records the eight
  non-converged AIS marginals as the block that sets the tail, and the SSP2-4.5
  p83 = 41.0 cm as prior- not data-driven. The tipping fraction *is* that
  quantity — so the largest movement in the programme lives in the least
  data-constrained part of the posterior. Present it with that caveat.

### Consequences
- Deliverables on the 78.02 cm vintage need the standing quarantine treatment
  (`outputs/quarantine/YYYYMMDD_<tag>/` + README). **Not done** — needs a sweep
  of affected deliverables. It is a **vintage difference, not a bug**; the
  README should say so.
- **Greenland pass 1 is untouched**: GIS moves −0.15 cm between vintages.

## [unreleased] — 2026-08-11 — Gate 3.1 cleared: the target conflict is Frederikse's own budget non-closure, and the Greenland fix is worth +12.4 logl anyway

Answers the blocking diagnostic before step 5 (joint recalibration). Full
argument in `notes/note_2026-08-11_gate31_target_conflict_verdict.md`.
**Verdict: proceed to step 5 unchanged; no data-side surgery required.**

### What the +0.74 cm mid-century conflict is (`python/diag_target_conflict.py`)
- Decomposed exactly (all series share the 1995–2005 reference):
  `Σ components − Dangendorf = (Σ comps − Frederikse GMSL) + (Frederikse GMSL − Dangendorf)`.
  Over 1950–1980 that is **+0.738 = +1.109 (budget closure) − 0.371 (reconstruction)**.
- **Not a splice.** Earliest modern-product year in any component target is 2019;
  it cannot reach the window. The total there is the Dangendorf reconstruction,
  not the NOAA STAR splice (2022+).
- **Not Dangendorf-vs-Frederikse** — that term has the *opposite* sign. Swapping
  in the independent Dangendorf total **reduces** the conflict by 0.37 cm
  (0.24 of Dangendorf's own per-year SE). The two reconstructions agree.
- **It is Frederikse 2020's own mid-century budget non-closure, inherited
  faithfully.** Our closure term (+1.109 cm) matches the weighted median closure
  of Frederikse's 5000-member ensemble (+1.104 cm) at **z = +0.006**. Ensemble
  spread on that window mean: sd 0.792, 5–95% [−0.188, +2.452] → ≈1.4σ,
  systematic but not significant at 5%.
- Provenance verified: ensemble `GMSL` is the observed tide-gauge reconstruction,
  **not** the budget sum (differs from Barystatic+Steric by up to 158 mm;
  cross-member correlation with the budget at 1950 = 0.085).

### The red team's prediction, corrected in magnitude and sign
- **The GIS miss is +0.822 cm over 1942–1982, not the 0.5–0.7 cm the memo
  carried.** Correct it wherever it appears.
- The model sits **below** the total target in mid-century (+0.322 cm), so the
  added melt moves the total *through* its target: residual goes −0.322 → +0.499,
  a sign flip of similar size, not a one-way 0.74 cm degradation.
- The GIS target matches at 1900–1930 (+0.058) and exceeds the model mid-century,
  i.e. it wants **more melt in the first half of the century** — the 1920s–40s
  southern-Greenland anomaly, which is exactly what driver option A delivers.

### Why stock BRICK-F\* under-melted Greenland — not the conflict (`python/diag_gis_likelihood_leverage.py`)
- The total channel's own σ over 1950–1980 is **1.538 cm**; a 0.74 cm conflict is
  0.47σ of it. Far too loose to have caused the under-melt.
- The mechanism is the **sampled per-series AR(1) noise model**. Pooled extC
  posterior medians (4 × 2,000,000 steps, second half): **ρ_gis = 0.985**
  (τ = 67.5 yr), **ρ_steric = 0.973**, against ρ = 0.45–0.62 for ais/gsic/dang.
  A 40-year systematic miss is reclassified as correlated noise nearly for free —
  the AR(1) removes **14–16×** of the leverage on a mid-century GIS offset
  (−27.7 vs −382.6 logl for a 0.65 cm step; −7.5 vs −122.8 for a smooth ramp).
- **n_eff caveat, recorded because the number is arresting.** n(1−ρ)/(1+ρ) gives
  n_eff = 0.93 for gis, but it describes the AR(1) term *alone* and **understates**
  the grip — the diagonal band term adds independent information each year (strip
  the band and the penalty rises to −141.7). Quote n_eff only with that
  qualification; the AR(1)+band figure is the one to trust. Both are conditional
  on noise params at their posterior medians, so they are upper bounds.
- **Decisive number, from the actual extC residuals rather than a synthetic shape:**
  gis residual −0.822 → 0.000 gains **+16.49 logl**; the total pays **−4.06**;
  **net +12.43 in favour**. The sampler should take the deal.

### Pre-registration updated
- **Outcome 1 expected** (Greenland improves, total degrades) — but "degrades"
  = the total's mid-century residual flipping −0.32 → +0.50 cm, 0.32σ of its own σ.
- **Outcome 3 is less likely than feared**: the AR(1) weakens the pull 14–16×,
  but +12.4 net logl survives it. If the posterior does come back ≈ extC, the
  cause is *not* the target conflict — look at sd_gis/rho_gis inflation next.

### Flagged for Marcus (methodological, not resolved here)
- The component and total targets cannot both be met to nominal σ in mid-century.
  **(a) do nothing and document** (recommended — the conflict is inside both σ's
  and keeps the only Frederikse-independent constraint at full strength), or
  **(b)** add the 0.792 cm closure sd in quadrature to the total σ in that window.
  Not to be resolved by whatever the sampler does — that is what produced the
  under-melt.
- **ρ_gis / ρ_steric ≈ 1 deserve their own decision** (same shape as the
  CarbonCycleEmulator AR(1) retirement, n_eff 0.8). Two of five component
  channels are weakly identified in level. Belongs with item 4.3 (TE vs a modern
  OHC target) — TE is the *other* ρ→1 channel, plausibly the same story.

## [unreleased] — 2026-08-10 — Greenland pass 1, steps 1–2: driver built on a real mask (two scoping numbers corrected), V_eq fitted to PISM

**Decision 1 settled (Marcus): PISM-dEBM is the single equilibrium ladder. No
Yelmo sensitivity arm.**

### Step 1 — the regional driver (`python/build_t_gis.py`)
- Builds the option-A southern-Greenland (59–70 °N) annual land-masked driver
  plus the whole-ice-sheet arm, from HadCRUT5 / Berkeley Earth / GISTEMP.
  Outputs `data/observations/t_gis_zones.csv` (+ `_allproducts`),
  `outputs/gis_driver_constants.csv`, `outputs/gis_amp_prior.csv`.
- **The mask was the bug.** `python/scope_greenland_zones.py` used a lon/lat box
  that put **Iceland** inside the southern band and Baffin/Ellesmere inside the
  northern ones, and applied a land mask **only to Berkeley Earth** — HadCRUT5
  and GISTEMP zone series were land+ocean blends over the whole box. Replaced by
  GTN-G 2023 region 05 polygon ∩ Berkeley 1° land fraction, subgrid-sampled,
  with region membership asserted by point test at build time.
- **Two scoping-note (§9) numbers are corrected.** A/B against the old box
  reproduces the scoping values exactly, so the shift is the mask, not code:
  - "products agree on southern Greenland to **1.19×**" was an artifact — ocean
    dilution in two of three products coincidentally pulled them toward
    Berkeley. Genuine spread **1.51×** (full window) / 1.58× (early).
  - the amplification **level is ~1.9, not 2.9**. Southern Greenland 1901–2024
    through-origin: 1.97 / 1.51 / 2.28 → **N(1.92, 0.32)**; modern (1961–2024)
    → N(1.79, 0.30). The §9 figure N(2.9, 0.2) came from the *early* window on
    the *contaminated* mask; both push it high. Prior sd is ~0.32, not 0.2.
- **Option A's leverage is unaffected**, checked: §3's "+2.2 → +5.9 cm" row used
  the RGI-r05 periphery driver at amp 2.04, and the corrected HadCRUT5 south amp
  is 1.97 — within 4%. The correction does not shrink the case for option A.
- **The zone choice survives and is stronger.** Re-validated on the corrected
  mask, south is still best-observed (1.51× vs 1.78–2.20× for central/north/all)
  and now clearly most relevant: melt-rate r = 0.80 vs 0.70 / 0.64 / 0.72. The
  scoping table had these in a 0.63–0.71 band that "did not discriminate".
- The spread is a **numerator** effect: the three globals agree to 0.04 °C at
  2015–2024 (1.259 / 1.262 / 1.222, HadCRUT5 matching the canonical IGCC 1.254
  anchor), so the products genuinely disagree about Greenland by ~0.5 °C / 30%.
- **Product choice resolved without a ruling**: all three pass the 1942–1982
  gate with the right sign (trend −1.4 to −2.2 °C/century, r = 0.80–0.87) and
  HadCRUT5 is marginally best in every window (0.80 / 0.91 / 0.87 / 0.95), which
  is also the glacier-module-consistent choice. Headline = HadCRUT5; the other
  two are written out so the arm is cheap.

### Step 2 — V_eq (`python/fit_gis_veq_pism.py`)
- Fitted in the ladder's native **GMT** frame on purpose, so it does not depend
  on the amplification: the regional driver drives the *transient*, the
  equilibrium is a function of the large-scale state.
- **No smooth parametric form fits, structurally.** Relative-weighted RMSE (m):
  linear 1.40, saturating 1.53, two-logistic 0.68, **pchip 0.000**. The ladder
  has three regimes — a low tail (0.05 → 1.64 m over GMT 0.5–2.18), a 4.6 m jump
  inside *one* 0.42 K rung interval, then slow saturation to 7.42 m. The
  two-logistic rails **both** widths at the rung-spacing floor: it is asking to
  be the interpolant. At GMT 2.5 the ladder says 5.17 m, linear/saturating 2.9.
- Adopted: **pchip through the rungs, anchored at (0, 0)**, verified monotone
  non-decreasing, no overshoot, bounded [0, V₀], max slope 15.9 m/K at GMT 2.39.
- **Weighting is not a detail.** Unweighted least squares in metres is decided by
  the top of a two-order-of-magnitude range: the absolute-weighted logistic2 is
  4× too high at GMT 0.50 and 2× at 0.92 — where the *hindcast* operates
  (present GMT ~1.25 → 0.53 m committed). That error would be absorbed as a
  slower response, the exact pathology this work exists to remove.
- **What the calibrator should sample: `pchip(T − dT)`, threshold location dT.**
  It is the only parameter that matters, and it matters in one place only —
  committed loss at SSP1-2.6 goes 6.50 / 1.54 / 0.36 m at dT = −0.8 / 0 / +0.8,
  while SSP5-8.5 is 7.42 throughout. This also makes the **Yelmo arm recoverable
  inside the PISM parameterisation**: Yelmo's SSP1-2.6 commitment of 5.34 m is
  pchip_shift at dT ≈ −0.7. A dT prior with a negative tail expresses the
  threshold disagreement without fitting Yelmo at all.
- **Step sharpness is not measured**: rungs are uniformly spaced at 0.4202 K and
  the collapse falls between two adjacent ones. Width parameters are bounded
  below at the rung spacing and rail there. Sharpness is a prior, not a datum.

### Step 2b — the dT prior (`python/set_gis_dt_prior.py`)
- **Box et al. 2022 check cleared** (Nat Clim Chang 12:808): 274 ± 68 mm
  committed by the 2000–2019 disequilibrium. Our 530 mm at present GMT is
  consistent — Box is explicitly "at least", and a current-geometry number, so
  the multi-millennial equilibrium should exceed it (their own
  2012-in-perpetuity variant is 782 mm).
- **dT ~ Normal(−0.63, 0.55) truncated [−1.58, +0.22].** PISM's own threshold
  (50% of V₀) is GMT 2.38, and both assessments put Greenland below it, so a
  prior centred on dT = 0 would encode "PISM is the best estimate":
  Bochow 2023 (Nature 622:528) 1.7–2.3 °C — *not independent*, it is our
  ladder's source; Armstrong McKay 2022 (Science 377:eabn7950) central 1.5,
  range 0.8–3.0 °C — independent. Upper truncation is the **Box floor**, not the
  literature: above dT = +0.22 the equilibrium commitment would fall below a
  measured lower bound. dT = 0 sits at +1.14 σ.
- **dT and τ are not separately identified in a one-channel model, and the
  direction is hostile.** Modern rate = commitment/τ, so a more negative dT
  demands a longer τ: dT = 0 → 630 yr, −0.63 → 1820 yr, −1.18 → 5349 yr. A
  one-channel fit absorbs any negative dT as a *slower* response — the pathology
  pass 1 exists to remove.

### Step 3 — the offline cell (`python/gis_offline_cell.py`)
**Acceptance test first.** Stock SIMPLE at the extC posterior medians, not
refitted, reproduces the incumbent: 2100 spread **2.29 cm** vs the known 2.16,
and the documented 1942–1982 miss at −0.83 cm. Two bugs were caught by it:
`g = 0` is BRICK's actual initial condition (V(1850) = v₀, 71 cm of
disequilibrium, *not* equilibrium — starting in equilibrium gave 0.11 mm/yr
against ~0.7 observed); and a fast channel relaxing toward a fixed *share* of
the commitment is incompatible with the ladder, so a second fast-channel form
(B′, SMB as a direct melt rate above an onset) was added.

| cell | RMSE cm | G1 | G2 | G3 | surf | 2100 spread | G4 |
|---|---|---|---|---|---|---|---|
| incumbent | 0.533 | – | – | – | – | 2.29 | – |
| stock | 0.325 | OK | OK | OK | – | 7.25 | OK |
| **A** | **0.061** | OK | OK | OK | – | 10.85 | – |
| B | 0.315 | OK | OK | OK | 0.78 | 6.90 | OK |
| **A+B** | 0.099 | OK | OK | OK | 0.74 | 6.30 | OK |
| A+B′ | 0.068 | OK | OK | OK | 0.36 | 6.27 | – |
| A+B+C | 1.675 | OK | – | – | 0.49 | 51.99 | – |
| A+B′+C | 1.009 | OK | OK | – | 0.53 | 13.08 | – |

- **The regional driver is the fix.** A alone: RMSE 0.533 → 0.061 cm, mid-century
  bias −0.828 → +0.014 cm. The 1942–1982 window is closed.
- **A caveat that changes the scoping diagnosis.** Refitting *alone*, with no
  structural change, takes stock from 2.29 to 7.25 cm of spread. Scoping §3's
  "+2.2 cm, the transient is the bottleneck" was measured at the *existing*
  posterior, where GIS competes with AIS/GSIC/TE against the total. Most of the
  spread deficit is a **joint-calibration outcome, not a structural defect of
  SIMPLE**. The case for A rests on the hindcast (8.7× lower RMSE), which the
  refit does not touch — not on the spread.
- **A+B passes everything**: three historical gates, the Mouginot partition
  (0.74 vs observed 0.735), spread 6.30 inside the band. A alone overshoots at
  10.85. A+B′ fits marginally better but gets the partition badly wrong (0.36),
  so the SLR history alone does not separate the channels — the partition does.
  A+B's 6.30 sits *on* the band floor; do not over-read it.
- **Separability, pre-registered, answered: no ridge.** In A+B the Δ<2.3 region
  spans 57% of the local f axis and 100% of log10 β_f at corr −0.03 — weakly but
  *independently* constrained. β_f being unconstrained is the physical result
  that once the fast channel is fast relative to a century its speed stops
  mattering; f is pinned by Mouginot. No need for the Antarctic runoff-line
  treatment.

### Step 4 — the Mimi port (`julia/greenland_ab_component.jl`)
- `greenland_ab` implements cell A+B in the Greenland slot. Option C is
  deliberately absent. Driver parameter is `greenland_surface_temperature`, not
  `global_surface_temperature`, so Mimi does not auto-connect raw GMST — the
  same frame contract the glacier blocks use. V/V₀ damping dropped.
- Two things confirmed against the stock component's source: it integrates with
  **lagged** `eq_volume`/`τ_inv` (t−1), and it **starts at V(1850) = v₀** — zero
  realised loss with the full disequilibrium present. Check [5] of the
  validation exists solely to stop the latter regressing.
- **`julia/validate_greenland_ab.jl`, 1850–2300, ssp245, tol 1e-9 — ALL PASS:**
  driver 0.0; `gis_eq` 1.1e-16; fast/slow/sea_level 1.1e-15 / 8.3e-17 / 1.1e-15;
  slot contract 0.0; `global_sea_level` == 5 components 0.0 (this is what
  confirms the new slot is actually read, not a stale stock component);
  initial-condition and constant-driver monotonicity checks pass.
- Units: cell is cm, components are m; conversion happens once in
  `python/emit_gis_port_reference.py`, which writes **both** systems so a slip
  shows as a factor of 100 rather than silently.
- `run_brickf_tests.sh` now runs **four** suites; all green including the three
  pre-existing ones.

### Tried and rejected
- **Option C in pass 1.** Both ladder cells break the hindcast (RMSE 1.675 /
  1.009 against 0.099) and fail G3, and A+B+C projects 72 cm of Greenland by
  2100 under SSP5-8.5, far outside AR6's ~9–18 cm — a specification failure, not
  a finding. Cause is structural: a proportional relaxation cannot serve both a
  6 cm historical loss against a 71 cm commitment and a 742 cm post-threshold
  commitment. Past the threshold, loss is limited by ice **throughput**, not by
  the size of the disequilibrium — scoping §10 option D. **C needs a
  rate-limited formulation first.** Scoping §13 had upgraded C and D to active
  for pass 1; this reverts that, and the original §10 call to defer was right.
- Fitting the Bochow-2026 cubic emulator (retracted 2026-08-10 — transcribed
  coefficients give no fold). Superseded: the ladders are raw model output, so
  V_eq is fitted to them directly and the emulator is off the critical path.
- Absolute-weighted least squares on the ladder (see above).
- The saturating glacier-reservoir form V₀ − a(1 − e^(−b(T−T_off))) proposed in
  scoping §10 as the option-C candidate: it cannot express the low tail and the
  collapse at once, and puts T_off at 2.11 with **zero** loss below it.

### Unverified, flagged
- Committed loss at present GMT 1.25 = 0.53 m, larger than a *recollection* of
  Box et al. 2022's near-term disequilibrium commitment (~0.27 m). Consistent in
  direction (that is a current-geometry number, this is the multi-millennial
  equilibrium) but **not checked against the source** — do so before it goes in
  a memo.

## [unreleased] — 2026-08-10 — BRICK-F* delivered: projection kernel, projections + hindcast, three comparison arms, data/test cleanup, sharing memo

The extC posterior was accepted on the deliverable on 2026-08-10 (commit 205ccbf;
4x2M chains, acceptance 0.236-0.237, SLR@2100 R-hat 1.000 / @2150 1.002). This
entry covers everything built on top of it.

- **`julia/brickf_projection.jl` — one tested projection kernel.** Posterior
  loading, the per-block driver splice, the 52-parameter apply, rebaselining and
  component extraction, replacing the block every extC-era driver would otherwise
  copy (and that had already drifted to 2-tau names in the 43 legacy sites).
  nu fixed at `nu_anch_obsfit` (the calibrator's sampled-mode FIT_BASIS); F_unch
  documented as a hindcast construct, excluded from projections by default.
  `julia/test_brickf_projection.jl`: drivers and melt series match the python
  offline reference at <=1.2e-12 on both amp bases, slot contract exact,
  deterministic re-run, F_unch flat after 2005 (projection sliver 0.08 mm at
  u=25 mm), and 126<245<585 monotonicity in every component.
- **Projections (`julia/project_ssps_components_brickf.jl`)** -> 
  `outputs/ssps_components_2300_extC.csv`. SSP2-4.5 total @2100 49.5 [41.5, 97.1],
  @2150 112.1, @2300 288.5 cm (chains gave 49.6 / 111.0 — kernel and chains agree);
  SSP1-2.6 35.9, SSP5-8.5 97.8 @2100. **The glacier scenario spread is no longer
  saturated**: glaciers @2100 8.5 / 10.6 / 14.7 cm across the three SSPs, against
  6.4 / 6.8 / 7.2 under the single-reservoir extA108 predecessor.
- **Hindcast (`julia/posterior_predictive_brickf.jl`)** -> 
  `outputs/postpred_extC_{components_timeseries,bias,coverage}.csv`. Reports BOTH
  the parameter band and the predictive band that adds the calibrated AR(1) +
  per-year obs error (exactly hetero_logl_ar1's Sigma). Mean bias ais -0.00,
  glaciers -0.00, gis -0.40, te +0.24, total +0.03 cm; predictive 90% coverage
  99.2 / 100 / 68.3 / 100 / 100 %. The GIS shortfall is one contiguous window,
  1942-1982, model 0.5-0.7 cm low — stock BRICK Greenland, untouched here.
- **Comparison arms.** `python/extract_magicc_components.py` pulls the MAGICC
  v7.5.3 + Nauels-2025 600-member component bands into the tracked
  `data/comparison/magicc_nauels_components.csv` (7 MAGICC modules -> BRICK's 5,
  summed per member before quantiles), so the comparison no longer needs the
  members-only MAGICC tree. `python/brickf_model_comparison.py` puts BRICK-F*,
  MAGICC-SLR, every FACTS module and pre-Mengel BRICK 2.0 on one basis.
  **Glaciers @2100: BRICK-F* 8.5/10.6/14.7 vs MAGICC 10.4/12.5/15.3, FACTS
  8.9-9.2 / 11.4-12.2 / 15.5-17.7, BRICK 2.0 (Wigley-Raper) 12.0/13.5/16.5** —
  BRICK-F* is inside the multi-model range at every scenario, the old ~2x
  MAGICC-vs-emulator glacier gap is closed, and Wigley-Raper's low-scenario
  over-melt (12.0 cm at SSP1-2.6, the highest of the five) is gone. Totals
  @2100 SSP2-4.5: 49.5 vs MAGICC 53.2 vs FACTS 48.7-67.9; SSP5-8.5 97.8 vs 97.8.
  Flagged, not fixed: **BRICK-F* Greenland under-responds to scenario**, +2.2 cm
  SSP1-2.6->5-8.5 against +6.3 to +7.3 everywhere else.
- **Committed-ladder review item RESOLVED, and the 2026-08-09 handoff's
  explanation was WRONG.** That note attributed the 37.5% aggregate ladder-gate
  pass to the model-basis denominator and expected the data basis to be satisfied
  by construction. `python/brickf_committed_ladder.py` shows the observed 2020
  stock (76.7 mm) is slightly LARGER than the model's (74.8 mm), so both bases
  agree: +1.2 K committed 56.3% (data) / 56.6% (model) vs GlacierMIP3
  37.4 [11.8, 54.0]. The real cause is aggregation — every reservoir is within
  1.2 sigma of its own rungs (R19 z +1.17/+0.97/+0.75/+0.80, SLOWP
  +0.50/+0.42/+0.17/-0.10, FAST +0.68/+0.65/+0.31/+0.14), and three modestly-high
  reservoirs against a tighter aggregate band put the aggregate ~2 points out at
  the lowest rung only.
- **Data-assembly cleanup: `python/brickf_data.py`** replaces the 4-deep
  exec-prefix chain (build_extc_inputs -> d1f -> d1e -> d1d -> d0, ~1650 lines of
  source-splitting exec) with an importable module — every input file named and
  sourced, one section per stage, no exec. The GlacierMIP3 ladder is read from
  the committed cache, so the production path no longer needs xarray or moepy.
  `python/test_brickf_data.py` (15 checks) proves the rebuilt artifacts are
  IDENTICAL to the committed ones — that is what licenses the refactor, since the
  accepted posterior was calibrated against those bytes — plus inventory,
  response-time, ladder, seam and driver-frame checks. Re-running the module to
  disk leaves git diff empty and validate_glaciers_nu3.jl still passes at 5e-13.
  build_extc_inputs.py keeps a SUPERSEDED pointer and stays runnable.
  **Tried and kept deliberately:** the fitted constants depend on `four_rung_fit`
  call ORDER through a shared RNG, so `build_artifacts()` reproduces the
  development sequence including two discarded fits. Per-block seeding would be
  cleaner but would change the calibrator inputs and invalidate the accepted
  posterior — recorded in the module header as the fix for the next recalibration.
  **Caught by a failing test, not by inspection:** the seam-adjustment test was
  first written asserting monotone removal and FAILED — GlaMBIE region 19 gains
  mass in 2019, so the running removal genuinely dips. The assertion was wrong,
  not the code.
- **`run_brickf_tests.sh`** runs all three suites in dependency order. The
  calibrator port validation and the projection-kernel test exercise the same
  glacier physics through the two independent code paths that must agree.
- **Figures + memo.** `python/plot_brickf_memo_figures.py` -> three figures
  (hindcast, SSP totals, glacier focus incl. the 2300 saturation contrast against
  Wigley-Raper). `python/brickf_posterior_summary.py` -> the parameter table.
  `notes/memo_2026-08-10_brickf_sharing.md` is the sharing memo to Marcus's
  binding spec (abstract / obs comparison / SSP vs FACTS+MAGICC / methodology
  for reimplementation), declarative, with six stated limitations.

## [unreleased] — 2026-08-09 (latest) — extC green-lit: D1f obs-amp arm + full 3-reservoir calibrator surgery (validated 5e-13, smoke-passed); launch gated on amp-basis call

- **Marcus green-lit extC + the obs-amp sensitivity arm**, and set the sharing-memo
  spec (abstract w/ data+structure choices; obs comparison; SSP vs FACTS+MAGICC;
  methodology for Tony; declarative style; only legacy comparison = pre-Mengel
  BRICK 2.0 — memory `feedback_brickf_sharing_memo_spec`).
- **D1f obs-amp arm (`python/d1f_obsamp_arm.py`) — MATERIAL per its pre-registered
  rule:** obs through-origin amps R19 0.61 / SLOWP 2.48 / FAST 1.40 vs regchar
  1.03/1.70/1.23; ANCH modern-rate bias flips sign (+26% → −11%), deficit ±1.7;
  **MID (the extC design) deficit-invariant** (6.79→6.79) with projections moving
  toward AR6 (ds245 10.2→11.3, spread 6.5→7.9). Amp basis = Marcus call; a
  cross-dataset amp check (Berkeley Earth / GISTEMP vs HadCRUT5) was requested
  and is running (`python/diag_amp_dataset_comparison.py`).
- **extC surgery COMPLETE (commit 6771ed5):** `glaciers_nu3` component (per-block
  lagged drivers; slot-contract `gsic_sea_level` = R19+SLOWP+FAST; `gsic_hind`
  for the seam scope) + `build_brick_nu3`/`update_brick_nu3!`/`set_glacier_forcing3!`;
  calibrator now 39 physical + 10 AR(1) = 49 params — per-block (a, b, T_off,
  log10κ) with Farinotti a-priors, bounds-only b/T_off (the per-block rung
  likelihood constrains them; corr 0.6, band σ, data-basis committed %),
  τ50-as-priors on log10κ (σ 0.114 ≈ ±30%), ν FIXED at anchored (MID design);
  likelihood-only params gic_u_unch (F_unch, flat[14.5,41.8] + taper in flow AND
  total channels, never in the Mimi graph), gic_delta (N(0,0.3), obs-side ramp
  1900–1959), gic_u_pre + gic_s_r5 (the Option-D ledger, replacing the pre-D A2b);
  A2 on sum(a_b) − S_all(2000); per-block GlaMBIE rate terms (SLOWP/FAST);
  obs_adj gsic target (r19 seam); OLD38_NAMES covariance branch (extB3c
  preferred); positional-KAPPA_IDX trap removed; `--amp-basis=regchar|obsfit`.
- **Machine-generated calibrator inputs** (`python/build_extc_inputs.py`, full
  precision): `t_glac_blocks.csv`, `extc_block_constants.csv` (both amp bases),
  `recalib_targets_ext_gsicadj.csv`. **Port validation** (`julia/
  validate_glaciers_nu3.jl` — includes the calibrator itself): drivers + series
  ≤5e-13 vs python on BOTH bases, slot contract exact, logposterior(θ0) finite.
  Smoke 50-iter: accept 0.34, all 16 glacier/ledger params moving plausibly.
  Two precision lessons: 6-decimal artifact CSVs broke 1e-9 validation (drivers
  are multi-region averages; amp truncation leaks through the splice tail) —
  all artifacts now %.12f/%.12g.
- **Two-stage launch still mandatory** (overdispersed_starts.csv predates extC):
  tuning (common start) → rebuild starts+cov → production. Pending: amp-basis
  call → tuning launch; eval_chain_gates.py rewrite + diag_slr_convergence
  repoint before --accept-slr.

## [unreleased] — 2026-08-09 — Marcus ruled Option D; P&M 2018 read from primary; D1e ledger cell built + launched

- **Marcus's S(1900) ruling: Option D** — the model-side ledger ("make the best
  defensible historical data target with appropriate set-asides… then work on getting
  the model to fit that data target"), framed by his two-issue decomposition:
  (a) dataset/model scope matching (pre-2000-melted glaciers held separately),
  (b) model design for remaining-history + present + scenario responsiveness.
  The S(1900) question is ~entirely (a); its only (b) content is keeping a pre-1900
  regularizer in extC.
- **P&M 2018 now on disk and read in full** (`ClaudeDocs/Papers/`, 9 pp): seven new
  primary receipts in `notes/memo_2026-08-09_d_ledger_target_spec.md` §1, most
  notably the derivable 1901 uncharted stock (18.8–50.4 mm SLE), the CRU origin of
  the 1901 start, r19-removal RAISING the uncharted estimate (49.1+6.3), and the
  global-only upscaling (Frederikse's 13%-r5 regionalization is their own invention
  vs P&M's 43.1% r5 small-glacier area share — target-content caveat).
- **D1e cell** (`python/d1e_dside_ledger.py`, commit 0646571): datum untouched at
  N(20,9); set-asides U_pre ~ flat[0,25] mm (0-edge = charted-scope reading) +
  S_r5 ~ N(2.5,2.0)[0,8] mm on the model side; g_lec |z|≤2 replaces g_s1900
  (legacy box still reported); matched-freedom patho; era-rate + per-reservoir-rate
  emitters (the T2 cheap item); evaluation-based sanity (d1d θ identity);
  pre-registered P1 (ANCH deficit unchanged 8.21±0.05), P2 (ledger interior,
  ANCH/MID 4/4), P3 (FREE decouples from the Leclercq pull), MID/sx2 5.07-vs-5
  watch item. Julia A2b carries the D-ledger spec + TODO(extC surgery)
  (change-together trap).
- **D1e EXECUTED (`notes/note_2026-08-09_d1e_dside_ledger_verdict.md`): P1/P2
  CONFIRMED, P3 FALSIFIED, 0/6 feasible (expected).** Sanity 4/4 (structures
  reproduce d1d to 5e-6; θ evaluation identity). ANCH deficit 8.22 (unchanged);
  every ANCH/MID row now **4/4 gates** with the ledger interior: 8.1 + 2.5 (S_r5,
  prior mean) + 9.4–10.5 (U_pre, mid-range of the P&M construction) = 20.0, z ≈ 0.
  Minimal bar misses only on δ = 1.005σ vs the ≤1.0 edge (third decimal). MID/sx2
  watch: 5.32, no feasibility flip (old ll_lec's κ-pull was mildly flow-aligned;
  MID re-priced honestly +0.2–0.3). **P3 falsified informatively: FREE keeps legacy
  S(1900) 26.3–27.1 with U_pre railed at 0 — the d1d FREE ~27–28 mm was
  flow-preference, not Leclercq pull** (revises the T1/D1d inference; the flow data
  independently want ~26 mm of pre-1901 melt). New emitters: per-reservoir modern
  rates (ANCH overshoot in BOTH blocks: SLOWP +37%/FAST +25%; MID puts SLOWP dead
  on GlaMBIE) + era rates (residuals small, mixed-sign). U_pre caveat stated: no
  independent constraint — interior-not-railed is literature-consistency, not
  data corroboration.

- **`notes/memo_2026-08-09_t1_s1900_box_scope.md` (T1):** the 20±9 mm Leclercq datum
  traced to the 2026-08-06 receipts family {10, 18.5, 21.8, 28.0} — the box floor (10)
  IS the lowest family member, zero margin; Leclercq 2011 primary-verified (Springer
  full text): 349 surviving-glacier length records calibrated onto 1951–2009 charted
  mass balance → two defensible scope readings (total-scope vs effectively-charted),
  so the uncharted correction to the datum is honestly 0–23 mm (reading-(i) central
  ≈9); r19/r5 corrections offset (+1–2 / −2–3 mm). Options A (keep+label) /
  B (re-derived box) / C (likelihood-only, recommended, e.g. N(15,10)) for Marcus.
  Sensitivity: any defensible re-derivation → all ANCH/MID rows 4/4 gates; deficits
  and 0/12 feasibility untouched (ANCH S(1900) is an analytic constant of the fit —
  bit-identical 8.12281 across variants); closest feasibility candidate
  C_both/MID/unc_sx2 at deficit 5.07 vs tol 5 flagged. Python + Julia constants must
  change together.
- **`notes/memo_2026-08-09_t2_structural_assessment.md` (T2):** century budget
  1900→2020 decomposed (blocks 38.4 / U 29.6 / δ 18.1 / resid 0.5 mm — 56%
  non-dynamical, both terms literature-anchored); era table with scope-corrected obs;
  parameter census (19 nominal; 4 hindcast-fitted, none dynamics; **a_b prior-pinned
  to 5 dp — the rungs determine 6 params, not 9** — new finding); comparator ledger
  (Wong WR-GSIC fails ≥3/4 itemized, NOT script-produced "0/4"; Nauels-ν 0/4;
  reassign catastrophic); 11-convention ledger — complexity lives in conventions,
  not parameters; minimality table (every remaining piece costs likelihood or scope
  honesty); recommendation separated: green-light extC after the T1 call + two cheap
  pre-extC items (obs-amp arm; era-rate emitter).
- **Record corrections (do not propagate):** (1) "adj-obs ~0.81" modern rate is the
  UNADJUSTED 2015–23 number; the like-for-like r19-adjusted comparator is **0.766**
  → ANCH overshoot 1.26× (not ~1.19×), MID 1.10×; (2) the arc handoff's SSP quote
  "7.7/9.8/14.1" is the A_4rung ablation row — headline C_both/ANCH is
  **9.06/11.23/15.78** vs AR6 9/12/18, and MID is slightly LOW at all three (not "on
  them"); (3) D1d gate status is 3/4, not 4/4 (the 4/4 claims belong to D1/D1c).
- Papers checked: Leclercq 2011 and P&M 2018 are NOT in ClaudeDocs/Papers (fetched
  key facts from publisher pages instead); Frederikse 2020 EDF Fig. 6a (on disk)
  gives the P&M time profile — near-constant to ~1980, exhausted by ~2000 —
  corroborating the taper.

## [unreleased] — 2026-08-09 — D1d (4-rung fits + r19 seam): bars NOT met but the offline program has CONVERGED — every datum within ~1.3σ

- **`python/d1d_fourrung_seam.py`** (Marcus green-lit options 1+4): 4-rung correlated-
  Gaussian S_eq fits (rung σ = band/2 floor 3, corr 0.6, soft Farinotti a-priors
  0.221±0.057 / r19 0.069±0.018) + r19 as third reservoir excluded from the hindcast
  (obs_adj removes GlaMBIE r19 post-2018; net 0.38 mm) + Farinotti-SLE r19 basis
  (resolves the Gt-vs-SLE BSL sub-decision). Sanity 3/3 after fixing an over-strict
  monotonicity assertion (r19 has positive-balance years). **All rung |z| ≤ 0.2 —
  no overconstraint** (the explicit Marcus requirement, verified).
- **Bars NOT met (0/12):** deficits improved to 7.3–8.2 (δ ≤ 1σ, U ≈ Frederikse
  central) but S(1900) drops to 8.1–9.8 mm — below the 10–30 box — because the
  (physically right) BSL r19 stock reduction removes ~1.4 mm of early melt; ANCH
  modern rate overshoots (0.97) in the seam variants, MID resolves it (0.84–0.85).
  λ-bridge diagnostic considered and NOT run (both frame endpoints share the S1900
  miss — stillborn).
- **Conclusion (`notes/note_2026-08-09_d1d_fourrung_seam_verdict.md`): the offline
  point-optimization program has converged** — FREE arms fit the adjusted century at
  noise level; every underlying constraint is met within ~1.3σ (S1900 z −1.2 vs
  Leclercq, in the direction the inventory-vs-total scope argument predicts); the
  remaining "failures" are pre-registered box edges. Assets for extC assembled
  (structure, rung covariances, priors, obs_adj, T_off bounds). Whether to re-derive
  the S(1900) box for inventory scope is a Marcus call.

## [unreleased] — 2026-08-08 (night) — D1c uncharted-ice cell EXECUTED: pre-registered prediction NOT confirmed (best 8.4 vs tol 5) but U fits at the Frederikse central and the gap is now fully literature-priced

- **`python/d1c_uncharted_cell.py`** (Marcus green-light): ANCH 2-block + exogenous
  F_unch(t) with U flat-prior on the scope-scaled P&M bounds [14.5, 41.8] mm; BOOK1
  (uncharted subtraction from the melt-to-date partition) + BOOK2 (r19-zero historical
  split); ablation arms repro/book/unc_sx2/unc_t5d × ANCH/MID/FREE + profile
  sensitivities (const/frontload/taper); pathological comparators re-fit per variant
  with matched U/δ freedom. Sanity 3/3; ANCH/repro ≡ D1 (|diff|=0.00); sx2 patho 52.82.
- **Verdict (`notes/handoff_2026-08-08_d1c_uncharted_verdict.md`): 0/14 feasible — the
  pre-registered prediction (feasible with δ≤1σ) FAILED** (const: 9.0 deficit, δ 1.2σ;
  taper: 8.4, δ 0.9σ). But: U FITS at 27.6–32.5 mm scope ≈ the Frederikse-expected
  central (31.7–32.5 global vs 32.35), not railed; early-century era logLs reach the
  noise floor; FREE/unc_sx2 deficit 0.55 (free dynamics + U fit the century at noise
  level — only the ν-spread coupling survives anywhere); profile ranking taper < const
  << frontload (frontload falsified; const's 1990 hard stop = step artifact ~0.6 logL).
  Residual ~8 logL localized to 1980–2023 with three priced candidates: bookfix→
  two-rung interpolation sensitivity (book-only ablation +2.5; modern rate 0.855→0.764),
  the Frederikse/GlaMBIE r19 modern-target seam, and late-century ν-shape.
- Abandoned within the cell: the frontload profile; and the notion that the 1990 profile
  step materially carried the deficit (taper bought only 0.6).
- Decision menu: D1d modern-seam cleanup vs accept-with-label (offline program complete)
  vs extC surgery directly (needs widened per-block T_off bounds). Marcus to rule.

## [unreleased] — 2026-08-08 (evening) — geometry-drift literature verdict: transient-physics version PARKED; verified scope mismatch (uncharted ice IS in the target, NOT in the model stock) covers most of the century-integral gap

- **`notes/memo_2026-08-08_geometry_drift_literature.md`** (all citations verified against
  primary sources). Mechanism A (state-dependent response times): qualitative support
  (JRW 1989; Christian 2018; Zekollari 2020 slope control; GlacierMIP3 2025 state
  dependence) but direction ambiguous for LIA-extended geometries and NO global
  quantification → no defensible prior; PARKED. Mechanism B (inventory-scope drift):
  Parkes & Marzeion 2018 — uncharted (missing + disappeared) glaciers contributed
  16.7–48.0 mm SLE 1901–2015 (0.17–0.53 mm/yr), explicitly absent from inventory-based
  models; **Frederikse 2020 (Parkes co-author) includes it in its glacier component**
  (confirmed via Gangadharan et al. ESD) → our GSIC target contains 17–48 mm of melt the
  model's V=0.290 present-RGI stock structurally cannot produce. Explains D1b's
  topology-invariance. Covers ~25–75% of t5d's fitted δ=0.69 mm/yr; residual within
  ~0.5–1.7σ of the ORIGINAL Roe prior. Roe 2021 initialization critique verified with
  specifics (mass-turnover τ, t* extrapolation, NAT-deficit implausibility) — T5d prior
  now literature-armed either way. NB GlacierMIP3 paper headline response times are 80%
  metrics; our pipeline uses regchar −50% columns (no bug).
- **Proposed (awaiting Marcus): D1c cell** — ANCH unchanged + exogenous uncharted-ice
  term F_unch(t) with the P&M prior (taper by 2000; r5-scope partition flagged) +
  optional T5d δ at the original prior. Prediction: deficit inside tol with δ ≤ ~1σ.

## [unreleased] — 2026-08-08 (later) — Marcus rulings after D1/D1b: T5c REJECTED; T5d acceptable; geometry-drift to be investigated for a literature basis

- **T5c (hindcast/projection hybrid) is OFF the menu** (Marcus: "I don't like T5c").
  **T5d (structured early-segment discrepancy) is acceptable.** **Geometry-drift**
  (state-dependent response times and/or inventory scope drift) to be scoped against the
  literature before any implementation. Literature verification launched for: JRW-1989
  response-time scaling, Roe/Christian/Marzeion attribution + initialization critique,
  Marzeion 2014 adjustment fraction, Zekollari 2020 Alps imbalance, GlacierMIP3 τ50
  definition, Leclercq 2011 independence, Parkes & Marzeion 2018 uncharted/vanished-ice
  contribution (candidate exogenous early-melt source absent from present-RGI models).

## [unreleased] — 2026-08-08 — D1b: splitting/reassigning the SLOW block does not recover the century integral; the cap is topology-invariant

- **Marcus: the D1 SLOW block (inert until ~1990, yet assigned ~33 mm of history) should
  maybe be split, or partly reassigned to FAST.** `python/d1b_slow_split.py` tests both
  against the unchanged D1 criteria (sanity 2/2; both pathological refs reproduce D1
  exactly). **Per-member two-rung diagnostic:** heterogeneity is real but does NOT map
  onto τ50 — r09/r07 carry their high commitment via STEEP b (threshold-like S_eq, ~96%
  loss by +2K) with T_off +1.6/+1.1, while the actual historical melters r03/r06
  (T_off −0.69/−0.93) have τ50 too slow to matter. **3BLOCK** (POLAR {19,03} / SUBPOLAR
  {09,07,06} / FAST) ≈ identical to D1 (ANCH deficit 20.6/12.0 vs 20.7/11.5; 4/4 gates;
  S2020 59 mm). **REASSIGN** (τ*≈500) much worse (1/4 gates, deficit 17.3–67.8): the
  merged FASTX composite T_off rises to −0.08, killing early excess and overshooting
  modern — the one-pool shape failure resurrected inside FASTX. 0/12 feasible.
- **Conclusion (`notes/note_2026-08-08_d1b_slow_split_verdict.md`):** the missing
  ~45–50 mm of pre-2000 melt is invariant to block topology — capped by GlacierMIP3
  response times + committed ladders + the exponential S_eq form. Reassignment is off
  the menu; the §6 decision menu (T5c / T5d-extended / geometry-drift κ(t) as new scope)
  stands. Abandoned: the hypothesis that τ-based splitting recovers equilibrium-proximity
  coherence (the two axes are independent in the data).

## [unreleased] — 2026-08-07 (late night 2) — D1 multi-reservoir cell EXECUTED: pre-registered FAIL (0/10) but first-ever 4/4-gate pass; tension isolated to the pre-2000 century integral

- **`python/d1_multireservoir_cell.py` built and run** (D0-exec pattern; sanity battery 3/3
  — blocks-sum identity 2.8e-17, ν=0 Mengel nesting exact, reproducibility; the sx2
  pathological reference reproduces T1's 52.82 exactly). Block anchors all data-derived:
  drivers = GlaMBIE-area-weighted per-region HadCRUT5; amp_b = regchar ISIMIP3 ratios
  (FLAGGED low: aggregate 1.34 vs amp_g 1.8 / obs-fit 1.59); (b_b, T_off_b) closed-form from
  the block's own two-rung EXACT GlacierMIP3 composite (moepy, cached:
  `outputs/d1_gmip3_steady_cache.nc` 71 KB + `d1_block_ladder_cache.csv`); (κ_b, ν_b) solved
  exactly from the block τ50 pairs (SLOW 665/159 → ν=1.35; FAST 130/37 → ν=1.60).
- **Verdict (`notes/handoff_2026-08-07_d1_multireservoir_verdict.md`): 0/10 pre-registered
  configs feasible** — ANCH passes ALL 4 gates out-of-sample in every variant (first
  structure ever; spread 6.5–6.9 cm in-band, modern rate 0.85 vs obs 0.81) but misses the
  1980–2023 flow criterion by 11.5–22.6 logL (tol 5). Anatomy: model S(2020)=57 mm vs target
  107 mm — the SLOW two-rung solve yields T_off=+0.465 glacier-K (preindustrial equilibrium,
  late-onset melt), so GlacierMIP3-consistent physics cannot produce the pre-2000 flow.
  POST-HOC MID arm (κ free, ν held at anchored): deficit unchanged, fitted κ ≈ anchored —
  the κ anchors are innocent; ν≥1.35 (the spread dial) carries the deficit. FREE rails ν→0
  (spread dies) but with NO P2 collapse (κ ratio 4.1). T5d absorbs half the deficit at
  δ=+0.69 mm/yr = 2.3σ of the Roe prior. Driver-swap control: per-block drivers ≈ 0 logL on
  aggregate flow. τ* and hist-split scans verdict-invariant. New sub-decision H (1850–2000
  melt split; Hugonnet default, scanned) flagged, not resolved.
- **Abandoned within this cell:** treating the FREE arm's shared-ν prior N(1.0,0.5) as able
  to hold ν up against the hindcast (it rails to 0 exactly as in D0/extB3 — reconfirmed);
  and the hypothesis that per-block DRIVERS carry the historical flow shape (the control
  killed it — the payoff is per-block S_eq frames + anchored transients).
- Structural decision (T5c vs T5b+T5d vs T5d-extended vs accept-with-label) awaits Marcus;
  no extC calibrator surgery until then.

## [unreleased] — 2026-08-07 (late night) — T5a multi-reservoir regional blocks = LEAD candidate; D1 offline cell specced

- **Marcus: multiple glacial reservoirs (T5a) is the lead candidate.** Handoff
  `notes/handoff_2026-08-07_t5a_multireservoir_lead.md` specs the D1 offline feasibility cell
  (no Julia surgery): 2 blocks by GlacierMIP3 response time (τ*=250 yr; SLOW = r19/r03/r09/r07/
  r06 ≈ 72% of stock, 71% of committed, 36% of modern melt, τ50 ~665→159 yr @1.5→3 °C; FAST =
  the rest incl Alaska), per-block drivers from `t_glac_regions_hadcrut5.csv` (area-weighted,
  per-block amp from GlacierMIP3 regional ratios), per-block (b,T_off) from the block's OWN
  two-rung ladder composite (exact per-experiment estimator, nc on disk), and an ANCHORED
  transient arm with (κ_b, ν_b) set by the block's two response times — making the hindcast an
  out-of-sample test — plus a free arm. Criteria = the T1 standard (4/4 adopted-anchor gates +
  1980–2023 flow within 5 logL of pathological) + per-block modern-split reports + the D0-style
  driver-swap control. T5d (early-segment discrepancy term) carried as a switch; failure mode
  pre-registered (P2-signature collapse → T5c/T5b+T5d discussion). Sub-decisions A–G flagged
  (block count/threshold, driver weighting, ν sharing, inventory partition basis incl the
  Gt-vs-Farinotti-SLE 0.343-vs-0.290 BSL note, optional Zemp-2019 fetch, σ×2-vs-discrepancy,
  ladder estimator). Calibrator-surgery scope sketched for planning only (extC tag family).

## [unreleased] — 2026-08-07 (night) — scope-corrected anchors ADOPTED in the gate machinery; T4 rejected; constraint-anatomy memo scopes T5

- **Anchors adopted (Marcus): `d0_glacier_shootout.py` gate constants swapped to the
  scope-corrected ladder** (37.4/46.3/63.0/75.5 central; [11.8,54.0]/[17.2,63.2]/[41.5,75.5]/
  [58.5,83.9] likely; sens 95 mm) with a provenance comment preserving the superseded published
  values; `d0_final` SC solve now derives COM12 from the same constant; eval/T1 inherit by exec;
  eval self-test still passes 4/4 on the C_nu1.0 point.
- **T4 REJECTED (Marcus) — new-structure scoping requested.** `python/diag_constraint_anatomy.py`
  + `notes/memo_2026-08-07_glacier_constraint_anatomy.md`: constraint inventory with per-item
  confidence; the one-reservoir arithmetic (rate = κ(a−S)(1−e^{−b·exc})exc^ν — gap and excess
  both functions of ONE state) showing the law demands 1.92× acceleration (2000-23/1920-49)
  where the target shows 0.76× (deceleration); branch A (fit-history) overshoots the
  best-measured modern rate 1.67× (1.36 vs target-derived 0.81 mm/yr, 2015-23) while
  under-melting the century (S2020 86 vs 107 mm); branch B (fit-modern-rate) misses total melt
  2.3×. **Corner scan: the ladder band floor (11.8%) is UNREACHABLE (the flow data's own slope
  forces more committed melt) and the overshoot is anchor-insensitive (1.36–1.51 mm/yr at
  com12 20–37.4%) — the tension is the SHAPE mismatch (monotone excess path vs non-monotone
  century flow), not the anchor level.** NB the target's own 2015–23 rate is 0.81 mm/yr, not
  the handoff's ~0.6 (GlaMBIE-2020 scope figure): overshoot ratios restated on the target basis.
  Per-region anatomy (S1a/S3/regchar/Hugonnet): stock-weighted response time 513 yr vs
  melt-weighted 285 yr, collapsing to 125 yr at ~3 °C (GlacierMIP3's own spread mechanism);
  regional warming spans 0.14–2.82 K — the single area-weighted driver mutes the ETCW that the
  early flow needs. Scoping menu: **T5a regional blocks (lead; per-region drivers/anchors/
  response times all on disk), T5b κ(T) single reservoir (only with T5d), T5c hindcast/projection
  hybrid (fallback), T5d early-segment discrepancy model (replaces σ×2)** — awaiting Marcus's
  §5 asks.

## [unreleased] — 2026-08-07 (evening 2) — T2 executed: GlacierMIP3 anchor scope-corrected (39→37.4 @1.2K), tension NOT dissolved; T1 offline test built

- **T2 (ladder-anchor scope correction) DONE — the anchor moves −1.7 pts at the +1.2K rung and
  the modern-flow overshoot only improves 2.00×→1.85×; the structural tension stands.** Data:
  GlacierMIP3 archive (Zenodo 10.5281/zenodo.15046588 v2; Zekollari 2025 Science adu4675) —
  small files tracked under `data/observations/raw/gmip3/`, the 1.47 GB per-experiment shifted
  netCDF untracked with a range-request re-fetch recipe (`python/scripts/remote_zip_extract.py`
  pulled 358 MB of ranged reads instead of the 984 MB zip).
- **Method (python/t2_gmip3_scope_anchor.py): replicate the paper's own 'All' estimators, then
  delta-transfer.** Reverse-engineered from GlacierMIP/GlacierMIP3: the published global CENTRAL
  = LOWESS median over 80 constant-climate experiments of the per-region model-MEDIAN composite;
  the published global BOUNDS were REPLACED downstream (0d aggregation notebook) and are ≈ the
  per-member composite over the 4 globally-covering models (PyGEM-OGGM_v13, GloGEMflow, OGGM_v16,
  GLIMB — their own cell-9 equivalence, confirmed on the only_global file). Replicated both
  estimators with moepy + the paper's frac auto-selection (selected 0.22–0.23 vs paper 0.23);
  **validation on full-RGI reproduces the published ladder: central max err 1.6, bounds max err
  2.1 pct-pts (PASS ≤3)**. A naive mass-weighted composite of per-region marginal quantiles
  over-disperses bounds by up to 11.5 pts (the authors' own "conservative regional sum" caveat) —
  kept in the CSV as a labeled cross-check arm only.
- **Final excl-r5-incl-r19 anchors (published + replicated scope delta):
  +1.2K 37.4 [11.8, 54.0]; +1.5K 46.3 [17.2, 63.2]; +2.0K 63.0 [41.5, 75.5]; +3.0K 75.5
  [58.5, 83.9]** (r5 is high-committed — 58% @1.2K — but only 9.8% of stock; r19 stays in scope).
  Scope sens 1.5→3K ≈ 95 mm SLE raw (full-RGI raw 109 / S1b BSL-corrected 98) — the shootout's
  85 mm report-constant was low under any basis. SC point under the new anchor: b 0.282,
  T_off −0.914, committed@1850 0.087 m, demanded gap 103 mm (was 108).
- **T1 offline two-reservoir-ν test built (python/t1_two_reservoir_offline.py)** — existence
  test at the SC point: fast/slow split (Nauels-ν fast pool share φ, linear slow pool τ_s,
  GlacierMIP3-response-time prior 463 [216–805] yr) + rate-cap arm, ν SCANNED not optimized
  (free ν rails to 0 and kills spread — same D0 non-identifiability), pre-1940 σ×2 likelihood,
  ladder/spread at calibrator amp 1.8, criterion = 4/4 gates AND 1980–2023 flow logL within 5
  of the free-N pathological optimum. First pass (pub anchor) validated the machinery: N1 ν=1
  at SC = 4/4 gates at deficit 21.2 (matches diag_pathology's −17.8−5.2 whitened attribution);
  free rate-cap hits deficit 0.3 but spread 0.0 (cap binds in projections — device rejected as
  a free fit).
- **T1 FALSIFIED (both anchors): 0/110 configs feasible** (4/4 gates AND 1980–2023 flow within
  5 logL of the pathological optimum). Binding gate = SPREAD (61% of the P grid; inventory/
  ladder/S1900 essentially never fail); monotone trade-off — flow-optimal low-φ cells saturate
  at spread 2.8–3.5 vs the 4.5 floor, and 4/4-gate cells exist only at φ=0.8
  (single-reservoir-in-disguise, deficit 15.6 vs single-N 16.8: the split buys ~1 logL). The
  two-NAUELS-pool variant (P2, slow pool keeps ν — quiet-now/mobilize-later) passes gates
  everywhere but its best deficit equals single-N ν=0.5 exactly, with fitted κ_s ≈ κ_f (the
  pools collapse). Ungated family floor ≈ 10 logL > the 5 tolerance. **Committed-ice retention
  and ν-spread load onto the same response; the split relocates, not resolves, the tension.
  Per the prior handoff's fallback logic, T4 (accept ν≈0 + labeled projection-ν sensitivity
  arm) is now the live default — awaiting Marcus.** Handoff:
  `notes/handoff_2026-08-07_t2_scope_anchor_t1_two_reservoir.md`.

## [unreleased] — 2026-08-07 (evening) — extB3/b/c ALL falsified; binding tension = modern flow vs GlacierMIP3 ladder; Dangendorf v2 SE adopted

- **All three tuning arms failed 0/4 gates on the same ν≈0.1 / T_off≈−1.8 mode** (extB3 baseline;
  extB3b + pre-1940 GSIC σ×2; extB3c + corrected Dangendorf σ — the last passes inventory at the
  median and improves S1900 to 34 mm, but spread stays ≤1.6 cm and ν piles at 0).
- **Diagnosis overturned the handoff item-7 framing** (`julia/diag_pathology_terms.jl` + whitened
  per-era attribution): flow_gsic alone buys the pathology (SC ν=1 point pays −25 logL; all other
  glacier terms favor SC +5); with early σ×2 active the price is MODERN (−17.8 in 2000–2023, −5.2
  in 1980–99, only −1.5 in 1900–19). Analytic check: ladder-demanded committed gap 0.105 m × κ·exc
  → 1.1 mm/yr at 2020 vs observed ~0.6 = 1.7× overshoot. **The single-reservoir ν transient cannot
  satisfy the GlacierMIP3 committed ladder and the GlaMBIE-era observed rate simultaneously**; the
  Roe/Marzeion early-segment question is resolved (σ×2 works), the remaining tension is structural.
  Decision menu (T1 two-reservoir/rate-cap; T2 ladder-anchor scope correction; T3 rejected; T4
  accept ν≈0) in `notes/handoff_2026-08-07_extB3_falsified_modern_flow_tension.md` — awaiting Marcus.
- **Dangendorf corrected Global_v2.nc ingested** (Sönke pers.comm.): old file's GMSL/SE slots held
  barystatic; v2 validates our Fields-derived dang values BIT-EXACTLY; SE is in meters
  (SE(2021)=2.68 mm). "Frederikse-sd conservative" claim falsified (true SE 1.3–2× larger
  1900–2010) → **dang_sig switched to native v2 SE** (Marcus), targets rebuilt (only dang_sig/lo/hi
  changed), prep script asserts units.
- Chains extB3/b/c + eval CSVs retained as falsification evidence; smoke junk deleted.

## [unreleased] — 2026-08-07 — extB3 tuning falsified (wiggle-tracking mode); extB3b σ-fallback launched

- **Gate machinery (`python/eval_chain_gates.py`)**: per-draw evaluation of the pre-registered
  gates on chain draws (2nd half), reusing the D0 formulas by exec (no new math). Hindcast on the
  calibrator driver convention (obs T_glac + 1.8×GMST splice); ladder/spread at amp_g 1.8;
  calibrator-bounds interior check; full-maxlag Geyer ESS; wiggle-mode co-indicators. Self-test
  reproduces the d0_final C_nu1.0 row (hindcast metrics to CSV precision, 4/4 gates).
- **extB3 tuning run (500k, seed 2026, accept 0.237, 36 min) FAILED gates 0/4** — the chain
  camped on exactly the wiggle-tracking mode pre-registered in handoff §2 item 7, all three
  co-indicators firing: σ_gsic → 0.032 cm (ρ 0.96), gic_nu piled at 0 (median 0.12,
  P(ν<0.05)=0.24 → scenario spread dead at 1.6 cm), S(1900) median 45 mm (P(>40)=0.77) with
  T_off dragged to −1.81 (10% from its bound; deep-offset partially back, committed@1850
  ≈ 0.155 m). Inventory z median −1.19; ladder over-committed (58/66/75/87%). Chain + eval CSV
  kept as the tuning evidence (`chain_extB3_seed2026_n500000.csv`, `eval_gates_extB3_seed2026.csv`).
- **extB3b = the documented fallback**: GSIC flow σ ×2 pre-1940 (Marzeion-2015-derived target
  segment = Roe-2021 initialization artifact; precedes the HadCRUT5 ETCW ramp ~1918). Flag-gated
  (`--gsic-early-sigma-x2`) so extB3 stays exactly reproducible; smoke-tested; 500k tuning
  relaunched under `--tag=extB3b`.
- Stale-comment fix: calibrator A2 header said S_raw(2020); code has used idx(2000) since the
  2026-08-06 Farinotti-epoch fix.

## [unreleased] — 2026-08-06 — D0 shootout: T_glac driver validated; ν needs a prior; deep offset was a driver artifact

- **T_glac data prep (`python/build_t_glac.py`)**: glacier-area-weighted observed temperature,
  HadCRUT5.0.2.0 analysis × GTN-G 2023 region polygons × GlaMBIE year-2000 area weights, scope
  excl-r5-incl-r19 (matches A2 V=0.290). ETCW in-driver 2.3× global (1930-40); amp_g fit 1.56-1.63
  vs GlacierMIP3 1.8. Pre-1898 gaps (r03 largest) filled by per-region OLS on global, flagged.
  New raw inputs documented in `data/observations/raw/README_modern_extensions.md` (HadCRUT5 nc
  untracked by size; GlacReg zip tracked).
- **D0 six-cell shootout (`python/d0_glacier_shootout.py`, follow-up arms in
  `python/d0_final_selfconsistent.py`)**: {Mengel-2τ, Nauels-ν} × {Gfair, Gobs, Tglac}.
  T_glac wins the decadal flow shape by ~+10 logL; the Gobs control shows the gain is the
  regional ETCW signal, not obs interannual variability. **ν rails to 0 in every arm** — the
  hindcast cannot identify ν (Nauels 2017 Table 2 fetched: κ 0.0079-0.0131, ν 0.096-0.445, fit
  to smooth CMIP5-forced projections); ν must enter via an informative prior.
- **Deep-offset pathology dissolved**: solving glacier-frame consistency directly (slope@0/amp_g,
  inventory at observed melt level, GlacierMIP3 39% @+1.2K) gives a 0.383 / b 0.286 / T_off
  −0.96 glacier-K ≈ −0.60 global-K (inside PAGES-2k amplified LIA minima), committed@1850 only
  0.092 m — the 0.20 m demand was the GMST driver compensating for missing regional warming.
  With ν ∈ [0.5, 2] at this point **all pre-registered gates pass simultaneously** (S(1900),
  inventory, GlacierMIP3 ladder, AR6-family scenario spread) — a first. Residual: 1900-1920 flow
  segment (Roe-2021/Marzeion-init-artifact question) — data-trust decision pending.
- **Tried and superseded within the session**: naive frame-scaled crossing (a .452, b .332,
  T_off −1.77) kept committed=0.20 and failed inventory/ladder — replaced by the direct solve;
  A2b-enforced (×25) optimization walked to a shallow-offset b-ceiling solution (ladder 92-100%)
  — enforcement alone does not find the healthy region.
- **GIS diagnostic (`python/diag_gis_regional_driver.py`)**: GIS melt rate correlates +0.71 with
  Greenland-region temperature vs +0.16 with GMST; Greenland ETCW 5.5× global; Greenland cooled
  −1.8 °C/century 1940-90 while global warmed. GIS = confirmed Option-D candidate (own
  workstream). TE = OHC story, no regional-T fix; AIS already has A6.
- Decision menu for extB3: memo §5-D0 (ν prior, early-century σ, amp_g, T_glac freeze, GIS timing).
- **extB3 implementation (2026-08-07)**: `julia/glaciers_nu_component.jl` (Mengel S_eq +
  Nauels-ν single-reservoir transient, melt-only clamp, driver param renamed
  `glacier_surface_temperature` to enforce the frame contract), `build_brick_nu`/
  `update_brick_nu!`/`set_glacier_forcing!` added to `brick_mengel.jl` (old paths kept for
  provenance), `calibrate_mcmc_ext.jl` rewired (T_glac driver + 1.8×GMST splice; gic block
  (a, b, T_off, log10κ, ν) with glacier-frame priors, b re-centered 0.29; 39→38 params;
  extB2 proposal covariance name-mapped, glacier rows fresh). Port validation
  `validate_glaciers_nu.jl` + `validate_glaciers_nu_compare.py`: Julia↔Python 1e-16,
  ν=0≡Mengel nesting 4e-19, non-glacier components bit-identical across the swap
  (AIS feels the glacier via global_sea_level coupling — matched-glacier A/B). 50-iter
  smoke test PASS (accept 0.36, finite start). Tuning run (500k, --tag=extB3) NOT yet launched.


## [unreleased] — 2026-08-05 — Mengel A0 confirmed; A1-LIA falsified; component review vs FACTS/AR6

- **A0 offline profile (`python/a0_mengel_profile.py`) CONFIRMED the T_lia-floor diagnosis** on all
  three handoff predictions: (P1) the algebraic (a,b|T_lia) curve crosses inventory-consistency at
  T_lia −1.14 / a 0.486 / b 0.464 (full-RGI) — Mengel's published values; (P2) the GSIC profile
  likelihood improves monotonically past the −1.00 floor and the railing is driven by the pre-1950
  target years; (P3) freeing `gic_sl0` absorbs the committed-melt demand but degenerates (a→∞, b→0)
  without an inventory term.
- **A1 as specified (widen T_lia from an LIA reconstruction) is FALSIFIED by the reconstruction:**
  PAGES 2k global LIA = −0.03..−0.14 °C rel 1850-1900 (tail −0.45); amplified glacier-region minima
  −0.5..−0.65. **Mengel 2016 has no T_lia at all** (equilibrium ≡ 0 at preindustrial; natural melt
  subtracted from calib data via Marzeion 2014, contested by Roe 2021). The parameter must be
  reinterpreted as an effective disequilibrium offset — GlacierMIP3 (Zekollari 2025: 39% of glacier
  mass committed at PRESENT climate) supports the ≈−1.1 offset physics while killing the LIA label.
  A pure sl0 (initial-state) fix fails GlacierMIP3 outright — tried on paper, abandoned.
- **A2 scope finding (agent-verified, Hock 2023):** the Frederikse glacier target EXCLUDES peripheral
  regions 5+19 → scope-matched inventory 0.221±0.057 m SLE vs full-RGI 0.324±0.084 (the 0.32
  `gic_a` floor). Our spliced GSIC target is internally scope-mixed (GlaMBIE tail includes
  peripheries). Scope choice = open decision; only the full-RGI crossing passes GlacierMIP3.
- **B1 hindcast stats on extA108** (`python/b1_component_hindcast_stats.py`): AIS now clean (the 1900
  overshoot is resolved); GIS/GSIC undershoot 1950-1993; TE overshoots pre-1950.
- **B2 projections review**: BRICK-AM per-component 3-SSP bands to 2300
  (`julia/project_ssps_components_2300.jl`); FACTS `global.coupling.{ssp126,ssp585}.n200` runs
  (native FaIR-1.6.4 climate needed `fair==1.6.4` baked into the image — the neutered-pip fix had
  broken the climate step); comparison table + figure
  (`python/b2_component_comparison.py`, `python/plot_b2_component_comparison.py`). Headlines @2100
  vs AR6 T9.9: glaciers low + spread-collapsed (0.8 vs 9 cm across SSPs); AIS too binary (low at
  SSP1-2.6, 46 vs 12 cm at SSP5-8.5, runaway post-2100); GIS modestly low; TE/LWS in family;
  total scenario-sensitivity ~2× AR6's.
- **A5 recalibration NOT launched** — §5 decision menu (inventory scope, GlacierMIP3 role, sl0,
  offset prior) in `notes/memo_2026-08-05_mengel_a0_results_and_recalib_options.md` awaits Marcus.

## [unreleased] — 2026-08-03 — Headline metric table complete; component-split claim refuted

- **The §0 table's missing pulse-relative cells are filled** (stochastic arms; deterministic still
  running). `python/metric_horizon_table.py` forms both metrics identically — ensemble MEAN marginal
  per GWP-100-equivalent tonne, so CO₂ ≡ 1.0 and the CH₄ entry *is* the metric:

  | yr after pulse | calendar | temperature (GTP-style) | total SLR | SLR ÷ temperature |
  |---|---|---|---|---|
  | 20 | 2050 | 3.70 | 4.63 | 1.25× |
  | 70 | 2100 | 0.79 | 2.24 | 2.82× |
  | 100 | 2130 | 0.52 | 1.68 | 3.23× |
  | 120 | 2150 | 0.45 | 1.45 | 3.23× |
  | 150 | 2180 | 0.38 | 1.22 | 3.18× |
  | 270 | 2300 | 0.24 | 0.79 | 3.34× |

  At the GWP-100-matched **100-yr** horizon an SLR metric values CH₄ at **1.68×** its GWP-100 while an
  endpoint-temperature metric values it at **0.52×**. The divergence is only ~1.25× at 20 yr and
  saturates near 3.2× from 100 yr on — it *opens with horizon*, it is not a fixed offset.
  **The SLR÷temperature column is GWP-INVARIANT** (the basis cancels), so the headline does not
  depend on the open GWP-basis choice (§4.3) — that choice moves both metrics identically.
- **REGRESSION PASS:** at the four horizons the earlier 4-horizon `_subann` run also covers, the
  6-horizon `_pr` run is **bit-identical** (worst relative difference 0.00e+00), confirming the
  2026-08-02 metric-packing fix (hardcoded offset `4` → `length(HORIZONS)`) perturbs nothing.
- **Research-plan §1 contribution 1: first example REFUTED, second CONFIRMED** (CLAUDE NOTE added at
  the claim, not a rewrite — Marcus's call on wording).
  - "CH₄-TE-led vs CO₂-AIS-led split" is **not supported**: both gases are AIS-led with near-identical
    shares and the small difference runs *opposite* to the claim (AIS @2130 CO₂ 78.8% / CH₄ 79.6%;
    TE 15.8% / 14.1%).
  - "Crossover horizon shifts vs a thermosteric-only estimate" **is** supported and is the stronger
    claim: a TE-only calculation gives 0.84–0.89× the full-SLR metric and crosses parity **~57 yr
    earlier (TE-only ~2184 vs full SLR ~2241)**. Both interpolated between bracketing horizons; the
    ~57 yr *shift* is the robust quantity, the levels are ±a decade or two.
  - `te@2300` was spliced from the `_subann` runs (the `_pr` run's comp-years were 2130/2150/2180);
    legitimate because the two runs are bit-identical at shared horizons. **Future runs should put
    2300 in `--comp-years`** so no splice is needed.
- **Tried and rejected:** extrapolating the full-SLR crossover off the short 2150→2180 segment gave
  ~2208 vs ~2241 when interpolating across the bracketing 2180→2300 segment — the metric is convex in
  horizon, so short-segment linear extrapolation overshoots the decline. Interpolate between horizons
  that actually bracket parity.
- **Basis sensitivity settled for the headline (§4.2):** stochastic and `_nonoise_flatsolar` agree on
  the MEAN to within **1.4% at every horizon**, on both the SLR metric and the SLR÷temperature ratio.
  For the headline table the basis choice is **immaterial**; it remains material only for the
  tip-fraction / mode decomposition (23% vs 33%), which is a separate open question.
- **Fossil-CH₄ arm complete (stochastic).** Wide files `_ch4foss1tg{,_nonoise_flatsolar}` built; the
  zero-pulse gate on the new basis **PASSED** (every metric exactly 0.000e+00 across all 6 horizons
  and all components). Fossil (GWP-100 = 29.8) vs biogenic (27), stochastic:

  | yr | SLR bio | SLR foss | temp bio | temp foss | SLR÷temp bio | SLR÷temp foss |
  |---|---|---|---|---|---|---|
  | 20 | 4.63 | 4.23 | 3.70 | 3.42 | 1.25 | 1.24 |
  | 70 | 2.24 | 2.11 | 0.79 | 0.81 | 2.82 | 2.60 |
  | 100 | 1.68 | 1.60 | 0.52 | 0.56 | 3.23 | 2.85 |
  | 150 | 1.22 | 1.19 | 0.38 | 0.44 | 3.18 | 2.71 |
  | 270 | 0.79 | 0.80 | 0.24 | 0.31 | 3.34 | 2.62 |

  Two consequences. (1) **The >3× divergence is a BIOGENIC-CH₄ statement** — the oxidation CO₂ makes a
  fossil pulse more CO₂-like and compresses it to ~2.6–2.85×. Both are large, but the arm must be
  labelled. (2) **GWP-100 = 29.8 increasingly UNDER-corrects for the oxidation carbon**: the physical
  fossil/biogenic marginal ratio climbs 1.02 → 1.13 → 1.27 → 1.43 at 20/70/150/270 yr against a fixed
  GWP ratio of 1.104, so by 270 yr a fossil tonne is worth ~1.29× its biogenic counterpart per
  GWP-equivalent tonne on temperature. (A fixed 100-yr integral cannot track a 270-yr endpoint.)
  See the FaIRtoFrEDI CHANGELOG for the fossil two-pass concentration-leak fix that preceded this.
- **GOTCHA documented in the driver header — `_arg` is `findfirst`, so the FIRST occurrence of a flag
  wins and later repeats are silently ignored.** A queued fossil job built its command as
  `"$BASE_ARGS $OVERRIDES"`; the intended 3-config zero-pulse smoke gate therefore ran as a full
  841×2000 production job (harmless — it produced the valid production stochastic arm, and the real
  zero-pulse gate was run afterwards and passed — but it cost a duplicate ~50 min run, which was
  killed mid-flight with the depot verified pristine afterwards). Never append overrides; state each
  flag exactly once.
- **Sequencing rule reaffirmed:** BRICK arms must never run concurrently under `run_subannual.sh` —
  the wrapper patches the SHARED MimiBRICK depot and restores it via an EXIT trap, so a second
  wrapper's trap would swap the integrator under a live run. Killing the *only* running wrapper is
  safe (the trap restores pristine, which is the desired end state) and was verified by diff.

## [unreleased] — 2026-08-02 — Metric framing, pulse-relative horizons, safe-patch wrapper

- **KEY MESSAGE fixed (Marcus):** CH4's SLR impact is much longer-lasting than its temperature impact,
  and that drives the CO2/CH4 comparison — an SLR metric values CH4 ABOVE GWP-100 while a GTP-style
  metric values it WELL BELOW. Quantified per GWP-100-equivalent tonne (CO2 ≡ 1.0), years after pulse:
  temperature 0.79/0.52/0.45/0.38/0.24 at 70/100/120/150/270 yr vs SLR 2.24 @70, 1.45 @120, 0.79 @270 —
  the two metrics differ by >3× at matched horizons. Component attribution is an intermediate step, NOT
  the headline (earlier framing over-elevated it).
- **`--horizons=` / `--comp-years=` flags**: the paper's key variable is YEARS SINCE THE PULSE (100/150
  yr = 2130/2180 for a 2030 pulse), not calendar 2100/2150. 4-arm re-run launched on
  2050,2100,2130,2150,2180,2300.
- **BUG FIXED — metric-packing offset was hardcoded `4 + 4*(ci-1)`** instead of `length(HORIZONS)`; with
  >4 horizons component writes clobbered horizon slots and left `met` partly uninitialized → NaN.
  **Caught by the zero-pulse gate.** No prior result affected (identical expression at 4 horizons;
  default-horizon re-run byte-compares 0.0 vs the original pre-change reference) — no quarantine.
- **`scripts/run_subannual.sh`**: applies the sub-annual DAIS patch and GUARANTEES restore via an EXIT
  trap (success/failure/interrupt), resolving the depot from the MimiBRICK `julia_v2` actually loads.
  The patch mutates a SHARED depot file, so a crashed hand-patch would silently change later jobs.
- Handoff: `notes/handoff_2026-08-02_ch4co2_metric_horizons.md`.

## [unreleased] — 2026-08-02 (late) — CH4 pulse arm: per-gas SLR marginals on BRICK-AM

- **FaIR CH4 biogenic 1 Tg @2030 pulse** (SSP2-4.5, 841 cfg, stochastic + `_nonoise_flatsolar`);
  pre-pulse marginal exactly 0.0 (paired seeds); wide files dumped; CH4 and CO2 arms share the SAME
  baseline (verified: 2.5e-12 cm through BRICK, zero tip-classifier disagreements) → cleanly paired.
- **Headline (MEAN total-SLR marginal, sub-annual, per GWP-100=27 CO2e): CH4/CO2 = 2.24 @2100,
  1.45 @2150, 0.79 @2300** — reproduces the research plan's placeholder crossover (~2.2-2.3 / ~1.4 /
  0.6-0.7) on a DIFFERENT posterior (BRICK-AM vs pre-FM Mengel) and DIFFERENT backbone (SSP2-4.5 vs
  RFF-SP). Basis-insensitive: stochastic vs deterministic agree to 0.04-1.7%.
- **FLAG — contradicts a stated paper novelty claim.** The research plan (§1 contribution 1) expects
  component resolution to reveal a "CH4-TE-led vs CO2-AIS-led split". It does NOT, here: BOTH gases
  are AIS-led with near-identical component shares (@2100 AIS 76% CH4 vs 75% CO2; TE 17% vs 19%), and
  the CH4/CO2 ratio is roughly uniform ACROSS components (2.26/2.66/2.59/2.05 for ais/gsic/gis/te).
  The real differential is in the DECLINE RATE: TE's ratio falls fastest (2.05→0.53 by 2300), AIS
  slowest (2.26→0.82). The crossover is a timing effect that scales all components, not a component-mix
  difference. The novelty argument needs rebasing on that, or the claim dropped.
- **FLAG — tip-classifier threshold needs re-tuning.** The documented baseline-AIS@2100 > 20 cm
  classifier (mimibrick-quirks item 11, calibrated on LHS-10k where it selects ~5%) selects **37.6%**
  on BRICK-AM extA108 (amp 1.08 puts far more mass near tipping; baseline AIS p50 6.99 / p75 32.50 cm).
  MEANS are classifier-free and unaffected; only the mode decomposition depends on this choice.

## [unreleased] — 2026-08-02 — Paired pulse arm + fast engine; production run locally (Torch now optional)

- **`weight_and_project_brick_fair.jl`: paired 10-GtCO2 pulse arm** (`--pulse=off|on|zero`,
  `--basis=`, `--pulse-gt=`, `--out-tag=`). Pulse runs in-process on the same model instance right
  after each baseline run (exact per-(config,draw) pairing); per-pair Δ dumped
  (`wong_cond_pulse_pairs*.csv`, 16 base + 16 Δ metrics — too big to commit; all statistics
  recomputable in post). Defaults reproduce the staged driver BYTE-FOR-BYTE (verified).
- **Fast engine (`--engine=fast`, default): ~30× — and it saved the Monday launch.** Discovery: any
  `update_param!` triggers a ~14 ms Mimi rebuild of the 451-yr model per run (integration is ~2 ms;
  `diag_wpf_runtime_breakdown.jl`), so the staged full run was ~12–14 h, not the estimated 1–2.5 h —
  it would have TIMED OUT on cpu_short. Fast path mutates the built instance in place (shared-backing
  SubArray views for forcing; ScalarModelParameter boxes for scalars; `run(mi)` — Mimi 1.6.0 internals)
  → 0.88–1.3 ms/run. Bit-identical to legacy: per-component, full-smoke CSVs, and the 24k-pair
  60cfg×400draw pulse run all byte-compare clean; `--engine=legacy` kept for A/B.
- **Five-test battery PASS** on the pulse arm (`python/check_pulse_battery_wpf.py`; companion ±10/+20
  GtCO2 FaIR arms dumped to `curv_wide` via `dump_fair_wide_curv.py`): zero-pulse Δ=0.0 exactly;
  sign-flip −1.000..−1.005 and doubling 0.998–1.000 on linear metrics; AIS shows genuine convex
  tipping asymmetry (dbl 1.06@2100 → 1.25@2300); cross-process bit-reproducibility; first-principles
  vs the 7.7e-3 cm/GtCO2 artifact reference (flag: 60-cfg preview medians ~4.7e-3 — reconcile on the
  full run before quoting).
- **60cfg×400draw preview:** conditional weighting leaves the pulse-marginal MEDIAN ~unmoved (+0.2%)
  and trims the AIS-tipping upper tail (95th −1.7% @2100, −4% @2300) — the coupling bites in the tail.
- **Full production COMPLETE, locally** (4 runs × 3.36M BRICK runs: {stochastic, nonoise_flatsolar} ×
  {annual, sub-annual patch}; depot patched from `julia/patches/` with backup and RESTORED pristine).
  **Headline results:** (1) levels — coupling immaterial (total@2100 COUPLED 46.68 vs INDEP 46.38 cm,
  width −0.68); (2) **pulse marginal — coupling ALSO immaterial** (mean ratio 1.003–1.009, TE 1.000,
  tip fraction 23.31→23.41%): the "may matter more on the marginal" conjecture is answered NO — the
  independent pipeline stands everywhere, unblocking the CH4/CO2 comparison; (3) sub-annual patch
  REQUIRED for quotable pulse numbers — cross-product mean @2100 1.469e-2 cm/GtCO2 reproduces the
  artifact's 1.498e-2 within 2%, driver-basis-consistent to 0.05%; the pooled MEDIAN is sample-fragile
  (23–33% tip-advance mode puts the 50th pctile in the bimodal density gap — quote mean or
  mode-decomposition, never bare pooled median); (4) the patch is a perfect no-op at mean forcing
  (ℓ^B bit-identical) but 401/1.68M hot-config × low-threshold pairs cross DAIS pre-2026 (ℓ^FB
  changes; immaterial). Annual-step pulse outputs re-tagged `_annualstep` (diagnostic only). Torch
  demoted to optional cross-check.

## [unreleased] — 2026-08-01 (late) — Conditional Wong-weighting: BRICK-AM draws consistent with FaIR

- **`julia/weight_brick_conditional_fair.jl`** — the ENDORSED forward-propagation consistency method (the
  correct alternative to the rejected joint calibration). For each FaIR config *k* it reweights the BRICK-AM
  posterior draws by historical-SLR consistency, `w_{i|k} ∝ exp[c·(ℓ^FB_{ik} − ℓ^B_i)]`, **normalized WITHIN
  each config** so `p(config)` stays uniform — every FaIR parameter set stays equally likely; SLR never
  touches the forcing marginal. `ℓ^B` at the mean (calibration) forcing so the ratio isolates the pairing
  and cancels the intrinsic fit (mitigates the Mengel double-count). Reuses `calibrate_mcmc_ext.jl` (now
  behind a `PROGRAM_FILE` guard) for the FREE list + θ→BRICK apply + dang-channel AR(1) likelihood.
- **Validated locally (60 configs × 400 draws):** (1) mean-forcing recovery — max|ℓ^FB−ℓ^B|=0, weight
  ESS/N=1.000 (exactly uniform at the calibration climate); (2) coupling signature — corr(weight, te_α)
  vs config OHC@2018 = −0.46 (hottest configs −0.156, coldest +0.113: hot ocean-heat down-weights high-te_α
  draws, TE∝te_α·OHC); (3) gentle, c=0.145 → mean conditional ESS/N=0.60 (≈ Tony's c≈0.2 for GMSL-only).
- Recovers the te_α↔OHC coupling in PROPAGATION, forcing marginal untouched.
- **Launch code built** (`julia/weight_and_project_brick_fair.jl` + `slurm/weight_and_project_brick_fair.sbatch`):
  one BRICK run per (config, draw) to 2300 yields BOTH ℓ^FB (weight) AND future SLR (bands); reports
  COUPLED (conditional-weighted, config equal) vs INDEPENDENT (equal) bands at 2050/2100/2150/2300 + comps.
  Local smoke (5 cfg × 100 draws) runs clean. **HELD for Monday launch (fairshare recovery)** — full run
  = DRAWS=2000 CONFIGS=all (~1.68M runs to 2300, fits cpu_short 4h). Run the 5-cfg smoke on Torch first.

## [unreleased] — 2026-08-01 — Joint FaIR/BRICK forcing calibration: BUILT, TESTED, **REJECTED**

- **Tried and abandoned.** Question (Marcus 2026-07-24): does jointly calibrating BRICK params + the
  FaIR forcing (recovering the `te_α↔OHC` coupling the mean-forcing shortcut drops) beat the shortcut?
- **Built:** `julia/diag_coupling_reweight.jl` (step-1 proxy), `calibrate_mcmc_joint.jl` (discrete index,
  mixed poorly), `calibrate_mcmc_joint_cont.jl` (continuous K=3 forcing-PCA reparam; basis
  `outputs/forcing_pca_basis.csv` via `python/precompute_forcing_pca.py`), `project_slr_joint_cont.jl`
  (deliverable R̂), `project_slr_coupling_test.jl`. Torch run: 4×4M chains, acceptance 0.237, recovery
  bit-identical to ext, deliverable total-SLR R̂ 1.001 (converged).
- **Result 1 — coupling real:** pooled corr(te_α, fpc2/fpc3) = −0.52/−0.61, te_α R̂ 1.004.
- **Result 2 — coupling IMMATERIAL to total SLR:** shuffle test tightens the TE component ~29 % but only
  −2.3 %/−0.55 cm on total @2100 (AIS tipping tail dominates).
- **Result 3 — freeing the forcing is HARMFUL:** the SLR likelihood re-inferred the forcing, drifting
  fpc1 (the ±0.68 °C ECS/atmosphere mode) to bend GMST **−0.28 °C @2100** (→ −0.48 @2300) vs the ensemble
  mean; this (not the coupling, not the params) drove the entire joint-vs-extA108 gap (−7.7/−45/−122 cm).
  The joint's lower SLR is low for the wrong reason.
- **Reason for rejection (Marcus 2026-08-01):** SLR must not re-infer atmospheric variables (forcing/ECS)
  that other data constrain far better; PROPAGATE FaIR uncertainty forward, don't RE-CALIBRATE it. OHC-only
  freedom also rejected (double-count vs FaIR's OHC constraint + te_α↔OHC degeneracy → low-value).
- **Canonical BRICK-AM stays `calibrate_mcmc_ext.jl` (mean forcing) + forward-propagated FaIR uncertainty.**
  Joint drivers retained, banner-marked DIAGNOSTIC/REJECTED. Full record:
  `notes/negresult_2026-08-01_joint_forcing_calibration.md`, memory `project_fair_brick_coupling_joint_calib`.

## [unreleased] — 2026-07-22 (late 3) — OHC time-component test: CONFIRMED (second-order)

- `python/reduce_cmip6_ohc_deck.py` (zostoga = thermosteric SLR, OHC proxy, 17 DECK models)
  + `python/diag_pai_ohc.py`: test whether OHC carries the Antarctic time-component that
  GMST alone misses. Fit ΔT_ant ~ α·ΔGMST (M1) vs α·ΔGMST + β·ΔOHC (M2), pooled over
  1pctCO2 + abrupt-4xCO2 (decorrelated in abrupt → identifies β).
- **RESULT — Marcus's hypothesis CONFIRMED, second-order:** β_OHC > 0 in **17/17** models;
  partial correlation r(T_ant, OHC | GMST) **positive in 17/17, median 0.46**; a GMST+OHC
  map fit on abrupt-4xCO2 predicts 1pctCO2 with **~40% lower error** (transfer RMSE
  0.98→0.61 K) and tracks the abrupt slow-rise GMST-only under-predicts. But within-scenario
  R² barely moves (0.94→0.95) — OHC is the cross-pathway/time correction GMST cannot supply,
  not a dominant term. Earns its keep for stabilization/long-horizon, not ramp projections.
- A6 note proposal 5B upgraded "OHC candidate" → **tested/confirmed** with Figure 3; caveat
  + provenance added; PDF re-rendered (now 3 figures).

## [unreleased] — 2026-07-22 (late 2) — denominator/aerosol test; terminology + note polish

- **New `python/reduce_cmip6_hemis.py` + `python/diag_pai_denominator.py`**: test Marcus's
  hypothesis that the mid-century amplification-ratio noise is a global-denominator (NH
  aerosol) artifact. CONFIRMED: mid-century NH aerosols depress the global mean below the
  SH mean (1980: global 0.31 K < SH 0.35 K), inflating the Antarctic/global ratio to a
  ~1.7 peak ~1980 that relaxes as aerosols clear; referencing to the SH mean halves the
  inter-model IQR (0.97→0.46 @1980) and removes the peak. (SH ref not usable for `a` — it
  settles ~1.39 since the SH warms less than the globe — but confirms the noise mechanism.)
  Textbook aerosol signature in `outputs/diag_pai_denominator.png`.
- **A6 note updates** (Marcus review): (1) ratio renamed "secant/level ratio" →
  **"Antarctic amplification ratio"** throughout (note + Figure 1 labels); T_AIS notation
  dropped from the figure; (2) the polar-cap/mask discussion moved to a **footnote**;
  (3) the aerosol/denominator finding added as a footnote; (4) proposal 5B gains **OHC as
  the observable slow-mode predictor** (already a BRICK input); (5) note serif switched
  Charter→Georgia (clean capital A). PDF re-rendered.

## [unreleased] — 2026-07-22 (late) — switch scenario diagnostic to the SECANT ratio; a ≈ 1.08

- `diag_pai_cmip6_time.py` reworked from the 41-yr windowed MARGINAL trend ratio to the
  **secant (level) ratio** R = (T_AIS−T_AIS,PI)/(T_glob−T_glob,PI), 30-yr running means,
  pre-1950 dropped (Marcus's request — the secant is what BRICK `a` actually is, so no
  marginal→level integration needed).
- **RESULT: the direct secant is ≈1.06–1.10 at crossing-relevant warming (2.5–3.5 K) and
  nearly FLAT across 2–5 K** (ssp245/ssp585 collapse). This CORRECTS the earlier
  integrated-marginal estimate of 0.97–1.03, which was biased ~0.1 low by a too-low
  extrapolated ΔT→0 intercept. The corrected secant now AGREES with the DECK 1pctCO2
  GHG-only secant (1.07–1.13), so the previously-claimed ~0.08 "aerosol suppression gap"
  was an artifact and is retracted.
- **A6 note consequences:** proposal A center moved 1.00 → **1.08** (`a ~ N(1.08, 0.15)`,
  equilibrium 1.196 now at +0.7σ); the "Level vs marginal slope" section deleted (moot);
  proposal B's marginal amp(ΔT) exponential replaced by the DECK two-mode map
  T_ant−T_ant,PI ≈ 1.08·ΔT_fast + 1.70·ΔT_slow; Figure 1 + captions synced. PDF re-rendered.

## [unreleased] — 2026-07-22 (evening) — DECK 1pctCO2/abrupt-4xCO2: the time component IS real

- `python/reduce_cmip6_tas_pai_deck.py` + `python/diag_pai_deck.py`: 41 models, GHG-only
  (aerosols/ozone at piControl — the confound-free test), anomalies rel. piControl mean.
- **At matched warming (2.5–4.5 K), amplification depends on forcing AGE**: abrupt-4xCO2
  reaches those levels ~6–22 yr after forcing (level ratio 0.93–1.11); 1pctCO2 takes
  ~100–124 yr (1.07–1.13). Paired D = −0.13…−0.08, bootstrap CIs exclude zero. The
  scenario-based null was an estimator-power result, not absence: cross-SSP forcing-age
  contrasts are ~10× smaller than the DECK contrast.
- **abrupt R(t) climbs 0.95 → ~1.2 over ~100 yr and asymptotes at 1.23 [IQR 1.11–1.45]**
  ≈ the DAIS equilibrium 1.196 (n=2 runs to 300 yr hint slightly higher). Gregory
  fast/slow-mode slopes: 1.08 / 1.70 — the slow (deep Southern Ocean) mode is strongly
  polar-amplified and drags the ratio up with time.
- Interpretation: along century-scale ramps, level and forcing-age co-vary, so the
  scenario amp(ΔT) closure silently absorbs the time dependence (fine for ramp-like
  futures); it would misextrapolate under stabilization (amp keeps rising while ΔT
  stalls) — relevant to post-2100/2150 horizons. 1pct GHG-only level ratio at 2.5–3.5 K
  (~1.07–1.13) sits ~0.08 above the scenario-based secant (0.97–1.03), consistent with
  ozone/aerosol suppression baked into real-world trajectories.

## [unreleased] — 2026-07-22 (later) — 5-scenario level-vs-rate test: NO identifiable rate component

- Added ssp119/ssp126/ssp370 to the PAI reduction (`python/reduce_cmip6_tas_pai_ext.py`,
  same members as the base pull; `data/cmip6_pai/tas_series_ext_*.csv`) and a level+rate
  decomposition (`python/diag_pai_cmip6_rate.py`): matched-warming table + joint fit
  pai = 1.196 − (1.196−a0)exp(−dT/Ts) − c·rate on the 32-model common subset.
- **RESULT: the rate/time component is NOT identified** — c = −0.50 [−0.91, +0.11]
  per (K/decade), CI spans zero, sign driven entirely by ssp126's degenerate stabilized
  windows; with the three well-behaved scenarios (245/370/585, rates 0.25–0.5 K/dec) the
  residuals from the level-only fit are flat in rate. The ssp245>ssp585 crossover at
  2.5–3 K that motivated the test is NOT corroborated as a rate effect (ssp370, nearly as
  fast as 585, sits with 245).
- Two contaminations diagnosed and filtered (named constants): ozone-hole/aerosol-era
  windows (centres <2005; median Antarctic trend negative under non-GHG forcing) and
  stabilized windows (global trend <0.10 K/dec; trend-ratio estimator degenerates +
  ozone-recovery confound — visually obvious for ssp119/126 post-2040).
- Conclusion: the level-dependent amp(ΔT) form stands as the supported parsimonious
  model; a genuine time/rate test needs idealized runs (1pctCO2 vs abrupt-4xCO2) or a
  single-model large ensemble, which remove the composition confound.
- **SSP3-7.0 subsequently EXCLUDED from the analysis** (Marcus: it is the aerosol
  outlier; SH forcing-mix confound). Rerun on the 33-model {126,245,585} subset:
  conclusion unchanged — c = −0.64 [−1.06, +0.07], matched-warming flat at 2.0–2.5 K
  (245 1.13 vs 585 1.14 @2.5 K); the crossover survives only in the 3.0 K bin. The A6
  note gained §4 (multi-scenario test) + Figure 2 and was re-rendered to PDF.

## [unreleased] — 2026-07-22 — PAI-vs-time diagnostic (CMIP6): amp rises with warming; A6 prior reference-frame flag

- **New `python/reduce_cmip6_tas_pai.py`** (streams Amon tas for 35 models from the public
  Pangeo/GCS zarr archive; annual global + AIS-proxy means to `data/cmip6_pai/`, 780 KB total)
  and **`python/diag_pai_cmip6_time.py`** (windowed 41-yr trend-ratio PAI1, Xie-2022 gate,
  collapse test) + **`python/diag_pai_mask_sensitivity.py`**.
- **RESULT (34 models, land≥50% south of 60°S):** within-scenario PAI1 RISES in both SSP2-4.5
  (+0.035/decade; median 1.06→1.19) and SSP5-8.5 (+0.016/decade; 1.13→1.19), and the two
  scenarios roughly COLLAPSE onto one curve in global warming level: ~0.9 at ΔT≈0.7 K rising
  to ~1.15–1.2 by ΔT≈2 K, then flattening at ≈ the DAIS equilibrium value 1.196. Supports a
  warming-level-dependent GMST→AIS amplification interpolating transient→equilibrium.
- **MASK FINDING (A6 flag):** our land-only AIS metric gives full-window (2015–2100) PAI1
  1.13/1.16 (ssp245/585) — Xie et al. 2022's 0.95/1.03 is instead reproduced by the ALL-points
  polar-cap mask (6-model test: cap60 0.92/0.98). Xie's "AIS" metric is cap-like; DAIS's
  temperature lineage (ice-core/continent) argues for the land-referenced number, so the A6
  transient prior N(0.95, 0.10) may sit ~0.15 low in DAIS's reference frame — which would
  overstate the transient-vs-equilibrium contrast and part of the phase-2 76→40 cm drop.
  Flagged for the M5/A6 revisit; NOT resolved here.

## [unreleased] — 2026-07-21 — artifact pulse-MEAN column (sub-annual) + BRICK-FM write-up

- **New `julia/diag_subannual_pulse_means.jl`**: full-ensemble 10-GtCO₂ pulse means under the
  temporary sub-annual DAIS-crossing depot patch (applied for the run, restored after), both
  calibrations × both drivers → `outputs/crossmodel_pulse_means_subannual.csv`. Also writes the
  equilib posterior subsample `data/MimiBRICK/parameters_subsample_brick_mengel_extA6eq.csv`
  once (10k rows, loadpost-identical thinning of the 4 extA6eq chains; untracked like its
  siblings) so equilib runs are prefix-reproducible.
- **RESULTS** (×10⁻³ cm/GtCO₂, [MAGICC, FaIR]): transient mean @2100 [15.9, 12.1], @2150
  [29.1, 22.9]; equilib @2100 [22.8, 21.0], @2150 [34.7, 31.8]. Cross-checks: levels move <1%
  under the patch, transient medians +6–15% — but **equilibrium medians rise 2–4×** (@2100
  MAGICC 5.4→22.6): most equilib draws are already tipped, so the previously-quantized
  tip-advance channel reaches the median draw, not just the tail. Raises the stakes of the
  pending sub-annual-integrator adoption decision (M2).
- **`notes/writeup_2026-07-21_brick_fm_vs_wong_brick.md`**: BRICK-FM vs the original Tony Wong
  BRICK — structure (Mengel glacier), interface (external forcing, precip_log, LWS lock),
  calibration (phase-1/phase-2 A2/A4/A5/A6/geometry/obs), results deltas, pending integrator
  decision, provenance table.
- Cross-model artifact republished with the pulse-mean column (snapshot + details in
  FaIRtoFrEDI `magicc_comparison/artifacts/`).

## [unreleased] — 2026-07-20 (later) — phase-2 production run DONE + accepted; A6 sensitivity running

- **Two-stage launch executed.** Tuning chain (1M, acceptance 0.237) → built
  `overdispersed_starts.csv` + 39-param `adapted_cov_ext.csv` → **4×2M over-dispersed
  production run** (acceptance 0.234–0.237, ~3 h). All phase-2 terms confirmed working in the
  tuning posterior: SMB β_total→1860 Gt/yr (target 1863); amp 1.195→0.944; T_on sd 0.1;
  λ/γ/κ sampling paleo.
- **Production converged on the deliverable + accepted:** SLR@2100 R̂ **1.006**, SLR@2150 R̂
  **1.008** (10 param marginals still fail — the ridge). `postprocess_mcmc_ext.jl --accept-slr`
  wrote the canonical phase-2 `parameters_subsample_brick_mengel_ext.csv` (10k of 4M draws).
- **HEADLINE (SSP2-4.5, rel 1995–2014):** SLR@2100 median **39.7 cm** [36.9–75.0]
  (v-next 76.1), @2150 **62.8 cm** [55.7–153.5] (159.1). Threshold crossing ~82%→~29%.
  Production medians match the tuning preview (39.9/63.0) — robust. Moves BRICK-Mengel from
  above-AR6 to ~AR6-central for SSP2-4.5. Key params cooled: ais_ocean_temperature₀ 0.862
  (base 0.981), anto_alpha 0.296 (0.405).
- **A6-equilibrium sensitivity RUNNING** (`run_A6eq_sensitivity.sh`, amp pinned 1.196, infix
  `extA6eq`, ~3.7 h) to isolate A6's share of the headline drop (Marcus-approved attribution).
- **M2 downstream REFRAMED — NOT a mechanical repoint.** 12 drivers read the June-13
  `parameters_subsample_brick_mengel.csv` (incl. the pulse/MAGICC-vs-FaIR pipeline). Repointing
  to phase-2 halves the SLR-based pulse results, mostly via A6 (judgment-call σ). Gated on the
  A6 attribution + Marcus's decision on which posterior the pulse paper adopts. Held.

## [unreleased] — 2026-07-20 — phase-2 begun: M1 accept, Dangendorf/Frederikse untangle, A2/A4/A5/A6 wired

Phase-2 kickoff (Marcus decisions 2026-07-19/20). Nothing launched yet — the phase-2
recalibration awaits Marcus sign-off on the pinned numbers (see the pre-run summary /
handoff §5). What landed this session:

### M1 — accept the v-next posterior on the deliverable (DONE)
- Added `--accept-slr` to `postprocess_mcmc_ext.jl`: writes the canonical (no-suffix)
  subsample + proposal seed iff `outputs/mcmc/slr_convergence_ext.csv` (now emitted by
  `diag_slr_convergence_by_chain.jl`) shows SLR R̂<1.05 at all horizons AND is fresher than
  every chain file. Regenerated `parameters_subsample_brick_mengel_ext.csv` (canonical) +
  `README_brick_mengel_ext_acceptance.md`. Downstream drivers deliberately NOT repointed yet
  (done once, at the phase-2 posterior, with the M2 pulse rerun).
- Fixed a stray-chain trap: a 2-iteration smoke chain (`chain_ext_seed2026_n2.csv`) matched
  the `chain_ext_seed*` glob and had (1) collapsed the marginal diagnostic to 1 draw/chain,
  (2) leaked one smoke draw into row 1 of the prior subsample. Quarantined
  (`outputs/quarantine/20260720_smoke_chain_n2/`); postprocess now errors loudly on a
  chain-length mismatch (shortest < ½ longest). **This means the handoff's marginal numbers
  (worst R̂ 1.458) always came from the four full chains — the 18:22 "certification" was the
  degenerate 1-draw read, now confirmed.**

### Dangendorf / Frederikse — two-layer data bug untangled (A3 + M3 pre-check)
- `data/observations/dangendorf_2024_gmsl.csv` was **Frederikse 2020's own observed GMSL**
  (bit-identical). Renamed → `frederikse2020_gmsl_total.csv`; relabeled the active pipeline
  (`prep_recalib_targets_ext.py`, `apply_wong_weights.py`, `hawkins_sutton.py`,
  `julia/compute_lB_per_post.jl` — the "Dangendorf importance weights" were FREDERIKSE
  weights; `dangendorf` kept as a deprecated alias that warns).
- Fetched the **real Dangendorf 2024** (Zenodo 10621070). Its `KalmanSmootherHR_Global.nc`
  is mis-written upstream (the "GMSLHR" slot holds the BARYSTATIC mean — proved: cos-weighted
  mean of the Fields-nc `Bary` reproduces it to 0.000 mm). True GMSL = cos-lat-weighted mean
  of the `HR` field (`Fields.nc`), per the record's own `Master_Final.m`; validated vs the
  paper (1900–2021 1.52 vs 1.5±0.19; 1993–2021 3.17 vs 3.4±0.42 mm/yr). Extracted →
  `dangendorf2024_gmsl_annual.csv`. **SE unattributable (same slot-shift) — resolve before
  any likelihood use.**
- **Bonus:** the record also redistributes the full 5000-member weighted **Frederikse
  component ensemble** (`GMSL_ensembles_F20.nc`) — the exact object the 2026-07-19 σ-fix said
  was missing; enables the correct re-referenced per-component band σ (M3 implement).
- Tension diag (`python/diag_dangendorf_vs_frederikse.py`, ref 1995–2005): Dangendorf sits
  INSIDE Frederikse's 5–95% at every trend window; mid-century 1930–1970 D 1.44 vs F 1.85
  (6.8th pctl) is the real but bounded tension; 1993–2018 D 3.03 agrees with altimetry 2.86
  better than F 3.36 does. 11/119 yr outside the F band. Figure + summary in `outputs/`.

### A2/A4/A5/A6 — phase-2 calibration changes WIRED (not yet run), 35→39 params
- **A2:** freed `λ`, `ais_γ`, `ais_κ` under their existing paleo marginals (param_priors.csv).
  Observationally unidentified over the historical window → they sample the prior; the point
  is to propagate fast-dynamics uncertainty and de-bias the hot medoid (λ 0.0137→prior 0.0104).
- **A4:** runoff line reparameterized to its identified direction (`T_on = −h0/c`, `c`) under a
  rebuilt joint paleo prior (`compute_paleo_geo_prior_ton.jl` → `paleo_geo_prior_ton.csv`;
  paleo T_on −15.64±5.54, r(T_on,c)=+0.64 vs the posterior r(h0,c)=0.9997 it replaces).
  `h0 = −T_on·c` reconstructed per draw.
- **A5:** SMB likelihood term on model `β_total` (1979–2008 mean) vs area-scaled Rignot 2019
  (2098×0.888 = **1863 ± 118 Gt/yr**; σ from Rignot's spread, Mottram-2021 alternative flagged).
  At the medoid β_total = 2389 Gt/yr (z=4.45) — target is interior to the paleo-prior-vs-SLR-fit
  tension, so it anchors precip0 to a physical intermediate and breaks the 34:1 input–output
  degeneracy. **σ is a Marcus sign-off item.**
- **A6:** GMST→Antarctic-temperature map sampled as transient amplification `amp` (anchor
  T_ant(GMST=0) preserved); prior **N(0.95, 0.10)** on CMIP6 PAI1 (Xie et al. 2022, Sci Rep
  12:16548: 0.88/0.95/0.97/1.03 for SSP1-2.6/2-4.5/3-7.0/5-8.5; no published inter-model sd —
  0.10 spans the scenario range without re-admitting the equilibrium 1.196). Replaces the
  hard-coded 0.8365/15.42 (amp 1.196, ~26% high). **σ is a Marcus sign-off item;** biggest
  headline-mover (could shift "82% crossed by 2100" to a minority).
- Smoke-tested (200 iter): 39 params, θ0 logpost −799 (vs baseline −779), amp anchor identity
  exact, all new params tracked. Launch is TWO-STAGE (common-start tuning run → build
  over-dispersed starts + adapted cov → 4×2M production); `--overdisperse` now errors clearly
  when the starts file predates the current parameter set.

---

## [unreleased] — 2026-07-19 — σ-fix re-baseline: accept-on-deliverable, + pulse-size robustness

### σ-fix re-baseline (4 × 2M, over-dispersed starts, corrected Frederikse band)

- **Parameter marginals NOT converged** — worst R̂ **1.458** (`ais_slope`), the same
  identifiability ridge. **This is slightly WORSE than run 3 (1.320), not better.**
  **Correction to an earlier claim:** I said the σ fix "plausibly fixes the sampling
  problem." It does not — widening the observational σ *flattens* the likelihood, which
  makes the weakly-identified ridge *less* identified, so param-level mixing got marginally
  worse. The σ fix remains correct (the uncertainty really was wrong), but its effect on
  sampling is neutral-to-negative, not positive.
- **Deliverable IS converged, now under OVER-DISPERSED starts:** SLR@2100 R̂ **1.003**,
  SLR@2150 R̂ **1.004** (`diag_slr_convergence_by_chain.jl`, chains started from
  `ais_iceflow0` quantiles 0.02/0.35/0.65/0.98). This closes the anti-conservative-R̂ hole:
  chains that start far apart on the failing direction still agree on projected SLR to ~5 cm
  against a ~23–35 cm within-chain sd. Projected SLR @2100 median 76.1 cm, @2150 159 cm.
- **Accept-on-the-deliverable is now vindicated:** the posterior gives a converged,
  over-dispersed-robust SLR projection despite the nuisance marginals. Subsample written to
  `data/MimiBRICK/parameters_subsample_brick_mengel_ext_NOTCONVERGED.csv` (the suffix is
  honest about the *marginals*; it is accepted for SLR-level use — see the naming decision below).

### Two postprocess convergence-gate bugs (both found because the re-baseline was FALSELY certified "all converged")

1. `ess(arr; maxlag = size(arr,1))` trips an internal "draws after splitting is 0" path on
   ≥1e6-draw chains → returns **NaN**, and `NaN < ESS_MIN` is `false`, so NaN-ESS params
   silently PASS. Fixed: `maxlag = min(nmin−4, 200000)` and require `isfinite(r) && isfinite(e)`.
2. The full 37-col × 2e6-row × 4-chain read (~5.7 GB) returns **corrupted** data (NaN R̂/ESS
   for every param) on the swap-bound machine. Fixed: read only diagnosed columns.
   Verified against a low-memory selective read: true worst R̂ 1.458, not "all converged".

### Pulse-size robustness ladder (Marcus's test) — answered and verified

`julia/diag_pulse_size_robustness.jl`: BRICK-Mengel paired at 7 sizes 0.03–30 GtCO₂, climate
by IRF scaling (validated vs real FaIR 20gt/0.01gt, <0.06% median error; P=10 rung reproduces
the production driver bit-identically). Two independent verifiers confirmed paired discipline,
units, linearity, horizons.

- **Per-ton MEDIAN robust to 0.7–2.2% over 0.03–1 GtCO₂** — quantization does NOT move the
  median (the median member never tips). ✔ we are OK at SCC pulse sizes.
- **Genuine large-pulse NONLINEARITY** (not quantization): median +9–20% at 10 GtCO₂,
  +42–101% at 30 GtCO₂, monotonic (compounding disintegration). **ACTIONABLE: the canonical
  BRICK-Mengel pulse tables were run at 10 GtCO₂ → they overstate per-ton median by ~9–20%.
  Recompute the headline at ≤1 GtCO₂.**
- **MEAN unusable** (90–111% ladder spread, non-monotone).
- **The median under-states fast dynamics** in the opposite direction from the mean: the tip
  fraction never reaches 50% at any rung, so the median is always the smooth-channel
  background (mean/median 11–18×). Median = *central* marginal, not the expectation. For a
  fat-tail-inclusive number use the Lemoine-Traeger P(tip)·ΔSLR_tip decomposition, not the mean.

### DECISION PENDING (Marcus)
- **Naming/acceptance:** is the SLR-level R̂ (1.003/1.004) the accepted convergence criterion,
  so the `_NOTCONVERGED` subsample should be renamed to a canonical "accepted-on-deliverable"
  path? Or hold for the parameter-level ridge (which needs a mixture/re-fix, not more iterations)?
- **Recompute the pulse headline at ≤1 GtCO₂** (the 10-GtCO₂ tables are ~9–20% high).

## [unreleased] — 2026-07-18 — BRICK-Mengel **v-next recalibration** (Strategy B: 28 → 35 params)

Branch **`brick-mengel-vnext`** (new). `brick-mengel` is archived/frozen per CLAUDE.md,
so this work branches off it rather than committing onto it. **Flagged for Marcus:**
confirm this is the intended home — the alternative is moving the calibration drivers
into the MimiBRICK-FM repo, which is now the canonical home of the Mengel model.

### Changed
- **`julia/calibrate_mcmc_ext.jl`** — the 7 DAIS geometry params (`ais_μ`,
  `bedheight₀`, `slope`, `iceflow₀`, `precipitation₀`, `runoffline_snowheight₀`, `c`),
  previously **fixed at the prior medoid**, are now **free** under a joint MvNormal
  paleo-covariance prior. 28 → 35 free params (25 physical + 10 AR(1) noise).
- **Forcing** switched from the RFF-SP-central splice to the **SSP2-4.5 harmonized**
  splice (`fair_mean_{gmst,ohc}_ssp245harm.csv`), so the calibration and the pulse
  projections sit on the same forcing. Both share the Smith historical → 1850–2020
  unchanged (1850/1900/1971 bit-identical); differs only over ~2020–2026 of the fit
  window (mean |ΔGMST| 0.03 °C) and in the tail.
- **`FaIRtoFrEDI/build_fair_mean_v145.py`** parameterized (`--emissions-file`, `--tag`,
  `--scenario-label`) so alternate forcings can be built **without overwriting** the
  canonical `fair_mean_{gmst,ohc}.csv`. Defaults unchanged.

### Added
- **`MimiBRICK.jl/calibration/compute_paleo_geo_prior.jl`** → `outputs/paleo_geo_prior.csv`.

### Quarantined
- June-13 28-param `ext` posterior → `outputs/quarantine/20260718_pre_vnext_28param_ext/`
  (**superseded, NOT bugged**). Necessary because `postprocess_mcmc_ext.jl` globs
  `chain_ext_seed*` and would otherwise silently mix 28- and 35-column chains.

### Tried and abandoned / rejected
- **Raw paleo covariance as the prior — rejected.** The 7 params span scales 1e-4…1e3,
  giving `cond(Σ) = 5.2e13`. Used the **standardized** form instead — `MvNormal(0, C)`
  on `z=(θ−μ)/sd`, `cond(C) = 2.75` — which keeps the paleo correlation structure
  without the ill-conditioning.
- **Continuing on the fork's `calibration/calibrate_mcmc_mengel.jl` — abandoned.**
  It does not run: it calls MimiBRICK internals (`get_model`, `set_external_forcing!`,
  `_apply_mengel_defaults!`) unqualified, as if lifted out of the module with the import
  dropped, and separately crashes on missing values because the extended targets gained
  trailing empty years after it was written. Evidence it was refactored for the PR and
  never re-run. My edits to it were **reverted**; pivoted to `calibrate_mcmc_ext.jl`,
  which runs and already had the Mengel emulator, the freed `ais_ocean_temperature₀`,
  the dropped point terms, and NaN handling. *Open: whether to also fix the fork script
  as separate cleanup / flag to Tony.*
- **`islog=true` for `precipitation₀` — rejected.** `setp!` applies `log()` when
  `islog=true`, and MimiBRICK v2.0.0 already computes `exp(ais_precipitation₀)`
  (default `log(0.37)`), so that would log twice. Sampled in log space with `islog=false`.
- **Geometry-specific proposal scale as the fix for low acceptance — rejected by test.**
  Plausible (paleo sd for `ais_μ` is 1.8 vs a chain spread of ~0.004) but **wrong**:
  it moved acceptance only 0.022 → 0.029. `GEO_PROP_SCALE` is retained as a sane default,
  not as the fix. The actual cause was the **θ0 start point** — geometry fell back to the
  paleo prior *mean* rather than the *medoid* the rest of the MAP was conditioned on
  (medoid `precip₀` 0.94 m/yr vs paleo mean 0.40, a 2.3× difference; `iceflow₀` −1.4 sd).
  That put `logpost(θ0)` at −5636 vs the 28-param baseline's −771. Isolated by running the
  original 28-param script at the same iteration count/seed (acceptance 0.192) as a control.
  With the medoid start: `logpost(θ0)` = −779, acceptance 0.196 → 0.222 after adaptation.

### Run 1 (4 × 500k) — NOT CONVERGED; diagnosed, not a bug

Acceptance healthy (0.224–0.241), but **12 params fail R̂<1.05**, and the failures are
exactly the 7 geometry params (R̂ 1.44–1.98) plus the AIS block they correlate with
(`ais_ocean_temperature₀` 1.09, `antarctic_alpha` 1.49, `anto_alpha` 1.25, `anto_beta` 1.51).
ESS ≈ 2000 with bad R̂ = good *within*-chain mixing, bad *between*-chain agreement.

Diagnosed with three tests rather than assumed:
- **Not multimodal.** Per-chain median `log_post` = 126.7 / 128.5 / 129.7 / 126.8 — all four
  chains sit on the same plateau. No chain found a better mode.
- **Not bound-railing.** Only 5% of pooled `ais_c` draws and 10% of `ais_runoff_h0` fall
  within 2% of a paleo bound. **This corrects the "watch `ais_c` railing" flag raised from
  the 50k tuning chain — it was an over-read of one short chain.**
- **The geometry block is weakly identified.** Posterior sd / prior sd = 0.46–0.76
  (`ais_bedheight0` 0.76 ≈ unidentified; the rest roughly halve the prior sd). Per-chain
  medians differ by 1.5–4.5 within-chain sd while posterior density is equal.

So the target is a broad, correlated, weakly-identified ridge — which is *why* the original
calibration fixed these at the medoid. Not a defect in the implementation.

### Run 2 (4 × 1M) — in progress
Reseeded from the **empirical 35×35 posterior covariance** written by postprocess. Run 1
started from the 28×28 embed + diagonal, which encoded nothing about the geometry ridge;
the empirical covariance captures its correlation, so this tests better mixing rather than
brute-forcing iterations. Run-1 chains quarantined to
`outputs/quarantine/20260718_vnext_run1_notconverged/` to keep the `chain_ext_seed*` glob clean.

**A non-converged subsample was written to the canonical
`data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv` and has been moved out** to
`outputs/quarantine/20260718_vnext_NOTCONVERGED_subsample/`. The June-13 `_ext` subsample at
that path was overwritten in the process — it is untracked, but regenerable from the
quarantined June-13 chains. The four MAGICC-vs-FaIR tables are unaffected: their driver
reads the non-`_ext` `parameters_subsample_brick_mengel.csv`, which is untouched.

### 2026-07-19 — ADVERSARIAL AUDIT: several of the above diagnoses were WRONG

A 4-lens adversarial audit of the convergence diagnosis (workflow `wf_e17a59f6-443`)
found real defects. Retractions, with what replaced them:

- **RETRACTED: every ESS number reported for runs 1–3.** `postprocess_mcmc_ext.jl:37`
  called `ess(arr)` with MCMCDiagnosticTools' default `maxlag=250`, which truncates the
  Geyer sum at τ≤500 and therefore **floors ESS at ntotal/500**. Reported values were
  exactly that floor (run1 ~2000, run2 ~4000, run3 ~8000). The "ESS doubled → mixing
  improved" reading — which I used twice as evidence — was the floor doubling with
  `ntotal`. **True run-3 ESS: `ais_iceflow0` 10.6 (τ=376,230), `antarctic_alpha` 19.6,
  `ais_precip0_LOG` 41.9, `ais_slope` 47.7.** Fixed; ESS now reported with τ.
- **RETRACTED: "longer chains, no methodological change."** Reaching ESS 400 for
  `ais_iceflow0` needs ~38M iterations *per chain* (~80 h/chain). Run 3 (2 M) confirmed
  it empirically: R̂ did **not** improve over run 2 and the worst param got *worse*
  (1.245 → 1.320). Chain length is not the lever.
- **RETRACTED: the identifiability causal story — it was backwards.** The parameters that
  fail R̂ are the **constrained, correlated** ones; the weakly-identified ones mix
  *trivially* (`ais_bedheight0` ESS 7218, `ais_c` 5356) because the sampler just draws the
  prior. Correspondingly, "re-fix `ais_bedheight0`" was exactly backwards — it is the
  best-converged parameter in the set (R̂ 1.000).
- **RETRACTED: run-1 provenance.** Run 1 did **not** use a 28×28 embed; its log shows the
  full-35×35 branch fired. Both runs were seeded 35×35 (run 1 from the 50k pilot). The
  earlier commit message and handoff describing a diagonal-vs-tuned contrast are wrong.
- **RETRACTED: "not multimodal."** Per-chain median `log_post` cannot distinguish a flat
  ridge from equal-height modes. Run 1 never reached the typical set (plateau ~126 vs the
  stationary ~135, ≈3000× in density), and run-2 seed2029 sat at ~126 for 600k iterations
  then jumped to ~135 — a metastable neck, escape time O(3–6 × 10⁵).
- **CORRECTED: bound-railing.** Holds for run 2 (max 0.0075 within 2% of a bound) but was
  **false for run 1**, where chains spent ~50% of draws against the `ais_runoff_h0`
  ceiling. The 2%-of-range band was too thin to see it.
- **UPHELD:** R̂ *is* rank-normalized split-R̂ (Vehtari 2021), verified by independent
  reimplementation. Reseeding the proposal is legitimate adaptive MCMC (fixed before the
  run, diminishing adaptation satisfied) — the R̂ validity problem is the shared start, not
  the reseed. `ais_runoff_h0`↔`ais_c` posterior correlation +0.954 (prior +0.228) is a
  genuine structural degeneracy. Rotating onto the *prior's* principal axes would be a
  no-op, since RAM already adapts a full covariance.

### THE RESULT THAT MATTERS: the deliverable IS converged

`julia/diag_slr_convergence_by_chain.jl` (new) runs 400 thinned draws per chain forward
on SSP2-4.5 and diagnoses **projected SLR** rather than the nuisance marginals:

| quantity | R̂ | ESS | between-chain median spread |
|---|---|---|---|
| SLR@2100 | **1.001** | 1564 | 4.5 cm vs 22 cm within-chain sd |
| SLR@2150 | **1.002** | 1420 | 5.1 cm vs 34 cm within-chain sd |

Verified **not** an artifact of parameters silently failing to set: a one-at-a-time
sensitivity probe gives each badly-mixed param large individual leverage on SLR
(`ais_iceflow0` up to 57 cm @2100, `ais_precip0_LOG` 49 cm), and the chains genuinely
disagree on those marginals. So the AIS geometry sits on a **compensating ridge** —
individually consequential, jointly constrained. Pooled median SLR@2100 = 76.8 cm
corroborates the earlier 77.7 cm posterior-predictive value.

### Run 4 (4 × 2M, OVER-DISPERSED starts) — in progress
The one remaining validity hole: all runs to date started all 4 chains at an identical
θ0, making R̂ anti-conservative (it cannot see mass no chain reached) — including the SLR
R̂ above. `--overdisperse` now starts each chain from a real posterior draw at
`ais_iceflow0` quantiles 0.02/0.35/0.65/0.98. Random jitter was tried first and failed
(200/200 non-finite logposterior). Expect R̂ to look worse; that is the diagnostic working.

### DECISION PENDING (Marcus) — superseded framing below

*(The original three options were written before the audit. Options 1 and 2 are now dead:
chain length cannot work, and `ais_bedheight0` was the wrong parameter to re-fix.)*

The live decision is **what to gate acceptance on**:

- **RECOMMENDED — gate on the deliverable.** Accept the posterior on SLR@2100/@2150 R̂
  (1.001/1.002) plus the AIS projection knobs, and report the 7 geometry marginals as a
  weakly-identified nuisance block on a compensating ridge. Requires disclosure in methods
  (see below). Conditional on run 4 confirming under over-dispersed starts.
- **Alternative — re-fix the hard-mixing params** (`ais_iceflow0` / `ais_slope` /
  `ais_precip0_LOG`, *not* `ais_bedheight0`). Cheap, but `ais_precip0_LOG` is the most
  projection-coupled geometry param (r = −0.282 with `antarctic_alpha`, +0.364 with
  `anto_beta`), so fixing it is not free.
- **Alternative — change sampler.** The ridge is curved; a linear reparameterization is a
  no-op under RAM. Would need HMC/NUTS on a transformed target or tempering.

**Must be disclosed in the paper's methods** regardless of choice: R̂ is rank-normalized
split-R̂; several AIS marginals do not reach R̂<1.05 at 4 × 2M and are reported as a
weakly-identified nuisance block; convergence is asserted on posterior-predictive SLR, not
on those marginals; the `ais_runoff_h0`↔`ais_c` degeneracy (posterior r = +0.954).

## [unreleased] — 2026-07-09 — CH4/CO2 pulse → SLR **research plan** (adversarially reviewed)

- **`notes/research_plan_2026-07-09_ch4co2_slr_paper.md`** — full research plan
  expanding the same-day handoff into a submission-oriented document: paper thesis
  + 4 contributions, literature positioning/novelty (Sterner-Johansson-Azar 2014 and
  Zickfeld 2017 as ancestors; Nauels 2025 / SURFER v3.0 / Wong's own arXiv preprint as
  threats), the **RFF-SP-vs-SSP backbone decision** (recommend RFF-SP primary for the
  gas headline + uncertainty band; SSP2-4.5 as the shared cross-model-panel backbone
  and AR6-anchor/curvature layer), pulse-experiment design + discipline, MAGICC Phase 2
  and FACTS comparison plans, figure/table set, 11 open methodological decisions, an
  11-row risk register, dependency-ordered sequencing, journal strategy, and a compiled
  reference list with DOIs.
- **Built from a 7-agent context sweep** over the BRICK-FM fork docs, MAGICC Phase 1/2
  handoffs, the completed 3-BRICK pulse study, FACTS scoping, the backbone evidence, and
  a verified literature search; then **adversarially reviewed by 3 independent critics**
  (numeric consistency — all headline numbers recompute and match source; novelty/strategy;
  methods/execution risk). Fixes folded in: reframed "level-vs-marginal inversion" as a
  mechanism decomposition (pre-empts the "expected threshold-model behavior" objection);
  added a **required CH4-specific scenario-sensitivity test** (the ~8% scenario-insensitivity
  is a CO2 cross-check, not CH4 — and RFF under-projects CH4 growth, obs ≥ p95); elevated
  Wong coordination and the reference-arm reuse-vs-re-run question to explicit gates; split
  the fossil-CH4 doc-vs-lock contradiction by arm; flagged the RFF CO2-unit (1000×) and
  MAGICC float32-floor pulse-size risks; and made GWP-basis dependence of the crossover a
  first-class result.

## [unreleased] — 2026-07-09 — CH4/CO2 pulse → SLR paper plan (BRICK-FM coming-out paper)

- **`notes/handoff_2026-07-09_ch4co2_slr_paper_plan.md`** — plan for the paper
  combining CH4-vs-CO2 pulse SLR impacts with the BRICK-FM introduction. Covers:
  BRICK-FM v-next recalibration scope (Smith 2024 emissions splice, freed AIS
  geometry params, IMBIE/Dyurgerov point-term reconciliation, TE overshoot,
  FaIR-config-aware calibration options), MAGICC Phase 2 + FACTS2.0 comparison
  plan, paper skeleton, open methodological decisions, and sequencing.
- **Discrepancy flagged (must resolve before recalibration):** the fork's
  `calibrate_mcmc_mengel.jl` includes the IMBIE + Dyurgerov Gaussian point terms
  unconditionally, but the ext refit that produced the shipped posterior dropped
  both — re-running the fork script as-is will not reproduce the shipped posterior.

## [unreleased] — 2026-06-24 — Phase 2 RFF-SP 2k subsample + extractor --subset flag

- **`outputs/rff_subset_2k.csv`** — canonical 2000-draw RFF-SP subsample for the
  Phase 2 MAGICC-vs-BRICK-Mengel comparison. Stride-5 selection (rff_idx 1,6,11,…,
  9996); deterministic and evenly-spaced across the RFF-SP inventory. Decision
  confirmed by Marcus 2026-06-24 (2k subsample + 1:1 LHS MAGICC member pairing).
- **`extract_pulse_marginals_3brick.py`** — added `--subset <csv>` flag.  Optional
  path to a CSV with `rff_idx` column; filters the 10k per-draw arm files to the
  specified subset before computing weighted marginals. Default (no flag) = full 10k
  (existing behavior unchanged). Subset output named
  `marginals_summary_<stem>.csv` to avoid overwriting the canonical 10k result.
  Validated on 2k: Mengel CO2 medians agree with full-10k to 0.3% (@2100) / 0.6%
  (@2300) — within sampling noise.
- **`extract_fossil_ch4_marginals_3brick.py`** — same `--subset` flag added.
  Output named `marginals_fossil_ch4_summary_<stem>.csv`.

## [unreleased] — 2026-06-17 — LWS seed lock + brick-mengel archived

- **Root cause** of the ~0.4 cm total-SLR drift between Mengel SSP-projection re-runs: MimiBRICK's
  `get_model` draws `lws_random_sample ~ Normal(0.0003, 0.00018)` UNSEEDED on every call. (Diagnosis:
  GSIC/GIS/TE bit-identical, AIS float-noise, LWS the entire delta with mixed signs across SSPs.)
- **Fix:** `build_brick_mengel` now takes `lws=:seeded` (default; fixed-seed LOCAL RNG, `LWS_SEED=2026`,
  reproducible realization), `:central` (0.3 mm/yr mean = MimiBRICK-FM), `:zero`, or `:random` (legacy
  unseeded). Local RNG keeps the global stream (FaIR-member pairing seeds) untouched. Verified bit-identical
  across re-runs; LWS now a single locked value (2.596 cm) across all SSPs (correct — LWS is climate-independent).
  Regenerated SSP / matched / hybrid Mengel outputs (shifts immaterial, sub-0.5 cm).
- **All canonical BRICK versions now have locked LWS:** `main` (BRICK2.0) and `brick-v1.2-vehicle`
  (preBRICK2.0) already seed `Random.seed!` immediately before `get_model` in their canonical drivers
  (obs-driven, flatcube); MimiBRICK-FM uses the `:central` mean; brick-mengel uses `:seeded`.
- **`brick-mengel` ARCHIVED** (annotated tag `archive/brick-mengel-2026-06-17`, branch kept). Frozen final
  state of the calibration/working branch; the Mengel model is canonical in MimiBRICK-FM, and this tag
  preserves the study drivers (MAGICC comparison, CO2/CH4 pulse 3-BRICK, recalibration diagnostics) that
  were never extracted there. Canonical going forward: brick-v1.2-vehicle, main, MimiBRICK-FM.

## [unreleased] — 2026-06-15 — CO2/CH4 pulse→SLR: headline reframed to CH4-as-CO2eq (Marcus)

Marcus: drop the fossil-CH4 variant from the HEADLINE (the co-emitted oxidation CO2 is an instantaneous
pulse, an inexact stand-in — a real fossil pulse spreads the oxidation CO2 over the methane oxidation
lifetime) and express the headline CH4 marginal in **CO2-equivalent (AR6 non-fossil GWP-100 = 27.0)** so
both gases are on cm/GtCO2(eq).
- `marginals_summary_co2eq.csv` — CH4 rows ×(1000/27.0)=×37.037 (exact linear rescale of every quantile/
  mean/component); CO2 unchanged. The physical `marginals_summary.csv` (cm/TgCH4) stays as source of truth.
- `plot_pulse3brick_marginals.py` regenerated → `pulse3brick_marginals.png` now plots CO2 (top row) vs
  CH4-as-CO2eq (bottom row) with the **y-axis SHARED per horizon column**, so the short-lived-forcer
  crossover is visible: CH4-eq Total towers over CO2 at 2100 (~2.2–2.7e-2 vs ~0.5–1.2e-2 cm/GtCO2eq) and
  falls below it by 2300. GWP from a named constant; fossil exclusion noted in the caption.
- `headline_table_co2eq.md` is the headline table (CO2 vs CH4-CO2eq + ratio + per-component); the fossil
  sensitivity stays in `headline_table_fossil_ch4.md` (NOT headline). CH4-CO2eq ÷ CO2 ratio ~2.2–2.3× @2100,
  ~1.4× @2150, ~0.6–0.7× @2300, all 3 versions.

## [unreleased] — 2026-06-15 — CO2/CH4 pulse→SLR: STEPS 5–7 DONE — STUDY COMPLETE

Steps 5 (per-version Wong weights), 6 (paired weighted marginals), and 7 (headline figure) all
complete. The CO2/CH4 pulse→SLR / 3-BRICK-version study is finished through the figure; narrative
is Marcus's to draft.

- **Step 5a/b — per-post baseline l_B (Dangendorf):** `slurm/submit_lB_pulse3brick.sh` (2-task array,
  4 cpu, ~1–2 min each). pre93 via `julia/compute_lB_per_post_v121.jl` (julia_v121, pre-#93 35-col
  posterior, precip_log=false); brick2 via NEW `julia/compute_lB_per_post_brick2.jl` (julia_v2,
  post-#93 posterior, **precip_log=true**, v2.0.0 get_model — a copy of the v121 script with the
  precip log-shim + brick2 defaults). mengel SKIPPED (equal-weighted; no Wong — locked 2026-06-15).
  Outputs Torch `outputs/brick_lB_per_post_{pre93,brick2}.csv` (10000 rows, all finite).
  - **Tried + abandoned:** running `compute_lB_per_post_v121.jl` as-was in julia_v121 — FAILED
    (`ArgumentError: Package Distributions not found`; the pinned v1.2.1 env has no Distributions).
    Fix: replaced the `MvNormal` logpdf with a Cholesky logpdf using only `LinearAlgebra` (stdlib),
    numerically identical. Did NOT mutate the pinned env (no Pkg.add). brick2 unaffected (julia_v2
    has Distributions; left as-is — each version's Wong weight uses only its own (l_FB − l_B), so
    cross-version logl-implementation differences are irrelevant).
  - **Uniformity check (per "suspicious uniformity = bug" discipline):** pre93 l_B is very tight
    (std 1.9, range 364–385) vs brick2 (std 79). NOT a degenerate code path — **9959/10000 unique**
    l_B values; the tightness is real, driven by the pre-#93 posterior's near-constant AR(1) nuisance
    params (rho_gmsl CV 0.4 %, sd_gmsl CV 0.19 vs brick2 0.41) under a *fixed* default-ssp245 backbone
    (the logl scale is set by sd/rho, which barely vary).
- **Step 5d — Wong weights:** NEW `python/apply_wong_weights_pulse3brick.py` (split-CSV adaptation of
  `apply_wong_weights.py`; reuses its Kalman logl / ESS / loaders verbatim). Reads l_FB from
  `{version}_baseline.csv`'s `slr_<year>` 1850–2300 trajectory (cm, re-ref to 2000; verified slr_2000==0),
  merges l_B. **post_idx convention bug caught:** Step-4 cells store post_idx **0-based** (driver does
  `post_idx_1b = post_i + 1`), but `load_posterior`/Julia l_B are **1-based** → fixed with a +1 map for
  the sd/rho lookup and l_B merge, keeping the 0-based cell key in the output. Replaced the coarse grid
  c-tuner with a **bisection** root-solve (ESS_fraction is monotone in c, and the grid over/undershot
  the steep ESS curve). Both arms hit **ESS = 50.0 %** exactly: pre93 c=0.262, brick2 c=0.00857.
  Wong shifts are modest (pre93 total SLR@2100 83.7→83.5 cm; brick2 73.8→77.9). Outputs Torch
  `outputs/wong_weights_{pre93,brick2}.csv` (per-cell w_norm + l_FB/l_B/log_w + keys).
  `--obs dangendorf` (1900–2018, 119 yrs) kept in sync between Julia l_B and the Python l_FB.
- **Step 6 — paired weighted marginals:** NEW `python/scripts/extract_pulse_marginals_3brick.py`.
  Pairs pulse↔baseline on the 4 keys (validate one-to-one; 10000/version/species), differences each
  of {total, ais, gsic, gis, te, lws} × {2100,2150,2300}, ÷ pulse size (CO2 0.01 GtCO2, CH4 1.0 Tg),
  weighted quantiles (pre93/brick2 Wong; mengel uniform) + unweighted for the §0 sanity check.
  Output `outputs/pulse3brick_v145/marginals_summary.csv` (108 rows; committed).
  - **Sanity PASSED:** unweighted total-q50 matches handoff §0 to **0.1–0.3 %** (ratios 0.999–1.003).
    Component means sum to total to machine precision (~1e-14). LWS marginal = 0 everywhere (the
    deterministic landwater add-on cancels in the pulse−baseline difference — correct).
  - **Physics (weighted q50, cm/unit):** pre93 CO2 is **GIS-dominated** (GIS 9.1e-3 of 1.15e-2 total
    @2100; 2.8e-2 of 3.1e-2 @2300 — the pre-#93 GIS pathology). brick2 GIS is tamed (5e-4) and the
    marginal is TE/GSIC-led. mengel has the largest **AIS** (8.99e-4@2100 → 3.78e-3@2300) with a fat
    tipping tail (CO2 mean 4.3e-2 ≫ median 4.7e-3). pre93 AIS marginal is slightly negative (~−1e-4).
- **Step 7 — headline figure:** NEW `python/plot_pulse3brick_marginals.py` → `outputs/pulse3brick_marginals.png`
  (2 rows species × 3 cols horizon; x = {Total, AIS, GSIC, GIS, TE}, grouped bars per version at the
  WEIGHTED median, Total bars carry weighted 5–95 % whiskers). **Grouped median bars (not a stacked
  mean)** deliberately, because the marginals are heavily right-skewed (mean ≫ median in the AIS-tipping
  tail) so a mean-stack misrepresents the central estimate; LWS omitted (marginal≡0). The figure makes
  the version story legible: pre-#93's Total is **GIS-driven** (towering red GIS bar), BRICK-Mengel
  leads on **AIS**, BRICK 2.0/Mengel TE comparable. Labels all from named constants; the caption text
  box is a placeholder for Marcus's narrative. Companion `outputs/pulse3brick_v145/headline_table.md`
  (Total median [5–95] + per-component attribution) committed for the writeup.
- **Canonical outputs (Torch unless noted):** l_B `outputs/brick_lB_per_post_{pre93,brick2}.csv`;
  weights `outputs/wong_weights_{pre93,brick2}.csv`; marginals `outputs/pulse3brick_v145/marginals_summary.csv`
  (committed); figure `outputs/pulse3brick_marginals.png` + `headline_table.md` (committed).

## [unreleased] — 2026-06-15 — CO2/CH4 pulse→SLR: STEP 4 DONE (90k BRICK runs)

Launched + completed the production run (Marcus go). Outputs: `outputs/pulse3brick_v145/{pre93,brick2,mengel}_{baseline,co2,ch4}.csv`.
- **Bug caught at launch + fixed:** the first submit (job 10846724) failed all 9 tasks in 48 s —
  `NPZ.jl: unsupported type U171`. The 2026-06-14 cube seed-provenance addition embedded numpy
  **string/0-d arrays** in the `.npz`, which the Julia reader can't parse. Fix: strip string/scalar
  provenance to a sidecar `cube_*.provenance.json`, keep only `cell_seeds` (int64) in the npz —
  applied to the existing r2 cubes on Torch (data arrays untouched) and to the builder
  (`lhs_climate_v145_meta.py`, FaIRtoFrEDI `c5a7b84`). Re-ran (job 10848541): all 9 COMPLETED, ~2 min/arm.
- **Validated:** 9 CSVs × 10000 rows, fully paired. Unweighted per-unit marginal medians (cm):
  | version | CO2/GtCO2 @2100 | @2300 | CH4/Tg @2100 | @2300 |
  |---|---|---|---|---|
  | pre93  | 1.15e-2 | 3.11e-2 | 7.27e-4 | 5.94e-4 |
  | brick2 | 5.07e-3 | 1.00e-2 | 3.07e-4 | 1.74e-4 |
  | mengel | 4.69e-3 | 1.15e-2 | 2.80e-4 | 2.12e-4 |
  pre-#93 CO2→SLR ≈ 2.3–3× post-#93 (GIS pathology, as expected); CH4@2300 resolvable (1Tg fix worked).
- **Weighting (Marcus 2026-06-15):** primary BRICK-Mengel = EQUAL-weighted; pre93+brick2 = Wong-weighted.
- **Next:** Step 5 Wong (pre93/brick2) → Step 6 weighted marginals (co2 ÷0.01, ch4 ÷1.0; mengel plain) → Step 7 figure.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR: Step-4 prep (P4) + Mengel l_B (P3)

Launch-readiness work while P1's cubes build (Marcus: P4 first, P3 second). Stops short of submitting.
- **P4 DONE** — synced BRICK drivers (`run_mimibrick_pulse_versioned.jl` + the 3 includes),
  the 3 posteriors + medoid central row, and the BRICK metadata to Torch `/scratch`. Wrote the
  9-task production array `slurm/submit_pulse3brick.sh` (idx = version*3 + arm; pre93→julia_v121,
  brick2/mengel→julia_v2; baseline arm `--save-trajs` for Wong; CO2 0.01Gt ÷0.01, CH4 1Tg ÷1.0;
  same `--seed 2026` for pairing) — STAGED, NOT submitted. Torch BRICK smoke (10 cells × 3 versions)
  all pass: closure resid 0.0, and totals **bit-identical to the local smokes** (pre93 5.3789, brick2
  3.2256, mengel 4.4536 m @2300) — cross-platform determinism confirmed.
- **P3 DONE (mechanics)** — `julia/compute_lB_per_post_mengel.jl`: per-member l_B vs Dangendorf for
  the 28-col mengel posterior (build_brick_mengel + medoid + 18 free params; uses `sd_dang`/`rho_dang`
  since the posterior has no `sd_gmsl`). Validated (5 members, finite l_B). ⚠ **OPEN Step-5 decision**
  flagged in the script: the Mengel posterior is already Dangendorf-calibrated, so whether to Wong-weight
  the mengel arm at all (vs equal-weight) is unresolved — await Marcus.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR: prerequisites P1+P2 executed

Executing the two Step-4 blockers from the pre-launch review (Marcus: go ahead with P1+P2).
- **P2 DONE** — `julia_v2` (v2.0.0) + `julia_v121` (v1.2.1) instantiated + precompiled on
  Torch via `slurm/precompile_julia_envs.sbatch` (compute node; login-node instantiate was
  stalling/precompiling — SIGKILL risk). Both verified: `get_model`+`run` OK (v2 SLR2100=102.1,
  v121 99.0 cm). Plots/GR/Qt precompile-fails are benign (headless, unused by the BRICK driver).
- **P1 IN PROGRESS** — paired r2 triplet (baseline + co2-0.01Gt + ch4-**1Tg**) built on Torch
  via `slurm/submit_triplet_r2.sh` (array job, one arm each). Moved to Torch after the local
  background build died untraced; Torch calibration sha256 matches local
  (`03b0368…`) so the realization equals the locally-validated smoke. Cubes land on `/scratch`
  with embedded seed provenance (`cell_seeds` etc.). Tag `_flat2015_r2`.
- The 0.01 Tg CH4 cube is float32-corrupted (see prior entry); CO2 stays 0.01 Gt.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR, 3 BRICK versions: foundations (runbook Steps 0–3)

Built the prerequisites for the CO2 & CH4 pulse→SLR marginal study across three
BRICK calibration versions (pre-#93 v1.2.1 / BRICK 2.0 / BRICK-Mengel), on the
FaIR-v1.4.5 × RFF-SP LHS-10k ensemble. Stopped before the 90k-run Torch launch
(Marcus: foundations-only this pass). Runbook:
`notes/handoff_2026-06-14_co2ch4_pulse_3brick_NEXT-SESSION.md`.

### Added
- **`julia_v121/` — a real MimiBRICK v1.2.1 env** for the pre-#93 arm (the
  `brick-v1.2-vehicle` Manifest pins 1.0.1, so this is a build, not a checkout).
  Pins MimiBRICK git `repo-rev v1.2.1` (sha `94ceca2`) under Julia 1.12; smoke
  passes (build→run 1850–2300, closure 4.4e-16 m). `julia_v121/build_v121_env.jl`.
- **`julia/run_mimibrick_pulse_versioned.jl` — ONE version-aware flat-cube driver
  for all THREE versions** (`--brick-version pre93|brick2|mengel`), one output
  schema (per-component + total SLR at 2100/2150/2300, optional GMSL history for
  Wong). Supersedes the schema-limited `run_mimibrick_flatcube_v121.jl` (components
  at 2100 only) — unified to remove the cross-arm schema-drift risk. pre93 runs in
  `julia_v121` (precip_log=false); brick2/mengel in `julia_v2` (precip_log=true);
  mengel applies the 28-col posterior as 18 free params over the medoid central row
  (mirrors `project_ssps_2100_mengel.jl`). Added NPZ to `julia_v2`.
- **`python/scripts/sanity_battery_pulse3brick.py`** + smoke metadata
  `outputs/smoke25_lhs10k_metadata.csv`. 5-test gate (zero-pulse/cross-process
  determinism, sign-flip, ×magnitude, first-principles, closure) on a 25-cell
  lhs10k-proxy smoke per version → **ALL PASS, gate OPEN**
  (`outputs/sanity_battery_pulse3brick_smoke.txt`). Smoke reproduces the pre-#93
  GIS pathology (dGIS@2100 ≈ 8.1e-3 cm/GtCO2 vs ~4–5e-4 for brick2/mengel; pre93
  total ~3× larger @2300), ×magnitude linear to ~1% (no AIS tipping at 0.01 Gt),
  CH4:CO2 per-unit ratio ~0.055–0.063.

### Corrected (vs the runbook's assumptions)
- **MimiBRICK v1.2.1 already uses `get_model(ssprcp_scenario=…)`**, NOT
  `rcp_scenario=` as the runbook claimed; it ships both RCP- and ssp-named SNEASY
  forcing files (no date suffix) and uses LINEAR precip0 (`precip_log=false`). The
  real v1.2.1→v2.0.0 differences are the date-suffixed forcing files + the
  precip_log reparam. (Forcing is overridden by the cube's GMST/OHC anyway.)
- **The Mengel 28-col posterior cannot be applied via `update_brick_params!`** (it
  lacks the full AIS/glacier/thermal_s0 columns). Canonical path = medoid central
  row for fixed params, then the 18 free params per draw, per `project_ssps_2100_mengel.jl`.
- **`brick_mengel.jl` must be include()d at module scope**, not lazily in a
  function — Mimi's `run(m)` otherwise hits a world-age MethodError on
  `run_timestep_glaciers_mengel`. Loading it is harmless for pre93/brick2 (the
  Mengel component is defined but only instantiated for `--brick-version mengel`).

### Pre-launch review (2026-06-14) — 3 prerequisites before Step 4
Verified sound: lhs10ks cell layout == metadata (incl. seeds); pairing (pre-2030
dGMST=0, @2000=0 → rebaseline cancels); cross-process paired determinism exact;
CO2 0.01 Gt well-resolved (15–30× float32 ULP, ×magnitude ~1%); posteriors all
10000 rows (no off-by-one); closure ~1e-11.
- **P1 — CH4 0.01 Tg cube is float32-corrupted → regenerate at 1 Tg** (Marcus
  2026-06-14). CH4 dGMST decays below the float32 ULP (~2.4e-7 °C) after ~2060
  (nonzero cells: 72%@2075, 34%@2100, 8%@2300); CH4 SLR marginal ratio
  (0.01-cube/1-cube) = 0.97@2100, 1.20@2150, 0.51@2300, **TE@2300 → 0**. 1 Tg CH4
  is ~10× smaller dGMST than CO2-1Gt → well below AIS tipping. Build
  `cube_v145_lhs10ks_pulse_ch4_pos_1tg_flat2015.npz` (FaIR driver, paired seeds),
  marginal ÷1.0; CO2 stays 0.01 Gt ÷0.01.
- **P2 — Torch envs missing.** Only the v1.0.1 `julia` env is on Torch; build
  `julia_v2` (brick2/mengel) + `julia_v121` (pre93) there (instantiate + precompile).
- **P3 — Mengel Wong-`l_B` path missing** for Step 5 (`compute_lB_per_post*` assume
  the 35-col posterior; mengel 28-col needs medoid + 18-free).

### Pending (next session — Step 4 after P1/P2)
- Torch: 3 versions × 3 arms {baseline, co2_pos_001gt ÷0.01, ch4_pos_**1tg** ÷1.0}
  × 10k = 90k runs, partition `cs`. Then per-version Wong weights (own `l_B`) +
  paired marginals + headline figure.

## [unreleased] — 2026-06-13 — BRICK-Mengel post-2018 multi-component extension

### Added
- **Extended ALL calibration targets past Frederikse 2020's 2018 end** with
  reconciled modern products and re-fit, to test the post-2020 Antarctic pause +
  (Marcus's expansion) Greenland / thermal-expansion / glaciers.
  - Data: GRACE-FO JPL mascon AIS+GIS (→2026), GlaMBIE 2025 glaciers (→2023),
    NOAA NCEI thermosteric (→2025), NOAA STAR total (→2024); IMBIE 2023 AIS+GIS
    cross-check (agrees with GRACE splices <0.07cm). `raw/README_modern_extensions.md`.
  - `python/prep_recalib_targets_ext.py` → `outputs/recalib_targets_ext.csv`
    (offset-match splice onto Frederikse over GRACE/obs overlap; per-component end yrs).
  - `julia/calibrate_mcmc_ext.jl` + `run_mcmc_ext_local.sh` + `postprocess_mcmc_ext.jl`:
    per-series AR(1) windows; **dropped IMBIE+Dyurgerov point terms**; total extended
    w/ NOAA STAR (Marcus decisions). 4×500k → 27/28 R̂<1.05.
  - Obs check `julia/posterior_predictive_ext.jl` + `python/plot_postpred_components_ext.py`.
  - High-T glacier melt verification `python/verify_mengel_hightemp_melt.py` (Marcus:
    confirm Mengel melts MOST glaciers at high T) — PASS (99% committed @4°C).
  - Projection A/B `python/plot_ssp_projections_ext_compare.py`; `project_ssps_2100_mengel.jl`
    gained an optional TAG arg (baseline default byte-identical).

### Result
- Extending barely moves the physics (ais_ocean_temperature₀ +0.013); GMSL@2100
  LOWER by 0.8–3.2cm, ~entirely via AIS; high-forcing overshoot vs AR6 persists
  (MICI-threshold-driven, unconstrainable by ~7yr). TE overshoot NOT resolved by
  NOAA steric (+0.51cm@2025). AIS pause not reproduced (warming-driven model).

### Tried / noted
- 4×**100k** with the baseline proposal covariance did NOT converge (25/26 R̂>1.05;
  per-chain logpost spread 6–138 = slow burn-in from a mismatched proposal, NOT a
  bug). Fixed by seeding the 500k from the ext-tuned `adapted_cov_ext.csv`.
- `.gitignore`: exclude the 276MB×4 MCMC chain files (regenerable).

## [unreleased] — 2026-05-30 — Rennels 7-panel SSP2-4.5 SLR + pulse figure

### Added
- **7-panel SLR figure for Lisa Rennels** confirming emission-pulse + BRICK
  results under SSP2-4.5. Left: total GMSLR rel 2005 (median + 75%/90% bands,
  unweighted spread over 841 v1.4.5 configs × 8 BRICK post-PR#93 posteriors).
  Right 2×3: SLR impulse response to a 2020 CO₂ pulse, decomposed into
  TE/GSIC/GIS/AIS/LWS/Total, with BOTH a +0.01 GtC and a +1e-4 GtC arm overlaid.
  - Driver: `python/scripts/rennels/rennels_build_ssp245_cubes.py` — FaIR v2.2.4
    (v1.4.5 cal) SSP2-4.5 baseline + 4 pulse arms (±0.01, +0.02, +1e-4 GtC at
    2020.5, CO₂ FFI), emits **GMST + OHC flat-cubes** (float64 — float32 destroys
    the 1e-4 GtC signal, ~1e-7 °C on ~2.5 °C). Pulse in GtC→GtCO₂ ×44/12.
  - Figure: `python/scripts/rennels/rennels_7panel_figure.py`.
  - Outputs: `outputs/rennels/slr_7panel_ssp245.{png,pdf}`,
    `rennels_pulse_response_summary.csv`, 5 cubes + metadata, BRICK CSVs.
- **Result:** 1e-4 GtC pulse IS resolvable through BRICK in float64; the two arms
  agree to <0.2% at 2150 (linear). Per-GtCO₂ total marginal @2150 = 0.0073
  cm/GtCO₂ (matches memory ~0.0074). TE dominates; LWS ≈ 0 (pre-2019 calib).
- **Sanity:** all 5 paired-pulse tests pass at FaIR level (zero/sign-flip 0.02% /
  doubling 2.0002 / linearity 0.02% / first-principles 0.415 m°C/GtCO₂) AND BRICK
  level (repro bit-identical / sign-flip anti-sym / doubling 2.0000 / linearity
  0.29% / closure Σcomp=total to 1.4e-13 m).
- **Caveat flagged on-figure:** unweighted SSP2-4.5 median runs above AR6
  (69 vs ~50 cm @2100; 132 vs ~68 cm @2150) — consistent with this project's
  hot BRICK posterior (RFF-SP gives ~93 cm @2100), not a bug; per user's
  explicit "unweighted climate+BRICK spread" choice (no Wong importance weights).
- **Absolute-units variant** `slr_7panel_ssp245_abs1em4.{png,pdf}`: right panels
  in metres of SLR per literal +1e-4 GtC pulse (TE ~2e-8 m @2300; direct-1e-4 vs
  0.01÷100 agree <0.2%). For comparison with Rennels' own per-1e-4-GtC numbers.

### Fixed / corrected
- **AIS get_model seed-bug note in CLAUDE.md was overstated** ("uniformly
  non-negative once seeded"). Measured: matched-seed AIS median is slightly
  NEGATIVE at 2050 and 34–56% of draws are negative at all horizons — the true
  small-pulse AIS signal straddles zero. A negative *median* alone is not proof
  of the bug. Demonstrated the actual bug signature: seed-mismatch zero-pert
  (2026 vs 1234) injects a systematic AIS offset (median −5e-4 cm, 100% negative)
  ~100× the true ~5e-6 cm signal. Diagnostic tests added to the note.

## [v2.1] — 2026-05-29 — finalized substack + poster (Group-Sobol H-S)

### Changed
- **Group-Sobol is now the canonical SLR Hawkins-Sutton method** (replaces the
  earlier TreeSHAP/Shapley attribution, which under-counted the emissions axis
  ~3× — 8.6% vs ~27-29% at 2150 — because collinear cumulative-emissions
  features dilute per-feature Shapley credit). Sobol decomposes *grouped* variance
  directly, immune to within-group collinearity, and is importance-weighted.
  Module: `python/scripts/substack/group_sobol_hs.py`; renderers
  `render_hybrid_tipping_split.py`, `paired_figures_hs.py`,
  `poster/hawkins_sutton_panels.py`.
- **Independent model-free cross-check:** a 324,000-run balanced-factorial ANOVA
  (`anova_hs_decomp.py`) reproduces the Sobol emissions/climate/internal shares
  to within ~2 pp at 2150 (emissions 27.0% ANOVA vs 28.9% Sobol), confirming the
  attribution is not a surrogate artifact. Overlay figure `anova_vs_sobol_overlay.py`
  → `outputs/substack/anova_vs_sobol_total_slr.{png,pdf}`.
- **Terminology:** reader-facing figures/captions now say "importance weighted"
  rather than "Wong-weighted" (provenance comments keep "Wong").
- **Pulse SLR figure:** removed the ensemble-mean line from the pulse-SLR panel
  (tipping-corrupted, not pulse-size-invariant); median + 5-95% band retained.
  Pulse GMST keeps its mean (no tipping pathology).
- **Exceedance table caption** corrected to "FaIR v2.2.4 (v1.4.5 calibration)"
  — distinguishes the model version from the calibration posterior.

### Notes
- Superseded TreeSHAP-era H-S outputs quarantined under
  `outputs/quarantine/20260528_treeshap_slr_underattribution/`.
- Decided to keep Sobol canonical and ANOVA as validator; no pulse ANOVA (the
  cross-check's motivation was the emissions axis, which is ~1% / uncontroversial
  for the pulse). See `notes/handoff_2026-05-28b_group_sobol_hs.md`.

## [Unreleased] — v145 end-to-end pipeline

### Added
- **Hybrid total_slr H-S decomposition with augmentation-based V_BRICK + V_seed** (2026-05-27).
  Pure-Shapley failed for SLR: even high-capacity surrogate + p99 outlier clip left
  OOF V_residual at 25-32%, factor 6-47× the pure-seed gold standard. Diagnosed as
  cfg×post interactions + AIS tipping nonlinearity that HistGradientBoosting can't
  capture. Replaced V_BRICK and V_seed in the SLR figure with model-free estimates:
  - V_BRICK: within-cell variance across 10 BRICK posts per cell (90,000 augmentation
    runs: 10,000 v5 cells × 9 extra post_idx via LHS-stratified sampling).
  - V_seed: within-cell variance across 10 seeds per (rff, cfg, post) group (200
    parent cells × 9 extra seeds = 1800 new FaIR runs + paired BRICK).
  Result: V_internal_SLR now declines from 4.6% (2025) to 0.5% (2150), matching
  physical expectation. BRICK is the dominant axis (~42-59%) across all years. A
  residual wedge (20-37%) is labeled as "cfg×post interactions + tipping" since
  those interactions can't be uniquely attributed.
  Files: `python/scripts/substack/hybrid_hs_total_slr.py`,
  `outputs/substack/shapley_hs_total_slr_hybrid.{png,pdf}`,
  `outputs/substack/v5_hybrid_decomp_diagnostic.csv`.

- **v5 noise-isolated H-S figures landed** (2026-05-27).
  Re-ran `shapley_hawkins_sutton.py` against the new LHS-10k_s cubes
  (`cube_v145_lhs10ks_{baseline,pulse_co2_pos_001gt}_flat2015.npz`) and
  the post-PR#93 BRICK posterior. Headline:
  - total_gmst V_internal at 2021 = **97.5%** (canonical H-S near-term
    recovered; v4 had ~0% because LHS-10k was single-seeded).
  - total_slr at 2050: emi 2% / climate 38% / brick 40% / internal 20%
    (first time all 4 axes nonzero — v4 internal was misallocated to
    surrogate fit gap).
  - pulse_gmst: ~100% climate response (matched-seed cancels internal).
  - pulse_slr: BRICK 35-50% of variance across 2050-2150.
  Companion BRICK metadata `outputs/lhs10ks_brick_metadata.csv` LHS-samples
  `post_idx ∈ {0..9999}` (one unique BRICK posterior member per cell);
  the previous `lhs10k_metadata_v145.csv` only used 3 unique post_idx
  across all 10,000 cells, which had been silently under-sampling BRICK
  uncertainty across the entire v4 family of plots.
  Caveat carried forward: TreeSHAP under-attributes BRICK; Owen-Shapley
  re-render (~40 hr Torch) still pending.

### Fixed
- **Hawkins-Sutton nested-ANOVA finite-replication bias** (2026-05-26).
  The variance-decomposition functions in `python/hawkins_sutton.py`
  (`decompose_slr_4way`, `decompose_gmst`) and the substack-side
  reimplementation in `updated_hawkins_sutton.py` were using `ddof=0`
  population variance at every level and were not subtracting the
  propagated within-cell sampling-noise term from each outer-level
  variance. With only 3 seeds × 3 posts per (rff, cfg) cell, the
  ddof=0 estimator was biased down by (n−1)/n = 2/3 at the inner
  level, and the cfg-means carried σ²_seed/n_seed sampling noise that
  was being absorbed into V_climate. Result: total-GMST early-year
  f_internal showed as 65% (canonical Hawkins-Sutton expectation:
  ~100%) and the substack/poster Panel C / D fractions were
  systematically tilted away from V_internal and toward V_climate.
  Fix: unbiased ddof=1 variances at every level via the
  `n_eff/(n_eff − 1)` Bessel correction (handles weighted variance via
  the effective sample size), plus subtract the propagated noise from
  each outer level (V_internal/n_seed off V_climate; V_climate/n_cfg
  plus V_internal/(n_cfg × n_seed) off V_emissions; analogous 4-way
  formulae with V_brick at the bottom). Clipped to ≥0 since
  finite-sample bias-corrected estimates can go slightly negative when
  the true variance is below the noise floor. Affected outputs: every
  Hawkins-Sutton figure in the substack and poster. Substantive
  changes: total-GMST f_internal at 2030 went 62% → 80%; Panel C
  fractions at 2100 went f_clim/f_emi/f_brick/f_int = 80/3/13/3% →
  54/23/23/0%; Panel D at 2100 went 17/3/45/35% → 1/1/81/16%. The
  Panel C/D PDFs in the IEc handoff are regenerated, and the
  discussion paragraph in poster_text.txt has been updated to reflect
  the new fractions.

### Tried and abandoned
- **Lemoine-Traeger tipping-decomposition framing for pulse-marginal SLR
  figures** (2026-05-26). Three active sites used L-T classifiers with
  inconsistent methodology: `gaussian_vs_empirical_slr.py` used a
  pulse-outcome classifier (per-year marginal > 0.3 cm; pulse-size
  sensitive); `extract_lhs10k_smallpulse_summary.py` used a baseline-state
  classifier (`ais_2100_cm > 20 cm`) but it was silently dead because the
  slim CSV didn't carry `ais_2100_cm`; `lemoine_traeger_decomposition.py`
  used baseline-state but had no callers. We initially standardized on
  baseline-state at 20 cm; that revealed that v1.4.5 + post-PR#93 BRICK +
  Wong weighting leaves 88% of cells classified as tipping-prone, so the
  "L-T linear baseline" was a 12%-subset mean (small slice; the L-T
  premium framing was more informative under v1.4.1 where tipping was the
  minority state). Decision: empirical importance-weighted p5/p50/p95
  quantiles satisfy "accurately reflect likely impact + uncertainty"
  while being both threshold-invariant AND pulse-size-invariant.
  `gaussian_vs_empirical_slr.py` + outputs retired to
  `outputs/quarantine/20260526_lt_to_empirical/`. Tipping-conditional
  columns dropped from `extract_lhs10k_smallpulse_summary.py` output.
  `lemoine_traeger_decomposition.py` library kept as a diagnostic
  utility (marked as such in its docstring) for any future revisit of
  the decomposition framework.

### Added
- **v1.4.5 FaIR pipeline end-to-end**: 18 v1.4.5 cubes (9 LHS-10k + 9 ANOVA-18k;
  baseline + 8 pulse arms each) on Torch; new BRICK driver
  `julia/run_mimibrick_flatcube.jl` adapted to the flat
  `(n_cells, n_year)` cube schema. 270× compute reduction vs. the rectangular
  layout that was used in the v1.4.1 era.
- **`run_mimibrick_flatcube.jl`** flat-cube driver with paired closure check
  (Σ components ≡ total SLR to 1e-10 m on the first row).
- **`python/scripts/run_wong_pipeline_v145.py`** end-to-end Wong-weighting
  pipeline matched to the new schema: l_FB from per-arm BRICK CSVs,
  l_B from post-PR#93 posterior, per-arm baseline-weighted CSVs + envelope
  summaries + paired marginal envelopes.
- **`python/scripts/emit_slim_legacy_csvs_v145.py`** writes slim,
  legacy-schema CSVs (bare-year SLR columns + keys + w_norm) so downstream
  plot scripts (`gaussian_vs_empirical_slr`, `slr_band`, `run_4way_slr_decomp`,
  `run_pulse_4way_slr_decomp`) work unchanged on the v145 outputs.
- **Tony component overlay**: added an LWS panel (BRICK ≡ 0 by design
  through the hindcast — Wong et al. 2017 calibration target had LWS
  removed — plus Frederikse 2020 Terrestrial Water Storage overlay).
  Added Frederikse 2020 overlays to the AIS and GSIC panels so the
  20th-century component biases that cancel into matching GMSL are
  visible: BRICK AIS overshoots Frederikse by ~3.3 cm at 1900 (1900-2000
  rise of +3.95 cm vs Frederikse +0.6 cm), GSIC undershoots by ~4 cm at
  1900, GMSL net agreement is within ~0.2 cm — diagnosed bias cancellation.
- **`fair_vs_obs_gmst_ohc.py`** new substack diagnostic figure: v1.4.5
  ensemble-mean GMST vs IGCC 2024 (4-dataset mean), and FaIR v1.4.5
  ensemble-mean OHC vs spliced Zanna 2019 + IGCC 2024.

### Changed
- **BRICK posterior**: swapped pre-PR#93 (`b > v0` in 97.6% of draws) for
  post-PR#93 (`b > v0` in 0%). The new posterior matches Frederikse 2020
  GIS back to 1900. Old posterior moved to
  `data/MimiBRICK/quarantine/20260524_pre_pr93/` with a README.
- **CITATION / .zenodo.json**: updated calibration source from FaIR v1.4.1
  to v1.4.5 and BRICK posterior provenance from v1.0.1 to post-PR#93 joint.

### Quarantined (pre-fix outputs, kept for postmortem)
- `outputs/quarantine/20260524_pre_v145_e2e/` — v1.4.1-era weighted CSVs
  superseded by v1.4.5 outputs:
  - `brick_lhs10k_baseline_to2300_weighted.csv` (LHS-10k baseline, v1.4.1 era)
  - `brick_lhs10k_pulse0p01gtc_to2300_weighted.csv`
  - `brick_lhs10k_pulse_to2300_weighted.csv` (1-GtC pulse)
  - `brick_anova_long_2300_weighted.csv` (13,500-row ANOVA, v1.4.1 era)
  - `brick_anova_long_2300.csv`, `brick_anova_pulse_long_2300.csv`,
    `brick_anova_marginal_long_2300_weighted.csv`
- `data/MimiBRICK/quarantine/20260524_pre_pr93/parameters_subsample_brick.csv`
  — pre-PR#93 posterior (97.6% b > v0).

### Diagnosed but not fixed (deliberate documentation)
- BRICK 20th-century **AIS overshoots Frederikse 2020 by ~3.3 cm at 1900**;
  cancels against GSIC undershoot. PR#93 only added Frederikse GIS to
  calibration; TE / AIS / GSIC still calibrated to Wong et al. 2017 targets
  (pre-ARGO Gouretski 2007 OHC and a less complete antarctic obs basis).
  Fix would require a future PR adding Frederikse AIS/GSIC to the
  calibration target set. Documented in memory
  `project_brick_component_biases_vs_frederikse`.

## [v1.0-poster-agu-chapman] — 2026-05-06
- Initial v1.4.1-era pipeline + AGU Chapman SLR conference poster artifacts.
- LHS-10k conditional-BRICK ensemble (ESS = 7,037).
- Hawkins-Sutton 4-way decomposition of total SLR and pulse-marginal SLR.
- Zenodo DOI: 10.5281/zenodo.20312325.
