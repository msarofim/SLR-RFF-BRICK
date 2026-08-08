# Memo 2026-08-08 — Geometry-drift literature basis: transient-physics version has weak legs; but the hunt surfaced a VERIFIED scope mismatch (uncharted ice) that covers most of the century-integral gap

**Context.** Marcus (2026-08-08, post-D1b): T5c rejected; T5d acceptable; "look into the
geometry-drift to see if we can find a literature basis." All citations below were
verified against primary sources (research-agent dossier, this session); quotes <25 words.
The gap to explain: the anchored D1 structure under-melts 1850–2020 by ~50 mm
(model 57 vs target 107 mm), all pre-2000; t5d's fitted rate bias was δ=+0.69 mm/yr
over 1900–1960 (≈41 mm), 2.3σ of the original Roe-motivated prior sd 0.30.

## 1. Mechanism A — state-dependent response times (geometry-drift proper): PARK IT

Verified support that response times are geometry- and state-dependent:

- Jóhannesson, Raymond & Waddington 1989 (J. Glaciol. 35(121), 355–369): volume response
  time τ = h/(−ḃ_t); "can be substantially less than the 10²–10³ years commonly
  considered to be theoretically expected."
- Christian, Koutnik & Roe 2018 (J. Glaciol. 64(246), doi:10.1017/jog.2018.57): "Most
  mountain glaciers have response times between ~10 and 100 years"; τ>50 yr glaciers
  "substantially out of equilibrium today."
- Zekollari, Huss & Farinotti 2020 (GRL 47, doi:10.1029/2019GL085578): Alps mean response
  time 50 ± 28 yr, controlled primarily by SLOPE; imbalance 35% (2001) → 44% (2010).
- GlacierMIP3 (Zekollari et al. 2025 Science, doi:10.1126/science.adu4675): response
  timescale correlates with slope (r = −0.89); "Under higher warming levels (above
  +1.5°C), all regions equilibrate faster." NB the paper's headline response times are
  **80%-response** times; our pipeline uses the regchar −50% columns (no bug — but don't
  compare our τ50s to the paper's main-text numbers).

**Why it fails as a usable mechanism:** for early-20th-century LIA-extended geometries
the DIRECTION is ambiguous — low-elevation termini raise |ḃ_t| (shorter τ, JRW) but the
extended low-slope valley tongues and larger thickness push the other way (longer τ, per
the slope control in Zekollari 2020/2025) — and **no paper quantifies early-century
response times globally** (closest found: Zekollari, Fürst & Huybrechts 2014 model a
single glacier, Morteratsch, from the LIA). There is no defensible prior to put on a
κ(t)/geometry-drift term. Recommendation: park unless a quantitative source emerges.

## 2. Mechanism B — inventory-scope drift (uncharted/vanished ice): STRONG, VERIFIED, QUANTIFIED

- **Parkes & Marzeion 2018** (Nature 563, 551–554, doi:10.1038/s41586-018-0687-9):
  glaciers missing from present inventories + glaciers that disappeared before 2015
  contributed **16.7–48.0 mm SLE over 1901–2015** (missing 12.3–42.7; disappeared
  4.4–5.3), i.e. "between 0.17 and 0.53 millimetres of SLE per year", framed against the
  ~0.5 mm/yr 1901–1990 GMSL budget gap. Explicitly absent from inventory-based models:
  estimates "rely on the analysis of glacier inventory data, which are known to
  undersample the smallest glacier size classes."
- **The linchpin — our target includes it: PRIMARY-SOURCE CONFIRMED** (Frederikse et al.
  2020, Nature 584, doi:10.1038/s41586-020-2591-3, Methods "Contemporary mass
  redistribution", from Marcus's PDF `ClaudeDocs/Papers/Frederikse.2020.s41586-020-2591-3.pdf`):
  "We account for missing (owing to their relatively small size) and disappeared
  glaciers using a previous estimate [ref 16 = Parkes & Marzeion 2018, confirmed in the
  reference list]. ... For each ensemble member, we uniformly sample between the upper-
  and lower-bound estimates." Uniform sampling in [16.7, 48.0] mm ⇒ the ensemble-mean
  target carries ≈ **32 mm** of uncharted melt (uniform sd ≈ 9 mm) — a sharper central
  number for the D1c prior than the raw bounds. Frederikse's regionalization rule is
  also stated: the uncharted contribution "can be scaled by the regional relative
  contribution from the large glaciers as recognized by RGI" — which resolves the
  excl-r5 partition sub-decision by adopting their own convention (scale by regional
  melt shares).
- **Consequence:** the `recalib_targets_ext.csv` GSIC series (Frederikse-based to 2018)
  contains 17–48 mm of 20th-century melt from ice that is STRUCTURALLY OUTSIDE the
  model's V = 0.290 present-RGI stock (and outside GlacierMIP3's committed/response-time
  data). The model-target century-integral gap of ~50 mm is therefore substantially a
  **bookkeeping mismatch, not a physics failure**. This also explains why it was
  topology-invariant in D1b — no rearrangement of modeled stock can produce melt from
  unmodeled stock.
- Sizing: 17–48 mm against the ~50 mm gap; against t5d's fitted need (δ=0.69 mm/yr
  1900–1960), the P&M rate 0.17–0.53 covers ~25–75%, leaving a residual δ of
  ~0.16–0.52 mm/yr — within ~0.5–1.7σ of the ORIGINAL Roe prior (no widening needed at
  the generous end).

