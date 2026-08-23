# Handoff — the commitment defect is now MULTI-MODEL and its free parameter is pinned from outside; the option space is closed to one survivor; and the onset was set to protect a number we now know is wrong

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, through `d0a5870` + one
housekeeping commit. Written 2026-08-23, to be picked up cold.

**Supersedes** `handoff_2026-08-23_greenland_targets.md` for its **§5 ranking** (items 1–3
are done) and for its §2.4 reading of the 2100 error. Its §1, §2.1–2.3, §3 and §6 are
**unchanged**; §1.1 is now *confirmed from outside the model*.

**Read with** `notes/scoping_2026-08-23_leq_options.md`, which is the decision layer for
what to build. This handoff is the evidence layer.

---

## 0. THE ONE-PARAGRAPH VERSION

Marcus re-stated the priority ordering mid-session (**volume+history > commitment >
melt-rate > transient models > simplicity**, and **test stringency scales with the number
of models**), which moved the work off the 2100 transient match — priority 4, scored
against ONE ice-sheet model — and onto priorities 1 and 2. Three results. **(1) Volume
PASSES**: `GIS_V0_M` = 7.42 m sits inside CLIMBER-X's 7.30–7.68 m range. **(2) The linear
`L_eq` is refuted in SHAPE, and now by more than one model**: CLIMBER-X commits 7.16 m at
2.0 K where we commit 0.160 m (**45×**), and Greve/SICOPOLIS — an independent model that
**passes** the observed-rate gate CLIMBER-X fails — exceeds our **φ = 1 ceiling** in 5/5
cells by **5.8–9.5×** at year 3000, while we are already **2.1× short at 2300**. **(3) The
ψ degeneracy the arc could not resolve internally is broken from outside**: Greve requires
ψ = 0.179–0.341 cm/yr against the 2250–2300 rate criterion's independent 0.273–0.282 —
two measurements 900 years apart agreeing to ~10%, both saying shipped cell A (0.125) is
2.2× short. **Nothing was shipped, no gate moved, no cell moved, no chain started.**

---

## 1. WHAT IS NOW SETTLED, AND BY HOW MANY MODELS

| claim | models | evidence |
|---|---|---|
| total ice volume is FINE | 1 (9 configs) | 7.42 vs 7.30–7.68 m; **the problem is not how much ice there is** |
| 2100 runs FAST, and it is ours not the target's | **16** | NORCE-CISM is a TYPICAL member (0.87/0.99/1.11× the ISMIP6 median); swapping targets leaves 1.17× → 1.30× |
| the commitment law is short in SHAPE | **4** (CLIMBER-X, SICOPOLIS, Yelmo-REMBO, PISM-dEBM) | 45× at 2.0 K; 5.8–9.5× over our φ=1 ceiling at 3000; **2.1× short already at 2300** |
| the threshold sits at 1.7–2.6 K GMT | **3** | Yelmo-REMBO 1.68–1.76, PISM-dEBM 2.18–2.60, CLIMBER-X 1.44–2.24 |
| ψ ≈ 0.24–0.28 cm/yr | 2 independent horizons | Greve@3001 0.179–0.341 (median 0.242) vs the 2250–2300 rate criterion 0.273–0.282 |

**The 2.1×-short at 2300 independently reproduces §1.1's 1.93× against PROTECT's own 2300
medians.** Three ice-sheet models, one number, and 2300 is the horizon the deliverable
reports — this is not a geological-timescale curiosity.

---

## 2. THE TWO TRAPS THAT NEARLY PRODUCED WRONG HEADLINES

### 2.1 A CO₂ step is not a temperature step
CLIMBER-X's `eqco2` steps **CO₂**. At 460 ppm its global anomaly is **1.30 K at year 300**
against a 2.45 K asymptote, and keeps climbing past 10 kyr as the sheet's own albedo
disappears. Comparing our temperature-step response to it manufactured a clean-looking
5–8×. Fixed by driving our emulator with **CLIMBER-X's own `tg(t)`**, gated to reproduce
`regional_driver`'s projection branch at 0.0e+00 °C.

### 2.2 Priority 1 applies to the TARGET, not only to us
With like-for-like forcing our model still read **4.0× fast** over the first millennium —
which looked like it stacked with the ISMIP6 2100 finding. It does not. CLIMBER-X's
fastest first century is **0.117 mm/yr at 1.09 K** against an observed **0.593 mm/yr** —
**5.1× too slow**. Its early horizons are not an admissible target, and its 5.1× deficit
and our 4.0× "excess" are one discrepancy seen from two sides.

