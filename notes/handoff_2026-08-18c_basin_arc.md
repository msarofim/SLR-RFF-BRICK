# Handoff — the rate-law dead end, the basin mock that PASSES, and the tier-1/2 buy-in

**Start-here document for the next session.** Repo `SLR-RFF-BRICK`, branch
**`ladrillo-dev`**, HEAD `8d52288`, **pushed and in sync with origin**.
Predecessor: `notes/handoff_2026-08-18b_committed_loss_amp_and_the_leq_dead_end.md`.

**Bottom line: the predecessor's §5 item 1 (the convex rate law) was tested and
closed NEGATIVE — pre-registered P1 and P2 both failed, for a reason more
instructive than the falsifier. Marcus then asked whether basins could help the
way GSIC's three groups did; the answer is measured YES: a multi-basin mock is
the FIRST structure to clear the whole 2300 scorecard offline (59/720 cells,
ratio 10–18× vs literature 7.9–31.9×). Marcus bought tiers 1 and 2: the passing
region SURVIVES the Mouginot inventory + onset-bracket checks (28/59 strict),
and the per-zone drivers + per-zone CMIP6 amp laws are BUILT and guarded.
Nothing is blocking. The next step is the ZONE-SPACE WIRING (§6), then the
pricing decision on a calibrator restructure — with ship-with-caveat still a
legitimate fallback throughout.**

---

## 0. WHAT CHANGED IN ONE TABLE

| | before | after |
|---|---|---|
| §5 item 1, convex fast-channel rate | the recommended test | **DEAD** — ratio peaks 4.71× at (k=14, p=2), then falls |
| candidate structures for ssp585@2300 | all measured dead | **basin mock PASSES the whole scorecard** — 59/720 |
| basin volumes/onsets vs literature | unchecked | **28/59 survive strict Mouginot; onsets all inside (4.69, 7.81] K** |
| `t_gis_zones.csv` | south, all | + **central (70–77 N), north (77–84 N)**; south/all guard-proved unchanged |
| per-zone CMIP6 amp law | south only | + central, north — **north is FLAT in warming level** |
| the 40-model CMIP6 panel | south/all columns | + per-zone columns; panel PINNED; originals reproduced to 0.0 |

Commits this session: `cb136af` (rate-power scan), `5620e4a` (basin mock),
`dce0283` (tier-1 lit check), `d59ce12` (tier-2a drivers), `8d52288` (tier-2b
amp shapes). All pushed.

---

## 1. THE RATE-POWER SCAN — dead end #2, and WHY it dies

`python/scope_gis_rate_power_vs_literature.py` + `plot_gis_rate_power_scan.py`
(→ `figures/gis_rate_power_scan_L12.png`). Exactly the predecessor's §5 spec:
2-D (k, p) scan of `r_f = alpha_f·Tbar·(max(T,0)/Tbar)^p + beta_f` on the
FAST channel only, anchored at Tbar = 1.9631 K, slow channel linear, hindcast
re-bisected per cell, reproduction-gated against the ridge CSV at 1e-9.

- **P1 (ratio monotone in p): FAIL at every k** — the ratio RISES THEN FALLS,
  peaking at p ≈ 1.5–2.5 (later for larger k).
- **P2 (some p in 1.5–3 reaches 7.9–31.9×): FAIL** — the whole surface peaks
  at **4.71× at (k = 14, p = 2)**.
- P3 (hindcast satisfiable): PASS. **The D2 falsifier did NOT fire** — `s`
  moves DOWN with p (0.6–0.8×), not up by orders of magnitude.

**The instructive failure:** differential equilibration DID appear (φ@2300 at
the peak: 0.27 ssp245 vs 0.54 ssp585, against ~0.99/0.99 shipped) but
self-limits, because both scenarios' 2300 REGIONAL drivers — **4.92 K (ssp245)
and 12.59 K (ssp585)** — sit far above the ~2 K anchor. Any p fast enough to
close ssp585 on its commitment also accelerates ssp245; past the sweet spot the
ratio falls back toward the clip-compressed Leq ratio. Consistency receipt at
the peak cell: commitment ratio 7.42/2.87 = 2.59 × φ ratio 2.04 ≈ 4.71 ✓.
Near-peak cells also break everything else (SSP1-2.6 2.2× over band, SSP2-4.5
3.9×, G4 2.8× of accepted). **(k=1, p=1) — the shipped model — is the best
all-round cell on the surface**, mirroring the 1-D ridge. The nesting gap at
p=1 (the `max(T,0)` floor in negative-driver years) is 3.6e-3 m — measured,
not assumed.

