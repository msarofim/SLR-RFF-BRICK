# Handoff — the pulse's Ladrillo stage is DONE and PLOTTED; stages 3-5 are the comparison

**Start here.** Written 2026-09-03, evening. Supersedes handoff `2026-09-03d`'s §6 for the
pulse's status. Two repos moved, nothing pushed to any remote — check before assuming.
`FaIRtoFrEDI` (branch `heat-ed-morbidity`) and `SLR-RFF-BRICK` (branch `ladrillo-dev`).

⭐ **Stages 1 and 2 are COMPLETE, gated and plotted. Stages 3-5 (BRICK 2.0, MAGICC, FACTS)
are the remaining work, and the second half of this note is about how to DRAW the result,
which is the part nobody has designed yet.**

---

## 1. WHAT IS DONE

| stage | state |
|---|---|
| 1 FaIR paired cubes | ✅ 56 cubes, 7 markers × 2 species, all gates pass |
| 2 Ladrillo arm | ✅ `julia/scope_slr_pulse_vv.jl` (`cc5bada`); 14 runs, **every gate passes** |
| 2b figures | ✅ `python/plot_pulse_response_vv.py` (`dd114e1`), 3 PNGs in `figures/` |
| 3 BRICK 2.0 | ❌ not begun |
| 4 MAGICC (+ Ladrillo-on-MAGICC-climate) | ❌ not begun |
| 5 FACTS | ❌ not begun |

**Spec (Marcus, settled):** 10 GtCO₂ **or** 1 GtCH₄, pulse year **2030**, seven van Vuuren
markers, **joint** driver, **TAPPED Greenland**, compared against BRICK 2.0 / MAGICC / FACTS.

⭐⭐ **THE TAP RULING, 09-03 — this is new and it binds stages 3-5.** Marcus: *"If we think
tapped is the best model structure, then we should be using that all the time. If the other
models don't have it, that would be a flaw on their parts."* So the reported Ladrillo arm is
TAPPED, and the cross-model figure must NOT quietly drop the tap to make the columns match.
Say in the caption that the comparators have no counterpart cell.

### Headline numbers (all `--tap`, L24, 2000 draws × 841 configs, cm rel 1995-2014)

- **CO₂ is scenario-invariant at 2100: 7.53-7.65e-03 cm/GtCO₂, a 1.6 % spread over all seven
  markers.** By 2300 it runs 0.0142-0.0210 cm/GtCO₂ = 44 %. Inherited, not coincidence: FaIR's
  own dGMST@2100 spans 1.14× and SLR-per-mK is a flat 0.02 everywhere.
- **CH₄ is U-SHAPED across markers, 2.70×, and the U is FaIR's not Ladrillo's** — dGMST@2100
  is itself U-shaped 0.00773 (vvL) to 0.01110 K (vvVL), the concentration-dependent forcing
  law. A component decomposition REFUTED the ice-module explanations first: all four
  components rise together vvL→vvVL (+17 to +25 %) = a uniform scaling = the climate input.
- **Ladrillo's own contribution is ONE amplification at vvH**: SLR-per-mK 0.05 (five coolest)
  → 0.06 (vvHL/vvM) → **0.11 (vvH)**, carried by AIS = 0.690 of vvH's 1.098 cm.
- **On a GWP100 CO₂e basis CH₄ delivers MORE sea level than CO₂**: 4.07× at 2050, 2.78× at
  2100, 1.82× at 2300. ⚠ Partly a statement about the METRIC — a 100-yr radiative-forcing
  integral is not matched to a response that integrates warming.

---

## 2. ⚠ FOUR THINGS THAT WILL BITE STAGE 3-5

1. **THE MARKER NAME ORDER IS NOT THE FORCING ORDER.** By baseline dT@2100:
   VL 1.640 < LN 1.721 < L 1.817 < ML 2.348 < HL 2.858 < M 2.885 < H 3.317 — **L/LN swap and
   HL/M swap.** At 2300 it reorders AGAIN (vvM 4.287 K but vvHL only 1.376 K, a declining
   pathway). Sort by the trajectory before reading or plotting any cross-marker pattern.
