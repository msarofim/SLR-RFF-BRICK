# Handoff — the committed-loss diagnostic, the amp discharge, and why the `Leq(T)` refit is a dead end

**Start-here document for the next session.** Repo `SLR-RFF-BRICK`, branch
**`ladrillo-dev`**, HEAD `37440d3`, **pushed and in sync with origin**.
Predecessor: `notes/handoff_2026-08-18_l12_channel_ordering.md`.

**Bottom line: the predecessor's §7 items 1 and 3 are both closed. The
committed-loss diagnostic is built; the amp(GMST) caveat is measured and ACCEPTED
by Marcus. Then the literature check turned up a real shortfall at ssp585, and
the obvious fix for it — an external `Leq(T)` target — was measured and CANNOT
WORK. Nothing is blocking. The next step is a structural change, and §5 specifies
it, including the physics.**

---

## 0. WHAT CHANGED IN ONE TABLE

| | before | after |
|---|---|---|
| §7 item 1, committed-loss diagnostic | not built | **BUILT** — 1.7–8.5 % discharged by 2300 |
| §6 amp(GMST) caveat | **open**, "justify or align" | **JUSTIFIED & ACCEPTED** — no refit |
| ssp585 @2300 vs literature | unquantified | **LOW by 3.8–6.9×**, two peer-reviewed sources |
| the `Leq(T)` refit | the recommended fix | **CANNOT WORK** — ridge ceiling + capped ratio |
| `diag_ladder_transition_resolution.py` | read L11 | reads L12 (verified byte-identical) |
| `|r| ≤ 0.05` inertness threshold | an **iid** null on MCMC draws | **ESS-aware** null |

---

## 1. §7 ITEM 1 — THE COMMITTED-LOSS DIAGNOSTIC IS BUILT

`python/diag_gis_committed_loss.py` + `python/plot_gis_committed_loss.py`
(→ `figures/gis_committed_loss_L12.png`). Pure post-processing on L12: **no refit,
no vintage**, exactly as option C's abandonment recommended.

**Only 1.7–8.5 % of Greenland's multi-millennial commitment is discharged by
2300**, every SSP, both ladder arms.

| SSP | GMT @2300 | PISM-dEBM | Yelmo-REMBO | realised @2300 | discharged |
|---|---|---|---|---|---|
| SSP1-2.6 | 1.74 K | 0.66–1.48 m | **0.76–4.90 m** (straddles) | 0.091 m | 3.2–8.5 % |
| SSP2-4.5 | 3.15 K | 6.79–7.01 m | 6.60–7.05 m | 0.168 m | 2.4–2.5 % |
| SSP5-8.5 | 7.81 K | 7.40 m (sat.) | 7.42 m (sat.) | 0.456 m | 6.1–6.2 % |

Three design choices that should not be re-litigated:

1. **Brackets, never interpolation.** Neither family resolves its own transition,
   so the committed loss is the two rungs either side, flagged when the bracket
   straddles the unresolved jump. The bracket rule and transition locator are
   **imported** from `diag_ladder_transition_resolution.py`, not re-implemented.
2. **Both arms throughout.** The arm is decisive only at low warming — 3.52× at
   SSP1-2.6's peak, 1.00–1.01× elsewhere. Reproducing that table exactly is the
   regression check on the whole path.
3. **Every ratio is against realised SLR at 2300**, including for the path peak.

**SSP1-2.6 is the one scenario where the evaluation LEVEL matters** — it peaks at
1.92 K, *above* Yelmo's transition, and settles to 1.744 K, *inside* it. Peak and
2300 are two different questions and both are reported. **The ladder is an
equilibrium object and cannot represent overshoot reversibility**, so it cannot
say whether the peak excursion commits the loss. Do not let the peak row be read
as if it could.

---

## 2. §6 amp(GMST) — MEASURED, AND ACCEPTED BY MARCUS

