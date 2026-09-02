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

## 5. THE POLICY (Marcus 2026-09-02) — DO NOT COMMINGLE THE TWO SCENARIO GENERATIONS

⭐ **This is a stronger argument than the "lossy mapping" one above, and it supersedes my framing.**

**The SSPs PREDATE the CMIP7 marker scenarios.** So there is no *correct* marker for an SSP — not
merely an imprecise one. Borrowing CMIP7 marker land use and irrigation for a CMIP6 SSP imports a
different scenario generation's assumptions into a scenario that already has its own. That is a
category error, not a tolerance question, and it is why the measured cost (0.003 K where the mapping
was defensible, 0.054-0.104 K where it was a stretch) understates the problem: even the "defensible"
mappings are anachronistic, they just happen to agree.

**The van Vuuren markers are the opposite case.** They ARE the CMIP7 markers, so each uses its own
`volcanic_solar_<MARKER>.csv` natively and the ambiguity is identically zero. The markers are
*required* there.

⇒ **THE SPLIT:**

| arm | treatment | why |
|---|---|---|
| **van Vuuren markers** | **marker-based** | native — each marker uses its own forcing, zero ambiguity |
| **SSPs** | **marker-free** | scenario-native land use from the SSP's OWN cumulative CO2 AFOLU; no CMIP7 assumption imported |

⚠ Keep the two sets **separate in any figure or table**. They are not a single ensemble, and a
combined band would mix a native treatment with an anachronistic one.
* ⚠ **Not appropriate for reproducing van Vuuren's own figures**, which need the per-marker forcing;
  `calibration_v160/README.md` states this.
* **Still missing for a sea-level answer:** only the GMST/OHC *means* are built. Driving Ladrillo
  marker-free needs the per-config **cubes** (`build_fair_cube_v160.py`, which resolves the marker
  the same way and would need the same `none` path), then the arms. Until then this note is about
  the climate driver only, not about sea level.


---

# ADDENDUM — THE SEA-LEVEL ANSWER (marker-free arms landed 2026-09-02)

Cubes built for the four like-for-like SSPs (MEAN-MATCH 2-9e-16) and Ladrillo L24 run on them,
tapped, matching every other L24 arm.

## The overshoot penalty, both ways

    yr   |        MARKER (HL vs L)        |          MARKER-FREE
         |   OS     126    penalty   dT   |   OS     126   penalty     dT
    2100 | 43.6    38.4    +5.2 cm  +0.142| 42.5    37.8   +4.7 cm  +0.118
    2150 | 54.2    50.2    +4.0 cm  -0.063| 52.5    49.4   +3.2 cm  -0.102
    2300 | 73.7    72.6    +1.1 cm  -0.082| 70.1    71.1   -1.0 cm  -0.133

⭐ **Removing the CMIP7 marker assumption moves the 2300 penalty by −2.2 cm, from +1.1 to −1.0 cm.
It does not rescue it — it turns it slightly negative. The small penalty is NOT a marker artifact.**

## Against SLEIP

SLEIP's own framing is that the penalty *"persists by 2300 compared to SSP1-2.6, even after GSAT has
returned to the SSP1-2.6 level by 2150"* — so 2150 onward is where their claim lives.

| | 2150 | 2300 |
|---|---|---|
| Ladrillo, marker | +4.0 cm | +1.1 cm |
| Ladrillo, marker-free | +3.2 cm | −1.0 cm |
| **SLEIP, 7 emulators** | — | **+10 to +30 cm** |

⇒ **Ladrillo shows 3-5 cm of overshoot penalty where SLEIP's ensemble shows 10-30 cm, and it decays
to zero by 2300 where theirs persists.** Ladrillo RECOVERS from an overshoot; their ensemble
largely does not.

⚠ **The honest caveat, unchanged.** Our SSP5-3.4-OS ends 0.06-0.13 K COOLER than our SSP1-2.6, which
biases our penalty LOW. But it cannot account for a 10-30 cm difference, and it is not a marker
artifact — going marker-free makes the temperature gap *larger*, not smaller. ⚠ A fully clean
comparison still needs SLEIP's own scenario pair on a matched dT; ours is a different realisation
of SSP5-3.4-OS, not theirs.

## ⇒ THE STANDING HYPOTHESIS, NOW WELL POSED

Since the temperature confound is bounded and the marker assumption is excluded, the residual is a
**model** difference: **Ladrillo has materially less sea-level hysteresis than the SLEIP ensemble.**
The leading candidate is the floored-equilibrium glacier law — of the four models we compare, only
MAGICC could express glacier regrowth before Ladrillo's 2026-08-31 change, and Ladrillo's glacier
rate at 2300 now falls to 0.00-0.55 mm/yr on declining pathways against 1.96 rising.

⚠ **NOT YET DEMONSTRATED.** The decomposition that would show it — the penalty by component, with
and without the floored law — has not been run. That is the next experiment, and it is cheap: the
old law is still reachable behind `GIC_REGROW_R`.
