# Phase-2 calibration — pre-run summary for Marcus sign-off (2026-07-20)

Everything below is **wired and smoke-tested but NOT launched**. The 4×2M production run
(~4.5 h) waits on your sign-off on the flagged numbers. Companion to
`handoff_2026-07-19_brick_fm_improvement_roadmap.md` (§5 decisions) and the acceptance README
`data/MimiBRICK/README_brick_mengel_ext_acceptance.md`.

## What's already done (reversible, committed `a954701`)

| Item | State |
|---|---|
| **M1** accept v-next on the deliverable | DONE — `--accept-slr` gate, canonical `parameters_subsample_brick_mengel_ext.csv` regenerated, README written |
| **A3** relabel Frederikse file + audit weight scripts | DONE — the "Dangendorf weights" were Frederikse weights |
| **M3 pre-check** real Dangendorf fetched + tension quantified | DONE — see below |
| **A2/A4/A5/A6** calibration changes | WIRED into `calibrate_mcmc_ext.jl`, 35→39 params, smoke-tested |

## The 39-param phase-2 model (was 35)

| Change | What it does | Pinned number | Sign-off? |
|---|---|---|---|
| **A2** free λ, γ, κ | propagate fast-dynamics uncertainty; de-bias hot medoid | paleo marginals: λ 0.0104±0.0036, γ 2.79±0.93, κ 0.0656±0.0135 | prior already exists — no |
| **A4** runoff line → (T_on, c) | kill the r=0.9997 h0/c degeneracy; fix +0.62 °C onset | paleo T_on −15.64±5.54 (onset ≈ +2.3 °C GMST), r(T_on,c)=+0.64 | T_on prior — **confirm** |
| **A5** SMB term vs Rignot | break the 34:1 SMB−discharge input–output degeneracy | **1863 ± 118 Gt/yr** (2098×0.888; medoid gives 2389, z=4.45) | **σ choice** |
| **A6** GMST→AIS map = amp | remove ~26%-high equilibrium map; de-bias the pulse | **amp ~ N(0.95, 0.10)** (CMIP6 PAI1, Xie 2022) | **σ choice** |

### A5 σ — the one number I'd most like you to confirm
- Central **1863 Gt/yr** = Rignot 2019 SMB 2098 area-scaled ×0.888 (grounded-AIS 12.295e6 km²
  → DAIS disc 10.92e6 km²). You already chose Rignot as the central.
