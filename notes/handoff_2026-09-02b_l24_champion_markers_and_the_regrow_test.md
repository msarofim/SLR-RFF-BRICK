# Handoff — L24 is champion, the SSPs are marker-free, and the GIC_REGROW test is next

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, **all pushed**. Written 2026-09-02.
Supersedes `handoff_2026-09-01c_readers_gates_and_the_amp_error_bar.md`.

⭐ **FIRST THING NEXT SESSION: run the GIC_REGROW experiment (§4).** Everything else here is
finished and recorded; that is the one open experiment, it is cheap, and it converts the project's
most interesting current claim from an observation into an attribution.

---

## 1. STATE

**L24 is champion** (promoted 2026-09-02, all six modules). It is L23's configuration with the
Antarctic amplification prior at its **shipped width N(1.09, 0.180)** — the measured 34-model CMIP6
spread — and it is the only vintage on that prior. On fit it is indistinguishable from L23 (85/65/6
vs 86/64/6; **3 of 304 cells** change verdict for a 1.8x wider prior), so it was promoted on
**provenance, not skill**.

⚠ `benchmark/champions.json` carries four fields per module — `why`, `correction_2026-09-01`,
`resolution_2026-09-01b`, `prior_promotion_2026-09-01`. **Read them before quoting any promotion
reasoning.** L23's promotion rested on a claim that was retracted the same day; that history is
deliberately preserved because the retraction is the reason the registry has a correction field.

⚠ **L24 vs L21 is NOT like-for-like** — their amp priors differ (N(1.09, 0.180) vs N(0.95, 0.10)).
The difference between those vintages is a **prior change, not a model improvement.**

**Deliverable shipped:** `deliverables/LadrilloUpdateDescription_L24.docx`, 9 figures, built from
`LadrilloUpdateDescription_FILLED.md` via `build_l24_deliverable_doc.sh` (which gates on the figure
count — it caught a rebuild that shipped 1 figure instead of 6 with every step exiting 0).

## 2. ⭐ THE MARKER POLICY (Marcus 2026-09-02) — BINDING

**The SSPs PREDATE the CMIP7 marker scenarios**, so there is no *correct* marker for an SSP.
Borrowing CMIP7 marker land use and irrigation for a CMIP6 SSP imports a different scenario
generation's assumptions. That is a category error, not a tolerance question.

| arm | treatment | why |
|---|---|---|
| **van Vuuren markers** | **marker-based** | they ARE the CMIP7 markers — native forcing, ambiguity identically zero. REQUIRED. |
| **SSPs** | **marker-free** | land use `calculated` from the SSP's OWN cumulative CO2 AFOLU; irrigation one shared trajectory |

⚠ **Keep the two sets separate in any figure or table.** A combined band mixes a native treatment
with an anachronistic one.

⚠ **Marker-free uses the stock posterior OFF-DESIGN** — the constrained parameters are
byte-identical, so 1.6.0 was never constrained under `calculated` land use. Measured cost over the
constraining period: **2-6 % of the ensemble's own p5-p95 spread**, smaller than the marker
ambiguity it removes. State the deviation wherever an absolute number from this set is used.

**Built today:** SSP5-3.4-OS on the 1.6.0 stack (emissions, cube, mean, Ladrillo arm), emissions for
ssp119/370/460, and the marker-free set (means for 7 SSPs; cubes + L24 arms for the 4 like-for-like
ones). Both builders are now parameterized — neither the scenario list nor the calibration directory
is a hardcoded literal.

## 3. THE RESULT THAT MOTIVATES §4

SLEIP Phase 1 (egusphere-2026-3874, the formal 7-emulator intercomparison — Wong, Nauels, Mengel,
Nicholls, Smith, Kopp, Slangen) reports an **overshoot sea-level penalty of 0.1-0.3 m by 2300** under
SSP5-3.4-OS vs SSP1-2.6, persisting after GSAT re-converges by 2150.

**Ladrillo gives 3-5 cm at 2150, decaying to ~0 by 2300:**

| | 2150 | 2300 |
|---|---|---|
| Ladrillo, marker | +4.0 cm | +1.1 cm |
| Ladrillo, marker-free | +3.2 cm | −1.0 cm |
| **SLEIP, 7 emulators** | — | **+10 to +30 cm** |

**Ladrillo RECOVERS from an overshoot where their ensemble largely does not.**

Ruled out as explanations: it is **not** the marker (going marker-free *deepens* the temperature gap
and makes the penalty slightly negative), and it is **not** a cumulative-budget artifact
(ssp534over emits **+10 GtCO2 MORE** than ssp126 to 2300 and still ends cooler — a path effect,
via a deep late net-negative excursion, −982 vs −515 GtCO2 over 2100-2300).

