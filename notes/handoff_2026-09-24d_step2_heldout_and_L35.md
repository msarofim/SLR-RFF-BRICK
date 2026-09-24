# Handoff — ⭐⭐ **STEP 2 IS DONE for the free-`sd_ais` cell: the arm ALREADY EXISTED (it is L31), it FAILS the held-out pre-1979 test at 1.39 σ — and a FAIL was pre-registered as AMBIGUOUS.** The read-out turned up an unplanned finding that forced the floored cell: **L35 is RUNNING**, ETA ~16:30

**Start here.** Self-contained. Follows `handoff_2026-09-24c_sigma_sensitivity_and_step2.md`, which
still stands for step 1, the memo sync, the σ-inflation null, and the target-divergence diagnostic.
Records CHANGELOG **09-24f**. Commits `b1eeec1` → `e57daa8` on `ladrillo-dev`, **ALL PUSHED — the
nine-commit backlog the last handoff flagged is cleared (22 commits pushed, `b54ed41..e57daa8`).**
`FaIRtoFrEDI` commit `3645688` also pushed (CLAUDE.md sub-index registration).
Memory: `ais_heldout_pre1979_fails_ambiguously` (new), `ais_noise_floor_is_target_dependent`
(extended + `description:` restamped in the same edit), **`INDEX_ais_decision.md` (NEW SPLIT)**,
`INDEX_ais_imbie.md`, `INDEX_ais.md`, `MEMORY.md` updated.

---

## ⛔ 0. RETRACTIONS — the 09-24c list still binds; there are NO new ones

**Still binding, do not re-quote:** ΔlnL +10.0 / +7.6 / +5.6 or −11.7 / +23.4; L27 ΔBIC +20.8;
*"L32 strictly dominates L27"*; *"every iid-like scorer prefers L27…"*; every number from the FIRST
L34 bench; and *"the break-even is NOT reachable from measured evidence."*
⭐ **They now all live in ONE place** — the header of the new `INDEX_ais_decision.md`. Read it before
quoting any L27-vs-L32 figure.

---

## 1. ⭐⭐ THE ARM STEP 2 ASKED FOR WAS ALREADY ON DISK

09-24c's next job was *"launch L35 = the IMBIE target build + `--ais-fit-from=1979`"*. Read literally
**that arm is L31** — run 2026-09-22, `run_L31.sh`: *"L31 = L28 PLUS `--ais-fit-from=1979`. CONTROL =
L28, ONE AXIS"* — with its posterior predictive on disk since. **The free-`sd_ais` cell of step 2 cost
no chain time at all.**

Pre-flight confirmed, not assumed: all four chain logs print, read back off the series rather than
re-typed (`calibrate_mcmc_ext.jl:635–639`), *"ais 1979-2025 … ⚠ AIS LEVEL TERM RESTRICTED … 79
pre-1979 years are now OUT-OF-SAMPLE, not absent"*; and `SERIES` excludes the total (`:1462`), so
pre-1979 AIS is not constrained through the total-SLR term either.

⚠ **Lesson for the next handoff: check whether a proposed arm already exists before writing its
runner.** 09-24c proposed it in good faith one session after L31 ran.

---

## 2. ⛔ THE PRIMARY IS THE **SHAPE**, NOT THE RMSE — the load-bearing choice, pre-registered

Pre-1979 the two target builds carry the **same Frederikse data** and differ by **exactly a constant
−0.134074 cm** (sd 6.2e-17). That constant is **not data**: both builds are re-referenced to their own
1995–2005 mean, and the builds differ over 1995–2005. An RMSE would charge an IMBIE-trained arm 0.134
cm for failing to reproduce **Frederikse's baseline convention** — scoring a re-referencing artefact
as prediction error, the same ruler class as 09-24b's obs-from-candidate and 09-24d's σ cliff.

⇒ **PRIMARY = the SHAPE error** (residual sd after removing the window mean). It is **identical under
both builds**, and `diag_ais_heldout_pre1979.py` **gates on that identity** (mutation-tested: a single
perturbed pre-1979 year trips it).

**BOUND from the OBSERVATION, not the code under test** (`threshold_from_obs_or_law`): Frederikse's
own published 1σ over 1900–1978 = **0.2337 cm**. ⚠ Explicitly **not** the bench's σ̄ = 0.1674, which
the post-2018 0.01 cm cliff years drag down. Both are printed; neither stands in for the other.

⭐ **The read was committed (`b1eeec1`) BEFORE any arm number existed**, so "pre-registered" is
provable rather than asserted.

---

## 3. THE RESULT

**Reproduction gate first:** `L27*` **0.7035** / L32 **0.8812** against the published 0.70 / 0.88 —
exact. **Mutation-tested four ways, all four fire:** σ from the live build instead of the frozen one
(L27 → 0.7819, caught); a wrong md5; a perturbed year breaking the constant identity; a wrong
published value.

