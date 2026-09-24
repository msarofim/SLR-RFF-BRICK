# Handoff — ⭐⭐ **L34 IS A NULL: the noise fix alone does nothing, and L32's gains came from the TARGET.** ⛔⛔ The whole-model benchmark was scoring every arm on the CANDIDATE's own observations — found, fixed, and the "WIN" it printed is quarantined. L33 benchmarked; all seven arms now on ONE ruler

**Start here.** Self-contained. Supersedes `handoff_2026-09-24_L34_the_missing_cell.md` for everything
after its §2 (that file's §3 on the held-out test and §4 on the target provenance still stand).
Records CHANGELOG **09-24b, 09-24c**. Commits `464b7d4` → **`aa763d2`** on `ladrillo-dev`,
⚠ **UNPUSHED at time of writing.** Memory: `ais_noise_floor_is_target_dependent`,
`gate_checked_a_file_the_code_never_read` (both new), `INDEX_ais_imbie.md`, `INDEX_diag.md` updated.

---

## ⛔⛔ 0. RETRACTIONS — the 09-23 list STILL BINDS, and there is a NEW one

**Still binding, do not re-quote:** ΔlnL **+10.0 / +7.6 / +5.6** (ar1_prof) or **−11.7 / +23.4**
(obs_iid) for L27-vs-L32; L27 ΔBIC **+20.8**; *"L32 strictly dominates L27"*; *"every iid-like
scorer prefers L27, every autocorrelation-allowing scorer prefers L32."*

⛔ **NEW 09-24 — do not quote any number from the FIRST L34 bench.** `L27*` **0.56**, L34 **0.58**,
BRICK **1.5740**, and the read-out's **"PRIMARY VERDICT: WIN"** are all ARTEFACTS of the ruler bug
(§2). They are quarantined at `outputs/quarantine/20260924_bench_obs_from_candidate/` with a README.
The correct figures are `L27*` **0.70**, L34 **0.73**, BRICK **1.4766**, verdict **AMBIGUOUS**.

⚠ **NEW 09-24 — 09-23c's "L33 is the better compromise of the two" is SUPERSEDED** by L33's
benchmark (§4). That reading rested on L33's better cumulative level (z −1.21 vs −1.45); the
whole-record scorer reverses it.

---

## 1. ⭐⭐ THE RESULT: L34 IS A NULL, AND THE 2×2 IS AN INTERACTION

**L34 = L27's Frederikse target + `--sd-ais-floor=smb`** — the missing cell of the 2×2.

**PRIMARY: AMBIGUOUS.** Full-period AIS **0.73 σ** vs `L27*` **0.70**. The pre-registration set
WIN ≤ 0.70 / LOSS ≥ 0.80 and requires 0.70–0.80 be reported **AS ambiguous, not rounded to a side**.
GUARD passed (≤ 0.010 σ) — ⚠ but with **near-zero power by construction**: L34 changes only the
Antarctic noise term, so a PASS there is not evidence and was not presented as any.

**MECHANISM: the floor did not fire.** `diag_ais_channel_separation.jl`, 1000 draws:
L27 **−116.18 ± 1.48**, L34 **−117.19 ± 1.58** ⇒ **indistinguishable from zero** (IMBIE −167.2).

⭐⭐ **Filling the cell shows the 2×2 is an INTERACTION, not two additive effects:**

| | free `sd_ais` | floored | **floor effect** |
|---|---|---|---|
| **Frederikse** | L27 −116.7 | **L34 −118.0** | **−1.4** |
| **IMBIE-2026** | L28 −71.4 | L32 −133.3 | **−61.9** |
| **target effect** | **+45.2** | **−15.3** | |

The floor does nothing on Frederikse and is enormous on IMBIE; the target swap **changes sign**
with the floor on/off. ⇒ **L32's gains came from the TARGET, not the noise specification, and the
champion CANNOT be improved without the target swap.** The 09-24 §5a hope — improve L27 while
keeping the paper's Frederikse basis and the IMBIE-null framing — **does not exist.**

Confirmed on **two independent routes** agreeing to ±3 Gt/yr (flux-split, and the canonical
channel-separation). ⇒ memory `ais_noise_floor_is_target_dependent`.

⚠ **A cost that was NOT in the pre-registered criteria:** the floor pushed `rho_ais`
**0.893 → 0.926**, toward the regime where the level channel cannot distinguish a constant
discharge offset from a late divergence (indifference ratio 1.001 at ρ 0.966, 1.74 at 0.90). **A
better-specified noise term bought a LESS identifiable level channel.**

Run health, for the record: floor **binds** (min 0.03259 exactly, p05 0.03262, 62.5 % within 2 %);
noise-mode gate PASS on all 4 seeds; SLR R-hat 1.000, ESS 1334/1390; 7 AIS marginals unconverged
and accepted on the deliverable criterion, **better than the champion's** (`ais_runoff_Ton` R-hat
1.141 vs L27's 1.313).

---

## 2. ⛔⛔ THE RULER BUG — READ THIS BEFORE TRUSTING ANY BENCH FILE

`python/bench_ladrillo.py` block [H] took `obs` from the **CANDIDATE's own postpred**
`<component>_obs` column (always present for ais/gsic/gis/steric, so the target fallback was dead
code). Worse, `fixed("targets")` resolves to a **FROZEN Frederikse copy** under
`benchmark/reference/_fixed/` ⇒ **the live target was never read by that block at all.**

⇒ `run_L34_bench.sh`'s md5 gate on `outputs/recalib_targets_ext.csv` **gated a file the scoring
never opened**, and its header's "THE TARGET MUST BE THE IMBIE BUILD WHEN THIS RUNS" described a
mechanism that did not exist.

**Harmless for months** (all arms shared one target); **not harmless after 09-21**. Each bench file
was silently scored on whichever target its candidate was fitted to. **L32 got the intended
out-of-sample comparison BY ACCIDENT.** L34 was scored IN-SAMPLE.

⭐⭐ **THE TELL, and the cheapest lesson here: two arms that CANNOT have changed both moved, by the
SAME additive −0.0704 cm** (the frozen `L27*` snapshot and frozen BRICK 2.0). A common offset on
frozen arms is a **ruler change, not a data change** — visible without knowing the cause. **Keep one
must-not-move arm in every comparison.** ⇒ memory `gate_checked_a_file_the_code_never_read`.

⭐ **This CORRECTS a standing diagnosis:** `run_L34_bench.sh`'s header blamed the BRICK
1.5740-vs-1.4766 discrepancy on the 09-21 target rebuild. **Wrong cause** — it is this bug. The
header's *advice* (read the `L27*` column inside a new arm's file, never the standalone
`bench_ladrillo_L27.md`) survives, but only because each file is internally consistent.

