# Antarctic calibration: L27 vs L32 — trade-off summary

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
every modern-record statistic.

## 3. Why the trade exists

IMBIE's own partition is exact: `net ≡ SMB + dynamics`. Ladrillo's SMB cannot produce the
**+141 Gt/yr** East-Antarctic snowfall anomaly IMBIE reports for 2018–23 (the module's window
anomalies span −20…+27 Gt/yr). With the SMB misfit pinned, **every Gt/yr gained on the net mass
balance transfers one-for-one into the dynamics error.**

## 4. L27 — pros and cons

**Pros**
- Best full-period Antarctic hindcast of any arm (0.70 σ).
- Near-exact in the reconstruction era (0.08 σ over 1920–49).
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
- Beats L27 against BRICK 2.0 at every autocorrelation bound.
- Better TOTAL SLR hindcast (0.22 vs 0.26 σ).
- Noise specification is consistent with the observed SMB variability rather than free.
- Robust to the floor's value: a 34 % cut (L33) keeps the dynamics gain (−126.2).

**Cons**
- Loses the full period (0.88 vs 0.70 σ) and badly loses 1920–49 (1.07 vs 0.08 σ).
- Its advantage is partly in-sample: it is fitted to the record it is scored best on (§6).

## 6. What the evidence CANNOT settle

**(a) The information criteria cannot adjudicate this pair.** Three independent reasons:
1. The two arms have **identical k** (50 free / 42 physical) ⇒ ΔAIC = ΔBIC = −2ΔlnL exactly.
2. The only common target available **is L32's own training data.**
3. The IC **profiles** σ and ρ per draw, so L32's bounded `sd_ais` — the key intervention —
   never enters the comparison.

**(b) A held-out test cannot be built from either candidate.**
- IMBIE's regional breakdown is an **exact partition** of the continental record
  (West + East + Peninsula − continental = 0.00 Gt at every year), and the continental sum is
  L32's training data. DAIS also has no regional degree of freedom.
- **GRACE is spliced into the fitted target of both arms** (L27: 8 years, 2019–26; L32: 3 years,
  2024–26). Over 2002–2018 the contamination runs the *other* way — Frederikse for L27, IMBIE for
  L32, and IMBIE reconciles gravimetry ⇒ **a GRACE score is biased toward L32.**

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

## 8. Specific questions for Tony

1. How do we decide which model is better given the tradeoff between matching recent past versus full-period?
2. Is a noise floor derived from the observed SMB variability the right way to express "the model's
   SMB is too quiet", or does that belong in the SMB component rather than the likelihood?
3. Is the 1920–49 window (L27 0.08 σ, L32 1.07 σ) real skill, or is the reconstruction there loose
   enough that near-exact agreement is not evidence?

---

*Provenance: FaIR 2.2.4 (calib 1.6.0); Ladrillo on `ladrillo-dev`. AIS RMSE from
`bench_ladrillo_<TAG>.md`, all arms scored on `outputs/recalib_targets_ext.csv`
(md5 `eb768cd96463`, IMBIE-2026 build) against the frozen `benchmark/reference/L27/` snapshot;
σ denominators from the frozen `_fixed` copy so σ is comparable across arms. Dynamics anomalies
from `diag_ais_channel_separation.jl`, 1000 draws, common 1979–2008 anomaly reference, ice-mass
sign. IMBIE 2026 = Otosaka et al., Sci. Data 13, 1301, doi:10.1038/s41597-026-08088-0.
L27 remains champion; nothing in this document has been promoted.*