## 2b. Two additional target-provenance facts from the Frederikse Methods (same page)

1. **Pre-1961 target flow is PURE Marzeion-2015 model output** (+ the uncharted add-on):
   the glacier component mixes two estimates — the obs-forced global glacier model
   (ref 18 = Marzeion, Leclercq, Cogley & Jarosch 2015, Cryosphere 9, 2399–2404) and the
   in-situ Zemp et al. 2019 series — "For each ensemble member, we randomly choose
   between the two estimates. Before 1961, each member uses the estimates from the first
   estimate." So the T5d segment (1900–1960) coincides EXACTLY with the pure-M15 window:
   the T5D_SEG_END = 1960 choice is now provenance-motivated, not arbitrary, and the Roe
   critique applies undiluted precisely there.
2. **The historical target contains NO r19 melt:** "the mass balance of [Antarctica's]
   peripheral glaciers is very uncertain ... Therefore, we assume no mass loss from the
   Antarctic peripheral glaciers." (Greenland peripherals go to the ice-sheet component,
   consistent with our r5-in-GIS treatment.) Our model's near-inert historical SLOW/r19
   (D1: 0.00–0.02 mm/yr pre-2000) is therefore CONSISTENT with the target's own
   convention — and the sub-decision-H historical split should assign r19 ≈ 0 of the
   1850–2000 target melt (the Hugonnet-share default gave its block 36%; D1b's h-scan
   showed this is shallow, but D1c's a_b bookkeeping should adopt r19≈0 for
   consistency). NB the post-2000 GlaMBIE splice DOES include r19 (~0.06 mm/yr) — a
   small, documented scope seam at the splice year.

## 3. The T5d side is also now better-armed (Roe critique verified, with specifics)

Roe, Christian & Marzeion 2021 (The Cryosphere 15, 1889–1905,
doi:10.5194/tc-15-1889-2021), Sect. 5: the Marzeion-lineage reconstruction used a
mass-turnover timescale "rather than the Jóhannesson et al. (1989) geometric timescale"
(response times "larger than is probably correct"); the t* equilibrium-year values "were
extrapolated to all other glaciers, irrespective of their geometry"; and the implied
natural-case sustained deficit "requires an ongoing warming trend, which is not seen in
the naturally forced model simulations." Their attribution: "the central estimate of the
magnitude of the anthropogenic mass loss is essentially 100 % of the observed mass loss"
— vs Marzeion et al. 2014 (Science 345, doi:10.1126/science.1254702): 25 ± 35%
anthropogenic 1851–2010 (69 ± 24% for 1991–2010). The T5d prior width can honestly span
this live disagreement about post-LIA adjustment.

Caveat to carry: Leclercq, Oerlemans & Cogley 2011 (Surv. Geophys. 32, 519–535,
doi:10.1007/s10712-011-9121-7; totals 8.4 ± 2.1 cm SLE 1800–2005) is length-record-based
and method-independent of Marzeion-2015 — an independent reconstruction with (likely)
high early rates caps how much can be blamed on M15 artifacts alone; but its 349 length
records are of SURVIVING glaciers, so it too under-samples the vanished ice. (Its
early-century RATE could not be verified from accessible text — do not quote one.)
Leclercq also underpins our A2b S(1900) = 20 ± 9 mm constraint.

## 4. Proposed next cell — D1c (NOT started; Marcus to green-light)

ANCH structure and anchors UNCHANGED (they pass all 4 gates), plus an **exogenous
uncharted-ice melt term** on the model side of the flow/level comparison:
F_unch(t) with the P&M 2018 published magnitude as the PRIOR — simplest form a declining
source integrating to U ~ [17, 48] mm over 1901–2015 (shape: P&M time series if
extractable, else exponential decay with scale fit inside the prior), entering the
likelihood only (no change to stock, S_eq, transient, inventory gate, or projections —
uncharted ice is exhausted/excluded going forward, so gates and spread are untouched by
construction). Optional small T5d δ retained with the ORIGINAL prior (sd 0.30).
Pre-registered criteria unchanged. Prediction to falsify: ANCH + U at the P&M central
brings the flow-window deficit inside tol without δ exceeding ~1σ.

Bookkeeping notes for D1c (updated with the Methods in hand): (i) prior sharpened —
Frederikse samples UNIFORMLY in the P&M bounds, so the target's expected uncharted
content is ≈32 mm (uniform sd ≈9 mm) over 1901–2015; use U ~ that distribution, not the
raw bounds; (ii) apply F_unch over the Frederikse-sourced years (to the ~2019 GlaMBIE
splice; P&M's rate is small by then; sensitivity: hard stop 2000); (iii) excl-r5 share
resolved by Frederikse's own regionalization rule (scale by regional RGI melt shares);
(iv) consistency fixes to the anchor bookkeeping: subtract the uncharted part from the
target melt BEFORE the sub-decision-H split, and set r19's share of the 1850–2000
target melt ≈ 0 (per §2b.2) — both small, both now provenance-grounded.
