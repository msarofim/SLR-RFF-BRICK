# Handoff — stage 3 is DONE, and the pulse size was cut 10x/100x after a floor test

**Start here.** Written 2026-09-04. Supersedes `2026-09-03f` for the PULSE SIZE and for stage 3's
status; `2026-09-03e` remains the reference for stage 4-5 mechanics and the tap ruling.
Two repos moved. **Nothing pushed** — `SLR-RFF-BRICK` (`ladrillo-dev`) and `FaIRtoFrEDI`
(`heat-ed-morbidity`).

⭐ **Three things happened: stage 3 (BRICK 2.0) was built and run; Marcus ruled on the two open
items from `09-03f`; and a pulse-floor test — asked for before any more large runs — found the
mechanism in the notes was WRONG and both spec pulse sizes TOO BIG. Marcus ruled the spec down to
1 GtCO₂ / 0.01 GtCH₄, which puts stages 1-3 into a re-run that was IN PROGRESS when this was
written.**

---

## 1. ⚠⚠ WHERE THINGS WERE LEFT MID-FLIGHT — READ BEFORE RUNNING ANYTHING

The FaIR cube rebuild at the new sizes was **launched and not yet verified**:

```
bash <scratch>/build_cubes.sh     # 14 builds: 7 markers x {CO2 --pulse-size=1, CH4 --pulse-size=0.01}
```

writing `data/observations/fair_cube_{gmst,ohc}_vv<M>_{pulsebase,pulse}_{CO2_1Gt,CH4_0p01Gt}_2030_raw.csv`
and `FaIRtoFrEDI/logs/cube_vv*_{CO2_1Gt,CH4_0p01Gt}.log`. **First check all 56 files exist and every
log's `--gates` block passes** (`[ZERO-PULSE]`, sign-flip, `[DOUBLING]`, `[MAGNITUDE]`), then:

1. **Stage 2 re-run** — `julia/scope_slr_pulse_vv.jl --marker=<M> --specie=<S> --tap --pulse-size=<1|0.01>`,
   14 runs, 4-concurrent, BLAS pinned, ~16 min. ⚠ Run from a FROZEN COPY under `julia/`.
2. **Stage 3 re-run** — `julia/scope_slr_pulse_vv_brick2.jl --marker=<M> --specie=<S> --ndraw=2000
   --pulse-size=<1|0.01>`, ~4 min for all 14.
3. The old 10Gt/1Gt outputs are **still at their canonical paths**. They are not wrong — they are a
   different, documented pulse size — so per `~/.claude/CLAUDE.md` they should be **moved to
   `outputs/quarantine/20260904_pulse_size_10Gt/` with a README** rather than deleted or left to be
   picked up silently. **NOT DONE YET.**

⚠ **`--pulse-size` was added to BOTH Julia drivers this session and has NOT been exercised end to
end.** Its label construction mirrors the Python side character for character
(`f"{g:g}".replace(".","p") + "Gt"` → `1Gt`, `0p01Gt`); a one-character difference opens the wrong
cube or none. **Smoke each driver with `--maxrows` before the sweep.**

---

## 2. STAGE 3 IS DONE — and the two models agree on the MEAN, not the MEDIAN

`julia/scope_slr_pulse_vv_brick2.jl` (`f6bd2d1`). MimiBRICK **v2.0.0** on the same paired cubes,
both arms in ONE process off ONE model build. 14 cells, **zero gate failures**, **~4 min**.

