# Support material for the SLEIP Phase 1 comment — verified numbers and scope triage

Written 2026-09-09. Companion to `handoff_2026-09-09_sleip_comment.md`.
**Marcus drafts the comment.** This file is numbers, scope triage, and citations only.

Draft under revision: `~/Documents/2026/PaperReviews/SLEIPreview.docx`.
**Ladrillo does not appear anywhere below** (Marcus, 2026-09-09). All illustration is BRICK 2.0 +
FACTS on FaIR vs MAGICC climate, plus SLEIP's own published numbers.

---

## 0. Deadline

**Open until 28 Oct 2026** (egusphere.copernicus.org, checked 2026-09-09). ~7 weeks. No time pressure.

---

## 1. ⭐ THE SCOPE ANSWER — the big ask costs them nothing

Marcus's constraint was "don't ask for work outside a reviewer's scope." The paper's own §2.2 and
§2 settle this in our favour:

> **"Both sets of simulations cover six SSP-RCP scenarios and their extensions out to 2300:
> SSP1-1.9, SSP1-2.6, SSP2-4.5, SSP5-3.4-OS, SSP3-7.0, and SSP5-8.5."** (§2, p.4)

"Both sets" = MAGICC-forced **and native**. The native configuration is 12 datasets and it already
contains **both members of the overshoot pair**. So:

⇒ **The native-forced overshoot penalty is computable from data they have already run.** It is a
difference between two trajectories that already exist in their archive. The ask is "add a
native-forced version of Fig. 8H", not "run a new experiment." That is the single most important
framing point for the whole comment.

Two further gifts, both letting the comment endorse rather than criticise:

- **§2.2 already states the mechanism**: "a tension can emerge when switching from native to MAGICC
  climate forcing because each emulator was calibrated in its native configuration under one set of
  forcing assumptions … this tension can lead to biases in the sea level response when running in
  the MAGICC-forced setup (Wong, 2026)." The comment is asking them to carry their own §2.2 caveat
  into §4.4, where it is currently absent.
- **§6 already proposes the deeper fix**: future phases should use "targeted sensitivity analyses …
  using stylised forcings such as pulse experiments, stepwise warming, constant warming rate,
  temperature stabilisation or **idealised overshoot profiles**." The comment can say Phase 1's own
  result is the argument for that plan — not that Phase 1 should have done it.

**Suggested split for the comment:**

| Ask | Cost to authors | Verdict |
|---|---|---|
| State the peak GSAT difference of the pair numerically | one number | **in scope** |
| Define the penalty statistic (diff-of-medians vs median-of-differences) | one clause | **in scope** |
| Native-forced Fig. 8H / penalty table | re-difference existing output | **in scope** |
| Scope the abstract + §4.2 "forcing hardly matters" claim to *levels* | one clause | **in scope** |
| Table 2: BRICK land water storage dash vs §3.1 | erratum | **in scope** |
| Say what the Farinotti / W-R volume anomaly implies | one sentence of judgement | **in scope** |
| Add a reversibility axis to the Table 2 taxonomy | new taxonomy | ask as a *limitation sentence*, not a new column |
| Re-run all 13 datasets on a second climate driver | new experiment | **out of scope — do not ask.** Point at §6 instead |

---

## 2. ⭐ Verified numbers — the overshoot *depth* is the mechanism, and it is never stated

The paper's §4.4 argument is (p.23, l.603–605):

> "their trajectories converge again around 2150 … from 2150 onwards both scenarios result in
> (almost) the same forcing on the sea level system. Any difference in sea level contributions after
> 2150 is therefore attributable **exclusively to the SSP5-3.4-OS temperature overshoot relative to
> the SSP1-2.6 response before 2150**."

That is correct as written. But it makes the penalty a function of the **pre-2150 overshoot depth**,
and **that depth is a property of MAGICC that is never stated numerically anywhere in the paper** —
it appears only as the dotted line on the right-hand axis of Fig. 8A.

### Table A — overshoot depth and post-2150 convergence

| driver / pair | peak of median ΔGSAT | at year | ΔGSAT @2150 | ΔGSAT @2300 | n |
|---|---|---|---|---|---|
| MAGICC v7.5.3, native SSP5-3.4-OS − SSP1-2.6 | **+0.659 K** | 2059 | +0.044 K | +0.042 K | 600 |
| FaIR 2.2.4 (calib 1.6.0), idealised matched pair | **+0.303 K** | 2060 | +0.035 K | +0.016 K | 841 |
| **ratio** | **2.18×** | same decade | — | — | |

**This is the sharpest way to put Marcus's bullet 1, and it splits it cleanly in two:**

- The *convergence* premise **holds in both** — residual ΔGSAT at 2150 is +0.04 K and +0.03 K
  respectively, and both stay flat to 2300. So the answer to "how closely does SSP5-3.4-OS match
  SSP1-2.6 post-2150" is **very closely, and this is not the driver-sensitive part.**
- The *depth* differs by **2.2×**, peaks in the same decade, and is the quantity the penalty
  actually scales with. So the driver-sensitivity lives entirely in the part of the experiment the
  paper does not quantify.

That distinction is worth making explicitly — it stops the comment reading as "your convergence is
sloppy", which it is not.

Reproduce: `python3 python/diag_magicc_overshoot_depth.py` (SLR-RFF-BRICK, `ladrillo-dev`).

### Table B — the penalty, in SLEIP's own metric (total GMSLR, 2300, difference of medians)

