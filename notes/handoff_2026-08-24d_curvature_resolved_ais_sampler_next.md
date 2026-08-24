# Handoff — the curvature deficit was never a model defect, and item 4 is next

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, through the commits below.
Written 2026-08-24, to be picked up cold. **Continues**
`handoff_2026-08-24c_lambda_prior_priced.md`. Everything in that handoff's §1–§4 stands;
its §6 priority list is superseded by §5 here.

---

## 0. THE ONE-PARAGRAPH VERSION

Three things closed since the last handoff. **The AIS fast-dynamics prior was priced and
then re-scoped**: its functional form is worth ≤6% of the band, the *choice* of λ inside the
paleo support is worth 2.18× it, MICI needs λ 1.06–2.20× above the paleo maximum so it is
outside the representable set, and λ's entire observational constraint is the **LIG alone** —
the other three Ruckert windows fire 0.0% of draws. **Option 3 shipped** as a process
headline plus a flagged `UNRESOLVED_AMPLIFICATION` arm (λ×1.351 from the LIG residual, the
duration cancels) weighted by a FACTS-derived **P_UNRES = 0.245**, after the obvious
probability definition failed a placebo test at 0.185 in 2020. And **the curvature deficit
that motivated a whole diagnostic arc turned out not to be ours**: the target set calibrates
components on **Frederikse 2020** and scores the total on **Dangendorf 2024**, whose
acceleration is **1.83× Frederikse's** — a model matching the Frederikse budget would read
0.546 against Dangendorf and we measured 0.571, agreeing to 5%.

---

## 1. THE CURVATURE ARC, AND HOW IT ENDED

It ran GIS 0.65× → AIS 0.727× → "shared ice-sheet signature" → a 2×2 → the resolution.
**Nothing in it was a model defect.** Read `curvature_deficit_is_recon_gap` first; the three
memories behind it are caveated, not deleted, because the *route* matters.

**The 2×2** (`julia/diag_curvature_deficit_2x2.jl`) exploited the fact that the components do
**not** share a hindcast driver — `ladrillo_setup` splices OBSERVED regional T into Greenland
and the glacier blocks, while AIS and steric run on FaIR-mean GMST/OHC, and all four are
fitted likelihood streams:

| component | driver | accel ratio | |
|---|---|---|---|
| `gis` | OBSERVED | 0.629 | deficit |
| `ais` | FaIR | 0.727 | deficit |
| `gsic_hind` | OBSERVED | **3.086** | excess |
| `te` | FaIR | **3.624** | excess |
| `total` | mixed | 0.571 | deficit |

Perfectly crossed ⇒ driver, likelihood-form **and** ice-response-memory all refuted. (The
third was my own hypothesis, added when the first two looked weak; it died with them.)

**The resolution.** With `lws` in, the observed budget closes to **2% in rate** and fails
**3.13× in curvature** — so not a missing component. But over **1993–2018** (no splice in the
window) the component sum closes against **Frederikse's own total to 1.3%** (0.007189 vs
0.007285). The budget is fine. **Dangendorf's acceleration is 1.83× Frederikse's**, and that
single number predicts the measured deficit to 5%.

⚠ **Still unquantified:** the component sum's curvature **halves** past the splice (0.007189
over 1993–2018 → 0.003533 over 1993–2024), and `prep_recalib_targets_ext.py` holds **LWS
constant from 2019** by construction. Real post-2018 slowdown vs splice artifact: NOT
established.

### What this retires, explicitly
* The 0.571× total deficit, the gis 0.65× and the ais 0.727× are **not** model defects.
* **Marcus's natural-variability driver proposal is not motivated by this** — but the
  driver-side finding stands on its own and is worth acting on eventually: our GMST driver's
  1993–2024 curvature is **−3.27e-4 vs observed +2.45e-4, the WRONG SIGN**. Confirmed for
  AIS; **not** for steric, whose OHC driver is already at 0.92× and whose two observational
  products disagree **3.7×** with each other. There is no curvature score to improve until
  the target set stops mixing reconstructions.

---

## 2. THE AIS PRIOR — WHAT IS SETTLED

* **The band is a prior, measured**: posterior-vs-prior KS **0.0141** (λ) / **0.0120**
  (Tcrit) against a 0.0304 critical value. "Likelihood-inert" is now evidence.
* **Provenance**: `param_priors.csv`'s λ row reproduces the DAISfastdyn 800k paleo marginal
  to **0.018 prior sd** — but as an independent **Gaussian truncated at paleo pctile 99.10**.
  ⚠ κ / α / `anto_alpha` do **not** match (0.33–0.64 sd) ⇒ the file is a **subsample**.
* **Form ≤6%; choice 2.18× the band**, one-sided upward (105 / 479 / 655 cm at paleo-min /
  box-top / paleo-max).
* **Transfer law**, from a 15-point measured ladder:
  **AIS₂₃₀₀(ssp585, median) = 70.67 + 19752·λ cm**, max resid 0.13% of range. Any λ band maps
  with **no chain re-read**.
* **λ rests on the LIG alone** — LGM / mid-Holocene / instrumental fire **0.0%** at both ends
  of generous ranges; 0.00% of draws cross in 1850–2024.
* **MICI is outside the representable set**: needs λ **1.06–2.20× above the paleo maximum**.
* **Hindcast**: rates 0.98–1.08×. (The 0.727× acceleration is retired — see §1.)

---

## 3. THE SHIPPED ARM

