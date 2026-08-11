# Handoff 2026-08-11 — Greenland pass 1 built and validated; recalibration GATED on two diagnostics

**Self-contained pickup:** this note + `notes/redteam_2026-08-11_brickf.md` +
the CHANGELOG entry for 2026-08-10/11. The earlier
`notes/handoff_2026-08-10_greenland_pass1.md` and
`notes/scoping_2026-08-10_greenland_options.md` are still useful background but
**both contain numbers this session corrected** — see §2 before reusing them.

Repo `SLR-RFF-BRICK`, branch `brick-mengel-vnext`. All work committed
(`f0374c6` is the tip). Two tracked files are dirty and are incidental:
`figures/diag_gis_regional_driver.png`, `outputs/mcmc/overdispersed_starts.csv`.
53 untracked files, all pre-existing MCMC scratch and raw netCDFs.

---

## 1. Where the work stands

Steps 1–4 of Greenland pass 1 are **done, committed and tested**. Step 5 (joint
recalibration) is **deliberately not started** — it is gated on two diagnostics
in §3.

| step | state | artifacts |
|---|---|---|
| 1. regional driver | DONE | `python/build_t_gis.py` → `data/observations/t_gis_zones{,_allproducts}.csv`, `outputs/gis_driver_constants.csv`, `outputs/gis_amp_prior.csv`, `figures/t_gis_driver.png` |
| 2. V_eq on the PISM ladder | DONE | `python/fit_gis_veq_pism.py` → `outputs/gis_veq_pism_{fit,curve}.csv`, `figures/gis_veq_pism_fit.png` |
| 2b. dT prior | DONE | `python/set_gis_dt_prior.py` → `outputs/gis_dt_prior.csv` |
| 3. offline cell | DONE | `python/gis_offline_cell.py` → `outputs/gis_offline_cell_{fits,series,ridge}.csv`, `figures/gis_offline_cell.png` |
| 4. Mimi port + 1e-9 validation | DONE | `julia/greenland_ab_component.jl`, helpers in `julia/brick_mengel.jl`, `python/emit_gis_port_reference.py`, `julia/validate_greenland_ab.jl` |
| 5. joint recalibration | **GATED** | see §3 |

`./run_brickf_tests.sh` runs **four** suites and all pass, including the three
pre-existing ones. Run it first in any new session — it is the fastest proof
nothing has drifted.

---

## 2. Decisions taken, and the two things they corrected

### Decisions
1. **PISM-dEBM only** as the equilibrium ladder (Marcus). No Yelmo arm.
2. **Driver zone south (59–70 °N)**, HadCRUT5 headline. Re-validated on the
   corrected mask and it is now *more* clearly the right zone than the scoping
   note claimed.
3. **Option C (the ladder as V_eq) is OUT of pass 1.** It failed; see §4.
4. **A+B is the module**: regional driver + two-channel SMB/dynamic split.
5. ISMIP6 remains evaluation-only, permanently.

### Correction 1 — the scoping note's amplification numbers are wrong
`python/scope_greenland_zones.py` used a lon/lat box that put **Iceland** in the
southern band and Baffin/Ellesmere in the northern ones, and applied a land mask
**only to Berkeley Earth**. A/B against the old box reproduces the scoping
numbers exactly, so this is the mask, not code.

- "products agree to **1.19×**" was an artifact of ocean dilution in two of
  three products. Real spread **1.51×**.
- amplification is **N(1.92, 0.32)** (south, 1901–2024), **not N(2.9, 0.2)**.

Option A's leverage is unaffected — scoping §3's "+2.2 → +5.9 cm" used the
RGI-r05 driver at amp 2.04, and corrected HadCRUT5 south is 1.97.

### Correction 2 — the spread deficit is mostly joint-calibration, not structure
Refitting **stock** SIMPLE on Greenland alone, no structural change, takes the
2100 scenario spread from 2.29 to 7.25 cm. Scoping §3's "the transient is the
bottleneck" was measured at the *existing* posterior, where GIS competes with
AIS/GSIC/TE against the total. **The case for A rests on the hindcast** (RMSE
0.533 → 0.061 cm, mid-century bias −0.828 → +0.014 cm), not on the spread.

