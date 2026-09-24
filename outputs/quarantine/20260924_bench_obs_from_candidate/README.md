# QUARANTINE 2026-09-24 — `bench_ladrillo.py` takes the OBSERVATIONS from the CANDIDATE's own postpred

## 1. The bug

`python/bench_ladrillo.py`, block [H], line 601:

```python
obs = (a[f"{lst}_obs"] if f"{lst}_obs" in a else tg[tcol].reindex(a.index)).reindex(yrs)
```

`a` is the **CANDIDATE's** postpred file. When it carries an `<component>_obs` column — it always
does — **the observations used to score EVERY arm (candidate, champion snapshot `L27*`, and
BRICK 2.0) come from the arm under test**, and the live target file `tg` is never consulted for
that component. The arm supplies its own ruler.

`run_L34_bench.sh`'s md5 gate on `outputs/recalib_targets_ext.csv` passes truthfully and is
**blind to this**: the target file genuinely IS the IMBIE build, it simply is not what gets used.

## 2. Why it bit HERE and not before

The candidate's postpred carries whichever target was live when its posterior predictive ran.

| candidate | postpred `ais_obs` | so the whole bench file was scored on |
|---|---|---|
| L27 (`bench_ladrillo_L27.md`) | Frederikse | Frederikse |
| L28–L33 (incl. `bench_ladrillo_L32.md`) | IMBIE 2026 | IMBIE 2026 |
| **L34 (these files)** | **Frederikse** | **Frederikse** |

`run_L34.sh` runs the posterior predictive **while the Frederikse target is live, deliberately**,
so that L34's own hindcast diagnostics sit against its own training target. That is correct for
COST A. It also means L34's postpred hands the bench the Frederikse obs.

⭐ **L34 is the first Frederikse-fitted arm to be benched since the target moved to IMBIE on
09-21**, which is why nothing caught this earlier.

## 3. What is INVALID here

`run_L34_bench.sh` states in capitals that it scores L34 on the **IMBIE** target, deliberately,
to put L34 in **exactly L27's out-of-sample position**. **That did not happen.** Both L34 and the
`L27*` snapshot were scored IN-SAMPLE on Frederikse.

⛔ **The PRIMARY criterion is NOT GRADED by these files.** The pre-registration set
WIN ≤ 0.70 σ / LOSS ≥ 0.80 σ against an `L27*` column that reads **0.70**. In these files `L27*`
reads **0.56**, because it is being scored on the target it was fitted to. A 0.70 threshold
applied to a 0.56 ruler measures nothing. `readout_prereg_criteria_L34.md` printed
**"PRIMARY VERDICT: WIN"** — that verdict is an ARTEFACT and must not be quoted.

## 4. The evidence

Two arms that CANNOT have changed — the frozen `L27*` snapshot and frozen BRICK 2.0 — both moved
between `bench_ladrillo_L32.md` and these files, by the SAME additive amount:

| arm | `bench_ladrillo_L32.md` bias | here | shift |
|---|---|---|---|
| `L27*` | −0.0067 | −0.0771 | **−0.0704** |
| BRICK 2.0 | −1.0797 | −1.1500 | **−0.0703** |

A common additive offset on two frozen arms is a ruler change, not a data change. And BRICK here
reads **1.5740 cm**, reproducing `bench_ladrillo_L27.md` exactly.

## 5. ⭐ This CORRECTS a standing diagnosis in the repo

`run_L34_bench.sh`'s own header says `bench_ladrillo_L27.md`'s BRICK value 1.5740 "differs from
every later file's (1.4766) with nothing about BRICK having changed", and attributes it to the
**target rebuild at 09-21 13:12**. **That attribution is wrong.** The cause is this bug: L27's
postpred carries Frederikse obs and L28–L33's carry IMBIE obs. The header's *advice* (never read
the standalone L27 bench; read the `L27*` column inside a new arm's file) remains correct — but
only because each file is internally consistent, not for the stated reason.

## 6. ⚠ BLAST RADIUS — what is NOT affected

- **`bench_ladrillo_L32.md` and the L27-vs-L32 reading STAND.** L32's postpred carries IMBIE obs,
  so L32 *and* `L27*` were both scored on IMBIE inside that file. Internally like-for-like.
- Every bench file is **internally** consistent: all arms share whatever the candidate supplied.
- ⛔ **What is unsafe is comparing a sigma ACROSS bench files** — which is exactly what the L34
  pre-registration did by fixing its thresholds from the numbers in the L32 file.
- COST A, COST B, GUARD and the MECHANISM decomposition in this session do NOT depend on
  `bench_ladrillo.py` and are unaffected.

## 7. The canonical replacement

**None yet — the fix is a methodological decision for Marcus**, and the two routes are not
equivalent:

- **(a) Re-run L34's posterior predictive with the IMBIE target live**, into a separate tag, and
  bench that. Leaves `bench_ladrillo.py` alone, so every historical bench file keeps its meaning.
  Needs care: L34's Frederikse postpred must be KEPT, because COST A's like-for-like with L27
  depends on it.
- **(b) Fix `bench_ladrillo.py` to take obs from the TARGET file**, making the ruler independent
  of the arm. Principled, and it is what the block's own docstring implies. But it changes every
  arm's scores and would require re-scoring L28–L33 and re-reading the L27-vs-L32 comparison the
  GMD draft rests on.

⛔ **`champions.json` UNTOUCHED. L27 remains champion. Nothing was promoted.**

Files here: `bench_ladrillo_L34.md`, `bench_ladrillo_L34.csv`, `readout_prereg_criteria_L34.md`
(commit 4ccdb83, bench run 09-24 09:15:40–09:26:39, driver `run_L34_bench.sh`, ALLDONE 0 failed).