| model | climate | penalty @2300 | % of SSP1-2.6 2300 total | SLEIP's published value |
|---|---|---|---|---|
| BRICK 2.0 | **MAGICC** | **19.36 cm** | 23.9 % | BRICK = highest share, 34 % (abstract, §4.4) |
| BRICK 2.0 | **FaIR** | **5.66 cm** | 6.1 % | — (no native-forced penalty published) |
| MAGICC-SLR | MAGICC | 14.28 cm | 21.5 % | ≈13 cm, Fig. 8H |
| FACTS wf1f (IPCC-AR5 AIS) | **FaIR** | **3.11 cm** | 2.3 % | **8 cm** (MAGICC), §4.4 |
| FACTS wf2f (LARMIP-2) | FaIR | 6.19 cm | 4.8 % | not stated in text |
| FACTS wf3f (DeConto/Kopp) | **FaIR** | **10.51 cm** | 5.1 % | **29 cm** (MAGICC), §4.4 |
| FACTS wf4 (Bamber SEJ) | FaIR | 8.30 cm | 4.5 % | not stated in text |

**Climate-swap ratios (MAGICC : FaIR):** BRICK 2.0 **3.4×**; FACTS wf1f **2.6×**; FACTS wf3f **2.8×**.
All three bracket the **2.18×** depth ratio in Table A.

⭐ **The FACTS rows are the strongest evidence and use nothing of ours but a differently-forced run
of their own code.** wf1f and wf3f are the two endpoints of the paper's own "8 cm to 29 cm" range;
their workflow definitions are identical to ours (1f = `ipccar5/AIS`, 3f = `deconto21`); two
completely different Antarctic methods give the same ratio to within 0.2; and the
**1f-lowest / 3f-highest ordering is preserved**. On MAGICC's climate BRICK 2.0 also lands within
9 % of MAGICC-SLR and inside the published 8–29 cm band; on FaIR's it falls below it.

Reproduce: `python3 python/diag_sleip_metric_penalty.py`.

### ⭐ Table C — a paper-internal version of the same point, needing none of our numbers

Worth using *first*, because it cannot be dismissed on any grounds:

- **BRICK sets the top of the penalty range** — "an additional 6 % (FACTS_1f) to **34 % (BRICK)**"
  (abstract, §4.4); "BRICK projects the largest Antarctic SLR penalty with a sharp onset in 2050.
  This propagates directly into the largest total SLR difference over most of the assessed time
  horizon."
- **BRICK is also the one emulator §4.2 names as an exception to "forcing hardly matters"** — "the
  BRICK native climate variant (SNEASY) produces Antarctic ice sheet projections that differ
  markedly from its MAGICC-forced run, which is however calibrated to a different climate model
  (DOECLIM)."

⇒ The emulator that sets the upper end of the 0.1–0.3 m range is precisely the one where the paper
has already documented that the climate-forcing choice moves its Antarctic response markedly — and
the penalty is Antarctic-dominated (Fig. 8G). That is an internal inconsistency between §4.2 and
§4.4 that the authors can check in an afternoon.

---

## 3. Additional clarifications Marcus's draft does not yet have

### a. ⭐ The penalty statistic is ambiguous, and the two definitions differ by >2×

Fig. 8B: the penalty is "the vertical gap (dashed to full line) between scenario pairs" where the
lines are the **median total sea level response** ⇒ *difference of medians*.
Fig. 8H: "the **median total SLR difference** between SSP5-3.4-OS and SSP1-2.6" ⇒ reads as *median
of the paired differences*.

These are not the same statistic on a skewed distribution. On our runs:

| model / climate | difference of medians | paired median | ratio |
|---|---|---|---|
| MAGICC-SLR / MAGICC | 14.28 cm | 12.75 cm | 1.12× |
| BRICK 2.0 / MAGICC | 19.36 cm | 11.72 cm | 1.65× |
| BRICK 2.0 / FaIR | 5.66 cm | 2.57 cm | **2.20×** |

One clause fixes it. Cheapest ask in the comment and unambiguously in scope.

### b. The headline number is a median, and the penalty distribution reaches zero

Every panel of Fig. 8 is a median: C–G are single median lines with no shading, and H is explicitly
a median bar. On our MAGICC-SLR run on MAGICC's own climate, the 2300 total penalty is
**median 12.75 cm, 5th percentile −0.20 cm, 95th percentile +30.86 cm** — i.e. the lower tail of the
ensemble shows **no penalty at all**, and the upper tail more than doubles it.

⚠ Frame this as "the abstract's 0.1–0.3 m is a range **across emulators**, not a range across the
ensemble; consider saying so" — *not* as "add distributions to Fig. 8." The former is a one-clause
clarification; the latter is a re-plot request and would be annoying.

### c. Table 2 gives BRICK a dash for land water storage, but §3.1 describes BRICK's LWS

- Table 2 caption: "Dash indicates components **not included** in an emulator." BRICK's land water
  storage cell is `-`.
- §3.1: "**The land water storage component of BRICK** is based on mass balance trends between
  2003-2013 from Dieng et al. (2015). This component assumes that the mean and variance of the
  distribution of land water storage annual sea level trends remains stationary…"
- Fig. 9 caption repeats the Table 2 reading: "BRICK and SURFER do not include a land water storage
  component and are absent from that panel."

Either the dash means "not submitted as a separate component to SLEIP" (in which case the caption's
definition needs widening) or it is an error. Cheap, and the kind of thing authors are glad to catch
pre-publication. **Phrase as a question, not an accusation.**

