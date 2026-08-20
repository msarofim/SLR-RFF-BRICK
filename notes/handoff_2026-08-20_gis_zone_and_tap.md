# Handoff — GIS_ZONE groundwork, the tap is LIKELIHOOD-INERT, and a system audit

**Start-here document.** Repo `SLR-RFF-BRICK`, branch **`ladrillo-dev`**.
Predecessor: `notes/handoff_2026-08-19d_aisc_was_misseeded.md`.

**Bottom line. (1) The `GIS_ZONE` "south"→"all" switch is now a FLAG rather than a
source edit, and building it turned up a silent bug that would have bitten the switch:
the `gis_amp` prior's sd/lo/hi were south-only literals with no reference to `GIS_ZONE`,
so flipping the zone would have left the sampler pinned against an upper bound (2.28)
BELOW its own new mean (2.347), with no error. Fixed by deriving all four numbers from
`gis_amp_prior.csv`. The switch is now blocked on one named prerequisite — re-running the
offline A+B fit on the `all` driver — and the gate says so. (2) THE HIGH-BASIN VOLUME TAP
DOES NOT NEED A RECALIBRATION. Its onset bracket is (4.69, 7.81] K GMT; the calibration
window tops out at 1.385 K in 2025, 3.31 K below the lowest onset. The tap is therefore
exactly likelihood-inert over 1900–2025 and belongs on the PROJECTION side, prior-
propagated like `gis_amp` — not as three more sampled parameters costing another ~7 h
calibration. (3) L13 has now MEASURED the basin rate scales for the first time:
mid 0.949 [0.53, 1.60], high 0.268 [0.139, 0.506]. (4) Torch is NOT worth it for the
work actually queued — see §4.**

---

## 1. GIS_ZONE — what landed, and the bug it exposed

`--gis-zone=<south|all|central|north>` is now a flag (commit `09eec0a`), for the same
reason `--adcov=` is: the arm becomes runnable, reviewable in the run script, and recorded
in the log, instead of living as an uncommitted one-character diff.

### 1.1 THE BUG: the amp prior did not follow the zone

`GIS_AMP` was a named constant; its **sd, lo and hi were inline literals** in the `FREE`
`push!` several hundred lines away, with no reference to `GIS_ZONE`:

```julia
push!(FREE, (name="gis_amp", ..., μ=GIS_AMP, σ=0.32, lo=1.51, hi=2.28, islog=false))
```

Those are south/full's numbers. `gis_amp_prior.csv` was named **only in a comment**.

| | south (shipped) | all (design) |
|---|---|---|
| mean | 1.9222 | **2.3470** |
| sd | 0.3181 | **0.5594** |
| [lo, hi] | [1.5102, 2.2847] | **[1.6696, 3.0395]** |

So flipping the zone would have moved the mean to **2.347 while the prior stayed on
[1.51, 2.28]** — an upper bound *below* the mean. The sampler would have been pinned
against a bound it could never leave, and nothing would have raised an error. Same
failure shape as the `L11_NAMES` mis-map: a hand-maintained copy of data that lives
somewhere else, silently wrong once the key changes. All four now derive from the CSV,
keyed on `(GIS_ZONE, GIS_AMP_WINDOW)`.

### 1.2 The `GIS_TBAR` assertion was zone-blind

It compared every zone against a bare `1.963` — south's anchor. It failed safe (loudly),
but blamed `t_gis_zones.csv` drift. Now zone-aware.

Zone anchors, computed from the driver (10-yr `GIS_TBAR_WIN` 2015–2024):
**south 1.9631 · all 2.6543 · central 2.7667 · north 3.2714 K.**

### 1.3 CORRECTION to my own first draft of that gate

I wrote that the `(ell, w)` reparameterisation priors must be re-derived at the new
anchor. **They must not.** `GIS_ELL_MU` and `GIS_W_MU` already derive from `GIS_TBAR`
and re-anchor automatically:

| zone | Tbar | r_s | ell | w |
|---|---|---|---|---|
| south | 1.9631 | 0.014884 | **−4.2074** | **0.93282** |
| all | 2.6543 | 0.019773 | −3.9234 | 0.94943 |

The south row reproduces the shipped log line (`ell ~ N(-4.2074, 1.0)`, `w` centred
0.9328) exactly, which is the check that the transform is understood correctly.

**The real prerequisite is narrower:** `GIS_NATIVE_MU` (α_s = 0.0070727, β_s = 0.0010)
and the five `gis_c1/c0/f/alpha_f/beta_f` prior centres, plus the `GIS_OFFLINE_G0`
reference `--gis-check` scores against, are **physical rate constants fitted against the
SOUTH series**. The `all` driver is **1.352× hotter at the anchor**, so the same α_s
produces correspondingly more melt and those priors would be centred on the wrong
physics. Re-run the offline A+B fit on `all`, update those centres, regenerate the
`--gis-check` reference (**do not widen its tolerance**), then relax the gate branch.

`julia/fit_greenland_only.jl` is **not** that tool — it is the stock/SIMPLE structural
test and is zone-unaware. Locating or rebuilding the offline A+B fit is the first task.

### 1.4 Provenance cost, stated

Deriving `GIS_AMP` from the CSV moves it **1.92 → 1.9221976** (+0.0022, 0.007 sd),
because the shipped line used a rounded literal. An L12 re-run from HEAD is therefore no
longer bit-identical to the shipped L12 — it is 0.007 sd away. Reproduce the exact
shipped L12 from `ab069bd` or earlier.

---

## 2. THE TAP IS LIKELIHOOD-INERT — it does not need a recalibration

This is the main analytical result and it changes the cost of the tap by about 7 h.

The tap's onset bracket, from the Tier-1 literature check, is **(4.69, 7.81] K GMT**.
The calibration window is 1900–2025 and its forcing (`fair_mean_gmst_ssp245harm.csv`)
runs **−0.050 → 1.385 K**, ending at 1.385 K in 2025. **The lowest admissible onset sits
3.31 K above the hottest calibration year.**

