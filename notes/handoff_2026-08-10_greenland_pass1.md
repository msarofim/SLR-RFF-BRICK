# Handoff 2026-08-10 — BRICK-F\* delivered; Greenland pass 1 scoped and ready to build

**Self-contained pickup:** this note + `notes/scoping_2026-08-10_greenland_options.md`
(the full scoping record, §1–20) + memory `project_brick_mengel_vnext_recalib`.
Branch `brick-mengel-vnext`, repo `SLR-RFF-BRICK`. All work committed.

---

## DECISION 1 (first thing to settle) — which of PISM / Yelmo / SICOPOLIS can we actually model, and which should go in?

### What we physically have, today

| model | data on disk | usable as an equilibrium ladder? |
|---|---|---|
| **Yelmo-REMBO** | `data/observations/raw/bochow2023/gris-rembo-*.nc` (1.3 MB, tracked) | **YES** — 15 no-overshoot runs, extracted, converged (drift 0.000 m at every rung) |
| **PISM-dEBM** | `data/observations/raw/bochow2023/pism_eq/*.nc` (48 MB, tracked; pulled from the 1.1 GB `pism_debm.zip`, which is in scratch and NOT tracked) | **YES** — 16 no-overshoot runs at 0.0–7.5 K in 0.5 K steps, extracted, max drift 0.16 m |
| **SICOPOLIS / CLIMBER-X** | **nothing** | **NO** — would need Höning et al. 2023/2024 data; availability not yet checked |

Both usable ladders are in `data/observations/greenland_equilibrium_bochow2023.csv`
(31 rows, built by `python/build_greenland_equilibrium_ladder.py` for Yelmo and
the PISM extraction alongside it). **Both are derived from raw model output, not
from any transcription** — this matters, see the retraction below.

### How different are they, really?