### d. ⭐ The Wigley–Raper point is fully supported by the paper itself — drop the unpublished-work framing

Marcus's current draft attributes the W-R critique to "my own (yet to be submitted) work." That is
not necessary and it is the one line in the draft that invites "your unpublished model disagrees."
The paper states both halves of the argument already:

1. **§3.1**: "Following Wigley and Raper (2005), we take the **equilibrium temperature as equal to
   −0.15 °C (relative to pre-industrial** global mean temperature)." ⇒ the equilibrium temperature
   is below pre-industrial, so glacier loss cannot halt at any attainable GSAT. Under SSP1-1.9 and
   in the post-2150 recovery phase of the overshoot experiment this is doing visible work.
2. **§4.1**: "Most models plateau at around 0.3 m SLE from glaciers under high scenarios, overall
   consistent with the estimated total global glacier volume outside the ice sheets of approximately
   0.32 m SLE (Farinotti et al., 2019), **with BRICK and FRISIA as an exception**, which are
   calibrated against Wigley and Raper (2005) that assumed a maximum glacier SLE contribution of
   0.41 m."

⇒ The authors have **already identified** that the two W-R emulators sit outside an observational
volume constraint. They stop short of saying what it implies. That is exactly Marcus's "apply your
own judgment" theme, and it can be made purely as "you found this — please say what you think it
means," with no external work cited at all.

⚠ Note the scope: W-R glaciers are used by **BRICK and FRISIA**, not BRICK alone. Fig. 8F shows
glaciers with "a slow partial recovery (glacier growth) after the GSAT convergence in 2150" across
emulators, so the reversibility differences are already visible in their own figure.

### e. ⭐ MP25's thermal expansion is described THREE different ways, and the differences matter here

The paper describes MP25's thermal expansion parameterisation three times, incompatibly:

| location | description |
|---|---|
| §3.5 | "Thermal expansion is parameterised as a **linear function of global mean temperature**" |
| §4.3 | "parameterising thermal expansion as directly proportional to the **cumulative GSAT integral**, and thus the only emulator with a linear relationship by construction" |
| §4.4 + Table 2 footnote | "computes thermal expansion from a **direct GSAT scaling** rather than MAGICC ocean heat content" |

TE ∝ T and TE ∝ ∫T dt are different models, and the overshoot experiment is the one place the
difference is maximal: **GSAT reconverges at 2150 by construction, its integral never does.**

**Why this is not pedantry — measured, FaIR 2.2.4 (calib 1.6.0), 841 configs, medians:**

| scenario | R² of OHC on GSAT | R² of OHC on cumulative GSAT |
|---|---|---|
| SSP5-8.5 | 0.912 | 0.956 |
| SSP2-4.5 | 0.830 | 0.933 |
| SSP1-2.6 | 0.058 | 0.903 |
| idealised overshoot pair | **0.0002** | 0.884 |

In the overshoot arm, instantaneous GSAT explains **essentially none** of the OHC variance. The
relation is not merely non-linear, it is **hysteretic**: at matched GSAT, OHC on the down-leg is
**1.9–3.1×** its up-leg value (e.g. at 0.90 K, 59 vs 185 ×10²² J).

⇒ Fig. 8D is consistent with the §4.3 (integral) reading and not the §3.5 (instantaneous) one:
MP25's TE penalty peaks ~50 yr later than every other emulator and ends **~3× higher**
(≈0.038 m vs ≈0.010–0.014 m at 2300). §4.4 notes MP25 is "the exception" but does not quantify or
weigh it, while stating TE differences are "small in magnitude and tightly clustered."

**Constructive ask:** state which parameterisation MP25 uses, and note in §4.4 that the TE driver
choice is not neutral under overshoot. Second example for the "apply your own judgment" theme.

⚠ **Also relevant to §4.3's own finding.** §4.3 reports TE "increasing **sub-linearly** with
cumulative GSAT, basically reflecting the MAGICC ocean heat content response." Our κ measurement
gives the mechanism: effective ocean heat uptake efficiency κ = N/ΔGSAT is **not constant**, falling
from ~0.80 W/m²/K at 2030 to 0.07 (SSP1-2.6) / 0.19 (SSP5-8.5) by 2280, because uptake is set by the
disequilibrium F − λT, not by T. MP25's linear-in-∫T construction assumes constant κ — which is
exactly the assumption §4.3's own sub-linearity finding contradicts.

⚠ **Not verified:** (i) MAGICC's own OHC-vs-GSAT relation — our `magicc_nauels_components.csv` holds
SLR components, not OHC, so the measurements above are FaIR's; §4.3's "sub-linearly … reflecting the
MAGICC OHC response" is their statement, consistent with ours but not independently checked here.
(ii) Perrette & Mengel (2025) has not been read to settle which of the three descriptions is right.
(iii) The 0.038 / 0.010–0.014 m figures are read off Fig. 8D by eye, not from released data.

### f. ⚠⚠ TWO CORRECTIONS TO THE CURRENT DRAFT (2026-09-09 version)

**(1) ¶ on the climate driver: FaIR's NATIVE pair does not converge — it INVERTS.** The draft says
"both MAGICC and FaIR show that post-2150 there is little difference between SSP5-3.4-OS and
SSP1-2.6." Measured, FaIR 2.2.4 / calib 1.6.0, 841 cfgs, medians:

