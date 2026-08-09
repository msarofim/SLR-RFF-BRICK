# T2 memo 2026-08-09 — honest structural assessment of the D1d C_both 3-reservoir glacier model

Task T2 from `handoff_2026-08-09_glacier_d1_arc_complete.md` §4, answering Marcus's two
questions directly: *how well does it match observations & future projections?* and
*is it overly complex, or is it reasonable?* Analysis in §1–§4; recommendation
**separated** in §5. Companion: `memo_2026-08-09_t1_s1900_box_scope.md` (the S(1900)
box; its options are pending and referenced, not re-argued, here).

## 0. Corrections to the running record (found while assembling this memo)

Three numbers in the arc notes are imprecise; fixed here and to be used going forward.

1. **The "adj-obs ~0.81" modern rate is the UNADJUSTED number.** The 2015–2023 rate of
   the raw target is 0.814 mm/yr; the r19-adjusted target — the like-for-like
   comparator, since `rate_modern_hind` is computed on `s_hind`, which excludes R19 —
   is **0.766 mm/yr** (recomputed from `outputs/recalib_targets_ext.csv` + the GlaMBIE
   r19 series, replicating `build_obs_adj()`; net r19 removal 0.38 mm matches the D1d
   sanity check). Consequence: **C_both ANCH modern overshoot is 1.26× (0.966/0.766),
   not ~1.19×; MID is 1.10× (0.839/0.766), not ~1.03×.** MID still resolves the
   overshoot within its κ log-priors, but the resolved state is a 10% high bias, not a
   3% one. (`note_2026-08-09` §2 table header and `handoff_2026-08-09` §3 carry the
   0.81 label — do not propagate it.)
2. **The arc handoff's "SSP levels 7.7/9.8/14.1" is the A_4rung ablation row, not the
   headline.** C_both/ANCH is **9.06 / 11.23 / 15.78** cm — closer to AR6 (9/12/18)
   than the handoff implies. And "MID ≈ on them" is generous: MID is 8.19/10.24/14.66,
   i.e. slightly LOW at all three levels.
3. **D1d's gate status is 3/4, not 4/4.** The "first-ever 4/4" claim belongs to D1 and
   D1c (S1900 = 15.9 and 10.1 respectively); D1d's honest-accounting fixes drop S1900
   to 8.1–9.8 vs the box floor 10 (see T1 memo for whether the box, or the model, is
   the thing being tested there).

## 1. Observational match

### 1a. The century budget, decomposed (C_both/ANCH/unc_t5d, the headline)

Cumulative 1900→2020, against the r19-adjusted target (86.6 mm):

| term | mm | share | status of the term |
|---|---|---|---|
| 3-reservoir block melt (S2020_all − S1900 = 46.5 − 8.1) | 38.4 | 44% | model dynamics, zero hindcast-fitted physics params |
| F_unch (uncharted scope, U) | 29.6 | 34% | fitted, flat prior [14.5, 41.8]; lands at the Frederikse central (~32 global × 0.87) — independent corroboration |
| δ × 60 yr (M15 early-segment bias, 1900–1960) | 18.1 | 21% | fitted, +0.30 mm/yr = 1.005σ of the Roe-motivated prior |
| residual | ~0.5 | <1% | noise |

This is the number a skeptical reviewer will fix on: **56% of the observed century
integral is explained by non-dynamical terms** (scope bookkeeping + an obs-bias term).
The defense is that both terms are literature-anchored, not free: the target
*verifiably contains* the uncharted contribution (Frederikse Methods, primary-verified
— uniform-sampled P&M 16.7–48.0 mm), and U fits at the Frederikse central from a flat
prior rather than railing; δ sits at exactly 1σ of a prior built from the published
Roe-vs-Marzeion disagreement, applied only on the provenance-exact pure-M15 window.
But the split should be stated plainly, as here, in anything that goes out.

### 1b. Era rates (mm/yr), 1900–2023

Observed (recomputed from the target; obs_adj differs only post-2018):

| era | obs | obs_adj | scope/provenance-corrected obs† | block model (indicative) |
|---|---|---|---|---|
| 1900–1919 | 0.891 | 0.891 | ≈0.27 | 0.23 |
| 1920–1949 | 0.959 | 0.959 | ≈0.32 | 0.34–0.35 |
| 1950–1979 | 0.520 | 0.520 | ≈0.08 | 0.21–0.22 |
| 1980–1999 | 0.543 | 0.543 | ≈0.39 | 0.33–0.34 |
| 2000–2023 | 0.729 | 0.713 | ≈0.71 | 0.70–0.75 |

