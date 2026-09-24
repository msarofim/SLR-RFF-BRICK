# Handoff — ⭐⭐ **The L27-vs-L32 full-period ranking IS σ-SENSITIVE and L27's win is EARNED PRE-1979, but the inflation factor CANNOT be measured (N_eff 0.6).** The cover email's SMB mechanism is only ~a quarter of the story. **NEXT JOB: step 2, the `--ais-fit-from=1979` held-out test** — pre-flight done, it is CLEAN

**Start here.** Self-contained. Follows `handoff_2026-09-24b_L34_null_and_the_ruler_bug.md`, which
still stands for L34, the ruler bug, L33, and the seven-arm frontier. Records CHANGELOG **09-24d,
09-24e**. Commits `700d3d6` → **`b91559a`** on `ladrillo-dev`, ⚠ **all UNPUSHED, together with the
four before them (`aa763d2` back through `464b7d4`) — nine commits unpushed in total.**
Memory: `ais_target_divergence_predates_2018`, `sigma_inflation_unmeasurable_from_two_offset_products`
(both new), `INDEX_ais_imbie.md` + `INDEX_diag_conv.md` updated.

---

## ⛔ 0. RETRACTIONS — the 09-24b list still binds, and there is ONE new one

**Still binding, do not re-quote:** ΔlnL +10.0 / +7.6 / +5.6 or −11.7 / +23.4 for L27-vs-L32;
L27 ΔBIC +20.8; *"L32 strictly dominates L27"*; *"every iid-like scorer prefers L27…"*; every number
from the FIRST L34 bench (`L27*` 0.56, L34 0.58, BRICK 1.5740, "PRIMARY VERDICT: WIN").
Verified 09-24c: **all of these still sit behind a retraction marker in memory, 0 unmarked.**

⛔ **NEW 09-24e — do not quote *"the break-even is NOT reachable from measured evidence."*** My first
pass printed it by comparing a point estimate (1.56) against a threshold (1.60) **with no error bar**.
With the bar it is meaningless (§3). The script now **gates that verdict on N_eff ≥ 2** and refuses.

---

## 1. Marcus's memo edits are IN THE SOURCE, and the sync is PROVEN

`deliverables/L27_vs_L32_proscons_for_TonyWong.mcs.docx` came back **edited directly** — no tracked
changes, no comments (`w:ins`/`w:del` = 0, `comments.xml` empty). **14 edits, all cuts plus two
rewrites**, all pulled into the `.md` per `marcus_edits_docx_directly`.

⭐ **GATE, not an assertion:** rebuilt the `.docx` from the synced `.md` and diffed the extracted text
with an independent reader — **identical apart from three trailing spaces.**

**The cuts are editorially coherent and should be respected on any future rebuild:**
- **Project-management content gone from BOTH arms symmetrically** — L27's *"Shipped: 7/7 runs,
  14/14 figures"* AND L32's *"Zero deliverables"* / *"costs the IMBIE-null framing"*. Tony cannot
  weigh our sunk cost as evidence and leaving one side in would be a thumb on the scale.
- Method commentary gone (the L33 summary-statistic paragraph, *"second time in this arc"*) — per
  `drafted_text_no_fix_history`.
- §2a's seven-arm frontier table gone; the memo is now the two-way decision it claims to be.
- Emphatic framing softened; Q1 rewritten in his voice; the one-sided GRACE test out of §6 and §8.
- Byline and the `[MCS]` placeholder removed — the cover email is the framing.

⚠ **THREE COHERENCE GAPS his cuts opened, flagged to him, NOT changed:**
1. **§3 poses the net/dynamics identity as unbreakable and nothing resolves it** — both the "L32 is
   the first arm off that line, by 38.9 Gt/yr" paragraph and the L32 pro *"Only arm to escape the
   net/dynamics identity trade-off"* were cut. One sentence would fix it.
2. §7's heading is *"Closed, and open"* and nothing open is listed.
3. The memo now carries **no author and no date**; the provenance footer has neither.

---

## 2. ⭐⭐ THE COVER EMAIL'S MECHANISM IS ONLY ~A QUARTER OF THE STORY

