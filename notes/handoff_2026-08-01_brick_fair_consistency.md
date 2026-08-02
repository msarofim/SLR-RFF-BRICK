# Handoff 2026-08-01 — BRICK-AM ↔ FaIR forward-propagation consistency (conditional Wong-weighting)

**Self-contained pickup:** read this + `CLAUDE.md` + memory `project_fair_brick_coupling_joint_calib`.

> **⚠️ SUPERSEDED IN PART — see the 2026-08-02 ADDENDUM at the bottom before running anything.**
> The "Monday launch" wall-time estimate below was wrong (~10×: the legacy driver pays a ~14 ms
> Mimi rebuild per run — the full job would have TIMED OUT on cpu_short). A validated fast engine
> (bit-identical, ~30×) plus a paired PULSE arm landed 2026-08-02, and full production was run
> LOCALLY. Monday's Torch run is now an optional cross-check, not the deliverable path.

## TL;DR / state
Built and validated a **conditional Wong-weighting** method that makes BRICK-AM posterior draws consistent
with FaIR in **forward propagation** (never re-calibrates the forcing). Local validation passed. The full
**launch code** (Torch run → coupled SLR bands) is built, smoke-tested locally, and staged on Torch.
**HELD for Monday** (fairshare recovery). Monday = submit a 5-config smoke, then the full run.

## How we got here (the arc)
1. The **joint FaIR/BRICK forcing calibration** was built, run on Torch, and **REJECTED** — it let the SLR
   likelihood *re-infer* the forcing (bent GMST ~0.28 °C cool @2100 via fpc1, the ECS mode), and the
   te_α↔OHC coupling it recovered is **immaterial to the total-SLR bands**. Record:
   `notes/negresult_2026-08-01_joint_forcing_calibration.md`.
2. **Marcus principle (2026-08-01):** SLR must not influence atmospheric variables (forcing/ECS) — they're
   better constrained by data not in this likelihood. **Propagate forcing forward; don't re-calibrate it.**
3. This work: build the correct forward-propagation consistency method, **conditional on each FaIR config,
   with every FaIR parameter set kept equally likely** (forcing marginal untouched).