**Ratio BRICK 2.0 / Ladrillo on the paired TOTAL, 28 cells:** **mean 0.71-1.22 (median 1.09)**;
**median 0.62-1.87**. ⇒ a THIRD, cross-model argument for the Lemoine-Traeger pair.
**Both corrected stage-2 headlines REPLICATE**: CO₂ @2100 median spread **1.6 %** (identical to
Ladrillo's) but **1.43×** on the mean; CH₄ @2100 median **3.9×**, mean **1.37×**.

⚠ CORROBORATION, NOT INDEPENDENCE (shared DAIS lineage). ⚠ No Greenland tap → `[TAP-CROSSING]`
reports **NO COUNTERPART**, never a zero.

**BRICK 2.0's `p_fired` exceeded Ladrillo's in ALL 28 cells**, so it got a test:
`julia/diag_gcrit_brick2_vs_ladrillo.jl` puts both firing conditions on ONE axis, the critical GMST.
**LOCATION** median **2.313 vs 2.657 °C** (BRICK fires 0.344 K colder); **SPREAD** sd **0.364 vs
0.607** (Ladrillo 1.67× wider — it SAMPLES the DAIS slope, BRICK holds it at 1.1955). The
posteriors, not a defect. ⇒ never quote a `p_fired` ratio without this split.

New gates: `[AIS-MAP-EXACT]`, `[LWS-EXACT-ZERO]`, `[CUBE-PREPULSE]`. Three mutation modes
(`lag`/`rebuild`/`shuffle`), each naming its discriminating gate.

---

## 3. ⭐⭐ THE PULSE FLOOR — the recorded mechanism was WRONG

`analyze_magicc_ch4_sweep.py` attributed the floor to MAGICC writing **float32**. It does not:
pymagicc's `_V2BinFormat` (`io/binout.py:144`, `version = 2` = `out_binary_format: 2`) reads every
chunk with `read_chunk("d")` = **DOUBLE**, and the Fortran record-marker check would raise on a
mismatch. **The output is not the floor.**

**The INPUT is.** openscm-runner writes the SCEN file through pymagicc, whose data-block formatter
is `"{:19.5e}"` (`pymagicc/io/base.py:669`) = **6 significant figures, ASCII**. MAGICC integrates
`round6(base+delta) − round6(base)`. At a 2030 FFI of 10-11 GtC the quantum is **1e-4 GtC =
3.664e-4 GtCO₂**, so 0.01 GtCO₂ is **27.3 quanta** and one quantum is **3.66 %** — **predicting the
recorded −1.037 sign-flip to the digit.** ⚠ The quantum is a property of the BASELINE's BINADE and
jumps 10× across our markers (9.65 GtC at vvL/vvVL → 1e-5; 10.2-11.2 at the rest → 1e-4).
⇒ `build_pulse_scenarios_vv.py --snap` lands every rung on a whole number of quanta and writes the
**EFFECTIVE** pulse to a manifest. **Divide by that, never by the round number.**

⭐ **`[ZERO-CONTROL]` = 0.000e+00** over 100×556 member-years, both markers, both gases ⇒ **MAGICC
is bit-deterministic**; there is no stochastic floor at all.

⭐⭐ **THE CLEAN WINDOW IS TWO-SIDED AND BOTH SPEC SIZES WERE ABOVE ITS CEILING** (vvHL, 100 members):

| species | old spec | members >1 % off @2300 | median per-unit | **new spec** |
|---|---|---|---|---|
| CO₂ | 10 GtCO₂ | 30/100, **6 sign-flips** @2100 | **0.834** | **1 GtCO₂** (0/100) |
| CH₄ | 1 GtCH₄ | 75/100 | **0.855** | **0.01 GtCH₄** (0/100) |

**The two ends are DIFFERENT FAULTS.** LARGE end: a SUBSET breaks discontinuously — six members'
SLR@2100 response flips sign (+2.0e-2 → −3.6e-2 cm/GtCO₂) while the per-member ratio's MEDIAN is
**1.0008**, so most members stay linear and the minority drags the ensemble statistic. SMALL end: a
2300 representation floor (1e-4 GtCH₄ → 42/100 off). ⭐ Both unify as **dGMST@2100 ≈ 3e-5 to
4e-4 °C**. ⚠ **The CEILING is MARKER-DEPENDENT** — vvL at 10 GtCO₂ has 2-3 members off and ZERO
sign flips against vvHL's six.

⚠⚠ **OPEN AND IMPORTANT: the MEAN's clean window is NOT yet established.** At n=100 the MAGICC mean
is dominated by a handful of tail members — its per-unit ratio wanders 0.73-1.00 with no plateau,
and the median's plateau (0.01-1 GtCO₂) is wider than the mean's apparent one (0.01-0.3). **The
mean is the reported statistic**, so re-run both ladders at the production **600 members** before
locking any per-tonne MAGICC number. This does NOT threaten the size ruling — 1 GtCO₂ and
0.01 GtCH₄ are inside both windows — but it does mean the mean's error bar is uncharacterised.

---

## 4. MARCUS'S RULINGS THIS SESSION

1. **The cross-model FIGURE FORM is DEFERRED until stages 4-5 are in.** Do not build it now, and do
   not treat `09-03e` §6's form-2 recommendation as live — MAGICC and FACTS may have no threshold to
   decompose, leaving a pair-shaped figure with empty cells for two of four columns.
2. **The AIS sub-component's 5-8.5 % relative se is ACCEPTED** — no stratification, no extra draws.
   **Say it in the caption.** The largest un-priced uncertainty is the BINARY FLUX FORM
   (`ais_binary_form_priced`, 26-750× the scenario separation), not this.
3. **The pulse spec moves to 1 GtCO₂ / 0.01 GtCH₄**, everything re-run so all four models share one
   size (like-for-like).

---

## 5. FILES

**`SLR-RFF-BRICK` (`ladrillo-dev`), commit `f6bd2d1` + uncommitted header/flag edits:**
`julia/scope_slr_pulse_vv_brick2.jl` (NEW), `julia/diag_gcrit_brick2_vs_ladrillo.jl` (NEW),
`outputs/pulse_brick2_{cells,paths,gates}_*` (tracked; `draws` gitignored, 38 MB).
⚠ **UNCOMMITTED**: `--pulse-size` added to `scope_slr_pulse_vv.jl` AND `..._brick2.jl`, plus their
revised spec headers. **Commit these before running the sweep**, so the outputs have a commit.

**`FaIRtoFrEDI` (`heat-ed-morbidity`), commit `2d98135`:**
`magicc_comparison/probe_pulse_input_floor.py` (free, no model run),
`build_pulse_scenarios_vv.py` (`--snap`, `[SNAP-EXACT]`/`[EFF-WITHIN-HALF-QUANTUM]`/`[SIZE-SPAN]`),
`analyze_pulse_floor_vv.py`, corrected docstrings in `analyze_magicc_ch4_sweep.py` and
`build_pulse_scenarios.py`, manifests + `pulse_floor_vvHL_co2.csv`.

**MAGICC repo (`~/Documents/2026/CodeProjects/MAGICC/slr-refresh`), UNTRACKED — check its own git:**
`notebooks/302d_run-magicc-pulse-vv.py` (NEW) and `data/processed/emissions/slr_vv*_{co2,ch4}ladder2030.csv`.

---

## 6. TRAPS

1. ⚠ **302d needs `multiprocessing.set_start_method("fork")`.** openscm-runner opens a `Manager()`
   unconditionally; macOS's default spawn re-imports the flat script and it dies with a bare
   `EOFError`. 302b never hit it because it was only ever driven from a Jupyter kernel.
2. ⚠ **Two of my own gates were wrong before they were right.** `[SNAP-EXACT]` compared float64
   values agreeing to 1e-16 and failed all 13 rungs — fixed by stating the identity in INTEGER
   QUANTA. `[EFF-WITHIN-HALF-QUANTUM]` used the BASE's quantum, too tight when a pulse crosses a
   binade UPWARD onto a coarser grid — fixed to the governing (coarser) quantum. Both are the
   `gate_bound_matches_its_claim` shape.
3. ⚠ **The `rebuild` mutation initially RESEEDED**, so every rebuild produced the same LWS and every
   gate passed. A mutation that changes no output is not a test.
4. **Torch verdict: local, correctly.** BRICK 2.0 sweep ~4 min; each MAGICC ladder ~4 min at n=100.
   Queue wait would exceed the run. Stage 4 production (21 scenarios × 600) is ~30 min.
5. **The L24 docx is CANONICAL**, not `FILLED.md`. Not touched this session.
6. **Pre-existing dirt, not mine:** `deliverables/LadrilloUpdateDescription_L24.docx` (modified),
   two untracked `.docx` at the SLR repo root, `outputs/diag_ais_crossing_pulse_vv_draws_L24.csv`,
   and FaIRtoFrEDI's `deliverables/vanvuuren_H_erf_2000_2250.csv` +
   `magicc_comparison/processed/vv_wide_20260831/`.

---

## 7. NEXT

1. **Finish the re-run** (§1), quarantine the 10Gt outputs, commit.
2. **Re-run the MAGICC floor ladders at 600 members** to pin the MEAN's clean window (§3).
3. **Stage 4 proper** — `build_pulse_scenarios_vv.py --set=headline` for 7 markers × 2 gases, then
   302d at 600 members (~30 min), then the Ladrillo-on-MAGICC's-climate arm. `09-03e` §4 has the
   caveats: MAGICC's glacier module is NOT independent of Ladrillo's, MAGICC is 0.38-0.93 K colder
   at 2300 on declining markers, ZJ → 1e22 J is ×0.1 by DEFINITION, and pymagicc leaks a run-tree
   copy per worker (check inodes with `find | wc -l`, not `du`).
4. **Stage 5 (FACTS)** — `09-03e` §5. Confirm the CH₄ pulse clears FACTS's float32 climate
   precision; at 0.01 GtCH₄ that margin is now **100× smaller** than when the check was specified.
   ⛔ EnTK forbids `_` in an experiment key.
5. **Every comparator arm must emit the Lemoine-Traeger pair.**