The draft email says the full-period loss happens *"in part because the SMB snowfall over 2018-2023
is pretty anomalous."* Tested by diffing the two target builds directly —
`python/diag_target_divergence_frederikse_vs_imbie.py`, same prep script, only `--ais-source` flipped
(Frederikse `070f74ab` at HEAD vs IMBIE `eb768cd9` in the tree):

| window | mean d (IMBIE − Frederikse) | rate diff |
|---|---|---|
| 1900–1978 | **−0.1341, EXACTLY CONSTANT (sd 6e-17)** | — |
| 1979–1992 | −0.109 | +0.0088 cm/yr |
| 1993–2005 | −0.007 | +0.0077 |
| 2006–2017 | **+0.148** | +0.0102 |
| 2018–2023 | +0.214 | +0.0184 |

⭐ **76 % of the cumulative divergence accumulates BEFORE 2018** (+0.352 cm over 1979→2017 vs
+0.109 cm over 2018→2023). IMBIE runs faster in **every** window and the **largest level offset,
+0.217 cm, is reached at 2017 — one year before the anomalous window opens.**

⚠⚠ **BUT DO NOT DELETE THE COUNTER-CONSIDERATION.** Split by **observational regime** instead:
**19 %** in 1979–92 (neither product satellite-constrained) and **81 %** in 1993–2023 (where IMBIE's
reconciliation actually applies). **Both facts hold at once.** The divergence predates 2018 **and**
it sits where IMBIE's advantage is real, so *"IMBIE is the better product"* IS load-bearing — it is
just not the same argument as *"therefore L32."*

