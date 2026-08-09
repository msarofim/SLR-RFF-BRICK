# T1 memo 2026-08-09 — the S(1900) box: provenance, scope corrections, re-derivation options, and sensitivity of the D1d verdict

Task T1 from `handoff_2026-08-09_glacier_d1_arc_complete.md` §4. Options in §3 are
**presented for Marcus's call, not adopted**. No code or constants were changed for this
memo; all numbers below are from the existing D1d outputs, the receipts already in the
repo, and two primary sources newly verified via publisher full text (Leclercq 2011) and
abstract+visible text (Parkes & Marzeion 2018).

## 1. Provenance of the box, traced end to end

The chain (each link verified in-repo today):

1. **A2b term proposed** — `memo_2026-08-05_mengel_a0_results_and_recalib_options.md:209`:
   "S(1900) − S(1850) ~ N(µ, σ) from a 19th-century glacier reconstruction
   (Leclercq/Oerlemans length-based 1800–2005 series is the candidate source — number +
   scope to be verified with receipts before implementation)."
2. **Receipts of record (2026-08-06)** — `julia/calibrate_mcmc_ext.jl:346-358` comment
   block, verbatim core:
   > VALUES (receipts 2026-08-06): Leclercq/Oerlemans/Cogley 2011 (SurvGeophys 32:519,
   > DOI 10.1007/s10712-011-9121-7) series gives 1850-1900 = 18.5 mm SLE (excl r19,
   > incl r5; from the Marzeion-2015 supplement data); their 2015 update = 28.0 mm;
   > published scope (×1.18 ANT upscale) ≈ 21.8; Oerlemans 2007 (differenced) ≈ 10 mm.
   > STRUCTURAL spread (10-28 mm, calibration-dataset-driven) >> any formal σ (~3-5 mm),
   > and the scope deltas vs our convention (drop r5, add r19) are a few mm with
   > offsetting signs. µ=20, σ=9 mm spans all four within ~1.2σ.

   So **20 ± 9 was never a Leclercq table value** — it is a considered envelope over a
   four-member source family {18.5, 28.0, 21.8, ~10}, chosen so all four sit within
   ~1.2σ. The MCMC term is `N(0.020, 0.009)` m on `gsic_raw[1900] − gsic_raw[1850]`
   (`calibrate_mcmc_ext.jl:359-360, :415-419`).
3. **Box pre-registered (D0)** — `handoff_2026-08-06_glacier_structural_nu_decision.md:79-83`:
   "Success gates (pre-registered …): … S(1900) within ~10–30 mm; …".
4. **Box implemented** — `d0_glacier_shootout.py:78` `S1900_GATE_MM = (10.0, 30.0)`;
   gate test at `:317/:327` on `s_raw[i1900]` (cumulative melt, S(1850) ≡ 0, mm,
   positive = melt). All d1* scripts inherit it via the exec-prefix. The box is
   **20 ± 1.11σ exactly** (10 = 20 − 1.11·9), not ±1σ as the arc handoff approximated —
   and its floor coincides with the LOWEST member of the source family (Oerlemans-2007
   ≈ 10), i.e. the box floor is the bottom of the literature spread, with zero margin.
5. In D1d the datum appears **twice with the same constants**: as `ll_lec` inside the
   maximized objective (`d1d_fourrung_seam.py:556`, also in the pathological comparator
   `:695`) and as the hard gate `g_s1900` (`:777`). The flow-criterion deficit
   (`flow_win_deficit`, 1980–2023 window, `:787`) contains **no** Leclercq content.

### What the Leclercq 2011 datum actually measures (primary-verified, Springer full text)

- **Method:** 349 glacier length records in 13 regional subsets; records must **start
  before 1945**; surging glaciers excluded. Normalized length → normalized volume via a
  power law (η most likely 2.0–2.1), then the volume proxy is **calibrated by linear
  least-squares onto the 1951–2009 mass-balance compilation** (Cogley); the result is
  "hardly dependent on the choice of the scaling parameter η".
- **Published scope (verbatim):** "Throughout this paper we mean by glacier contribution
  the contribution to sea-level change from all glaciers and ice caps outside the large
  ice sheets of Greenland and Antarctica. Included are the glaciers and ice caps on
  Greenland and Antarctica which are not part of or attached to the main ice sheets."
  → published scope **includes r5 and r19 periphery**, excludes the ice sheets proper.
- **Totals:** 8.4 ± 2.1 cm (1800–2005) and 9.1 ± 2.3 cm (1850–2005). The 1850–2005
  total EXCEEDS the 1800–2005 total: the 1800–1850 contribution was net negative
  (growth toward the mid-19th-century maximum). Median length-change rate −0.9 m/a
  (1801–1850) vs **−5.8 m/a (1851–1900)** — strong retreat was already underway in the
  datum's window.

### The crux: two readings of what "scope" the 20 mm carries

- **Reading (i) — total-scope (the reading assumed by the D1d verdict note §3):** the
  authors' scope statement covers *all* glaciers and ice caps, so the 1850–1900 value
  includes melt from the then-alive stock that later became P&M's "uncharted" glaciers.
  An inventory-scope model must sit BELOW the datum by that share.
