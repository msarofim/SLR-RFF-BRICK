# Handoff — 2026-05-20 — Permafrost + CH4/O3/carbon-cycle extension

This is a project-launch handoff. A fresh Claude session should be able
to start cold by reading this note plus `~/.claude/CLAUDE.md`, the
project's `CLAUDE.md`, and the user's auto-memory at
`~/.claude/projects/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/memory/`.

## 1. Project scope

Extend the SLR-RFF-BRICK climate pipeline to include:

1. **Permafrost CO2 and CH4 release** as a temperature-driven positive
   feedback. Currently the FaIR v2.2.4 + Smith v1.4.1 calibration treats
   the carbon cycle as having no significant permafrost contribution —
   that's a documented gap in AR6-class reduced-complexity models.
2. **Atmospheric chemistry of CH4 and O3** beyond what's already in
   FaIR's standard forcing pathway. Specifically: tropospheric O3
   production from CH4 oxidation, stratospheric water vapor from CH4
   oxidation, and the OH-CH4 feedback that lengthens CH4's lifetime as
   atmospheric CH4 rises. FaIR has *some* of this baked into its forcing
   coefficients but the chemistry is highly aggregated.
3. **Extended carbon cycle representation**, particularly the
   temperature-dependence of ocean/land sinks under high warming. FaIR's
   Joos-style impulse response carbon cycle is the standard simplification
   here; the question is whether to keep it or substitute something
   richer (e.g., a coupled OCMIP-style ocean carbon module).

## 2. Key methodological choices to flag upfront

A fresh session should *not* silently resolve any of these — get explicit
direction from Marcus before committing to one:

### 2.1 Permafrost representation

- **Schaefer-style empirical** (Schaefer et al. 2011, 2014): temperature
  drives a logistic / Arrhenius-style cumulative permafrost-carbon release,
  parameterized against site-level studies. Easy to plug into FaIR as an
  added emissions stream.
- **PInc-PanTher / Schneider von Deimling 2015**: probabilistic ensemble
  approach, gives a distribution of permafrost emissions per °C of
  warming. Natural fit to FaIR's probabilistic framing.
- **CMIP6-resolved (Lawrence et al. 2020)**: pull out a parameterization
  from a full Earth System Model run. More work, more "official-looking,"
  but pegs you to whatever ESM you choose.

### 2.2 Feedback coupling vs. forcing perturbation

- **Coupled feedback:** at each timestep, FaIR's GMST drives permafrost
  emissions, which feed back into FaIR's atmospheric CO2/CH4
  concentrations, which drive GMST. Requires modifying FaIR's emissions
  pathway each year. More physically accurate but more invasive
  modification of the FaIR driver.
- **Forcing perturbation:** run baseline FaIR (current SLR-RFF-BRICK
  pipeline), compute permafrost emissions from the baseline GMST
  trajectory, add as additional forcing, re-run FaIR. Simpler but ignores
  the feedback. Probably fine as a first cut.

### 2.3 Calibration validity

The FaIR-calibrate v1.4.1 posterior was fit *without* explicit permafrost
feedback. If you couple in a permafrost feedback now, the posterior
parameters may double-count the response (the calibration "absorbed" some
permafrost-like behavior into other parameters like climate sensitivity).
Options: re-calibrate (a lot of work), use a low-permafrost subset of
v1.4.1 (fragile), or apply a correction factor (least defensible). Flag
explicitly to Marcus.

### 2.4 Scenarios

Use the same RFF-SP set, or wait for the van Vuuren scenarios (the other
new project)? Each gives a different probability structure for the
emissions input.

## 3. What's reusable from SLR-RFF-BRICK

Path references assume the repo is at
`/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/`.