⚠ **Standing caveat:** our SSP5-3.4-OS ends 0.06-0.13 K COOLER than our SSP1-2.6, which biases our
penalty LOW. It cannot account for 10-30 cm, but a fully clean comparison needs SLEIP's own scenario
pair on a matched dT — ours is a different realisation of SSP5-3.4-OS, not theirs.

⇒ **Hypothesis:** Ladrillo has materially less sea-level hysteresis than the SLEIP ensemble, and the
**floored-equilibrium glacier law** is the leading candidate. Of the four models we compare, only
MAGICC could express glacier regrowth before the 2026-08-31 change; Ladrillo's glacier rate at 2300
now falls to **0.00-0.55 mm/yr on declining pathways against 1.96 rising**.

## 4. ⭐ THE NEXT EXPERIMENT — GIC_REGROW: turn the observation into an attribution

**Question.** How much of Ladrillo's near-zero overshoot penalty is the floored-equilibrium glacier
law, and how much is the rest of the model?

**Design.** One arm pair on the SHIPPED L24 posterior — **no refit**. Re-run the overshoot pair with
the OLD glacier law and difference the penalties, by component.

    NEW law (shipped):  FLOOR on,  R = 1
    OLD law:            FLOOR OFF, R = Inf        <- both, or it is not the old law

⚠⚠ **`R = Inf` ALONE IS NOT THE OLD LAW.** The old melt-only ratchet is *exactly* `R = Inf` **AND**
`FLOOR = 0`: the old `exc = max(T − T_eq, 0)` zeroes the cooling step precisely as `mult /= Inf`
does, and the old `S_eq` was unfloored. Setting only one gives a half-old law that resembles
neither. (This was already got wrong once, on the likelihood-tilt work.)

**Mechanism — reuse, but FIX FIRST.**
`outputs/scope_amp_likelihood_tilt_INSTRUMENTATION.patch` already adds the ENV switches
`AMPPROF_FLOOR` and `AMPPROF_R`. ⚠⚠ **It instruments the WRONG MODULE for a projection experiment.**
`brick_mengel.jl` includes **both** glacier modules — `glaciers_nu_component.jl` (line 24) then
`glaciers_nu3_component.jl` (line 25) — and **nu3 is the SHIPPED one**. The floor exists
**separately in each** (`nu:91`, `nu3:90`) and the patch only changes `nu`'s. `GIC_REGROW_R` is
defined once in `nu` and picked up by `nu3` only because Julia resolves the global at call time.

⇒ **Instrument `glaciers_nu3_component.jl:90` as well**, or the projections run with the floor still
ON. This is the "the law lives in FOUR places and they must move together" warning firing again.

**Steps.**
1. Copy the repo to a FROZEN worktree (never edit a module while a run reads it). Apply the patch,
   then add the nu3 floor switch.
2. **Verify the switch bites before trusting anything:** on a monotonically warming path the two
   laws are BIT-IDENTICAL (0.000e+00) — so a warming scenario is the NULL CONTROL and must show no
   difference, while a declining one must. If ssp585 moves, the instrumentation is wrong.
3. Run four arms on L24, tapped: `ssp534over` and `ssp126`, each under OLD and NEW.
   `julia --project=julia_v2 julia/scope_slr_fair_uncertainty.jl --tag=L24 --ssp=<S> --tap`
   (~4 min each; use the marker-free cubes, per §2).
4. Report the penalty **by component** under each law. The glacier row is the attribution.

**What each outcome means.**
* Penalty rises to ~10-30 cm under the OLD law ⇒ **the glacier law explains the gap to SLEIP**, and
  we can say the ensemble's penalty partly reflects models that cannot regrow.
* Penalty barely moves ⇒ the law is not the explanation and the difference is elsewhere —
  ⚠ look at Antarctica, which carries 73-79 % of our spread.
* ⚠ Consider it against `glacier_floor_bounded_regrowth`'s own pricing: the law is worth **−0.15 cm**
  at vvLN/2300. If the penalty moves by *far* more than that, something else moved too — check the
  arm before believing it.

## 5. GOTCHAS

* **Chains ~2.2 GB each; a refit is ~3 h for 4 x 2M.** Check `uptime` first; pin BLAS threads.
* **Every L24 arm is TAPPED.** L21/L23 have no untapped van Vuuren or MAGICC arms. An untapped set
  is silently non-comparable — this bit me on 2026-09-02.
* **A flag that is absent does not error**; it selects a default, and the default is not the
  predecessor's value. **Four dropped-flag incidents in three days.** Every vintage now has a pinned
  `run_mcmc_<TAG>.sh` with an arm-verification block.
* **L23 and L24 have the SAME original command line and different priors** — `AMP_SIGMA`'s default
  moved between their run times.
* `notes/handoff_2026-09-02_fable_review_brief.md` is a **fresh-eyes brief** listing the six places
  I most distrust this work. Read it before deciding what to do after §4.