2. **THE PAIRING IS THE WHOLE EXPERIMENT.** The response is ~0.07 cm against arms individually
   60-400 cm. Stage 2 runs both arms in ONE process off one `ASSIGN` vector so the pairing is
   an identity, not a seed reproduced twice. **Do the same in stages 3-5**, and keep
   `[DRAW-PAIRING]`, which records what each arm actually ran rather than trusting `ASSIGN`.
3. **THE IDENTITY GATE'S HORIZON IS NOT THE PULSE YEAR.** Ladrillo's Greenland shape law reads
   a CENTRED 30-yr running mean, so a 2031 change moves sea level from **2026**. Derived bound
   = pulse − window/2 − 1 = 2014. BRICK 2.0 has no such smoother, so its bound SHOULD hold to
   2029 — if it does not, that is a real defect, not this mechanism. Memory:
   `pulse_reachback_is_the_shape_window`.
4. **THE TAP FIRES WHERE THE ENSEMBLE STRADDLES THE ONSET, NOT WHERE IT IS HOTTEST.** New
   crossings: vvM 6 draws / 2 configs, vvHL 2/1, **vvH ZERO** — 85.4 % of vvH configs already
   cross 4.69 K at baseline. Same shape as `amp_leverage_falls_at_high_forcing`.

---

## 3. STAGE 3 — BRICK 2.0. The cheapest, and start here.

`julia/scope_slr_fairunc_oldbrick.jl` is only **219 lines** and already shares Ladrillo's
splice pivot, 1995-2014 re-reference, `PAIR_SEED = 2026` and draw→config permutation. It reads
`fair_cube_{gmst,ohc}_$(SSP)_raw.csv` — **and the pulse cubes are named so that
`--ssp=vvM_pulsebase_CO2_10Gt_2030` resolves directly.** That naming was deliberate.

Write `scope_slr_pulse_vv_brick2.jl` as the analogue of `scope_slr_pulse_vv.jl`: both arms in
one process, same gate set minus `[TAP-CROSSING]` (no counterpart) and with `[NO-REACHBACK]`
extended to **all** components.
⚠ `get_model` is built ONCE PER SSP because LWS is seeded before it (`brick20_joint_band`), and
line 122 hardcodes `ssprcp_scenario="ssp245"` for the reason `BUILD_SSP` documents. **Pin the
draw count to the shipped thinning** or the control compares different subsets.
⚠ This arm is **corroboration, not independence** — it shares Ladrillo's lineage.

## 4. STAGE 4 — MAGICC, plus the Ladrillo-on-MAGICC's-climate arm

Native MAGICC pulse machinery already exists in **FaIRtoFrEDI**:
`magicc_comparison/build_pulse_scenarios.py`, `build_pulse_comparison.py`,
`build_pulse_comparison_ch4.py`. The second arm's machinery also exists —
`python/scope_ladrillo_on_magicc_climate.py` and the `_magiccclim` paths, driven through
`scope_slr_fair_uncertainty.jl --climate=magicc`.
⚠ **MAGICC's glacier module is NOT independent of Ladrillo's** (shared Nauels-2017 law;
equilibria differ 0.06-0.86). State that caveat on glaciers; it is fine for AIS/GIS/TE.
⚠ **MAGICC is 0.38-0.93 K COLDER at 2300 on the declining markers** — so a Ladrillo-vs-MAGICC
gap is a TWO-variable comparison until the climate is held. That is exactly what the
Ladrillo-on-MAGICC's-climate arm is for; run it before attributing anything to a module.
⚠ ZJ → 1e22 J is **×0.1 because ZJ is a DEFINITION**, never from a ratio.
⚠ `pymagicc` leaks a full run-tree copy PER WORKER — check inodes with `find | wc -l`, not `du`.

## 5. STAGE 5 — FACTS. The only genuinely independent ice-sheet method.

Proven cheap (~1 min/experiment; the 7-marker 2300 extension took ~7 min).
⚠ **Confirm the CH₄ pulse clears FACTS's float32 climate precision.** 10 GtCO₂ was chosen
partly because smaller pulses sit under it; the CH₄ pulse is far larger in GMST terms
(53 mK peak vs 4.4 mK) so it very likely clears — **measure it, don't assume the Julia-side
precision carries over**. ⛔ EnTK forbids `_` in an experiment key.

---

## 6. ⭐ THE OPEN DESIGN QUESTION: WHAT THE COMPARISON FIGURE SHOULD BE