**⇒ The separation needs a threshold BETWEEN the two scenarios' 2300 driver
temperatures. No smooth law anchored at the calibration point can supply it.**

---

## 2. THE BASIN MOCK — the first structure that clears everything

`python/scope_gis_basin_mock_vs_literature.py` + `plot_gis_basin_mock.py`
(→ `figures/gis_basin_mock_L12.png`). Marcus's question, and the glaciers_nu3
precedent (R19/SLOWP/FAST cured exactly this disease for GSIC — one law's
railed fit compressed the scenario spread; per-block onsets restored it).

    L_total = A+B(shipped, k=1, s re-bisected)  +  sum_b S_b
    S_eq,b(G) = V_b · clip((G − T_on_b)/1K, 0, 1),   G = GMST rel 1850-1900
    S_b[i]    = S_b[i-1] + (S_eq,b(G[i-1]) − S_b[i-1]) / tau_b

Two dormant basins: MID (~NW) and HIGH (~NE+NO); `mid_share = 0` = single
dormant basin (a structural variant). Onsets in GMT space (per-zone drivers
did not exist yet; a zone driver RESCALES onsets, it does not change
feasibility). 720-cell grid; dormant loss is linear in V so unit responses
factor out; gated vs the ridge k=1 row at 6e-17.

- **F1: 59/720 cells pass** all three 2300 bands + G4 within 15% of shipped +
  inventory. Ratio **10.1–17.6×** (lit 7.9–31.9×).
- **F2: a plateau, not a knife-edge** — every tau (50–400 yr), every V
  (1.5–4.5 m), onsets 5–7 K, with and without an active mid basin (41/18).
- **F3: falsifier clean** — zero passers need an onset below ssp245's 2300
  GMT. The binding constraint is 2100-keeping (162/720), and it selects the
  physical regime: onsets ≥ 5 K cross under ssp585 only in **2107 (5 K) /
  2135 (6 K) / 2179 (7 K)**, so dormant basins are inert at 2100 BY
  CONSTRUCTION and ssp126/245 stay bit-identical to shipped.

Exemplar (widest 585 margin): onsets 5/6 K, V = 2.5 m (70% high), tau = 100 →
0.092 / 0.172 / **2.433** m at 2300, G4 1.000×, ratio 14.2×.

**What the mock is NOT: a calibration.** It shows the structure CAN represent
the separation (both single-law families provably cannot); it does not show
the onsets/volumes are right — that was tier 1's job.

> Display trap: in the passing-region table, `t_on_mid = 2.5` rows are
> `share = 0` placeholders (the dedupe keeps the first inert value). No passer
> has an ACTIVE mid basin below 4 K — do not misread that column.

---

## 3. TIER 1 — the literature checks (28/59 SURVIVE STRICT)

`python/diag_gis_basin_lit_check.py` → `outputs/diag_gis_basin_lit_check.csv`.

**Inventory (Mouginot et al. 2019, PNAS 116:9239, doi 10.1073/pnas.1904242116,
per-region SLE from the region paragraphs):** SW 74, CW 134, NW 127, NO 93,
NE 180, CE 72, SE 55 cm (sum 735 ≈ V0 742). The paper's own conclusion is the
premise: **NO+NE hold "the largest potential SLE (273 cm) in Greenland"**, low
present discharge (25.9 / 39.5 Gt/yr in 2018) because speeds are low while ice
shelves buttress them. Gate: high ≤ 2.73 m, mid ≤ 1.27 m (NW), single-basin
≤ 2.73 strict / ≤ 4.00 loose → **28 strict / 33 loose of 59**. The v_tot = 4.5
cells die here.

**Dormancy today (Dataset S2, on disk at
`~/Documents/2026/ClaudeDocs/Papers/Mouginot/pnas.1904242116.sd02.xlsx`,
parsed per region with build_greenland_partition's own functions, parse-GATED
against the paper's printed cumulative losses):** **NO+NE = 37% of the ice
sheet's SLE but 20% of the 1972–2018 loss.** The premise is in the
observational record.

**Onset window (TC 19:6887's two arms — numbers already vetted in
`diag_gis_committed_loss.py`):** stabilised year-2100 ssp585 climate (4.69 K
held) realises 0.282–1.230 m by 2300; continued warming to 7.81 K realises
1.732–3.127 m ⇒ **the marginal volume tap activates in (4.69, 7.81] K GMT**.
ssp245's stabilised band excludes large taps below 3.15 K. **All 59 passing
onsets sit inside the bracket.** Corroboration: Aschwanden et al. 2019
(Sci. Adv. 5:eaav9396, PMC6584365 — NOT in the local Papers folder): RCP8.5
2300 = 94–374 cm (16–84%), NW outlets land-terminating by 2300, discharge
still important into the 23rd century.

**Honesty items, stated in the output, do not launder them away:**
1. **tau has NO independent published gate** — it is constrained jointly with
   onset by the scorecard itself.
2. **NE first-response has already begun** (Zachariae shelf loss, ~1.3 K GMT)
   at Gt/yr scale. The mock's onset is the **VOLUME-TAP onset** (margin
   retreat into the deep basins), which is what the stabilised-arm bracket
   measures — keep the two concepts separate in any write-up.
