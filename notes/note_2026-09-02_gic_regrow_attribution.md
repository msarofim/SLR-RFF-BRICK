# GIC_REGROW — the glacier law is NOT why Ladrillo recovers from an overshoot

**2026-09-02.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`. Executes §4 of
`handoff_2026-09-02b_l24_champion_markers_and_the_regrow_test.md`.
Script `python/diag_gic_regrow_penalty.py`; run it with no arguments to reproduce every number here.

## THE ANSWER

**The floored-equilibrium glacier law accounts for essentially none of Ladrillo's near-zero
overshoot penalty.** Swapping it back to the pre-2026-08-31 melt-only ratchet, on the SHIPPED L24
posterior with no refit, moves the penalty by **at most 6.2e-05 cm** at any component or horizon,
against a block-bootstrap bar of **±0.008 to ±0.068 cm**. The move is three to four orders of
magnitude below its own error bar.

This is the handoff's **second** outcome branch: the law is not the explanation, and the gap to
SLEIP's 10-30 cm at 2300 is elsewhere.

## THE PENALTY, BY COMPONENT

Paired median of `ssp534over_nomarker - ssp126_nomarker`, `joint` arm, marker-free per the
2026-09-02 marker policy, cm. `±` is a moving-block bootstrap (block 25, 4000 resamples).

| horizon | glaciers | gis | ais | te | lws | **total** | OLD - NEW (total) |
|---|---|---|---|---|---|---|---|
| 2100 | +0.876 | +0.797 | +0.454 | +1.659 | 0 | **+3.970 ±0.045** | -1.9e-07 ±0.064 |
| 2150 | +0.569 | +0.345 | +0.433 | +0.577 | 0 | **+2.168 ±0.046** | -1.1e-07 ±0.065 |
| 2300 | -0.064 | -0.365 | **+0.003** | -1.089 | 0 | **-1.227 ±0.048** | +7.4e-07 ±0.068 |

⭐ **The row that matters is `ais` at 2300: +0.003 ±0.007 cm.** Antarctica contributes a penalty
of +0.433 cm at 2150 and **nothing at all** by 2300. Whatever gives the SLEIP ensemble a persistent
0.1-0.3 m, our Antarctica does not have it — and Antarctica is where 73-79 % of our spread lives.

⚠ The 2300 total is **negative** and that is the standing dT caveat, not a physical result: our
SSP5-3.4-OS ends 0.06-0.13 K COOLER than our SSP1-2.6, which drags `te` to -1.089 and `gis` to
-0.365. A clean penalty needs SLEIP's own scenario pair on a matched dT.

## ⚠ TWO STATISTICS FOR "THE PENALTY", AND THEY DIFFER BY ~1 cm

The handoff's headline numbers are **differences of medians**; the table above is the **median of
paired differences**. Both were computed here and both are printed:

| | 2100 | 2150 | 2300 |
|---|---|---|---|
| difference of medians (the handoff's) | +4.712 | +3.169 | -1.035 |
| median of paired differences | +3.970 | +2.168 | -1.227 |
| gap | +0.741 | +1.001 | +0.193 |

Neither is wrong. Diff-of-medians is the like-for-like comparator against an ensemble that reports
per-scenario medians (SLEIP); the paired median answers "what does the overshoot cost a GIVEN
world". The gap is real skew in the joint distribution, not noise. **Quote which one you mean.**
The OLD-vs-NEW move is ~0 under either.

## HOW THE NULL WAS GIVEN POWER

A null is worthless until the test is shown able to find something (`no_power_null`). Three gates,
in increasing strength:

* **[GATE-A]** instrumentation at shipped defaults reproduces the shipped L24 arms:
  max |Δmedian| = **0.000e+00 cm** on both scenarios. ⚠ **This gate is VACUOUS on its own** — it
  passes identically whether the switch works or is ignored. It is a no-op check, not evidence.
* **[direct probe]** `_nu_step` on a synthetic block, NEW vs OLD, at T = -0.5 / 0.0 / +1.0 K:
  7.676 / 7.756 / 7.978 vs 8.000 / 8.000 / 8.000. The switch is live.
* **[branch counters]** in a real projection of `ssp534over_nomarker`: **222,764 of 5,454,000**
  nu3 steps (4.1 %) are cooling steps, `S_eq < 0` on **219,602** (4.0 %), min d = **-2.33 K**,
  min S_eq = **-0.46**. The regrowth branch is entered, and often. `nu calls = 0` confirms **nu3 is
  the shipped module and `glaciers_nu_component.jl` is dead code on this path.**
* **[GATE-B] null control.** `ssp585_nomarker`, monotonically warming: max |Δmedian| over all 36
  cells = **2.085e-05 cm**. The residual originates BEFORE 1990 (the paths file starts there and is
  already non-zero), i.e. in historical volcanic cooling steps common to every scenario.
* **⭐ [GATE-C] positive control with an INDEPENDENTLY KNOWN answer.** `vvLN`, marker-based (it IS a
  CMIP7 marker), glaciers@2300 NEW - OLD = **-0.2027 cm**. `glacier_floor_bounded_regrowth` priced
  this at **-0.20 cm pre-computed** (diff **-0.0027**). **The instrumentation moves a projection by
  0.20 cm — 9,721x the SSP move.** The null is a measurement, not a dead switch.

### The two published prices for vvLN differ, and this arm picks one

That memory records "**DELIVERED -0.15** against a **PRE-COMPUTED -0.20** after flooring". This
experiment lands on **-0.2027**, i.e. on the pre-computed value, 0.053 cm from the delivered one.
That is what a held-posterior law swap *should* recover: the pre-computed number is law-only,
whereas the delivered -0.15 was read across shipped arms whose **posteriors also differ**, so it
carries a refit's worth of movement as well as the law's. Stated as a hypothesis — the test is to
recompute the delivered figure as a held-posterior swap on its own vintage.

## ⚠ AN ALGEBRAIC CORRECTION TO THE HANDOFF'S ⚠⚠

The handoff warns that `R = Inf` ALONE is not the old law and that the floor must also be turned
off. **Numerically, `R = Inf` alone IS the old law.** `S_eq < 0` requires `T < T_off`; and
`T_eq = T_off - log(frac_left)/b >= T_off` always, because `frac_left <= 1` so `-log(frac_left) >= 0`.
Hence `S_eq < 0` implies `d = T - T_eq < 0`, which is exactly the branch that divides `mult` by
`Inf`. **Under `R = Inf` the floor is unreachable.** The branch counters confirm it empirically:
`S_eq < 0` fired 219,602 times and `d < 0 AND S_eq < 0` fired 219,602 times — the same number, so
every negative-`S_eq` step was also a cooling step, with no exceptions.

The half-law that genuinely differs is the OTHER one: `FLOOR = 0` with `R = 1`, which would let
glaciers regrow PAST pre-industrial. Both switches were still set, so the arm matches the old code
literally and not merely in value.

Also: the existing `outputs/scope_amp_likelihood_tilt_INSTRUMENTATION.patch` **does** already carry
a `glaciers_nu3_component.jl` hunk (it has two diff sections). The handoff's claim that it
instruments only `nu` is wrong. Both modules were instrumented here regardless; the exact diff is
`outputs/gic_regrow_INSTRUMENTATION.patch`.

## WHY THE NULL WAS PREDICTABLE, AND WHY IT WAS STILL WORTH RUNNING

`glacier_floor_bounded_regrowth` already said the law is worth -0.15/-0.14 cm at vvLN/vvML and
"**~0 elsewhere**", with `S_eq` going negative on 12.9 % of cells at vvLN and **<1.2 % elsewhere**.
The SSPs are "elsewhere". Nobody had connected that pricing to the overshoot question. The
experiment converts an implication into a measurement with an error bar, and it is what rules the
law out rather than merely making it unlikely.

## WHAT THIS LEAVES

The hypothesis in the handoff — that Ladrillo has less sea-level hysteresis than SLEIP and the
glacier law is the leading candidate — is **half confirmed and half refuted**. The hysteresis gap
is real. The glacier law is not its cause.

⭐ **Next candidate, from the decomposition rather than from a prior guess: Antarctica contributes
+0.433 cm of penalty at 2150 and +0.003 cm at 2300.** Our DAIS relaxes back; SLEIP's ensemble
largely does not. `INDEX_ais` already records that **MICI is not representable** in our DAIS
parameterisation, which is a mechanism that by construction cannot be undone once triggered.
⚠ Hypothesis, not a finding. The test is a component-wise hysteresis diagnostic on the AIS module,
not another law swap.

## PROVENANCE

FaIR 2.2.4 (calib 1.6.0) + CMIP7 -> Ladrillo L24 (shipped posterior, **no refit**), 4 chains x 2M,
500 draws/chain, `joint` arm (841-config FaIR climate), `spliced` forcing, tapped
(`tap4p69K_V5p64m_tau800`), marker-free SSP drivers, cm, end year 2300. Run from a FROZEN worktree;
tags `L24GICNEW` / `L24GICOLD` read L24 chains via `--chain-tag`. Six arms, ~3.6 min each, local.
⚠ Marker-free uses the stock posterior OFF-DESIGN (2-6 % of the ensemble p5-p95 over the
constraining period) — state that with any absolute number from this set.