| arm | target | `sd_ais` | AIS fit | **shape (cm)** | /σ₁₉₀₀₋₇₈ | /σ̄ | bias vs IMBIE | cov90 |
|---|---|---|---|---|---|---|---|---|
| L27 | frederikse | free | 1900– | 0.0241 | 0.10 | 0.14 | +0.035 | 100 % |
| L28 | imbie2026 | free | 1900– | 0.1501 | 0.64 | 0.90 | −0.276 | 34 % |
| **L31** | **imbie2026** | **free** | **1979–** | **0.3241** | **1.39** | **1.94** | **−0.686** | **3 %** |
| L32 | imbie2026 | floor | 1900– | 0.0501 | 0.21 | 0.30 | −0.141 | 100 % |
| L33 | imbie2026 | floor21 | 1900– | 0.0713 | 0.31 | 0.43 | −0.197 | 100 % |
| L34 | frederikse | floor | 1900– | 0.0305 | 0.13 | 0.18 | +0.034 | 100 % |

**PRIMARY: L31 = 0.3241 cm = 1.39 × the published band ⇒ FAIL.**

⚠⚠ **AND A FAIL WAS PRE-REGISTERED AS AMBIGUOUS.** One-sided in the **opposite** direction from the
GRACE test: the held-out data **IS** the product under doubt, so it cannot separate *"the model is
wrong"* from *"Frederikse is wrong."* **A pass would have been informative; this is not.** The
asymmetry was stated at the gate before the number landed, so the verdict could not be moved after it.

⭐ **POWER, measured before the verdict was read** (`no_power_null`):
- **(P1)** L31's pre-1979 90 % band half-width is **0.5143 cm = 2.20× the bound** ⇒ a coverage pass
  would have been cheap, which is why a point error carries the verdict. Coverage is in fact **3 %**.
- **(P2)** L31 vs **in-sample L28** — same target, same free `sd_ais`, **ONE axis**: **+115.9 %**, far
  outside the bench's 2 % dead band ⇒ the held-out years **do** do work; the null is not structural.

---

## 4. ⭐⭐ THE UNPLANNED FINDING, AND WHY L35 IS RUNNING

At the **same target and the same full fit span**, the noise floor cuts the pre-1979 shape error
**L28 → L32 = 0.1501 → 0.0501 cm, a factor 3.0.** On the **Frederikse** target the same floor moves it
the **other way** (L27 0.0241 → L34 0.0305). That is the **same target-dependent interaction** L34
found on the dynamics channel ([[ais_noise_floor_is_target_dependent]]: −1.4 Gt/yr on Frederikse vs
−61.9 on IMBIE) — now on a **second, independent channel**, in a window the floor was never aimed at.

⇒ ⛔ **L31's FAIL MAY NOT BE READ AS L32's.** L31 carries free `sd_ais`; the memo's arm does not.
Inferring the floored cell from its neighbour is exactly the error L34 was built to catch, and it
would be the second time in this arc.