| FaIR pair | peak ΔGSAT | at | @2150 | min after 2150 | @2300 |
|---|---|---|---|---|---|
| native `ssp534over − ssp126` | +0.308 K | 2059 | **−0.073 K** | −0.087 K (2165) | −0.038 K |
| native nomarker | +0.301 K | 2061 | **−0.107 K** | −0.127 K (2164) | −0.090 K |
| idealised `ssp534overMATCH` | +0.303 K | 2060 | +0.035 K | — | +0.016 K |
| *(MAGICC, for contrast)* | *+0.659 K* | *2059* | *+0.044 K* | — | *+0.042 K* |

⇒ **The 0.30 K peak is robust across all three constructions** — quote it freely. But in FaIR's
native pair SSP5-3.4-OS ends up **cooler** than SSP1-2.6 after 2150, by up to 0.09–0.13 K. The
"little difference post-2150" clause is true of MAGICC and of our idealised pair, **not** of FaIR's
native pair. ⛔ Nicholls and Smith are both on the author list and are the people most likely to
check this.

Two honest ways out, Marcus's call:
- Say the FaIR figure comes from a **forcing-matched idealised pair** built so that post-2150
  forcing converges — which is only needed *because* FaIR's native pair inverts.
- Or drop the idealised pair and make the stronger claim from the native one: in FaIR the scenarios
  do not merely reconverge, they **cross**, so even the abstract's "returned to the SSP1-2.6 level by
  2150" premise is climate-model-dependent.

**(2) ¶ on Fig. 8B vs 8H: "though probably quite similar" is not supported.** Difference-of-medians
vs paired-median, total GMSLR @2300:

| model / climate | diff of medians | paired median | ratio |
|---|---|---|---|
| MAGICC-SLR / MAGICC | 14.28 cm | 12.75 cm | 1.12× |
| BRICK 2.0 / MAGICC | 19.36 cm | 11.72 cm | 1.65× |
| BRICK 2.0 / FaIR | 5.66 cm | 2.57 cm | **2.20×** |

They coincide only when the penalty distribution is near-symmetric. For the MICI-carrying and
threshold emulators — the ones setting the top of the 8–29 cm range — they do not.

### g. The Fig. 6 / Fig. 7 self-correction is CORRECT, and there is a number for it

The draft's instinct ("longer time with low warming gives more time for OHC to rise"), then
withdrawn on inspection, was rightly withdrawn — but the mechanism is worth stating. OHC does **not**
collapse onto a single curve against cumulative GSAT, and the residual runs *opposite* to the first
guess. FaIR medians, OHC (10²² J) at matched cumulative GSAT (K·yr from 1850):

| cumulative GSAT | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 | spread |
|---|---|---|---|---|
| 300 K·yr | 190 (2167) | 247 (2135) | 308 (2112) | 1.62× |
| 400 K·yr | 214 (2226) | 298 (2170) | 396 (2132) | **1.85×** |

The cool scenario accrues its cumulative warming slowly, near equilibrium, at collapsed κ; the hot
one accrues it fast while far from equilibrium. Cumulative GSAT cannot tell "1 K for 400 yr" from
"4 K for 100 yr", but the energy imbalance can. ⇒ The requested extra column (component SLR against
GSAT, complementing Figs. 6–7) is well motivated: **cumulative GSAT is itself an incomplete
predictor for the steric term**, not a neutral change of axis.

⚠ FaIR's OHC. SLEIP's Figs. 6–7 use MAGICC's, which we cannot check (`magicc_nauels_components.csv`
holds SLR components, not OHC).

### h. ⚠ PANEL LETTERS, and the sub-zero line in Fig. 8D

⚠ **Thermal expansion is panel 8D, not 8E.** Caption order "(C-G) … total SLR, thermal expansion,
global glaciers, Greenland ice sheet, and Antarctic ice sheet" ⇒ C total, **D thermal expansion**,
E glaciers, F Greenland, G Antarctic. Earlier drafts of this note said 8E; corrected.

**The emulator dipping below zero in Fig. 8D is ProFSea**, not MP25. Colour-matched against legend
swatch cores extracted per entry: ProFSea's core (185,132,170) vs the curve's (190,159,182),
distance 30, against ≥67 for FACTS_1e/1f and 105 for MP25. MP25 (137,70,200) stays at or above zero
throughout. Measured from the raster: depth **13 px = 0.0016 m** (gridline spacing 81 px per 0.01 m),
spanning roughly 2015–2040 and bottoming ~2025–2032. ⚠ An initial 29 px reading was the left axis'
antialiasing, not the curve.

**⛔ RETRACTED: the "ProFSea is reading out the driver's ΔOHC" explanation does not survive a
magnitude check.** ProFSea's coefficient is 0.113 m/YJ (§3.6), so a −1.6 mm excursion requires
**ΔOHC ≈ −1.42 ×10²² J**. FaIR's ΔOHC minimum on the same scenario pair is **−0.022 ×10²² J** —
**65× too small**. The FaIR sign reversal (ΔGSAT −0.0016 K in 2027, ΔOHC −0.022 ×10²² J in 2028) is
real but is not the same phenomenon and must not be offered as corroboration.

For scale: −1.4 ×10²² J is about one year of present-day global ocean heat uptake, and would need
roughly **−0.1 W/m² sustained over ~10 years**. That is not absurd for an aerosol-driven near-term
difference (SSP1-2.6 cutting SO₂ faster while SSP5-3.4-OS still tracks SSP5-8.5 to 2040) — but it is
**unverified**, it is ~65× what our FaIR setup produces, and we hold no MAGICC OHC to check it.

