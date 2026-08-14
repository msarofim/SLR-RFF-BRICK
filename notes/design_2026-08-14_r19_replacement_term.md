# Design — the R19 replacement term for D1

Marcus, 2026-08-14: "Design the R19 replacement term." Evidence:
`julia/diag_r19_deliverable_leverage.jl`, `diag_r19_hindcast_visibility.jl`,
`diag_r19_replacement_target.jl` → the matching `outputs/diag_r19_*.csv`.

**Bottom line.** The term can be built, and §5 specifies it. But the four
measurements below change what D1 *is*: the total stream is the only observation
in the whole system that constrains R19's historical trajectory, so any
replacement is that stream's information recycled, not new information. D1 stops
being "drop a redundant stream" and becomes "drop a stream and carry one
parameter's worth of it forward as a summary". That is a methodological choice,
so it is put to Marcus in §6 rather than settled here.

---

## 1. It matters — this is not an `ais_iceflow0`-style caveat

The first thing to check, because the repo has a standing precedent against
promoting a marginal shift to a blocker: `ais_iceflow0` fails its marginal R̂ at
2.359 and is a *reporting caveat*, because thread 3 measured it explaining
R² < 0.001 of the projection. So the D1 R19 shift was tested on the deliverable.

Median projection shift from moving R19 to its D1 posterior, cm:

| scenario | component | 2100 | 2300 |
|---|---|---|---|
| SSP1-2.6 | glaciers | −0.34 | −0.07 |
| SSP2-4.5 | glaciers | −0.23 | **+0.77** |
| SSP5-8.5 | glaciers | +0.02 | **+1.44** |
| SSP5-8.5 | total | −0.04 | +2.19 |

**MATERIAL.** Up to 1.44 cm on the 2300 glacier median (1.67 cm moving the whole
R19 block). Read the *glaciers* column: R19 enters the total only through
glaciers, and the total at 2300/SSP5-8.5 carries AIS-tail median noise at 400
draws. The 2100 numbers are small (≤0.44 cm) — this is a 2150+ problem, like
Greenland's.

## 2. The total really could see it

Signature on the modelled total of moving `gic_T_off_R19` from the L10 median to
the D1 median: **mean 0.62 cm, max 1.47 cm** over 1900-2024, against a
total-stream σ of 0.232-0.565 cm on a window mean (spec §2). Ratio **6.3**. So
this is genuine information loss, not a weakly-identified parameter relaxing.

## 3. But nothing else can see it, and a modern-rate term least of all

**No other channel contains R19.** The Frederikse glacier target assumes zero
R19 melt by construction; the gsic component channel is `HIND_BLOCKS =
SLOWP+FAST`; the GlaMBIE term is on the SLOWP/FAST *share*. R19 is in none of them.

**GlaMBIE's own R19 is too weak to substitute.** Rate 0.04925 mm SLE/yr with
σ = 0.03606 as coded (**1.37 σ**) or 0.17423 under the within-region serial
correlation the GlaMBIE restructure itself argued for (**0.28 σ**). Against
SLOWP's 11.47 σ, R19 is the noisiest block in every product.

**And the information is in the wrong place in time for a rate term anyway.**
The signature of the shift on the total, by year:

| 1920 | 1950 | 1980 | 2000 | 2010 | 2024 |
|---|---|---|---|---|---|
| +1.18 | +0.74 | +0.30 | +0.05 | −0.06 | −0.19 |

mean |diff| **1900-1999 = 0.750 cm**, **2000-2024 = 0.087 cm**. Everything is
re-referenced to 1995-2005, so the trajectories converge at the reference and
diverge backwards. **A modern-rate constraint sees 12% of the signal.** This
kills the obvious design (add a GlaMBIE R19 absolute-rate term) on two
independent grounds.

## 4. One number that has to be stated before any of this is enshrined

**L10's R19 modern rate is 3.03× GlaMBIE's**: 0.1490 [0.0544, 0.2300] mm/yr
against 0.04925. That is **+2.77 σ** on the as-coded GlaMBIE σ and **+0.57 σ** on
the correlated one. Under the σ this project has already argued is the right one,
there is **no conflict** — but the point estimate is 3× high, and any target
distilled from L10 inherits that.

## 5. THE TERM