> **⚠ THE TWO FINDINGS MUST NEVER BE STACKED.** The 2100 fast bias rests on ISMIP6 alone.

**Generalise this.** Before any model's transient horizons are used as a target, gate the
model on the observed record. Greve **passes** (0.440–0.988 mm/yr over 2016–2050 brackets
the observed 0.593); CLIMBER-X **fails**. And **equilibrium ladders cannot be gated at
all** — there is no transient in them — so use ladders for **shape**, never for **rate**.

---

## 3. TWO CORRECTIONS I MADE TO MY OWN CLAIMS

1. **"CLIMBER-X is the only source for the threshold location" — WRONG.** It is in commits
   `bc86c31` and `f04f213`. `data/observations/greenland_equilibrium_bochow2023.csv` has
   been tracked since **2026-08-10** with two equilibrium ladders. Corrected in
   `notes/scoping_2026-08-23_leq_options.md` §0 and in memory `gis_commitment_3models`.
   **The docstring of `diag_gis_greve_year3000.py` still carries the wrong sentence in its
   §4 print block — fix it on the next touch.**
2. **I under-read the prior art.** Options C, D and γ were tried and killed 2026-08-10..22.
   Anything proposed must clear that history. §5 below is the do-not-re-propose list.

---

## 4. WHAT TO DO NEXT — AND THE ORDER MATTERS

1. **§4.1, the NPV/SC-GHG sensitivity to τ. STILL NOT RUN, and it now goes FIRST.** τ moves
   from 800 to ~2700 yr under §1; the discount factor at 2250 is 0.0012. **This may show
   the entire τ question is worth ~nothing to the deliverable**, which decides how much of
   the rest is worth doing. It is the cheapest item and the only one that can retire work.
2. **Re-scan onset over 1.5–3.0 K** — the ladder range — with V and τ free, scoring history
   + 2100 (ISMIP6 median) + 2300 (PROTECT + Greve) + 3000 (Greve). **Expect 2100 to move,
   and treat that as a feature**: see §5.
3. **Pin V to the ladder** (95–100% of the sheet above ~2.5 K) and let τ follow from
   ψ ≈ 0.24–0.28. Tests whether §1's two-sided determination is self-consistent.
4. **Drop CLIMBER-X as a target.** Redundant on the threshold, and the weakest-gated. Keep
   it labelled as the only source that scans stabilisation levels with a coupled climate.
5. Stage 2 only after the target set can support it (unchanged from the prior handoff).

---

## 5. THE FINDING THAT NOBODY WAS LOOKING FOR — READ THIS BEFORE TOUCHING THE ONSET

**The reservoir onset is 4.69 K GMST. Every equilibrium ladder puts the Greenland
threshold at 1.7–2.6 K. It is 2.0–2.8× too high.** Memory `gis_tap_priced_l13` records
where 4.69 came from: *"Bracket floor 4.69 K = exactly the 'don't move 2100' constraint."*
**It was chosen to protect 2100, not from evidence.**

* **The protection was protecting a defect.** 16 ISMIP6 ice-sheet models say 2100 is
  already **1.30× fast**. Holding the onset above every scenario's 2100 warming preserved
  a value we now know is wrong.
* **It is why no cool-arm failure is repairable.** The reservoir is inert below onset, so
  ssp126/ssp245 never see it — and Greve's ssp126 cell still shows a **26.1 cm** gap at
  3001 that nothing in the current structure can supply.

**Highest-value single change available, and it is a prior move, not new machinery.**

---

## 6. THE OPTION SPACE IS CLOSED TO ONE SURVIVOR

**The constraint that explains every failure:** an admissible form must let the **total
commitment grow ~40× WITHOUT the near-term flux moving.**

**DEAD — do not re-propose:** option C (ladder `L_eq` in proportional relaxation — the rate
scales with `L_eq`, hindcast RMSE 1.675); option D (throughput cap — makes `L_eq`
*algebraically* irrelevant); option 2/γ (bounded by 1/φ, φ(2300) already 0.84–0.92); every
completely-monotone family (exact bound `d ln τ_eff/d ln s < 1`, max 0.9997, vs 1.31
needed); `RAMP_W_K`; and — **killed this session** — the T-space form
`dL/dt = c(T − Θ(L))₊` with a single melt constant (`c` fitted to the arms gives a hindcast
**0.08×** observed; history wants `c` 3.6× larger, which overshoots both cool arms).