---

## 3. THE GATE — two diagnostics before step 5

Marcus's priority order. Neither is expensive; both change how the
recalibration is read.

### 3.1 Resolve the target conflict (blocking)

Computed in `notes/redteam_2026-08-11_brickf.md` §0 from
`outputs/recalib_targets_ext.csv`: the five component targets (Frederikse) sum
**0.74 cm above** the independent total target (Dangendorf 2024 + NOAA STAR)
over 1950–1980, while the Greenland component target sits 0.5–0.7 cm *above* the
model over 1942–1982.

| window | Σ components | Dangendorf | residual |
|---|---|---|---|
| 1900–1930 | −12.455 | −12.202 | −0.253 cm |
| 1950–1980 | −3.878 | −4.616 | **+0.738 cm** |
| 1993–2018 | +1.777 | +1.723 | +0.054 cm |

Residual over 1900–2023: mean +0.195, sd 0.477, range [−0.592, +1.540] cm,
trend +0.23 cm/century.

So the likelihood is pulled two ways in mid-century and stock BRICK-F\* resolves
it by under-melting Greenland. **Adding ~0.7 cm of mid-century Greenland melt
will degrade the total fit by about the same unless another component gives it
back.**

**What to do.** This is a data question, and it should be answered on the data
side *before* the MCMC, not diagnosed afterwards from a posterior. Concretely:

- Decompose the 1950–1980 residual by component. Which target contributes the
  +0.74 cm? Frederikse's own components should close against Frederikse's own
  total — check whether the discrepancy is Dangendorf-vs-Frederikse *total*, or
  a component we spliced (GRACE-FO, NOAA NCEI, GlaMBIE).
- If it is Dangendorf-vs-Frederikse at the total level, that is a known,
  citable difference between two reconstructions and the honest fix is to widen
  the total target's σ in that window rather than to let the model split the
  difference silently.
- Record the choice explicitly — it is a methodological choice about target
  construction and must not be resolved by whatever the sampler does.

**Pre-register the three outcomes** (redteam §0) so the posterior is read
against a stated expectation:
1. Greenland improves, total degrades → the conflict is real; fix the data side.
2. Greenland improves, glaciers/TE absorb it → check the GlacierMIP3 rungs and
   the GlaMBIE modern rate did not break.
3. Greenland's improvement is suppressed, posterior ≈ extC → the joint
   calibration limits Greenland, not the module, and pass 1 buys little.

Outcome 3 is live, given correction 2 above.

### 3.2 Attribute the 28 cm BRICK-Mengel → BRICK-F\* shift

Memory `project_brick_mengel_postpred` records BRICK-Mengel at SSP2-4.5 2100 =
**77.7 cm**; BRICK-F\* gives **49.5 cm**. That is the largest single quantitative
movement in the programme and it is **unattributed**. My expectation is that it
is mostly the Antarctic recalibration removing the early-century overshoot, but
**I did not test this and it should not be asserted.**

**Cheapest test:** run the extC projection kernel with the AIS block held at the
BRICK-Mengel posterior medians and everything else at extC (or the reverse), and
read off how much of the 28 cm the AIS swap accounts for. `julia/brickf_projection.jl`
is the tested kernel — use it, do not re-derive the parameter map. The archived
branch `archive/brick-mengel-2026-06-17` has the Mengel-vintage posterior.

**Also:** any deliverable built on the 77.7 cm vintage is affected. Apply the
quarantine rule (`outputs/quarantine/YYYYMMDD_<tag>/` plus a README naming the
bug, the files, and the canonical replacement) rather than deleting or silently
overwriting.

---

## 4. The other updates, ranked (redteam §7)

Items 4.1–4.2 are prerequisites alongside §3; 4.3–4.6 are before external
release.

