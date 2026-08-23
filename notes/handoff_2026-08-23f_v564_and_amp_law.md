# Handoff — V ships at 5.64 m, and the 2100 fast bias is the AMPLIFICATION LAW, not the ice response

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, through `ce33b6b`.
Written 2026-08-23, to be picked up cold.

**Supersedes** `handoff_2026-08-23e_cell_shipped_rate_fail.md` for its §1 (the open V
decision — now made) and §6 (the open-work list — now re-ranked). Its §3 (the test
rewrite) and §7 (non-obvious state) are **unchanged and still load-bearing**.

---

## 0. THE ONE-PARAGRAPH VERSION

`GIS_TAP_CELL` ships at **V = 5.64 m, τ = 800 yr, onset 4.69 K, 2-stage cascade,
whole-sheet**. V moved from 6.00 because the 2250–2300 melt-rate criterion failed
there; 5.64 is simultaneously the **rate ceiling** and the **Greve year-3001 optimum**
— two independent criteria 700 years apart agreeing to within 1% — and the minimum of
the weighted score. It costs 2.6% of the 2300 level. Separately, the **2100 fast bias
has been split for the first time and it is the DRIVER, not the response**: driven by
each GCM's own Greenland temperature our ice lands ON the ISMIP6 median (0.99×);
driven through our amplification law it over-shoots 1.31×. Because `regional_driver`
splices *observed* regional T over the entire observational record, **the amp law is
exactly hindcast-inert and a correction is prior-propagatable, not a refit.** That is
now the highest-value open item in Greenland — and Greenland itself is no longer where
the leverage is.

---

## 1. THE SHIPPED CELL

| | value |
|---|---|
| stages | 2 (cascade) |
| **V** | **5.64 m** |
| τ | 800 yr |
| onset | 4.69 K GMT |
| home | whole sheet |
| ramp width | 1.0 K |

**Why 5.64.** On a V ladder at fixed (onset, τ, stages):

| V | 2100/ISMIP6 | 2300/Greve | 3001/Greve | w(6:3:1) | ssp585@2300 |
|---|---|---|---|---|---|
| 5.20 | 1.361 | 0.757 | 0.921 | 0.3268 | 91.7 |
| 5.40 | 1.363 | 0.767 | 0.953 | 0.3260 | 93.3 |
| **5.64** | 1.365 | 0.780 | **0.990** | **0.3258** ← min | 95.3 |
| 5.80 | 1.367 | 0.788 | 1.015 | 0.3260 | 96.6 |
| 6.00 | 1.369 | 0.798 | 1.046 | 0.3267 | 98.2 |

Minimum under the 2100 > 2300 > 3001 weighting the evidence supports; within 0.1% of
the minimum under every other weight set; Greve@3001 at 0.990×; and **exactly the
largest V clearing the 2250–2300 rate band when solved in the wired component**
(5.66 offline, 5.64 wired — a 0.4% port). Leave-one-GCM-out on the rate band **0/5 →
4/5**.

⚠ **IT IS ON THE CEILING, NOT INSIDE IT.** V was solved *as* the clearing value, so the
verdict turns on the third significant figure: **41.4 offline, 41.5 wired at 300
draws, against a 41.5 top**. The diagnostic prints this rather than absorbing it into a
band-edge tolerance, because inventing one there would be choosing the verdict.

**What it costs:** Greenland ssp585@2300 98.7 → **95.7 cm**, 0.999× → **0.969×** the
matched p50. 2150 moves 2.44 cm (21.1% of the sampled spread). **2100, both cool
scenarios and the entire 1850–2025 hindcast are unchanged at 0.000e+00**, measured on
the wired model.

**Deliverable:** `outputs/ssps_components_2300_L14_tap4p69K_V5p64m_tau800_n2_ws.csv`
(+ `_shapefullcurve`). V=6.00 quarantined at
`outputs/quarantine/20260823_v6p0_cell/` — a **refinement within one family**, not a
refutation like the first-order cell before it.

---

## 2. THE 2100 FAST BIAS IS THE AMPLIFICATION LAW — the highest-value open item