- **Reading (ii) — effectively charted-scope (mechanically stricter):** the estimate is
  a *length signal of surviving glaciers*, scaled by a regression onto *charted-stock*
  mass-balance observations (1951–2009). The scale factor therefore maps the signal to
  charted-equivalent SLE; vanished/uncharted glaciers are in neither the signal nor the
  calibration target. Under this reading the datum is already ≈ inventory-scope and the
  uncharted correction is ≈ 0. (This is the same "349 records are of SURVIVING
  glaciers" caveat already recorded in `memo_2026-08-08_geometry_drift_literature.md:105-111`.)

My assessment (labeled as such): reading (ii) has the stronger mechanical case — the
calibration step, not the scope intent, sets what the number measures. But the
published scope statement supports (i), and neither paper settles it (P&M cite Leclercq
only in the reference list; no overlap statement — checked). **The defensible
correction is therefore a RANGE bounded below by 0 (reading ii) and above by the
pre-1900 uncharted melt estimate (reading i).** This is a genuine structural
uncertainty; the honest treatment carries it in σ, not in μ alone.

## 2. Scope corrections, enumerated with magnitudes

Target quantity: model `S(1900)` = 1850→1900 melt of the present-RGI stock, excl r5,
incl r19 (Farinotti-BSL basis).

### (a) Pre-1900 melt of the later-uncharted stock — the dominant and NEW correction

Primary-verified P&M 2018 anchors: uncharted contribution 1901–2015 = **16.7–48.0 mm**
(missing 12.3–42.7 + disappeared 4.4–5.3), average **0.17–0.53 mm/yr**, "less important
after 1990". Nothing pre-1901 is in the accessible text; the supplement is paywalled
and not in `~/Documents/2026/ClaudeDocs/Papers/`. The 1901 start is most plausibly the
start of the CRU forcing data behind the Marzeion-family model (inference, flagged —
not a statement from the paper). The on-disk Frederikse 2020 Extended Data Fig. 6a
plots the P&M curve directly: near-constant rate through ~1980, flattening to ≈0 by
~2000 — supporting the taper profile already adopted, and confirming the stock was NOT
exhausted before 1901 (so pre-1900 melt cannot have been enormous).

Bound construction (range, not a point, per the task spec):

- 1901–1990 effective global rate: 16.7–48.0 mm over ~90 yr → 0.19–0.53 mm/yr.
- Pre-1900/post-1900 rate ratio m: **[0.25, 1.0]**. Floor: weaker mid-19th-c forcing;
  several regions still near LIA max into the 1870s–90s. Ceiling: small glaciers respond
  fast post-LIA (argues m near 1), but m ≫ 1 would have exhausted the stock before the
  17–48 mm of 20th-century melt could occur — self-consistency caps m near 1. Leclercq's
  own −5.8 m/a median retreat 1851–1900 supports m well above the floor.
- U_pre(1850–1900) = 50 yr × m × rate ≈ **[2.4, 26.5] mm global**; × 0.87 non-r5 scope
  → **[2, 23] mm scope**, central ≈ 8–11 mm.
- Applies **only under reading (i)**; under reading (ii) the correction is ≈ 0.

If Marcus has institutional access to the P&M supplement, an actual pre-1901
back-extrapolation of their model state could replace this bound — optional sharpening,
not required for the decision.

### (b) r19 (Antarctic periphery)

Model includes r19 (Farinotti-BSL a = 0.069 m), but its 1850–1900 melt is small — the
D1d BSL fix removed ~1.4 mm of early r19 melt vs the Gt-share basis, and R19's fitted
T_off (+0.27) makes it a late-onset melter. The A2b receipt's 18.5 mm base number
**excludes** r19; Leclercq's published-scope variant includes the Antarctic periphery
via the ×1.18 upscale (≈21.8). Correction to bring an excl-r19 datum to model scope:
**+1 to +2 mm**. (Frederikse's r19≈0 is a *target* convention; the datum question is
separate.)

### (c) r5 (Greenland periphery)

Model excludes r5 (it lives in the GIS target). The 18.5 mm receipt variant **includes**
r5. GlaMBIE 2000–23 melt share for r5 is 13.0%; using that as the historical share
(uncertain, the only handle we have): correction **−2 to −3 mm**.

**(b)+(c) net ≈ −1 ± 2 mm — offsetting**, exactly as the 2026-08-06 receipt anticipated
("a few mm with offsetting signs"). The new content of this memo is (a): a **0–23 mm**
correction whose size depends on the reading in §1, with a reading-(i) central of
~9 mm.

## 3. Options (for Marcus — none adopted)

**Option A — keep the box, label the failure.** S(1900) = 7.2–9.8 mm across all D1d
ANCH/MID rows vs floor 10; document as a known scope-limited edge. Cheapest; but the
gate then permanently fails for a reason we believe is scope bookkeeping, which
degrades the gate's diagnostic value for extC.

**Option B — re-derive the box for inventory scope.** μ′ = 20 − U_pre + (b) + (c);
candidates:
- B1 (reading-(i) point): μ′ ≈ 11, σ′ = √(9² + 5.5²) ≈ 10.5 → box (±1.11σ′, floored at
  0): **[0, 23]**.
- B2 (reading-agnostic): μ′ = 15, σ′ = 11 → box **[3, 27]**.
Any defensible variant has floor < 7.2, so the choice within the honest range does not
affect which rows pass (see §4). Note a hard floor near 0 has no bite — Option B
effectively converts the lower bound into a formality.

**Option C — replace the box with the likelihood term at scope-corrected (μ′, σ′)**
(the arc handoff flags this as cleaner; I agree). Drop `g_s1900` as a hard gate (or
retain a wide QC-only sanity box, e.g. [0, 40]) and report the z-score of the A2b term
instead. Candidate term: **N(15, 10) mm** — spans reading (ii) (μ=20 at +0.5σ), the
reading-(i) central (≈11 at −0.4σ), and the four-member source family {10, 18.5, 21.8,
28.0} within 1.3σ. Alternative if Marcus prefers to keep μ untouched and encode the
scope question purely as uncertainty: **N(20, 12)** (asymmetry can't be expressed in a
Normal; a wider σ is the honest symmetric encoding). Whatever is chosen **must change
together** in both places (arc-handoff trap note): `d0_glacier_shootout.py:63`
(`LEC_MU/LEC_SIG`, inherited by every d1* script via the exec prefix) and
`julia/calibrate_mcmc_ext.jl:359-360` (the extC A2b term).

## 4. Sensitivity: does any defensible re-derivation change the D1d verdict pattern?

Mechanics first (verified in code today): in the **ANCH** arm the fitted parameters are
(σ, ρ, U, δ), none of which enters the reservoir integration, so S(1900) is an
analytic constant of the fit — proven by the bit-identical `S1900_mm = 8.12281` across
`C_both/ANCH/unc_t5d` and `C_both/ANCH/unc_sx2`. Re-derivation therefore changes
**only pass/fail** for ANCH. In MID/FREE the `ll_lec` term is live: MID sits at
7.17–9.77 mm (weak pull vs the κ-priors), FREE is actively pulled to 27–28 mm by the
current N(20,9) — under a re-centered term the FREE optimum would drop; MID would move
marginally.

Current D1d gate anatomy (from `outputs/d1d_fourrung_seam.csv`): **every ANCH/MID row
fails `g_s1900` and nothing else** (inv/ladder/spread all pass); every FREE row passes
`g_s1900` and fails spread. Deficits: ANCH 7.33–8.21, MID 5.07–6.58, FREE ≤ 0.89.

| re-derivation | gate pattern | deficits | feasibility (4/4 AND ≤5) |
|---|---|---|---|
| none (status quo) | ANCH/MID 3/4 | unchanged | 0/12 |
| any Option B box (floor < 7.2) | **ANCH/MID → 4/4** | ANCH exactly unchanged; MID shifts marginally | still 0/12 on current numbers |
| Option C (no hard box) | gate row becomes a z-report | same as above | n/a (bar re-expressed) |
| keep N(20,9), reading (ii) | ANCH/MID 3/4 | unchanged | 0/12; datum tension z = −1.14 to −1.43 |

Specifics worth having on record:

- Under any re-derived box, the **pre-registered minimal bar** (C_both ANCH deficit
  ≤ 8.4 with |δ| ≤ 1σ and gates) would then hinge on δ = **1.005σ vs the ≤ 1.0σ edge** —
  another box-edge miss at the third decimal, not a substantive one.
- **No row flips to feasible** without a re-run: the closest is `C_both/MID/unc_sx2`
  at deficit **5.07 vs tol 5**. Its fit would shift slightly under a re-centered
  Leclercq term (live `ll_lec`), so a post-decision d1d re-run (~25–45 min with caches)
  could move it across — flagged, not predicted.
- Under reading (ii) with no correction at all, the datum stands at z −1.14 to −1.43 —
  the verdict note's "everything within ~1.3σ" is marginally optimistic for the MID
  rows (C_both/MID = −1.43); the headline ANCH row is −1.32.
- To make the current ANCH values FAIL a scope-corrected box you would need to reject
  the correction entirely AND keep the floor above 9.8 — i.e. exactly the status quo.
  Conversely no defensible re-derivation makes anything worse.

**Bottom line:** the box call flips the cosmetic gate count (3/4 → 4/4 across all
ANCH/MID rows) but does not touch the substantive D1d conclusions — deficits 5.1–8.2
vs a fully-fitted pathological comparator, offline program converged, extC the venue.
What the call actually decides is whether extC inherits (a) a hard gate that fails for
scope-bookkeeping reasons (Option A), or (b) an honestly re-scoped likelihood term
(Option C, my recommendation, with B as the halfway house). The same (μ′, σ′) becomes
the extC A2b term either way, so this decision is on the extC critical path.