`python/build_ais_unresolved_amplification.py`. Named for its **role**, not a mechanism —
MICI trends down (Edwards 2019 / DeConto 2021 / Morlighem 2024) while fracture damage trends
up (Blasco et al. 2026), so a mechanism-named arm would have looked refuted while its family
was reinforced.

* **Scale**: λ → λ/(1−0.26) = **1.351 × λ** from Ruckert's own LIG shortfall. **The
  above-threshold duration CANCELS**, which matters because it is only known to ~100–1200 yr.
  Arm λ = 0.014280, paleo pctile 86.3, inside the support ⇒ reads the measured ladder.
* **Weight**: **P_UNRES = 0.245**. ⚠ the obvious definition `P(SEJ > process p95)` **failed a
  placebo test** — 0.185 at 2020, before any mechanism can have operated — and gave 0.52.
  Shipped `P(SEJ > process MAX)`, floor 0.075, post-engagement 0.300–0.335, floor-corrected
  **0.245 ± 0.02**. The p95 route floor-corrects to 0.310 independently.
* **Deliverable**: **dE[AIS]/dP = 10.9 / 27.2 / 73.3 cm** at 2100 / 2150 / 2300. Anyone who
  rejects 0.245 substitutes their own with no re-run.
* ⚠ Small vs DeConto's 687–1355 cm **by construction** — the price of not double-counting.
* ⚠ **Blasco et al. 2026 does NOT justify enlarging it.** Its 4.5× / 50–130% sit on a **54 mm
  ASE-only** base; the absolute increment is **~18 cm = 25% of our arm**, and the ratio
  applied to our base gives an absurd 1230 cm. Direction-only evidence. See
  [[ratio_needs_its_base]] — I relayed that ratio without its base and it flipped my advice.

---

## 4. NON-OBVIOUS STATE

* **`--maxrows=N` smoke mode reads from iteration 1 (pre-burn-in)**. Its `[INDEP]`
  correlation is meaningless (0.618 vs the real 0.047). Plumbing only, never a result.
* **The λ ladder is the reusable asset.** 15 points over the full paleo support, both
  scenarios, three horizons. Any future λ band is post-processing.
* ⚠ **ssp245 @2100 and @2150 are λ-INERT** — the median moves 5.58 → 5.59 cm across the
  *entire* paleo support while the spread moves ×0.198–×2.623. A λ sensitivity read off a
  median there reports zero and is not zero. The large % residuals in the Test-3 linearity
  table are this, not nonlinearity: the denominator is 0.028 cm.
* **Chain reads are ~12 min but were much faster when the OS page cache was warm.** Judge
  progress by `%CPU`, not the log — Julia block-buffers to a file.
* **`pgrep -f "<script name>"` self-matches the polling shell** and deadlocks an `until`
  loop. Match the interpreter (`pgrep -f "julia.*<script>"`) or poll the PID.
* Every trap in `handoff_2026-08-24c` §4 and `2026-08-24b` §3 still applies.

---

## 5. OPEN, IN PRIORITY ORDER

1. **ITEM 4 — `ais_runoff_Ton` (R̂ 1.092, rank 4 at ssp245) and `antarctic_alpha`
   (R̂ 1.777, rank 5).** The two parameters that both fail to mix **and** reach the
   deliverable. This is the agreed next item (Marcus, 6 → 4 → 5). `ais_iceflow0` is the
   block's worst at R̂ 2.244 but is a reporting caveat — quote it **with its scenario**, since
   its R² is 12× larger at ssp585 than at ssp245.
2. **ITEM 5 — re-price at 2100 / 2150.** The ranking already differs at 2100 and §4's
   λ-inert finding says the horizon caveat is real and compounds with the scenario one.
3. **The target set's reconstruction mixing.** Score like against like — Frederikse's own
   total for the Frederikse-era budget, or move the components onto Dangendorf. Until then
   no curvature score means anything. Also settle the post-splice halving in §1.
4. **The AIS observed driver** (Marcus's proposal, deprioritised by §1 but still real). The
   gridded sources are global so `build_t_gis.py`'s zone machinery needs only a latitude
   change, and the anchor-preserving 11-yr splice already exists. ⚠ for AIS *mass loss* the
   physically relevant driver is the **ocean** forcing (ANTO / Southern Ocean subsurface),
   not surface air; and AIS is only **10% of the total rate**, so it cannot move the total
   much regardless.
5. **FrEDI linearity**, when dSC/dP is actually wanted. Marcus: testable with existing
   modules, may not hold for future work ⇒ **do not publish dSC/dP as a durable
   coefficient**.
6. **Marcus's prose** for module-memo §1 and §9, and the `2.0` tag decision.

---

## 6. FILES

**New this arc:** `julia/scope_ais_lambda_prior.jl`, `julia/scope_ais_three_tests.jl`,
`julia/diag_curvature_deficit_2x2.jl`, `python/diag_ais_mwp1a_lambda.py`,
`python/build_ais_unresolved_amplification.py`, `data/dais_paleo/`, and their outputs.
**Memories:** `ais_lambda_prior_envelope`, `dais_paleo_is_four_levels`,
`ais_lambda_rests_on_lig`, `ais_curvature_deficit_shared` (caveated),
`mwp1a_corroborates_lambda_width`, `unresolved_amplification_arm`, `blasco2026_damage`,
`ratio_needs_its_base`, `weight_recent_literature`, `curvature_budget_no_closure`,
`curvature_deficit_is_recon_gap`.
