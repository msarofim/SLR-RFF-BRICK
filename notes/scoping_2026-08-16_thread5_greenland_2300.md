# Scoping handoff — Thread 5: Greenland at 2300 (Option C, and why it needs D)

**Start-here document for the next session.** Repo `SLR-RFF-BRICK`, branch
`brick-mengel-vnext`, **pushed and in sync** as of 2026-08-16 (`b816a9f`).

This is a *scoping* session, not a run. Nothing below is blocked on compute; it
is blocked on four decisions in §6.

---

## 0. THE ONE THING TO GET RIGHT BEFORE STARTING

The 2026-08-16 handoff said thread 5 "needs an external `Leq(T)` target, i.e.
re-opening Option C". **Both halves of that are misleading and would waste the
session:**

1. **The external `Leq(T)` target already exists in this repo.**
   `python/build_greenland_equilibrium_ladder.py` builds the Bochow et al. 2023
   equilibrium ladder into a tracked CSV, and `python/fit_gis_veq_pism.py` has
   already fitted four candidate forms to it →
   `outputs/gis_veq_pism_{curve,fit}.csv`, `figures/gis_veq_pism_fit.png`.
   Nothing needs to be sourced.
2. **Option C did not fail for lack of a curve.** It failed because it was
   paired with **proportional relaxation**. Re-running C alone will reproduce
   the same failure.

**The unit of work is C+D together**, not C.

---

## 1. SETTLED — do not re-derive any of this

From `notes/note_2026-08-14_thread5_commitment_not_relaxation.md`
(`python/scope_gis_2300_relaxation.py`, which carries a 0.05 cm reproduction gate
against the shipped projections and refuses to print a diagnosis if it fails):

- **It is a COMMITMENT defect, not a relaxation one.** A+B is **99% equilibrated
  by 2300** (φ = 0.987 / 0.991 / 0.989 across the three SSPs). Under SSP1-2.6 it
  has *stopped*: 0.002 cm/yr at 2300 with 2 mm of commitment left. The spec's
  framing — "what replaces proportional relaxation at high warming" — is wrong.
- **A+B's relaxation is FASTER than the stock SIMPLE it replaced.** The
  realisation term runs the *wrong* way (+0.41 to +0.84 m) and is more than
  cancelled by a commitment term of −0.54 to −0.97 m. Confirmed independently by
  a 2×2 cross-test that does not rely on the linearisation.
- **Committed loss is 19-24× below the ice-sheet models** at each scenario's own
  2300 GMST: A+B 0.137 / 0.205 / 0.454 m against Yelmo/PISM/SICOPOLIS 3.1-3.4 /
  4.8-5.1 / 8.6-8.7 m. A+B commits **6% of the ice sheet at ~6.5 K**.
- **THE RIDGE, and this is the load-bearing fact.** The 1900-2025 hindcast
  constrains only the **product** φ·Leq. Scale `(c1, c0)` by `k`, re-solve the
  rate scale that restores the 5.78 cm hindcast target, and 2300 moves:

  | k | Leq(2300) m | rate scale | τ_slow @2300 | hindcast | **2300 cm** |
  |---|---|---|---|---|---|
  | 1.0 (as calibrated) | 0.204 | 1.0034 | 30 yr | 5.78 | **14.59** |
  | 5.0 | 1.020 | 0.1117 | 272 yr | 5.78 | 46.30 |
  | 22.6 (Bochow-matched) | 4.610 | 0.0231 | 1316 yr | 5.78 | **58.29** |

  **Every row fits the hindcast exactly as well**, and 2300 saturates near ~60
  cm. So `gis_c1`'s posterior/prior sd ratio of 0.12 is a *conditional* width at
  the timescales the module can express — **not** evidence the commitment is
  identified.

- **Secondary defect, carry it but don't let it drive:** the channels are
  labelled backwards. Both `alpha` and `beta` are larger on the "slow (dynamic)"
  channel, so slow relaxes *faster* everywhere above T_south = −1.41 K (76.6% of
  draws at 2 K). **Nothing in the module exceeds ~80 yr**, so there is no slow
  reservoir at all, and the Mouginot partition pins the *surface* share onto
  whichever channel the sampler made slower.

---

## 2. WHY OPTION C FAILED THE FIRST TIME — the precise mechanism

From CHANGELOG "Tried and rejected", pass 1:

- Both ladder cells **break the hindcast**: RMSE **1.675 / 1.009** against A+B's
  **0.099**, and both fail gate G3.
- A+B+C projects **72 cm** of Greenland at 2100 under SSP5-8.5, far outside
  AR6's ~9-18 cm. That is a *specification failure*, not a finding.