**Fixed** (`d176403`): obs from the **target file**, named and md5-stamped in every report;
`--obs-source=candidate` reproduces the old behaviour so historical files stay re-derivable; σ
denominators still from the frozen copy (**they must not move or no σ is comparable across files**);
and a **per-component divergence banner** when the candidate's obs disagree with the scoring target.

**Verified, not assumed:** `--selftest` passes; legacy mode reproduces the quarantined bench
**identically**; L34 re-scored gives `L27*` 0.70 and BRICK 1.4766 as expected; and **L32 re-scored in
target mode is byte-identical to its legacy file** ⇒ the L27-vs-L32 reading is **UNAFFECTED**.
Re-scoring every arm moved **only L27** (0.56 → 0.70) — the one Frederikse-fitted arm with a bench.

⚠⚠ **CHOOSING THE TARGET IS NOT NEUTRAL.** L27/L34 are in-sample on Frederikse; L28–L33 on IMBIE.
**No single AIS ruler is fair to both families.** The default is the live target and the choice is
now stamped and banner-flagged, but **dual-target reporting is still OWED** if the comparison is to
be presented as neutral. Marcus's call; not done.

---

## 3. ⭐ ALL SEVEN ARMS ON ONE RULER — a single axis with a four-point frontier

AIS RMSE (σ), every arm scored on the IMBIE target against the frozen `L27*`:

| arm | what it is | full | 1920–49 | 1950–92 | 1993–2026 | TOTAL |
|---|---|---|---|---|---|---|
| **L27** | Frederikse, free `sd_ais` — **champion** | **0.70** | 0.08 | 0.37 | 1.27 | 0.26 |
| L34 | Frederikse + SMB floor | 0.73 | 0.07 | 0.34 | 1.32 | 0.26 |
| **L32** | IMBIE + SMB floor | 0.88 | 1.07 | 0.47 | 1.01 | 0.22 |
| L33 | IMBIE + floor cut 34 % | 1.11 | 1.43 | 0.60 | 0.96 | 0.22 |
| L29 | IMBIE, ρ capped 0.90 | 1.45 | 1.85 | 0.64 | **0.52** | 0.21 |
| L28 | IMBIE, free `sd_ais` | 1.53 | 1.89 | 0.62 | 0.67 | 0.20 |
| L30 | IMBIE + discharge ramp | 1.53 | 1.93 | 0.64 | 0.73 | 0.20 |

**Pareto frontier: L27, L32, L33, L29.** Dominated: **L34** (worse than L27 on both axes — the
cleanest statement of the null), **L28** and **L30** (both worse than L29 on both).

