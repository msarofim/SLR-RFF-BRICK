# Note — running the SSPs WITHOUT the CMIP7 marker assumptions

**Written 2026-09-02.** Answering "can we run all the SSPs without any of the CMIP7 marker
assumptions?" **Yes — the machinery already existed, and it is arguably the better default for
cross-scenario work.** Seven SSPs built marker-free. **Scoping only; the shipped drivers are
unchanged.**

## 1. WHAT "MARKER-FREE" MEANS, AND HOW COMPLETE IT IS

`volcanic_solar_<MARKER>.csv` carries four prescribed series. Marker-free status of each:

| series | marker-dependent? | marker-free treatment |
|---|---|---|
| Volcanic | **NO** — identical across all 7 markers | unchanged |
| Solar | **NO** — identical across all 7 | unchanged |
| **Land use** | YES | ⭐ `input_mode` = **`calculated`** — derived from each scenario's OWN cumulative CO2 AFOLU. Fully scenario-native, no marker. |
| **Irrigation** | YES | ONE shared trajectory (the 7-marker mean). ⚠ Removes the *choice*, but the number is still CMIP7-derived; 1.6.0 ships no calculated mode for it. |

⇒ **Land use becomes genuinely scenario-native; irrigation becomes choice-free but not
assumption-free.** Volcanic and solar were never marker-dependent. This is `calibration_v160/`,
built originally because RFF-SP has no marker file; `build_fair_mean_v160.py --marker none` now
selects it.

## 2. ⚠ THE POSTERIOR IS USED OFF-DESIGN — and here is the size of it

The constrained parameters are **byte-identical** between the two calibrations (verified), so
1.6.0's posterior was never constrained under `calculated` land use. That is only tolerable if the
deviation is small over the **constraining period**. Measured on ssp245:

| window | max \|diff\| | as % of the ensemble's OWN p5-p95 spread |
|---|---|---|
| 1900 | 0.0084 K | 2.3 % |
| 1950 | 0.0087 K | 2.4 % |
| 2000 | 0.0106 K | 2.3 % |
| 2023 | 0.0296 K | **6.0 %** |

Mean over 1850-2023: **+0.0008 K** — a wiggle, not a systematic offset.

⚠ **I first called this "NOT SAFE" against a hand-picked 0.02 K gate. That verdict was wrong** and
is exactly the error `tolerance_scaled_to_spread` warns about — an absolute threshold that ends up
choosing the physics. Scaled to the quantity it tests, the deviation is 2-6 % of the ensemble's own
spread, and **smaller than the marker ambiguity it removes** (0.022-0.094 K, up to 19 % of that
spread). ⇒ **Usable, as a stated deviation.**

## 3. THE RESULT — and the marker matters exactly where the mapping was a stretch

⛔ **Only four scenarios are LIKE-FOR-LIKE.** `ssp119`, `ssp370`, `ssp460` have no calib 1.6.0 marker
run — their mean files are 2026-06-13, i.e. **calib 1.4.5** — so a difference would confound the
marker treatment with the whole migration. I built the table with all seven first and had to throw
three rows away.

| scenario | marker | marker GMST @2300 | marker-free | diff | the mapping |
|---|---|---|---|---|---|
| ssp245 | M | 3.176 | 3.180 | **+0.004** | direct correspondence |
| ssp585 | H | 7.498 | 7.500 | **+0.002** | no documented counterpart, empirically fine |
| ssp126 | L | 1.815 | 1.761 | **−0.054** | "no clean counterpart" — documented open question |
| ssp534over | HL | 1.733 | 1.628 | **−0.104** | our 09-02 choice; an overshoot has no CMIP6 analogue |

⭐ **The marker treatment costs ~0.003 K where the mapping was defensible and 0.054-0.104 K where it
was a stretch.** Going marker-free removes a choice that was only ever load-bearing for the
scenarios that had no honest counterpart — which is precisely the argument for adopting it.

## 4. EFFECT ON THE OVERSHOOT QUESTION

    OS minus SSP1-2.6 at 2300:   marker -0.082 K   ->   marker-free -0.133 K

⇒ **Marker-free DEEPENS the gap.** The overshoot ending cooler than SSP1-2.6 is **not** a marker
artifact — removing the markers makes it more pronounced. Combined with the path finding
(ssp534over emits +10 GtCO2 MORE cumulatively and still ends cooler), the temperature behaviour is
a real property of the scenario pair, and Ladrillo's small sea-level penalty cannot be explained
away as a forcing-assumption artifact.

## 5. RECOMMENDATION, AND WHAT IS STILL MISSING

* **Run marker-free as a SENSITIVITY SET alongside the marker set, not as a replacement.** That
  turns the marker ambiguity from a choice into a measured quantity, per scenario.
* ⚠ **Not appropriate for reproducing van Vuuren's own figures**, which need the per-marker forcing;
  `calibration_v160/README.md` states this.
* **Still missing for a sea-level answer:** only the GMST/OHC *means* are built. Driving Ladrillo
  marker-free needs the per-config **cubes** (`build_fair_cube_v160.py`, which resolves the marker
  the same way and would need the same `none` path), then the arms. Until then this note is about
  the climate driver only, not about sea level.
