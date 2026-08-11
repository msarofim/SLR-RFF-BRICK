# Gate 3.1 verdict — the target conflict is real, correctly reproduced, and not blocking

2026-08-11. Answers the blocking diagnostic in
`notes/handoff_2026-08-11_greenland_pass1_complete.md` §3.1 /
`notes/redteam_2026-08-11_brickf.md` §0.

Scripts: `python/diag_target_conflict.py`, `python/diag_gis_likelihood_leverage.py`.
Outputs: `outputs/diag_target_conflict{,_summary.md}.csv`,
`outputs/diag_gis_likelihood_leverage{,_summary.md}.csv`,
`figures/diag_target_conflict.png`, `figures/diag_gis_likelihood_leverage.png`.

**Verdict: proceed to step 5 unchanged.** No data-side surgery is required. One
methodological choice is flagged in §4 and is Marcus's call; the default (do
nothing, document) is defensible on the numbers below.

---

## 1. What the +0.74 cm actually is

The residual is exactly additive, because every series is re-referenced to
1995–2005:

    Σ components − Dangendorf = (Σ components − Frederikse GMSL)   [budget closure]
                             + (Frederikse GMSL − Dangendorf)      [reconstruction difference]

| window | Σ comps | total | residual | = closure | + reconstruction |
|---|---|---|---|---|---|
| 1900–1930 | −12.455 | −12.202 | −0.253 | **+0.260** | −0.513 |
| 1950–1980 | −3.878 | −4.616 | **+0.738** | **+1.109** | −0.371 |
| 1942–1982 | −4.269 | −4.982 | +0.713 | **+1.163** | −0.450 |
| 1993–2018 | +1.777 | +1.723 | +0.054 | +0.086 | −0.031 |

**It is Frederikse's own mid-century budget non-closure**, not our splice and
not Dangendorf-vs-Frederikse. Three findings, in the order they kill the
alternatives:

1. **Not a splice.** The earliest year any modern product (GRACE-FO, GlaMBIE,
   NOAA NCEI) enters a component target is **2019**. It cannot reach 1950–1980.
   The total over that window is the Dangendorf reconstruction itself, not the
   NOAA STAR splice (which starts 2022). Verified in the summary's provenance
   block.
2. **Not Dangendorf-vs-Frederikse.** That term is **−0.371 cm**, i.e. the
   *opposite* sign — swapping in the independent Dangendorf total **reduces**
   the conflict by 0.37 cm rather than causing it. It is 0.24 of Dangendorf's
   own per-year SE over the window. The two reconstructions agree.
3. **We reproduce Frederikse exactly.** Our closure term (+1.109 cm) matches the
   weighted median closure of Frederikse's own 5000-member ensemble (+1.104 cm)
   at **z = +0.006**. The non-closure is a property of Frederikse 2020, faithfully
   inherited, not something our processing introduced.

Scale: the ensemble's own spread on that window-mean closure is sd 0.792 cm,
5–95% [−0.188, +2.452]. So the mid-century non-closure is ≈1.4σ of Frederikse's
joint uncertainty — systematic, but not significant at 5%.

Provenance note: `GMSL` in `frederikse2020_GMSL_ensembles.nc` is the observed
tide-gauge reconstruction, **not** the budget sum — verified (differs from
Barystatic+Steric by up to 158 mm; cross-member correlation with the budget at
1950 is 0.085). `Barystatic` equals the four mass components to 0.15 mm.

---

## 2. The red team's prediction, corrected in sign and magnitude

The red team predicted the Greenland fix would degrade the total fit by ≈0.7 cm.
That over-states it, because **the model currently sits BELOW the total target
in mid-century**, so the added melt moves the total *through* its target, not
away from it. From `outputs/postpred_extC_components_timeseries.csv`, mean
obs − model p50 over 1942–1982:

| component | obs − model (cm) |
|---|---|
| **gis** | **+0.822** |
| glaciers | −0.017 |
| ais | +0.003 |
| te | −0.097 |
| **total** | **+0.322** |

Two corrections to the record:

- **The GIS miss is +0.822 cm, not the 0.5–0.7 cm the memo carried.** Use 0.82.
- Applying it takes the total residual from **−0.322 to +0.499 cm** — a sign
  flip of similar magnitude, not a 0.74 cm one-way degradation.

**Direction of the miss.** GIS obs sits *above* the model in mid-century while
matching at 1900–1930 (+0.058), so the target says Greenland lost more ice in
the **first half** of the century than the model produces — the 1920s–40s
southern-Greenland warm anomaly. That is precisely what the regional driver (A)
is built to deliver, which is a coherence check on pass 1, not a coincidence.

---

## 3. Why stock BRICK-F\* under-melted Greenland — it is not the target conflict

The total target's own σ over 1950–1980 is **1.538 cm**. A 0.74 cm conflict is
0.47σ of it; the total channel is far too loose to have caused the under-melt.
The actual mechanism is the **per-series AR(1) noise model** in
`calibrate_mcmc_ext.jl`, whose σ *and* ρ are both sampled (half-normal(0,5) on σ).

