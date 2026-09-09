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

⇒ Fig. 8E is consistent with the §4.3 (integral) reading and not the §3.5 (instantaneous) one:
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
(iii) The 0.038 / 0.010–0.014 m figures are read off Fig. 8E by eye, not from released data.

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