3. Neither TC 19:6887 nor Aschwanden's main text carries per-sector timing at
   the resolution we would like; the bracket is arm-differencing, not a
   published per-basin activation temperature.

---

## 4. TIER 2a — per-zone drivers (BUILT, GUARD-PROVED)

`build_t_gis.py` change: `DIAG_ZONES` **central (70–77 N)** and **north
(77–84 N)** — always computed for the confidence table — are now WRITTEN to
`t_gis_zones.csv` and `t_gis_zones_allproducts.csv` (`DRIVER_ZONES`).

- **The driver guard** (new, permanent): before overwriting, the rebuilt
  south/all columns must reproduce the existing file to 1e-9, else abort —
  a raw-product drift can no longer move the CALIBRATION driver as a rebuild
  side effect. **PASSED this build.** Corollary: the untracked raw `.nc`
  files under `data/observations/raw/` are now load-bearing for the guard —
  if someone re-downloads them and the products were updated, the guard FIRES
  and the rebuild must be a deliberate act.
- Julia consumers (`ladrillo_projection.jl`, `calibrate_mcmc_ext.jl`) read by
  **column name** — verified unaffected.
- **Per-zone 2015–2024 anchors** (the per-zone TBAR analogs the wiring needs):
  south **1.9631** (= the known TBAR, cross-validating the build), central
  **2.7667**, **north 3.2714 K**.
