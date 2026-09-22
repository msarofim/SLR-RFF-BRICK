# Handoff — `--rho-max` built and gate-tested; L29 (L28 + rho_ais ≤ 0.90) LAUNCHED 19:57 (09-21 19:30 → 20:10)

**Start here.** Continues `handoff_2026-09-21b_imbie2026_L28.md` (its §1 ordering and §3 traps stand; this note adds only what
changed). CHANGELOG **09-21i** is the record; commit `fcbe828` on `ladrillo-dev` (+ this note's commit). Memory:
`mutation_test_gates` gained the 09-21 instance; `INDEX_diag` a one-liner.

**STATE AT HANDOFF (2026-09-21 ~20:10):**
- **Champion and the paper's posterior are STILL L27**; draft r9; champions.json untouched. L28 landed, not promoted (09-21h).
- **L29 = L28 + `--rho-max=ais:0.90`, RUNNING.** Launched 19:57 from a frozen copy of `run_L29.sh` (scratchpad); runner PID
  17867, chain PIDs **17881–17884** (seeds 2026–2029); ETA chains ~00:00–00:30 (four CCX `run_dispersed_multistart.R` jobs
  were already at 100 % on 4 of the 10 cores), then convergence diag → postprocess → postpred → components → stage-2
  diagnostics (no paper arms). Log: `outputs/log_L29.txt`; per-chain `outputs/mcmc/log_L29_seed*.txt`.
  ⚠ Julia's stdout is BUFFERED to those per-chain logs — the cap banner / repair line / logpost(θ₀) appear only when a chain
  EXITS (the smoke run on the identical configuration showed them: seed 2029's rho_ais 0.916 → 0.855, marginal 0.0522 held,
  logpost(θ₀) 790.15 vs L28's 805.10). `run_L29.sh`'s arm verification greps them after `wait`.
- Torch verdict was said out loud: Mac.

## 1. ⭐ NEXT
1. **Read L29 when it lands** (`bench_ladrillo_L29.md`, `diag_imbie2026_vs_targets` L29 outputs, `diag_ais_flux_split_vs_imbie_L29`,
   `diag_refit_precision` L27/L28/L29 vs L28). The pre-registered reading (scoping §4): (a) sensitivity parameters UP
   (anto_α, ice-flow₀, antarctic_α vs L28's 0.29 / 1.06 / 0.30) with the 1900–78 misfit growing ⇒ the physics CAN carry the
   shape and the structural question is about the early century; (b) the fit degrades everywhere (cumulative, 2011–17 rate AND
   early century all worse) ⇒ it cannot ⇒ a steepening is needed. Either way report which term binds; check `rho_ais` sits
   AT the cap (it will — the noise gate fails only if it crosses).
2. Then the handoff-b list: which posterior the paper ships (L27 / L28 / L29 / post-structure), the steepening build if
   warranted (free exponent on the ocean-temperature ratio first), the 09-16 list.

## 2. WHAT LANDED (09-21i)
- `--rho-max=<series>:<val>[,...]` in `julia/calibrate_mcmc_ext.jl`: `RHO_MAX` vector over `SERIES`, default 0.99 each (the
  rejection at the old `:1490` and the `--dump-priors` table read it); `repair_rho_start!` moves a start rho above the cap to
  0.95×cap with σ scaled to hold the marginal; bad series / out-of-range value error at load.
- Identity gate PASS (flag absent). Mutation: `ais:0.90` on the gate config = IDENTICAL = NO POWER (start 0.61, 300 iters
  never above 0.66); `ais:0.60` = repair fires, chain differs, max rho_ais 0.59998928. Bad-input errors verified.
- `run_L29.sh`: `run_L28.sh` + the flag, otherwise identical (target md5 asserted, starts `overdispersed_starts_L27r.csv`,
  proposal `adapted_cov_L27_named.csv`); arm verification greps the banner + repair; noise gate also fails on rho_ais ≥ 0.90;
  stage 2 folded in (no paper arms). `L29` declared in both TAG_DESC guards.

## 3. ⚠ TRAPS (adds to handoff-b §3)
- `pgrep -fl "julia.*calibrate_mcmc_ext"` from inside a Claude Bash call also lists the CALLING shell (its command line contains
  the pattern) — count the julia PIDs, not the matches. Four chains = PIDs 17881–17884.
- Smoke/gate-mutation artefacts (`*smokeL29*`, `*gate300mut*`, `*smk_*`, `*gatebad*`) were deleted from `outputs/mcmc/`; the
  gate's own `*gate300*` files are the standing ones.
- `outputs/ladrillo_priors_L24.csv`, `seed_diag_L24_seed2026.txt`, `vv_responsiveness_L24.csv` show as MODIFIED in the tree
  from earlier today (the identity gate does not touch them — they predate this session); not committed here, not mine to resolve.