**4.1 Decide `g`.** The fraction of the 1850 commitment already realised at
1850 fits at 0.711 with no observational anchor before 1900. Stock SIMPLE has
g = 0 by construction. **I introduced `g` so the ladder cells could start
sensibly, and those cells were then rejected** — so it is a loose end I left
open. Recommendation: fix at 0 for A+B unless it earns its place in a
likelihood-ratio sense. This is the weakest thing in the new module.

**4.2 Fix or justify β_f.** The fast rate is unidentified — 100% of its local
range within Δ<2.3 at corr −0.03 (`outputs/gis_offline_cell_ridge.csv`). The
physical reading is benign (once the fast channel is fast relative to a century
its speed stops mattering) but the model should not carry a parameter the data
cannot see. Fixing it at a literature SMB response time costs nothing
measurable and removes a free parameter before the MCMC.

**4.3 Re-check thermal expansion against a modern OHC target.** TE is stock and
was not revisited. Per `mimibrick-quirks` #8 its α is suspected ~3× below the
physics value because Wong's calibration ran against SNEASY OHC anchored to
Gouretski 2007 (~2× Cheng IAPv4.2 over 1953–1996). The fit is fine (bias
+0.24 cm) — a biased α against a biased target reproduces the series. The
exposure is **extrapolation**: TE is 17.3 of the 49.5 cm SSP2-4.5 2100 total and
25.9 cm at SSP5-8.5, driven by FaIR/modern OHC rather than the target it was
fitted against.

**4.4 Report a ν sensitivity once.** The glacier response exponent is fixed per
reservoir (`nu_anch_obsfit`, 1.55–1.62), so transient-shape uncertainty is not
propagated. One sensitivity run and one sentence of justification.

**4.5 Refit with the four glacier set-asides fixed at prior centres.**
`gic_u_unch` (26.5 mm), `gic_delta` (0.21 mm/yr), `gic_u_pre` (6.5 mm),
`gic_s_r5` (2.5 mm) total ~35 mm against a ~90 mm 20th-century signal. If the
glacier residual acquires structure when they are fixed, they were doing real
work; if it does not, they may have been absorbing structural error.

**4.6 State the structural-uncertainty caveat wherever bands are compared.**
The memo already says BRICK bands carry no climate uncertainty (projections use
FaIR *mean* GMST). It should also say BRICK-F\* reports parameter spread within
**one structure**, while FACTS deliberately spans several modules per component
— so our bands understate total uncertainty and are not comparable to theirs.

**4.7 Fix the `brickf_data.py` RNG call-order dependence** at the next
recalibration, as that file's own header says. It is documented and byte-tested
but it means the calibrator's inputs are reproducible only by re-running the
exact development call sequence.

---

## 5. Results worth not re-deriving

**Offline cell** (`outputs/gis_offline_cell_fits.csv`). Acceptance test: stock
SIMPLE at the extC posterior medians, not refitted, reproduces the incumbent —
spread **2.29 cm** vs the known 2.16, mid-century bias −0.83 cm.

| cell | RMSE cm | G1 G2 G3 | surf | 2100 spread |
|---|---|---|---|---|
| incumbent | 0.533 | – – – | – | 2.29 |
| stock | 0.325 | OK OK OK | – | 7.25 |
| **A** | **0.061** | OK OK OK | – | 10.85 |
| **A+B** | 0.099 | OK OK OK | 0.74 | 6.30 |
| A+B′ | 0.068 | OK OK OK | 0.36 | 6.27 |
| A+B+C | 1.675 | OK – – | 0.49 | 51.99 |

