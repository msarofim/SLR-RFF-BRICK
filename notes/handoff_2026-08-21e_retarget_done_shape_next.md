# Handoff — the RE-TARGET is done. The cool bands were already matched, the ssp585 band was not, and the tap's admissible set inverted.

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`.
Written 2026-08-21, to be picked up cold.

**Supersedes** `handoff_2026-08-21d_preflight_done_retarget_first.md` for its §2
(all four steps of §2.1 are DONE) and for §4 item 4 (both single-law death
certificates are void). **Its §3 (option 2, the state-dependent relaxation rate)
is UNCHANGED and is now the job** — the falsifier §2.1 pre-registered resolved in
exactly the direction that says so.

**Read with:** `handoff_2026-08-21b_protect_matched_forcing.md` (how the PROTECT
evidence was built), `spec_2026-08-14_next_calibration.md` (D1-D5, settled, NOT
STARTED).

Commits this handoff closes over: `350f656` `19420f2` `03f1617` `67a6fb2`
`291e2ac` `5157709`.

---

## 0. THE ONE-PARAGRAPH VERSION

The falsifier was pre-registered and it fired the *conservative* way. **The two
cool 2300 bands were already forcing-matched** — ssp245 to 1.00× on the 2015-2300
GSAT integral, ssp126 to 1.10× — so the pre-flight's kill of k = 2-3 survives, and
tightens to **k ≤ 1.0**. Only ssp585 moved, and it moved hard: **173-313 → 43-145
cm**. That single correction inverts most of what rested on it. The **untapped
base now clears every 2300 target**; the **shipped tap cell FAILS**, 1.59× above
the band top; the lit and matched admissible sets are **exactly disjoint** (25 /
104, intersection 0); and both single-law variants that were declared dead on the
ssp585/ssp245 *ratio* are alive, because that ratio band — a derived quantity —
moved 7.94-31.91× → 2.00-13.68×. **What did NOT move is the thing that matters
next:** `scope_gis_ridge_vs_protect.py` re-ran byte-identical, because it scores
our model on THEIR forcing and never used the band dict. Its interior optimum
**k = 2-3 still opposes the cool bands' k ≤ 1.0**. Re-targeting removed the ssp585
half of that disagreement and left the half that was always the real one. So:
**option 2, and the tension in §3 below is the thing it has to resolve.**

---

## 1. WHAT WAS MEASURED

### 1.1 The forcing behind every band (`scope_gis_cool_band_forcing.py`, `350f656`)

PROTECT-Greenland long runs at ssp126/ssp245, split by forcing family exactly as
the ssp585 arms were. r2300 = the GCM's own scenario to 2100 then held at its
2081-2100 mean; x2300 = the natural CMIP6 extension. **Entirely offline** — the
cached `data/cmip6_gis/` series carry ssp126/ssp245 to 2100 for CESM2 and
MPI-ESM1-2-HR, and CESM2-WACCM's ssp126 store runs to **2299** (the `ssp585` stores
are the ones truncated at 2100 — `[[pangeo_cmip6_no_ext]]` is about ssp585, not
about extensions in general). ssp585 **reads the two prebuilt forcing CSVs** rather
than re-deriving the kernel a fourth time — and could not rebuild them anyway,
since UKESM1-0-LL and CNRM-ESM2-1 are not in `data/cmip6_gis`.

| band | family | GSAT@2300 | ∫2015-2300 | ours | ratio | verdict |
|---|---|---|---|---|---|---|
| SSP1-2.6 | r2300 | 1.96 K | 544 K·yr | 1.73 K / 495 | **1.10×** | MATCHED |
| SSP1-2.6 | x2300 | 2.48 K | 651 | " | 1.32× | hotter — but its SLR is *lower* (9.8 vs 11.1 p50), so the extra warming is not what sets the band |
| SSP2-4.5 | r2300 | 2.99 K | 790 | 3.14 K / 790 | **1.00×** | MATCHED |
| SSP5-8.5 | r2300 | 5.58 K | 1406 | 7.80 K / 1626 | 0.86× | theirs COOLER |
| SSP5-8.5 | x2300 | **13.80 K** | 2614 | " | **1.61×** | the verified mismatch |

The **integral** is the predictor to read, not the 2300 level: an ice sheet
integrates forcing, and r2300/x2300 can share a level while differing by centuries
of melt. Both are computed; the level arm is the stated sensitivity.

### 1.2 The matched target set (`build_gis_matched_targets.py`, `gis_targets.py`)

PCHIP through log(SLR@2300) vs the integral, five anchors, 1.96-13.80 K.

| | MATCHED | LIT | rule |
|---|---|---|---|
| SSP1-2.6 | 6.2-15.9 cm | 5.8-16.3 | union of bracketing anchors |
| SSP2-4.5 | 10.6-21.5 cm | 9.8-21.8 | PCHIP, inside the hull |
| SSP5-8.5 | **42.9-145.0 cm** | 173.2-312.7 | PCHIP, inside the hull |

p50 98.5 cm reproduces the old ~100 cm bracket independently, but the band is now
**derived** (p05-p95 at our forcing) rather than the two anchors' p50s quoted as a
range — and all three bands are now the same kind of interval, which they were
not: the LIT ssp585 band was a span across two sources, the cool ones p05-p95-like.

**ssp126 deliberately does NOT get the interpolated number.** Its predictor is 10%
below the anchor hull and PCHIP's left end-slope there is set by a *decreasing*
segment that is a change of family and GCM, not a forcing response; extrapolating
on it flares the band to 4.8-25.5 cm. The hull rule is stated once and applied
mechanically, and the adopted union band is if anything GENEROUS — which matters,
because Q1 is a band-TOP test, so the kill surviving is a fortiori.

### 1.3 The scorecards (`19420f2`, `03f1617`)

**Both reproduction gates exact** under `--targets=lit`: the ssp_bands scan
reproduces the 2026-08-21f table row for row, and the tap pricer reproduces
25/140 with G1/G2/G2b/G3 all PASS.

**The derived ratio band moved furthest: 7.94-31.91× → 2.00-13.68×.**

| | LIT | MATCHED |
|---|---|---|
| untapped base ssp585@2300 0.500 m | out, "3.5× SHORT" | **IN** (0.429-1.450) |
| untapped base ratio 2.73× | "SHORT by 2.9×" | **IN** (2.00-13.68×) |
| **shipped tap cell** 2.303 m | `bands_ok` True → PASS | **`bands_ok` FALSE → FAIL**, 1.59× over the top |
| tap admissible cells | 25/140 | 104/140, **intersection 0** |

> The 25 lit passers span 1.753-2.933 m; the matched band tops out at 1.450, and
> **0/25 clear the matched LEVEL bands** (19/25 still clear the ratio band — the
> level is what kills them). The 104 matched passers span 0.500-**1.444** m, and
> **0.500 IS the untapped base**: the scorecard now passes largely by turning the
> tap DOWN. Do not read 104 > 25 as good news.

**ssp_bands k-scan.** The **binding scenario flips**: ssp585 failed at 16/16 k
against lit, at **1/16** against matched, and the cool pair now binds (ssp126
12/16, ssp245 15/16). **k = 1 is ALL PASS** — the first k on this grid ever to
satisfy all four criteria. The ceiling verdict inverts: the 1.463 m peak was
"1.18× SHORT of the band FLOOR" and **clears the matched floor 3.41×**, so the V0
clip is not what binds. Q1 **tightens to k ≤ 1.0** (ssp245's matched band is
narrower, so it leaves at k=1.25 rather than 1.5).

### 1.4 Both single-law death certificates are VOID (`03f1617`) — read the caveat

| variant | `--targets=lit` (reproduces) | `--targets=matched` |
|---|---|---|
| Leq ridge | 3.36× vs 7.94-31.91×, 2.4-9.5× SHORT, *"cannot be the fix"* | overlaps; 11/13 k in band; k=[1.0] satisfies ALL → *"CAN work"* |
| rate-power | P2 FAIL, no cell clears all three | P2 **PASS**; k=1 p=1 and k=1 p=1.25 clear everything |

**This is NOT "the variants now work".** The cell surviving in both is **k = 1,
p = 1 — the shipped base model** (no ridge move, linear rate), and under matched
targets essentially the *whole* ratio grid is in-band, shipped 2.73× included. The
ratio criterion has lost its discriminating power. Correct reading: the base
already passes, so neither variant is *needed*; whether either *helps* is a
question for the shape scorecard, not the 2300 bands.

---

## 2. THE MECHANICS — read before touching any scorecard

* **`python/gis_targets.py` is the ONE place both target sets live.** Six scripts
  scored against `LIT_2300_M`; four imported it and **two carried their own copied
  literals**, which is why no single edit could correct them all. All eight
  consumers now import. `LIT_2300_M` is re-exported from
  `scope_gis_leq_ridge_vs_literature` under its old name and is **still the raw
  literature dict** — four scripts import it by that name and must not have it
  change under them. Scripts that want to *score* call `gis_targets.from_argv`.
* **`--targets=lit|matched`, default MATCHED.** Every scorecard prints
  `gis_targets.banner()`, so a verdict can never be read without knowing which set
  produced it, and **the set is appended to every output filename** (`_lit` /
  `_matched`) so neither run can overwrite the other's artefact. The pre-retarget
  unsuffixed CSVs are left exactly where they are.
* **`gis_targets` self-checks at import**: the MATCHED literals are re-derived from
  `outputs/gis_matched_targets_2300.csv` and the import RAISES if they have
  drifted. Literals so a scorecard cannot silently depend on a regenerated file;
  the check so they cannot silently rot.
* **`diag_gis_committed_loss.py` legitimately keeps its own dict** — it is a
  TWO-ARM structure (stabilised vs continued-warming) that `gis_targets` does not
  serve. Annotated, not rewired.
* **NOT RE-RUN**: the basin-mock, 3basin-partition and zonespace scorecards were
  wired (they now print the banner) but not executed. Their committed verdicts are
  lit-set verdicts.

---

## 3. THE JOB — option 2, and the tension it has to resolve

`scope_gis_ridge_vs_protect.py` **re-ran byte-identical** (re-run and diffed
against the committed log, not assumed), because it runs our model on THEIR
forcing and never used the band dict. So it is the one scorecard the re-target
structurally cannot touch, and **its verdict stands**:

| | wants | source |
|---|---|---|
| 200 yr of SHAPE vs the PROTECT trajectories, matched forcing | **k = 2-3** (RMS log-misfit 0.293-0.294; shipped k=1 is 0.497, **1.70× worse**) | `scope_gis_ridge_vs_protect.py` |
| the cool scenarios' 2300 LEVEL bands, now forcing-matched | **k ≤ 1.0** | `scope_gis_ridge_vs_ssp_bands.py --targets=matched` |

**This is the same tension `handoff_2026-08-21d` §1 recorded, with the ssp585 half
removed.** It is now clean: our slow channel wants a longer τ to track the physics
trajectory in *shape*, and a longer τ over-realises the cool scenarios' commitment
in *level*. **A scale cannot fix a rotation** — which is exactly the §3 argument for
option 2, and it is now the ONLY live reading rather than one of several.

Option 2 as specified in `handoff_2026-08-21d` §3 is **unchanged and is the job**:
`r = r0(T)·(1 + γ·L/(k_b·V0))`, built offline behind a `γ` argument in
`basin2_series` (default 0.0 ⇒ bit-identical, the G3-style nesting gate), scored
with the `rms_log_misfit` column, `greenland_3basin_component.jl` untouched until a
γ clears offline. **MEASURE the likelihood inertness, do not assume it.** Watch
(a) 2100 must not move, (b) the V0 clip's role, (c) the hindcast does NOT come free
the way it does for k.

### 3.1 DONE 2026-08-21i — the cool arms are IN the shape scorecard, and the answer is quantified

`python/build_protect_cool_forcing.py` (three drivers) +
`python/scope_gis_shape_all_scenarios.py` (5 arms, 20 horizons). Every arm runs our
model on THAT arm's forcing against THAT arm's runs — scenario AND family matched
on both sides.

| | best k | score | at k = 1 |
|---|---|---|---|
| ssp585 arms (the published scan's own 8 horizons, reproduced exactly) | **3** | 0.293 | 0.497 |
| cool arms (12 new horizons) | **0.75** | 0.229 | 0.262 |
| all five (**NOT** comparable to 0.293) | 1 | 0.374 | — |

**The argmins disagree**, costing each other 2.23× / 2.96× in the other's metric —
a scale cannot serve both, confirming §3's premise rather than assuming it.
**But the shipped model is not symmetrically placed: at k = 1 it is 1.14× off the
COOL optimum and 1.70× off the ssp585 one.** Essentially all the deficiency is on
the warm arm, so the correction must act SELECTIVELY there.

**Selectivity, measured twice.** A term ∝ `L/V0` has **4.1×** more leverage on the
warmest arm than any cool one — but the arms **bracket** our ssp585 (5.61 and
13.63 K vs our 7.81) rather than matching it, so on **our own deliverable drivers**
it is **2.3×** (ssp585 0.0753 vs ssp245 0.0327). **Do not quote 4.1× for the
deliverable.** Sizing for the offline grid, not a fit: a 2× late-rate boost needs
γ ~ **13** on the total-V0 basis, and the cool arms move **0.43** of that. That is
the trade γ has to beat, and 2.3× is *modest* — γ is not guaranteed to clear it.
**Run it; do not assume it.**

Six gates, all passing: splice arithmetic 1.8e-15, hold construction 4.4e-16
(UKESM1-0-LL not cached and reported as NOT checked), ssp585 reproduction 2.8e-14
cm, rel-2015 offset scenario-invariant (spread 0.0000 cm, measured), hindcast
history choice 0.000 cm, and **band composition == forcing composition per GCM per
arm** — which caught a live counting trap: a PROTECT *run* is a
`(group, model, exp)` triple, and counting unique `exp` NAMES undercounts x2300 by
a third (12 vs 18 at ssp585, 4 vs 6 at ssp126) because one experiment name appears
under several ice-sheet-model directories.

### 3.2 SUPERSEDED — the original framing of §3.1, kept for provenance

The shape scorecard currently runs **ssp585 arms only**. The cool-scenario PROTECT
long runs and their forcing paths now exist
(`outputs/scope_gis_cool_band_forcing.csv` carries the annual n-weighted GSAT for
every ssp × family, 1850-2300, in driver form). **Running our model on the ssp126
and ssp245 matched forcings would put the shape constraint and the cool-level
constraint in ONE scorecard at matched forcing** — which is precisely what the §3
tension needs in order to be settled rather than restated. That is a Julia
`diag_protect_forcing_matched`-style run on two new drivers, not new physics.
**Do this before or alongside γ**, because it is the measurement that tells you
whether γ can satisfy both constraints at once or whether nothing can.

---

## 4. WHAT THIS DOES *NOT* SETTLE — do not overclaim

* **The tap's SIZE finding hardens; its EXISTENCE is now the open question.** The
  untapped base clears every matched 2300 target and the shipped cell does not.
  That is a strong statement against the shipped cell, and NOT yet an instruction
  to remove the tap — the 2150 evidence (`protect_matched_forcing`) is a separate
  horizon and was not re-scored here.
* **Every anchor past 2100 is NORCE-CISM.** ONE ice sheet model under many climate
  forcings ⇒ the p05-p95 is CLIMATE-forcing spread, **not** ice-sheet structural
  spread. A target, never a hard cut. This caveat is printed by `banner()` on every
  matched-set run for exactly this reason.
* **The matched band is an interpolation across FAMILIES** (r2300 → x2300), which
  differ in GCM panel and CISM configuration as well as forcing. Flagged in the
  builder; the 2300-level arm is the stated sensitivity (ssp585 58.6-172.2 cm vs
  the integral arm's 42.9-145.0).
* **No gate changed, no cell moved, no chain started.** The D1-D5 change set
  (`spec_2026-08-14_next_calibration.md`) is still NOT STARTED and still applies
  whichever option wins. **Rebuild starts and `adapted_cov` BY NAME**
  (`[[nameless_matrix_order]]`). The real unconverged mass is still AIS.

---

## 5. FILES

**New** — `python/scope_gis_cool_band_forcing.py`, `python/build_gis_matched_targets.py`,
`python/gis_targets.py`; `outputs/scope_gis_cool_band_forcing.csv`,
`outputs/scope_gis_cool_band_targets.csv`, `outputs/gis_matched_targets_2300.csv`;
`_lit`/`_matched` pairs of `scope_gis_ridge_vs_ssp_bands`, `scope_gis_tap_l14`,
`scope_gis_leq_ridge_vs_literature`, `scope_gis_rate_power_vs_literature` (CSV + log).

**Modified** — `scope_gis_leq_ridge_vs_literature.py` (re-export + own `--targets`,
verdict text now COMPUTED from the set rather than asserting the lit conclusion),
`scope_gis_ridge_vs_ssp_bands.py`, `scope_gis_tap_l13.py`,
`scope_gis_rate_power_vs_literature.py`, `scope_gis_basin_mock_vs_literature.py`,
`scope_gis_3basin_partition.py`, `scope_gis_basin_zonespace_vs_literature.py`,
`plot_gis_basin_mock.py`, `plot_gis_rate_power_scan.py` (the two copied literals),
`diag_gis_committed_loss.py` (annotated), `CHANGELOG.md` (2026-08-21h).

**Memory** — `protect_matched_forcing` (§2026-08-21g + frontmatter),
`gis_ridge_broken_by_protect`, `gis_tap_priced_l13`, new `audit_every_target`,
`INDEX_slr.md` live state, `MEMORY.md`.

---

## 6. TRAPS

* **A comparison at two different forcings is not a comparison** — now bitten
  THREE times on this dataset. But the corollary this session added: **audit EVERY
  band, not just the suspect one.** Two of three were already matched, and that
  asymmetry is what decided which conclusions survived. `[[audit_every_target]]`
* **A DERIVED criterion moves further than the bands it comes from.** The level
  bands moved 1.0-0.39×; the ratio band built from two of them moved 7.94-31.91× →
  2.00-13.68×. Audit derived criteria first.
* **A scorecard can pass by disabling the thing it scores.** 25 → 104 passers looks
  like good news; the survivors' effect size runs down to the untapped baseline.
  Check what the survivors DO. And compare SETS, not counts — the disjointness is
  the headline and is invisible in the counts.
* **The k = 1 row is not the shipped model** (unchanged from 2026-08-21d §6).
* **Band membership does not locate an optimum** — use `rms_log_misfit`.
* **Sensitivity arms have to be RUN**, not reasoned about.
* **Do not widen a gate to make a new vintage pass** — `G1_REF` is keyed by vintage.