`python/diag_gis_2100_bias_decomp.py`.

**The paradox it resolves.** We match the observed level (fitted), match the rate over
four free windows (0.95–1.07×), and **under-run the acceleration at 0.63×**. A model
that under-runs curvature while matching the rate should arrive **low** at 2100, not
1.32× high.

**The test**, as 2015→2100 *change* so no level offset can produce any of it:

| route | median vs ISMIP6 |
|---|---|
| GMST route (production, `regional_driver` = amp·S·GMST) | **1.31×** |
| DIRECT route (the GCM's OWN Greenland anomaly spliced in) | **0.99×** |

**The ice response is exonerated. The defect is the driver.** Our **effective** amp
(`amp × S`, derived from the driver — *not* the raw `gis_amp` posterior median 1.91,
which is not what gets applied) is **1.58–1.63** against these models' own south-zone
**1.08–1.39**: a 1.40× over-drive against a 1.32× SLR bias, i.e. near-linear response.

**AND IT IS PROJECTION-SIDE.** `regional_driver` (`scope_gis_2300_relaxation.py:114`)
returns *observed* southern-Greenland T for every year `YEARS <= last observed year`
and only splices `amp·S·GMST` after it. **The amp law has exactly zero effect on the
hindcast**, so a correction is prior-propagated like the reservoir — not a refit. That
is the difference between a week's work and a recalibration.

⚠ **n = 5 cells**, one member each, DIRECT-route spread **0.65–1.33×**. Guidance about
a direction, **not a correction factor to apply**.

⚠ **NOT a contradiction of "the GCM's own regional T makes it worse."** That was
measured at **2300 on the r2300 arm**, where our commitment is far too small and every
route under-predicts. At **2100** the direct route is essentially exact. Same
comparison, different horizon, opposite sign — **state the horizon whenever quoting
either.**

**What a fix would look like, unscoped:** the amp law applies a north-sized
amplification to a south-zone driver. Re-anchoring it to the measured south-zone value
is the obvious move, but `c1` was calibrated against the *observed* south driver and
may absorb part of the level — so the first task is to check whether re-anchoring amp
alone moves 2300 and the cool arms, since those are currently in reasonable shape.

---

## 3. THE SEPARATION TARGET WAS AN ENDPOINT-DIVISION ARTEFACT

`python/diag_gis_separation_target.py`. Both numbers this repo has quoted for months —
**7.9–31.9×** (literature) and **2.00–13.68×** (matched) for ssp585/ssp245 — are the
2300 bands' **endpoints divided**. That is the outer envelope under an independence
assumption the ensemble does not satisfy: every anchor past 2100 is NORCE-CISM.

**The like-for-like target is the matched p50 ratio**, PCHIP'd to our own forcing
integral: **ssp585/ssp245 = 6.40×, ssp585/ssp126 = 8.87×**.

| arm | 585/245 | 585/126 |
|---|---|---|
| original BRICK | 1.90× (0.30) | 2.56× (0.29) |
| Ladrillo untapped | 2.72× (0.42) | 4.99× (0.56) |
| **V=5.64 (shipped)** | 5.22× (0.82) | **9.58× (1.08)** |

**Per-scenario: ssp585 is 0.97× the matched p50, ssp126 is 0.90× and ssp245 1.19× —
the COOL arms carry the residual separation error, and the reservoir is inert there by
construction.** Any further separation work is a cool-arm problem, not a cell problem.

---

## 4. HOW IT LOOKS AGAINST ORIGINAL BRICK

`julia/diag_gis_cell_vs_priority_ladder.jl` — four arms through the same setup,
forcing, baseline and obs file; only the Greenland module differs (`:stock` SIMPLE on
the `extC` posterior = original BRICK, calibrated in our own pipeline).

**Ladrillo wins**: historical shape (1900–1950 0.73× → 1.00×, 1950–1990 1.49× →
0.95×), level (39/126 → **105/126** years inside the obs band; worst miss 0.161 →
0.077 cm), acceleration (0.32× → 0.63×), 2300 commitment, and separation (2.56× →
9.58× on 585/126 against an 8.87× target).

**Ladrillo does NOT win**: the 1995–2024 rate itself (BRICK 0.95× vs our 1.06× —
marginal), and **priority 3**, where BRICK's stock module is **inside** the melt-rate
band at 14.0 cm/century while untapped Ladrillo is 4.5× too slow and the tapped cell
sits on the ceiling.

⚠ The obs band's half-width collapses **65×** across the record (1.068 → 0.016 cm), so
"years in band" is dominated by the satellite era. The absolute miss is printed beside
it for that reason.

---

## 5. WHAT IS OPEN, RE-RANKED

1. **THE AMP LAW** (§2). Highest value, hindcast-inert, and now diagnosed rather than
   suspected.
2. **ANTARCTICA, and this is the real headline.** At 2300 on ssp585, AIS is **281.7 cm
   = 54.5% of the total with a p05–p95 of 252.3 cm**; Greenland is 98.7 → 95.7 cm =
   19.1% with a spread of 26.9 cm. At SSP2-4.5 the AIS band is **[15.4, 296.1] cm — a
   19× range**, wider than the whole total's spread. AIS also still carries the 20
   unconverged marginals (`ais_iceflow0` R̂ 2.449) that make L14 **projections-only,
   not parameter-level inference**. **Greenland is now the smallest-uncertainty ice
   component in the model. The leverage is AIS.**
3. **The cool arms carry the residual separation error** (§3). ssp126 0.90×, ssp245
   1.19×; the reservoir cannot reach them.
4. **The melt-rate criterion has no interior solution.** Untapped 3.1 (4.5× slow),
   shipped 41.5 (at the ceiling). The model goes floor-to-ceiling with nothing
   comfortable between. Accepting 5.64 means accepting a boundary cell — fine as
   guidance (5 GCM clusters), but it is not margin.
5. **The `--tap-set` cell-choice envelope has no cascade version.** The first-order
   band was **1.180 m at Greenland 2300 — 4.4× the sampled p05–p95** and the larger of
   the two uncertainties. Currently unquantified. Never quote the quarantined one.
6. **The x2300 arm remains unreachable** — 58.3 cm against a 122.8–189.0 band,
   band-independent. Reported, not a blocker.
7. **The moderate-scenario SC-GHG commitment term is exactly zero** at onset 4.69 —
   a decision on evidence, but a second arm is needed if the CH₄-vs-CO₂ SLR paper
   wants it.
8. **Housekeeping:** `build_protect_r2300_forcing.py` still carries `ONSET_K = 6.5`
   labelled "GIS_TAP_CELL.onset_K". Output unaffected; comment stale.

---

## 6. FILES

**New this session:** `python/diag_gis_2100_bias_decomp.py`,
`python/diag_gis_separation_target.py`,
`julia/diag_gis_cell_vs_priority_ladder.jl`, and their CSVs/logs.
**Modified:** `julia/greenland_3basin_component.jl` (the cell),
`julia/project_ssps_components_ladrillo.jl`, `julia/test_gis_tap_wiring.jl`,
`python/diag_gis_cascade_rate_crit.py`, `python/scope_gis_tap_shape.py`,
`python/scope_gis_onset_rescan.py` (`--v-extra=`, and the psi guard below),
`CHANGELOG.md`.
**Quarantined:** `outputs/quarantine/20260823_v6p0_cell/`.

**A BUG FIXED IN PASSING:** `scope_gis_onset_rescan.py` still emitted
`psi = 100·V/τ` at `--stages=2` and tested it against the Greve range. That formula is
first-order and undefined on a cascade — the cell read 0.750 against a range topping
out at 0.341, a "2.2× violation" that is pure artefact. Now NaN/None on the cascade arm
with the psi section skipped. `--stages=1` verified **byte-identical**, stdout and CSV.

Commits `7b2540a` → `ce33b6b`. Memories: `gis_2100_bias_is_amp_law`,
`endpoint_division_is_not_a_ratio_band`; `gis_cascade_shipped_rate_fail` updated to the
shipped V.