- σ options: **118** (Rignot's own ±133 area-scaled; the current default, looser/safer) vs
  **~83** (Mottram 2021 5-RCM ensemble ±94 area-scaled; tighter, pulls harder — the medoid is
  already z=4.45, Mottram σ makes it z≈6.3). I set **118**. Say if you want Mottram's tighter σ.
- Sanity: the target is *interior* to the existing tension (geometry paleo prior wants
  precip0→~1000 Gt/yr, the SLR-fit medoid wants 2389), so the term anchors precip0 to a
  physical intermediate rather than fighting the SLR fit. Healthy.

### A6 σ — you chose "CMIP6-derived σ"; here's the honesty caveat
- Xie et al. 2022 (Sci Rep 12:16548) PAI1 over the AIS: 0.88 / **0.95** / 0.97 / 1.03 for
  SSP1-2.6 / **SSP2-4.5** / SSP3-7.0 / SSP5-8.5. **The paper publishes NO inter-model sd.**
- I could not retrieve a verified inter-model spread from a second source (Sun et al. 2025 GRL
  returned HTTP 403; I declined to fabricate one). So the σ=0.10 I set is **the scenario range
  plus structural headroom**, not a literal CMIP6 inter-model sd. It spans SSP1-2.6→above the
  old equilibrium value without re-admitting 1.196 (which sits at +2.45σ). If you want a
  literal inter-model sd, I need a source you trust or your emergency-constraint judgement.
- This is the **biggest headline-mover** — amp 0.95 delays threshold crossing (crossing GMST
  rises from ~2.4 to ~3.0 °C), so it could move "82% crossed by 2100" to a minority. Bias
  direction is correct (transient < equilibrium), but the magnitude is what shifts the result.

## M3 — the total-term decision, now with numbers

You said Dangendorf is a big improvement but worried about inconsistency with the (Frederikse)
components. The tension diagnostic (`outputs/diag_dangendorf_vs_frederikse.png`) addresses that
worry directly, and it's smaller than feared:

- Dangendorf sits **inside** Frederikse's weighted 5–95% at **every** trend window.
- Mid-century (1930–1970): D 1.44 vs F 1.85 mm/yr — 6.8th percentile of F's ensemble, z=−1.54.
  Real, but bounded (not outside the components' own spread).
- Satellite era (1993–2018): D 3.03 vs F 3.36; **altimetry is 2.86** — Dangendorf agrees with
  altimetry *better* than Frederikse does.
- Year-by-year: 11/119 yr outside F's 5–95% band (≈ what 5–95% predicts).

**So: moving the total to Dangendorf while keeping Frederikse components introduces <1
F-σ of trend inconsistency — much less than your worry implied.** BUT there is a blocker:

- **Dangendorf's per-year SE is unusable as delivered.** Its Zenodo `Global.nc` is mis-written
  upstream (the GMSL slot holds the *barystatic* mean; I recovered the true GMSL from the
  fields file, but the SE column has the same slot-shift and I can't attribute it). Using
  Dangendorf as a *likelihood* term needs a defensible σ — either email Dangendorf, or derive
  σ from the tide-gauge count / the basin-resolved SEs (also in the record).

**Three coherent total-term options (your call, M3):**
1. **Components + STAR only** — drop the (Frederikse) total pre-2018, keep NOAA STAR 2019–2024.
   Cleanest; no new σ problem; 20th c. constrained by components alone. *No Dangendorf.*
2. **Dangendorf (1900–2018) + STAR (2019–2024)** — your leaning. Needs the Dangendorf-σ
   resolved first (above). Independent 20th-c. total that agrees with the components to <1σ.
3. **Relabel Frederikse total as budget-closure** — cheapest, weakest for review.

Separately, I found the **full Frederikse 5000-member component ensemble** (redistributed in
the same Zenodo record) — this is the object the 2026-07-19 σ-fix said was missing. Regardless
of the total-term choice, it lets us compute the *correct* re-referenced per-component band σ
(replacing the "raw band width" over-statement). I'll fold that into the target rebuild.

## The launch is TWO-STAGE (not one 4.5-h run)

The `--overdisperse` starts + adapted-cov predate the 4 new params, and over-dispersed starts
MUST be real posterior draws (random jitter → non-finite logpost). So:
1. **Tuning run** — 1 common-start chain (~1M, ~1 h) on the 39-param model, to (a) confirm
   mixing + acceptance with the SMB pull, (b) produce a posterior.
2. Build `overdispersed_starts.csv` (draws at `ais_iceflow0` quantiles 0.02/0.35/0.65/0.98) +
   `adapted_cov_ext.csv` from it.
3. **Production** — 4×2M over-dispersed, seeds 2026–2029, `caffeinate -i`, column-selective
   reads, then `postprocess_mcmc_ext.jl --accept-slr` + `diag_slr_convergence_by_chain.jl`.

## What I need from you to proceed

1. **A5 σ**: keep 118 (Rignot) or switch to ~83 (Mottram)?
2. **A6 σ**: is 0.10 (scenario-range headroom) acceptable given no published inter-model sd,
   or do you have a source/number?
3. **M3 total term**: option 1, 2, or 3 above? (If 2, the Dangendorf-σ problem must be solved
   first — say whether to email Dangendorf or derive it.)
4. **Go for the two-stage launch** once 1–3 are pinned?
