# Handoff — ⭐ OPTION 6 WORKS (L32/L33 escape the identity trade-off) BUT L27 STILL WINS THE WHOLE-MODEL BENCHMARK; the decision is now a JUDGEMENT, and the PAPER'S ARGUMENT is what changed (09-22 18:00 → 09-23 20:00)

**Start here.** Self-contained. Supersedes `handoff_2026-09-22d_dynamics_constraint_answered.md` for everything after
its §0 — that file's §1 (the dynamics-constraint answer) and §2 (traps) still stand and are not repeated in full.
Records CHANGELOG **09-22j, 09-22k, 09-22l, 09-22m, 09-23a–g**. Commits `8ce77ac` → **`e35396c`** on `ladrillo-dev`,
all pushed. Memory: `ais_dynamics_channel_is_the_weaker_one`, `ais_smb_variability_is_weather`,
`ic_cannot_adjudicate_a_noise_change` (CORRECTED in place), `alldone_after_failed_steps` (all new/updated),
`INDEX_ais_imbie.md` + root `MEMORY.md` updated.

---

## ⛔⛔ 0. READ THIS BEFORE QUOTING ANY NUMBER: TWO OF MY OWN CLAIMS WERE RETRACTED THIS SESSION

**RETRACTION 1 — "L32 strictly dominates L27" is WRONG** (made 09-23b, corrected 09-23d). It rested on two Antarctic
summary statistics (level z, 2018–23 dynamics anomaly). The whole-model benchmark scores the full 1900–2025 record and
**L27\* is better on the full-period AIS: 0.70σ vs L32's 0.88σ.** ⇒ **Two favourable summary statistics are not a
domination claim.**

**RETRACTION 2 — "every iid-like scorer prefers L27, every autocorrelation-allowing scorer prefers L32" is WRONG**
(made 09-23e, corrected 09-23g). L27's IC had been computed **09-20 18:05**, against the target that was **rebuilt onto
IMBIE 09-21 13:12** — 19 h later. Different data. Re-run on a common target, **both arms favour L32** and the obs_iid
sign FLIPS (−11.7 → **+77.6**). ⇒ the "arms disagree" finding does not exist.

⛔ **Do not re-quote:** ΔlnL +10.0 / +7.6 / +5.6 (ar1_prof) or −11.7 (obs_iid) for L27-vs-L32; L27 ΔBIC "+20.8" vs
BRICK; "L32 strictly dominates L27".

---

## 1. WHERE THE IMBIE QUESTION STANDS — CLOSED as an investigation

`net ≡ smb + dyn` is an identity and the module's SMB cannot produce IMBIE's snowfall excursion, so fitting the
Antarctic LEVEL and matching its DYNAMICS partition are mutually exclusive ([[ais_net_dynamics_tradeoff_identity]]).
Six options were enumerated; **five are now tested.**

| option | arm | verdict |
|---|---|---|
| 1 stay on L27 | — | the status quo; still the champion |
| 2 fit the IMBIE level | L28 | ⛔ buys the level, pays in dynamics (−74.6) |
| 3 + ρ cap | L29 | ⛔ indistinguishable from L28 on every channel |
| 4 + discharge ramp | L30 | ⛔ slope on its prior floor, ≤2 cm |
| 5 restrict the level span to 1979+ | **L31** | ⛔ **NULL** (09-22m) |
| 6 **observation-derived noise floor** | **L32 / L33** | ⭐ **WORKS, and robust** (09-23b/c) |

### 1a. Option 5 was a null, and WHY is the transferable part
`--ais-fit-from=1979`. Primary criterion (pre-registered ≤ −110): **−75.4 ± 4.7** vs L28's −74.6 ⇒ **no effect**, and it
cost **2.4–2.5×** on the pre-1979 hindcast. Given the freedom, the refit spent it on MORE BASELINE discharge, not more
trend (`antarctic_alpha` 0.302 → **0.252**, the FLATTER direction), sliding FURTHER along the identity line.
⭐ **Why: the barrier fell 3.2–4.5× on the restricted span, but the DENSEST objection (1992–2002, 2.4–3.6× per-year
density) is direct IMBIE and SURVIVES the restriction.** Pre-1979 carried 78 % of the penalty MASS at only 1.09–1.24×
density — mostly LENGTH. ⇒ **a penalty's SHARE says what dominates the total; its DENSITY says what is actually
objecting, and only density predicts what removing a segment does.** Share alone would have predicted a win.

