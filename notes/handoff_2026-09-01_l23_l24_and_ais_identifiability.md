# Handoff — the glacier ratchet is gone, L23 is champion, and Antarctic amplification turns out to be prior-dominated

> ⛔ **SUPERSEDED TWICE. Do not start here — start at `handoff_2026-09-01c_readers_gates_and_the_amp_error_bar.md`.**
> This handoff's headline, that the glacier-law change moved Antarctica, is **REFUTED**: the law
> is inert in the calibration likelihood (a null WITH power at 4–5 orders of headroom) and L23
> also changed proposal covariance, so the 2x2 was never one variable. See
> `handoff_2026-09-01b_adcov_and_the_parquet_migration.md` §2–3 and `handoff_2026-09-01c_readers_gates_and_the_amp_error_bar.md` §1.
> Its "13+ commits UNPUSHED" is also stale — everything is pushed as of 2026-09-01.

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, HEAD **`f969e92`** plus one
outputs commit. Written 2026-09-01, continuing
`handoff_2026-08-31g_magicc_climate_arm.md`.

**⭐ FIRST STEP NEXT SESSION (Marcus): SCOPE THE SKEWED PRIOR.** See §7.

⚠ **Two repos touched. `FaIRtoFrEDI` has 3 unpushed commits on `heat-ed-morbidity`** — the
MAGICC wide-CSV builder and the ZJ docstring fix landed on an unrelated feature branch because
that was the checked-out branch, and Marcus has not ruled on moving them. `facts` and
`MAGICC/slr-refresh` were read-only; the standing "don't push those" instruction holds.

---

## 1. WHAT CHANGED IN THE MODEL

**The melt-only glacier ratchet is gone** (`a0155bf`). Replaced by a FLOORED equilibrium plus
bounded regrowth at R = 1:

    S_eq = max(a(1 - exp(-b(T - T_off))), 0)      # the FLOOR
    dS   = min(kappa*|T - T_eq|^nu, 1) * (S_eq - S)   # sign kept, not discarded