**ALIVE: the flux reservoir**, because ψ = 100·V/τ separates near-term flux from total. It
is close to the simplest object that does, which is what priority 5 asks for.

---

## 7. FILES

**New this session**, all read-only, each with its own CSV + log in `outputs/`:
`python/diag_gis_ismip6_2100_ism_spread.py`, `python/diag_gis_climberx_commitment.py`,
`python/diag_gis_greve_year3000.py`.
**Notes:** `notes/scoping_2026-08-23_leq_options.md` (the decision layer).
**Ran, not modified:** `python/diag_gis_stepback_lit_leq.py` — its result is in §6 and is
**not** written to `outputs/`; it prints only.

**Unchanged:** nothing in `julia/`, no gate changed, no cell moved, no chain started, and
`scope_gis_reservoir_offline.py` + its CSV untouched so **86/216 still reproduces**. The
D1–D5 change set (`spec_2026-08-14_next_calibration.md`) is still NOT STARTED.

---

## 8. NON-OBVIOUS STATE

* **Extracted data on disk, gitignored, re-fetchable from the DOIs in each
  `PROVENANCE.txt`:** `data/gis_post2100/climberx_10kyr/grl/` (157 MB of `eqco2`
  `V_sle`/`tg`), `data/gis_post2100/greve_chambers_2022/scalars/` (**856 KB** — extract
  only these, not the 3D fields; the archive is 4.5 GB),
  `data/gis_post2100/ismip6_scalars/CMIP5_CMIP6_Scalars_Paper/GrIS/` (1.4 MB).
* **Greve's `run_specs_headers/` is now gitignored.** Its only load-bearing content — the
  experiment → GCM/scenario map — is transcribed into `EXPS` in
  `diag_gis_greve_year3000.py`. The ISMIP6 `README.txt`, which carries the equivalent
  `expb01–b10` map, **is** tracked.
* **ISMIP6 TIME-AXIS TRAP.** All 69 GrIS scalar files carry exactly **86 annual records
  (2015–2100)**, but their `time` *attributes* disagree once decoded — AWI reads
  2016–2101, UCIJPL 2014–2099, UAF 2017–2438. Decoding mis-indexes **30 of 69** files and
  reads two models as ~0 cm. **Index positionally**, gated on `n == 86` and `sle[0] == 0`.
* **Greve's mass conversion** is `limnsw / 3.618e17 kg per m SLE` (ISMIP6 convention). Its
  `lim` is total mass and is NOT the SLE variable. Control drift over 985 yr: −0.0063 m.
* **CLIMBER-X `eqco2` is FIXED-ORBIT** — the 280 ppm control drifts 0.058 K and 0.009 m
  over 100 kyr, so it is a genuine control. The separate `ssp` group is not fixed-orbit.
* Our 2100 in `diag_gis_greve_year3000.py` differs from
  `diag_gis_ismip6_2100_ism_spread.py` by **0.91–1.82%**: posterior thinning (`DRAW_STRIDE`
  10 vs full 10k), not the extended axis. The script prints this cross-check itself.
* `python/diag_gis_greve_year3000.py` integrates on **`YEARS_EXT` = 1850–3001**, not the
  repo-wide `YEARS` = 1850–2300. Its `ext_driver` is gated to reproduce `regional_driver`
  on the overlap at 0.0e+00 °C — **keep that gate if you touch it.**

---

## 9. TRAPS ADDED THIS SESSION

* **A CO₂ step is not a temperature step** (§2.1).
* **Apply the observational gate to the TARGET before using its horizons** (§2.2); and
  **equilibrium-only sources cannot be gated at all**, so they inform shape, never rate.
* **Two findings pointing the same way are not two findings** if one is the other seen from
  the other side (§2.2).
* **Never quote `max(L_eq)` over an unbounded temperature grid** — it reports the value at
  a 200 K extrapolation. Quote it at a stated, physically relevant ΔT.
* **A ratio against a near-zero denominator is not a quantity** — CLIMBER-X's committed
  loss goes slightly negative below ~330 ppm; blank those cells rather than print them.
* **Pooling above- and below-threshold cases** averages "2× high" with "40× low" into a
  number describing neither. Split on the threshold.
* **Check the repo before scoping.** Half of what looked like a fresh option space was
  already tried, named and killed; `build_greenland_equilibrium_ladder.py`,
  `fit_gis_veq_pism.py`, `scope_greenland_commitment.py` and `diag_gis_stepback_lit_leq.py`
  all predate this session.
