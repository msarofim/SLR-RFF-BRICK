# Handoff 2026-08-13d — SESSION CLOSE. Threads 4 and 5 are next; everything else is done or retired

**This is the pickup document for the next session.** Read it with `LADRILLO.md`
(what the model IS, and what its posterior may and may not be used for). For the
*evidence* behind today's conclusions read `handoff_2026-08-13c_thread3_ridge_falsified.md`
and the CHANGELOG entries for 2026-08-13; do not re-derive them.

Repo `SLR-RFF-BRICK`, branch `brick-mengel-vnext`, tip **`0f0d254`**, baseline tag
**`ladrillo-1.0`**. All six suites pass. Nothing is pushed.

---

## 0. WHERE THINGS STAND

Ladrillo 1.0 is shipped and reproducible: amp law implemented, deliverables
regenerated on the L10 posterior, both superseded vintages quarantined, the
acceptance certificate re-issued against the model actually shipped, and a single
baseline document (`LADRILLO.md`) that says what may be claimed from it.

Of the six questions Marcus set after the review-board pass, **four are closed**:

| # | question | outcome |
|---|---|---|
| 1 | per-scenario amp curve | **CLOSED.** The shipped support (0.75–2.75 K) is composition-free; above it the curve is flat-within-noise. The flat-hold stands and is better supported than when chosen. |
| 2 | `gis_beta_f` prior re-bounding | **CLOSED — don't.** Its posterior is 0.05 of its prior width and it is not on the non-mixing direction. Keep it free. |
| 3 | fix the AIS (and Greenland) ridge | **CLOSED, premise falsified.** No AIS ridge exists, and the failing axis explains R² < 0.001 of the projection. Do nothing to the AIS sampler. Greenland has a separate, real, small fix (§2). |
| 6 | a clean Ladrillo baseline | **CLOSED.** `LADRILLO.md` + tag `ladrillo-1.0`. |
| **4** | **prepare a new calibration** | **NEXT — now the main event** (§1) |
| **5** | **run through 2300; keep investigating alternatives** | **NEXT** (§2) |

Thread 3's outcome is what makes thread 4 the main event: it removed the AIS
sampler work that was competing for the same slot.

---

## 1. THREAD 4 — the next calibration, as ONE spec

The point of doing it as one spec is that each of these changes invalidates the
posterior, so shipping them separately means three calibrations instead of one.
Nothing here should be started before item 1.0.

### 1.0 PREREQUISITE — re-measure on L10 before designing anything
`python/diag_noise_model_and_grip.py` and `python/diag_gis_likelihood_leverage.py`
are **pinned to the extC vintage** (they read from
`outputs/quarantine/20260813_extc_vintage/` and their chain glob is
`chain_extC_seed*`). Their conclusions predate the A+B Greenland module and the
L10 chains. Re-point them at L10 and re-run **first** — the noise-model design
below rests on numbers those scripts produce.

Cost: both read the 2.2 GB chains. Budget ~40 min each, or re-scope them to the
posterior subsample where the question allows it (today's alignment control went
from ~40 min to 8 s that way — see 13c §4).

### 1.1 The discrepancy term — the highest-value change
What is known, and is not in dispute:
- the per-series AR(1) is **misspecified on all five streams** — no member of the
  AR(1) family whitens any of them;
- the **total** stream is **56% algebraically redundant** with the components
  (the total *is* their sum plus LWS) **and** is the loosest constraint in every
  window.

So the likelihood currently double-counts the same observations and then lets the
loosest copy dominate. Three design axes, all genuinely open:

1. **What replaces AR(1)?** An explicit model-discrepancy term δ(t) with its own
   covariance (GP or low-order basis) is the standard answer, and it is what the
   noise-model note recommends. It is also what makes "the model is wrong in a
   correlated way" representable instead of being absorbed as observation noise —
   which is the mechanism `diag_gis_likelihood_leverage.py` identified for
   Greenland's mid-century miss surviving.
2. **What happens to the total stream?** Drop it, down-weight it, or model the
   component/total dependence explicitly. Dropping is cleanest and loses little
   (it is the loosest constraint); keeping it requires the cross-covariance to be
   written down. **Marcus's call**, and it changes what the calibration is.
3. **Do the target sigmas get re-derived?** `prep_recalib_targets_ext.py` already
   carries a caveat that an anchor-shaped closure sigma may double-count level
   correlation given ρ ≈ 0.97. If the noise model changes, this should be settled
   in the same pass rather than left as a caveat.

### 1.2 Greenland slow-channel reparameterisation — small, concrete, do it
Sample `(log r_s(T̄), tilt)` instead of `(α_s, β_s)`, where
`rate_s(T) = α_s·T + β_s` and `T̄` is a reference regional anomaly. This does two
things at once: it moves the **hard rail at α_s = 0** (chain p05 values are
0.000–0.001, and a random-walk proposal against a boundary is what sticks) out to
infinity, and it puts the measured non-mixing direction — which is the *level* of
the slow rate — on its own coordinate.

Implementation notes:
- choose `T̄` explicitly (the hindcast-mean regional anomaly, or the 2015–2024
  anchor) and derive labels from that constant;
- the priors are currently written on `(α_s, β_s)` in `calibrate_mcmc_ext.jl`;
  transform them exactly, the way
  `MimiBRICK.jl/calibration/compute_paleo_geo_prior_ton.jl` transformed the paleo
  ensemble when `(h0, c)` became `(T_on, c)`. That file is the template;