Pooled extC posterior medians, 4 chains × 2,000,000 steps, second half:

| series | ρ | AR(1) τ (yr) | stationary sd (cm) | mean band σ (cm) | n_eff |
|---|---|---|---|---|---|
| ais | 0.616 | 2.1 | 0.017 | 0.171 | 29.9 |
| gsic | 0.594 | 1.9 | 0.017 | 0.459 | 31.6 |
| **gis** | **0.985** | **67.5** | 0.318 | 0.188 | **0.93** |
| **steric** | **0.973** | 37.1 | 0.302 | 0.310 | **1.70** |
| dang | 0.453 | 1.3 | 0.068 | 1.538 | 47.1 |

ρ_gis = 0.985 is near-random-walk: a 40-year systematic miss is reclassified as
correlated noise almost for free. Direct cost of a 0.65 cm residual over
1942–1982 at the posterior medians:

| series | shape | AR(1)+band (as calibrated) | band only (iid) | AR(1) only | leverage AR(1) removes |
|---|---|---|---|---|---|
| gis | step | −27.71 | −382.60 | −141.70 | **14×** |
| gis | ramp | −7.53 | −122.77 | −8.92 | **16×** |
| dang | step | −3.46 | −3.48 | −748.62 | 1× |
| dang | ramp | −1.22 | −1.22 | −258.24 | 1× |

**Caveat on n_eff, stated because the number is arresting.** n(1−ρ)/(1+ρ)
describes the AR(1) term *alone* and therefore **understates** the grip — the
diagonal band term contributes independent information every year. The "AR(1)
only" column above is that understatement made explicit: strip the band and the
gis penalty rises to −141.7. The AR(1)+band column is the number to trust, and
n_eff ≈ 0.93 should be quoted only with this qualification. Both figures are
also conditional on the noise parameters being held at their posterior medians;
the sampler can additionally inflate σ, so these are upper bounds on the grip.

### The decisive number — the realised correction

Driving the same calculation with the **actual** extC residuals rather than a
synthetic shape (mean over 1942–1982, residual = model − obs):

| series | residual now | correction | residual after | Δ logl |
|---|---|---|---|---|
| gis | −0.822 | +0.822 | +0.000 | **+16.49** |
| dang (total) | −0.322 | +0.822 | +0.499 | **−4.06** |
| | | | | **NET +12.43** |

The Greenland correction is worth **+12.4 log-likelihood units net** even after
the AR(1) has removed 14–16× of the GIS leverage and even after paying the total
channel in full. **The sampler should take this deal.**

---

## 4. Pre-registration, updated, and the one flagged choice

Against the red team's three outcomes: **outcome 1 is expected** (Greenland
improves, total degrades) — but "degrades" means the total's mid-century
residual flips from −0.32 to +0.50 cm, which is 0.32σ of that channel's own σ.
Outcome 3 (improvement suppressed, posterior ≈ extC) is **less likely than the
red team feared**: the AR(1) weakens the pull by 14–16× but +12.4 net logl
survives it. If the posterior nonetheless comes back looking like extC, the
explanation is *not* the target conflict and the next place to look is σ_gis
inflation — check whether the posterior sd_gis/rho_gis move.

**Flagged methodological choice (Marcus's call).** The component targets and the
total target cannot both be satisfied to their nominal σ in mid-century, because
Frederikse's own budget does not close there. Two defensible treatments:

- **(a) Do nothing; document.** The conflict is 0.47σ of the total channel's own
  σ and ≈1.4σ of Frederikse's joint spread — inside both. **Recommended**: it
  keeps the only Frederikse-independent constraint at full strength, and the
  quantities above show the fit is not being distorted.
- **(b) Add the ensemble closure sd (0.792 cm over the window) in quadrature to
  the total target's σ in mid-century.** More conservative, but it weakens the
  independent total constraint on account of an offset already inside its σ.

Do **not** resolve this by letting the sampler split the difference silently —
that is what stock BRICK-F\* did, and it is why Greenland under-melted.

---

## 5. Loose ends this raised (not blocking pass 1)

- **ρ_gis = 0.985 and ρ_steric = 0.973 are worth a decision of their own.** Two
  of five component channels have near-random-walk residual models, so their
  parameter marginals are weakly identified *in level* and the reported
  component bands are correspondingly soft. This is the same shape as the
  CarbonCycleEmulator AR(1) retirement (memory `project_ccx_ar1_posterior_pathology`,
  where n_eff was 0.8). Not a pass-1 blocker — the +12.4 net survives it — but
  it belongs on the list with §4.3 (TE against a modern OHC target), and the two
  are plausibly the same story: TE is the *other* ρ→1 channel.
- The memo's "0.5–0.7 cm" GIS miss should be corrected to **+0.822 cm** wherever
  it appears.