- Cell scores: A+B+C **563.20**, A+B'+C **118.15**, against A+B **19.15**.

> **The cause is structural: a proportional relaxation cannot serve both a 6 cm
> historical loss against a 71 cm commitment AND a 742 cm post-threshold
> commitment. Past the threshold, loss is limited by ice THROUGHPUT, not by the
> size of the disequilibrium.**

That last sentence is the whole design brief. It is scoping §10's **Option D**,
and it is why C needs D first.

**And the scoping doc independently says C is worth it at 2300** (§19, and note
it *corrects* an expectation the author had going in):

- At 2300 the equilibrium curve matters **on its own, even at the current slow
  transient** — SSP5-8.5 goes 50 → 167-193 cm from the shape of `V_eq` alone.
  280 yr at τ ≈ 800 yr is about a third of an e-folding. **C is NOT contingent on
  B at the 2300 horizon.**
- The two ice-sheet models differ from each other **far less** than either
  differs from the linear form (1.15× apart at SSP5-8.5, against 3.3-3.8× for
  linear-vs-either). **Getting off the linear form is first-order; the
  PISM-vs-Yelmo choice is second-order — do not let that disagreement delay the
  change.**
- **The exception is low warming, and it is the one that matters for policy.** At
  SSP1-2.6 the arm is decisive: **28 cm (PISM-like) vs 86 cm (Yelmo-like)**, a
  factor of three, because SSP1-2.6 peaks at +1.84 °C right on the 1.7 °C
  threshold. A step curve crosses it; a graded curve does not.

---

## 3. WHAT ALREADY EXISTS — do not rebuild

| asset | what it gives you |
|---|---|
| `python/build_greenland_equilibrium_ladder.py` | Bochow 2023 ladder → tracked CSV; 90-100 kyr equilibrium window, no-overshoot runs only |
| `python/fit_gis_veq_pism.py` → `outputs/gis_veq_pism_curve.csv` | four candidate `V_eq(T)` forms already fitted: **pchip, linear, saturating, logistic2**, on a 0-8 K grid |
| `python/scope_greenland_bochow2026.py` → `outputs/scope_greenland_bochow2026.csv` | per-family (Yelmo/PISM/SICOPOLIS) per-SSP projections at 2100/2150/2300 |
| `python/scope_gis_2300_relaxation.py` | the ridge diagnostic **with a reproduction gate** |
| `python/gis_offline_cell.py` | the offline cell harness — where cells are scored before any Julia work |
| `notes/scoping_2026-08-10_greenland_options.md` | 53 KB, options A-D, the ladder verdicts, §19's corrections |

**The offline cell is the right place to do this.** Every structural decision so
far was made there and only then ported; `julia/greenland_ab_component.jl` claims
to bit-match it.

---

## 4. ALSO TRIED AND REJECTED — do not retry

- **The saturating glacier-reservoir form** `V₀ − a(1 − e^(−b(T−T_off)))`,
  proposed in scoping §10 as *the* Option-C candidate. It cannot express the low
  tail and the collapse at once, and puts `T_off` at 2.11 with **zero** loss
  below it.
- **The Bochow-2026 cubic emulator** fitted from transcribed coefficients —
  retracted 2026-08-10, the coefficients give no fold. The ladders are raw model
  output, so fit `V_eq` to them directly; the emulator is off the critical path.
- **Absolute-weighted least squares on the ladder.**
- `gis_offline_cell.py` **reported non-optima once** (under-converged starts,
  quarantined at `outputs/quarantine/20260812_gis_offline_cell_underconverged/`).
  If a cell score looks surprising, check convergence before believing it.

---

## 5. THE DESIGN BRIEF

A form that simultaneously expresses:

1. **a small historical loss** — 5.78 cm over 1900-2025, hindcast RMSE at A+B's
   ~0.06-0.10 level, not 1.0-1.7;
2. **a threshold / fold** near ~1.7 K, since that is what makes SSP1-2.6
   decisive;
3. **near-total loss at high sustained warming** — the ladders reach 8.6-8.7 m;
4. **a rate that is THROUGHPUT-limited past the threshold**, not proportional to
   the disequilibrium. This is the new piece and the reason pass 1 failed.

Note (4) is what breaks the φ·Leq ridge. Under proportional relaxation the
hindcast can only ever see the product; a throughput cap makes the historical
rate depend on something *other* than the size of the commitment, which is what
would let the hindcast constrain them separately.

---

## 6. DECISIONS NEEDED FROM MARCUS BEFORE ANY CODE

