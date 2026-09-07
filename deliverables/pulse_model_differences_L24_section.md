<!--
SECTION DRAFT for LadrilloUpdateDescription_L24.docx (handoff_2026-09-05b item 3).
Paste as a new Heading2 section after "Ladrillo Projection Comparison".

⚠ EVERY NUMBER BELOW IS GENERATED. The tables are produced by
   FaIRtoFrEDI/magicc_comparison/build_pulse_doc_tables.py -> deliverables/pulse_model_differences_tables.md
and pasted here verbatim; re-run it and re-paste rather than editing a number in place.

Style follows the existing document: Heading2/Heading3, bold lead-in labels on BodyText
paragraphs, FIG N captions as their own paragraphs. Figure numbering starts at FIG 10,
continuing from FIG 9 in the current draft.
-->

## Ladrillo Compared on a Pulse

Everything above compares scenarios. A separate question is what each model does to a single
marginal emission, which is the quantity a social cost of greenhouse gases integrates. A
1 GtCO₂ or 0.01 GtCH₄ pulse was released in 2030 on top of each of the seven van Vuuren
markers, and every model was run twice — once with the pulse and once without — on the same
draws, so the difference is paired member by member rather than differenced between ensembles.

**Basis for every pulse number below.** Response is the paired **mean**, in cm per Gt of the
gas emitted, at 2100 and 2300. The mean rather than the median: in a threshold model the median
deletes most of the expected Antarctic response, so a median-only comparison would understate
Ladrillo and BRICK 2.0 against models that have no threshold. Each model divides by the pulse it
actually emitted — MAGICC's emissions file quantises a nominal 1 GtCO₂ to 0.99992 Gt.

**The comparison rests on five of the seven markers.** MAGICC's Greenland surface-mass-balance
module is evaluated below pre-industrial on vvLN and vvML and returns physically wrong values
there, so those two markers are dropped from MAGICC entirely. A horizon can be dropped one at a
time; a time-integral cannot, so the whole marker goes rather than one of its years.

**FACTS enters as workflows, not as a model.** Two of its four ice-sheet workflows cannot see a
pulse at all: the expert-elicitation ensembles behind `deconto21` (Antarctica) and `bamber19`
(Antarctica and Greenland) are selected by a discrete pick that a ~4 × 10⁻⁴ °C shift never
flips, so they return exactly zero for every member, every marker and every year. That leaves
`wf1f` (AR5 ice sheets) and `wf2f` (LARMIP Antarctica) as the only pulse-valid workflows, and
both are shown. Their disagreement with each other at 2300 is about a factor of two, comparable
to the disagreement among the three primary models.

**The two "on MAGICC's climate" rows are a decomposition, not a fourth and fifth model.**
Ladrillo and BRICK 2.0 were each re-run on MAGICC's own paired pulse climate, holding the
sea-level module and moving only the forcing. They belong beside the MAGICC column as an
attribution of the difference, never in the model row.

### Total response

| model | CO2 2100 | CO2 2300 | CH4 2100 | CH4 2300 |
|---|---|---|---|---|
| MAGICC-SLR | 0.0151 [0.0122, 0.0164] | 0.0412 [0.0244, 0.0868] | 0.6222 [0.5547, 0.6964] | 0.7826 [0.5929, 1.1254] |
| Ladrillo L24 | 0.0175 [0.0124, 0.0186] | 0.0364 [0.0359, 0.0485] | 0.9852 [0.9674, 1.0686] | 0.9898 [0.7970, 1.1350] |
| BRICK 2.0 | 0.0173 [0.0134, 0.0190] | 0.0323 [0.0277, 0.0490] | 1.0692 [0.6861, 1.6125] | 0.9867 [0.8012, 1.3872] |
| FACTS wf1f (AR5 ice sheets) | 0.0061 [0.0059, 0.0069] | 0.0127 [0.0087, 0.0168] | 0.3740 [0.3424, 0.4407] | 0.2875 [0.2464, 0.4490] |
| FACTS wf2f (LARMIP AIS) | 0.0086 [0.0083, 0.0095] | 0.0273 [0.0210, 0.0314] | 0.5898 [0.5432, 0.6754] | 0.5172 [0.4916, 0.7091] |
| *decomposition, not a fourth model:* | | | | |
|   Ladrillo on MAGICC's climate | 0.0174 [0.0112, 0.0205] | 0.0345 [0.0209, 0.0489] | 0.6169 [0.4820, 0.6604] | 0.6577 [0.4354, 0.7490] |
|   BRICK 2.0 on MAGICC's climate | 0.0207 [0.0107, 0.0229] | 0.0302 [0.0235, 0.0600] | 0.8841 [0.5151, 0.9518] | 0.7889 [0.5760, 1.0908] |

