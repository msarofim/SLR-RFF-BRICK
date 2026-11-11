---
title: "Ladrillo GMD draft: guidance for the next round of hand edits"
subtitle: "Draft saved 2026-11-11 10:19 · prepared 2026-11-11"
---

# How to use these notes

Your 11-08 to 11-11 edits took in nearly all of the 11-07 suggestions. This list covers what is left. Items run page by
page, using the page numbers Word showed at your last save. Tags:

- **HAND**: a text change for this round. Suggested wording is in the indented blocks.
- **DECIDE**: your call; the recommended option comes first.
- **CLOSE**: the text now handles the comment; resolve the bubble.
- **NEXT PASS**: I do it in the pass you asked for (figures, notation, references). No hand work needed.

Tony's tracked edits stay as he wrote them. No suggestion below rewrites his text; where a fix touches a paragraph he
edited (the discrepancy paragraph, Sect. 4.1's "We note that"), it only adds to or joins his wording. Comments are named
by page and first words, because Word renumbers them on every save.

**Two corrections to my 11-07 suggestions.** (1) The reproducibility sentence I gave you says every seed is "recorded in
the output file that each figure reads". That is not true: the files behind Figs. 2, 3 and 5 record no seed. A corrected
sentence is on p. 15. (2) The Greenland amplification bound is 2.28, not 2.29 (p. 7). I had carried a rounding error
over from the earlier text.

# Decisions

1. **Version: v1.0 (recommended).** A first public release reads naturally as v1.0, but Ladrillo.jl already has a
   `v1.0.0` tag (2026-10-08, an older build with different land-water and paleo settings), plus `v1.1.0`, `v1.2.0` and
   `v1.3.0`. The repository has never been public, so the tags can be renamed. What I would do in the next pass:
   rename the four internal tags to `v0.1.0`–`v0.4.0`, set the package version to 1.0.0 (Project.toml, CITATION.cff,
   README), tag `v1.0.0` at the release commit, and record the mapping in both CHANGELOGs. No number changes. Text
   changes: title, Conclusions, and Code availability ("Ladrillo v1.0 (Ladrillo.jl, git tag v1.0.0)"). The other
   option is to keep v1.3, with no extra work.
2. **IGCC edition for the heat-inventory numbers.** The 91%, the α value 0.141 (Sect. 2.2.4) and the 1.11 / 1.10 /
   1.02 factors (Sect. 4.1) come from the 2024 indicators. The reference list cites only the 2025 indicators (Forster et
   al., 2026). Recommended: I rerun the diagnostic on the 2025 data in the next pass and update those numbers in the
   text. The other option is to add the 2024 edition (Forster et al., 2025) to the references.
3. **Code availability.** The text says the archive holds "the scripts that produce every figure and table".
   Ladrillo.jl ships only the Table 5 script. Recommended: I copy the figure scripts into Ladrillo.jl before the
   release. The other option is to narrow the sentence.
4. **Poinelli sentence (p. 23).** See the Sect. 4.3 item.
5. **Table 2 note 7 (carried over).** Recommended: leave 37.4 cm as is.
6. **Tony's "intermediate simplified model" framing (his reply on p. 8, carried over).** If you want it, one sentence at
   the end of the Introduction would carry it. Otherwise reply and close.

# Claude's next pass

| item | what I will do |
|---|---|
| Figures | Insert the lettered Figs. 1–4 and 6 and the joint-arm Fig. 5 from `figures/paper/`. Move Fig. 5 after the peak-and-decline paragraph, as Tony suggests, unless you object. |
| Equations | Put each equation on its own line with its number at the right: Eqs. (1)–(2), (3)–(7), (8)–(11), (12)–(14). |
| Table A1 | The four ln rows and footnote ᶜ (values from the 11-10 build). `ais_c`: "Runoff-line slope c" → "Rise of the runoff line per °C, c_R". `gis_s_high`: "(NO+NE)" → "(North and Northeast)". p. 5: "log₁₀ κ are sampled" → "ln κ are sampled". |
| Notation | "onset T_on = 4.69 K" after Eq. (11) → T_thr. L_i, L_m → 𝓛_i, 𝓛_m (L stays the e-folding length). Table A3 symbols to match. "(ais_iceflow₀)" → "(ais_iceflow0)", as in Table A1. "Eq(4)" → "Eq. (4)". "φ (Ḡ₃₀" → "φ(Ḡ₃₀". "two coefficient" → "two-coefficient". "200 year" → "200-year". One spelling of FACTS's. |
| Dashes, signs, units | En dashes in ranges (9–14, 27–56, 17–20, 20–244, 60–3200). Minus sign in "(−0.6)". "Gt/yr" and "mm/yr" → "Gt yr⁻¹" and "mm yr⁻¹". Double spaces; "( World" in Table 3 note 18. |
| References to add | Lin et al. (2026), Poinelli et al. (2026), GlaMBIE Team (2025) (cited on p. 6; only the 2024 dataset is listed), RCMIP v5.1.0 and the CMIP7 historical emissions (Sect. 3.2), NOAA STAR (product page), and Forster et al. (2025) if you choose option b in Decision 2. |
| References to fix | Morlighem et al. (2017) DOI → `10.1002/2017GL074954`. Sarofim et al. (2021) pages "11, 1–3". Rennels et al. (2022): "Catawbasam" and the release DOI. |
| Citation forms | "(Frederikse et al. 2020)" ×2 and "(Fox-Kemper et al. 2021)" → comma form. "Millan et al., 2022 estimate" → "Millan et al. (2022) estimate". "Mouginot et al. 2019 data" → "Mouginot et al. (2019)". "(CMIP6) (Eyring et al., 2016)" → "(CMIP6; Eyring et al., 2016)". "(Wong et al., 2017b; Shaffer 2014)" → "(Shaffer, 2014; Wong et al., 2017b)". |
| Runtime sentence (p. 24) | Re-measure on the Zenodo BRICK 2.0 posterior and update the numbers. Tony's wording stays. |
| Version | As in Decision 1. |

---

# Page 1: title and abstract

**Title. HAND, after Decision 1.**

> Ladrillo v1.0: a sea-level model derived from BRICK with improved 20th-century hindcasts

**Abstract. HAND.** "…constrained by observational data., Ladrillo is driven by…" → "…constrained by observational
data. Ladrillo is driven by…". The abstract is now 231 words.

# Page 2: Introduction

**"Ladrillo is derived from BRICK (…), Ladrillo and BRICK have many similarities." HAND.** The comma joins two
sentences:

> Ladrillo is derived from BRICK (Wong et al., 2017b, 2022; below, 'BRICK' refers to the model family and 'BRICK 2.0'
> to its MimiBRICK v2.0.0 release, against which Ladrillo is compared) and shares many of its features.

Optional, in the next sentence: "and a committed loss and response time at future warming levels" → "and the glacier
committed loss and response time at future warming levels".

# Page 4: Sect. 2.1

**Joint/fixed paragraph. HAND.** "driven by the FaIR ensemble-mean: : the per-year mean" → "driven by the FaIR ensemble
mean: the per-year mean". Then CLOSE Tony's "one consideration here is whether this constitutes a viable…". A possible
reply: "Projections now use the joint arm; the ensemble mean drives only the calibration and two convergence checks."

# Pages 5–6: Sect. 2.2.1 Glaciers

**Block-temperature paragraph, last sentence. HAND.** "The glacier record ends before A_b affects the drivers." does
not say why it matters. This version adds the prior-propagation note from your 11-07 notes:

> The glacier record ends before A_b affects the drivers, and the posterior of A_b stays close to its prior (Table A1).

Receipt: the Table A1 posterior medians are 2.64, 1.47 and 0.726, against prior centres of 2.50, 1.45 and 0.72.

**RGI 19 paragraph. HAND.** "Zekollari et al., 2025). ts response time" → "Zekollari et al., 2025). Its response time".

**Regrowth. HAND.** The paragraph is still split after "up to each block's". Join the two pieces and remove the double
space after "1850 ice extent."

CLOSE Tony's "I'd add these descriptions" (p. 5; they follow Eqs. 1–2) and "is this used in the model somewhere…"
(p. 6, with your reply).

# Pages 6–8: Sect. 2.2.2 Greenland

**Amplification paragraph. HAND.** "2.29 in GISTEMP" → "2.28 in GISTEMP", and "[1.51, 2.29]" → "[1.51, 2.28]". The
GISTEMP regression is 2.2847 (`outputs/gis_amp_prior.csv`); Table A1 already shows 2.28.

**Paragraph after Eqs. (3)–(7), last two sentences. HAND.** G is no longer defined there:

> …where G is GMST, A_G the sampled amplification and Ḡ₃₀ the 30-year running mean of G.

Optional, after "The calibration builds this series once with the prior-centre amplification (1.92).": "No likelihood
term depends on A_G, so its posterior matches its prior (Table A1)." Table A1 shows 1.91 (1.57–2.23) against
N(1.92, 0.32) on [1.51, 2.28].

CLOSE Tony's "not totally clear what the abbreviations refer to" (p. 6). His "I'm not totally sure how to interpret
this" (p. 8, level and tilt) is answered by the text, but his reply in the same thread ("That also seems like an
opportunity…") is Decision 6. Resolving the thread resolves both, so resolve it once you have decided.

# Pages 8–9: Sect. 2.2.3 Antarctica

**DAIS geometry paragraph. HAND.** "The seven DAIS geometry parameters (…) shared a joint prior" → "share a joint
prior". Then CLOSE Tony's "I may have edited to ruin the grammar here" and "cite frederikse?".

**Fast dynamics.** CLOSE Tony's "I'd insert your favorite MICI/MISI…". Fox-Kemper et al. (2021) is cited and his
wording stays.

**Antarctic amplification. HAND.** "raises Antarctic sea level at 2300 by by 39 cm" → "by 39 cm"; "BRICK2.0's" →
"BRICK 2.0's".

# Pages 9–10: Sects. 2.2.4 and 2.2.5

**Thermal expansion. HAND.**

- "ΔOHC is the annual change in J in FaIR's ocean heat content." → "ΔOHC is the annual change in FaIR's ocean heat
  content, in J."
- Optional simplification. The paragraph says twice that FaIR's ocean heat is Earth's total heat uptake. "FaIR's ocean
  heat content is Earth's total heat uptake, so the matching observational value divides…" → "The matching
  observational value therefore divides…".

Then CLOSE Tony's "we'll also want to caveat about mean here". The numbers in this paragraph depend on Decision 2.

**Land water. HAND.** "…minus the GlaMBIE glacier mass) which are then held constant through 2025." reads as if all of
2019–2023 were held. Replace with "…minus the GlaMBIE glacier mass); the 2023 value is held through 2025." Remove the
double space after "observations."

# Pages 10–12: Sect. 3.1 and Table 3

CLOSE Tony's "is my edit accurate?" and "does observed here mean…" (both with your replies), "similarly to above, what
exactly does this entail?" (the caption now defines offset matching), and "if in this sentence and the next you're
referring to the calibrated ladrillo model…" (p. 12; the sentence now begins "The calibrated Ladrillo model").

# Pages 13–15: Sect. 3.2

**Discrepancy paragraph (Tony's five questions, p. 14). HAND.** Four insertions answer his questions and keep his
sentences:

1. "modeled by a low-order polynomial in time" → "modeled by a linear and a quadratic term in time".
2. "The basis is orthogonalized against a constant and against the ocean-heat shape, so it can only describe structure
   that rescaling the driver cannot." →

> Both terms are orthogonalized over 1900–2025, without weighting, against a constant and against FaIR's ocean heat
> content time series, so they can only describe structure that rescaling the ocean heat content cannot.

3. "The second coefficient is centred near zero in the posterior (median 0.069 cm)" → "The second (quadratic)
   coefficient spans zero in the posterior (0.07 cm, 5–95% −0.05 to 0.20)".
4. "the first is not (0.21 cm, 5–95% 0.01–0.396 cm)" → "the first (linear) is not (0.21 cm, 5–95% 0.01 to 0.40)".

Sources: the calibrator's discrepancy basis (powers of scaled time, Gram–Schmidt with a plain inner product against a
constant and the ocean-heat shape, unit RMS) and the Table A1 rows. Then CLOSE all five.

**ρ.** CLOSE Tony's "does this mean we disallow rho = 0.99?" with your "yes". The text and Table 5 now use "<".

**Convergence paragraph. HAND.**

- "Convergence is assessed with R̂ the rank-normalized" → "Convergence is assessed with R̂, the rank-normalized".
- "ais_slope 1.06), all eight have ESS below 400 (20-244)." → "ais_slope 1.06); all eight have ESS below 400 (20–244)."

Then CLOSE Tony's "this feels out of place…" (the sentence is gone) and "and this isn't even all that crazy…". If you
want to answer the second in the text: "Only ais_runoff_Ton exceeds the looser threshold of 1.1." Cite a source for
1.1 if you add it; Gelman et al. (2013) is my recollection.

**Reproducibility. HAND (correction of my 11-07 text).** Replace "All results are reproducible: every random seed is
fixed and is recorded in the output file that each figure reads." with:

> Ladrillo's calibration and projection drivers fix every random seed, so the results can be regenerated.

The figure inputs do not record seeds (checked: `outputs/vv_model_comparison_L27.csv` behind Figs. 2 and 3, and the
joint-arm path file behind Fig. 5, have none). I can add seed provenance to the figure inputs later if you want the stronger sentence back.

# Page 15: Sect. 3.3 Verification

CLOSE Tony's "what the level and tilt and native forms are…". The text now points to Sect. 2.2.2 and Eq. (4).

# Pages 16–18: Sect. 4.1

**Broken paragraph. HAND.** "We note that" (Tony's insertion) still ends one paragraph and "the non-closure…" starts the
next. Join them.

CLOSE Tony's "this isn't actually the model we want to entertain…", "I don't recall this set of autocorrelation
coefficient tests…", and both comments on the 1.21–1.27 factors ("a little confusing because…" and "also a little
confusing…"). Tony's "they'll want panel labels on these guys" closes after the figure swap.

# Page 19: Sect. 4.2

**Component paragraph (Tony's "can these be tied more directly…"). HAND (optional), then CLOSE.** The glacier sentence
is in. Matching sentences for the other components, rechecked against the Fig. 3 data at 2300
(`outputs/vv_model_comparison_L27.csv`; the largest Antarctic difference outside the two named scenarios is +7.2 cm,
Medium):

> Ladrillo's Greenland contribution is lower than BRICK 2.0's in six scenarios (by 3–9 cm) and higher in High
> (+20 cm), where the above-threshold channel fires. Its Antarctic medians are within about 7 cm of BRICK 2.0's except in
> High-to-Low (−18 cm) and High (+31 cm). Thermal expansion, from the same module with a different α, is 1–6 cm higher
> in every scenario.

# Pages 21–22: Figs. 5–6 and the FACTS paragraph

**Fig. 5 caption. HAND.** "the FaIR ensemble mean of GMST forcing (a)" → "the FaIR ensemble-mean GMST (a)". Delete the
final "Fixed arm.": the caption already says "Joint arm", and the 0.08 cm regrowth is the joint-arm value
(`outputs/verify_magicc_regrowth_attribution_L27.csv`). Then CLOSE Tony's "these are a subset of the 7 van Vuuren et al
scenarios?" and "so is this not sampling uncertainty in the climate side…".

**FACTS paragraph. HAND.** Reply to Tony's "I didn't realize FACTS is doing that…", for example: "This is FACTS's
default; the text shows what evaluating the fit past 2100 does." Then CLOSE.

# Page 23: Sect. 4.3

**High scenarios. HAND.**

- "FACTS 56–76 cm across its workflows (relative to 2005).." → "FACTS 56–76 cm across its workflows (FACTS relative to
  2005, the others to 1995–2014)."
- End of the paragraph: "so the difference is due to the different ice-sheet modules, not the climate modules." → "so
  the difference comes from the ice-sheet modules." Tony's "Driving both Ladrillo and BRICK 2.0 using MAGICC's climate"
  stays.

Then CLOSE Tony's "should FACTS be among them?" and "one thing a reviewer… 'climate'…" (he says it is fine as is).

**Antarctic spread. HAND.** "0104 and 0.0035 in BRICK 2.0's posterior )" → "0.0104 and 0.0035 in BRICK 2.0's
posterior)", and one space in "307 cm  at 2300". Then CLOSE Tony's two comments on λ ("does this mean there is just one
constant rate parameter…" and his reply). The text now points to Sect. 2.2.3, which explains the joint draw and why λ
is not in the likelihood.

**Lin and Poinelli. DECIDE + HAND.** Grammar first: "the increase from fast dynamics in Ladrillo are not unrealistic" →
"is not unrealistic". On the clause itself, two facts a reviewer could raise:

- Poinelli's increase needs no further warming (constant 1996–2023 forcing). Ladrillo's increase at 2100 is the
  temperature-triggered λ term.
- The sizes differ. Poinelli's Thwaites total is 1.9–3.0 cm. Ladrillo's medians with and without fast dynamics differ by
  about 5 cm (SSP2-4.5) and 29 cm (SSP5-8.5) at 2100.

Options: (a, recommended) end the paragraph after "for that glacier" with "Results for a single glacier are difficult to
compare with a model that represents Antarctica as one sheet." (your 10-21 wording). (b) Keep your clause with the
grammar fix.

**Peak-and-decline. HAND (optional).** 1.83 of 8.47 cm is 22%, so "About ¾ of this difference comes from model structure
and ¼ from climate" → "About four-fifths of this difference comes from model structure and one-fifth from climate".
Then CLOSE Tony's "cite equation number(s)?" (Eqs. 1–2 are cited). His "maybe move this figure…" is in the next pass.

# Pages 23–24: Conclusions

**First paragraph.** Only the version (Decision 1). CLOSE my "Claude 10-15: on the Zenodo BRICK 2.0 posterior…"
comment; the −18 to +47 cm sentence replaced it.

**Runtime paragraph.** Next pass (re-measure). Tony's wording stays.

# Pages 35–36: back matter

**Code and data availability.** Decisions 1 and 3. Keep your placeholder comment until the release.

**Acknowledgements. HAND.** Frank Errickson is still missing. He pointed out that FaIR's ocean heat content is Earth's
total heat uptake (2026-10), which the Sect. 2.2.4 and 4.1 text now rests on.

# Optional simplifications (carried over)

- Sect. 3.3 Verification is one long paragraph. A numbered list, (i) to (iv) plus the MCMC and BRICK 2.0 checks, would
  read faster with no change in content.
- Table 3 notes 17, 19, 20 and 21 carry provenance detail (hash prefixes, fetch dates, file names). Moving it to Code
  and data availability would shorten the table.
- Sect. 2.2.2 "Two channels" and "Two basins" could be one paragraph.

# Comments after this round

Of the 44 open comments, all but four close with the items above. These stay open: your Code availability placeholder,
Tony's level-and-tilt thread until Decision 6, and his "panel labels" and "move this figure" comments, which close after
the next pass.