The floor is what makes it safe: `S_eq` goes negative below `T_off` on **12.9 %** of block x draw
cells at vvLN/2300 on our own climate (47.6 % on MAGICC's), so unclamping without flooring would
regrow glaciers PAST their 1850 extent. MAGICC's own tabulated equilibrium has no negative branch
and a positive 27.6-135.9 mm floor, so the one comparator that regrows regrows toward a floor too.
Because `mult` is capped at 1 the step is a convex combination of S and S_eq, so **boundedness is
structural, not a second clamp**.

R = 1 is a STATED CONVENTION in a named constant, not a fitted quantity — removing the clamp
moves the hindcast by 0.014 cm = 3 % of the gsic target's median sigma, so no refit can inform it.

**Changed in all four places that carry the law together** (2 Julia components, `integrate_N` in
`d0_glacier_shootout.py`, and the pricing scope) because `validate_glaciers_nu3.jl` checks Julia
against the python at 1e-9 — moving one side would make that gate hide a divergence instead of
testing it. Port validation passes on both amp bases at ~5e-13.

**A passing port gate cannot show the change is LIVE** (both sides moved), so
`python/validate_glacier_floor_regrowth.py` states the four properties the change actually claims.
The load-bearing one: **on a monotonically warming path the new and old laws are BIT-IDENTICAL
(0.000e+00)**. The floor BINDS where tested — driven to -3 K the unfloored equilibrium reaches
-1.045 m while the stock stops exactly at 0.

**Delivered as priced.** Glacier regrowth at 2300: vvLN **-0.15 cm**, vvML **-0.14 cm**, ~0
elsewhere — against a pre-computed prediction of -0.20 / -0.17 after flooring.

---

## 2. ⚠ THE FINDING THAT MATTERS MOST: THE GLACIER LAW IS NOT INERT ON ANTARCTICA

Refitting under the new law moved **AIS@2300 by +66 cm at ssp245** while the glacier component
moved **0.05 cm**. A 2x2 separates the two changes that landed between L21's chains and L23's —
my glacier law (`a0155bf`) and the L22 steric AR(1) marginal cap (`abd308d`), which **I had
missed entirely** when I first called this sampler wander:

`ais_gmst_amp` pooled posterior median, prior N(1.09, 0.10):

| | old glacier law | new glacier law |
|---|---|---|
| **pre** steric-cap | **L21 0.9455** | — |
| **post** steric-cap | **L22 0.9434** | **L23 1.0865** · **L23b 1.0850** |

* steric cap changed, law held → **0.0021**. Not the cause.
* law changed, cap held → **0.1431 = 1.43 prior sd**. The cause.
* RNG only (L23b) → **0.0014**. Sampler noise negligible.

At SLR level: between-refit reproducibility **4.93 cm**, against a **66.04 cm** L21→L23 gap.

⇒ **A glacier modelling convention was setting Antarctic amplification.** Under the old law the
likelihood pulled amp 1.45 sigma BELOW its prior; under the new law it sits on the prior. Every
earlier claim in that session that the change is "provably inert on warming paths" was about the
glacier OUTPUT at FIXED parameters and does **not** survive a refit.

⚠ **METHOD NOTE.** Between-chain spread WITHIN one refit is a BAD proxy for between-refit spread
of the POOLED estimate: 34.35 cm within-L23 chain-median range against 4.93 cm between refits.
Do not size a reproducibility claim off the within-run range in either direction.

---

## 3. AMPLIFICATION IS PRIOR-DOMINATED, AND NO OBSERVATION CAN FIX IT

`antarctic_icesheet_magdep_component.jl:165` with the calibrator's `1/theta` mapping gives

    T_antarctic = A * GMST + TANT0 ,   TANT0 = -18.435 C FIXED

so **A is the regression slope of Antarctic surface temperature on GMST** — and it only ever
multiplies the ANOMALY. Its footprint is proportional to GMST: ~0.5 C where the observations are,
3-8 C where the answer is. The shift that moves AIS@2300 by 66 cm perturbs Antarctic temperature
by **0.083 C** over the existing SMB term's window and precipitation by **0.52 %**.

Option **B** (give the likelihood a term that can see A) was therefore MEASURED AND REFUTED
before being built (`no_power_null`). Slope se against the prior sd:

| window | sigma_obs 0.4 | 0.6 | 0.8 |
|---|---|---|---|
| 1979-2024 | 0.271 | **0.407** | 0.542 |
| 1957-2024 | 0.200 | 0.300 | 0.400 |
| 1850-2024 (longer than any record) | **0.119** | 0.179 | 0.239 |

Every cell loses to a 0.10 prior. And the other candidates are closed: **IMBIE was deliberately
removed** from this likelihood in June to avoid double-weighting; an **SMB term against Rignot
2019 is in the likelihood NOW** and does not identify A; **paleo** would constrain EQUILIBRIUM
amplification where the model needs the TRANSIENT coefficient.

**Confirmed at both widths** (this is the vindication of F): posterior sd / prior sd =
0.97 / 0.97 / 0.99 at sigma 0.10 (L21/L22/L23) and **0.95 at sigma 0.180 (L24)**. The likelihood
adds nothing at either width.

---

## 4. WHAT WAS DECIDED AND DONE

* **L23 PROMOTED to champion** across all six modules (2026-09-01, Marcus), snapshot frozen at
  `benchmark/reference/L23/`, reasoning recorded in `champions.json`: it adopts the position that
  the ratchet was manufacturing the old AIS amplification constraint.
* **F APPLIED** (`165a860`): `AMP_SIGMA` 0.10 → **0.180**, the measured between-model spread
  (34 CMIP6 models: ssp245 0.194 / ssp585 0.177 / pooled 0.180; an independent 41-model DECK
  1pctCO2 ensemble agrees on the CENTRE ~1.09). Bounds are mu+-3sigma so they widen with it;
  `--amp-sigma=` reproduces the 0.10 arm exactly for a controlled A/B.
* **G WITHDRAWN.** Marcus: reporting three values for the user to choose between is the model
  developer's job left undone. He is right; determining the distribution IS the deliverable.

**L24 (the F refit) results.** Chains clean, structure identical to L23.

| | L23 (sigma 0.10) | L24 (sigma 0.180) |
|---|---|---|
| amp posterior sd / prior sd | 0.99 | 0.95 |
| AIS@2300 within-chain sd | 93.06 | **99.47** (x1.07) |
| AIS@2300 pooled median | 201.85 | **189.18** (-12.7) |

⚠ **A 1.8x wider prior produced only a 1.07x wider AIS band.** Amplification dominates the
between-VINTAGE SHIFT but is NOT the dominant term in the BAND. I conflated those when
recommending F. F is still right — a prior-dominated parameter should carry its measured width —
but it does not transform the band, and the -12.7 cm median move is larger than the amp shift
alone buys (3.9 cm), so other parameters moved too. **Not decomposed.**

---

## 5. ⚠ MISTAKES I MADE — read these, they are the expensive ones

1. **Ran the first L23 refit with the WRONG FLAGS**, omitting `--gis-ordered --gis-basins2`
   (recorded in `memo_2026-08-23_greenland_module.md:372`). Three hours of chains produced an
   `:ab` Greenland — a SECOND moved axis. Quarantined at
   `outputs/quarantine/20260831_l23_missing_gis_flags/` with a README. **Verify the flag set with
   a 4000-iteration smoke whose column set is diffed against the predecessor BEFORE launching.**
2. **Claimed "verified identical chain headers" on a grep that could not show it** — I grepped
   `gis_k_mid|basin`, which cannot match `gis_s_high`, the ONE column by which the runs differed.
   A partial check reported as a complete one, and it is what would have caught mistake 1.
3. **Called the AIS move sampler wander** and leaned toward the flattering reading (L21
   unequilibrated). The 2x2 refuted it. I had also **missed that two calibrator changes landed
   between the runs**, not one.
4. **`rc=$?` in my launch scripts was a lie** — `$(date)` runs before `$?` expands, so the
   reported code was date's, always 0. Four L23b chains that died were all reported `rc=0`.
   The file-count and `[STRUCTURE]` gates are what actually caught things.
5. **Built the regeneration pipeline backwards from the plot scripts**, so four real producers
   were missing and each surfaced only when its consumer ran (`slr_convergence`,
   `vv_model_comparison`, `ladrillo_model_comparison`, the UNTAPPED SSP deliverable). Also
   `postprocess` exits 0 when it REFUSES the canonical write — hence the `[POSTERIOR]` gate.

---

## 6. SWEEP FINDINGS (2026-08-31, `3bf3b65` and around)

Fixed: a constant defined in the SECOND-included file that would throw `UndefVarError`;
my own validator's `import` running the entire d0 shootout and overwriting its outputs;
`scope_glacier_regrowth.py` reconstructing "shipped" with the retired law; a validator header
documenting an invocation that cannot work; two `intersect()` scans that could silently narrow.

**The gate-verdict contract had THREE hardcoded copies** of the accepted set — including one
function-local inside `ladrillo_figs.py`, the module the other two now import it from. So the new
`[OHC-OFFSET]` gate, which had PASSED, killed three consumers in sequence. Now one definition,
`ladrillo_figs.GATE_VERDICTS_OK`, with `DOES-NOT-CANCEL` deliberately absent.

**Found, NOT fixed — two factual errors in L21's declared provenance**, which feed figure
captions: `ladrillo_figs` says "8 chains" where 4 exist; `PROV` in
`plot_postpred_components_ext.py` says "20 marginals unconverged" where its own log says 18.
Left for Marcus: they are declared facts about a champion.

**Also found:** `outputs/d0_glacier_shootout.csv` did not reproduce from its own code even at
HEAD — its `Gfair` cells predate the calib 1.6.0 migration. Regenerated deliberately; the
structural conclusion (N beats M, AIC 12 vs 31) is unaffected.

---

## 7. ⭐ OPEN ITEMS — the skewed prior is FIRST (Marcus 2026-09-01)

1. **⭐ SCOPE THE SKEWED PRIOR.** The one substantive improvement left. CMIP6's amplification
   distribution is **right-skewed** and the Gaussian F installed does not capture it:

   | | p17 | median | p83 |
   |---|---|---|---|
   | CMIP6 empirical (34 models) | 0.934 | 1.095 | **1.348** |
   | N(1.09, 0.180) | 0.923 | 1.090 | **1.267** |

   Upper half-width 0.253 vs lower 0.161 — a **1.57x asymmetry**. The Gaussian reproduces p17 and
   **understates p83 by 0.081**, which at 386 cm/unit is worth **~31 cm at 2300**. Since the AIS
   response is CONVEX in amp, that upper tail is exactly where the risk is, and Marcus's own
   standing rule prefers empirical percentiles over `mean +- sigma` on skewed quantities.
   ⚠ **It changes the prior's FORM, not one constant** — the sampler's proposal and the mu+-3sigma
   bounds logic both assume a Gaussian. Scope it; do not bolt it on. Per-model values are behind
   `python/scope_ais_amp_law_form.py`.
2. **Does L24 get the pipeline and the benchmark?** ~2 h. Expected outcome is a slightly wider
   band and a lower median, NOT a fit improvement — so it mostly confirms.
3. **Promote L24?** Same physics as the champion, honest prior width. Not done; Marcus's call.
4. **Why did the OLD law displace amp's CENTRE but not its WIDTH?** L21/L22 sit 1.45 sigma below
   the prior at full prior width. A likelihood that shifts but does not sharpen is an odd
   signature and nobody has explained it. This is the mechanism behind §2 and it is unexplained.
5. Inherited and untouched: the phantom `wf*e` FACTS files; the `ais@2300` CONTROL exceedance;
   `scope_ladrillo_vs_brick20_scorecard.py` has no L21/L23 run; `plot_ssps_gsic_wr_vs_mengel.py`
   still carries the extA108 arms; `--gis-check` hardcodes REF values that live in a CSV.

---

## 8. NON-OBVIOUS STATE

* **Five vintages of chains on disk, ~43 GB.** `L21` (old champion), `L22`, `L23` (CHAMPION),
  `L23b` (reproducibility replicate, seeds 3026-3029), `L24` (widened prior). Plus the
  quarantined mis-flagged run at 8.6 GB. 220 GB free.
* **`--overdisperse` now has a REPLICATE SEED BANK** (`a6fd634`): seeds 3026-3029 map onto the
  SAME start rows as 2026-2029, so a replicate differs only in the RNG stream. Canonical seeds
  untouched.
* **The canonical launch line**, verified:
  `julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl 2000000 <seed> --tag=<T>
  --gis-ordered --gis-basins2 --overdisperse`, BLAS pinned to 1 thread, 4 chains, ~170-175 min.
* **`postprocess` needs `--accept-slr`**, and `diag_slr_convergence_by_chain_ladrillo.jl --tag=<T>`
  must run BEFORE it. 17-19 parameter marginals fail R-hat on every vintage; this is the
  documented ridge, and acceptance is on the DELIVERABLE (Marcus 2026-07-19).
* **The MAGICC wide CSVs are 121 MB and UNTRACKED** in `FaIRtoFrEDI/magicc_comparison/processed/
  vv_wide_20260831/`; `build_magicc_wide_vv.py` rebuilds them from the sha256 in `PROVENANCE.md`.
* ⚠ **macOS bash 3.2**: no `wait -n`, and `pgrep -fc` is not a valid flag. Both bit me.
* **`ais_gmst_amp` sensitivity**, measured: 78 cm/unit @2100, 178 @2150, **386 @2300**.
