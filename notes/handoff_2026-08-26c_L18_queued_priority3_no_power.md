# Handoff — L18 is BUILT, VERIFIED and QUEUED (the Mac could not run it). Priority 3 is ANSWERED: its own test has NO POWER.

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, **84+ commits ahead of
`origin/ladrillo-dev` and deliberately unpushed — do not push without asking.**
Written 2026-08-26 to be picked up cold. **Continues** `handoff_2026-08-26b_amp_is_the_lever.md`.

**L14 IS STILL CHAMPION. `benchmark/champions.json` UNTOUCHED.** L15/L16/L17 unpromoted, L17
rejected. **No new chain completed this session.**

---

## 0. THE ONE-PARAGRAPH STATE

Priority 1 (the start-matched amp arm) is **written, smoke-verified, and queued** — it launched
and had to be killed, because the Mac is swap-bound at **load 218** and quoted a **12.66-day ETA**
while Marcus's own 23.5-hour CCX job is running on it. Nothing partial was written; relaunch is
one command. Priority 3 (the free exit-vs-return test) **was run, and it refutes its own framing**:
the out-of-MID time is ONE ABSORBING EVENT per chain, so both hazards are N=1 estimates. A
replacement test with real power was written and calibrated but has run only on the control.
**The amp question is exactly where -26b left it. Nothing about it changed.**

---

## 1. ⇒ WHAT TO RUN FIRST, WHEN THE MACHINE IS FREE

```bash
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
uptime                                   # ⚠ CHECK THIS FIRST. See §4.
sysctl -n vm.swapusage
ps -p 7879 -o pid=,command=              # is the CCX modefind job still running?
bash run_mcmc_L18.sh                     # ~2h34m on an IDLE machine
```
Then the standard post-chain sequence from -26b §6 with `T=L18`, plus the two new scripts:
```bash
bash scripts/ton_band_by_chain.sh L18
bash scripts/ton_transition_rates.sh L18
bash scripts/ton_escape_scale.sh L15 L16 L17 L18    # ⚠ still owed on L15/L16/L17 — see §3
```

**⚠ DO NOT rebuild `overdispersed_starts.csv` first.** Reusing L14's file unrebuilt is the
DECISION (-26b §4), and it is what makes the amp comparison exactly controlled.

---

## 2. L18 — WHAT IT IS, AND THE VERIFICATION THAT IS ALREADY BANKED

`run_mcmc_L18.sh` = L16's exact command **plus `--overdisperse`**. ONE change: the START.
Prior N(1.090, 0.180) unchanged; proposal `adapted_cov_L15pool_seed2026.csv` unchanged; targets,
`--gis-ordered`, `--gis-basins2`, 2M length all L16's.

* **L18 vs L16 = the START effect**, prior held fixed.
* **L18 vs L14 = the AMP-PRIOR effect**, start protocol matched.

**Smoke run `TAG=L18smoke` (4x4000) already passed — this does not need repeating:**

| line | value |
|---|---|
| `A6 prior` | `amp ~ N(1.090, 0.180) on [0.550, 1.630]` ✅ L16's prior |
| `logpost(θ0)` | 224.59 / 228.81 / 224.70 / 222.75 ✅ four DISTINCT real draws |
| `[MAP start = ...]` | **-644.51 — BIT-IDENTICAL to L16's and L17's** |

**⚠ THAT LAST ROW IS AN UNPLANNED BONUS CHECK, AND IT MATTERS.** L18 prints the same MAP
logposterior as L16/L17, which proves it scores against **the same objective**. So L18-vs-L16 is
genuinely single-change and is NOT confounded by the `893bfaa` target move (`lws` 0.123,
`dang_closure_sig` 0.151) that makes the Aug-20 L14 run unusable as a control for a NEW arm.
Re-check this line on the production run — if the MAP value is not -644.51, something moved.

**Starts verified safe:** amp 1.0813 / 1.0945 / 0.8275 / 0.8829, inside **both** priors' bounds
([0.700, 1.250] and [0.550, 1.630]), so the prior change drags no start to a bound.

