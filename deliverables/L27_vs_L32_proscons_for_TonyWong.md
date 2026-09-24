# Antarctic calibration: L27 vs L32 — trade-off summary

**Marcus C. Sarofim (NYU Marron Institute)** · 2026-09-24 · Ladrillo / SLR-RFF-BRICK, branch `ladrillo-dev`

> `[MCS]` — framing, recommendation and the ask of Tony go here. Everything below is measured
> numbers and the structure of the choice; no recommendation is embedded.

---

## 1. The choice

Both arms are the **same model and the same objective**. They differ only in what the Antarctic
likelihood is fitted to, and in one noise-model setting:

| | fitted AIS target | `sd_ais` |
|---|---|---|
| **L27** — shipped champion | Frederikse 1900–2018 + GRACE 2019–2026 | free |
| **L32** — candidate | Frederikse 1900–78 + **IMBIE 2026** 1979–2023 + GRACE 2024–26 | floored at the SMB-derived 0.03259 cm |

**Everything outside Antarctica is unaffected.** Glaciers, Greenland and thermal expansion agree to
two decimal places between the arms (0.69 / 1.07 / 1.51 σ). The AIS component is the only thing in
question.

## 2. The numbers, all on one ruler

Scored against the IMBIE-2026 target, one benchmark run, frozen champion snapshot.
AIS RMSE in units of the AIS target's own 1σ (0.1674 cm); lower is better.

| statistic | **L27** | **L32** | observation |
|---|---|---|---|
| AIS RMSE, **full period** 1900–2026 | **0.70** | 0.88 | — |
| AIS RMSE, 1920–1949 | **0.08** | 1.07 | — |
| AIS RMSE, 1950–1992 | **0.37** | 0.47 | — |
| AIS RMSE, **1993–2026** (satellite era) | 1.27 | **1.01** | — |
| 90 % coverage, 1993–2026 | 3 % | **27 %** | — |
| Rate z, satellite era | −2.42 | **−1.79** | — |
| Cumulative level z, 1979–2023 | −2.63 | **−1.45** | — |
| **2018–23 dynamics anomaly** (Gt/yr) | −119.1 | **−133.1 ± 4.9** | IMBIE **−167.2** |
| TOTAL SLR hindcast (σ) | 0.26 | **0.22** | — |
| ΔBIC vs BRICK 2.0 (ρ ≤ 0.99 / 0.95 / 0.90) | +9.1 / +68.0 / +137.9 | **+15.4 / +69.8 / +139.1** | both clear the criterion |

**Neither arm dominates.** L27 wins the full period and the two pre-satellite windows; L32 wins
every modern-record statistic. That is the whole decision.

### 2a. Where the two sit among all seven arms

Every arm built in this arc, on the same ruler. AIS RMSE (σ):

| arm | what it is | full | 1920–49 | 1950–92 | **1993–2026** |
|---|---|---|---|---|---|
| **L27** | Frederikse target, free `sd_ais` — **champion** | **0.70** | 0.08 | 0.37 | 1.27 |
| L34 | Frederikse target + SMB floor | 0.73 | 0.07 | 0.34 | 1.32 |
| **L32** | IMBIE target + SMB floor — **candidate** | 0.88 | 1.07 | 0.47 | 1.01 |
| L33 | IMBIE target + floor cut 34 % | 1.11 | 1.43 | 0.60 | 0.96 |
| L29 | IMBIE target, ρ capped at 0.90 | 1.45 | 1.85 | 0.64 | **0.52** |
| L28 | IMBIE target, free `sd_ais` | 1.53 | 1.89 | 0.62 | 0.67 |
| L30 | IMBIE target + discharge ramp | 1.53 | 1.93 | 0.64 | 0.73 |

**The arms lie on a single trade-off axis** between the reconstruction era and the satellite era,
and four of the seven are on its Pareto frontier: **L27, L32, L33, L29**. Three are dominated —
**L34** (worse than L27 on both), and **L28 and L30** (both worse than L29 on both).

L27 and L32 are the two frontier points that are *balanced*; L29 buys the modern record at
1.45 σ of full period, and L33 sits in a flat stretch where the exchange rate is poor (§7).

## 3. Why the trade exists — it is an identity, not a tuning failure

IMBIE's own partition is exact: `net ≡ SMB + dynamics`. Ladrillo's SMB cannot produce the
**+141 Gt/yr** East-Antarctic snowfall anomaly IMBIE reports for 2018–23 (the module's window
anomalies span −20…+27 Gt/yr). With the SMB misfit pinned, **every Gt/yr gained on the net mass
balance transfers one-for-one into the dynamics error.**

L27, L28 and L30 are three points on that single constraint line. **L32 is the first arm off it**,
by 38.9 Gt/yr — bought by flooring `sd_ais` at the observed SMB interannual variability
(116.5 Gt/yr year-on-year, stable across four decades, R² 4.3 % on GMST ⇒ weather, not forced).

## 4. L27 — pros and cons

**Pros**
- Best full-period Antarctic hindcast of any arm (0.70 σ).
- Near-exact in the reconstruction era (0.08 σ over 1920–49).
- **Shipped**: 7/7 van Vuuren runs, 14/14 paper figures, and the GMD draft's posterior.
- The dynamics-record null it supports is a defensible published result: its worst dynamics misfit
  (+48.1 Gt/yr, 2018–23) is **0.4 of IMBIE's own σ** (130 Gt/yr).

**Cons**
- Worst satellite-era fit of the two (1.27 σ) with **3 % coverage** — it essentially misses the
  modern record's uncertainty band.
