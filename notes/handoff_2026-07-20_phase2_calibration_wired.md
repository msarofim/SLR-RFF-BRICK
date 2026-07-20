# Handoff — BRICK-FM phase-2 calibration wired, tuning run in flight (2026-07-20)

Self-contained continuation of `handoff_2026-07-19_brick_fm_improvement_roadmap.md`. A fresh
session should pick up from this + `CLAUDE.md` + the linked memories. Companion:
`notes/prerun_summary_2026-07-20_phase2_calibration.md` (the sign-off doc, now all-resolved).

**Repos/branches:** `SLR-RFF-BRICK@brick-mengel-vnext` (HEAD after commits below),
`MimiBRICK.jl@brick-fm`, `FaIRtoFrEDI@heat-ed-morbidity` (forcing builder only).

## State in one paragraph

The three phase-2 goals Marcus set — (1) fix the last decade of obs, (2) let more Antarctic
variables move, (3) add constraints from obs/physics — are all **implemented and committed**,
and the phase-2 recalibration is mid-launch: a **1M tuning chain is running in the background**
(stage 1 of 2). Everything is reversible up to the production run, which is **held for Marcus's
explicit GO** per the standing directive.

## What Marcus decided this session (all via AskUserQuestion, all implemented)

- **M1 convergence:** accept on the SLR-level deliverable (R̂ 1.003/1.004), not the marginals.
- **M2 pulse rerun:** defer to the phase-2 posterior (don't rerun the 10-GtCO₂ tables interim).
- **A5 σ:** Rignot's own, area-scaled → **1863 ± 118 Gt/yr** (not Mottram's tighter 83).
- **A6 σ:** **N(0.95, 0.10)**, documented as scenario-range+headroom (Xie 2022 has no
  inter-model sd; I declined to fabricate one).
- **M3 total term:** **real Dangendorf 2024 (1900–2021) + NOAA STAR (2022–2024)**, σ from the
  Frederikse ensemble (Dangendorf's own SE corrupted upstream — derived, not emailed).

## Commits (brick-mengel-vnext)

1. `a954701` — M1 gate + Dangendorf/Frederikse untangle + A2/A4/A5/A6 wired.
2. `3c78cc7` — pre-run summary.
3. `cda7ca2` — M3 target rework (Dangendorf+STAR, ensemble σ).
4. `build_overdispersed_starts.jl` commit — stage-2 prereq.

## The two data bugs found (both in memory [[project-dangendorf-frederikse-mislabel]])

1. Repo `dangendorf_2024_gmsl.csv` was **Frederikse 2020** (renamed
   `frederikse2020_gmsl_total.csv`; pipeline relabeled; `dangendorf` kept as a warning alias).
2. **Real Dangendorf 2024's Zenodo `Global.nc` is mis-written upstream** — its GMSL slot holds
   the *barystatic* mean. True GMSL = cos-weighted `HR` from the 704 MB `Fields.nc` (gitignored;
   re-fetch URL in `diag_dangendorf_vs_frederikse.py`); validated vs paper. **Its SE is
   unattributable** (same slot-shift) — that's why the total-term σ is the Frederikse ensemble
   sd, not Dangendorf's own. **Worth reporting to Sönke Dangendorf.**
   Bonus: the record redistributes the full 5000-member Frederikse component ensemble
   (`GMSL_ensembles_F20.nc`) — now used for the correct per-component band σ.

## The phase-2 calibration model (`julia/calibrate_mcmc_ext.jl`, 35→39 params)

- **A2** `λ`, `ais_γ`, `ais_κ` freed under their param_priors.csv paleo marginals. Unidentified
  historically → they sample the prior; the point is uncertainty propagation + medoid de-bias.
- **A4** runoff line sampled as `(T_on=−h0/c, c)` under a rebuilt joint paleo prior
  (`compute_paleo_geo_prior_ton.jl` → `outputs/paleo_geo_prior_ton.csv`; paleo T_on −15.64±5.54,
  r(T_on,c)=+0.64). `h0=−T_on·c` reconstructed per draw. **Traps:** T_on and amp are DERIVED
  params — their `setp!` is skipped and they're set explicitly in `logposterior`; the proposal
  seed maps the old 35-param cov BY NAME (h0's row deliberately dropped).
- **A5** SMB Gaussian on `β_total` (1979–2008 mean, Gt/yr via ρ_ice) vs 1863±118. At the medoid
  β_total=2389 (z=4.45); the target is interior to the paleo-prior(→~1000)-vs-SLR-fit(2389)
  tension, so it anchors precip0 to a physical intermediate. **Watch it doesn't over-fight the
  total-SLR term in the tuning run.**
- **A6** `ais_gmst_amp ~ N(0.95,0.10)`; `coef=1/amp`, `intercept=−AIS_TANT0/amp` (anchor
  T_ant(GMST=0)=−18.435 preserved). Biggest headline-mover: amp 0.95 raises the threshold-
  crossing GMST from ~2.4 to ~3.0 °C, could move "82% crossed by 2100" to a minority.

## Targets (`prep_recalib_targets_ext.py`, rerun; pre-M3 quarantined)

Total = Dangendorf 1900–2021 + STAR 2022–2024 (continuous across the splice). Components stay
Frederikse VALUES but band σ is now the ensemble re-referenced sd (shrinks toward 1995–2005 —
finishes the 2026-07-19 σ fix; zero band inversions). Verified good.

## NEXT STEPS (exact)

**When the tuning run finishes** (bg `bow5b2b5c`, log `outputs/mcmc/log_ext_tuning_seed2026.txt`,
ETA ~1h from ~07:50; check acceptance settles reasonably — it was climbing 0.05→0.08):
1. `julia --project=julia_v2 julia/build_overdispersed_starts.jl outputs/mcmc/chain_ext_seed2026_n1000000.csv`
2. `cp outputs/mcmc/adapted_cov_ext_seed2026.csv outputs/mcmc/adapted_cov_ext.csv` (39-param seed)
3. **Move `chain_ext_seed2026_n1000000.csv` OUT of `outputs/mcmc/`** (it matches the
   `chain_ext_seed*` glob → would pollute the production postprocess). Quarantine it.
4. Report tuning acceptance + whether the new params (λ/γ/κ moved? amp pulled to ~0.95?
   T_on/precip0 shifted by the SMB term?) look sane. **HOLD for Marcus GO.**

**On GO — the 4×2M production run (~4.5h, the run the handoff gates):**
5. `bash julia/run_vnext_production.sh` (4 chains parallel, `--overdisperse`, caffeinate).
6. `julia --project=julia_v2 julia/diag_slr_convergence_by_chain.jl`
7. `julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --accept-slr`
8. **M2 + downstream (task #10):** repoint the pulse/table drivers (they still read the June-13
   non-`_ext` `parameters_subsample_brick_mengel.csv`) to the new posterior; recompute the pulse
   headline at **≤1 GtCO₂** (median, never mean); regenerate the MAGICC-vs-FaIR BRICK cells.

## Still-open Marcus decisions (carried, non-blocking)

- **M6 branch home:** `brick-mengel-vnext` vs moving calibration drivers into MimiBRICK-FM.
- **M7:** fix/flag the broken fork `calibrate_mcmc_mengel.jl` to Tony.
- Report the Dangendorf Zenodo slot bug upstream; JOSS paper; 100/150-yr-from-emission horizons.

## Machine note

Swap-bound (per prior handoffs); read production chains column-selectively (postprocess already
does). Production is 4 parallel chains × 2M under `caffeinate -i`, ~4.5h.