**⚠ `no_power_null`, in the script header too:** the starts disperse along `ais_iceflow0` and are
ALL IN MID. L18 has power on the START question ONLY. **100% MID would be BY CONSTRUCTION** and
is NOT evidence about the LOW/HIGH modes.

**FALSIFIABLE PREDICTION, registered in the script header BEFORE the run — resolve it before
reading anything else:** if the START was the confound, L18's AIS `median_vs_lit` moves most of
the way to L14's (ssp245 @2100/@2150/@2300: L14 0.531 / 0.406 / 0.949 vs L16 0.865 / 1.710 /
1.974). If instead it lands on the **L16MID conditioned column (0.815 / 1.601 / 1.908**, only
15/8/6% closed), the start was NOT doing the work and **the amp prior is the lever** — which makes
the remaining decision a PROVENANCE call the benchmark structurally cannot see.

---

## 3. PRIORITY 3 IS ANSWERED — AND THE ANSWER IS "THIS TEST CANNOT ANSWER IT"

`scripts/ton_transition_rates.sh` (NEW), output `outputs/ton_transition_rates_L14_L17.txt`.
Mutation-tested on three synthetic chains — a crosser, an absorbed chain, a never-leaves control —
against hand-counted answers before use.

**⚠ THE FRAMING IS VACUOUS AS POSED.** A chain alternates in/out, so `|exits - returns| <= 1`
ALWAYS. -26b §1 proposed "an exit-rate vs return-rate count"; the COUNTS are equal by
construction and discriminate nothing. Only excursion COUNT and LENGTH can.

**⚠ AND THE HAZARD VERSION HAS NO POWER EITHER.** Out-of-MID time is **one absorbing event** per
affected chain:

| chain | absorbed share of out-time | longest run | typical excursion EXCLUDING it |
|---|---|---|---|
| L17/2028 | **98.2%** | 475,232 | 25.1 |
| L16/2026 | **93.2%** | 184,781 | 38.7 |
| L17/2026 | **73.9%** | 724,358 | 442.0 |
| L15/2029 | 63.4% | 630,001 | 1937.9 |
| L16/2028 | 27.7% | 83,438 | 205.3 |
| L16/2027 · L16/2029 · L17/2027 · L17/2029 | 6-10% | 619-1,049 | 28.8-37.9 |

**Excluding each chain's single longest run, L16 and L17 are indistinguishable** — the same
~25-45-draw boundary jitter. Both hazards are therefore **N=1 estimates driven by one event**.
`no_power_null` + `two_statistics_can_be_blind`.

**The DIRECTION is weakly consistent with return-blocking** — L17's absorbing excursions run
475k-724k draws against L16's 83k-185k — **but that is TWO events per arm. Do not quote it as
established.**

**L14 behaves as a control should:** 100% MID on all four chains, 0-131 out-of-MID draws, so it
reports *no power* rather than a clean pass (`audit_every_target`).

### The replacement test — WRITTEN AND CALIBRATED, STILL OWED ON L15/L16/L17

`scripts/ton_escape_scale.sh` (NEW) uses every post-burn draw (~1e6/chain) instead of 2 events.
It compares the observed longest excursion against a **driftless-diffusion return time**
`T = D^2/(p*s^2)`:
* `observed >> T_diff` ⇒ a **REAL restoring force / genuine second mode**.
* `observed ~ T_diff` ⇒ no barrier, just a slow proposal — fixable by tuning.

**⚠ Mutation-tested TWICE, and the first version was WRONG.** It counted the edge-*crossing* jump
as a step of the return journey and inflated the step RMS **17x** (0.166 on a synthetic walk whose
steps are exactly 0.01). Fixed by requiring both ends of a step to be out of MID. The synthetic
now recovers `p` and `s` exactly.

**⚠ THE CALIBRATED NULL: a pure driftless random walk scores `obs/diff = 2.0x`.** Judge the real
chains against 2x, not against 1x. Having this number is the point of the exercise.