**⭐ THE BETTER QUESTION — the TE laws are near-identical, so the difference should not exist.**
Marcus asked whether the other emulators have integration or lag in the OHC→SLR conversion. **They
do not.** Read from §3:

| emulator | thermal expansion | Table 2 |
|---|---|---|
| ProFSea | OHC × AR6 coefficient **0.113 ± 0.013 m/YJ** | 2 |
| FRISIA | "a linear function of ocean heat content changes", **0.11 ± 0.01 m/YJ** | 2 |
| FACTS | time-invariant CMIP6 coefficients × emulated OHC | 2 |
| BRICK | "proportional to the ocean heat uptake", 2 free calibration parameters | 2 |
| MAGICC | OHC integrated across **40 hemispheric ocean layers**, layer-specific coefficients | 3 |
| SURFER | product of **layer-specific** coefficients and heat absorbed | 3 |
| MP25 | GSAT / cumulative-GSAT (not OHC) | 2* |

Only MAGICC and SURFER resolve the ocean vertically, and that is a depth decomposition rather than
a lag. **ProFSea and FRISIA state the same law with the same coefficient to within 3 %, and in the
MAGICC-forced configuration receive the same MAGICC OHC — yet only ProFSea goes negative.** That
cannot come from the TE parameterisation as described.

⇒ **Ask it as a question, claim no mechanism:** two emulators with near-identical stated thermal
expansion laws and a common OHC input give visibly different TE responses in the same experiment —
what differs? Surfacing exactly this is what SLEIP is for. Candidates we could not distinguish:
different OHC depth range or baselining, unpaired Monte Carlo sampling between the two scenario runs
(ProFSea draws 10⁶ members), or a historical constraint applied per-scenario.

⚠ Separately, §4.2 already notes a *different* negative TE effect: "MAGICC-SLR's multi-layer ocean
model produces slightly negative thermosteric contributions in later time periods under … SSP5-3.4-OS
… Simpler emulators do not capture this reversal." That is 2170–2300, not the 2020s dip — do not
conflate them.

### i. ⭐ SLEIP's GSAT reconvergence is COINCIDENTAL, and that is the stronger framing

The pair is not constructed to match. §4.4: "We only look at one overshoot scenario pair, as SSP1-2.6
and SSP5-3.4-OS are the only scenarios with GSAT convergence in the SSP-RCP set" — they *selected*
the pair that happens to converge. The scenarios were designed to different 2100 forcing levels
(3.4 vs 2.6 W/m²), so any GSAT reconvergence arrives later, through the post-2100 extensions.

⇒ **Both the depth AND the reconvergence are emergent properties of (these two scenarios) × (MAGICC).**
Our FaIR run is the demonstration: the same two scenarios in a different climate model do not
reconverge, they **cross** (−0.073 K at 2150, min −0.087 K at 2165).

⇒ **`ssp534overMATCH` should NOT appear in the review comment** (Marcus, 2026-09-09). It is a bespoke
construction for precise experiments; explaining it in a comment costs more than it buys, and the
native pair makes the point better. Reserve it for controlled work. Supersedes the earlier suggestion
that the comment might disclose the idealised pair — the native-pair framing replaces it entirely.

⇒ This also strengthens §6's own proposal for "idealised overshoot profiles" in Phase 2: relying on a
coincidental convergence in one scenario pair is precisely why a designed overshoot is needed.

### j. DRAFT REVIEW (2026-09-09, second pass) — accuracy verdict

**All eleven page/line citations verified correct** by mapping each printed line marker to its page:
155→p.6, 200→p.8, 325→p.11, 370→p.13, 440→p.15, 477→p.18, 508→p.19, 530→p.20, 547→p.21, 610→p.24,
633→p.25. All quoted passages are verbatim. The 0.30 K / 0.66 K overshoot depths are correct
(FaIR native 0.308, MAGICC 0.659).

Fixes needed:
1. ¶ on thermal expansion: **"the M25 model" → "MP25"**.
2. ¶4 of the opening: "of great value to the community **if** certain component modules could be
   identified" — missing "if".
3. The AIS paragraph opens "in contrast" — but the new Thermal Expansion section now sits between it
   and the Wigley-Raper paragraph it was contrasting with. Needs re-anchoring, and a capital.
4. Fig. 8B/8H ¶: **"though probably quite similar" is not supported.** Our runs: 1.12× (MAGICC-SLR),
   1.65× (BRICK on MAGICC), **2.20×** (BRICK on FaIR). Suggest "these can differ materially where the
   distribution is skewed, as it is for the MICI-carrying workflows."
5. TE ¶: "layer-specific … (as in MAGICC)" — **SURFER also uses layer-specific coefficients**
   (3 ocean layers, GLODAPv2.2016b-derived, p.14 line ~405).
6. W-R ¶: "will continue melting at a non-zero rate" — add "as long as glacier volume remains"; the
   W-R rate scales with the remaining volume fraction as well as with T − T_eq.
7. ⭐ **The climate-driver ask does not yet say the data already exists.** §2, p.4 line 105–107:
   "Both sets of simulations cover six SSP-RCP scenarios and their extensions out to 2300" — "both
   sets" = MAGICC-forced AND native, so the requested native-forced table needs **no new runs**.
   Saying so is what keeps the biggest ask inside reviewer scope.