- the same treatment may or may not be wanted for the FAST channel — it converges
  fine, so the default is to leave it alone.

### 1.3 AIS discharge constraint — OPTIONAL, and only for parameter inference
`ais_iceflow0` is weakly identified and does not reach the projection. The only
change that would make it *identified* is an observational constraint on
grounding-line **discharge** (Rignot / IMBIE), the physical partner to the A5 SMB
anchor which already exists. It buys nothing for the deliverable. Include it only
if AIS parameter-level inference is wanted for its own sake — and note that the
area convention that bit the SMB anchor (grounded AIS 12.295e6 km² vs DAIS's
idealised 10.92e6 km² disc, factor 0.888) applies again.

### 1.4 Also decide, while the spec is open
- `gis_amp` is **likelihood-inert** (the calibrator runs to 2026) yet is sampled.
  Keep sampling it — it is the dominant control on the 2100 Greenland projection
  and its prior is the honest uncertainty — but say so explicitly in the spec.
- ν sensitivity, once (owed).
- The refit with the four glacier set-asides at prior centres (owed).

---

## 2. THREAD 5 — through 2300, and what replaces proportional relaxation

**Reporting is already settled:** run and report through 2300 with the
`LADRILLO.md` §5 caveats. Note the horizon ordering was corrected today — **2150
is the worst horizon** for cross-chain agreement (between/within 0.137 vs 0.051 at
2300), because by 2300 most draws have tipped and the distributions re-converge.
Do not write the caveat as growing with horizon.

**The open investigation** is what replaces proportional relaxation at high
warming. Option C failed decisively and is out of pass 1, but its criticism
applies to A+B too — a relaxation model fitted to a ~20 cm historical loss is
being extrapolated against a 7.42 m commitment. Today gave that criticism a
numerical fingerprint: **the slow channel that carries the multi-millennial
commitment is exactly the one the 1900–2024 record cannot identify**
(`gis_alpha_s`/`gis_beta_s`/`gis_f` all fail; the fast/SMB channel converges).

First concrete step: **re-run `python/scope_greenland_bochow2026.py` against A+B.**
It is pinned to the extC quarantine and says so in its header, because it was
written to compare the Bochow 2026 tipping emulator to stock-SIMPLE Greenland.
Comparing it to the module we actually ship is live work and the natural entry
point. Carry the preprint caveat already recorded there (open discussion;
referees have raised UQ and verification concerns; code availability a
placeholder).

Second, and cheaper: the **flat-hold of `S` above 2.75 K compounds** the
high-warming caveat, since SSP5-8.5 sits at S = 0.860 from ~2075 onward. Both
belong in the same sentence wherever 2300 or high-warming Greenland is reported.

---

## 3. NON-OBVIOUS STATE

- **Julia soft scope.** A top-level `for` makes an accumulator assigned inside it
  a NEW LOCAL. This killed two diagnostic runs today right after their first
  output row, and I misattributed it to memory pressure twice because the box
  genuinely does swap on 2.2 GB reads. Declare `global` in top-level loops.
- **Killing a redirected Julia run pollutes its log** — the dying process dumps a
  backtrace, and a replacement truncating the same file interleaves with it. Use a
  fresh log name per launch.
- **Prefer the posterior subsample to the chains** whenever the question is about
  the projection rather than about between-chain behaviour: 10 MB vs 4 × 2.2 GB,
  8 seconds vs 40 minutes.
- **Chains on disk, gitignored, ~2.2 GB each**: `chain_L10_seed{2026..2029}_n2000000.csv`.
  `chain_L10tune_*` (54-param, superseded) is **deletable**; keep `L10tune2` as the
  provenance of the starts file.
- **The accepted posterior is gitignored** and exists only on this machine;
  `LADRILLO.md` §2 has the regeneration command.
- **Two quarantines**, both with READMEs, both vintage-difference-not-bug:
  `20260813_pre_extc_mengel_vintage/` and `20260813_extc_vintage/`. Five scripts
  are deliberately PINNED to the extC quarantine because they *describe* that
  vintage; see its README §6 before repointing any of them.
- Python env `source ~/climate-env/bin/activate`; Julia `--project=julia_v2`.
  Pin `OPENBLAS_NUM_THREADS=1` for parallel chains (4.8× on this M4).
- Naming: **Ladrillo**. Never `sed s/brickf/ladrillo/g` — `brickf` ⊂ `brickfm`.
  Dated `notes/` are frozen.
- **The branch is still `brick-mengel-vnext`**, which no longer describes what is
  on it. Renaming touches the three-canonical-BRICK-versions convention, so it is
  Marcus's call — flagged, not done.

---

## 4. TODAY'S COMMITS

| commit | what |
|---|---|
| `8b68d19` | amp(GMST) law implemented; G4 9.80 → 7.37 cm on the L10 posterior |
| `3735c5a` | deliverables regenerated on L10 with the law |
| `59e0706` | quarantine the pre-extC "78.02 cm" vintage |
| `b2f698a` | handoff 13b |
| `f98a78d` | sub-choice 1 settled; Greenland block convergence measured |
| `76bbc0a` | **the Ladrillo 1.0 baseline** — `LADRILLO.md`, extC quarantined, certificate re-issued |
| `7c42573` | ridge hypothesis falsified; the two blocks have different diseases |
| `4f76635` | the unmixed axis does not reach the deliverable + alignment control |
| `4ebd578` | align the 2150 caveat across `LADRILLO.md` |
| `0f0d254` | handoff 13c |