| IMBIE target | full fit 1900– | fitted 1979+ only |
|---|---|---|
| free `sd_ais` | L28 | L31 |
| floored `sd_ais` | **L32** (the memo's arm) | **L35 ← RUNNING** |

---

## 5. ⭐ L35 — RUNNING NOW, CRITERIA PRE-REGISTERED IN THE RUNNER

`run_L35.sh` = **L32 + `--ais-fit-from=1979`. CONTROL = L32, ONE AXIS.** Launched **09-24 13:24**,
4 chains × 2,000,000, seeds 2026-2029, **driver PID 58046, chain PIDs 58067-58070**, log
`outputs/log_L35.txt`. At 13:31: 4 % done, **ETA ~2 h 15 m for the chains** (acceptance 0.236, healthy),
so chains ≈ **15:45** and postprocess done ≈ **16:30**.

**PRE-REGISTERED (in the runner's header, committed before launch):**
- **PRIMARY** held-out 1900–1978 SHAPE error, same observation-derived bound:
  **PASS ≤ 0.2337 cm** · **FAIL ≥ 0.3241 cm** (no better than free-`sd` L31) ·
  **0.2337–0.3241 is PARTIAL and must be reported as PARTIAL, not rounded to either.**
- **INTERACTION** — a *measurement*, not a pass/fail: L31→L35 against the full-span L28→L32 = −0.1000 cm.
- **GUARD** four non-Antarctic components within ~0.02 σ of L32. **COST** the in-sample 1979–2025 fit.
- ⚠ **NOT criteria:** `sd_ais` on its bound (true by construction); **`log_post`** — 79 fewer
  likelihood terms ≈ **666 units of pure bookkeeping** (L31 measured −1220.7 full vs −554.95 on 1979+),
  and L35 adds a floor on top, which moves the σ scale as well.

**Arm verification is gated per chain on BOTH flags and was mutation-tested before launch:** a
1-iteration run with each flag dropped in turn — dropping the floor kills the floor gate only,
dropping the span flag kills the span gate only, both present passes both. A dropped floor would have
produced **a second L31** and a dropped span flag **a second L32**, each wearing a new label. The
runner **refuses to postprocess** if either gate misses on any seed.

**No target swap** (L35 trains on the already-live IMBIE build), so unlike `run_L34.sh` there is **no
exit trap and no window in which another IMBIE arm's gate would fail.** **TORCH CONSIDERED AND NOT
WARRANTED** — the Julia/Mimi/MimiBRICK stack is not provisioned there; launched at load 1.49 with no
other chains running.

### 5a. WHEN IT FINISHES — the exact next three steps
1. `grep -E "ALLDONE|INCOMPLETE" outputs/log_L35.txt` and **read the ARM VERIFICATION block**: four
   seeds must each show the floor line, `ais 1979-`, and `FLOOR DERIVED FROM OBSERVATION`.
2. `python python/diag_ais_heldout_pre1979.py` — **add `"L35": ("imbie2026","floor","1979-2025")` to
   its `ARMS` dict first**; it scores every arm in one place, on one ruler.
3. Read the PRIMARY against the pre-registered **PASS / PARTIAL / FAIL** bands **as written**, and the
   INTERACTION beside the full-span −0.1000 cm.

---

## 6. FILES

**New:** `python/diag_ais_heldout_pre1979.py`, `run_L35.sh`,
`outputs/diag_ais_heldout_pre1979.csv`, this handoff. **Modified:** `CHANGELOG.md`;
`FaIRtoFrEDI/CLAUDE.md`. **In flight:** `outputs/log_L35.txt`, `outputs/mcmc/*L35*`.
**NOT touched:** `champions.json`, the standing ruler, `benchmark/reference/_fixed/`, the Tony memo,
`outputs/recalib_targets_ext.csv` (still the IMBIE build, md5 `eb768cd9`).

---

## 7. ⚠ NON-OBVIOUS STATE AND TRAPS

**New this session:**
- ⚠ **A RUNNING CHAIN'S SETUP LINES ARE NOT READABLE MID-RUN.** Julia block-buffers **stdout** when
  redirected to a file, while ProgressMeter writes to **stderr** unbuffered — so `log_L35_seed*.txt`
  contains **only the progress bar** until the process exits and flushes. The flag lines (`Extended
  fit windows`, `AIS LEVEL TERM RESTRICTED`, `sd_ais FLOOR`) appear **only at the end**. ⭐ This is
  why the runner's ARM VERIFICATION correctly sits **after `wait`** — and why a mid-run readback
  attempt looks alarmingly like a dropped flag when it is nothing of the kind. Verify mid-run from
  the **driver log's argv line** instead; it records the exact flag string passed.
- ⚠ **`seed_diag_L35_seed*.txt` does NOT carry the flags or the starting logpost** — it is the
  proposal-covariance block only. It cannot confirm an arm's identity.
- ⭐ The processes were confirmed alive **by PID** (`ps -p 58067,…`), never by `pgrep -f`
  (`pgrep_wait_loop_matches_itself`).

**Memory tree, 09-24f pass:**
- ⭐⭐ **`INDEX_ais_imbie.md` was SPLIT** at 16,957 B of its 18,432 B ceiling (the 09-24c handoff had
  flagged it and deliberately deferred). New **`INDEX_ais_decision.md`** (12,811 B) takes **WHICH ARM
  SHIPS** — the benchmark and its ruler, the frontier, the ICs, both held-out tests, the σ-sensitivity,
  the memo. `INDEX_ais_imbie.md` (10,333 B) keeps **WHAT THE ANTARCTIC SHOULD BE** — the target,
  L28–L31, the identity, how L32/L33 were built. **Both now under soft.** The split line is stated in
  BOTH headers, four straddlers are named, and an **orphan sweep proved all 12 original entries
  survive exactly once** across the two files.
- All retracted L27-vs-L32 figures were consolidated into `INDEX_ais_decision.md`'s header.
- `MEMORY.md` is **15,300 B of CONTENT** (21,509 raw — **strip the `<!-- -->` blocks first**; this is
  the seventh time the raw count would have raised a false alarm): over soft 12 KB, well under hard.
- ⚠ Closest to the hard ceiling now: `INDEX_ccx_ref.md` 18,129 B and `INDEX_diag.md` 17,291 B.

**Carried forward, still true:** never compare a σ across bench files written before 09-24; L34's
logpost is comparable to neither L27's nor L32's; `ic_hindcast_obs_sigma.csv` is a SHARED input every
IC run regenerates; `diag_ais_flux_split_vs_imbie.jl` omits `ISO` and is wrong in a ramp arm; three
`outputs/*_L24.*` modifications remain; **the committed `outputs/recalib_targets_ext.csv` is the
FREDERIKSE build while the code default is `imbie2026`** (Marcus's file, untouched — if "IMBIE is the
better product" is adopted this resolves toward the IMBIE build); **`champions.json` carries a stale
"+21 at 0.99"**, currently +9.1 (Marcus's file, untouched).

**Owed either way (unchanged):** the 7 van Vuuren runs and 14 paper figures, and the three coherence
gaps Marcus's memo cuts opened (§3's unresolved net/dynamics identity, §7's empty "and open", no
author/date). **The memo waits, as instructed.**