So the tap contributes **exactly zero** to the likelihood over the calibration window.
Sampling `(T_on, V_tap, τ)` inside `calibrate_mcmc_ext.jl` would be pure prior
propagation through a 4 × 2 M chain — three more parameters, a re-tune, a re-run, and no
information gained. It belongs on the **projection side, prior-propagated**, exactly as
`gis_amp` already is ("the driver is built ONCE at `GIS_AMP` … prior-propagated into the
projections, not estimated").

**This does NOT contradict "projection-side-only is dead."** That verdict
(`ladrillo_leq_ridge_ceiling` §6) was about the basin **partition**, which *is* visible
in the hindcast — the shipped A+B was absorbing NW and NO+NE mass onto a south driver,
and that needed the recalibration that became L13. The **tap** is a 2300-regime mechanism
the hindcast cannot see. Two different things; the first is done, the second was never
gated on a calibration.

**Consequence for sequencing:** the tap can be scoped and priced entirely offline against
the **existing certified L13 posterior**, with no further MCMC. Do that before
considering any HPC.

**One caveat to carry:** "inert over the calibration window" must be *verified*, not
assumed, once the tap is wired — the natural check is that a tap-on and tap-off
projection are bit-identical to 2025 and diverge only after the onset year. That is the
same nesting-gate discipline that caught the `:basins` mis-projection (19c), and it is
cheap.

---

## 3. L13 MEASURES THE BASIN RATE SCALES — first time

Post-burn, pooled over all four certified chains (thinned, n = 2000):

| basin | log10 s_b | **s_b** | [q05, q95] | offline prototype (ratio vs south) |
|---|---|---|---|---|
| mid (NW) | −0.0226 | **0.949** | [0.529, 1.595] | 4.47 |
| high (NO+NE) | −0.5725 | **0.268** | [0.139, 0.506] | 0.384 |

(south is PINNED at 1.0 — its common mode is exactly degenerate with the shared shape
rates.)

**Two readings, and the second is a live question.**

1. **The high basin's dormancy is confirmed by the calibration, and more strongly than by
   Mouginot.** s_high = 0.268 with q95 = 0.506, so 1.0 is far outside the interval. This
   is an *independent* confirmation of the 0.54 volume-vs-loss dormancy ratio, from the
   hindcast rather than from the sector inventory — and it is the parameter the tap sits
   on top of.
2. **The calibration does NOT reproduce the prototype's 4.47× over-active NW** — it puts
   mid at ~1.0. **ANSWERED by measurement, not assumed: this is the window, and it is
   correct behaviour.**

### 3.1 THE RESTRUCTURE VALIDATES — `diag_l13_basin_shares.jl` on `chain_L13_seed2026`

Rate scales south 1.0000 (pinned) · mid 0.9375 · high 0.2644.

| window | | south | mid | high | total cm/yr |
|---|---|---|---|---|---|
| 2002–2011 | model | 0.583 | 0.213 | 0.204 | 0.0892 |
| | target | 0.592 | 0.207 | 0.201 | |
| | **z** | **−0.18** | **+0.13** | +0.05 | |
| 2012–2018 | model | 0.558 | 0.207 | 0.234 | 0.0623 |
| | target | 0.554 | 0.262 | 0.183 | |
| | **z** | **+0.08** | **−1.09** | +1.03 | |

**Worst |z| on a scored share: 1.09.** Every scored share is inside ~1σ, and the
`s = 1` null — the volume shares **0.456 / 0.173 / 0.371** — is far away, so the fitted
partition has genuinely moved from volume-proportional toward the observed loss split.
**That is the restructure doing exactly what it was built to do.**

The mid basin's residual −1.09 is the two-window tension: one rate scale cannot hit both
0.207 (2002–2011) and 0.262 (2012–2018), so it sits near the first. That, not a bug, is
why the calibrated mid ≈ 0.94 rather than the prototype's 4.47 — the prototype was
exactly-identified on the **cumulative 1972–2018** split, precisely the split the window
trap forbids as a target (Greenland was near balance before ~1995, so early shares divide
by a vanishing denominator and run to 2.272 and −0.911). **The discrepancy is explained
and the calibrator is on the right side of it.**

---

## 4. TORCH — not worth it for what is actually queued

**Recommendation: stay local.** The reasoning, not just the verdict:

* **The bottleneck is serial, and Torch cannot touch it.** An MCMC chain is inherently
  sequential; 2 M iterations take ~5.5 h wall no matter how many cores exist. Torch can
  only run more chains or more *arms* concurrently.
* **The M4 is already fast at this workload, and per-core it likely beats the cluster.**
  `pin_blas_threads` measured 11 h → 2 h17 on the M4 purely from pinning BLAS to 1 thread.
  These runs are single-threaded by design (`OPENBLAS_NUM_THREADS=1`), which is the regime
  where a fast desktop core wins.
* **The queued work is now one arm, not a factorial.** §2 removes the tap from the
  calibration entirely. That leaves at most the `--gis-zone=all` arm: one re-tune (~1.4 h)
  plus one 4 × 2 M production (~5.5 h) — a single overnight run the Mac handles with four
  cores.
* **Setup and data movement are not free.** Julia depot + `julia_v2` instantiate +
  MimiBRICK on the cluster, driver CSVs rsynced, and 2.2 GB × 4 chains per arm landing on
  `/scratch`. The diagnostics then read those full 2.2 GB CSVs, so either they run on
  Torch too or 9 GB per arm comes back over the wire.

**When Torch WOULD be worth it — a concrete trigger, not a vibe:** if we decide to
**co-calibrate the Greenland amp with the basin parameters** across a factorial of arms.
`ladrillo_leq_ridge_ceiling` §5 established that the passing region's size swings 2→172 of
720 across the amp envelope and that **the amp-robust core is EMPTY**, which is the
standing argument *for* co-calibration. A zone × amp-arm factorial is 6–8 independent
4 × 2 M runs; at 4 concurrent chains locally that serialises to ~40 h, and it is exactly
the embarrassingly-parallel shape a cluster is for. **That is the trigger. Until then,
local.**

Per `tony_wong_redesign`: pro/con before new ensembles — this is that pro/con.

---

## 5. SYSTEM AUDIT — what was checked, and what it found

Prompted by two silent bugs in two days. Classes derived from those failures.

**FOUND — Class B (hardcoded constant that should derive):** the `gis_amp` prior, §1.1.
This is the one that mattered.

**FOUND — Class C (defined, checked, echoed, never passed):** `run_l11_production.sh` and
`run_d2_stream_attribution.sh` carry the same unpassed-`$ADCOV` defect fixed in the L12/L13
scripts. **Both are currently harmless** — the file each names happens to equal what the
preference list picks (`adapted_cov_L11tune3_seed2026.csv`), so their provenance labels
were accidentally correct. Latent, not active. Worth fixing when either is next touched.

**A NOTE ON THE AUDIT ITSELF.** My first Class-C detector returned a clean sweep, and the
clean sweep was false: BSD grep on macOS does not treat `\|` as alternation, so the pattern
never matched anything. It was caught only by **mutation-testing the detector against the
known pre-fix script** (`git show 57959ee:julia/run_l13_production.sh`) and noticing it
failed to flag `$ADCOV`. Per `mutation_test_gates`: a gate that passes proves nothing until
it has been shown to fail on a real defect. **Use `grep -E` in this repo's audit scripts.**

**CHECKED CLEAN:**

* **Class E (silent variant fallback)** — `ladrillo_gis_variant` errors on ambiguity and
  `brick_mengel`'s `lws` dispatch errors on unknown values. `ladrillo_used_cols` still uses
  `variant === :stock ? … : AB_COLS`, so a hypothetical *fourth* variant would silently get
  the A+B column list; guarded in practice by `ladrillo_gis_variant`. Hardening
  opportunity, not a live bug.
* **Class D (positional indexing into a parameter layout)** — no hits. The matches are
  `[1, :]` on genuinely single-row CSVs and `D2_BASIS[:, k]` on a real basis matrix.
* **The two shares terms do NOT double-count.** `MOUG_SHARE` scores the whole-sheet
  fast/slow **channel** partition; `GISB_TERM` scores the geographic **sector** partition.
  Different partitions of the same total, and the 3-basin component explicitly preserves
  the output contract — `gis_fast` is the basin SUM, so the whole-sheet term still scores
  the whole-sheet quantity. Verified in `greenland_3basin_component.jl:57` and the
  likelihood block.
* **`--gis-check` inertness** (the `WEDGE_OFF` issue) is already repaired.

**NOT YET AUDITED** — worth a pass when there is appetite: the Python `scope_*`/`diag_*`
layer (the audit above covered Julia and shell), and unit consistency at the m-SLE / cm
boundaries, where `climate-modeling` flags a recurring trap class.

---

## 6. NEXT ACTIONS, in order

1. **Scope the tap offline against the certified L13 posterior** (§2). No MCMC. The
   deliverable is the ssp585/ssp245 2300 ratio as a function of (T_on, V_tap, τ) with
   s_high = 0.268 fitted rather than assumed, scored against the 7.9–31.9× literature band.
2. **Locate or rebuild the offline A+B Greenland fit**, then re-derive it on the `all`
   driver to unblock `--gis-zone=all` (§1.3).
3. Decide on L13 promotion (still open from 19d; L12 canonical at 45.53 cm meanwhile).
4. Only if a zone × amp factorial is bought: stand up Torch (§4).

**Open decisions for Marcus:** L13 promotion; whether the D2G/D2S arms get re-run
(bounded at ~2 % of the steric effect); and whether L13's mid-basin −1.09 z
against the 2012–2018 window is worth a second rate-scale knob (it is the only scored
share outside 0.2σ).
