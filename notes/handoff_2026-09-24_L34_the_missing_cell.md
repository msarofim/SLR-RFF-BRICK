# Handoff — ⭐⭐ **L34: THE MISSING CELL OF THE 2×2 (L27 + the SMB noise floor), RUNNING.** §5d's held-out test is CLOSED — neither candidate dataset is held out. The calibration target's provenance stamp had never once reached a file (09-23 20:00 → 09-24 07:30)

**Start here.** Self-contained. Supersedes `handoff_2026-09-23_option6_works_but_L27_still_wins_the_bench.md` for
everything after its §0 — that file's §1 (the option ladder and L32/L33's results), §2 (the benchmark) and §3 (the IC)
still stand and are not repeated in full. Records CHANGELOG **09-23h, 09-23i, 09-24a**. Commits `064c517` → **`96494ab`**
on `ladrillo-dev`, all pushed. Memory: `heldout_is_a_property_of_the_target_code`, `to_csv_drops_dataframe_attrs` (both
new), `ic_cannot_adjudicate_a_noise_change` (description restamped), `INDEX_ais_imbie.md` (corrected + split),
**`INDEX_ais_imbie_arch.md` (new)**, root `MEMORY.md` updated.

---

## ⛔⛔ 0. THE 09-23 RETRACTIONS STILL BIND — DO NOT RE-QUOTE

Both retractions from the previous handoff stand unchanged, and their numbers keep resurfacing:

⛔ **Do not quote:** ΔlnL **+10.0 / +7.6 / +5.6** (ar1_prof) or **−11.7 / +23.4** (obs_iid) for L27-vs-L32; L27 ΔBIC
**+20.8**; *"L32 strictly dominates L27"*; *"every iid-like scorer prefers L27, every autocorrelation-allowing scorer
prefers L32."* The corrected figures are ΔlnL +3.1 / +0.9 / +0.6 and obs_iid **+77.6** (both arms favour L32), and the
IC cannot adjudicate this pair at all.

⚠ **These were still live in the memory index at the start of this session.** `INDEX_ais_imbie.md`'s NEWEST entry was
the retracted 09-23e reading, with **no 09-23g correction anywhere in the index**, and the corrected memory file's
frontmatter `description` — the field used for recall relevance — still carried *"the two arms DISAGREE."* Both are now
restamped. ⭐ **A correction written into a memory file's BODY does not propagate to its `description` or to the index
line that points at it.** Fixing one of the three is not fixing the claim.

---

## 1. ⭐⭐ WHAT IS RUNNING: L34 = L27 + `--sd-ais-floor=smb`

Marcus, on being shown that L32 wins the satellite era but loses the full-period AIS to L27: **"What about fixing the
noise specification on L27?"** That names a cell nobody had run.

| | free `sd_ais` | floored `sd_ais` |
|---|---|---|
| **Frederikse target** (L27's) | **L27** — champion | **L34** ← running |
| **IMBIE-2026 target** | L28 | L32 / L33 |

⭐ **L32 changed TWO things at once** — the AIS target AND the noise model. **L34 isolates the noise fix on the
champion's own target**, which is the only way to learn which of the two produced L32's dynamics win and which produced
its full-period loss.

⭐⭐ **And it is not tidiness.** 09-23b measured that a misspecified noise term does not merely under-disperse the
posterior — **it BIASES THE MEAN**, because the mean is made to do the noise's job (L32's AIS hindcast bias at 1900 went
−0.524 → −0.154 when the floor went on, the OPPOSITE of the prediction). **L27 carries the same misspecification:** its
fitted `sd_ais` is **0.02162 cm** against the SMB-derived floor of **0.03259** — a factor **1.51 below**. So the
champion's mean may be biased too, and the floor may improve *the very statistic L27 currently wins on*.

### 1a. Pre-flight — passed on all three, and the binding check is the one that mattered
30k, one chain, on L27's own target:

| check | result |
|---|---|
| floor value | **0.03259 cm**, identical to L32's ⇒ the derivation is INDEPENDENT of which level target is live |
| **floor BINDS** | **YES** — p05 **0.03262** vs floor 0.03259, min exactly on it, **64.2 %** of draws within 2 % (L32 72 %, L33 48 %) |
| sampler not crippled by the bound | acceptance **0.238** (L31 0.237, L32 0.246) |

⚠ **Check the binding before reading ANY sensitivity arm** — against a slack constraint you are comparing nothing.

