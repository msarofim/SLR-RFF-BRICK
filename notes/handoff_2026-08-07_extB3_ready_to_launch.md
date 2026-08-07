# Handoff 2026-08-07 — extB3 implemented & smoke-passed; tuning launch pending; name → BRICK-F*

**Self-contained pickup:** this note + `notes/memo_2026-08-05_mengel_a0_results_and_recalib_options.md`
(§3e = D0 shootout results, §5-D0 = the decision menu, now RESOLVED — see §2 below) + memory
`project_brick_mengel_vnext_recalib` + `CLAUDE.md`. Branch **`brick-mengel-vnext`**, 48 commits
ahead of origin, unpushed. Nothing is running. The 500k tuning chain is one command away (§3).

---

## 1. Where things stand (one paragraph)

The D0 offline shootout (2026-08-06/07) settled the glacier structural question: the ETCW/regional
driver (**Option D, T_glac**) fixes the decadal flow shape (+10 logL; the Gobs control proves it is
the regional signal, not obs wiggles) and **dissolves the deep-offset pathology** — the 0.20 m
committed-at-1850 demand was the GMST driver compensating for missing regional warming; the
glacier-frame self-consistent solution (a 0.383, b 0.286, T_off −0.96 glacier-K ≈ −0.60 global-K,
inside amplified PAGES-2k LIA minima) needs only 0.092 m committed and passes inventory + the full
GlacierMIP3 ladder. **ν is not identifiable from history** (rails to 0 under the flow likelihood in
every configuration) but ν ∈ [0.5, 2] at that point passes ALL pre-registered gates — the only
configurations ever to do so — buying S(1900) compliance and the AR6-family scenario spread (dead at
ν = 0). Marcus locked the design (§2); the new component + calibrator are implemented, port-validated
(4/4, machine precision), and smoke-tested (50 iters, accept 0.36, finite start). extA108 remains
canonical until extB3 is accepted; the CH4/CO2 pulse arms stay parked until then.

## 2. Decisions locked (Marcus, 2026-08-07 session)

1. **Glacier driver = T_glac** (`data/observations/t_glac_hadcrut5.csv`: HadCRUT5.0.2.0 analysis ×
   GTN-G 2023 region polygons × GlaMBIE year-2000 area weights, scope excl-r5-incl-r19 = V=0.290
   scope; pre-1898 gaps filled per-region from global, `fill_frac` column) — observed through 2024,
   then **amp_g × GMST anchor-preserving splice (11-yr anchor 2014–2024)**.
2. **amp_g = 1.8** (GlacierMIP3 glacier-area warming ratio). The historical fit gives 1.56–1.63 —
   retained as a documented sensitivity alternative, not the default.
3. **Transient = Nauels-2017 single reservoir** dS/dt = κ·(S_eq−S)·max(T−T_eq(S),0)^ν, replacing the
   2-τ fast/slow split (which existed to fake the onset behavior driver+ν now supply mechanically).
   S_eq stays Mengel's exponential (GlacierMIP3 fits that form to its own committed ladder).
   **ν = 0 nests Mengel single-τ exactly** (κ = 1/τ).
