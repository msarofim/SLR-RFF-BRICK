# Handoff — Thread 5: options C and D resolved; the channel inversion priced

**Start-here document for the next session.** Repo `SLR-RFF-BRICK`, branch
**`ladrillo-dev`**, HEAD `0bafe2a`, **pushed and in sync with origin**.
Predecessor: `notes/scoping_2026-08-16_thread5_greenland_2300.md`.

> **BRANCH RENAMED 2026-08-16: `brick-mengel-vnext` → `ladrillo-dev`.** The old
> remote branch is **deleted**; `main`, `brick-mengel` and `brick-v1.2-vehicle`
> are untouched, and `main` remains the default. **Every note dated before
> 2026-08-16 refers to `brick-mengel-vnext`** — those notes are deliberately
> FROZEN (records of what was known when written), so read the old name as this
> branch rather than editing them. This closes the rename carried from handoff
> 13d. The name was chosen because Ladrillo 1.0 requires Greenland pass-1 step 5,
> which has **not** been run, so everything here is still pre-1.0.

**Bottom line: C is abandoned, D and D2 both fail, and the one genuine blocker
(the channel inversion) turned out to cost 0.067 nlp to fix. Nothing is left
blocking except a re-tune decision.**

---

## 0. READ THIS FIRST — three errors in the predecessor handoff

The 2026-08-16 scoping handoff carries three claims that do not survive checking.
Do not re-inherit them.

1. **"28 cm (PISM-like) vs 86 cm (Yelmo-like), a factor of three" is NOT a §19
   finding.** It is §16's, computed from curves §16 itself labels *"illustrative
   … not proposed calibration forms"*. **§19.3 explicitly retracts it**
   ("CORRECTION 1 — the threshold-location arm is not decisive after all"), and
   **§20 then voids §19.3's own basis** (the Bochow-2026 Table 2 transcription
   has `a` and `c` both negative, so the cubic is strictly monotonic and has **no
   fold at all**) and calls the 85.7 cm figure "superseded".
2. **"against A+B 19.15" is A+B′**, which scores 19.154. A+B scores **17.856**.
3. **"A+B+C projects 72 cm at 2100 under SSP5-8.5" is not reproducible.** The
   committed pass-1 `gis_offline_cell_fits.csv` and a clean re-run both give
   **10.62 cm**. The A+B+C fit reproduced exactly (563.196381 both times), so
   this is not a seed difference. Source of the 72 cm unknown.

**Also, a harness gotcha that caused a false alarm:** the log line
`fitted <cell> nlp=` prints the **pre-repair** score. The CSV carries the
**post-repair** value (e.g. B: 234.92 in the log, 232.07 in the CSV). **Compare
CSV to CSV.**

---

## 1. THE FOUR DECISIONS — all resolved (Marcus, this session)

| # | decision | resolution |
|---|---|---|
| 1 | Bochow 2026 admissible as calibration target? | **Benchmark only.** Moot in practice — the C calibration target is the *published* Bochow **2023** ladder (Nature 622:528, Zenodo CC-BY-4.0), a different object from the 2026 EGUsphere preprint. Calibration never embedded a preprint. |
| 2 | One ladder family or carry the arm? | **Carry both arms** — conditional on no outside information tipping it; verified none does (§2 below). |
| 3 | New vintage or offline arm? | **Offline first.** Still open at the end — see §7. |
| 4 | Is a millennial τ acceptable downstream? | **Not blocking; the premise is false** (§3 below). |
| — | Option C itself | **ABANDONED** (Marcus, after the D/D2 results). |
| — | G4 scenario spread | **Downgraded from blocker to documented divergence** (Marcus). |

---

## 2. DECISION 2 — "PISM graded vs Yelmo step" is a SAMPLING ARTEFACT

`python/diag_ladder_transition_resolution.py`. This discharges the validation
that scoping §18 item 4 and §20 both left outstanding.