A+B's fitted theta: `c1=1.83242; c0=80.4366; f=0.869733; alpha_f=0.00147717;
beta_f=1e-06; alpha_s=0.0437202; beta_s=0.0147444; g=0.711358` (cm units; the
component takes metres — `python/emit_gis_port_reference.py` converts).

**Why C failed, and why it matters for A+B too.** A proportional relaxation
cannot serve both a 6 cm historical loss against a 71 cm commitment and a 742 cm
post-threshold commitment; past the threshold, loss is limited by ice
**throughput**, not by the size of the disequilibrium. That is scoping §10
option D. The same criticism applies to A+B at high warming — its linear L_eq
never reaches the pathological regime, so it is invisible rather than absent.
**Flag it wherever 2300 or high-warming Greenland is reported.** Scoping §13 had
upgraded C and D to active for pass 1; this reverts to §10's defer.

**V_eq**: no smooth parametric form fits the PISM ladder. Relative-weighted
RMSE (m): linear 1.40, saturating 1.53, two-logistic 0.68, **pchip 0.000**. The
two-logistic rails *both* widths at the 0.4202 K rung-spacing floor — it is
asking to be the interpolant. If C is ever revived, `pchip(T − dT)` with dT
sampled is the form, and the dT prior is already derived
(`outputs/gis_dt_prior.csv`, Normal(−0.63, 0.55) truncated [−1.58, +0.22]).

**Separability, pre-registered and answered: no ridge.** f and the fast
timescale are weakly but *independently* constrained. No need for the Antarctic
runoff-line treatment (sampling an identified combination).

---

## 6. Traps and non-obvious state

- **`g = 0` is BRICK's real initial condition.** Stock `greenland_icesheet`
  starts at V(1850) = v₀ — zero realised loss with the full 71 cm of
  disequilibrium already present. Starting it in equilibrium gives a modern rate
  of 0.11 mm/yr against ~0.7 observed. This cost two wrong runs of the offline
  cell. Check [5] of `julia/validate_greenland_ab.jl` exists to stop it
  regressing.
- **Stock `greenland_icesheet` integrates with LAGGED `eq_volume` and `τ_inv`
  (t−1).** The component and the python reference both match this.
- **Driver parameter must be named `greenland_surface_temperature`**, not
  `global_surface_temperature`, or Mimi auto-connects raw GMST. Same frame
  contract the glacier blocks use.
- **Units: the offline cell is cm, Mimi components are m.** The conversion
  happens once, in `python/emit_gis_port_reference.py`, which writes both
  systems so a slip shows as a factor of 100.
- **Mimi will not build with unbound glacier block params** even when you only
  want to validate Greenland — bind them from `outputs/extc_block_constants.csv`.
- **The external interface is still GMST + OHC only**, deliberately. Every
  regional driver is built inside the model as `amp × GMST + offset` with an
  anchor-preserving splice (`brickf_driver` in `julia/brickf_projection.jl`), so
  the drop-in property that distinguishes BRICK-F\* from MAGICC-SLR survives the
  regional-driver change. Do not break this.
- **The eight non-converged AIS marginals are all in the block that sets the
  tail.** The SSP2-4.5 p83 of 41.0 cm is prior-driven, not data-driven.
  Convergence on the deliverable (R̂ 1.000 at 2100) justifies the projections,
  not the tail, and not quoting AIS parameter marginals.
- **A+B's 6.30 cm spread is ON the evaluation band floor** (6.3–7.3), not
  inside it. The joint calibration can only push it down.
- The Bochow-2026 emulator retraction still stands; `outputs/scope_greenland_bochow2026*.csv`
  must not be used. The ladders are raw model output and need no emulator.

---

## 7. If someone asks "is this still BRICK?"

Architecturally yes, component-wise decreasingly. After Greenland, 2 of 5
components are replaced, DAIS is re-parameterised but structurally intact and
load-bearing, TE and LWS untouched. The bigger departure is the **calibration
philosophy**: original BRICK fit a GMSL total; BRICK-F\* fits a component budget
plus process-model equilibrium ladders plus modern regional rates. One-liner:
*the skeleton and the Antarctic are BRICK; the glaciers, Greenland and the
evidence base are new.* Full argument in `notes/redteam_2026-08-11_brickf.md` §5,
positioning against FACTS and MAGICC-SLR in §6.