4. **ν prior N(1.0, 0.5) on [0, 2.5] — projection-informed BY DESIGN and labeled as such.** The
   hindcast cannot identify ν; the prior center comes from the D0 gate table (spread needs ν ≳ 0.5;
   SSP2-4.5 level overshoots AR6's likely range beyond ν ≈ 1–1.5; S(1900) best near 1). Writeup
   honesty requirements: state "prior ≈ posterior for ν", and always report the **ν = 0 nested
   reference arm** (nearly free) so the exponent's effect is explicit. Precedent check (receipts):
   Nauels 2017 fit (κ, ν) to Marzeion transient projections (Table 2: κ 0.0079–0.0131,
   ν 0.096–0.445); FRISIA v1.0 (Ramme 2025, GMD 18:10017) set p = 1.5 to match AR6 — **no published
   emulator pins this exponent from physics or history**; importing it via a labeled prior is the
   field's universal practice, adopted knowingly (the A3-line discussion).
5. **Clamp = melt-only ratchet** (no regrowth; 0^0 = 1 makes ν=0 the two-way Mengel limit). An
   explicit irreversibility assumption that binds only in strong-mitigation projections; the
   two-way variant κ·(S_eq−S)·|T−T_eq|^ν is the sensitivity arm if regrowth ever becomes load-bearing.
6. **Glacier-frame priors**: gic_b re-centered 0.52 → **0.29** (= Mengel's published global-frame
   0.52 ÷ amp 1.8; leaving 0.52 would pull b toward re-saturation); gic_T_off keeps N(−1.0, 0.5)
   (already the glacier-frame value); gic_a keeps N(0.45, 0.08); κ sampled as log10(κ),
   N(−1.975, 0.65) on [−4, −0.5] (centered on Nauels's mean-set 0.0106).
7. **Early-century (1900–1920) σ treatment: deferred to tuning evidence.** The residual ~2 cm of
   target melt in 1900–1920 sits exactly on the Marzeion-2015-derived segment Roe 2021 calls an
   initialization artifact, and precedes the HadCRUT5 ETCW ramp (~1918). Run extB3 with target σ
   as-is first (the full calibrator likelihood adds the Dangendorf total term the offline objective
   lacked); pre-1940 σ inflation (×2) is the documented fallback if the chain camps on the
   wiggle-tracking mode (recognizable as: σ_gsic collapsing toward its floor + gic_nu piling at 0 +
   S(1900) > 40 mm).
8. **GIS regional driver = separate workstream after extB3** (`python/diag_gis_regional_driver.py`:
   GIS melt rate r = +0.71 vs Greenland-region T, +0.16 vs GMST; Greenland cooled −1.8 °C/century
   1940–90 while global warmed; r05 series already saved in `t_glac_regions_hadcrut5.csv`).
   TE needs no regional-T fix (OHC story); AIS already has its treatment (A6).
9. **Name: leaning BRICK-F\*** — see §7.

## 3. Next action: the extB3 tuning run

```bash
cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK && julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 500000 2026 --tag=extB3
```

~26 ms/iter post-compile (smoke timing) → **≈ 3.5–4 h**. Then evaluate the chain (2nd half) against
the pre-registered gates before any production talk:

| gate | criterion |
|---|---|
| A2 inventory | gic_a − S_raw(2000) within N(0.290, 0.060), \|z\| < 1 |
| A2b / S(1900) | S_raw(1900) in 10–30 mm |
| GlacierMIP3 ladder (evaluation-only, never in the likelihood) | committed % of 2020 mass at glacier-T = 1.8×{1.2, 1.5, 2, 3} K inside [15–55], [20–64], [43–76], [60–85]; lit central 39/47/63/77; sens(1.5→3K) vs ~85 mm |
| scenario spread | glacier ΔS@2100 (rel 1995–2014) SSP1-2.6→5-8.5 spread in 4.5–13.5 cm (AR6 medians 9/12/18) |
| bounds | gic params interior (>2% of range from lo/hi); watch gic_nu piling at 0 |
| mixing | acceptance ~0.234 plateau; `ess(..., maxlag=size(arr,1))` — NEVER the default maxlag |

Gate machinery: the D0 formulas in `python/d0_final_selfconsistent.py` (ladder, spread, splice) apply
directly to chain draws — a small per-draw evaluation script is the first TODO of the next session
(adapt from the d0 script; no new math). If gates pass → rebuild `overdispersed_starts.csv` +
`adapted_cov` from the extB3 tuning posterior (two-stage launch; extA108-era starts sit in the old
railed region and the file will fail the pn0 column check anyway) → production 4 × 2M over-dispersed,
R̂ gated on SLR@2100/2150 + the glacier-spread deliverable.

## 4. What was built this session (all committed on brick-mengel-vnext)

**Data prep (Option D):** `python/build_t_glac.py` → `data/observations/t_glac_hadcrut5.csv`
(+ per-region `t_glac_regions_hadcrut5.csv`, provenance sidecar, `figures/t_glac_vs_gmst.png`).
Raw inputs: `GlacReg_2023.zip` (tracked, DOI 10.5904/gtng-glacreg-2023-07) +
`HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc` (32 MB, **untracked — re-fetch URL in
`data/observations/raw/README_modern_extensions.md`**).

**D0 shootout:** `python/d0_glacier_shootout.py` (6 cells), `python/d0_final_selfconsistent.py`
(SC solve + ν ladder), outputs `d0_{glacier_shootout,b_toff_profile,c_needle_threading,
e_nu_kappa_map,_final_selfconsistent}.csv` + two figures. `python/diag_gis_regional_driver.py` + figure.

**extB3 Julia:** `julia/glaciers_nu_component.jl` (new component; driver param renamed
`glacier_surface_temperature`); `julia/brick_mengel.jl` gained `build_brick_nu` / `update_brick_nu!`
/ `set_glacier_forcing!` (old Mengel paths untouched for provenance); `julia/calibrate_mcmc_ext.jl`
rewired (T_glac driver block; gic FREE block a/b/T_off/log10κ/ν; KAPPA_IDX derived-param; θ0 gic
starts at prior centers; ADCOV prefers `adapted_cov_extB2_seed2026.csv` with 39-param name-mapping,
glacier rows fresh diagonal; NP 29→28, NK 38). Validation: `julia/validate_glaciers_nu.jl` +
`python/validate_glaciers_nu_compare.py` → `outputs/validate_glaciers_nu.csv`, **4/4 PASS**
(Julia↔Python 1e-16 m; ν=0≡Mengel 4e-19; swap bit-clean under matched glacier).

## 5. NOT yet done (post-tuning work — do not forget)

- **`postprocess_mcmc_ext.jl` still expects the old param names** (gic_T_lia/f/tau_*) — update
  before postprocessing any extB3 chain. Also mind its `chain_ext_seed*` glob vs the extB3 tag.
- **Every projection/diagnostic driver still calls `build_brick_mengel`/`update_brick_mengel!` and
  knows nothing of T_glac** (`project_ssps_components_2300.jl`, `posterior_predictive_ext.jl`,
  `diag_*`, pulse drivers, `weight_and_project_brick_fair.jl`, …). Repoint to `build_brick_nu` +
  `set_glacier_forcing!` AFTER tuning acceptance. Projections past 2026 need the T_glac splice
  extended (amp 1.8 × the scenario GMST, same anchor convention — for projections the anchor stays
  the 2014–2024 obs window).
- At acceptance: quarantine extA108 per convention; regenerate B1/B2 comparisons; re-run CH4/CO2
  pulse arms and measure the delta (glaciers ~1–1.5% of the pulse marginal — produce the number).
- Rename rollout (§7) atomically at acceptance: provenance labels, figure captions, walkthrough doc.
- Optional arms queued: Berkeley-Earth cross-check of T_glac; |·|^ν two-way clamp sensitivity;
  mass-loss-share weights (computed, near-identical); space-for-time ν estimate from GlaMBIE
  regional rates vs regional excess (the one genuinely observational ν route — mini-project).

## 6. Non-obvious state / traps for the next session

- **Frame contract:** all gic_* parameters are GLACIER-FRAME (per glacier-area K). The component's
  driver param is deliberately named `glacier_surface_temperature` so `set_forcing!` cannot reach it;
  feeding raw GMST anywhere under-responds by the amplification factor. Global-frame equivalents for
  sanity checks (via the HISTORICAL fitted amp ≈ 1.6, which is what the D0 solve used — not the 1.8
  projection value): b_glob = b_glac × amp ≈ 0.286 × 1.6 ≈ 0.46 (Mengel-family), T_off_glob =
  T_off_glac ÷ amp ≈ −0.96/1.6 ≈ −0.60 (PAGES-2k-range).
- **AIS consumes the glacier path** (`global_sea_level` → Δ_sea_level forcing in the DAIS component)
  — any A/B across glacier variants must MATCH glacier output or AIS differences (~0.3 mm) are the
  coupling, not a bug. (validate_glaciers_nu.jl V3 does this with f=1/τ-matched Mengel.)
- ν=0 has 0^0=1 semantics → the nested limit allows regrowth; any ν>0 with the clamp does not.
  Family discontinuity in the regrowth regime only; never binds in the hindcast.
- Old MAP (`calib_full_joint_params.csv`) gic values are OLD-FRAME — θ0 special-cases `gic_*` to
  prior centers. Do not "fix" that back.
- fair_mean_gmst_ssp245harm's 1850–1900 mean is −0.0000, so the obs T_glac (rel 1850–1900) and the
  FaIR frame align without adjustment — verified in D0, do not add a shift.
- Smoke-test convention: `--tag=extB3smoke`, then DELETE the junk chain + adapted_cov.
- Shell cwd resets between calls — `git -C` / absolute paths.
- Pre-1992 AIS target = Frederikse's constant-rate prior (Adhikari 2018), so early AIS "fit" is
  fit-to-prior; unchanged this session.

## 7. Naming — leaning **BRICK-F\*** (Marcus, 2026-08-07)

**F** = FaIR-forced (designed to run on FaIR, no SNEASY anywhere; the joint free-forcing
alternative was tested and REJECTED 2026-08-01). **\*** = the wildcard over every departure from
the approved Tony Wong MimiBRICK v2.0.0 — which makes the name's definition the delta list:

1. **Forcing:** FaIR GMST + OHC obs-driven override (fixed prior, never re-inferred from SLR).
2. **Glaciers:** WRB single-reservoir → Mengel-2016 equilibrium + Nauels-2017 ν transient
   (`glaciers_nu`), driven by observed glacier-area temperature + 1.8×GMST splice (Option D).
3. **Antarctic:** transient GMST→AIS amplification sampled with anchor preserved (A6; replaces the
   hard-coded equilibrium 1.196 map); DAIS geometry freed under the joint paleo prior (Strategy B);
   runoff line reparameterized to its identified direction (A4); Rignot SMB anchor (A5);
   fast-dynamics λ/γ/κ freed.
4. **Targets:** extended reconciled series to 2023–2026 (GRACE-FO, GlaMBIE, NCEI, STAR), Dangendorf
   2024 total, Frederikse-ensemble σ, per-series windows, glacier inventory (A2) + 19th-century
   flow (A2b) terms; legacy point terms dropped.
5. **LWS:** locked (seeded realization; irreproducibility bug fixed).
6. **Posterior:** extB3 (pending acceptance) replacing the SNEASY-era calibration.

Citation policy is unchanged by the rename: Mengel 2016 (S_eq form), Nauels 2017 (transient form),
Wong et al. (BRICK/MimiBRICK base), + the T_glac data DOIs. Adopt the name at production
acceptance, updating provenance labels/captions in the same pass (feedback_output_provenance_labels).
Typography note for prose: "BRICK-F\*" needs escaping in markdown and reads aloud as "BRICK-F-star";
if that ever grates in a paper, BRICK-FA (FaIR-forced, Amplified) was the runner-up.

## 8. Memory updated

`project_brick_mengel_vnext_recalib` (top block = extB3 implementation state + launch command) and
the MEMORY.md index line. The memo carries §3e (D0 results) + §5-D0 (decisions, now resolved here).