### 1b. ⭐⭐ Option 6 works. THE EVIDENCE WAS MEASURED BEFORE THE ARM WAS BUILT (Marcus asked)
IMBIE 2026 Antarctic SMB anomaly **excluding 2020–23 entirely**: sd 92.8, **yoy sd 116.5 Gt/yr** (134.7 with it). Every
decade independently 107–132. **Eight years |z| > 1.5** spread 1981 → 2023. All three regions. ⇒ **the excursion is not
the variability.**
⭐ **And it is WEATHER: GMST explains R² = 4.3 %** (its annual change, 0.01) ⇒ **a FORCED SMB term is unavailable**;
only a stochastic one.
⚠ **Vintage caveat:** IMBIE 2021's TOTAL yoy sd is 35.3 vs 2026's 53.8 on the shared window — the size is partly
reprocessing-dependent. ⚠ corr(SMB, dyn) = −0.742 is largely CONSTRUCTION (the partition is an identity).

**⚠⚠ MY "SMB IS 25× TOO QUIET" FRAMING OVERSTATED IT.** That is the MODEL's SMB (yoy sd 3–6 Gt/yr). The LIKELIHOOD's
free AR(1) already absorbs 0.43–0.67× of the implied innovation, so **the real gap is 1.5–2.3×.** It is still a genuine
misspecification: `sd_ais`'s prior is effectively unconstrained (N⁺(0,5) **cm**) and the implied floor **0.03259 cm**
sits ~2× outside L28's posterior p95 (0.0171) — **the likelihood CHOSE a value the SMB record forbids.**

**L32 = L28 + `--sd-ais-floor=smb`** (floor derived from the IMBIE file at run time, printed, recorded in the priors
artifact). **All four pre-registered criteria met, and two went the OPPOSITE way to my prediction:**

| criterion | threshold (set before the numbers) | result |
|---|---|---|
| **PRIMARY** 2018–23 dyn anomaly | win ≤ −110 | **−133.1 ± 4.9** ✅ (best of ANY arm; IMBIE −167.2) |
| COST A hindcast | report either way | bias @1900 **−0.524 → −0.154**, @1950 −0.210 → −0.144 ✅ **IMPROVED** |
| COST B width | a "wider" win is no win | p05–p95 **1.01–1.03×** L28 in 4 of 6 cells ✅ |
| GUARD non-AIS | ~0.02σ | ≤ 0.008 cm ✅ |

⭐ **Off the trade-off line by 38.9 Gt/yr** (dyn = 149·cum − 260.1 through L27/L28/L31 predicts −94.2 at L32's cum
1.113). **Mechanism: `antarctic_alpha` 0.3015 → 0.3779**, highest of any arm — L31 moved it DOWN and failed, L32 UP and
won. **Best-converged arm** (R-hat 1.00011, 7/50 marginals).
⚠⚠ **I predicted COST A and COST B wrong.** ⇒ ⭐ **A misspecified noise term does not merely under-disperse the
posterior — it BIASES THE MEAN, because the mean is made to do the noise's job.** Do not assume loosening a constraint
trades fit for spread.

### 1c. ⭐ And it survives the vintage (L33)
`--sd-ais-floor=smb2021` re-derives the floor against the earlier release (TOTAL yoy sd 36.0/54.8 = **0.656** ⇒
**0.02139 cm**, a **34 % cut**; ⚠ the total→SMB transfer is an ASSUMPTION, printed at the gate). **Dyn −126.2**, off the
line by **−37.1** vs L32's −38.9, and the BETTER level (z **−1.21** vs −1.45). ⇒ **the escape is not sensitive to the
floor's value.** Best-sampled arm yet (R-hat 0.99857, ESS 1575.4).
⭐ **The floor BINDS in both** (L32 p05 0.03261 vs 0.03259, 72 % within 2 %; L33 0.02142 vs 0.02139, 48 %) — **check
that before reading any sensitivity arm, or you are comparing against a slack constraint.**