Committed loss, m SLE, both from raw output on a common GMT axis
(`GMT = ΔT_summer/1.19 + 0.5`, the authors' own conversion):

| GMT | PISM | Yelmo | agree? |
|---|---|---|---|
| 0.50 | 0.05 | 0.09 | yes |
| 0.92 | 0.19 | 0.16 | yes |
| 1.34 | 0.66 | 0.34 | close |
| **1.76** | **1.48** | **4.90** | **NO** |
| **2.18** | **1.64** | **6.05** | **NO** |
| 2.60 | 6.28 | 6.41 | yes |
| 3.02 | 6.79 | 6.60 | yes |
| 3.86 | 7.15 | 7.05 | yes |
| 4.70 | 7.29 | 7.30 | yes |
| 6.80 | 7.40 | 7.42 | yes |

**They agree everywhere except a window of roughly GMT 1.6–2.4 °C**, where Yelmo
has tipped and PISM has not. Outside it the two ladders sit within ~0.2 m of each
other. Yelmo's jump is between 1.68 and 1.76; PISM's is between 2.18 and 2.60,
and PISM shows an intermediate plateau at 1.48–1.64 m (20–22% of volume) across
1.76–2.18 — **an intermediate state visible in the raw data**, which is what
Bochow et al. 2023 described and what the 2026 preprint's text denies. Trust the
data here, not the preprint text.

### Recommendation for decision 1

Our scenario peaks are **SSP1-2.6 1.92 °C, SSP2-4.5 3.19 °C, SSP5-8.5 7.81 °C**.

- **For SSP2-4.5 and SSP5-8.5, one model is enough.** Both sit well above the
  reconvergence point, where PISM and Yelmo agree to ~0.2 m. Marcus's condition
  — confident in the model, numbers not dramatically different from the
  alternatives — is satisfied for these scenarios by either model.
- **For SSP1-2.6, one model is not enough.** At 1.92 °C the two ladders differ by
  4.4 m of committed loss (1.64 vs 6.05), because SSP1-2.6 peaks squarely inside
  the disagreement window. This is not a rounding difference; it is the
  difference between "Greenland is fine" and "Greenland is committed".
- **Suggested resolution:** build on **PISM as the single implemented ladder** —
  it has the finer sweep (0.5 K steps vs Yelmo's uneven grid), it is the more
  widely benchmarked model (two entries in the ISMIP6-Greenland ensemble,
  Goelzer et al. 2020; Yelmo is not in it), and its raw output shows the
  intermediate plateau that the wider literature increasingly supports (Höning
  2023/2024; Kypke et al. 2026). Then carry **Yelmo as a threshold-location
  sensitivity arm reported only for SSP1-2.6**, where it changes the answer.
  That satisfies "one model if it's a good one" without hiding the one place the
  choice matters.
- **SICOPOLIS: drop from pass 1** unless someone wants to chase the Höning data.
  Its distinctive feature (an intermediate state) is already present in PISM's
  raw output, so it adds less than it did when the preprint was the only source.

**This is decision 1 and everything downstream waits on it.**

---

## RETRACTION carried forward — do not reuse these numbers

I implemented the Bochow et al. 2026 preprint emulator (EGUsphere
doi 10.5194/egusphere-2026-614) from its Table 2 and reported per-family
projections. **Those numbers are void.** Transcribed, the Yelmo fit is
a = −1.83, c = −2.14; with both negative the cubic is strictly monotonic
(3az² + c < 0 ∀z) so it has one real root at every temperature and **no fold at
all** — which contradicts the paper's own premise. Validated against the
extracted Yelmo ladder it gives 1.22 → 4.92 m where the data give 0.09 → 6.60 m.
The PDF's mathematics layer extracted badly; the table is likely misaligned.

Void: the per-family 2100/2150/2300 table, the sampled-ensemble quantiles, and
the committed-loss table in `outputs/scope_greenland_bochow2026*.csv`.
The script `python/scope_greenland_bochow2026.py` is kept because the framework
description is right, but **its outputs must not be used until Table 2 is
re-read from a reliable rendering and the emulator reproduces the ladders.**
The ladders are the acceptance test.

Since both ladders now come from raw data, the emulator is no longer on the
critical path — a V_eq curve can be fitted directly to the PISM ladder.

---

## What was delivered before Greenland (all committed, all tested)

BRICK-F\* — MimiBRICK v2.0.0 + 3-reservoir glaciers + recalibrated Antarctic +
extended datasets, one joint 52-parameter posterior
(`data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv`).

- `julia/brickf_projection.jl` — the one tested projection kernel. **Use it; do
  not re-derive the parameter map.** Tests: `julia/test_brickf_projection.jl`.
- `julia/project_ssps_components_brickf.jl` → `outputs/ssps_components_2300_extC.csv`
- `julia/posterior_predictive_brickf.jl` → `outputs/postpred_extC_*.csv`
- `python/brickf_model_comparison.py` → FACTS / MAGICC-SLR / BRICK 2.0 arms
- `python/brickf_data.py` (+ `test_brickf_data.py`) — data assembly, no exec chain,
  byte-identical to the committed calibrator inputs
- `./run_brickf_tests.sh` — all three suites, green
- `notes/memo_2026-08-10_brickf_sharing.md` — the sharing memo, all three changes

Headlines: SSP2-4.5 total @2100 **49.5** cm, @2300 288.5. Glaciers @2100
8.5 / 10.6 / 14.7 — inside the MAGICC and FACTS range at every scenario, and the
old glacier saturation is gone.

---

## Greenland pass 1 — decided scope

Marcus's decisions, in order given:

1. **A + B in pass 1** — regional temperature driver + SMB/dynamics two-channel split.
2. **Driver zone: southern Greenland (59–70 °N), annual, land-masked**, sampled
   amplification ≈ N(2.9, 0.2). Whole-ice-sheet annual as the pre-registered
   sensitivity arm. **Not JJA** — worse on both confidence and relevance in
   anomaly space. Evidence in scoping §9.
3. **C and D also pursued** (the 2300 response matters), scoped in §13/§16.
4. **ISMIP6 evaluation-only, permanently** — it is a transient intercomparison of
   the same quantity we predict, so fitting to it would make BRICK-F\*'s Greenland
   a second-hand FACTS `FittedISMIP` and destroy the comparison's independence.
   The GlacierMIP3-equivalent for Greenland is the **equilibrium ladder**, which
   does belong in the likelihood. Reasoning in §14.
5. **Sample across model families rather than picking one** — now refined by
   decision 1 above, since only two families are actually available.

### Why Greenland needs work (all verified)

- Scenario response is a third of everyone else's: **+2.2 cm** SSP1-2.6→5-8.5 at
  2100, against +6.3 to +7.3 in MAGICC and every FACTS module.
- Hindcast misses a contiguous **1942–1982** window by 0.5–0.7 cm — the only such
  failure in the fit.
- Diagnosed cause: **the transient, not the equilibrium.** The committed-loss
  difference across scenarios is 44 cm; only ~6% is realised by 2100 because the
  e-folding time is 836–1218 yr. Dead ends measured and excluded: the V/V₀ damping
  (+2.2 → +2.2 cm) and doubling the equilibrium sensitivity (+2.2 → +3.7).
- The regional driver lifts the hindcast melt-rate correlation **0.21 → 0.77**.

### Data in hand

| what | where | status |
|---|---|---|
| SMB/discharge partition | `data/observations/greenland_partition_mouginot2019.csv` | **ready** — closure MB = SMB − D exact to 0.000 Gt/yr; 74% of the extra loss surface, 26% dynamic; 1970s decade mean +46.9 Gt/yr (the ice sheet was *gaining*) |
| equilibrium ladders | `data/observations/greenland_equilibrium_bochow2023.csv` | **ready** — PISM 16 rungs + Yelmo 15 rungs |
| regional temperature | `python/scope_greenland_zones.py` builds them from the three gridded products already on disk | ready to build |
| Mankoff 2021 | not needed as a partition | **excluded** — its pre-1986 discharge is a lagged fit to runoff, so its channels are not independent. Usable as a total only |

---

## Next actions, in order

1. **Settle decision 1** (above).
2. **Build the driver**: southern-Greenland annual series from HadCRUT5 /
   Berkeley Earth / GISTEMP with the anchor-preserving splice. Reuse the glacier
   driver machinery in `python/brickf_data.py`.
3. **Fit V_eq directly to the chosen ladder** — a saturating or threshold form
   fitted to PISM's 16 rungs. No dependence on the preprint.
4. **Offline cell**: fit stock / A / B / A+B+C against the historical target plus
   the Mouginot partition, with **pre-registered gates** (modern rate,
   mid-century shape, the 1942–1982 window), reporting ISMIP6 as
   evaluation-only. Pre-register the separability question: do the fast fraction
   and fast timescale identify jointly, or ride a ridge? If a ridge, sample the
   identified combination, as the Antarctic runoff line does with (T_on, c).
5. **Surgery + port validation** at 1e-9 against the offline reference, the way
   `julia/validate_glaciers_nu3.jl` does.
6. **Joint recalibration** of the whole model, then re-run the existing
   projection / comparison / memo pipeline, which is generic.

## Traps and non-obvious state

- **Validate before reporting.** The one thing that went wrong in this session
  was reporting emulator numbers before checking them against ground truth that
  was already on disk. Every new Greenland number should be checked against the
  ladders and the Mouginot partition first.
- The Mouginot spreadsheet repeats the **years** for the error block in columns
  69–128 alongside values in 2–61; a positional read silently mixes them.
- Bochow's `f_conv` is **regional summer** warming, not GMT. Convert with
  `GMT = f_conv/1.19 + 0.5`.
- `pism_debm.zip` (1.1 GB) is in the session scratchpad, not tracked. Only the 16
  no-overshoot runs (48 MB) were copied into the repo.
- Höning's irreversibility criterion is a **state** condition (>0.4 m lost from
  the south blocks regrowth), which suits the cubic's hysteresis better than a
  temperature rule.
- **Kypke et al. 2026 caveat for the pulse work**: post-threshold collapse timing
  is chaotic over 10⁴–10⁵ yr, so a BRICK-F\* SLR pulse response computed above the
  threshold is not meaningfully predictable in timing. State this for SC-CO₂ use
  above ~+2 °C.
- Greenland remains the only stock ice module; thermal expansion and land-water
  storage are also stock but fit well and were not revisited.