**At 2100 the three primary models agree; at 2300 they do not.** MAGICC-SLR is the largest CO₂
responder at both horizons and its 2300 spread across markers is by far the widest — a factor
of 3.6 between the coolest and warmest marker, against 1.4 for Ladrillo and 1.8 for BRICK 2.0.
FACTS sits roughly two to three times below all three at 2100, and one component explains it:
Antarctica leaves only two of its modules, and both are far smaller than the DAIS-lineage
response.

### The methane-to-carbon exchange rate

| model | per-marker (like-for-like) | per-species median | CO2 rank | CH4 rank |
|---|---|---|---|---|
| MAGICC-SLR | **0.618** | 0.637 | 1 of 3 | 3 of 3 |
| Ladrillo L24 | **0.820** | 0.913 | 2 of 3 | 1 of 3 |
| BRICK 2.0 | **1.088** | 1.024 | 3 of 3 | 2 of 3 |
| FACTS wf1f (AR5 ice sheets) | **0.829** | 0.762 | — | — |
| FACTS wf2f (LARMIP AIS) | **0.697** | 0.637 | — | — |
| *decomposition, not a fourth model:* | | | | |
|   Ladrillo on MAGICC's climate | **0.604** | 0.640 | — | — |
|   BRICK 2.0 on MAGICC's climate | **0.755** | 0.876 | — | — |

**The species ordering reverses between models, and this is the most policy-legible result in
the comparison.** MAGICC-SLR is the highest responder to CO₂ and the lowest of the three to CH₄.
Expressed as an exchange rate — the sea-level response to a tonne of methane divided by the
response to a tonne of CO₂-equivalent at GWP₁₀₀ — the models disagree by a factor of 1.8. That
ratio is the sea-level channel of the ratio of the social cost of methane to the social cost of
carbon, so a model choice made for other reasons moves a policy-relevant ratio by nearly a
factor of two.

**The aggregation matters and should be stated.** Taking each species' median across markers
independently pairs the median methane marker with the median CO₂ marker, and for Ladrillo and
BRICK 2.0 those are different markers. Forming the rate within each marker and averaging
afterwards is the like-for-like statistic; both are shown above. The reversal and the 1.8×
spread survive either choice. The share attributed to the climate does not, and is given below
on both.

**Most of the reversal is the climate, not the sea-level module.** Re-running each module on
MAGICC's own climate moves its exchange rate most of the way to MAGICC's: on the like-for-like
per-marker rate the swap closes 107 % of the gap for Ladrillo and 71 % for BRICK 2.0 (on the
per-species median, 99 % and 38 %). An independent test confirms it. Integrating the global
mean surface temperature response over 2030–2300 and forming the same methane-to-CO₂e ratio from
warming alone gives a FaIR-to-MAGICC ratio of 1.324 (95 % bootstrap over ensemble members
[1.298, 1.351]), against 1.36 and 1.44 for the two modules' own measured swaps. The integrated
warming alone accounts for essentially all of the ordering reversal; what the sea-level modules
add is small and, notably, of opposite sign in the two of them.

### How long a pulse keeps raising sea level

| model | CO2 t50 | CO2 t90 | CO2 end/peak | CH4 t50 | CH4 t90 | CH4 end/peak |
|---|---|---|---|---|---|---|
| MAGICC-SLR | 2203-2229 | 2282-2288 | 1.000 | 2176-2194 | 2276-2280 | 1.000 |
| Ladrillo L24 | 2203-2213 | 2283-2285 | 1.000 | 2170-2181 | 2273-2276 | 0.883 |
| BRICK 2.0 | 2193-2214 | 2281-2285 | 1.000 | 2172-2184 | 2274-2277 | 0.937 |
| FACTS wf1f (AR5 ice sheets) | n/a | n/a | n/a | n/a | n/a | n/a |
| FACTS wf2f (LARMIP AIS) | n/a | n/a | n/a | n/a | n/a | n/a |
| *decomposition, not a fourth model:* | | | | | | |
|   Ladrillo on MAGICC's climate | 2200-2210 | 2282-2284 | 1.000 | 2164-2182 | 2273-2277 | 0.985 |
|   BRICK 2.0 on MAGICC's climate | 2194-2211 | 2281-2284 | 1.000 | 2171-2186 | 2274-2277 | 0.951 |

FIG 10. Time to 50 % and 90 % of the 2030–2300 response integral, by model and species.

**The timing is model-independent; the shape is not.** The time by which half the 2030–2300
response integral has accrued agrees within about a decade across a climate model and two
sea-level models — around 2200 for CO₂ and around 2180 for methane — and the 90 % time agrees
within two years. This is a stronger agreement than the response magnitudes show, and it holds
across the class boundary between a climate model with its own ice sheets and a sea-level
emulator driven by an external climate.

**Every duration number here is a share of what is delivered by 2300, never of the eventual
total.** The CO₂ response has not peaked in any model: its 2300 value is its maximum everywhere.
The methane response has turned over, which is what makes the two species comparable at all on
this statistic and what makes the CO₂ column of the peak statistic uninformative.