Constrain the **observable**, not the parameter — house rule
(`project_ccx_bound_the_observable_not_the_parameter`: a bound bisected at
defaults leaked). The observable is R19's own cumulative contribution, read from
the model's `:gsic_r19` slot, so no differencing of aggregates is involved.

```julia
# R19 replacement for the dropped total stream (D1). See
# notes/design_2026-08-14_r19_replacement_term.md.
const R19_CUM_WIN   = (1900, 2024)
const R19_CUM_MU    = 1.7558      # cm, L10 posterior predictive mean
const R19_CUM_SIGMA = 0.7767      # cm, its posterior sd
r19_cum = (gsic_r19_cm[yi(R19_CUM_WIN[2])] - gsic_r19_cm[yi(R19_CUM_WIN[1])])
ll += logpdf(Normal(R19_CUM_MU, R19_CUM_SIGMA), r19_cum)
```

Every property checked rather than assumed:

| check | result |
|---|---|
| **discriminates?** D1 R19 block sits **1.79 σ** from the target | yes — has teeth |
| **R19-specific?** corr with `gic_a_SLOWP` +0.038, `gic_a_FAST` −0.024 | yes — duplicates nothing |
| **hits the right parameter?** corr with `gic_T_off_R19` **−0.641** | yes |
| **Gaussian?** skew **−0.03** at 1900-2024 (0.45 at 1900-1950) | yes, at this window |
| **window?** separation rises 1.63 → 1.79 σ from 1900-1950 → 1900-2024 | use the long one |

The 44% relative σ makes this a *weak* term. That is correct, not a defect: it
reproduces exactly what the total knew about R19 and no more.

**Add the GlaMBIE R19 rate alongside it, at the correlated σ.** It is only 0.28 σ
and will barely move anything, but it is the one genuinely independent
observation of region 19, it costs nothing, and it pulls against the §4 3× point
estimate rather than with it:

```julia
ll += logpdf(Normal(0.04925, 0.17423), r19_modern_rate_mm_yr)   # GlaMBIE 2000-2024
```

Verification when it is written: mutation-test it (perturb `gic_T_off_R19` and
require `ll` to move — a term with no effect looks exactly like a term that
works, spec §7.4), and re-run the §1 leverage diagnostic on the new posterior to
confirm the 2300 glacier median comes back.

## 6. THE CHOICE THIS FORCES — for Marcus

The target in §5 is derived from L10, which used the total. So:

**Option A — build the term as specified.** D1's claim changes from "total GMSL
leaves the likelihood" to "total GMSL leaves four streams' worth of likelihood
and its R19 content is retained as a one-parameter summary". This is a
modularised/cut inference: defensible and standard, but it must be *labelled*,
and the D1 write-up in spec §2 must be rewritten. It also means D1 no longer
simplifies the inference as cleanly as advertised.

**Option B — don't drop the total.** D1's stated justification is that the total
is "the loosest constraint in every window". True in aggregate — and beside the
point for R19, where it is the *only* constraint. Keeping it costs the
sd_dang/rho_dang pair and the closure-σ machinery, and buys a genuinely
independent constraint on the one block nothing else sees.

**Option C — drop the total and accept the R19 loss**, with the 2300 glacier
median moving up to 1.7 cm and the R19 marginal reverting to prior-and-rung
dominance. Honest, and defensible *if* the 2300 column is not a deliverable —
but it is exactly the horizon where Greenland is already known to be broken, so
loading a second unconstrained direction onto it is hard to argue for.

**My recommendation: B.** §3 is the reason — this is not a stream we can replace
with better data, because for R19 there is no other data. §5 exists so that A is
a real option if D1 is wanted for other reasons, but a term whose target is
distilled from the stream it replaces is not an improvement in inference, only in
bookkeeping. B keeps the constraint where the information actually is, and the
cost D1 was meant to remove (spec §2.1's closure-σ inflation) can be addressed
directly instead — `--no-closure-sigma` already exists.

## 7. Not addressed here

Whether R19 should be *reparameterised* so the projection does not hinge on a
direction the historical record cannot see. R19 is small historically (0.058 cm
observed cumulative to 2020) and material at 2300 (1.4-1.7 cm) — the same
structural shape as Greenland's commitment ridge. That is a model-structure
question, not a likelihood one.
