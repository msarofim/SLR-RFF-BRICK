# Memo — How large an ensemble for a trustworthy SLR Hawkins-Sutton plot?

**Date:** 2026-05-28
**For:** Marcus C. Sarofim
**Question (Marcus, 2026-05-28):** the production Group-Sobol SLR surrogate
ceilings at OOF R²≈0.71 (2150). How big would a new Torch ensemble need to be to
do a better job — with ANOVA, Shapley, or Sobol?

---

## Method

Learning curve: fit the production HistGB surrogate on nested random subsets of
the current 10,000-cell LHS-10k_s ensemble (N_train ∈ {500, 1000, 2000, 4000,
7000}), fixed 2,000-cell held-out test, 3 seeds. Wong-weighted OOF R². Fit a
saturating curve R²(N) = R∞ − C·N^(−p) and extrapolate the N needed for target
R². Script: `python/scripts/substack/hs_scoping_learning_curve.py`;
data: `outputs/substack/hs_scoping_learning_curve.csv`.

## Results — R²_oof vs training-set size

| N_train | total SLR 2100 | total SLR 2150 | pulse SLR 2150 |
|--------:|:--:|:--:|:--:|
| 500   | 0.629 | 0.584 | 0.565 |
| 1,000 | 0.672 | 0.626 | 0.622 |
| 2,000 | 0.699 | 0.655 | 0.657 |
| 4,000 | 0.734 | 0.691 | 0.705 |
| 7,000 | 0.751 | 0.708 | 0.748 |
| **fitted R∞** | **0.90** | **0.87** | **1.00** |

R² rises ≈ **+0.03 per doubling of N**, with **no plateau** in range → the
ceiling is **data-limited, not (within this range) irreducible**. But the climb
is slow (logarithmic), so brute force is expensive.

## Extrapolated ensemble size for a target R² (ORDER-OF-MAGNITUDE ONLY)

Extrapolating a 5-point fit 30–1000× beyond the data is highly uncertain; treat
these as decade-scale guidance, not point estimates.

| target R² | total SLR 2100 | total SLR 2150 | pulse SLR 2150 |
|:--|:--:|:--:|:--:|
| 0.80 | ~40k (4×) | ~340k (34×) | ~27k (2.7×) |
| 0.85 | ~800k (80×) | ~1.5e8 (∞) | ~120k (12×) |
| 0.90 | impractical | ∞ | ~940k (94×) |

- **Total SLR 2150 is the hard target:** even R²=0.80 needs ~30× the current
  ensemble; R²≥0.85 is effectively unreachable by ensemble size, and the fitted
  asymptote (R∞≈0.87) says ~13% of 2150 variance is irreducibly high-order
  (multiplicative climate×ice interactions + genuine structure).
- **Pulse SLR asymptotes to R∞=1.0** (matched-seed removes internal noise; the
  marginal is a smoother, more deterministic function) — so pulse is the better
  surrogate target, but still needs ~12× for R²=0.85.

## Critical reframe: surrogate R² ≠ trustworthiness of the H-S wedges

The R²≈0.71 ceiling limits **pointwise** prediction. The **first-order Sobol
group indices are expectations** (conditional means over the input
distribution), which can be accurate even when pointwise R² is mediocre — they
only need the surrogate to capture each group's *main-effect* structure, not
every cell. Evidence it is robust here: the **normalized** emissions share was
stable (~0.33 of explained at 2150) across weighted/unweighted fits, monotonic
on/off, and 600- vs 1500-tree capacity (`_sobol_surrogate_diag.py`). So the
shipped normalized figure (emissions 27% of total at 2150, vs TreeSHAP's 8.6%)
is defensible *now*; a bigger ensemble would mainly **shrink the dropped
model-unresolved wedge and tighten the interaction estimate**, not overturn the
main-effect ranking.

## Method comparison (ANOVA vs Shapley vs Sobol)

- **Shapley and Sobol both ride the same surrogate** → identical R² ceiling and
  identical learning curve. Choosing one over the other does **not** change the
  data requirement. (Sobol is still preferred over Shapley because it handles
  collinear within-group features correctly — the whole reason we switched.)
- **Model-free factorial ANOVA needs no surrogate.** Main-effect (H-S wedge)
  estimates converge at ~1/√(levels-per-factor), which is **faster than driving
  a surrogate to R²=0.9**. The catch is design: you need a **balanced factorial**
  (each factor at many levels, with replication / crossing) — the existing
  ANOVA-18k (15 cfg × 400 RFF) is too sparse on cfg to trust V_cfg, which is
  exactly why we moved off it.

## Recommendation

1. **The current normalized Group-Sobol figure is publishable** as the headline,
   with the R² caveat already in the caption. Don't block the poster/Substack on
   a bigger ensemble.
2. **If we invest in Torch compute, build a balanced factorial, not a bigger
   LHS.** A balanced design (e.g. ~40 cfg × 40 RFF × ~16 post crossed, with the
   seed axis for internal variability ≈ **~25k–40k FaIR+BRICK runs**, i.e. ~3–4×
   the current cube) gives model-free ANOVA main effects + clean 2-way
   interactions, AND a 4× LHS surrogate (R²≈0.80 at 2100). This is the
   highest-value spend: it both validates the Sobol shares model-free and shrinks
   the model-unresolved wedge at near-term.
3. **Do not chase total-SLR-2150 R²≥0.85** — the learning curve says it needs
   ~10⁸ runs; the irreducible high-order ceiling (R∞≈0.87) means it's the wrong
   goal. Report 2150 with its interaction + (small) caveat wedge instead.
4. **Cost unit:** each cell = 1 FaIR run + 1 BRICK run; the current 10k-cell
   cube is 1×. A 3–4× balanced factorial ≈ 30–40k runs is the recommended
   target; well within Torch `cs`-partition reach (the postaugment already ran
   100k BRICK draws).

## Bottom line

The ceiling is data-limited but the climb is slow and total-SLR-2150 has a real
~0.87 asymptote. A ~3–4× **balanced factorial** ensemble (~30–40k runs) is the
sweet spot: model-free ANOVA cross-check + a stronger surrogate, validating the
emissions-axis correction without an impractical 30–100× LHS expansion. The
shipped normalized figure stands on its own in the meantime.