1. **Is Bochow 2026 admissible as a CALIBRATION TARGET, or only as an EVALUATION
   BENCHMARK?** It is an EGUsphere preprint and the recorded status is
   "provisional — referee concerns on UQ, verification and functional form all
   still binding". Calibrating to it embeds a preprint in the deliverable;
   benchmarking against it does not. **This is the decision everything else
   hangs off.** (The Bochow *2023* ladder used by
   `build_greenland_equilibrium_ladder.py` is a different, published object —
   worth confirming which is which before starting.)
2. **One ladder family, or carry the arm through to the reported results?**
   Scoping §19 recommends carrying it, because PISM-like vs Yelmo-like is a
   factor of three at SSP1-2.6 — exactly the question a reader cares about
   (does Ladrillo think SSP1-2.6 commits Greenland?). Averaging the arms hides
   it. Carrying it doubles the reported projection set.
3. **New posterior vintage, or a separate study arm?** A Greenland structural
   change means a full re-tune + 4×2M + re-acceptance (~5 h unattended) and a
   new vintage, weeks after L11 was accepted. Alternative: develop and report it
   offline/as a sensitivity arm, and fold it into the next vintage.
4. **Is a centuries-to-millennial τ acceptable downstream?** Any Bochow-matched
   commitment forces τ into the hundreds-to-1300 yr range. The CH4-vs-CO2 SLR
   pulse work reads this module; check whether a millennial Greenland τ changes
   those metrics before committing to it.

---

## 7. PRE-REGISTER THESE, before looking at any result

- **Hindcast**: RMSE stays at A+B's ~0.06-0.10, and G1/G2/G3 pass. Pass 1 failed
  here (1.675 / 1.009) — this is the first gate, not an afterthought.
- **2100 sanity**: SSP5-8.5 GIS stays inside AR6's ~9-18 cm. Pass 1 gave 72 cm.
- **G4 scenario spread**: A+B is currently **10.44 cm, ABOVE** the 6.3-7.3
  evaluation band. Pushing it down is the desirable direction. State before
  running whether C+D is expected to raise or lower it.
- **Does 2300 SSP5-8.5 move materially**, and does the **+1.5 °C commitment land
  inside the published range**? (Scoping §10's own pre-registration for C. If
  2300 does not move, the change is not worth its complexity.)
- **The 2×2 cross-test** from the thread-5 note, as a gate: feeding the new
  commitment through the old relaxation and vice versa should behave
  predictably, and the diagonal must reproduce the arms.

---

## 8. NON-OBVIOUS STATE

- **The amp(GMST) law is PROJECTION-SIDE ONLY.** The calibrator runs 1850-2026
  at a constant `GIS_AMP = 1.92`. Do not assume the law is live in a calibration
  diagnostic.
- **`gis_g` is fixed at 0.0 and `gis_v0` at 7.42 m SLE**, both by argued
  decision (`greenland_ab_component.jl` header: `gis_g` unidentified and
  confounded with `gis_c0`, LR test accepts g=0). Any C+D form has to say what
  it does with `v0`.
- **The L11 posterior carries `gis_slow_ell` / `gis_slow_w` only** — no native
  `(alpha_s, beta_s)`. Anything reading it must go through `ladrillo_posterior`
  or call `ladrillo_native_greenland!`.
- **The posterior medians are NOT the offline A+B optimum** the spec quotes
  (`alpha_s = 0.00708, beta_s = 1e-6`). The optimum rails `beta_s`; the median
  does not. Reasoning from the offline optimum's channel timescales does not
  carry to the shipped posterior.
- Julia `--project=julia_v2`; pin `OPENBLAS_NUM_THREADS=1` for parallel chains.
- Naming: **Ladrillo**. Never `sed s/brickf/ladrillo/g` — `brickf` ⊂ `brickfm`.
- **Branch rename is still outstanding**, carried from handoff 13d.

---

## 9. UNRELATED LOOSE END, so it is not lost

The D2 attribution (2026-08-16) left one thing undiagnosed: **the two D2 streams
are sub-additive.** Steric-only moves `thermal_alpha` +1.48 L10 sd; both streams
together move it +1.31; the arms sum to 137% of the joint move. Adding the gsic
term pulls the steric shift back and nobody knows why. Not on the Greenland
critical path — see `notes/handoff_2026-08-16_l11_figures_and_thermal_alpha.md`
§4 and `project_ladrillo_l11_thermal_alpha_moved_away` in memory.

Also queued there: the one-line `d2_basis` change (weighted metric on the steric
stream only). **Deliberately deferred** — the effect is +1.7 cm on a 95 cm 2100
ssp585 total, which does not justify churning a posterior vintage on its own.
**Fold it into whatever vintage this Greenland work produces**, if it produces
one.