## The method
Per FaIR config *k*: `w_{i|k} ∝ exp[c·(ℓ^FB_{ik} − ℓ^B_i)]`, **normalized WITHIN each config** so
`p(config)=1/841` stays uniform (SLR never touches the forcing marginal — only the pairing / conditional).
- `ℓ^FB` / `ℓ^B` = historical total-SLR (Frederikse "dang" channel, each draw's own AR(1) `sd_dang`/`rho_dang`)
  under config-*k* vs the **mean** (calibration) forcing. The **ratio** cancels each draw's intrinsic fit →
  healthy ESS (Tony's insight; my crude step-1 used absolute ℓ and degenerated to ESS=1) and mitigates the
  Mengel double-count (Tony excluded the Mengel arm from global Wong-weighting for this reason).
- `c` tuned to a **gentle** mean conditional ESS/N (default 0.6): a consistency nudge, not a re-calibration.
- **Recovers the te_α↔OHC coupling in PROPAGATION**, forcing marginal fixed.

**Validated locally** (`weight_brick_conditional_fair.jl`, 60 cfg × 400 draws): mean-forcing recovery EXACT
(max|ℓ^FB−ℓ^B|=0, ESS/N=1.000); coupling signature corr(weight, te_α) vs config OHC@2018 = **−0.46**
(hottest configs −0.156, coldest +0.113 — hot ocean-heat down-weights high-te_α draws, TE∝te_α·OHC);
c=0.145, ESS/N=0.60 (≈ Tony's c≈0.2 for GMSL-only).

## Files (all committed; last commit 5d3741f)
| file | role |
|---|---|
| `julia/weight_brick_conditional_fair.jl` | weighting only (validated; historical) |
| `julia/weight_and_project_brick_fair.jl` | **THE launch driver** — weighting + projection to 2300 + COUPLED vs INDEPENDENT bands (one BRICK run per (config,draw) gives both ℓ^FB and future SLR) |
| `slurm/weight_and_project_brick_fair.sbatch` | single job, `cpu_short` 4h, `DRAWS`/`CONFIGS` env-overridable |
| `julia/calibrate_mcmc_ext.jl` | ★ CANONICAL BRICK-AM (mean forcing); now `PROGRAM_FILE`-guarded so the drivers `include` its FREE list + θ→BRICK apply + dang likelihood |
| `calibrate_mcmc_joint*.jl`, `project_slr_*.jl` | REJECTED joint experiment, banner-marked DIAGNOSTIC |

## Monday launch — exact steps
On Torch (VPN up; `ssh torch`; `cd /scratch/ms17839/SLR-RFF-BRICK`):
```
sshare -u ms17839 -A torch_pr_1041_general        # confirm FairShare recovered off 0.28
DRAWS=200 CONFIGS=5 sbatch slurm/weight_and_project_brick_fair.sbatch    # SMOKE first (~few min)
#   verify exit 0 + sane COUPLED/INDEP bands in logs/wpf_brick_<jid>.out
DRAWS=2000 CONFIGS=all sbatch slurm/weight_and_project_brick_fair.sbatch # FULL (~1.68M runs to 2300, ~1–2.5 h)
```
Outputs → `outputs/mcmc/wong_cond_slr_bands.csv` (COUPLED vs INDEPENDENT, total+comps @2050/2100/2150/2300)
+ `wong_cond_weights_full.csv`. Pull back, interpret coupled-vs-independent.

## Non-obvious state / gotchas
- **Torch has the full input set** (verified): both drivers, ext + all its inputs, extA108 subsample, and
  the **wide forcing** (transferred 2026-08-01 to `/scratch/ms17839/FaIRtoFrEDI/magicc_comparison/processed/curv_wide/`
  — the driver reads it via `REPO/../FaIRtoFrEDI/...`), pristine MimiBRICK depot.
- **ext parses `ARGS[1]` as N_ITER with no flag-guard** → must pass positional `2000 2026` *before* flags.
  The sbatch already does this; keep it if invoking by hand.
- **Fairshare 0.28** on 2026-08-01 (RawUsage 65k from the rejected joint run); ~7-day half-life.
- Rejected joint chains (~13 GB, `chain_jcont_*_n4000000.csv`) left on scratch as reproducible diagnostics.
- **Expected result:** coupling is immaterial to the *total* SLR (the shuffle test showed −0.55 cm @2100),
  so COUPLED ≈ INDEPENDENT on the total; the method should matter for the **steric/TE** component and for
  **pulse / SC-SLR** work — that's the real payoff to pursue next.

## Next after the bands land
- Interpret COUPLED vs INDEPENDENT. If small on the total (expected), the current independent pipeline is
  ~adequate for levels; document the coupling's (small) effect and move the method to where it bites.
- Apply the conditional weighting to **pulse / SC-SLR** (te_α↔OHC may matter more on the marginal).

---

# ADDENDUM 2026-08-02 — pulse arm built + fast engine + production run LOCALLY

All of the below was validated and run on the Mac (zero cluster time), per Marcus's
"do as much as possible before the next Torch run" directive.

## 1. Paired pulse arm in the launch driver

`julia/weight_and_project_brick_fair.jl` gained (defaults preserve the staged behaviour BIT-FOR-BIT —
verified by byte-comparison of the smoke outputs):

| flag | meaning |
|---|---|
| `--pulse=off\|on\|zero` | `on` = also run the paired 10-GtCO2 2030 CO2 pulse forcing per (config,draw), IN-PROCESS on the same model instance (exact pairing); `zero` = wiring test (base fed as pulse arm; Δ must be exactly 0.0) |
| `--basis=<sfx>` | wide-file suffix for BOTH arms: `""` (canonical stochastic), `_nonoise`, `_nonoise_flatsolar`, `_neg10gt`, `_20gt` |
| `--pulse-gt=` | GtCO2 normalization (default 10; use 20 with `--basis=_20gt`) |
| `--out-tag=` | extra output suffix so validation runs never clobber canonical paths |
| `--engine=fast\|legacy` | see §2; default `fast` |

Metrics extended 8 → 16 (adds comps @2150/@2300) when pulse≠off; `--pulse=off` keeps the staged 8-row
bands schema. Outputs (suffix = basis + zerotest-tag + out-tag):
`wong_cond_slr_bands<sfx>.csv`, `wong_cond_weights_full<sfx>.csv`, and in pulse mode
`wong_cond_pulse_bands<sfx>.csv` (COUPLED vs INDEP, cm per GtCO2) +
`wong_cond_pulse_pairs<sfx>.csv` (per-pair: w + 16 base + 16 Δ metrics; ~600 MB at full scale —
do NOT commit; medians/means/tails all recomputable in post from this file).
The sbatch passes `DRAWS/CONFIGS/PULSE/BASIS/OUTTAG` env vars through.

## 2. Fast engine — the launch-blocking discovery

**The handoff's "~1–2.5 h single-core" full-run estimate was wrong ~10×.** Any `update_param!` dirties
the Mimi model and the next `run()` pays a **~14 ms full rebuild** of the 451-yr model (the integration
itself is ~2 ms; measured via `julia/diag_wpf_runtime_breakdown.jl`). Legacy per-run cost ≈ 25–30 ms ⇒
the staged full run ≈ 12–14 h on the Mac, likely worse on Torch — **it would have TIMED OUT on
cpu_short (4 h) with nothing written.** The 2.25 ms/iter joint-calib MCMC didn't see this because its
model window is 177 yr (rebuild ~8× cheaper).

Fix (`--engine=fast`, now the default): build once, then mutate the BUILT instance in place — array
params are SubArray views into shared external-param backing (one write reaches all 4 GMST consumers;
asserted at startup), scalars are mutable `ScalarModelParameter` boxes — and `run(mi)` directly.
**0.88–1.3 ms/run (~30×).** Pinned to Mimi 1.6.0 internals (`getfield(params, :nt)`).

**Validation chain (all PASS):** per-component bit-identity (ais/gsic/gis/te/total) fast-vs-legacy;
full-smoke CSV byte-identity vs the STAGED driver's outputs; production-scale byte-identity on the
60cfg×400draw pulse run (24k pairs × 32 metrics, fast == legacy); zero-pulse exact-0.0 under both
engines; cross-process bit-reproducibility (two separate Julia processes → identical CSVs).

## 3. Five-test sanity battery — PASS

FaIR ±10/+20 GtCO2 companion ensembles already existed (`fair_ensemble_v145_ssp245_pulseco2_{neg10gt,20gt}_2030.npz`);
dumped to wide files via `dump_fair_wide_curv.py` (base arms bit-identical to canonical for GMST,
1e-14-rel float-formatting noise on OHC — physically identical). Battery = 3 matched 10cfg×100draw runs
(`_p10ref`, `_neg10gt_signflip`, `_20gt_dbl`); verdicts via `python/check_pulse_battery_wpf.py`:

1. **Zero-perturbation:** Δ = 0.0 exactly, 16 metrics × all pairs.
2. **Sign-flip:** −1.000..−1.005 on linear metrics (te/gis/gsic/total@2050).
3. **Doubling:** 0.998–1.000 on linear metrics. AIS shows the expected convex tipping asymmetry
   (dbl ratio 1.06 @2100 → 1.25 @2300) — genuine physics, the mechanism-decomposition story in miniature.
4. **Bit-identical reproducibility:** cross-process AND fast-vs-legacy.
5. **First-principles:** Δtotal@2100 medians 4.2–4.7e-3 cm/GtCO2 vs the 7.7e-3 sub-annual artifact
   reference (1:1-paired, all 841 cfgs) — same ballpark; see §5 flag.

## 4. 60cfg×400draw preview (stochastic basis, annual step)

COUPLED vs INDEPENDENT on the pulse marginal mirrors the levels finding: **medians ~unmoved**
(Δtotal@2100 4.72e-3 vs 4.71e-3 cm/GtCO2, +0.2%), **AIS-tipping upper tail trimmed** (95th −1.7% @2100,
−4.0% @2300). The coupling's bite on the marginal is in the tail, not the center.

## 5. Full production — COMPLETE (run locally 2026-08-02; 4 runs × 3.36M BRICK runs, ~45 min each)

Four runs at `DRAWS=2000 CONFIGS=all PULSE=on`: {stochastic, `_nonoise_flatsolar`} × {annual-step,
sub-annual patch}. Depot patch applied from `julia/patches/antarctic_icesheet_smoothed_trigger.jl.txt`
with backup, RESTORED + verified pristine after (`chmod u-w`). Zero-pulse gate re-passed under patch.

**RESULT 1 — levels (canonical, unpatched, `wong_cond_slr_bands.csv`): coupling immaterial, as
predicted.** total@2100 COUPLED 46.68 [33.51, 104.66] vs INDEP 46.38 [33.18, 105.01] cm — Δmedian
+0.30 cm, width −0.68 cm; @2300 Δmed +3.15 on 247 cm (+1.3%). TE medians move 0.00. INDEP median
matches the extA108 pipeline (~46–47). **The independent pipeline stands for levels.**

**RESULT 2 — pulse marginal: the coupling is immaterial on the marginal TOO.** Coupled/indep ratio of
the pulse MEAN = 1.007 @2100, 1.003 @2150, 1.009/0.999 @2300; TE component 1.000; tip-advance fraction
23.31%→23.41%. Same on both bases. The handoff conjecture ("te_α↔OHC may matter more on the marginal")
is ANSWERED: it does not — the within-config te_α tilt (gentle, ESS/N 0.6) ~cancels in pulse−base.
**Clean negative result: the existing independent machinery is adequate for levels AND marginals;
conditional weighting = a documented consistency check, not a pipeline change. Unblocks the CH4/CO2
comparison on the current pipeline.**

**RESULT 3 — the sub-annual patch is REQUIRED for quotable pulse numbers, and the MEAN is the robust
statistic.** Annual-step medians are quantization-suppressed (total@2100 4.65e-3 vs sub-annual mean
1.47e-2; @2150 median 6.96e-3 vs 1.65e-2 — the AIS tip channel is frozen by annual stepping).
Validation: my sub-annual cross-product MEAN @2100 = **1.469e-2 cm/GtCO2 vs the artifact's 1:1-paired
1.498e-2 (within 2%)**, and it is driver-basis-consistent to 0.05% (stochastic 1.4695e-2 vs
deterministic 1.4688e-2). The MEDIAN is **sample-fragile**: ~23% (stoch) / 33% (nnfs) of pairs sit in
the tip-advance mode, so the 50th percentile falls in the bimodal density gap — early-chain-841 draws
give 1.06e-2 vs full-ensemble 5.8e-3 @2100 with IDENTICAL tip fractions (23.4/23.3%) and IDENTICAL
smooth-mode medians (4.67/4.65e-3). The artifact's 7.74e-3 median is the same fragility, not a physics
disagreement. **Quote: sub-annual mean, or mode-decomposed (smooth-mode median + tip fraction +
tip-mode mass, Lemoine-Traeger style). Never the bare pooled median.**

**RESULT 4 — the patch is NOT perfectly a historical no-op under per-config forcing** (new, minor):
ℓ^B bit-identical (exact no-op at mean forcing ✓) but ℓ^FB differs for 401/1,682,000 pairs (0.02%) —
45 low-threshold draws × hot configs cross DAIS pre-2026. Immaterial to bands/weights (c 0.1258 vs
retuned; max|Δw| 1.5e-3); canonical weights = the UNPATCHED run (calibration parity).

**Files** (`outputs/mcmc/`): canonical levels+weights = `wong_cond_slr_bands.csv` +
`wong_cond_weights_full.csv` (unpatched). Quotable pulse = `wong_cond_pulse_{bands,pairs}_subann.csv`
and `..._nonoise_flatsolar_subann.csv`. Annual-step pulse files re-tagged `_annualstep` (quantization
DIAGNOSTIC — do not quote medians/means from them). `pairs` + `weights_full` files are 0.1–1.1 GB —
NOT committed; small bands CSVs committed.

## 6. Monday — revised

- **Done: the full deliverable (levels + pulse, both bases, both integrators) ran locally. No Torch
  run is needed.** Optional cross-check only (determinism verified; expect bit-identical): `git pull`
  on /scratch, staged smoke, then full with fast engine — bands-only ≈ 0.5–1.5 h, PULSE=on ≈ 1–3 h
  (request 6 h; the LEGACY engine would NOT fit ANY window — 12 h+). Note Torch's pristine depot
  means Torch can only reproduce the `_annualstep` pulse variants without applying the patch there.
- Next: Marcus interprets RESULTS 1–2 (method closes as a documented consistency check); then the
  **CH4 arm** — generate the FaIR CH4 pulse pair (`fairtable7_v145_pulse.py --specie ch4
  --pulse-mtch4 1.0` ± `--no-noise --flat-solar-after 2025`, then `dump_fair_wide_curv.py
  --out-suffix _ch4bio...`), run this driver with `--basis=_ch4bio... --pulse-gt=1` (units then
  per-Tg — relabel before quoting), sub-annual patch on for the quotable arm. Then SC-SLR.