| arm | floor | cum | level z | 2018–23 dyn | off line |
|---|---|---|---|---|---|
| IMBIE 2026 | — | 1.316 ± 0.140 | — | **−167.2** | — |
| L27 | — | 0.948 | −2.63 | −119.1 | — |
| L28 | — | 1.224 | **−0.66** | −74.6 | — |
| L32 | 0.03259 | 1.113 | −1.45 | **−133.1** | −38.9 |
| **L33** | **0.02139** | 1.147 | **−1.21** | −126.2 | −37.1 |

**Which of L32/L33?** Statistically tied on the primary (Δ 6.9 ± 6.9). **L32 as candidate, L33 as its published
sensitivity** — L32's floor needs one fewer assumption. L33 is a defensible alternative (better level, better ESS).

---

## 2. ⭐⭐⭐ BUT THE WHOLE-MODEL BENCHMARK FAVOURS L27, AND IT IS THE TRUSTWORTHY SCORER

`bench_ladrillo.py` (via `run_L32_bench.sh`). Full-period RMSE in units of each component's own target 1σ. **`L27*` is
the frozen `benchmark/reference/L27/` champion re-scored INSIDE THE SAME RUN on the live target — the only valid ruler.**

| component | L27\* | **L32** | L28 | verdict |
|---|---|---|---|---|
| **AIS** | **0.70** | **0.88** | 1.53 | **WORSE** |
| glaciers | 0.69 | 0.69 | 0.68 | SAME |
| Greenland | 1.07 | 1.07 | 1.09 | SAME |
| thermal exp. | 1.51 | 1.51 | 1.52 | SAME |
| TOTAL | 0.26 | **0.22** | 0.20 | SAME |

⭐ **Non-Antarctic components identical to the champion to 2 dp** — the change stayed Antarctic (this CONFIRMS the
transitive inference flagged as unverified on 09-23c). ⭐ `L27*` reads 0.70σ in the L28, L29 AND L32 files alike.

**By window — L32 is the INTERMEDIATE arm:**

| AIS window | n | L27\* | **L32** | L28 |
|---|---|---|---|---|
| 1920–1949 | 30 | **0.08**, cov 100 % | 1.07 | 1.89, cov 0 % |
| 1950–1992 | 43 | **0.37** | 0.47, cov **93 %** | 0.62 |
| **1993–2026** | 33 | 1.27, cov **3 %** | **1.01**, cov **27 %** | **0.67**, cov 52 % |
| rate z | — | **−2.42** | **−1.79** | −1.03 |

⚠ L27's 1920–49 edge is partly HOME FIELD (that segment is Frederikse, what L27 was fitted to) so its SIZE is
flattered — **but unlike L31, L32 DID fit that period and chose to fit it worse**, so the advantage is real.

**⭐⭐⭐ AND THE DECISIVE ASYMMETRY POINT:** the benchmark scores against the live IMBIE target **that L32 was fitted to
and L27 was not** — and **L27 STILL WINS the full-period AIS.** A win AGAINST an in-sample asymmetry is worth far more
than a win with it. **This is the strongest single result in the comparison.**

---

## 3. THE IC (AIC/BIC) — vs BRICK it is fine; for L27-vs-L32 it CANNOT ANSWER

**vs BRICK 2.0 (corrected, common target)** — Δ = BRICK − Ladrillo, positive favours Ladrillo, Δk = −15:

| arm / bound | L27 ΔBIC | **L32 ΔBIC** |
|---|---|---|
| ar1_prof ≤ 0.99 | **+9.1** | **+15.4** |
| ar1_prof ≤ 0.95 | +68.0 | +69.8 |
| ar1_prof ≤ 0.90 | +137.9 | +139.1 |
| obs_iid | +2175.3 | +2330.5 |

