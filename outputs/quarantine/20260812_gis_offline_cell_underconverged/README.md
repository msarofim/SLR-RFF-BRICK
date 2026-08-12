# Quarantine 2026-08-12 — `gis_offline_cell` outputs from the under-converged fitter

## 1. What the bug is

`python/gis_offline_cell.py` reported optima that are **not optima**. The
multi-start Nelder-Mead protocol drew every start **uniformly** over bounds that
span five orders of magnitude on the rate axes (`alpha*`, `beta*` ∈ [1e-6, 0.2]),
ran 60 of them, and took the best result **without a restart**. A uniform draw
on [1e-6, 0.2] puts essentially no mass below 1e-3, so the slow end of every rate
axis was never explored; and one NM call is not a converged minimisation on this
objective, because the simplex degenerates on the flat log-scaled directions and
stops.

**The tell, and it was sitting in the committed outputs the whole time:** in
`gis_offline_cell_ridge.csv`, **214 of the 225** A+B `(f, beta_f)` grid
points — which *fix two parameters* and re-optimise the other six with a
*weaker* inner optimiser (`RIDGE_MAXFEV=1500`, single start) — scored **below**
the reported 8-parameter optimum of `nlp = 42.5228`, by up to 24 units. A
constrained fit cannot beat an unconstrained one at the same objective.

Verified not to be a difference of objective: re-evaluating the committed A+B
parameter vector under the corrected code reproduces `nlp = 42.5228`, spread
6.301 cm, RMSE 0.0987 cm and Mouginot share 0.741 exactly. The two numbers are
the same function at different points; one of them is 24.7 units from the
minimum.

**This is a bug, not a vintage difference.**

## 2. Files quarantined here

Produced by `python/gis_offline_cell.py` at commit `0259ec5` and earlier:

| file | what it is |
|---|---|
| `gis_offline_cell_fits.csv` | per-cell parameters, gates, projections — **the table behind Greenland pass-1 decision 4** |
| `gis_offline_cell_series.csv` | per-cell hindcasts |
| `gis_offline_cell_ridge.csv` | the separability profiles (also affected: point-to-point scatter ±6 nlp, larger than the `RIDGE_DELTA = 2.30` threshold applied to it) |
| `gis_offline_cell.png` | the figure built from the above |

## 3. Canonical replacement

Re-run to the same canonical paths — `outputs/gis_offline_cell_{fits,series,ridge}.csv`,
`figures/gis_offline_cell.png` — by the corrected script. The correction is
three changes in `python/gis_offline_cell.py`, all under the
`# ---- fitting protocol` constant block: log-uniform draws on the rate axes,
`N_MULTISTART` 60 → 240, and a restart-until-no-improvement `polish()`. The
ridge is seeded at the converged optimum and restarted.

`convergence_check()` now enforces the invariant above on **every run** and
raises if any ridge point beats the reported optimum, so this failure mode
cannot recur silently.

## 4. Size of the impact — read this before reusing any pre-fix number

For A+B (the module chosen in pass 1), committed → converged:

| quantity | pre-fix | post-fix |
|---|---|---|
| neg log posterior | 42.52 | **17.86** |
| RMSE | 0.0987 cm | 0.0617 cm |
| mid-century bias (G2) | −0.045 cm | +0.015 cm |
| modern rate (G1) | 0.758 mm/yr | 0.775 mm/yr (obs 0.841) |
| Mouginot surface share | 0.741 | 0.735 (constraint 0.735) |
| **2100 scenario spread (G4)** | **6.30 cm — inside the 6.3–7.3 band** | **10.44 cm — ABOVE the band** |
| 2100 SSP5-8.5 | 13.77 cm | 17.37 cm |

`c0` is deliberately not tabulated. Two converged runs under different seeds
returned `c0 = 61.99, g = 0.917` and `c0 = 5.21, g = 0.183` at the same
`nlp = 17.856` and 2100 projections agreeing to **< 0.001 cm** in all three
scenarios. `(c0, g)` is a flat manifold, not a shifted estimate — which is an
independent confirmation of item 4.1's verdict on `g`.

Every gate verdict except **G4** is unchanged, and the hindcast gates all
improve. **G4 flips.** So the statement carried in
`notes/handoff_2026-08-12_ladrillo_gates_cleared_step5_ready.md` §6 — "A+B's
6.30 cm 2100 spread is *on* the evaluation band floor (6.3–7.3), not inside it.
The joint calibration can only push it down" — is a property of the
under-converged fit and **must not be reused**. The converged A+B sits *above*
the band, so the joint calibration pushing the spread down is now the expected
and desirable direction rather than a worry.

Diagnostics: `python/diag_gis_g_betaf.py`, `outputs/gis_g_betaf_variants.csv`,
`outputs/gis_g_betaf_profiles.csv`, `figures/gis_g_betaf.png`.

## 5. What is NOT affected

- **The Julia port.** `julia/greenland_ab_component.jl` ports the model
  *structure*, and `julia/validate_greenland_ab.jl` validates it against the
  offline cell at 1e-9 by running **both** at the same parameter vector. That
  test is a structural identity check and is indifferent to which parameter
  vector it is run at.
- **The extC posterior.** It predates the Greenland module entirely; the
  offline cell never fed it.
- **Gates 3.1 and 3.2.** Neither used `gis_offline_cell_fits.csv`.