- Rate z −2.42: the modern acceleration is under-reproduced.
- Its `sd_ais` (0.02162 cm) sits a factor **1.51 below** the SMB-derived floor, i.e. the likelihood
  chose an interannual noise level the observational record excludes.
- Sits on the net/dynamics constraint line; cannot improve one channel without paying the other.

## 5. L32 — pros and cons

**Pros**
- Best modern record of any arm on level, rate, coverage and dynamics simultaneously.
- Only arm to escape the net/dynamics identity trade-off.
- Beats L27 against BRICK 2.0 at every autocorrelation bound.
- Better TOTAL SLR hindcast (0.22 vs 0.26 σ).
- Noise specification is consistent with the observed SMB variability rather than free.
- Robust to the floor's value: a 34 % cut (L33) keeps the dynamics gain (−126.2).

**Cons**
- Loses the full period (0.88 vs 0.70 σ) and badly loses 1920–49 (1.07 vs 0.08 σ).
- **Zero deliverables**: 0/7 van Vuuren runs, 0/14 figures. Adopting it re-runs the paper's figure set.
- Changes the paper's Antarctic basis and costs the IMBIE-null framing currently drafted.
- Its advantage is partly in-sample: it is fitted to the record it is scored best on (§6).

## 6. ⚠ What the evidence CANNOT settle — the part worth Tony's judgement

**(a) The information criteria cannot adjudicate this pair.** Three independent reasons:
1. The two arms have **identical k** (50 free / 42 physical) ⇒ ΔAIC = ΔBIC = −2ΔlnL exactly.
2. The only common target available **is L32's own training data.**
3. The IC **profiles** σ and ρ per draw, so L32's bounded `sd_ais` — the whole intervention —
   never enters the comparison.

**(b) A held-out test cannot be built from either candidate.**
- IMBIE's regional breakdown is an **exact partition** of the continental record
  (West + East + Peninsula − continental = 0.00 Gt at every year), and the continental sum is
  L32's training data. DAIS also has no regional degree of freedom.
- **GRACE is spliced into the fitted target of both arms** (L27: 8 years, 2019–26; L32: 3 years,
  2024–26). Over 2002–2018 the contamination runs the *other* way — Frederikse for L27, IMBIE for
  L32, and IMBIE reconciles gravimetry ⇒ **a GRACE score is biased toward L32.** It is a one-sided
  test: an L27 win would be informative, an L32 win would not.

⇒ **There is no scorer that settles this. It is a judgement about what the Antarctic module is for:
hindcasting the reconstruction era, or tracking the modern record.**

## 7. Closed, and open

**Closed — every structural degree of freedom tried on DAIS is dead:** a discharge ramp (L30, the
likelihood declined it and a power test confirms the objective is not blind — 95.7 % recovery of a
synthetic ramp), a free exponent on the ocean-temperature ratio (inert; needs n≈20 against IMBIE's
2.02×), a ρ cap (L29, indistinguishable from L28 on every channel), and a dynamics likelihood
channel (a 3.6–16× *weaker* copy of the level channel's pull, not a corrective).

**Closed today — the noise fix alone does not work.** L34 = L27's target + the SMB floor, run
2026-09-24: full-period AIS **0.73 σ** (vs L27 0.70), satellite era **1.32** (vs 1.27), dynamics
anomaly **−117.2 ± 1.6** against L27's −116.2 ± 1.5 — indistinguishable. The floor is
**target-dependent**: it moves the dynamics anomaly by ~1 Gt/yr on Frederikse and by ~62 Gt/yr on
IMBIE. **L32's gains come from the target, not the noise specification**, and the champion cannot
be improved without the target swap.

**Closed today — L33 does not displace L32 as the IMBIE-side arm.** L33 (same target and
mechanism, floor cut 34 %) was benchmarked 2026-09-24: full period **1.11 σ** against L32's 0.88,
satellite era **0.96** against 1.01. It is not *dominated* — it does buy a little more of the
modern record — but the exchange rate is poor: **0.23 σ of full period surrendered for 0.05 σ of
satellite era, ≈ 4.6 : 1**, where the L27 → L32 step trades at 0.69 : 1.

⚠ **Worth noting for method, not just for the answer.** L33 has the *better* cumulative level
(z −1.21 vs L32's −1.45), which on that statistic alone made it look like the better compromise.
The whole-record scorer reverses that. This is the second time in this arc that a favourable
summary statistic has failed to predict the full-period hindcast.

## 8. Specific questions for Tony

1. Given no scorer can separate these, does the Antarctic module's **purpose** decide it — and which purpose?
2. Is a noise floor derived from the observed SMB variability the right way to express "the model's
   SMB is too quiet", or does that belong in the SMB component rather than the likelihood?
3. Does the one-sided GRACE test have value despite its bias toward L32?
4. Is the 1920–49 window (L27 0.08 σ, L32 1.07 σ) real skill, or is the reconstruction there loose
   enough that near-exact agreement is not evidence?

---

*Provenance: FaIR 2.2.4 (calib 1.6.0); Ladrillo on `ladrillo-dev`. AIS RMSE from
`bench_ladrillo_<TAG>.md`, all arms scored on `outputs/recalib_targets_ext.csv`
(md5 `eb768cd96463`, IMBIE-2026 build) against the frozen `benchmark/reference/L27/` snapshot;
σ denominators from the frozen `_fixed` copy so σ is comparable across arms. Dynamics anomalies
from `diag_ais_channel_separation.jl`, 1000 draws, common 1979–2008 anomaly reference, ice-mass
sign. IMBIE 2026 = Otosaka et al., Sci. Data 13, 1301, doi:10.1038/s41597-026-08088-0.
L27 remains champion; nothing in this document has been promoted.*