- Observed per-zone amp priors already existed in `outputs/gis_amp_prior.csv`:
  north full-window **N(2.83, 0.92)** (product range 1.84–4.06 — wide;
  GISTEMP's 1200 km smoothing is the high outlier), central **N(2.36, 0.53)**.

---

## 5. TIER 2b — per-zone CMIP6 amp shapes (BUILT; NORTH IS FLAT)

`reduce_cmip6_tas_gis.py`: emits `tas_gis_central`/`tas_gis_north`;
**panel PINNED to the shipped 40 models** (`EXISTING_ONLY` — a drifted catalog
cannot swap the ensemble); resume-by-columns (skip only files carrying all
expected columns). The re-reduction reproduced **every original column to 0.0
across all 40 files** (the GCS zarr store is static).

`diag_gis_amp_cmip6.py`: gains `--zone` (default south). South keeps every
canonical path and **re-verified byte-identical** (only the provenance commit
hash moved in `gis_amp_shape_meta.csv`); other zones write `_<zone>`-suffixed
outputs. Observed comparison values now come from `gis_amp_prior.csv` per
zone, with the hardcoded south numbers kept as asserted receipts.

**Results** (`outputs/gis_amp_shape_{central,north}.csv` + meta + fullcurve
arms + summaries + figures):

- **north: FLAT** — secant slope **−0.0195/K [−0.0390, +0.0069]**, CI includes
  zero (slope estimator agrees). ⇒ **The high basin's amp law is effectively
  the CONSTANT observed amplification** — the simplest possible wiring.
- **central: DECLINING** — **−0.0307/K [−0.0631, −0.0010]**, CI excludes zero;
  same character as the south's known decline.

> Naming quirk to not trip on: the shape metas are
> `gis_amp_shape_meta_<zone>.csv` (from `_suffixed` on the canonical path) but
> the fullcurve metas are `gis_amp_shape_fullcurve_<zone>_meta.csv` (built
> from the already-suffixed stem). Both patterns are committed.

---

## 6. WHAT'S NEXT — THE WIRING, then the pricing decision

Not started; nothing here is committed to. **The methodological choices below
go to Marcus before implementation** (per the standing rule):

1. **Zone-space mock.** Re-express the dormant basins on their own zone
   drivers: parameterize the `regional_driver` splice by zone column with the
   per-zone amp × per-zone S(dT) (north S ≈ 1, so north driver ≈ obs north
   series + 2.83 × GMST splice), then re-grid onsets in ZONE-driver units and
   re-run the mock scorecard. Rough translation: north onsets ≈ 2.8 × [5–7 K]
   ≈ **14–19 K north-zone anomaly** rel 1850–1900, against 3.27 K observed
   2015–2024. Expectation: the pass region maps over monotonically and
   ssp126/245/G4 stay untouched by construction; if it does NOT, that is a
   finding about the zone splice, not a bug to hide.
2. **Choices needing Marcus:** which driver carries the MID basin (the central
   zone is ~CW/CE/NW latitudes, not NW specifically); amp window per zone
   (full vs modern — the north product spread is 2.2×); soft-ramp width W
   (fixed 1 K so far); whether dormant basins enter the CALIBRATOR at all or
   stay projection-side only (the hindcast cannot see them — the glacier
   precedent argues: pin structure offline, sample few).
3. **Only after the zone-space mock clears** does pricing the calibrator
   restructure make sense. **Option (c) — ship ssp585/2300 with the 3.8–6.9×
   shortfall as a stated caveat — remains legitimate at every stage**; the
   2100 deliverable is unaffected throughout.

---

## 7. THINGS THAT DID NOT SURVIVE / correction ledger

1. First figure draft said the basin-mock region panel counted "of 52 each" —
   wrong for the 6/7 K columns (64 combos); fixed to a range before commit.
2. First lit-check print said NO+NE = "0% of the ice sheet" — a m-vs-cm mixup
   in the percentage only (the gates were correct); fixed before commit.
3. The tier-1 web hunt: PMC6584623 is NOT Aschwanden (it is a groundwater
   paper); the correct ID is **PMC6584365**. science.org 403s; PMC serves it.
4. Predecessor §7 items still parked: the L11-vintage memo figures at L12
   (needs a Julia run; only if fig1/2/3 are to be shown) and the `d2_basis`
   one-liner (now three vintages deferred).

---

## 8. NON-OBVIOUS STATE

- **L12 remains canonical and untouched** — everything this session is
  offline post-processing or new data infrastructure; no chain was run, no
  posterior moved, `LADRILLO_POSTERIOR_CSV` unchanged.
- The two inherited modified-uncommitted files
  (`figures/diag_gis_regional_driver.png`, `outputs/mcmc/overdispersed_starts.csv`)
  are STILL inherited from the L12 session and still untouched — third handoff
  carrying them; either commit or discard them deliberately next session.
- Untracked by convention: `outputs/log_*.txt` (this session added
  `log_scope_gis_rate_power`, `log_scope_gis_basin_mock`,
  `log_diag_gis_basin_lit_check`, `log_build_t_gis_zones`,
  `log_reduce_cmip6_zones`, `log_amp_south_reverify`, `log_amp_central`,
  `log_amp_north`), plus the raw obs `.nc` files (now guard-load-bearing, §4).
- `~/Documents/2026/ClaudeDocs/Papers/Mouginot/` has the paper + SI + sd01 +
  sd02; **Aschwanden 2019 and TC 19:6887 are NOT local** — ask Marcus to drop
  PDFs there if deep-reading is needed (the PMC/Copernicus fetches covered
  this session's needs).
- macOS has no `timeout`; pin `OPENBLAS_NUM_THREADS=1` for anything parallel.
- The CMIP6 re-reduction streams from the anonymous GCS zarr catalog
  (~40 s/model); it is resumable and the panel is pinned, so a re-run is safe.

## 9. FILES

**Created:** `python/scope_gis_rate_power_vs_literature.py`,
`python/plot_gis_rate_power_scan.py`, `python/scope_gis_basin_mock_vs_literature.py`,
`python/plot_gis_basin_mock.py`, `python/diag_gis_basin_lit_check.py`.

**Modified:** `python/build_t_gis.py` (driver zones + guard),
`python/reduce_cmip6_tas_gis.py` (per-zone columns, panel pin, resume-by-columns),
`python/diag_gis_amp_cmip6.py` (`--zone`), `CHANGELOG.md` (entries f/g/h).

**Key outputs:** `outputs/scope_gis_rate_power_vs_literature.csv`,
`outputs/scope_gis_basin_mock_vs_literature.csv`,
`outputs/diag_gis_basin_lit_check.csv`, `data/observations/t_gis_zones.csv`
(4 zones), `outputs/gis_amp_shape_{central,north}.csv`, the 40 re-reduced
`data/cmip6_gis/tas_series_gis_*.csv`, figures
`gis_rate_power_scan_L12.png`, `gis_basin_mock_L12.png`.

**Memory touched:** `ladrillo_leq_ridge_ceiling` (rate-power dead end; basin
mock; tiers 1+2 landed), `INDEX_slr.md` (arc line updated twice).