### 1b. ⭐ PRE-REGISTERED CRITERIA — fixed by Marcus BEFORE any number existed
- **PRIMARY — FULL-PERIOD AIS RMSE** in the whole-model benchmark, scored on the live IMBIE target in ONE run against
  the frozen **`L27*`** column. **WIN ≤ 0.70 σ. LOSS ≥ 0.80 σ. 0.70–0.80 is AMBIGUOUS and must be said so.**
  (For scale: `L27*` reads 0.70 and L32 0.88 in the L32 bench file.)
- **MECHANISM** 2018–23 dynamics anomaly vs L27's −119.1 (IMBIE −167.2). Confirms the floor fired; does NOT decide promotion.
- **COST A** AIS hindcast bias @1900/1950/2018/2025 vs L27 — report either way. ⚠ The L32 prediction was wrong; a
  prediction is not a criterion.
- **COST B** SSP AIS p05–p95 @2100/2300 vs L27. **A win that is only a wider posterior is no win.**
- **GUARD** the four non-Antarctic components within ~0.02 σ of L27.
- ⚠ **NOT a criterion:** `sd_ais` sitting on its bound. True by construction.

### 1c. How to run and read it
```
bash run_L34.sh          # 4 chains x 2e6, seeds 2026-2029, ~2h45   log = outputs/log_L34.txt
bash run_L34_bench.sh    # AFTER the above completes               log = outputs/log_L34_bench.txt
```
**Launched 09-24 06:11**, commit `f7d101b`, load 2.17, PIDs 22573–22576. At 07:25 it was **48 %**, ETA ~1 h 20, all four
chains alive, load 8.35.

⭐⭐ **THE BENCH SCORES L34 ON THE *IMBIE* TARGET THOUGH IT WAS FITTED ON FREDERIKSE — DELIBERATELY.** That puts L34 in
**exactly L27's out-of-sample position**, so L34-vs-L27 is a clean one-axis comparison (the noise floor) with the target
held fixed on both sides of the ruler. Scoring it on its own training target would hand it the in-sample advantage that
09-23d spent a whole session stripping out of the L32 reading. `bench_ladrillo.py` re-scores the frozen
`benchmark/reference/L27/` snapshot in the same run and emits it as `L27*` — **that column is the only valid ruler;
never `outputs/bench_ladrillo_L27.md`, which is on the retired target.**

### 1d. ⚠ L34 IS NOT A "PURE FREDERIKSE" ARM AND MUST NEVER BE WRITTEN UP AS ONE
The floor is derived from **IMBIE's SMB record** at run time. It is a **VARIABILITY** channel, not a **LEVEL** one —
genuinely different information from the level series L28/L32 fit — but IMBIE information does enter L34. Same import
as L32; only the level target differs. Say it at the gate.

---

## 2. ⛔⛔ THE OPERATIONAL HAZARD: THE SHARED TARGET FILE

L34 needs the **Frederikse** target live while **nine** other drivers gate on the **IMBIE** md5. This is the exact class
that produced retraction 2 on 09-23g (two individually valid files, mutually invalid).

`run_L34.sh` therefore rebuilds the Frederikse target, **gates on md5 `070f74ab…`**, and **restores the IMBIE build
(`eb768cd9…`) through an `EXIT INT TERM` trap, verified by md5.** ⭐ **Both gates were MUTATION-TESTED:** a deliberately
wrong expected md5 exits 2 **and still restores**; a SIGTERM mid-run restores.

⚠⚠ **THE TRAP'S REAL LIMIT WAS MEASURED, NOT ASSUMED.** Bash **defers a signal trap until the running foreground
command returns** — in the test a TERM sent at 06:06:26 did not restore until the stand-in `sleep` ended at 06:07:14.
So during the ~3 h `wait`:
- ⇒ **KILL THE CHAINS BY PID** (they are listed in `outputs/log_L34.txt`). `wait` then returns and the trap runs.
- ⇒ `kill` on the DRIVER defers the restore; **SIGKILL never restores at all.**
- ⇒ If the target IS left swapped, nothing reads it silently: **all nine IMBIE drivers refuse to start.** Recover with
  `python python/prep_recalib_targets_ext.py` (no flags = the IMBIE build).
- ⇒ **Do not launch an IMBIE arm against this window.**

⚠ **A missing log line was chased rather than waved off, and it is worth knowing why.** The per-chain `sd_ais FLOOR`
line does **not** appear in the chain logs — which, taken at face value, would mean an UNFLOORED arm labelled L34, i.e.
a second L27 and three hours wasted. Re-running the driver's **exact** flag string for 1 iteration printed the floor
line, so the omission is **stdout block buffering** (the progress bar is unbuffered stderr; the `println` is buffered
stdout). The end-of-run per-chain FLOOR GATE reads the value back regardless. ⭐ **A gate whose evidence is a log line
can be defeated by buffering; confirm against the parameter or a re-run, not the log.**