† = obs_adj minus the fitted uncharted taper (rate 0.342 mm/yr to 1970, linear→0 by
2005) minus δ (0.301 mm/yr on 1900–1960), i.e. what the reservoirs alone are asked to
match. Construction is mine, from the fitted (U, δ); era-mean arithmetic in the taper
tail is approximate. **Caveat:** the block-model column is the D1/D1b 2-/3-block ANCH
value — D1d does not emit model era rates (its `flow_*` columns are era log-likelihoods,
not rates). A one-line emitter added to `d1d_fourrung_seam.py` would produce the exact
headline column on the next run (~25–45 min with caches); flagged as a cheap pre-extC
item. The era logLs confirm where the residual lives: 1900–19 and 1920–49 sit at the
noise floor reached in D1c (−16.5/−15.9), mid-century is small (−4.0), and the modern
windows are positive.

The corrected-obs column also shows the one place the model *over*-delivers relative
to the corrected target: mid-century (1950–79), where obs were already quiet and the
U+δ subtraction makes them quieter. This is the flip side of a constant-rate taper; a
reviewer may ask about it, and the honest answer is that the taper shape is the
simplest literature-consistent profile (taper 8.4 < const 9.0 << frontload 12.6, and
Frederikse's plotted P&M curve supports near-constant-to-1980).

### 1c. Point constraints

| datum | model (ANCH) | target | verdict |
|---|---|---|---|
| S(1900), mm | 8.12 | Leclercq-family N(20, 9); box [10, 30] | z = −1.32; box FAILS low. Direction predicted by the scope argument; whether the correction is 0 or up to −12 mm of the mean is the T1 call |
| inventory z (a_tot − S(2000) vs N(0.290, 0.060)) | +0.56 | \|z\| < 1 | PASS |
| S(2020) total-scope (blocks + U) | 76.1 mm since 1850 | ~107 mm (86.6 obs + ~20 Leclercq pre-1900) | gap ≈ δ×60 + S1900 shortfall — same decomposition as §1a |
| GlaMBIE per-reservoir modern rates | D1 2-block: SLOW 0.195 / FAST 0.520 | 0.239 / 0.417 | split imperfect (FAST-heavy); D1d per-reservoir rates not emitted — same cheap emitter item |
| modern rate 2015–23 (hind scope) | 0.966 | 0.766 (adj) | **1.26× overshoot — the one genuine dynamical residual.** MID (κ free within ~±30% log-priors) reaches 0.839 = 1.10× at deficit 5.1–6.6 |

### 1d. What the FREE arm establishes

FREE (κ, shared ν, σ, ρ, U, δ all fit) reaches deficit **−0.4 to +0.9 — the adjusted
century at noise level**. That is the data-compatibility statement: nothing in the
observations is inconsistent with the 3-reservoir + F_unch structure. But FREE buys it
by railing ν to 0.22–0.26 and killing scenario spread (2.0–2.1 cm vs gate floor 4.5):
**the hindcast alone cannot identify the projection-relevant dynamics.** The anchored
arm is therefore not a weaker version of FREE; it is the arm where the projection
physics is carried by GlacierMIP3 rather than left unidentified. This is the honest
frame for the deficit ledger too: the pre-registered FLOW_TOL = 5 has been missed by
four successively better cells (20.7 → 11.5 → 8.4 → 7.3/8.2), each against a
fully-fitted 9-parameter pathological comparator; any revision of that bar is Marcus's
explicit call, with the original metric still reported.

## 2. Projection match

### 2a. SSP levels and spread at 2100 (cm, rel. 1995–2014)

| model | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 | spread (5-8.5 − 1-2.6) |
|---|---|---|---|---|
| **C_both ANCH** | **9.06** | **11.23** | **15.78** | **6.72** |
| C_both MID | 8.19 | 10.24 | 14.66 | 6.47 |
| AR6 ch.9 medians | 9.0 | 12.0 | 18.0 | 9.0 |
| FACTS n200 (B2 runs) | — | — | — | 6.5–8.5 |
| production single-reservoir Mengel (extA108/BRICK-AM) | 6.38 | 6.77 | 7.19 | 0.81 |
| gate | | | | [4.5, 13.5] |

ANCH is on AR6 at SSP1-2.6, −0.8 cm at SSP2-4.5, −2.2 cm at SSP5-8.5 — mildly
conservative at high forcing, in the FACTS family for spread. Against the production
model this is an **8.3× spread improvement** (0.81 → 6.72 cm) while simultaneously
*removing* hindcast-fitted dynamics parameters. Standing caveat (B2 memo): our bands
are parameter-only on mean forcing; FACTS/AR6 include climate-ensemble spread —
medians comparable, widths not. Also on the record: the spread gate is a
projection-consistency **design goal, not an observation** (anatomy memo C8), re-affirmed
when T4 was rejected.

### 2b. Committed ladder vs GlacierMIP3

Model-basis aggregate committed fractions (ANCH): 46.8 / 55.2 / 66.3 / 80.8 % at
+1.2/+1.5/+2.0/+3.0 K vs likely bands [11.8,54.0]/[17.2,63.2]/[41.5,75.5]/[58.5,83.9]
— all in band, none forced (per-reservoir rung |z| ≤ 0.14). Nuance to carry: at the
DATA S(2020) basis the +1.2 K aggregate is 37.4% — on the adopted central by
construction; the model-basis ~47% is the century under-melt appearing in the
denominator, not an anchor error. Two-edged honesty point: the rung σ's are wide
(R19 28–36 pct-pts; FAST 9–13), so "all rungs in band" is a weak claim for R19 and a
meaningful one only for FAST/SLOWP.

### 2c. Response-time behavior

The mechanism the structure was built to express: GlacierMIP3 50%-response times
collapse with warming (stock-weighted 513 yr @1.5 °C → 125 yr @3 °C; melt-weighted
285 yr; committed-weighted 487 yr — all verified from the regchar table). The anchored
transient solves land at **ν ≈ 1.54–1.62** across all three reservoirs — the
"τ-collapse dial". Honesty items: (i) **ν > 1 has no published-value precedent** —
Nauels 2017's own calibrated range is 0.096–0.445; the >1 precedent is the FRISIA
p = 1.5 *form* only. Our ν is derived from the τ50 pairs, not from any prior fit, and
the FREE arm rails it to ~0.25 — the value is carried entirely by the GlacierMIP3
anchors. (ii) The amp inputs are the regchar (ISIMIP3) ratios, which are systematically
low vs both the calibrator convention (aggregate 1.34 vs amp_g 1.8) and the obs
through-origin fit (1.59); **an obs-amp sensitivity arm was never run** and is cheap
with caches — the one outstanding orthogonal test. (iii) 80%-vs-50% metric: the 2025
paper's headline response times are 80%-response; ours are the regchar −50% columns —
fine internally, never cross-compare.

## 3. Complexity audit — "is it overly complex?"

### 3a. Parameter census, with identification status

Nominal count: **19** (3×(a, b, T_off) + 3×(κ, ν) + U + δ + σ + ρ). The honest census
is more informative than the count:

| group | n | how set | identification status |
|---|---|---|---|
| a_b | 3 | Farinotti 2019 (R19 direct 0.069±0.018; SLOWP/FAST = Gt-share split of 0.221±0.057) | **prior-pinned: fitted value = prior mean to 5 decimals in every row** (new finding, `d1d_blocks.csv`). Mechanism: the rungs are committed *fractions*, nearly scale-invariant in a. These are data inputs, not fitted parameters |
| b_b, T_off_b | 6 | 4-rung correlated fit (12 rung data, σ 8.7–36.3 pct-pts, corr 0.6) + soft a-priors | genuinely fitted, weakly constrained (all rung \|z\| ≤ 0.14). T_off is the live output; two of three (+0.27, +0.23) sit outside the current calibrator bounds (−2.00, −0.10) — extC surgery item |
| κ_b, ν_b | 6 | closed-form from 6 τ50 anchors (1.5/3.0 K pairs) | exactly identified, zero residual dof |
| amp_b (+ amp_g) | (3+1 fixed) | regchar / GlacierMIP3 convention | fixed inputs, not fitted; obs-amp arm outstanding |
| U | 1 | flat [14.5, 41.8] mm (P&M × 0.87) | hindcast-fitted; lands at Frederikse central, not railed |
| δ | 1 | N(0, 0.30) mm/yr, 1900–1960 only | hindcast-fitted; 1.005σ |
| σ, ρ | 2 | AR(1) nuisance | hindcast-fitted |

So the ANCH headline fits **4 parameters to the hindcast, none of them dynamics**, and
is measured against a 9-parameter fully-fitted comparator. Two bookkeeping honesty
items a reviewer will find: the Leclercq datum is used **twice** with the same
constants (likelihood term `ll_lec` AND hard gate `g_s1900`) — T1's Option C would
remove the duplication; and the per-block GlaMBIE terms + κ log-priors are **inactive
in the ANCH arm** (MID/FREE only) — they must not be counted among the constraints the
headline honors.

### 3b. Comparators

| structure | params (all hindcast-fitted?) | outcome |
|---|---|---|
| Wong/BRICK 2.0 GSIC (Wigley–Raper) | 4 (yes) | fails ≥3 of our 4 gates on assembled evidence: inventory z = +2.12 at the posterior median (18.7% of draws pass); ladder 100%-committed **by construction** (no finite temperature-dependent equilibrium); spread 4.47 cm vs 4.5 floor. Plus the +4σ 1900 hindcast undershoot with 0.00% joint pass (h1/h2 diagnostic). NB: "0/4 gates" was never produced by a script on the Wong posterior — use the itemized version |
| single-reservoir Mengel 2-τ | 6 (yes) | A0-falsified (T_lia rails; freed sl0 degenerates without an inventory term) |
| single-reservoir Nauels-ν (extB3/b/c MCMC, 500k×3) | 5 (yes) | **0/4 gates in all three arms**; camps on ν ≈ 0.1, spread ≤ 1.6 cm; per-term attribution: the GSIC flow term alone buys the pathology; the analytic anatomy: the law demands 1.92× flow acceleration where obs show 0.76× deceleration |
| T1 offline pool-splits (frame-sharing) | 7–8 | 0/110 feasible; optimizer collapses κ_s ≈ κ_f |
| D1 2-block / D1b 3-block | ~13 | first 4/4 gate passes (S1900 15.9); century-integral gap ~50 mm — closed only by the scope terms (D1c/D1d) |

The pattern across the falsification ledger: **every simpler structure fails on data,
not on taste**, and the failures were established with pre-registered criteria before
the structure was extended. That is the strongest available defense against
"overfit by iteration" — the iterations were falsifications, and the winning
structure's dynamics are anchored out-of-sample rather than tuned.

### 3c. The conventions ledger — where the complexity actually lives

Conventions a reviewer must accept (each with a primary source on file):

| # | convention | anchor |
|---|---|---|
| 1 | r5 lives in the GIS target, not GSIC | Frederikse GrIS = Kjeldsen incl PGIC; GRACE tail incl PGIC |
| 2 | r19 excluded from the hindcast flow (kept in stock/gates/projections) | Frederikse Methods verbatim: "we assume no mass loss from the Antarctic peripheral glaciers" |
| 3 | F_unch uncharted term in the target comparison | P&M 2018 + Frederikse Methods (uniform-sampled, confirmed) |
| 4 | taper profile for F_unch | empirical (beats const/frontload) + Frederikse EDF 6a shape |
| 5 | obs splice Frederikse→GlaMBIE at 2019, r5 removed | prep_recalib_targets_ext.py |
| 6 | δ window 1900–1960 | Frederikse Methods: pre-1961 = pure M15 |
| 7 | δ prior N(0, 0.30) | Roe 2021 vs Marzeion 2014 disagreement span |
| 8 | 0.87 non-r5 scope factor on U | Frederikse's own regionalization rule |
| 9 | amp_g = 1.8 aggregate / amp_b regchar per-block | GlacierMIP3 |
| 10 | S(1900) box [10, 30] | T1 memo — under review, weakest of the set |
| 11 | 50%-response τ columns (not the paper's 80% headline) | regchar |

**Plain answer to "overly complex?": the parameter complexity is defensible — by
construction it is LESS fitted than every simpler alternative it replaced — but the
conventions burden is real: eleven scope/provenance rulings, of which ~half exist
because the calibration target is a reconstruction with its own embedded conventions
rather than a direct observation.** The mitigation is that each ruling is now
primary-source-verified and the two that were tested quantitatively (ignore scope →
extB1's 13-cm pre-1900 fiction; ignore uncharted → D1's irreducible ~50 mm gap) were
falsified in pre-registered cells. The conventions are forced, not decorative — but
they are the paper's exposition burden, and §5 says what I'd do about that.

### 3d. Minimality table — what could be dropped, at what cost

| drop / simplify | Δ vs headline | verdict |
|---|---|---|
| merge R19 into SLOWP (2-block, A_4rung) | deficit −0.9 (7.3) | cheaper BUT scope-dishonest (r19 back in a hindcast whose target has none) and loses the Farinotti-BSL basis; keep the seam |
| drop δ (unc_sx2) | deficit −0.9 (7.3/5.1) | U rails to 39.5–41.0 mm — above the Frederikse central, near the prior ceiling — and early-era logLs collapse (−16.5 → −31.9). δ is doing real, prior-consistent work |
| drop U (book-only) | deficit +2.5; modern rate degrades | not optional: the target verifiably contains uncharted melt |
| drop per-block drivers (global driver control) | deficit −0.7 (control BETTER) | aggregate wash; keep only for the block-level rate split (0.20/0.52 vs control 0.15/0.59; GlaMBIE 0.24/0.42) — defensible either way |
| further SLOW split (D1b 3BLOCK) | ≤0.5 | correctly NOT adopted |
| reassign subpolar → FAST | deficit +47 (ANCH), 1/4 gates | the reservoir structure is load-bearing, not cosmetic |
| block GlaMBIE terms | zero (already off in ANCH) | — |

The structure is near its minimality frontier: every remaining piece either costs real
likelihood, breaks scope honesty, or both, when removed. The only free simplifications
(drop block-GlaMBIE terms from the headline description; drop the gate/likelihood
double-use of Leclercq) are bookkeeping cleanups, not model changes.

## 4. Summary judgment (analysis, not recommendation)

- **Obs match:** century integral closed at noise level with literature-anchored scope
  terms carrying 55%; early eras at the noise floor; mid-century slightly over-delivered
  against the corrected target; the one genuine dynamical residual is the modern-rate
  overshoot, honestly **1.26×** in ANCH, reduced to 1.10× by κ freedom the τ50 data
  themselves cannot exclude (~±30%). S(1900) is a box-edge question pending T1.
- **Projection match:** on AR6 at low forcing, −6% at SSP2-4.5 and −12% at SSP5-8.5
  vs the AR6 medians (−0.8/−2.2 cm); spread in the FACTS family and 8.3× better than the
  production single-reservoir; ladder in-band without forcing; the τ-collapse mechanism
  is expressed rather than imitated.
- **Complexity:** 19 nominal parameters of which 4 are hindcast-fitted (none dynamics)
  — leaner in fitted content than any alternative tried; eleven conventions, each
  sourced, is the real cost; ν ≈ 1.55 is anchor-carried with no published-value
  precedent and one cheap sensitivity arm (obs-amp) still unrun.

## 5. Recommendation (separate from the analysis above)

1. **Proceed to extC** once the T1 S(1900) call is made — the offline program is
   converged and every remaining tension is either a box edge or exactly the kind of
   marginal freedom (κ ±30%, T_off bounds, U/δ posteriors) that the MCMC is the right
   venue to price. The asset list in the arc handoff §4 is complete; add the two
   corrections from §0 (0.766 comparator; per-row SSP quotes) to whatever prose
   accompanies it.
2. **Before or alongside extC, run the two cheap items:** (a) the obs-amp sensitivity
   arm (caches make it ~cell-cost; it is the only untested input with a known low
   bias); (b) the era-rate/per-reservoir-rate emitter in `d1d_fourrung_seam.py` so the
   headline's own era table §1b stops borrowing D1's column.
3. **For the paper framing:** lead with the falsification ledger (extB3 0/4 → T1 0/110
   → D1 4/4-but-gap → D1c/D1d scope closure), and present the conventions table §3c as
   a provenance audit of the *target*, not as model assumptions — that is what they
   are, and it converts the memo's main weakness into the paper's methodological
   contribution. (Framing suggestion only — voice and argument are yours.)
4. **Bookkeeping cleanups regardless of T1 outcome:** remove the Leclercq
   gate/likelihood double-use (T1 Option C does this automatically); note in the next
   handoff that the block-GlaMBIE terms are MID/FREE-only so the headline's constraint
   list stays honest.
