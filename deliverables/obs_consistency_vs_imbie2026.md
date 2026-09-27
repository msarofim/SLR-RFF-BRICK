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
- ⚠ **Open, and not tested here:** whether GlaMBIE's glacier series and IMBIE share input through the
  Antarctic-periphery region 19, which the target explicitly keeps. If they do, the components are not
  as independent as the budget assumes — which would weaken the test further, not rescue it.
