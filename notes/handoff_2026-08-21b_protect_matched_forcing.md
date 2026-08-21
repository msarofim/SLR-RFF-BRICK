# Handoff — the PROTECT comparison was never at matched forcing, and the tap is too EARLY

**Start-here for the tap.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`.
Supersedes the *reading* in `handoff_2026-08-21_protect_greenland.md` (its data
work stands; its conclusion does not). Commits `2c1687b`, `860742d`, `07b0883`,
`c0ce0ee`.

---

## 0. THE HEADLINE

The prior handoff's step 5.1 was "check the x2300 GMST path against ours — cheap,
and it gates everything below." It gated everything below. **The paths do not
match**, and once they do, the conclusion inverts: the shipped cell is not too
LOW at 2150, it is **3.5× too HIGH**.

| 11-yr GSAT, °C vs 1850-1900 | 2100 | 2150 | 2300 |
|---|---|---|---|
| ours (`fair_mean_gmst_ssp585`) | 4.70 | 6.40 | 7.78 |
| **PROTECT x2300 (12 IPSL : 6 CESM2-WACCM)** | **6.61** | **9.86** | **13.64** |

Ours crosses the 6.5 K onset in **2154**. Theirs crosses it in **2097-2101**.

| Greenland, cm, ALL under the PROTECT forcing | 2100 | 2150 | 2300 |
|---|---|---|---|
| PROTECT x2300 p50 (on our basis) | 12.2 | 46.5 | 234.4 |
| ours, tap OFF | 19.9 | **45.2** | 90.0 |
| ours, shipped cell | 19.9 | **161.3** | 286.0 |

**NOT ACTED ON.** No gate changed, no cell moved, admissible set still all 25.

---

## 1. WHERE THE FORCING CAME FROM

`outputs/cmip6_ssp585ext_gsat.csv`, from `python/reduce_cmip6_gsat_ssp585ext.py`.

* The x2300 arm is forced by **exactly two GCMs**, 12 IPSL-CM6A-LR : 6
  CESM2-WACCM (`outputs/protect_greenland_gis_runs.csv`; weights recomputed, never
  hardcoded).
* **Neither the PROTECT scalars nor `info_p11` carry any climate variable.** The
  NetCDFs are `ivol`/`ivaf`/`lim`/`slc`/`sle` only.
* **The Pangeo/Google CMIP6 zarr mirror truncates `ssp585` at 2100** for both
  models — every member, 1032 monthly steps, 2015-01 to 2100-12. This is a trap
  worth remembering: the mirror is the repo's default CMIP6 route and it silently
  has no post-2100 extension. 2101-2300 came from **ESGF**
  (`scripts/fetch_cmip6_ssp585ext.sh`, ~400 MB, gitignored, md5-pinned).
* 1850-2100 is the repo's existing `data/cmip6_gis/tas_series_gis_<model>.csv`,
  same member, same cos(lat) + month-length weighting, so the splice is not a
  method change disguised as a signal. Overlap is asserted empty.

---

## 2. THE DECOMPOSITION — RUN `--untapped` BEFORE READING ANY RATIO

`julia/diag_protect_forcing_matched.jl`. **GIS only**: OHC stays on our ssp585,
so `te` and `total` from that driver are meaningless and are not written.

The `ours` arm reproduces the shipped run exactly (13.9 / 28.2 / 230.3 cm), so
the control is the run it controls for.

`--untapped` (v = 0) separates the two candidate explanations for the 3.5×:

* **Base Greenland matches the physics at 2150 to 3%** (45.2 vs 46.5 cm).
* Therefore the **entire** 2150 excess is the tap, draining at τ = 50 yr from an
  onset the PROTECT world crosses in 2097.

Caveat on the base model: it matches at 2150 but is **1.6× high at 2100** and
**2.6× low at 2300**. Ours is more linear, CISM more convex; 2150 is where they
cross, not where they agree in shape.

---

## 3. THE FINDING IS THE SHAPE, NOT THE CELL

`figures/protect_forcing_matched.png` panel (c). Tap **needed** (physics minus our
base) vs tap **given** by the shipped exponential, cm:

| year | needed | given |
|---|---|---|
| 2120 | −7.0 | 46.2 |
| 2140 | −2.3 | 97.3 |
| 2200 | 32.9 | 169.4 |
| 2300 | 144.4 | 195.9 |

The physics wants **nothing from the tap until ~2147**, then a term **still
accelerating at 2300** (0.68 cm/yr over 2160-2200 → 1.25 over 2260-2300). The
shipped exponential is front-loaded and saturating. **No single exponential fits
both ends**: τ = 158 yr matches 2300 and still puts 57 cm at 2150 where ~1 is
wanted.

### The whole admissible set fails there

`--set`, 25 cells (`outputs/diag_protect_forcing_matched_L14_set.csv`):

* inside the physics band at 2150: **0 / 25**
* inside at 2300: **16 / 25**
* inside at **both: 0 / 25**

Set spread at 2150 is 100-224 cm against a physics band of 45-53. Even the
slowest cell on the grid (τ = 200 yr) is 2× high. **The τ axis tops out before the
regime the physics wants.**

### What fits is exactly inert on our own scenario

`--scan` (EXPLORATORY, deliberately outside the priced grid): onset **9.5-10.0 K,
τ 80-120 yr, V 2.0 m** clears both horizons. Our ssp585 peaks at 7.81 K, so those
cells never fire on it — **measured, not argued: 0.0 cm difference from the
untapped run at 2300**, i.e. Greenland@2300 would go 230.3 → 50.0 cm.

Read that as functional form, **not** as a 9.5 K physical threshold. An
exponential can only be back-loaded by moving the onset late, so fitting a convex
trajectory forces the onset past our scenario's reach. Note too that the onset
bracket (4.69, 7.81] **is** our ssp585's own 2100 and 2300 GMST — a
scenario-relative construction that cannot be tested by a hotter ensemble from
inside itself.

---

## 4. A SECOND, SMALLER MISMATCH: AMPLIFICATION

Same reducer, using the repo's own `build_t_gis` mask (`amp_11yr` column):

| Greenland/global amp, 11-yr | 2100 | 2150 | 2290 |
|---|---|---|---|
| IPSL-CM6A-LR | 1.60 | 1.45 | 1.31 |
| CESM2-WACCM | 1.42 | 1.39 | 1.30 |
| **ours, effective `amp·S(dT)`** | **1.65** | **1.65** | **1.65** |

Ours is pinned flat by the S table's hold above 2.75 K. So even at matched
*global* temperature we feed Greenland **7% (2100) to 27% (2290)** more warming
than the PROTECT ice sheet saw. The GCMs' continued decline is what the
pre-registered `gis_amp_shape_fullcurve` arm assumes — **an argument for running
that arm, not for adopting it** (two GCMs, one member each).

---

## 5. NEXT

1. **Run the `gis_amp_shape_fullcurve` sensitivity** (`LADRILLO_GIS_SHAPE` env
   var) on the matched-forcing driver. It is pre-registered, it is one env var,
   and it removes the flat-hold that produces the 27% gap in §4. Do this before
   anything structural.
2. **Price a convex tap form** against the same physics residual — the residual
   curve in §3 is the target, and it is close to a power law in (t − t_onset).
   `outputs/diag_protect_forcing_matched_L14_untapped.csv` minus
   `outputs/protect_greenland_gis_annual.csv` is the fitting target, already on
   disk.
3. **The τ axis of the priced grid should be extended** regardless of form —
   200 yr is the ceiling and it is not slow enough to reach the physics.
4. **Per-basin check still available and still unused**: `scalars_rm_GIS` carries
   IMBIE2-Rignot basins, so **NO+NE is exactly our high basin** — a direct physics
   check on the tap's own basin rather than the sheet total.
5. **Do NOT gate the admissible set on this.** n = 18, ONE ice sheet model
   (NORCE-CISM), TWO GCMs at ONE member each. Marcus 2026-08-21: the looser gate
   stands. What has changed is the *direction* of the evidence, not its weight.

---

## 6. TRAPS

* **A comparison at two different forcings is not a comparison.** The prior
  handoff's "2300 agrees to 1.4%" was two worlds 5.9 °C apart landing on the same
  number, which is a coincidence, not a validation — and it was read as one.
* **The Pangeo CMIP6 zarr mirror has no post-2100 data**, for any member of either
  model, while advertising `experiment_id == "ssp585"`. Check `time[-1]`, not the
  experiment id.
* **`--untapped` before any ratio.** "3.5× too high" is uninterpretable until the
  base model and the tap are separated; they attribute the excess to entirely
  different things.
* **Suspicious uniformity is a bug signal, and it fired.** The first `--scan`
  printed twelve identical console blocks: the horizon selector matched
  (year, arm, component) but not the cell, so every cell after the first reported
  the first one's rows. `project_ssps_components_ladrillo.jl` carries an explicit
  warning about exactly this for its `--tap-set` arm. The CSV was always right.
* **Sensitivity arms have to be RUN.** The CHANGELOG draft attributed the
  splice-vs-raw difference (3.5 cm at 2150) to smoothing, before `--unsmoothed`
  had been run. Smoothing actually moves Greenland 0.0 cm at 2150.