| family | rungs | GMT grid | largest jump | width | in its OWN finest intervals |
|---|---|---|---|---|---|
| PISM-dEBM | 16 | **0.420 K uniform** | 4.64 m | 0.420 K | **1.0× → UNRESOLVED** |
| Yelmo-REMBO | 15 | 0.084–1.681 K (**refined at its threshold**) | 4.14 m | 0.084 K | **1.0× → UNRESOLVED** |

**Both transitions are exactly one grid interval wide.** Neither ladder resolves
its own transition, so each apparent width is an upper bound set by the sampling
design. PISM only looks "graded" because its grid is 5× coarser there. This
confirms §19.4's "both are cliffs, they differ only in *where*" **from raw model
output** instead of from the retracted preprint text.

**Where the arm bites — committed loss, low warming only:**

| SSP | peak GMT (L11) | PISM | Yelmo | ratio |
|---|---|---|---|---|
| **SSP1-2.6** | **1.92 K** | **1.48–1.64 m** | **4.90–6.05 m** | **3.52×** |
| SSP2-4.5 | 3.19 K | 6.79–7.01 m | 6.60–7.05 m | 1.01× |
| SSP5-8.5 | 7.81 K | saturated 7.40 m | saturated 7.42 m | 1.00× |

Brackets deliberately **not interpolated** — interpolating across a transition
neither model resolved would invent a shape. Note SSP5-8.5's 7.81 K peak is
**above the ladder's 6.80 K top rung**; harmless (both saturate) but must be
stated if C ever returns.

**Paleo checked and REJECTED as a tiebreak.** LIG GrIS estimates cluster
3.7–5.5 m, nearer *Yelmo* — the opposite of a PISM lean. Unusable: only ~55% of
Eemian SMB change is attributable to ambient temperature, **~45% to insolation
and nonlinear feedbacks** (van de Berg et al., Nature Geo doi 10.1038/ngeo1245),
whose own conclusion is that Eemian-based projections "may **overestimate** the
future vulnerability of the ice sheet". Confounded in exactly the direction that
would spuriously favour Yelmo.

Standing → PISM (twice in ISMIP6-Greenland, Goelzer 2020 TC 14:3071); physics on
the disputed mechanism → Yelmo (REMBO's retreat-precipitation feedback, which
dEBM-simple cannot represent); Bochow's own authors decline to adjudicate.
**Nothing tips it → carry both arms.**

---

## 3. DECISION 4 — the pulse work does NOT read this module

`python/diag_greenland_exposure_in_pulse_metrics.py` (re-checks the wiring on
every run, so the claim cannot go stale silently).

**Structural.** All four pulse drivers (`project_pulse_hybrid_mengel`,
`pulse_signsweep_brick_mengel`, `run_mimibrick_pulse_versioned`,
`project_pulse_ssp245_mengel`) build via **`build_brick_mengel`**, which replaces
only the **glacier** slot with `glaciers_mengel` and leaves Greenland as **stock
MimiBRICK SIMPLE**. The Ladrillo A+B Greenland is installed **only** by
`build_brick_nu3_gis`, which no pulse driver calls. Their parameter lists confirm
it — they update `greenland_a/b/α/β/v₀`, never `gis_c1/gis_c0/gis_alpha_f`.

**Quantitative.** Greenland's share of the weighted marginal pulse response:

| horizon | AIS | GSIC | **GIS** | TE | CO2 GIS | CH4 GIS | gap |
|---|---|---|---|---|---|---|---|
| 2130 | 78.8% | 1.6% | **3.9%** | 15.7% | 3.9% | 4.6% | **0.7 pp** |
| 2180 | 81.6% | 1.1% | **4.0%** | 13.3% | 4.0% | 4.7% | **0.7 pp** |

Near-equal in both pulses ⇒ largely **common-mode in the CO2e ratio**. Measured
under stock SIMPLE; a C+D Greenland would differ, so **re-run this diagnostic if
any pulse driver is repointed at `build_brick_nu3_gis`.**

---

## 4. OPTIONS C AND D — both fail, and the reason for D is ALGEBRAIC

### Scores (CSV, post-repair)