8. ProFSea ¶: strengthen from "worth a sentence explaining" to the specific diagnostic — **FRISIA
   states the same law with the same coefficient (0.11 vs 0.113 m/YJ) and receives the same MAGICC
   OHC, yet does not dip.** Claim no mechanism (see §h).

### k. NEW COMMENT CANDIDATES from a full read, ranked

**1. ⭐⭐ SURFER fails the historical check yet still sets p-box bounds.** Four paper-internal facts:
p.30 line ~725 "SURFER is an exception: its total sea level trajectory runs outside the observational
range"; Table 6 gives SURFER **5.08 mm/yr** for 2006–2025 against Forster et al. (2026) 3.67 (SLEIP
mean 3.82); §5 calls SURFER and BRICK "clear outliers" for historical Antarctic contribution; and
§3.7 (p.14, line ~406) concedes SURFER's own structural bias — "all radiative imbalance is absorbed
by the ocean, leading to some overestimation of thermosteric rise on centennial timescales". Against
that, §4.5 (p.26, line ~656) states "we do not differentiate between these confidence levels and
reflect all participating emulator components within one p-box", and the p-box is the **minimum 17th
/ maximum 83rd percentile across models** — so a single emulator sets each bound.
⇒ Ask: should emulators that fail the historical check be flagged, down-weighted, or at least should
the paper report **which** emulator sets each p-box bound? Squarely the "apply your own judgment"
theme, and grounded entirely in their own numbers.

**2. ⭐⭐ The ensemble-combination rule is never stated.** MAGICC supplies **600 members** (§2.1);
FACTS uses **2,000 samples per workflow** (p.10, line ~282); ProFSea draws **1,000,000 members**
(p.13, line 380); FRISIA runs its own Monte Carlo; BRICK a Bayesian posterior. The paper never says
how the 600 climate members are combined with each emulator's own parameter ensemble — paired,
crossed, or independently drawn. That determines what every percentile and p-box bound means, whether
they are comparable across emulators with ensembles differing by 500×, and **whether Fig. 8's
overshoot penalty is a paired difference** — which is the same question as the 8B/8H definition and a
candidate explanation for the ProFSea dip. One sentence in §2 fixes it.

**3. ⭐ p.28 line 696–698 is the strongest form of the claim being challenged** — "Native-climate-
forcing p-box projections are generally in close agreement with the MAGICC-forced results …
suggesting that sea level process uncertainty rather than climate modelling uncertainty mainly spans
the overall **projection envelope**." Worth citing alongside p.15 line 440: it is a statement about
the envelope, which §4.1 attributes to AIS structural spread, and it cannot license a conclusion
about a scenario *difference*. Best single anchor for the "add 'for MAGICC' throughout" instinct.

**4. ⭐ SURFER's glacier sea level potential is 0.5 m** (p.14, line 410) — larger than the 0.41 m the
paper flags for BRICK/FRISIA and well above Farinotti's ~0.32 m — yet §4.1 names only BRICK and
FRISIA as exceptions. Either SURFER never approaches its potential, or the exception list is
incomplete. Strengthens the glacier paragraph: the volume-constraint issue is broader than W-R.

**5. Table 6: Forster et al. (2026) is quoted as 3.67 ± 2.47 mm/yr.** ±2.47 on 3.67 is very wide for
a satellite-era GMSL rate. Worth asking whether that is the intended quantity and interval — as
printed, essentially every emulator passes, so the comparison has little power.
⚠ We have NOT checked Forster et al. (2026); ask, do not assert.

**6. Only 5 of 7 emulators have historical simulations** — Table 6 gives FACTS a 2005 start and
ProFSea 2007, and §5 evaluates BRICK, FRISIA, MAGICC, SURFER and MP25. So two emulators that
contribute to every p-box are never historically evaluated. Worth one sentence, and it compounds #1.

**7. (minor) Land water storage socioeconomics are not harmonised.** MAGICC-SLR adopts "the SSP2
(medium population growth) trajectory throughout, applied uniformly across all climate scenarios";
ProFSea takes AR6 under **SSP3-7.0** for all scenarios; FRISIA and MP25 scale to IIASA population.
Climate-independent LWS cancels in the overshoot penalty (our MAGICC-SLR run gives exactly 0.00) but
not in the p-boxes, where LWS reaches 0.08–0.12 m at 2300. The protocol harmonised the climate driver
but not the socioeconomic one; worth stating.

### l. THIRD-PASS CHECK (2026-09-09) — citations verified; SURFER glaciers MEASURED

New citations all verified: p.28 l.696 (verbatim), p.14 l.409–410, p.30 l.724, **p.5 l.122**,
p.10 l.282, p.18 l.474–480. The Forster check is the reviewer's own and is right: Table 11 gives
3.66 [3.42–3.92] ≈ ±0.25 vs SLEIP's ±2.47, a factor of ~10, with central values agreeing
(3.66 vs 3.67) — only the interval is wrong.

⛔ **A p-box argument against the SURFER-glacier point was raised in session and WITHDRAWN.** The
p.18 sentence attributes the BRICK/FRISIA exception to W-R having "**assumed** a maximum glacier SLE
contribution of 0.41 m", i.e. it compares an ASSUMED RESERVOIR against Farinotti's ~0.32 m volume
estimate. SURFER's 0.5 m is the same kind of quantity. Arguing from the p-box confused a model
POTENTIAL with a projected PLATEAU — the very conflation being alleged. Marcus was right.

