# Are the other observational datasets in FIG 1 consistent with IMBIE 2026?

**Question (Marcus, 2026-09-27).** Short answer: **two of them disagree with IMBIE at ~2σ, and the one
test that could adjudicate has no power to do it.** Sources named per block; all values cm SLE on the
figure's shared 1995–2005 baseline.

## 1. Which datasets *could* disagree at all

FIG 1 carries six observational series. Four of them measure something IMBIE does not, so they cannot
be inconsistent with it in any direct sense:

| series | overlaps IMBIE? |
|---|---|
| GlaMBIE 2025 (glaciers, − r5) | no — different component |
| NOAA 0–2000 m thermosteric | no |
| observed land-water storage | no |
| Dangendorf 2024 / IGCC (total) | **only through the budget** (§3) |
| **Frederikse 2020 + GRACE-FO — Antarctic** | **yes, directly** |
| **Frederikse 2020 + GRACE-FO — Greenland** | **yes, directly** |

## 2. ⭐⭐ The two that do overlap disagree — **in opposite directions**

| | IMBIE 2026 | our target | difference | in IMBIE's own sd |
|---|---|---|---|---|
| **AIS 1979–2023** | +1.312 | +0.907 | **−0.405 cm** | **−2.8 σ** |
| **GIS 1972–2023** | +1.749 | +1.990 | **+0.241 cm** | **+1.9 σ** |

**Frederikse is LOW on Antarctica and HIGH on Greenland**, each by about two of IMBIE's standard
deviations. This is the same opposite-signed structure the *model* shows against IMBIE
([[gis_imbie2026_early_bias]]) — and it is worth separating the two: **the target disagreement is
between two observational products**, and is not something the calibration can fix.

⚠ **The modern agreement is partly SHARED DATA, not independent corroboration.** IMBIE 2026 is a
reconciliation of *"altimetry, gravimetry, and the input-output method"* (its own dataset header), and
our ice-sheet targets splice **GRACE-FO from 2019**. So gravimetry sits inside both. The
pre-satellite disagreement is the informative part; the post-2019 agreement is partly circular.

## 3. ⛔ The budget test cannot adjudicate — and my first reading of it was wrong

The one way the *other* datasets bear on IMBIE is closure: do the components sum to the independently
measured total (Dangendorf 2024)? If IMBIE's ice sheets close the budget better than Frederikse's,
that is evidence for IMBIE.

⚠⚠ **I first reported "swapping to IMBIE makes closure BETTER by 0.180 cm." That reading does not
survive an error bar or a second window, and is withdrawn.**

| window | total | residual, Frederikse ice | residual, IMBIE ice | improvement |
|---|---|---|---|---|
| 1979–2021 | +10.79 | −0.734 ± 1.465 (**0.5 σ**) | −0.555 (0.4 σ) | **+0.180** |
| 1993–2021 | +8.31 | +0.160 ± 1.151 (**0.1 σ**) | +0.232 (0.2 σ) | **−0.071** |
| 1972–2021 | +10.88 | −0.683 ± 1.541 (**0.4 σ**) | −0.626 (0.4 σ) | **+0.057** |

Two things kill it:

1. **The budget already closes.** Every residual is **0.1–0.5 σ**. There is no significant non-closure
   for a better ice-sheet product to explain. (This is the same conclusion as
   [[curvature_needs_an_error_bar]] reached for the curvature version of the question.)
2. ⛔ **The "improvement" FLIPS SIGN with the window** (+0.180, −0.071, +0.057) and every value is
   **one tenth to one twentieth of the bar on the residual**. That is noise, not a ranking.

⇒ **The budget test has NO POWER to choose between Frederikse and IMBIE on the ice sheets** — it is
the [[no_power_null]] pattern: a test whose null is structurally guaranteed reports "no difference"
identically to one that looked and found none. It should be reported as unable to discriminate, and
**not** cited in either product's favour.

## 4. What this does and does not license

- ✅ **Sayable:** the two ice-sheet observational products disagree at ~2σ, in opposite directions, and
  the disagreement is largest where satellite constraint is weakest.
- ⛔ **Not sayable:** that the budget favours IMBIE (it does not discriminate), or that IMBIE is
  "the better product" *on this evidence*. The argument for IMBIE is its reconciliation method and
  vintage, not closure.
- ~~Open, and not tested here: whether GlaMBIE and IMBIE share input through region 19.~~
  **Answered 2026-09-29 — §5.**

## 5. Region 19: no shared input, a small DOMAIN overlap, and it does not change §3 (2026-09-29)