This is the part that is genuinely undecided, and it is worth deciding BEFORE running stages
3-5, because the answer changes what each stage has to emit.

**What stage 2's figures established that should carry over** (`python/plot_pulse_response_vv.py`):
- focal marker with a full band; other markers dotted medians on a recessive one-hue ordinal
  ramp **with direct labels** — when the context lines share a hue, the label IS the identity
  channel, so label collision is a correctness bug, and the ramp's lightest step is a contrast
  requirement (3.12:1 floor used).
- **log y for anything carrying a band** (the band spans its own 14× CO₂ / 6× CH₄ skew at a
  horizon); **linear when only medians are drawn** and they share an order of magnitude.
- every figure carries model + calibration + posterior vintage + arm + basis + commit.

**The four candidate forms for the cross-model figure, with the objection to each:**

1. **Four lines (one per model) + one band, per species per marker.** Simple, but 7 markers ×
   2 species = 14 panels, and the models nearly coincide at 2100 (stage 2 says CO₂ varies 1.6 %
   ACROSS MARKERS — the model spread may well be larger than the scenario spread, which is
   itself the finding). Risk: 14 near-identical charts.
2. **A "spread of models" band against the "spread of draws" band** — the honest question is
   which uncertainty dominates. This is probably the RIGHT headline: one panel per species,
   x = year, two nested bands, medians as lines. ⚠ needs the two bands to be visually
   distinguishable without color alone.
3. **Dot-and-whisker by model at three horizons** (2100/2150/2300), faceted by species, one
   marker. Reads exactly like the FACTS matched-pair table already in `INDEX_cmp`
   (`facts_matched_pair_penalty`), so it would be consistent with existing deliverable
   graphics. Loses the time profile — which for CH₄ is the whole story (two regimes).
4. **Per-tonne ratio to Ladrillo**, one line per comparator, centred on 1.0. Compact and shows
   agreement/disagreement directly, but a ratio hides the BASE (`ratio_needs_its_base`) and
   near-zero denominators early in the run would blow up.

**My recommendation, for Marcus to accept or overrule:** form **2** as the headline (it answers
"is the model choice or the parameter uncertainty bigger?"), form **3** as the table-like
companion at horizons, and drop 1 and 4. But this is a methodological choice about aggregation
and it is Marcus's to make — **do not pick it silently.**

**Also undecided:** whether the cross-model figure is per-marker (7×) or pools markers; and
whether to show CO₂ and CH₄ on one CO₂e axis (stage 2's figure 3 shows they are the same order
of magnitude, so it is feasible) or keep them separate.

---

## 7. HOUSEKEEPING

- **Outputs**: `outputs/pulse_ladrillo_{cells,draws,paths,gates}_vv<M>_<SPECIE>_..._L24_tap4p69K_V5p64m_tau800.csv`.
  `draws` carries per-draw base/pulse/diff at the three horizons; `paths` carries the median
  and p05/p95 path — the figures read `paths`.
- **The 56 pulse cubes are UNTRACKED by decision** (Marcus 09-03) though the scenario cubes
  beside them are tracked: ~200 MB, rebuild in ~1 min each. `.gitignore` names the reason.
- **Frozen driver copies must live under `julia/`**, not `/tmp` — the drivers include
  `ladrillo_projection.jl` by `@__DIR__`. The first sweep launch failed all 14 jobs in five
  seconds on exactly this. `julia/_frozen_*.jl` is gitignored.
- **Torch verdict**: stayed local and should have. 14 runs, 4 concurrent, BLAS pinned to 1
  thread each, **15.6 min wall**. Stages 3-5 are the same order; re-check only if FACTS or
  MAGICC changes the arithmetic.
- **Memory**: `pulse_ladrillo_arm_built`, `pulse_reachback_is_the_shape_window`, indexed in
  `INDEX_cmp.md`. ⚠ `INDEX_cmp.md` is at **17.2 KB against an 18 KB hard ceiling** — it needs a
  split (`INDEX_cmp_pulse.md` is the natural cut) before stage 3's findings land.
- **The L24 docx is CANONICAL**, not `FILLED.md`. Run `python3 deliverables/sync_filled_from_docx.py
  --verify` before any text edit.