| Existing component | Relevance to permafrost extension |
|---|---|
| `python/lhs_climate_pilot{,_ext}.py` | FaIR cube generator. Likely needs modification to inject permafrost emissions stream. |
| `python/run_fair_rff.py` | Single-RFF FaIR runner. Good place to prototype permafrost coupling on one RFF before factorial. |
| `data/RFF-SP-emissions/` and `data/RFF-SP-socioeconomics/` | RFF-SP emissions inputs. Still applicable for the emissions side. |
| `python/scripts/build_lhs10k_metadata.py` | LHS sampling — can be reused if you add a permafrost-parameter dimension to the LHS. |
| `python/scripts/run_4way_slr_decomp.py` / `run_pulse_*` | Hawkins-Sutton decomposition with BRICK posterior. Could be extended to a 5-way (adding "permafrost-parameter" as a 5th variance source). |
| `outputs/lhs10k_metadata.csv` | The current LHS-10k design. Reuse RFF / cfg / post columns; add permafrost-param columns. |

The SLR side (BRICK, Wong importance weighting, LHS-10k design,
Hawkins-Sutton infrastructure) is essentially unchanged — permafrost
modifies inputs to BRICK (via the FaIR-produced GMST), not BRICK's
internals.

## 4. Suggested first steps (in order)

1. **Decide methodology** (§2 above) with Marcus before any code is written.
2. **Prototype on one RFF-SP draw** with `python/run_fair_rff.py`. Add
   a permafrost emissions stream as a function of GMST(t), run FaIR
   with and without it, plot the difference. Sanity-check the magnitude
   against published permafrost-feedback estimates (~0.1–0.4 K extra by
   2100 in CMIP6 literature).
3. **Pulse-permafrost diagnostic**: zero-permafrost-perturbation gives
   bit-identical pairs (the universal CLAUDE.md §"Sanity tests for
   paired/marginal experiments" check applies).
4. **Sign-flip check**: forcing the permafrost emissions to be negative
   should anti-symmetrically reduce GMST. If not, your coupling is buggy.
5. **Scale to full ensemble** only after the sanity tests pass on a
   single draw.
6. **Variance decomposition** (Hawkins-Sutton): treat permafrost
   parameters as a new dimension and run the extension to the 4-way
   decomposition. Probably ends up 5-way (emissions / climate / internal /
   permafrost / BRICK).
7. **Repo decision**: extend SLR-RFF-BRICK as a branch, or create a new
   repo (`SLR-RFF-FaIR-PF-BRICK`?). Discuss with Marcus before forking.

## 5. External references to track down

- **Schaefer K. et al. 2011.** "Amount and timing of permafrost carbon
  release in response to climate warming." Tellus B.
- **Schaefer K. et al. 2014.** "The impact of the permafrost carbon
  feedback on global climate." Environmental Research Letters.
- **Schuur E. et al. 2015.** "Climate change and the permafrost carbon
  feedback." *Nature* 520:171–179.
- **Schneider von Deimling T. et al. 2015.** "Observation-based modelling
  of permafrost carbon fluxes with accounting for deep carbon deposits
  and thermokarst activity." *Biogeosciences*.
- **McGuire A.D. et al. 2018.** "Dependence of the evolution of carbon
  dynamics in the northern permafrost region on the trajectory of climate
  change." *PNAS*.
- **Lawrence D.M. et al. 2020.** "Land Use and Land Cover Changes
  in CMIP6." (For CMIP6 land-permafrost coupling structure.)
- For CH4 chemistry: **Holmes C.D. 2018** (CH4 oxidation in chemistry-
  climate models), and **Naik V. et al. 2013** (preindustrial-vs-present
  CH4 lifetime).
- For carbon cycle: **Joos F. et al. 2013** (IRF-based carbon cycle, the
  basis of FaIR's approach) and **Friedlingstein P. et al. 2014**
  (carbon-climate feedback inter-comparison).

## 6. Open questions a fresh session should ask Marcus on Turn 1

- "Permafrost methodology: Schaefer-empirical, Schneider-probabilistic,
  or CMIP6-resolved? Coupled feedback or forcing perturbation?"
- "Do we re-fit a FaIR calibration that's permafrost-aware, or keep
  v1.4.1 and document the over-counting?"
- "Same RFF-SP set as SLR-RFF-BRICK, or wait for the van Vuuren scenarios
  to be online first?"
- "New repo, or extend SLR-RFF-BRICK on a branch?"
- "How does this work relate to BRICK / sea-level? Are we re-running the
  SLR pipeline with permafrost-modified GMST, or is this a GMST-only
  question for now?"