**Question:** do GlaMBIE's glacier series and IMBIE 2026 overlap through the Antarctic periphery
(RGI6 region 19), which the glacier target deliberately keeps?

**Shared INPUT DATA: none.**
- GlaMBIE's region-19 inputs (read from the zip's `glambie_input_20240716/19_antarctic_and_subantarctic/`)
  are **altimetry** (Gardner 2013 ICESat, Jakob & Gourmelen, Khan), **DEM differencing** (Hugonnet),
  **glaciological** (Zemp, WGMS) and **combined** (Dussaillant, Huss). **There is no gravimetry input
  for r19**; Alaska, for example, has one.
- IMBIE 2026 discusses two of these — Hugonnet 2021 (its ref 32, 20.9 ± 4.9 Gt/yr, 2010–2018) and
  Jakob & Gourmelen 2023 (ref 35, 3.5 ± 0.4 Gt/yr, 2010–2020) — together with Rignot 2019 (balance)
  **only in order to decline** an Antarctic correction: *"We thus do not attempt to correct the altimetry
  time-series for their omission of the GICs mass changes in Antarctica"* (Otosaka et al. 2026,
  Methods, "Accounting for the Ice Sheets' Peripheral Glaciers and Ice Caps"). It does use Hugonnet
  for **Greenland's** GICs. That is r5, which the glacier target subtracts, so it never reaches the sum.

**DOMAIN overlap: yes, partial, and present in BOTH arms.**
- IMBIE: *"all our gravimetry estimates account for both the main ice sheets and their periphery …
  this is not the case of our altimetry estimates and one of our input-output estimates"* (same
  section). So the reconciled Antarctic series carries **some fraction** of the connected periphery
  from 2002 on. The fraction is the gravimetry weight in an inverse-variance mean, and **the published
  CSVs do not give per-technique series**, so it cannot be recovered.
- The Frederikse arm has the same property. Frederikse 2020 drops r19 from glaciers *because* "GRACE
  cannot distinguish the contributions from the Greenland and Antarctic peripheral glaciers from those
  from the ice sheets" (his Methods). His AIS column includes Bamber 2018, which by its own statement
  includes PGIC, and our target splices GRACE-FO mascons from 2019. This was already recorded in
  `notes/memo_2026-08-05_mengel_a0_results_and_recalib_options.md` §2c (near-coast PGIC ≈ 3.3 % of
  IMBIE-3 gravimetry). **It is not a new hole in the calibration target.** The `prep_recalib_targets_ext.py`
  comment calling r19 a "deliberate zero everywhere else in the chain" is true of Frederikse's
  *glacier* column only, and is now corrected there.

**Size: a ceiling, since the fractions are unknown.** Assume one arm carries 100 % of r19 and the other
0 %. The differential double count can then be no larger than **all** of GlaMBIE's r19 loss over the
gravimetry years inside the budget windows. That includes the sub-Antarctic islands, which lie outside
any ice-sheet mask, so the ceiling overstates:

| GlaMBIE r19 | mean rate | cumulative | σ (independent yrs → fully correlated) |
|---|---|---|---|
| **2002–2021** (gravimetry ∩ budget windows) | −13.5 Gt/yr | **0.075 cm** | 0.049 → 0.219 cm |
| 2000–2023 (all of GlaMBIE) | −17.8 Gt/yr | 0.118 cm | 0.058 → 0.279 cm |

(3618 Gt per cm SLE; `glambie_results_20240716/calendar_years/19_antarctic_and_subantarctic.csv`.)

**What it does to §3:**
- **"The budget closes" and "the test cannot rank": unchanged.** 0.075 cm is **≤ 0.065σ** of the
  residual bars (1.15–1.54 cm).
- ⚠ **It is the same size as the "improvement" itself** (0.057–0.180 cm), so the withdrawn number
  carries a **systematic of its own magnitude**. Its sign also depends on the window. Extra periphery
  in one arm raises that arm's component sum, which worsens its |residual| where the components
  overshoot the total and improves it where they undershoot. The residuals **change sign** between
  the 1979/1972 windows and 1993–2021, so the systematic's effect on the "improvement" changes sign
  with them. (This holds whichever way the residual is defined; the table's sign convention was not
  re-checked, since the budget arithmetic in `deefbee` was not scripted.) As predicted, this weakens
  the test further and never rescues it.
- **The draft's sentence is unaffected.** "substituting one product for the other moves the residual
  by a tenth of its own uncertainty" (`build_gmd_otosaka.py`) holds with or without the overlap.