⇒ **L32 clears BRICK at every bound and beats L27 there.** Hindcast RMSE vs BRICK: AIS **0.88 vs 8.82**, glaciers 0.69
vs 3.37, Greenland 1.07 vs 3.84, TE 1.51 vs 1.73, TOTAL 0.22 vs 0.48.
⚠⚠ **`champions.json` CARRIES A STALE FIGURE**: its L27 rationale says *"+21 at 0.99"*; on the current target it is
**+9.1**. Criterion still holds; the number needs restamping. **NOT changed — it is Marcus's.**

**⛔ For L27 vs L32 the IC cannot adjudicate, for THREE independent reasons:**
1. **Identical k** (50 / 42) ⇒ ΔAIC = ΔBIC = −2ΔlnL exactly. The criteria cannot differ and add nothing.
2. **In-sample asymmetry**: L27's obs_iid ln L̂ fell **23.2 → −66.1** (89 units) purely from being scored on data it was
   never fitted to. **The only common target IS L32's training data.**
3. The IC **PROFILES** sd/ρ per draw, so **L32's bounded `sd_ais` never enters** — it re-fits the very noise model the
   arm changed.

---

## 4. ⚠ NON-OBVIOUS STATE AND TRAPS (09-22d §2 and 09-22b §8 still apply)

- ⛔ **`outputs/bench_ladrillo_L27.md` is on the RETIRED target** (written 09-21 09:24, target rebuilt 13:12; its BRICK
  AIS RMSE is 1.5740 vs every later file's 1.4766). **Use the `L27*` column inside a NEW arm's bench file.**
- ⛔ **`ic_hindcast_obs_sigma.csv` is a SHARED input regenerated by every IC run.** Before comparing two stored
  likelihoods, **check the mtime of every shared input against the last change to the DATA** — two individually valid
  files can be mutually invalid. That is how retraction 2 happened; a `git status` caught it.
- ⛔ **A driver that prints ALLDONE after failed steps + an input check that can never pass = a silent-success
  machine.** Flagged by ANOTHER SESSION reading the log cold. The `step()` + unconditional ALLDONE pattern is
  **INHERITED** (`run_L28/L29/L30.sh` all have it). Fixed and mutation-tested in `run_L32_bench.sh`; gate back-ported
  to `run_L31/L32/L33.sh` with a dated note that it post-dates those runs. ⭐ **Take verification patterns from `ls` of
  a real product, never from an error message.** ⭐ **Log manual recovery in the driver's own step format.**
- ⚠ **`--sd-ais-floor` requires its own starts file.** L27's overdispersed starts all have `sd_ais` 0.019–0.021, below
  L32's floor, so every chain would refuse to start (it dies loudly; pre-flighted).
  `overdispersed_starts_L27r_sdfloor.csv` = those starts with `sd_ais` at floor×1.05, spread preserved, every other
  column byte-identical.
- ⛔ **L31/L32/L33 logposts are NOT comparable to L28's or to each other** — a removed span (79 fewer terms, ~666 of
  bookkeeping), a bound, and a different σ scale. Compare on hindcast statistics and the channels.
- ⚠ **`posterior_predictive_ladrillo.jl`'s `in_sample` was per-SERIES** and mislabelled a restricted arm's early rows
  in-sample (shipped so for one L31 run). Now per-YEAR, span recovered from `ladrillo_priors_<TAG>.csv`'s provenance —
  not a flag a caller can forget — and loud if absent. Mutation-tested both ways.
- ⚠ **`ladrillo_model_comparison.py` needs the UNTAPPED SSP deliverable** (`project_ssps_components_ladrillo.jl 2000
  --tag=X --no-tap`). Easy to omit; its error names the command.