`python/diag_gis_amp_calib_projection_gap.py`. The caveat carried since L10
("projection-side only; the calibrator runs at constant `GIS_AMP` = 1.92 —
justify or align"). Two independent legs, both nominal.

**Leg 1 — over the fitted years, the law IS the constant.** `S` is anchored so
`S == 1` exactly at `dT_eff` = 0.940 K. Over 1850–2026 it spans 0.9796–1.0023, so
the worst-year amp departure is **0.0391 = 0.19 of amp's own posterior sd**
(0.2011), against a stated 0.5 sd materiality threshold. At 2100 the departure is
1.33 sd — the whole effect lives in the projection period, where the law is meant
to act.

**Leg 2 — `gis_amp` is likelihood-inert, re-verified ON L12** (not inherited: the
wedge truncates the Greenland block). Marginal ≡ its truncated prior, mean/sd
**1.9107 / 0.2011** vs **1.9049 / 0.2013**.

> **⚠ The `|r| ≤ 0.05` figure in the older notes is an IID null applied to MCMC
> draws, and it is too tight.** L12's max is `|r|` = 0.0799 (`ais_mu`), which
> against an iid null reads as 8σ coupling *and* as a regression from L11 — both
> artefacts of the wrong null. The ESS-aware null: **ESS 641** of 10,000 draws,
> null max`|r|` over 56 params **median 0.0988 / p95 0.1309**, so the observed
> value sits **below the null median**. **Quote the ESS-aware null.**

Corroborating that it is noise: the top-correlate identity is unstable across
vintages (L11 `gis_c0` 0.056 → L12 `ais_mu` 0.080), and L12's top correlates are
all **AIS** parameters — the block with 16 unconverged marginals, where
non-mixing manufactures exactly this. No mechanism couples `gis_amp` to AIS.

**ESS trap en route:** a first pass capped the autocorrelation sum at 50 lags, but
it does not terminate until 111 — truncating **inflated** ESS to 983 and
**narrowed** the null. Cap at 200 and let the initial-positive-sequence rule stop
it. Same direction as the known `maxlag` trap.

**ACCEPTED (Marcus, 2026-08-18): "the amplification approach is justified."** The
caveat moves from *open* to **JUSTIFIED**. Do not re-open it. **The flat-hold
sub-choice above 2.75 K is separate and still open.**

---

## 3. THE LITERATURE VERDICT — and a framing error of mine

### 3.1 The correction, first

I called the low discharged fraction **"throughput-limited, not
commitment-limited". That is wrong for the shipped module** and is corrected in
the CHANGELOG and in `ladrillo_option_c` memory. That phrase belongs to the
option-C/D **fit series**, where a throughput cap made `Leq` algebraically
irrelevant. **A+B behaves the opposite way**: it relaxes *faster* than the stock
SIMPLE it replaced and is **99 % equilibrated by 2300** (φ = 0.987/0.991/0.989).
It has essentially finished discharging.

So 1.7–8.5 % is **not** a rate limitation. It is arithmetically the same fact as
the already-recorded defect that **A+B's own committed loss is 19–24× below
Bochow**. The diagnostic re-expressed a known defect against an external ladder;
it did not find a new mechanism. Worth having — but do not sell it as more.

### 3.2 The verdict is scenario-dependent, and the obvious comparison is a trap

| SSP | Ladrillo @2300 | stabilised-forcing lit | continued-warming lit | verdict |
|---|---|---|---|---|
| SSP1-2.6 | 0.091 m | 0.058–0.163 | **0.092** | CONSISTENT (near-exact) |
| SSP2-4.5 | 0.168 m | 0.098–0.218 | not reported | inside |
| SSP5-8.5 | 0.456 m | 0.282–1.230 | **1.732–3.127** | **LOW by 3.8–6.9×** |

> **THE TRAP.** Ladrillo's 0.456 m sits comfortably inside the stabilised band
> 0.282–1.230 m and looks validated. **It is not apples-to-apples.** That band
> holds **year-2100 climate constant** to 2300, whereas Ladrillo keeps warming —
> ssp585 reaches **7.81 K at 2300** against 4.69 K at 2100. Both arms are carried
> in the script so the flattering one cannot be quoted by accident.

**Discharged, ssp585: Ladrillo 6.2 % against a literature 23.4–42.2 %.**

**The commitment being multi-millennial is real, not an excuse** — TC 20:309
reaches 5.1–7.1 m only by **3000**, and its two-way coupled run has not
equilibrated even then. A few-percent discharge by 2300 is physically fine *at low
warming*; at ssp585 it should be about a third.

**This replaces a single-sourced claim.** The 2300 shortfall previously rested on
**Bochow 2026**, an EGUsphere preprint whose Table 2 this project itself retracted
and whose referees raised UQ concerns. Two peer-reviewed, physically-based sources
now agree, at a *larger* factor (3.8–6.9× vs 4.3×).

Sources: **TC 19:6887 (2025)** doi 10.5194/tc-19-6887-2025 (GrIS ensemble, both
arms; ssp585-ext from IPSL-CM6A-LR and CESM2-WACCM). **TC 20:309 (2026)** doi
10.5194/tc-20-309-2026 (MAR–GISM coupled, ssp585 IPSL-CM6A-LR, 0/1/2-way =
1.732 / 2.149 / 2.201 m @2300; 5.122 / 5.635 / 7.135 m @3000).

---

## 4. THE `Leq(T)` REFIT CANNOT FIX ssp585 — measured before buying it

`python/scope_gis_leq_ridge_vs_literature.py`, offline, L12 median params.

**The argument.** The 1900–2025 hindcast constrains only the PRODUCT `phi·Leq`, so
scaling `(c1,c0)` by k and re-solving the rate scale fits identically at every k —
a **ridge**. An external `Leq(T)` target **selects a point ON that ridge; it
cannot move the model off it.** So the refit only works if some ridge point suits
all three scenarios at once. **None does.**

| k | rate s | Leq@585 | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 | 2100 vs k=1 |
|---|---|---|---|---|---|---|
| **1.0 (as shipped)** | 1.010 | 0.54 | **0.092 ✓** | **0.172 ✓** | 0.469 | 1.00× |
| 12.0 | 0.044 | 6.47 | 0.291 | 0.526 | **1.754 ✓** | 1.05× |
| **14.0 (the ceiling)** | 0.037 | 7.42 | 0.298 | 0.535 | **1.794 ✓** | 1.05× |
| 22.6 (Bochow-matched) | 0.023 | 7.42 | 0.305 | 0.555 | 1.318 | 1.05× |
| 50.0 | 0.010 | 7.42 | 0.297 | 0.389 | 0.670 | 0.34× |

**k = 1 — the shipped model — is the BEST point on the ridge** (2/3 in band).
Every k that repairs ssp585 breaks the two scenarios that are currently right.

**Finding 1 — the ridge has a CEILING and is NON-MONOTONE in k.** ssp585@2300
peaks at **1.794 m at k = 14**, barely the *bottom* of the 1.732–3.127 m band,
then falls. `Leq` clips at `V0` = 7.42 m, so past k ≈ 14 more commitment is
unavailable while the rate keeps slowing. At that peak SSP1-2.6 is **1.8×** over
its band top and SSP2-4.5 **2.5×** over.

**Finding 2 — THE INVARIANT, and this is the one to quote.** The ssp585/ssp245
ratio at 2300:

> **literature demands 7.9×–31.9×; the ridge delivers 1.72×–3.36× at any k.**

A linear `Leq` **ties the scenarios together** — raising it to lift ssp585 lifts
the cooler ones by nearly the same factor, so the ratio barely moves. It is
**2.4–9.5× short of anything this family can reach**. Band membership is coarse;
this is the real statement.

---

## 5. WHAT'S NEXT — ITEM 1: THE NONLINEAR RATE LAW ON THE A+B CHANNELS

Marcus's call, 2026-08-18. **Test it, and weigh its physical plausibility at the
same time — the two are not separable here, because the physics is asymmetric
between the two channels and that asymmetry is the whole design.**

### 5.1 Why a nonlinear RATE is the term that can move the invariant

At k = 1 both scenarios are ~equilibrated (φ ≈ 0.99), so realised = `Leq` and the
ratio is just the `Leq` ratio, ≈ 2.7. **To break that you need the cooler scenario
NOT equilibrated while the hotter one IS** — i.e. a rate that is small at low T
and large at high T. That is precisely what a convex `r(T)` does, and it is the
only term in A+B that can produce **differential equilibration** across scenarios.

Combined with a raised `Leq`, the mechanism is: ssp245 sits far from a large
commitment (slow), ssp585 approaches a large commitment (fast). That can generate
a large ratio, which `Leq` scaling alone provably cannot.

**This also explains why option C failed**: it put a threshold in `Leq` **only**
and left the rate linear in T. The threshold has to be in the dynamics.

### 5.2 The physical case — and it is ASYMMETRIC. Do not apply one law to both.

**FAST / SMB channel — convexity is well-motivated. Put the nonlinearity here.**

- **PDD convexity.** Positive-degree-day melt is convex in mean temperature
  because of the melt threshold: warming shifts more of the seasonal distribution
  above 0 °C, and both melt intensity *and* melt-season length grow together.
  Structural property of the scheme, not a citation-dependent claim.
- **Bare-ice / albedo expansion.** The ablation zone widens with warming, exposing
  low-albedo bare ice, which raises melt per degree — a positive feedback on the
  rate itself.
- **Firn saturation and ice slabs.** Greenland's firn buffers meltwater by
  refreezing, but the buffer is finite: once low-permeability ice slabs form,
  meltwater runs off instead of percolating. **MacFerrin et al. 2019**, Nature,
  doi 10.1038/s41586-019-1550-3 — ice slabs expanded the runoff area by
  **26 ± 3 % since 2001**. This is a genuine threshold that makes runoff rise
  superlinearly with warming, and it is the mechanism most directly analogous to
  a convex `r(T)`. See also *Increasing surface runoff from Greenland's firn
  areas*, Nat. Clim. Change 2022, doi 10.1038/s41558-022-01371-z.

**SLOW / DYNAMIC channel — convexity is NOT defensible. Leave it linear.**

- **Discharge self-limits by going land-terminating.** **Aschwanden et al. 2019**,
  Sci. Adv., doi 10.1126/sciadv.aav9396 — by 2300 under RCP8.5 almost all NW
  Greenland outlets are land-terminating and discharge is greatly reduced. The
  dynamic channel **peaks and then declines** on exactly our horizon.
- **Basal lubrication self-limits.** Melt switches the bed from a cavity system to
  a channelized one with lower pressure and *reduced* motion — **Shannon et al.
  2013** PNAS doi 10.1073/pnas.1212647110; **Andrews et al. 2016** Nat. Commun.
  7:13903.
- **Area shrinkage.** A shrinking ice sheet has less margin to discharge; the
  absolute rate must eventually fall.

> **The physics is a HANDOVER from discharge to SMB** — the predecessor's D2 work
> reached the same conclusion from the fit side. So the honest structure is
> **convex rate on the fast/SMB channel, linear (or peak-then-decline) on the
> slow/dynamic channel**. A symmetric superlinear law applied to both would be
> *less* physical than the incumbent, and would be the easy thing to do by
> accident.

### 5.3 The form, and the anchoring discipline that makes it identifiable

Proposed, nesting the incumbent at p = 1:

    r_f(T) = alpha_f · Tbar · (max(T,0) / Tbar)^p  +  beta_f
    r_s(T) = alpha_s · T + beta_s                              (UNCHANGED)

**Anchor at `Tbar` so that `p` and the rate scale `s` are not degenerate.** At
T = `Tbar` the fast rate equals `alpha_f·Tbar + beta_f` for **every** p, so p
rotates the law about the calibration point instead of rescaling it. This is the
identical discipline to the amp law's `S(anchor) == 1` — and it is why that law is
identifiable. **Without the anchor, p and s trade off and the scan will be
uninterpretable.**

`Tbar` = **1.9631 K**, derived from the driver over 2015–2024 — **derive and
assert it, never hardcode** (`LADRILLO_GIS_TBAR`).

**`max(T,0)` is required, not cosmetic:** the regional driver goes negative early
in the record, and a negative base with non-integer p is NaN. A silent NaN here
would look like a failed bisection.

### 5.4 The test — cheap, offline, on the harness that already exists

Extend `scope_gis_leq_ridge_vs_literature.py` to a **2-D (k, p) scan**, bisecting
the rate scale `s` for the hindcast at every cell, and report at each cell: the
three 2300 values against their literature bands, the 2100 G4 **relative to
(k=1, p=1)**, and — the headline — the **ssp585/ssp245 ratio**. No chain, no
calibrator edit. Only if a cell clears everything does a refit become worth
pricing.

### 5.5 Pre-register these BEFORE running it

| | prediction |
|---|---|
| **P1** | the ssp585/ssp245 ratio rises **monotonically** in p (mechanism = differential equilibration) |
| **P2** | some p in **1.5–3** reaches the literature ratio 7.9–31.9× at some k |
| **P3** | the hindcast stays satisfiable at every (k, p) — bisection converges — because the anchor pins the law near the hindcast temperatures |
| **P4** | 2100 G4 stays within **15 %** of the (k=1, p=1) value over the cells that pass P2 |

**Falsifier to watch for, and it is the likely one.** If raising p mostly slows
the *hindcast-era* rate and forces `s` up so far that everything rescales
together, the ratio will not move — the fix would then be doing nothing while
appearing to fit. **This is D2's failure mode: "fit by deleting the machinery it
was given"** (q_thalf railed at its bound, q_marine at its floor). Check for
railing and for `s` moving by orders of magnitude, and treat either as the
falsifier firing, not as a result.

### 5.6 The alternatives, if item 1 fails

(b) a threshold form carrying **both** `Leq` and rate; (c) ship the ssp585 2300
column with the **3.8–6.9× shortfall as a stated caveat**. Option (c) is a
legitimate outcome, not a failure — the 2100 deliverable is unaffected either way.

---

## 6. THINGS THAT DID **NOT** SURVIVE — do not re-inherit

1. **"Throughput-limited, not commitment-limited"** applied to the shipped module.
   **Wrong** — see §3.1. A+B is 99 % equilibrated; it is a commitment deficit.
2. **`|r| ≤ 0.05`** as the inertness threshold. An **iid** null on MCMC draws —
   see §2. Use the ESS-aware null.
3. **A first-draft G4 test** in the ridge scan compared the **median-parameter**
   2100 spread against the **ensemble** 6.3–7.3 cm band and so reported the
   **shipped** model as failing at k = 1. Medians are not multiplicative — the
   same trap behind the retracted "56 % redundant". G4 is now judged **relative to
   k = 1**, the only meaningful comparison at median parameters.
4. **An ESS of 983** for `gis_amp`. Truncated at 50 lags; the sum runs to 111.
   The correct value is **641**.

**Open and NOT explained** (inherited, still untested): `ais_iceflow0` R̂ improved
2.449 → 1.755 across the L12 promotion with no mechanism. The test remains a
second constrained vintage on different seeds.

---

## 7. STATE OF THE POINTERS

`LADRILLO_POSTERIOR_CSV` → **L12**, unchanged.

**Repointed this session:** `diag_ladder_transition_resolution.py` L11 → L12. It
was **not** on the predecessor §5 pinned-provenance list, so that was staleness.
Now derives from a `LADRILLO_TAG` constant. **Verified a no-op before claiming it
was one:** its SSP section depends on GMST only, and **GMST is the FaIR mean
forcing, not a posterior quantity — `max|GMST_L11 − GMST_L12| = 0.0`,
bit-identical** — and both output tables re-ran byte-identical.

> **Keep this fact.** GMST is **vintage-invariant**; only posterior-dependent
> quantities move on a promotion (GIS @2300 ssp585 41.97 → 45.59 cm). It decides
> cheaply whether an L11-vintage artefact actually needs regenerating.

**Still deliberately NOT repointed**, per the predecessor §5: the extA108 pulse
drivers, extC variant-detection fixtures, stock-SIMPLE Mengel pulse drivers, the
L10-vs-D1 arms in `diag_r19_*`, and `diag_gis_ordering_in_l11_posterior.py`. Also
`scope_gis_2300_relaxation.py` still reads **L10 by design** — L10 is the last
NATIVE-Greenland posterior, and that script's reproduction gate is written against
it. The new ridge scan imports its functions but reads L12 itself.

**§7 item 4 (regenerate L11-vintage memo figures at L12) is NOT done.** It needs a
Julia posterior-predictive run plus `ladrillo_model_comparison` at L12; neither
L12 output exists. Only worth the compute if `ladrillo_L11_fig1/2/3` are actually
to be shown. **§7 item 2, the `d2_basis` one-liner, is still parked** — now
deferred past two vintages.

---

## 8. NON-OBVIOUS STATE

- **All work is PUSHED**, `1f7d207` → `37440d3` (5 commits this session).
- **L12 carries the slow channel as `(ell, w)` ONLY.** `gis_alpha_s`/`gis_beta_s`
  do not exist in the L12 subsample — L10 was the last native vintage. Anything
  touching native Greenland params must map via `ladrillo_native_greenland!`
  (`alpha_s = w·e^ℓ/Tbar`, `beta_s = (1−w)·e^ℓ`). **This bites immediately**: the
  ridge scan crashed on it first run.
- `python/ladrillo_committed_ladder.py` is about **GLACIERS**, not Greenland.
  Similar name, unrelated file — do not reach for it for Greenland work.
- The two modified-but-uncommitted files in `git status`
  (`figures/diag_gis_regional_driver.png`, `outputs/mcmc/overdispersed_starts.csv`)
  are inherited from the L12 session, untouched here.
- **macOS has no `timeout`**; pin `OPENBLAS_NUM_THREADS=1` for parallel chains.

---

## 9. FILES

**Created this session**

| file | purpose |
|---|---|
| `python/diag_gis_committed_loss.py` | committed vs realised, both arms, + the literature check |
| `python/plot_gis_committed_loss.py` | the two-panel companion figure |
| `python/diag_gis_amp_calib_projection_gap.py` | the amp caveat, both legs, ESS-aware null |
| `python/scope_gis_leq_ridge_vs_literature.py` | walks the ridge; the ceiling and the invariant |

**Modified:** `python/diag_ladder_transition_resolution.py` (L11 → L12), `CHANGELOG.md`.

**Key outputs:** `outputs/diag_gis_committed_loss.csv`,
`outputs/diag_gis_amp_calib_projection_gap.csv`,
`outputs/scope_gis_leq_ridge_vs_literature.csv`,
`figures/gis_committed_loss_L12.png`.

**Memory touched:** `ladrillo_channel_inversion` (L12 supersession),
`ladrillo_option_c` (diagnostic built; framing corrected; literature verdict),
`ladrillo_gis_amp` (nominal + accepted; `|r|` correction),
**`ladrillo_leq_ridge_ceiling` (new)**, plus `INDEX_slr.md` and `MEMORY.md`.