⭐ **The 1920–49 collapse (L27 0.08 σ → L32 1.07 σ) cannot come from early-record DATA:** pre-1979
the builds are identical up to a **constant −0.1341 cm** (= 0.80 of the memo's 0.1674 cm ruler, from
the IMBIE build's join-match over (1979, 1988)). It is **parameter re-tuning to chase the faster
satellite-era rate** — and L32 is 13× worse there than an arm that never saw IMBIE, *on IMBIE's own
ruler.*

---

## 3. ⭐⭐ STEP 1 (RUN): the ranking IS σ-sensitive; the factor is UNMEASURABLE

`python/diag_ais_prescore_sigma_sensitivity.py`. **Scoring only, no refit, standing ruler untouched.**
Generalises the bench's SCALAR denominator (`bench_ladrillo.py:682,1309`) to per-year:
`σ_y(F) = F·σ̄` before 1979, `σ̄` after. Rationale: **62 % of the full-period scoring window (79 of
127 yr) is the pre-1979 Frederikse-only segment**, where L27's win is earned and no satellite
constraint exists.

⭐ **GATE: at F = 1 it reproduces the published one-ruler numbers exactly** — `L27*` **0.7035** vs
0.70, L32 **0.8812** vs 0.88. **Mutation-tested:** a wrong published value IS caught; ⚠ **a wrong
`SPLICE_START` is NOT** — at F=1 the denominator is uniform so the splice year never enters. Blind
spot documented at the gate; 1979 rests on §2's diagnostic instead.

| F | `L27*` | L32 | |
|---|---|---|---|
| 1.00 | 0.703 | 0.881 | published |
| 1.41 | 0.689 | 0.726 | |
| **1.52** | 0.687 | 0.695 | **enters the bench's own 2 % dead band ⇒ INDISTINGUISHABLE** |
| **1.60** | 0.686 | 0.686 | **break-even** |
| 3.00 | 0.677 | 0.574 | |

⭐ **Relaxing to F = 3 gains L32 35 % against L27 4 %** ⇒ direct confirmation **L27's full-period win
is EARNED pre-1979.** F ≈ 1.5 is a modest inflation (0.167 → 0.251 cm on a 79-yr unconstrained
segment), so the flip is not exotic. And *indistinguishable* arrives **before** either arm "wins".

⛔⛔ **THE FACTOR CANNOT BE MEASURED THIS WAY — the substantive finding.**
`RMS((IMBIE − Frederikse)/σ_Frederikse)` over 1979–2017 = **1.56, sitting AT the 1.60 break-even.**
**lag-1 ρ = 0.968 over 39 yr ⇒ N_eff = 0.6**, 1-sd bar **±1.39** (range 0.17–2.95). **The difference
between two systematically offset reconstructions is ONE SLOW CURVE, not N samples.**
⚠⚠ **Its stability is a TRAP:** 1.56 / 1.60 / 1.57 / 1.56 across four checkable windows looks like
robustness and is **re-measurement of the same curve.**

⇒ **Step 1 neither clears L27 nor crowns L32. It RELOCATES the decision.** `champions.json`
**UNTOUCHED; L27 remains champion.**

---

## 4. ⭐⭐ NEXT JOB — STEP 2: the `--ais-fit-from=1979` HELD-OUT TEST

**Why this and not more σ work:** it needs **no choice of σ**. That is the whole point.

### 4a. ⭐ PRE-FLIGHT IS DONE AND THE TEST IS CLEAN
The obvious worry was that pre-1979 AIS stays constrained through the total-SLR term. **It does not:**
`julia/calibrate_mcmc_ext.jl:1462` — `const SERIES = [:ais,:gsic,:gis,:steric]  # the total is NOT a
likelihood term`, and `RHO_MAX` is sized to `length(SERIES)`. The `dang` series is built for
diagnostics only. ⇒ **`--ais-fit-from=1979` genuinely removes pre-1979 AIS from the objective.**
⚠ Confirm at the gate anyway: lines 635–639 PRINT the fit windows **read back off the series, never
re-typed**, and warn that pre-1979 is *"OUT-OF-SAMPLE, not absent"*. Read that line in the log.

### 4b. THE ARM
**L35** = the **IMBIE target build** + `--ais-fit-from=1979`. Copy `run_L34.sh` as the template
(4 seeds, the noise-mode gate, the ALLDONE counter pattern). ⚠ The committed
`outputs/recalib_targets_ext.csv` is the **Frederikse** build while the code default is `imbie2026`
(§6.2) — **assert the md5 is `eb768cd9` at the top of the runner**, and note 09-24b's lesson that a
gate must point at a file the scoring actually reads.

### 4c. ⚠⚠ PRE-REGISTER THE READ BEFORE RUNNING — thresholds first, numbers second
The question: **does an arm fitted ONLY to IMBIE 1979–2023 PREDICT Frederikse's 1900–1978?**

- **Bound from an OBSERVATION, not from the code under test** (`threshold_from_obs_or_law`): the
  Frederikse target's **own published 1σ band** over 1900–1978. **PASS = out-of-sample pre-1979
  RMSE ≤ 1.0 σ.** Do NOT derive the bound from L27's or L32's own agreement — that is re-baselining.
- **If no absolute bound is defensible, assert an ORDERING instead:** is L35's pre-1979 error nearer
  L27's 0.08 σ or L32's 1.07 σ?
- ⚠ **STATE THE ASYMMETRY AT THE GATE. This test is ONE-SIDED, in the OPPOSITE direction from the
  GRACE test.** A **PASS is informative** (the two products are reconcilable, the trade-off was an
  artefact of the joint fit, and there is no dilemma). A **FAILURE is AMBIGUOUS** — the held-out data
  IS the product under doubt, so it cannot separate "the model is wrong" from "Frederikse is wrong."
- ⚠ **Measure the POWER before believing a pass** (`no_power_null`): 79 unconstrained years with a
  free `sd_ais` may fit almost anything. A synthetic-recovery check is the honest companion.

### 4d. What it cannot do
It cannot make L27-vs-L32 an IC comparison (identical-k problem stands, `INDEX_ais_imbie`), and it
does not retire §5a of 09-24b: **either way the 7 van Vuuren runs and 14 figures are owed.**

---

## 5. FILES

**New:** `python/diag_target_divergence_frederikse_vs_imbie.py`,
`python/diag_ais_prescore_sigma_sensitivity.py`,
`outputs/diag_target_divergence_frd_vs_imbie.csv`,
`outputs/diag_ais_prescore_sigma_sensitivity.csv`, this handoff.
**Modified:** `deliverables/L27_vs_L32_proscons_for_TonyWong.{md,docx}` (synced + rebuilt),
`CHANGELOG.md`. **Committed but untouched in substance:** `.mcs.docx` (his file, now tracked).
**NOT touched:** `champions.json`, the standing ruler, `benchmark/reference/_fixed/`.

---

## 6. ⚠ NON-OBVIOUS STATE AND TRAPS

**New this session:**
- ⛔ **Never quote a z past 2018 from a Frederikse-build diagnostic.** That build's AIS σ collapses
  **0.1023 cm (2018) → exactly 0.0100 cm (2019)** and holds through 2024 — a **10.2× cliff** at the
  GRACE-FO splice (`IMBIE_SIG_FLOOR`, `prep_recalib_targets_ext.py:149,267`). The **IMBIE** build has
  **no cliff** (0.079 → 0.121 cm). This is what makes `diag_imbie2026_vs_targets_windows_L32.csv`
  report **19–27 σ**. ⭐ Same tell as 09-24b's ruler bug: **a step that large on unchanged data is
  the ruler.**
- ⚠ **A THIRD difference between the arms the memo does not state.** The fit is clean — `ϵband`
  (`calibrate_mcmc_ext.jl:586`) floors the likelihood σ at 0.05 cm, so 0.01 never reached the
  objective (**verified, not assumed**). But over 2019–2026 **L27's fitted target carries σ = 0.05 cm
  while L32's carries 0.085–0.121 cm** ⇒ **L27 weights its GRACE tail ~2× more tightly**, in exactly
  the window the decision turns on. The memo's §1 claims two differences. **Marcus's call.**
- ⚠ `σ̄` = 0.1674 cm is the **mean per-year σ over the whole frozen Frederikse record** — which
  **includes the 0.01 cm cliff years**, dragging it down. Common to every arm so it cannot change a
  ranking, but it makes every σ-normalised score slightly larger than a cliff-free σ̄ would.

**Carried forward, still true:** never compare a σ across bench files written before 09-24;
L34's logpost is comparable to neither L27's nor L32's; `ic_hindcast_obs_sigma.csv` is a SHARED input
every IC run regenerates; `diag_ais_flux_split_vs_imbie.jl` omits `ISO` and is wrong in a ramp arm;
a case-insensitive `Inf` scan matches "inflation"; three `outputs/*_L24.*` modifications remain.

### 6.2 Tracked-file inconsistencies, both Marcus's, both untouched
1. **Committed `outputs/recalib_targets_ext.csv` is the FREDERIKSE build (`070f74ab`) while the code
   default is `imbie2026`** ⇒ a fresh clone and a rebuild disagree. ⭐ **If "IMBIE is the better
   product" is adopted, this resolves in a specific direction** — the committed file should become
   the IMBIE build, not the reverse.
2. **`champions.json` carries a stale "+21 at 0.99"**; on the current target it is **+9.1**.

### 6.3 Memory tree
09-24c pass: the dangling `[[suspicious_uniformity]]` link removed (that rule is **promoted** to
`~/.claude/CLAUDE.md`, so no file exists by design); the **81 %** regime split added to
`ais_target_divergence_predates_2018` **with its `description:` and index line restamped in the same
edit** (the dominant failure mode of the 09-24 audit). All 09-24 retracted figures re-verified behind
markers, **0 unmarked**.
⚠ **`MEMORY.md` is 15,223 B of CONTENT** (21,460 raw — **strip the `<!-- -->` blocks first**, this is
the sixth time the raw count would have raised a false alarm): over soft 12 KB, **well under** hard.
⚠ **`INDEX_ais_imbie.md` is now 16,957 B** (was 14,386 at session start — I added ~2.6 KB): over soft,
under hard. **A split was deliberately NOT done** — it is the live, unresolved arc and
`INDEX_ais_imbie_arch.md` is *provenance only, never live state*, so misfiling live state there is
worse than being over soft. The archive tier has room (8,008 B). **Flagged, not done.**
⚠ `INDEX_diag.md` 17,291 B and `INDEX_ccx_ref.md` 18,129 B are the closest to the 18,432 hard ceiling.