---

## 3. ⛔ §5d IS CLOSED — THE HELD-OUT TEST CANNOT BE BUILT (09-23h)

The previous handoff's §5d named the only route that could settle L27-vs-L32 on evidence rather than judgement: score
both posteriors on Antarctic data **neither** was fitted to, using the IMBIE regional breakdowns or GRACE-only
2002–2026. **Both were checked against `python/prep_recalib_targets_ext.py`. Neither is held out.**

**(a) The regional breakdown is an EXACT partition.** West + East + Peninsula minus continental = **0.00 Gt at every
year** (2023: −4779.5 both). It is a decomposition of the same numbers, and the continental sum **is L32's training
data**. DAIS also has no regional degree of freedom. Dead twice over.

**(b) GRACE is SPLICED INTO the fitted AIS target of BOTH arms** (`SPLICE_FROM["ais"]=2019`, `EXT_Y1=2026`):

| arm | fitted AIS target | GRACE yrs in-sample | window setting the splice offset |
|---|---|---|---|
| L27 | Frederikse 1900–2018 + **GRACE 2019–2026** | 8 | `OVERLAP["ais"] = (2003, 2018)` |
| L32 | Frederikse 1900–78 + IMBIE 1979–2023 + **GRACE 2024–26** | 3 | `IMBIE_GRACE_OVERLAP = (2003, 2023)` |

And over **2002–2018 the contamination runs the OTHER WAY** — Frederikse for L27, but **IMBIE-2026 for L32, and IMBIE
reconciles gravimetry** ⇒ a GRACE score is **biased toward L32**.