| cell | n_par | nlp | hindcast RMSE | 2100 spread | 2100 ssp585 | **ladder leverage** |
|---|---|---|---|---|---|---|
| **A+B** (incumbent structure) | 8 | **17.86** | **0.062** | 10.44 | 17.37 | n/a |
| A+B+C | 7 | 563.20 | 0.844 | 0.28 | 10.62 | **757.42 cm** |
| A+B′+C | 6 | 118.15 | 0.350 | 6.24 | 16.31 | 4.29 cm |
| A+B+C+D | 9 | 47.04 | 0.128 | **0.00** | 7.01 | 9.68 cm |
| A+B′+C+D | 7 | 109.01 | 0.349 | 5.75 | 15.54 | **0.00 cm** |
| A+B′+C+D2 | 9 | **20.96** | **0.082** | 15.69 | 27.54 | 1.14 cm |

*Ladder leverage* = range of 2300 ssp585 when the committed loss is scaled
0.5×–22.6× with everything else fixed. It is **C's own leverage**: if it is ~0,
option C is inoperative whatever else the numbers say.

### D (constant throughput cap) — the algebraic obstruction
`dL/dt = min(r·(L_eq − L), q)`. **Wherever the min selects `q`, `dL/dt` is
independent of `L_eq`.** A binding cap does not limit the commitment's influence,
it **removes** it. Measured: the capped channels sit **at** the cap in **99–100%
of projection years**, so A+B+C+D reduces to `dL/dt = q_f + q_s = 0.073631 cm/yr`
constant and returns **7.0091 cm at 2100 under all three SSPs, identical to 6
dp** — arithmetic, not physics. **D neuters C.**

### D2 (state-dependent throughput) — better fit, achieved by deleting C and D
Michaelis-Menten rise-then-plateau in temperature × marine-margin extinction in
cumulative loss. Sources: **Aschwanden et al. 2019** (Sci Adv
10.1126/sciadv.aav9396 — by 2300 under RCP8.5 almost all NW Greenland outlets are
land-terminating and discharge is greatly reduced, i.e. the channel **peaks and
declines** on our horizon); **King et al. 2020** (Comms Earth Env 1:1, ~4–5%
speedup per km retreat). **Deliberately excluded: moulins / basal lubrication as
a growing tail** — that mechanism **self-limits** (melt switches the bed from a
cavity system to a channelized one with lower pressure and *reduced* motion —
Shannon 2013 PNAS 10.1073/pnas.1212647110; Andrews 2016 Nat Comms 7:13903). The
term that keeps growing is surface melt = the uncapped `smbrate` channel, so the
physics is a **handover** from discharge to SMB.

D2 **passes the hindcast gate (0.0815, first C-cell ever)** but fails both
projection gates, and it fits by **deleting the machinery it was given**:
`q_thalf` **railed at its upper bound 20** (MM saturation railed OFF, factor
near-linear), `q_marine` = **11.02 cm** against a 10.0 floor (marine margin spent
almost immediately, dynamic throughput **exactly 0.00000 cm/yr by 2100** in all
SSPs), `alpha_s` → 0.

### THE SYNTHESIS
**The better the fit, the deader the ladder.** The one cell with a live ladder
(757 cm) is by far the worst fit; every acceptable fit has leverage ≤ 9.68 cm;
and **A+B with no C at all still fits best of everything**. Across five
structures, **no configuration was found in which C both fits the hindcast and
moves 2300**. Three independent routes agree 2300 Greenland is **throughput-
limited, not commitment-limited** (this fit series; §19.3's millennial-τ argument,
weak because it rests on the retracted table; and the arithmetic that 7.42 m by
2300 needs ~2.65 cm/yr sustained).