**Measured from Fig. 4** (SSP5-8.5, glaciers, 2300; whisker ranges; gridline calibration 27 px per
0.10 m):

| emulator | range (m) |
|---|---|
| BRICK | 0.233 – **0.448** |
| FRISIA | 0.341 – 0.374 |
| **SURFER** | **0.322 – 0.326** (a flat line ≈ 0.324; deterministic) |
| FACTS 1f–3f, 4 | 0.311 – 0.315 |
| MAGICC | 0.241 – 0.333 |
| MP25 | 0.233 – 0.322 |
| ProFSea | 0.148 – 0.315 |

⇒ **The sharpest form of the point.** SURFER assumes a reservoir **56 % larger than Farinotti**
(0.5 vs 0.32 m) yet realises only ~0.324 m by 2300 — its 200-yr relaxation timescale means the
assumption is **latent, not binding, at this horizon**. But SURFER is explicitly built for
"timescales from decades to millions of years", so it would bind on the horizons it targets. Ask why
the assumed-reservoir comparison is applied to W-R and not to SURFER — while noting SURFER's
realised 2300 value sits at Farinotti, so it is not an exception to the *plateau* statement.

⭐ **Bonus for the same paragraph: BRICK's upper tail reaches ~0.448 m — above W-R's own 0.41 m
assumed maximum**, because §3.1 makes **initial glacier volume one of six uncertain calibrated
parameters**. So "W-R assumed 0.41 m" does not bound BRICK; ~40 % above Farinotti's central estimate
is reachable. Worth asking whether that is intended.

### m. THE P-BOX AND THE FACTS GROUPING — answering "does it depend on the grouping?"

**A bound is always set by exactly one contributor** — that is what min/max means, and no grouping
changes it. What the grouping changes is *how many candidates compete* and hence *how wide the
p-box is*. §4.5 groups FACTS per component, so the number of contributors differs by component:

| component | non-FACTS | FACTS groups | total contributors |
|---|---|---|---|
| thermal expansion | 6 | 1 (shared sterodynamic module) | **7** |
| global glaciers | 6 | 2 (1e–3e; 1f–3f, 4) | **8** |
| Greenland | 6 | 3 (1e–3e; 1f–3f; 4) | **9** |
| **Antarctic** | 6 | **5** (1e; 1f; 2e–f; 3e–f; 4) | **11** |
| land water storage | 4 (BRICK, SURFER absent) | 1 | **5** |

⭐ **The consequence is a genuine artefact: p-box width is monotone in the number of contributors.**
Splitting FACTS into 5 AIS groups gives a *wider* AIS p-box than pooling them into 1 would — the max
over five group-83rds is ≥ the 83rd of the pooled mixture, and the min over five ≤ the pooled 17th.
So the AIS p-box (11 contributors) is structurally predisposed to be wider than thermal expansion (7)
or land water storage (5), **independent of any true difference in uncertainty** — and AIS is exactly
the component the paper says dominates the envelope through structural diversity. Cross-component
comparisons of p-box width are therefore not like-for-like.

Conversely, had all seven workflows counted separately everywhere, FACTS alone would supply 7 of 13
candidates and could plausibly set both bounds of every component. The grouping is what prevents
that — but it is a judgment call that directly determines the published ranges, and the paper never
reports **which contributor sets which bound**. §4.5 also concedes the grouping "introduces a minor
inconsistency for the number of total SLR p-box estimates" without saying what the inconsistency is.

⇒ Three cheap asks: state the number of contributions entering each component p-box; say which
contribution sets each bound; and explain the acknowledged total-SLR inconsistency.

### n. SUBMISSION CHECK (2026-09-09, final draft)

**Verdict: ready.** Every citation in the final draft has been verified against the PDF; every quote
is verbatim; every number traces to a measurement in this note. The p-box paragraph is accurate —
it says "Table p-boxes" (correctly distinguishing them from the Fig. 3/4 boxplots) and "min and max
p17 and p83", which matches Table 3's own header `p-box: mean p50 (min p17 - max p83)`.

Mechanical fixes only:
1. "this particulare 0.1 to 0.3 range" → **particular**
2. The BRICK parenthetical "(Also… " **never closes** — add ")"
3. "make it clear that this it is a result" → stray **"it"**
4. "each emulators set" → **emulator's**
5. AIS paragraph opens lower-case "in contrast"
6. "3.66[3.42to3.92]" → spacing

**One free strengthening.** The BRICK parenthetical hedges "if it is an adjustable parameter". It
demonstrably is, and the citation is the **very next sentence** after the line already cited:
**p.8, line ~201** — "BRICK's glacier component has six uncertain parameters, including the
proportionality constant, **initial glacier volume**, and exponent in the power law relationship".
Our Fig. 4 measurement corroborates the asymmetry: FRISIA's SSP5-8.5 whisker is 0.341–0.374 (inside
the 0.41 m W-R ceiling) while BRICK's is 0.230–0.456 (through it) — consistent with BRICK sampling
the initial volume and FRISIA fixing it.

⚠ **One residual risk, Marcus's call (he has kept the "another exception" framing).** SURFER's
*realised* glacier contribution at 2300 under SSP5-8.5 is **0.322–0.326 m** — i.e. at Farinotti.
Couplet (SURFER, on the author list) can therefore reply "SURFER does not exceed 0.32 m; the 0.5 m
reservoir is never approached." Half a sentence preempts it: the concern is the assumed reservoir on
the long timescales SURFER targets, not its 2300 value.