- ⚠ **`diag_ais_flux_split_vs_imbie.jl` reads `ice_flux` only** (and omits `ISO`) — immaterial for non-ramp arms in the
  hindcast, WRONG in a ramp arm or a tipping projection. **Still not fixed; Marcus's call from 09-22.**
- ⚠ **A case-insensitive `Inf` in an error scan matches "inflation"** — it reported a false "1 error per chain" on L33.
- ⚠ **Disposable test tags need a distinctive prefix.** I named one "PREFLIGHT" and my cleanup glob deleted a tracked
  `adapted_cov_PREFLIGHT_seed2026.csv` from the L23 era. Restored from HEAD; nothing was pushed deleted.
- ⚠ Three pre-existing `outputs/*_L24.*` modifications remain in the tree; still not mine to resolve.
- ⚠ **Contention is normal on this machine.** L32 launched at load 3.4 and a 13-process R job joined 7 min later
  (load 68.7, ETA 2h45m → 4h30m); Marcus ruled "let it run". **Read the meter at ~5 min; do not pause another
  session's job.**

---

## 5. ⭐ WHAT IS ACTUALLY OPEN — the decision, and one item that changed today

### 5a. THE DECISION IS A JUDGEMENT, NOT A MEASUREMENT (Marcus's)
**Is the Antarctic module for hindcasting the reconstruction era, or for tracking the modern record?** L32 buys the
satellite era (1.01 vs 1.27, **9× the coverage**), the rate (−1.79 vs −2.42), the dynamics anomaly and the level z; it
pays in 1920–1949 and the length-weighted full-period AIS. **No further computation resolves it.**
**`champions.json` UNTOUCHED — L27 remains champion and the paper's posterior.**

### 5b. ⭐⭐ THE PAPER'S ARGUMENT CHANGED AND THE INSERT NEEDS REVISING **regardless of 5a**
`deliverables/GMD_imbie2026_null_INSERT.md` line 92 argues:
> *"The two posteriors sit at different points on that constraint rather than one being better calibrated than the
> other"*

**L32 shows that constraint is ESCAPABLE** — by fixing a noise model inconsistent with the observed SMB record by
1.5–2.3×, not by moving along the trade-off. That is a stronger and more interesting claim than the null, now measured
on two floors with pre-registered criteria. **The insert currently tells the reader the trade-off is unavoidable given
the module; that is no longer what the evidence says.** It also still needs Marcus's `[MCS]` sentences, and its
Otosaka author list/title are still unverified.

### 5c. Fix the reproducibility inconsistency (independent of everything)
The draft says *"Deliberately removed: IMBIE… IMBIE was dropped from the Antarctic likelihood"* while
`prep_recalib_targets_ext.py` defaults to `AIS_SOURCE = "imbie2026"`. **Anyone re-running from the current repo gets
IMBIE in the likelihood and does not reproduce L27.** Historically true, presently false.

### 5d. If more computation is wanted: a HELD-OUT test
Every comparison so far is contaminated by L32 having been trained on the scored target. The honest way past it is to
score both posteriors on Antarctic data **neither** was fitted to — the regional IMBIE breakdowns (East/West/Peninsula,
all present in `data/observations/raw/imbie2026/`) or GRACE-only 2002–2026. A few hours, and it is the only route that
could settle 5a on evidence.

### 5e. Operational gap if L32/L33 were ever promoted
0 of 7 van Vuuren runs (**the paper's figures are van Vuuren**), 0 of 14 paper figures, no MAGICC-climate swap, no
frozen `benchmark/reference/L32/`. Promotion also means rewriting 5c's paragraph and discarding the null insert's
out-of-sample framing. **The benchmark scores SSPs only, so its pass is necessary and NOT sufficient.**

### 5f. Standing list, unchanged
Comment #12 (code availability), venue (GMD), package extraction for Tony's team, `facts` remote, FACTS/MAGICC scope,
pulse analysis. Figures: FIG 4/FIG 5 direct-labelling landed 09-22 (`lf.direct_label()`); `SRC_COLOR`'s `#ff9900`
contrast 2.14:1 is left as-is (markers + linestyles carry it).