**It ran on the L14 control ONLY** before being killed to protect the CCX job (partial preserved,
`outputs/ton_escape_scale_L14_L17.PARTIAL.txt`). **Re-run on L15/L16/L17.** This is now the test
that would establish whether the `T_on` barrier is real — which is the deeper question under the
whole L15→L18 arc.

---

## 4. ⚠⚠ THE MACHINE — READ BEFORE LAUNCHING ANYTHING

L18 launched 21:12 and was killed 21:39. **It was not slow; it was not going to finish.**

| measurement | value |
|---|---|
| progress-meter ETA | **12.66 days** |
| effective cores per chain | **0.056** (3.56 s CPU in 64 s wall) |
| load average | **218.86** |
| processes / runnable | 629 / 113 (94 Chrome renderers, 28 WebKit) |
| free RAM | **0.1 GB** of 17.2 GB; compressor 7.3 GB; swap 20.0 of 21.5 GB |

**⚠ THE DECISIVE REASON TO STOP RATHER THAN PUSH THROUGH:** the Mac is running **Marcus's own CCX
job**, `calibration/run_modefind_pump_arms.R`, PID 7879, alive since Tue 8 PM with **23.5 h of CPU
invested**. Four julia chains on a thrashing machine degrade that job for days. That job was
verified still alive and healthy after L18 was stopped.

**Nothing partial was written** — L18 died in startup, so no `chain_L18_seed*.csv` exists and there
is nothing to quarantine. Its startup logs were renamed `log_L18_ABORTED_swapbound_seed*.txt` and
`seed_diag_L18_ABORTED_swapbound_seed*.txt` so they cannot be mistaken for a run.

**⚠ ADD THIS TO THE PRE-LAUNCH RITUAL.** `uptime` and `sysctl -n vm.swapusage` before any
production chain. -26b §5 already warned "a slow run is not a hung one" — the converse also holds:
**a run quoting days is not a slow run, it is a run that will not finish.** Read the meter's ETA
at ~5 minutes and kill early if it is measured in days.

**⚠ AND DO NOT RUN A FULL-CHAIN SWEEP CONCURRENTLY WITH PRODUCTION CHAINS.** The `cut | awk` passes
in `ton_transition_rates.sh` / `ton_escape_scale.sh` read 2.2 GB per file, 16 files. Run them
BEFORE or AFTER a production launch, never alongside it.

---

## 5. CORRECTION TO THE PREDECESSOR HANDOFF

-26b §2 lists L14's four starts as `223.78 / 228.36 / 225.60 / 223.78`. **Seed 2026's value is
224.32**, not 223.78 — seed 2029's value was duplicated into its slot. Verified against
`outputs/mcmc/log_L14_seed2026.txt`. Four DISTINCT real draws either way, so §2's conclusion is
untouched; the slip matters only if someone tries to match a start by its logposterior.

---

## 6. FILES AND COMMITS THIS SESSION

**Commit** `53d08dc` (on `ladrillo-dev`, unpushed) + the CHANGELOG/handoff commit that follows it.

**New:** `run_mcmc_L18.sh`, `scripts/ton_transition_rates.sh`, `scripts/ton_escape_scale.sh`,
`outputs/ton_transition_rates_L14_L17.txt`, `outputs/ton_escape_scale_L14_L17.PARTIAL.txt`.
**Untracked byproducts:** `outputs/mcmc/{chain,adapted_cov,log,seed_diag}_L18smoke_*` (the smoke),
`outputs/mcmc/*_L18_ABORTED_swapbound_*` (the aborted launch).
**Modified:** `CHANGELOG.md`.

**Still open, unchanged from -26b:** the amp prior is a **PROVENANCE call and is Marcus's** —
L14's N(0.95, 0.10) on Xie's sliding-window trend ratio vs L16/L17's N(1.09, 0.180) on two
corrected CMIP6 secant ensembles. **The benchmark scores fit, not provenance, and structurally
cannot see this.** L18 sharpens the stakes; it does not decide it.

**Priority 2 (the `T_on`-dispersed L14 arm) is untouched** and still needs `--param=` added to
`build_overdispersed_starts.jl`. See -26b §4.