**A level-based version of the same question does not agree** and should not be used. Asking
when a response first reaches half its 2300 value is well defined only while the response is
still rising; once methane's response peaks and declines, that question is answered absurdly
early. The integral version is monotone by construction.

### Which components carry the persistence

| model | ais share | te share | glaciers share | gis share |
|---|---|---|---|---|
| MAGICC-SLR | 42%-60% | 13%-22% | 4%-12% | 19%-29% |
| Ladrillo L24 | 64%-72% | 15%-18% | 5%-10% | 8%-10% |
| BRICK 2.0 | 66%-82% | 11%-18% | 4%-12% | 3%-5% |
| *decomposition, not a fourth model:* | | | | |
|   Ladrillo on MAGICC's climate | 40%-68% | 14%-25% | 6%-20% | 8%-15% |
|   BRICK 2.0 on MAGICC's climate | 55%-80% | 9%-20% | 6%-19% | 3%-7% |

FIG 11. Component shares of the methane response integral, by model.

**Antarctica is why a methane pulse acts for so long.** It is the largest contributor to the
integral in every model, the latest — its half-time is three to seven decades after thermal
expansion's — and the only component that does not turn over anywhere: its 2300 value is
0.96–1.00 of its peak in all three models. Thermal expansion, which tracks methane's own
radiative forcing most directly, has fallen to 0.40–0.52 of its peak by 2300, and glaciers to
0.06–0.70. Greenland is the exception that has to be stated: it holds at its peak in BRICK 2.0
and MAGICC but falls to as little as 0.38 in Ladrillo, so persistence is a property of
Antarctica in every model and of Greenland only in some. Greenland is also where the models
disagree by
class: it carries 19–29 % of MAGICC's methane integral against 3–10 % for the two sea-level
models, and re-running them on MAGICC's climate closes only a small part of that. Greenland is
a module difference; thermal expansion is not.

### Thermal expansion across the class boundary

| marker | MAGICC's ocean heat | Ladrillo / BRICK 2.0 thermal expansion | MAGICC's own thermal expansion |
|---|---|---|---|
| vvVL | 0.6087 | 0.6083 / 0.6087 | **0.4846** |
| vvL | 0.6069 | 0.6066 / 0.6072 | **0.4806** |
| vvM | 0.5927 | 0.5926 / 0.5921 | **0.4992** |
| vvHL | 0.5894 | 0.5892 / 0.5889 | **0.4662** |
| vvH | 0.5867 | 0.5867 / 0.5858 | **0.5147** |

FIG 12. Thermal expansion response shape on FaIR's climate, on MAGICC's climate, and MAGICC's own.

**The sea-level modules transmit the ocean heat they are handed, exactly.** As noted in the
hindcast discussion above, thermal expansion in both Ladrillo and BRICK 2.0 is exactly
proportional to the ocean heat given to them, and the "on MAGICC's climate" arms pass MAGICC's
own paired ocean heat, not its temperature. The consequence is measurable and it holds: across
56 model-marker-species cells in both climates, a module's thermal-expansion shape reproduces
its climate's ocean-heat shape to within 0.0016 on the peak ratio and to within one year on the
half- and ninety-percent times. On this component the two modules are indistinguishable from
each other — they differ by about 0.001 — while changing the climate moves both by 0.19.

**MAGICC's own thermal expansion is not proportional to the ocean heat MAGICC reports.** It
reaches only 79–88 % of what its own ocean heat implies, and it leads that ocean heat by five to
nine years on methane and by one to four years on CO₂. Since the modules are exact transmitters,
this is a difference inside MAGICC's heat-to-expansion mapping — a depth or expansivity structure
that a single global coefficient cannot represent — and not an artifact of driving a sea-level
emulator with an external climate. Why it takes that particular form is untested.

### Caveats carried by these numbers

**The splice.** Each model's climate driver is spliced to a common observed path before 2014,
and for a threshold model the splice does not cancel between the pulse and baseline arms the way
it does for a smooth one. On the Antarctic component the splice moves the median response by
20 % for Ladrillo and 32 % for BRICK 2.0, and on BRICK 2.0's methane response it reaches 96 % of
the raw value. Any Antarctic or methane number from a threshold model should be read with its
own arm's splice figure attached.

**Two earlier readings are withdrawn rather than repeated.** A claim that the climate-versus-
module decomposition has no resolving power on methane applies only to the total and to
Antarctica; thermal expansion and glaciers are resolved on methane in both modules. And a claim
that Greenland is the one component whose signature carries from scenario levels to marginal
responses rested on one of four cells, with both CO₂ cells resolving the other way.

**Precision.** The Antarctic sub-component carries a 5–8.5 % relative standard error on the
mean, accepted rather than bought down with more draws; the largest unpriced uncertainty in the
Antarctic response is the functional form of the threshold flux, not this. Interval widths quoted
here should not be compared with each other at the one-percentage-point level.
