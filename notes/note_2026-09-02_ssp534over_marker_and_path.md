# Note — the CMIP7 marker assumptions behind SSP5-3.4-OS, and why it ends cooler than SSP1-2.6

**Written 2026-09-02**, revisiting the assumptions in the SSP5-3.4-OS build after the overshoot
penalty came out an order of magnitude below SLEIP's. **Scoping only; nothing changed in the model.**

## 1. WHAT THE MARKER ACTUALLY SETS

`volcanic_solar_<MARKER>.csv` carries **four** prescribed series — Volcanic, Solar, **Land use**,
**Irrigation** — not two. Volcanic and Solar are identical across all seven markers, so the marker
choice is *entirely* a land-use + irrigation choice after 2023.

Measured, W/m², at 2300 (`L` is what ssp126 uses; `HL` is what ssp534over uses):

| | L (ssp126) | HL (ssp534over) | H | HL − L |
|---|---|---|---|---|
| Land use | −0.0771 | −0.1209 | −0.1978 | **−0.0438** |
| Irrigation | −0.0595 | −0.0383 | −0.1073 | **+0.0212** |
| Volcanic, Solar | identical | identical | identical | 0 |
| **net** | | | | **−0.0226** |

⭐ **Irrigation runs OPPOSITE to land use and cancels about half of it.** HL's irrigation forcing is
*less* negative than L's, offsetting −0.0438 of land use down to a −0.0226 net. Anyone reasoning
about the marker from land use alone would double the effect.

⚠ **The irrigation scaling is applied, and cannot silently fail.** 1.6.0's Irrigation is a
prescribed (`input_mode=forcing`) species, and FaIR applies `forcing_scale` internally only to
CALCULATED species — so a naive driver leaves it unscaled and the run just looks cooler. The
builder scales every prescribed specie explicitly and **hard-errors** if any lacks a scale column
(the `fbb1375` fix). Verified in our run: `Solar`, `Volcanic`, `Land use`, `Irrigation` all scaled.

## 2. THE MARKER SENSITIVITY, MEASURED FOR THIS SCENARIO

Re-ran SSP5-3.4-OS with marker **H** to bound it:

    yr        HL         H      H−HL     OS(HL)−126   OS(H)−126
    2100    2.043     2.007    −0.036       +0.142       +0.106
    2150    1.715     1.649    −0.066       −0.063       −0.130
    2300    1.733     1.642    −0.091       −0.082       −0.173

⚠ **0.091 K at 2300 — at or above the top of the documented SSP range** (0.022–0.094 K). **Overshoot
and low scenarios are disproportionately marker-sensitive**, because the prescribed land-use and
irrigation forcing is a larger share of a *reduced* total forcing after the peak. On ssp585 the same
0.146 W/m² would be ~1 % of the signal; here it is ~5 %.

⇒ **Scaling that to the actual HL-vs-L difference (−0.0226 W/m²) gives ~0.014 K — about 17 % of our
−0.082 K OS-minus-SSP1-2.6 gap at 2300.** The marker explains a sixth of it, not the whole thing.

⭐ **And HL was the right choice.** Under H the gap would be **−0.173 K**, more than double, making
the penalty anomaly *worse*. The alternative would have deepened the artifact it was suspected of
causing.

## 3. THE COOLER ENDING IS REAL, AND IT IS A PATH EFFECT — NOT A BUDGET ONE

The remaining ~83 % is the scenario. And it is not what one would guess:

    cumulative CO2 1750-2300:   ssp534over  3,101 GtCO2   ssp126  3,091   diff  +10
    cumulative CO2 2100-2300:   ssp534over   −982 GtCO2   ssp126   −515   diff −467

⭐ **SSP5-3.4-OS emits MORE cumulatively than SSP1-2.6 (+10 Gt to 2300) and still ends 0.082 K
COOLER.** The mechanism is the *path*: a deep sustained net-negative excursion after 2100 (−982
against −515 GtCO2) draws concentrations down faster than SSP1-2.6's flat tail, and the ocean then
has 150+ years to equilibrate to the lower forcing. Cumulative budget does not determine the 2300
endpoint on these pathways.

## 4. ⇒ WHAT THIS DOES TO THE OVERSHOOT-PENALTY QUESTION

It **sharpens** it rather than dissolving it.

* The temperature confound is now **quantified**: 17 % marker, 83 % a real path effect. It is not an
  artifact of our marker choice, and it would have been worse under the alternative.
* Because SSP5-3.4-OS ends at or below SSP1-2.6 in temperature, **any positive sea-level penalty at
  2300 is committed/hysteretic sea level, not a temperature difference.** SLEIP report **0.1–0.3 m**
  of it across seven emulators; Ladrillo gives **0.011 m**.
* ⇒ The open question is now well posed: **does Ladrillo have materially less sea-level hysteresis
  than the other emulators, and if so is that the floored-equilibrium glacier law (which lets it
  recover where melt-only models cannot) or a missing commitment mechanism?**

⚠ **Still do not quote the 0.011 m as a model finding** until it is checked against SLEIP's own
scenario pair — their SSP5-3.4-OS and SSP1-2.6 may not have the same temperature relationship as
ours, and the comparison is only meaningful on a matched dT.