### o. FINAL VERSION — verified end to end (2026-09-09)

All six mechanical fixes applied. Two substantive improvements the reviewer made himself:
- The BRICK parenthetical now asserts "**because** it is an adjustable parameter" rather than "if".
- The SURFER ask is now scoped "**in terms of total meltable ice available** (and 0.5 m is even
  further from 0.32)" — which closes the rebuttal risk in §n: the exception is explicitly about the
  reservoir, not the realised 2300 plateau, so SURFER's actual 0.322–0.326 m is no longer a counter.

**The last unverified citation now checks out.** p.2, lines 65–68 reads: "Emulators used in IPCC AR6,
which were assembled in the Framework for Assessing Changes To Sea-level (FACTS), **however** differ
substantially in their capacity to project longer term SLR **beyond**, with some methods being
incapable of projecting beyond their 2100 training horizon". Both observations are right — the
"however" is stranded mid-sentence, and "beyond" has no object.

⇒ **Every citation in the review has now been checked against the PDF.** Remaining: one grammar nit
("but because it is an adjustable parameter **then** there will exist" — drop "then") and an optional
six-word citation for the adjustable-parameter claim (**p.8, line ~201**, "six uncertain parameters,
including the proportionality constant, initial glacier volume, and exponent").

---

## 4. ⛔ Guardrails — things the comment must not say

1. ⛔⛔ **Never assert MAGICC's overshoot depth is wrong.** Which of MAGICC/FaIR is right on this pair
   is unresolved on our side, and `magicc_colder_than_fair_2300` records MAGICC running 0.38–0.93 K
   colder at 2300 on declining pathways with that behaviour explicitly unchecked. The claim is that
   the penalty is **conditional on** the driver, never that the driver is wrong.
2. ⛔ **Our FaIR pair is the idealised `ssp534overMATCH`** — `ERF_126 + max(ERF_534 − ERF_126, 0)`,
   built in forcing space because FaIR's *native* pair inverts after 2150. **Never call it
   SSP5-3.4-OS.** Post-convergence residuals are close (+0.044 vs +0.035 K @2150) so the pairs are
   comparable, but they are not identically constructed — say so in the comment.
3. ⛔ The 2.18× therefore **mixes a forcing-pathway difference with a climate-response difference**;
   it is not a clean statement about FaIR's vs MAGICC's climate sensitivity. Describe it as "on a
   comparably-converging pair, the overshoot is half as deep," not "FaIR responds half as much."
4. ⛔ **Do not generalise to "climate forcing dominates."** A climate-swap share is a property of the
   **quantity**, not of the model: the same BRICK 2.0 climate swap moves the pulse H/VL ratio by only
   16 % — module-dominated, the opposite verdict (`climate_swap_share_is_per_quantity`). The claim is
   scoped to the *level overshoot penalty*.
5. ⚠ **FACTS on MAGICC's climate is RUNNABLE but NOT RUN by us.** The FACTS-on-MAGICC column in
   Table B is **their** published number, ours is FaIR-forced. Ours is n = 200 with our module
   builds; theirs is their build and sample size. **Like-for-like on workflow definition, not on
   build** — state that.
6. ⚠ **Do not claim the whole 8–29 cm range would collapse under a different driver.** Our evidence
   is two BRICK-lineage models plus FACTS; non-threshold emulators (ProFSea, MP25, thermal expansion
   generally) should amplify far less.
7. ⚠ BRICK 2.0 on MAGICC's climate at 19.36 cm is **inside** the 8–29 cm band; on FaIR's at 5.66 cm it
   is **below** it. Both statements are needed — quoting only one is the argument.

---

## 5. Code change made in this session

`python/diag_magicc_overshoot_depth.py` carried `OUR_PEAK_EXCESS_K = 0.311`, a value **typed from
`note_2026-09-02`** directly beneath a comment reading "our own matched-pair numbers are READ, never
retyped." It had drifted: the live value computed from the FaIR GMST cubes is **+0.303 K**
(841 configs). The handoff quotes a third value, 0.308 K / 2.14×.

Patched to compute peak-of-median and the 2150/2300 residuals from
`data/observations/fair_cube_gmst_{ssp534overMATCH,ssp126_nomarker}_raw.csv`. The ratio is now
**2.18×**, computed, not 2.12× or 2.14×.

⇒ **Use 2.18× and +0.303 K in the comment.** The 0.308/0.311 values in the handoff and in any
earlier note are superseded.

---

## 6. Still not done (unchanged from the handoff)

1. **Zenodo `10.5281/zenodo.21027187` has never been downloaded.** It holds their per-emulator
   output. It would give the exact per-emulator penalties instead of the 8/29 endpoints, and would
   settle whether a native-forced penalty is computable from what they released — which would let
   the comment say "we checked, and it is" rather than inferring it from §2.
2. **Nobody has checked FRISIA's native FaIR (2.1.1, calib 1.1.0) or FACTS's native FaIR (v1.6.4,
   AR6-calibrated) against MAGICC on this pair.** If their native FaIR versions give a *deeper*
   overshoot than our 2.2.4/calib 1.6.0, §2 above weakens materially. ⭐ **This is the most likely
   way the argument is wrong, it is checkable from the Zenodo release, and it should be checked
   before filing.**
3. FACTS on MAGICC's climate for the overshoot pair — runnable, not run.