**→ Marcus abandoned C.** Recommended surviving use: **a committed-loss
diagnostic** — evaluate `V_eq` on each scenario's GMST as a post-processing step,
report both PISM and Yelmo arms (§2's 3.52× at SSP1-2.6), clearly labelled as
multi-millennial equilibrium and kept separate from realised SLR. This needs **no
refit and no vintage**, and it is where the decision-2 arm is decisive.

---

## 5. THE CHANNEL INVERSION — cosmetic, 0.067 nlp to fix

`python/diag_gis_channel_inversion.py`. Three tests chosen to **separate**
hypotheses, not confirm one.

- **T1 EXCHANGEABILITY.** Swapping the channels leaves the hindcast residual
  **bit-identical (0.000e+00 cm)** — they enter `L_total` symmetrically, so the
  126-yr target carries **zero** label information. The swap costs **44.20 nlp**,
  *all* of it the Mouginot penalty. **Label assignment rests entirely on one
  prior term with σ = 0.05.**
- **T2 WHAT MOUGINOT PINS.** It constrains the fast share of the extra loss
  **RATE** (0.7351, target 0.735); `f` is the share of the **COMMITMENT**
  (0.7827). They differ by 0.048. **Neither constrains `alpha` — a share cannot
  pin a sensitivity.** Hence `alpha_f − alpha_s = −0.00424`, crossover at
  **T_south = 1.740 K**.
- **T3 ORDERED REFIT (decisive).** Imposing `alpha_s ≤ alpha_f` **and**
  `beta_s ≤ beta_f`:

| | nlp | hindcast RMSE |
|---|---|---|
| unconstrained | 17.856 | 0.0617 |
| ordered | **17.923** | **0.0604** |
| **cost** | **+0.067** | *improves* |

Ordered τ_fast/τ_slow = 242/10⁹, 128/10⁶, 87/273, 66/137, 45/68 yr at
T_south = −1/0/1/2/4 K — correctly ordered everywhere, and it **restores a
long-timescale reservoir** (the "nothing exceeds ~221 yr" half of the defect).

**CAVEAT, must ship with it:** at the ordered optimum
`alpha_f = alpha_s = 0.0036625` **exactly** — the constraint binds at equality.
The data are **indifferent** about which channel carries the sensitivity; the
ordering is carried entirely by `beta_f` (0.0078) vs `beta_s` (1e-6, railed).
**This is a prior we chose, not a result the data supported.** Flatness
corroborated: `c0` moves 61.99 → 6.75 and `g` moves 0.917 → 0.244 between the two
optima at essentially the same fit.

---

## 6. G4 — provenance, and why it was downgraded

The 6.3–7.3 band is the **min–max of four EXTERNAL emulators**, from
`outputs/ladrillo_model_comparison_L10_spread.csv`: FACTS FittedISMIP **6.343**,
MAGICC-SLR **7.091**, FACTS bamber19 **7.230**, FACTS emuGrIS **7.263**. It is a
*resemble-your-peers* check, **not a physical bound** — reinforced by the standing
decision that ISMIP6 is evaluation-only permanently so Ladrillo does not become a
second-hand FittedISMIP.

**The same file lists Ladrillo L10 itself at 7.394** — essentially on top of the
peer cluster. The 10.44 cm figure is the **offline A+B cell**, a different object
from what ships. A+B's *levels* are physically fine: 2100 ssp585 **17.37 cm**
(inside AR6's ~9–18) with ssp126 **6.93 cm**. For scale, the same file's AIS
spreads run **−2.32 to +35.45 cm** across FACTS modules — Greenland is the
well-behaved component.

---

## 7. WHAT IS LEFT BEFORE FINALIZING

**No blockers remain.** What is left is one decision and a documentation list.

**THE DECISION (was decision 3, now with a price and a benefit):** the ordering
constraint must be applied at the **calibration** level — this test is on the
offline A+B optimum, while L11 carries `gis_slow_ell`/`gis_slow_w`, not native
`alpha_s`/`beta_s`. Carrying it into the deliverable needs a **re-tune + 4×2M +
re-acceptance (~5 h unattended) and a new vintage**. Buy it, or ship L11 with the
inversion documented?

**If a vintage happens, fold in:**
- the deferred `d2_basis` one-liner (weighted metric on the steric stream only;
  +1.7 cm on a 95 cm 2100 ssp585) — explicitly parked for "whatever vintage this
  Greenland work produces";
- the `beta_s` rail at 1e-6, which persists in **both** the constrained and
  unconstrained optima and is **still undiagnosed**.

**Caveats that must ship either way:**
- the commitment is **unidentified** (the φ·L_eq ridge; re-confirmed, no
  structure fixed it);
- the **amp(GMST) law is projection-side only** — the calibrator runs at constant
  `GIS_AMP` = 1.92, so calibration and projection use different Greenland
  amplification. Justify or align;
- `gis_g` = 0 and `gis_v0` = 7.42 m are **fixed by argument, not fitted**;
- R̂ = 2.359 non-mixing is a reporting caveat;
- G4 divergence per §6;
- the channel ordering is **imposed, not identified** (§5).

---

## 8. NON-OBVIOUS STATE

- **All work is PUSHED** (11 commits, `63e91cf` → `0bafe2a`), and the **branch
  rename carried from handoff 13d is DONE** — see the banner at the top. Both
  items are off the outstanding list.
- Working tree clean except `figures/diag_gis_regional_driver.png`, modified
  **before** this session — not ours.
- `FaIRtoFrEDI/CLAUDE.md` documents this repo's branches as *main /
  brick-mengel (archived) / brick-v1.2-vehicle* and **never listed the working
  branch at all**, so it did not go stale in the rename — but it also does not
  mention `ladrillo-dev`. Worth adding when someone next edits that file;
  deliberately not done here, since restructuring the cross-repo branch table is
  outside this thread.
- **Mid-session the macOS TCC grant for `~/Documents` was lost** (metadata
  readable, `open` denied, unaffected by disabling the sandbox, and Claude's own
  `request_directory` grant did **not** fix it). Fixed via System Settings →
  Privacy & Security → Files and Folders / Full Disk Access, then restart. If
  reads start failing with `EPERM` while `ls` works, this is why.
- `gis_offline_cell.py` now carries cells `A+B+C+D`, `A+B′+C+D`, `A+B′+C+D2` and
  the `_throughput` / `dyn_throughput` machinery. **D nests C bit-exactly**
  (verified 0.000e+00); **D2 nests D only asymptotically** (2.4e-2 cm) and is
  labelled as such — a warm start, not a containment proof.
- `diag_cd_ridge_break.py` gained a third verdict, **"COLLAPSED, NOT
  IDENTIFIED"**, after the D run showed its original "(i) RIDGE BROKEN" verdict
  could fire *vacuously* — 2300 stops depending on `k` because the model stops
  depending on anything. It also prints that the ridge test is **structurally
  uninformative on smbrate cells** (their loss rides on the `k_smb` flux the test
  deliberately does not scale, so the bisection is UNREACHABLE at every k).
- Pre-registrations for C+D are in CHANGELOG **2026-08-16c**, written before any
  C+D cell existed (`d30b203`), with an amendment added while the fit was still
  running and before any C+D cell had been fitted. **Prediction 2 (G4 spread
  would go DOWN) failed outright** — it was flagged in advance as "a prediction I
  could be flattered by", which is why it was worth flagging.
- The §7 **2×2 cross-test was pre-registered and never run.** Moot now that C is
  abandoned; **required if any C ever ships in the dynamics.**

---

## 9. FILES

**Created this session**
| file | purpose |
|---|---|
| `python/diag_ladder_transition_resolution.py` | ladder grid-resolution test (§2) |
| `python/diag_greenland_exposure_in_pulse_metrics.py` | decision-4 wiring + share test (§3) |
| `python/diag_cd_ridge_break.py` | φ·L_eq ridge + ladder-leverage verdicts (§4) |
| `python/diag_gis_channel_inversion.py` | T1/T2/T3 channel tests (§5) |

**Modified:** `python/gis_offline_cell.py` (D, D2, cells, bounds, nesting),
`CHANGELOG.md` (entries 2026-08-16c/d/e/f).

**Outputs:** `outputs/diag_{ladder_transition_resolution,
greenland_exposure_in_pulse_metrics, cd_ridge_break, gis_channel_inversion}.csv`,
refreshed `outputs/gis_offline_cell_{fits,series,ridge}.csv`,
`figures/gis_offline_cell.png`, logs `outputs/log_gis_offline_cell_CD{,2}.txt`.