⚠ **"L32 wins the satellite era" is only true against L27.** L29 (0.52), L28 (0.67) and L30 (0.73)
all beat it there. L32's distinction is being the best-balanced frontier point.

---

## 4. L33 CLOSED — it does not displace L32

Benchmarked 09-24 (`run_L33_bench.sh`, ALLDONE 0 failed / 0 missing). Full period **1.11 σ** vs
L32's 0.88; satellite era **0.96** vs 1.01. **Not dominated**, but a poor exchange rate:
**0.23 σ of full period for 0.05 σ of satellite era, ≈ 4.6 : 1**, where L27 → L32 trades at 0.69 : 1.

⚠ **Second time in this arc a favourable summary statistic failed to predict the whole-record
scorer** (L33's level z −1.21 vs L32's −1.45 pointed the other way). The first was 09-23d.

---

## 5. WHAT IS OPEN

### 5a. THE DECISION IS STILL MARCUS'S JUDGEMENT, and L34 did NOT change the option set
Hindcast the reconstruction era (**L27**) or track the modern record (**L32**). **No scorer settles
it**: the IC cannot adjudicate the pair (identical k ⇒ ΔAIC = ΔBIC = −2ΔlnL; the only common target
IS L32's training data; the IC profiles σ/ρ so L32's bounded `sd_ais` never enters), and **no
held-out test can be built** (§3 of the previous handoff — the regional breakdown is an exact
partition, GRACE is spliced into both and biased toward L32). **Either way the 7 van Vuuren runs and
14 figures are owed.** `champions.json` **UNTOUCHED**; **L27 remains champion.**

### 5b. Deliverable shipped, awaiting Marcus's text
`deliverables/L27_vs_L32_proscons_for_TonyWong.{md,docx}` — number-dense, `[MCS]` placeholder for
framing and the ask of Tony, **no recommendation embedded**. Built by `build_tony_memo_docx.sh`
(pandoc only; refuses to overwrite a `.docx` newer than its `.md`; independent-reader gate
MUTATION-TESTED — a different valid 5840-word `.docx` passes a word-count check and is caught only
by the title assertion).

### 5c. ⚠ TWO TRACKED-FILE INCONSISTENCIES, both Marcus's, both untouched
1. **The COMMITTED `outputs/recalib_targets_ext.csv` is the FREDERIKSE build (`070f74ab`) while the
   code default is `imbie2026`** ⇒ a fresh clone and a rebuild disagree about the target.
2. **`champions.json` carries a stale "+21 at 0.99"**; on the current target it is **+9.1**. The
   criterion holds; the figure needs restamping.

### 5d. Standing list, unchanged
Comment #12 (code availability), venue (GMD), package extraction for Tony's team, `facts` remote,
FACTS/MAGICC scope, pulse analysis. The null insert still needs Marcus's `[MCS]` sentences (its
Otosaka reference is now VERIFIED against Crossref — 58 authors, Sci. Data 13, 1301, 09-24b).

---

## 6. ⚠ NON-OBVIOUS STATE AND TRAPS

**New this session:**
- ⛔ **Never compare a σ ACROSS bench files written before 09-24** — each was on its candidate's own
  target. Files written after carry a stamped ruler line; check it.
- ⛔ **L34's logpost (~779) is comparable to NEITHER L27's** (bounded vs free σ) **nor L32's**
  (different target). Compare on hindcast statistics and channels only.
- ⚠ `diag_ais_channel_separation.jl` used to write **untagged** outputs and clobbered them in place.
  The 09-23 L27/L28/L32/L33 run was preserved as
  `outputs/diag_ais_channel_separation{,_summary}_20260923_L27L28L32L33.csv` **before** L34's run;
  the tagging fix landed separately (`04e030e`) and mine is at
  `diag_ais_channel_separation_L27L34{,_summary}.csv`.
- ⚠ `bench_ladrillo.py` is now ~4 s per arm and postpred MODEL columns are target-independent, so
  **re-scoring every arm is a scoring change, not a re-run.** Cheap; use it.
- ⚠ `INDEX_diag.md` is at **17,291 B** of an 18,432 hard ceiling (over soft). A split is approaching
  but not forced, and the natural split line is not obvious — what remains is one coherent
  enumerated family. Flagged, not done.

**Carried forward, still true:** `ic_hindcast_obs_sigma.csv` is a SHARED input every IC run
regenerates — check every shared input's mtime against the last DATA change before comparing two
stored likelihoods. `diag_ais_flux_split_vs_imbie.jl` reads `ice_flux` only and omits `ISO` —
immaterial for non-ramp arms (L34 is non-ramp), WRONG in a ramp arm. A case-insensitive `Inf` in an
error scan matches "inflation". Three pre-existing `outputs/*_L24.*` modifications remain in the tree.