⭐ **That leaves GRACE as a ONE-SIDED test**: an **L27 win would be informative** (the same "wins against the in-sample
asymmetry" argument as the benchmark, on an estimator with a different error structure); **an L32 win would not be.**
Not run. If it ever is, the asymmetry belongs at the gate.

⭐⭐ **The transferable lesson: "neither model was fitted to it" is a claim about the TARGET-BUILDING CODE, not about
the dataset's name.** A product can be held out by provenance and in-sample by splice; a "different" release can be an
exact partition of the training data. Cost to check: minutes.

**Only remaining unseen-by-both candidate:** the **IMBIE 2021 vintage LEVEL** (in repo, used so far only for L33's
floor). Marcus's ruling 09-23: *it would not add information either way.* **Not pursued.**

---

## 4. §5c — THE ROOT CAUSE WAS IN THE CODE, AND THE CODE HALF IS FIXED (09-23i)

The draft says *"IMBIE was dropped from the Antarctic likelihood"* while `prep_recalib_targets_ext.py` has defaulted to
`AIS_SOURCE = "imbie2026"` since 09-21 (`c247e06`) ⇒ **anyone rebuilding from the current repo does not reproduce L27.**

⭐ **But the prose is the symptom.** `outputs/recalib_targets_ext.csv` — the file the whole calibration is fitted to —
carried **no provenance of any kind**. And the single line that tried to record it, `src.attrs["ais_source"]`, is a
**NO-OP**: pandas `to_csv` silently drops `.attrs`. Verified rather than assumed (pandas 2.3.3 round-trips `.attrs` as
`{}`; `grep -c ais_source` on the shipped sidecar returned **0**). **A provenance stamp that had never once reached a
file** ⇒ `to_csv_drops_dataframe_attrs`, the same class as `seed_recorded_in_the_artifact`.

**Fixed:** a loud banner naming the target AND which posterior it reproduces; a real
`outputs/recalib_targets_ext_provenance.txt` sidecar carrying **the md5 of the file it describes**; the dead line
replaced by a real column. **Verified by byte-identity** (nine drivers gate on that md5): rebuild with no flags leaves
the target unchanged; the mutation test `--ais-frederikse` flips banner and stamp; **and that build is byte-identical to
the quarantined L27 target `070f74ab…`** — which is the precondition L34 rests on, re-proven two days after `c247e06`
first claimed it.

⚠⚠ **THE PROSE HALF IS NOT FIXED — IT IS MARCUS'S TEXT.** Two items in
`deliverables/LadrilloUpdateDescription_FILLED.md`:
1. the *"Deliberately removed: IMBIE"* paragraph — historically accurate about L27, misleading about the repo's present
   default. Needs a clause naming `--ais-frederikse` as the flag that reproduces the shipped posterior.
2. ⚠ **it still says "This document describes posterior L24"** while the champion is L27. Flagged, untouched; not
   raised in any previous handoff.

---

## 5. WHAT IS OPEN

### 5a. THE DECISION IS STILL A JUDGEMENT (Marcus's) — and L34 may reframe it
**Is the Antarctic module for hindcasting the reconstruction era, or for tracking the modern record?** L32 buys the
satellite era (1.01 vs 1.27, 9× coverage), the rate (−1.79 vs −2.42), the dynamics anomaly and the level z; it pays in
1920–1949 and the length-weighted full-period AIS. §5d closed the one route that could have settled it on evidence.

⭐ **But L34 changes the option set.** If L34 wins the primary, the champion can improve **without a target swap** — the
paper keeps its Frederikse basis and the IMBIE-null story intact, and only gains a better-specified noise model. That is
cheaper than promoting L32, which additionally costs §4's paragraph and the null insert's out-of-sample framing.
**Either way the 7 van Vuuren runs and 14 figures are owed.** `champions.json` **UNTOUCHED**; **L27 remains champion.**

### 5b. The null insert — Marcus ruled NOT to revise it
`deliverables/GMD_imbie2026_null_INSERT.md` line 92 argues the identity trade-off is unavoidable given the module, which
L32 showed is escapable. **Marcus, 09-23: given his answer on 5a, the insert does not need revising.** Left as is. It
still needs his `[MCS]` sentences, and its Otosaka author list is unverified — **the title, journal, DOI and data DOI
ARE in `data/observations/raw/imbie2026/README.md`**; only the author list is open.

### 5c. Standing list, unchanged
Comment #12 (code availability), venue (GMD), package extraction for Tony's team, `facts` remote, FACTS/MAGICC scope,
pulse analysis. `SRC_COLOR`'s `#ff9900` contrast 2.14:1 left as-is (markers + linestyles carry it).

### 5d. ⚠ `champions.json` still carries a STALE figure
Its L27 rationale says *"+21 at 0.99"*; on the current target it is **+9.1**. The criterion still holds; the number
needs restamping. **NOT changed — it is Marcus's file.**

---

## 6. ⚠ NON-OBVIOUS STATE AND TRAPS (09-23's §4 still applies in full)

Carried forward, still true: `outputs/bench_ladrillo_L27.md` is on the RETIRED target — use the `L27*` column inside a
new arm's bench file. `ic_hindcast_obs_sigma.csv` is a SHARED input every IC run regenerates — check every shared
input's mtime against the last DATA change before comparing two stored likelihoods. `ladrillo_model_comparison.py` needs
the UNTAPPED SSP deliverable. `diag_ais_flux_split_vs_imbie.jl` reads `ice_flux` only and omits `ISO` — immaterial for
non-ramp arms, WRONG in a ramp arm or a tipping projection; **still Marcus's call from 09-22.** A case-insensitive `Inf`
in an error scan matches "inflation". Three pre-existing `outputs/*_L24.*` modifications remain in the tree.

**New this session:**
- ⛔ **L34's logpost is comparable to NEITHER L27's** (a bound + a different σ scale) **NOR L32's** (a different target).
  Compare on hindcast statistics and the channels only.
- ⚠ **`--sd-ais-floor` requires `overdispersed_starts_L27r_sdfloor.csv`** — L27's plain starts all have `sd_ais`
  0.019–0.021, below the floor, and every chain would refuse to start. The file was built for L32 and is correct for L34
  **unchanged** (it is L27's starts with `sd_ais` at floor×1.05, spread preserved, every other column byte-identical).
- ⚠ **Disposable tags: use a distinctive prefix and delete by EXACT PATH, never a glob.** A previous session's
  `PREFLIGHT` glob deleted a tracked file. This session's throwaways were `_preflight_L34.sh` and tag `ZZFLOORCHK`,
  removed by exact path; `git status` confirmed 0 strays.
- ⚠ **`INDEX_ais_imbie.md` was split** at 17,369 B → **11,631 B live + `INDEX_ais_imbie_arch.md` (8,007 B)**. The split
  line is: **did the attempt CHANGE THE MODEL'S STRUCTURE, and is it CLOSED?** Everything in the archive (L30 ramp, free
  T_oc exponent, L29 ρ cap, D1 dynamics channel, the 09-22j iso-cumulative pricing) is **dead** — read it before
  proposing any new structural DOF for DAIS. Three straddlers named in its header.
- ⚠ Contention is normal here. L34 launched at load 2.17; by 07:25 the machine was at 8.35 with the four chains up.
  Read the meter at ~5 min; do not pause another session's job.
